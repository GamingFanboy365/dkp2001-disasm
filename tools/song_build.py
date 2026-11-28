#!/usr/bin/env python3
"""Build a song for the game's sound driver from a description.

    python3 tools/song_build.py updates/music/jungle.py

writes updates/music/jungle.s (assembled into the updates build) and, with
`--midi OUT.mid`, a standard MIDI file of it to listen to (General MIDI sounds stand
in for the game's samples).

A description (see updates/music/jungle.py) gives NAME, TEMPO (beats per minute),
INTRO and LOOP (lists of bars, played once / forever; with ONCE = True the whole song
plays once and stops, as for a fanfare), and TRACKS: one per part,
each with a channel, a program (an instrument of the race tunes' set, vgroup0) and its
bars. A bar is a string of events separated by spaces, each "NOTE:LEN" or "r:LEN"
(rest) where NOTE is like C4, F#5, Bb3 (or a drum key number) and LEN is in
sixteenths; several notes joined by "+" sound together. A drum bar can also be a
16-step pattern per key, e.g. {36: "x...x...", 42: "xxxxxxxx..."}.

The song format (see midi_commands in asm/src/audio/code/audio.S): per track, a stream
of 0 tempo (3 bytes, microseconds per beat), 1-4 a delay of 1-4 bytes, 5 note on (channel,
key, velocity), 6 note off, 7 controller (channel, number, value), 8 program change
(channel, program), 11 end of track. Controller 102 marks a track's loop point and 103
jumps back to it (how Rare's tunes loop), 7 is volume, 10 pan.
"""
import importlib.util
import os
import struct
import sys

PPQN = 384                       # ticks per beat, as Rare's race tunes
SIXTEENTH = PPQN // 4
BAR = PPQN * 4
NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def key(s):
    """C4 = 60 (middle C), F#5 = 78, Bb3 = 58; plain numbers are drum keys."""
    if s.isdigit():
        return int(s)
    n = NOTES[s[0]]
    i = 1
    while i < len(s) and s[i] in "#b":
        n += 1 if s[i] == "#" else -1
        i += 1
    return n + 12 * (int(s[i:]) + 1)


def bar_events(bar, vel, gate):
    """(tick, key, length, velocity) for one bar."""
    out = []
    if isinstance(bar, dict):                       # drum steps: x loud, o soft, . rest
        for k, steps in bar.items():
            for i, ch in enumerate(steps):
                if ch in "xo":
                    out.append((i * SIXTEENTH, int(k), SIXTEENTH, vel if ch == "x" else vel * 3 // 5))
        return out
    t = 0
    for tok in bar.split():
        name, ln = tok.split(":")
        ln = int(ln) * SIXTEENTH
        if name != "r":
            for nm in name.split("+"):
                out.append((t, key(nm), max(SIXTEENTH // 2, int(ln * gate)), vel))
        t += ln
    if t not in (0, BAR):
        raise ValueError(f"bar is {t / SIXTEENTH:g} sixteenths, not 16: {bar}")
    return out


def build(d):
    tracks = []
    tempo = int(round(60_000_000 / d.TEMPO))
    loop_start = len(d.INTRO) * BAR
    loop_end = loop_start + len(d.LOOP) * BAR
    # track 0: the conductor (tempo), like Rare's
    tracks.append([(0, 0, bytes((0,)) + tempo.to_bytes(3, "little")), (loop_end, 9, bytes((11,)))])
    for part in d.TRACKS:
        ch, prog = part["channel"], part["program"]
        ev = [(0, 0, bytes((8, ch, prog))),
              (0, 1, bytes((7, ch, 7, part.get("volume", 100)))),
              (0, 1, bytes((7, ch, 10, part.get("pan", 64))))]
        if not getattr(d, "ONCE", False):           # ONCE: played through once, then the
            ev += [(loop_start, 2, bytes((7, ch, 102, 0))),     # driver stops the tune
                   (loop_end, 8, bytes((7, ch, 103, 0)))]
        bars = list(part.get("intro", [None] * len(d.INTRO))) + list(part["loop"])
        if len(bars) != len(d.INTRO) + len(d.LOOP):
            raise ValueError(f"track on channel {ch} has {len(bars)} bars, not {len(d.INTRO) + len(d.LOOP)}")
        notes = []
        for b, bar in enumerate(bars):
            if not bar:
                continue
            for t, k, ln, v in bar_events(bar, part.get("velocity", 100), part.get("gate", 0.85)):
                notes.append((b * BAR + t, k, ln, v))
                ev.append((b * BAR + t, 5, bytes((5, ch, k, v))))
                ev.append((b * BAR + t + ln, 4, bytes((6, ch, k, 0))))
        ev += expression(part, ch, notes)
        tracks.append(ev)
    return tracks, loop_start, loop_end


def bend(ch, value):
    value = max(0, min(16383, int(value)))
    return bytes((10, ch, value & 255, value >> 8))


def expression(part, ch, notes):
    """Rare's lead expression, as the race tunes use it (NOTES.md): on notes at least
    `long` sixteenths long, vibrato (CC 1) after a short delay, and (`swell`) a pitch bend
    up and back; a note followed by a rest (a phrase end) can `fall` away at its end.
    Bend values: centre 8192, 0-16383."""
    out = []
    long = part.get("long", 6) * SIXTEENTH
    single = sorted({(t, ln) for t, k, ln, v in notes})
    starts = [t for t, ln in single]
    for i, (t, ln) in enumerate(single):
        if ln < long:
            continue
        if part.get("vibrato"):
            out.append((t, 3, bytes((7, ch, 1, 0))))
            out.append((t + ln // 3, 3, bytes((7, ch, 1, part["vibrato"]))))
            out.append((t + ln, 3, bytes((7, ch, 1, 0))))
        if part.get("swell"):
            up, mid = 8192 + part["swell"], t + ln // 2
            for k in range(5):                                  # up and back, as Rare's do
                out.append((mid - 96 + k * 24, 3, bend(ch, 8192 + (up - 8192) * k / 4)))
                out.append((mid + 48 + k * 24, 3, bend(ch, up - (up - 8192) * k / 4)))
        nxt = starts[i + 1] if i + 1 < len(starts) else None
        if part.get("fall") and (nxt is None or nxt - (t + ln) >= 2 * SIXTEENTH):
            for k in range(1, 7):                               # a fall at the phrase end
                out.append((t + ln - 96 + k * 16, 3, bend(ch, 8192 - part["fall"] * k / 6)))
            out.append((t + ln + 1, 3, bend(ch, 8192)))
    return out


def encode(ev):
    """Events (tick, order, bytes) -> the driver's byte stream. Note-offs sort before
    note-ons at the same tick; the loop jump comes last."""
    out = bytearray()
    now = 0
    for t, _, b in sorted(ev, key=lambda e: (e[0], e[1])):
        dt = t - now
        if dt:
            n = (dt.bit_length() + 7) // 8
            out += bytes((n,)) + dt.to_bytes(n, "little")
            now = t
        out += b
    if out[-1] != 11 and not out.endswith(bytes((11,))):
        out += bytes((11,))
    return bytes(out)


def emit(d, tracks, path):
    name = d.NAME
    lines = [f"@ {name}: generated by tools/song_build.py from {os.path.basename(path)[:-2]}.py.",
             "@ Ours (updates patch): an original tune, played with the race tunes' instruments.", "",
             '\t.section .fixes, "ax", %progbits', "\t.balign 4", f"{name}_tune:",
             f"\t.word\t{len(tracks)}, {PPQN}, {name}_trks, vgroup0_vmap, vgroup0_samplist",
             f"{name}_trks:"]
    lines += [f"\t.word\t{name}_trk{i}" for i in range(len(tracks))]
    for i, ev in enumerate(tracks):
        data = encode(ev)
        lines.append(f"{name}_trk{i}:")
        for k in range(0, len(data), 16):
            lines.append("\t.byte\t" + ", ".join(str(b) for b in data[k:k + 16]))
    lines.append("\t.balign 4")
    open(path, "w").write("\n".join(lines) + "\n")


def midi(d, tracks, path):
    """The same song as a type-1 MIDI file (the loop played twice), to listen to."""
    def vlq(n):
        b = [n & 127]
        while n > 127:
            n >>= 7
            b.insert(0, (n & 127) | 128)
        return bytes(b)
    chunks = []
    _, loop_start, loop_end = build(d)
    drum = {e[2][1] for ev in tracks for e in ev if e[2][0] == 8 and e[2][2] == 127}
    remap = lambda ch: 9 if ch in drum else (ch if ch != 9 else 8)
    for ev in tracks:
        out, now = bytearray(), 0
        evs = sorted(ev, key=lambda e: (e[0], e[1]))
        # play the loop twice
        evs = evs + [(t + loop_end - loop_start, o, b) for t, o, b in evs if loop_start <= t < loop_end]
        for t, _, b in sorted(evs, key=lambda e: (e[0], e[1])):
            op = b[0]
            if op == 0:
                msg = bytes((0xFF, 0x51, 3)) + int.from_bytes(b[1:4], "little").to_bytes(3, "big")
            elif op == 5:
                msg = bytes((0x90 | remap(b[1]), b[2], b[3]))
            elif op == 6:
                msg = bytes((0x80 | remap(b[1]), b[2], 0))
            elif op == 7:
                if b[2] in (102, 103):
                    continue
                msg = bytes((0xB0 | remap(b[1]), b[2], b[3]))
            elif op == 8:
                msg = bytes((0xC0 | remap(b[1]), 0 if b[2] == 127 else b[2]))
                if b[2] == 127:              # the drum kit: General MIDI drums are channel 10
                    continue
            else:
                continue
            out += vlq(t - now) + msg
            now = t
        out += b"\x00\xff\x2f\x00"
        chunks.append(b"MTrk" + struct.pack(">I", len(out)) + out)
    open(path, "wb").write(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), PPQN) + b"".join(chunks))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    spec = importlib.util.spec_from_file_location("song", src)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    tracks, ls, le = build(d)
    emit(d, tracks, src[:-3] + ".s")
    secs = (le - ls) / PPQN * 60 / d.TEMPO
    print(f"{d.NAME}: {len(tracks)} tracks, intro {ls // BAR} bars, loop {(le - ls) // BAR} bars ({secs:.0f} s)")
    if "--midi" in sys.argv:
        midi(d, tracks, sys.argv[sys.argv.index("--midi") + 1])


if __name__ == "__main__":
    main()

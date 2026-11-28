"""The way Rare's race tunes are played, as helpers for our song descriptions
(updates/music/*.py; see NOTES.md, "Rare's music"). Measured from the build's seven tunes:

- notes are short, mostly 1-2 sixteenths, in syncopated 3+3+2 rhythms, each with its own
  velocity (accents on the beat, lighter ghost notes between);
- chords are stabs: three-note hits (program 30, the menu tune) and two-note jabs
  (program 18), on the same syncopated steps;
- melodies are doubled in thirds on a second track of the same instrument (the beach
  tune's two pianos, program 1);
- sustain is rare: a short held counter-line (program 19) or the castle tune's soft
  sixteenth shimmer (program 41, quiet) carries the length;
- the kit pumps: kick on every beat at full velocity, a soft snare on the off-beats,
  sixteenth hats with open hats on the "and"s.
"""

MENU_STABS = "x.x...xx.xx.x..."         # the menu tune's stab steps (0 2 6 7 9 10 12)
TRESILLO = "x..x..x.x..x..x."           # 3+3+2, twice
OFFBEATS = "..x...x...x...x."           # reggae chops

RARE_KIT = {36: "x...x...x...x...", 38: "..o...o...o...o.", 42: "xoooxoooxoooxooo", 46: "..o...o...o...o."}
RARE_KIT_FILL = {36: "x...x...x...x...", 38: "..o...o...xoxoxx", 42: "xoooxoooxooo....", 45: "........x.......",
                 43: "..........x....."}
ONE_DROP = {36: "........x.......", 38: "........x.......", 42: "x.o.x.o.x.o.x.o.", 46: "..............o."}
ONE_DROP_FILL = {36: "........x.......", 38: "........x.o.x.xx", 45: "......x.........", 43: "..........x.....",
                 42: "x.o.x.o........."}


def hits(chord, pattern, loud=118, soft=86):
    """A bar of one-sixteenth stabs of `chord` (notes joined by +) on the x/o steps."""
    out = []
    for c in pattern:
        if c == "x":
            out.append(f"{chord}:1:{loud}")
        elif c == "o":
            out.append(f"{chord}:1:{soft}")
        else:
            out.append("r:1")
    return " ".join(out)


NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def key_number(name):
    n = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[name[0]]
    i = 1
    while name[i] in "#b":
        n += 1 if name[i] == "#" else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def key_name(n):
    return NAMES[n % 12] + str(n // 12 - 1)


def third_below(bar, scale):
    """The same line two steps lower in `scale` (pitch classes): the second track of a pair."""
    out = []
    for tok in bar.split():
        parts = tok.split(":")
        if parts[0] == "r":
            out.append(tok)
            continue
        names = []
        for nm in parts[0].split("+"):
            m, steps = key_number(nm) - 1, 0
            while True:
                if m % 12 in scale:
                    steps += 1
                    if steps == 2:
                        break
                m -= 1
            names.append(key_name(m))
        out.append(":".join(["+".join(names)] + parts[1:]))
    return " ".join(out)


def hits_bar(*segments):
    """One bar of stabs from (chord, pattern) segments whose patterns add up to 16 steps."""
    out = []
    for chord, pattern in segments:
        out.append(hits(chord, pattern))
    return " ".join(out)


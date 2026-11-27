#!/usr/bin/env python3
"""Relocation test: prove the source has no hard-coded addresses left.

Plays a front-end tour (title, mode select, character and world select) and
every track. Builds the ROM twice more with 4 KiB of padding inserted, once before .text
(moving all ROM code and data) and once before .rodata (moving data only).
Then it plays every track in mGBA on all three ROMs with the same inputs and
compares screen hashes. If a pointer were still a raw number, the shifted
ROMs would crash or behave differently.

Usage: python3 tools/reloc_test.py path/to/romtest [--fixed | --updated] [first_track] [last_track]

With --fixed the bug-fix build is tested instead (make fixed), and with
--updated the updates build (make updated); there the Jungle 03
out-of-bounds read is fixed, so every track must be identical.

Track N is reached by pressing A N times on the debug menu, then START.
"""
import hashlib
import subprocess
import sys

# Tracks whose behaviour legitimately depends on where data sits, because the
# original game reads out of bounds there (see README, "Bugs found").
KNOWN = {31: "Jungle 03: AI reads past the end of __net_jungle_03"}

ROMS = {
    "original": "build/dkp.gba",
    "code+data shifted": "build_shift_c0x1000_d/dkp.gba",
    "data shifted": "build_shift_c_d0x1000/dkp.gba",
}


def run(romtest, rom, track):
    presses = [f"{40 + 12 * i}:A" for i in range(1, track + 1)]
    st = 60 + 12 * track + 30
    script = presses + [f"{st}:START", f"{st + 300}:A:1500", f"{st + 500}:LEFT:60",
                        f"{st + 800}:RIGHT:90", f"{st + 1000}:B:10", f"{st + 1100}:UP:80"]
    out = subprocess.run([romtest, rom, str(st + 1500), "50"] + script,
                         capture_output=True, text=True, check=True).stdout
    return hashlib.sha1(out.encode()).hexdigest()


def frontend(romtest, rom):
    """Quit a race into the real front-end, cycle the game modes, the characters
    and the world list, then start a race. Uses the title/menu sprites."""
    t = ["200:START", "800:START", "860:DOWN", "900:DOWN", "960:A"]
    t += [f"{1150 + i * 90}:RIGHT" for i in range(8)] + [f"{1900 + i * 90}:LEFT" for i in range(8)]
    t += ["2700:A"] + [f"{2900 + i * 80}:RIGHT" for i in range(10)] + ["3800:A"]
    t += [f"{4000 + i * 60}:DOWN" for i in range(5)] + ["4400:A", "4700:A"]
    out = subprocess.run([romtest, rom, "5400", "25"] + t, capture_output=True, text=True, check=True).stdout
    return hashlib.sha1(out.encode()).hexdigest()


def main():
    global ROMS, KNOWN
    args = [a for a in sys.argv[1:] if a not in ("--fixed", "--updated")]
    romtest = args[0]
    first = int(args[1]) if len(args) > 1 else 0
    last = int(args[2]) if len(args) > 2 else 39
    if "--fixed" in sys.argv or "--updated" in sys.argv:
        updated = "--updated" in sys.argv
        base, pre = ("build_updated", "build_up") if updated else ("build_fixed", "build_fx")
        flags = ["FIXES=1", "UPDATES=1"] if updated else ["FIXES=1"]
        ROMS = {"original": f"{base}/dkp.gba",
                "code+data shifted": f"{pre}_c/dkp.gba",
                "data shifted": f"{pre}_d/dkp.gba"}
        KNOWN = {}
        subprocess.run(["make", "-s", "updated" if updated else "fixed"], check=True, capture_output=True)
        for d, var in ((f"{pre}_c", "SHIFT_CODE=0x1000"), (f"{pre}_d", "SHIFT_DATA=0x1000")):
            subprocess.run(["make", "-s", f"BUILD={d}"] + flags + [var, f"{d}/dkp.gba"], check=True, capture_output=True)
    else:
        subprocess.run(["make", "-s", "compare"], check=True)
        subprocess.run(["make", "-s", "shifted", "SHIFT_CODE=0x1000"], check=True, capture_output=True)
        subprocess.run(["make", "-s", "shifted", "SHIFT_DATA=0x1000"], check=True, capture_output=True)
    bad = []
    h = {name: frontend(romtest, rom) for name, rom in ROMS.items()}
    diff = [n for n in h if h[n] != h["original"]]
    print("front-end tour: " + ("OK" if not diff else f"differs ({', '.join(diff)})"))
    if diff:
        bad.append("front-end")
    for t in range(first, last + 1):
        h = {name: run(romtest, rom, t) for name, rom in ROMS.items()}
        diff = [n for n in h if h[n] != h["original"]]
        if diff:
            note = KNOWN.get(t, "UNEXPECTED")
            print(f"track {t:2d}: differs ({', '.join(diff)}) - {note}")
            if t not in KNOWN:
                bad.append(t)
    n = last - first + 1
    print(f"{n - len([b for b in bad if b != 'front-end'])}/{n} tracks OK" + (f"; unexpected: {bad}" if bad else ""))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

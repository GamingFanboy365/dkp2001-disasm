"""Results theme (updates patch): an original island reggae tune for the RESULTS screen.

Written for this project from scratch (melody, bass, chords and drums), not an
arrangement of any existing tune, in the style of the build's own race tunes (NOTES.md:
modal vamp harmony, a long loop of varied 8-bar sections, busy staccato ostinato under a
sparser lead, the lead harmonised in parallel thirds on its repeats, wide velocities).
G mixolydian, 92 bpm: off-beat guitar skank, a 16th muted-guitar ostinato, a fretless bass
that falls at phrase ends, a one-drop groove with ghosted hats, and a bell melody. A two-
bar intro, then a 32-bar loop: A, A' (harmonised), B, A'' (harmonised, busier).
Played with the instruments Rare's race tunes use (vgroup0).

Build: python3 tools/song_build.py updates/music/results.py [--midi results.mid]
"""
NAME = "results"
TEMPO = 92

A = ["G", "G", "F", "G", "G", "G", "C", "D"]
B = ["C", "C", "G", "G", "Am", "Am", "F", "D"]
INTRO = ["G", "G"]
LOOP = A + A + B + A

SCALE = [7, 9, 11, 0, 2, 4, 5]                       # G mixolydian, as pitch classes
SKANK = {"G": "B4+D5", "F": "A4+C5", "C": "C5+E5", "D": "A4+D5", "Am": "C5+E5"}
BASS = {"G": ("G1", "D2"), "F": ("F1", "C2"), "C": ("C2", "G2"), "D": ("D2", "A2"), "Am": ("A1", "E2")}
RIFF = {"G": ("G3", "B3", "D4"), "F": ("F3", "A3", "C4"), "C": ("G3", "C4", "E4"),
        "D": ("F#3", "A3", "D4"), "Am": ("A3", "C4", "E4")}


def skank(ch):
    c = SKANK[ch]
    return f"r:2 {c}:2 r:2 {c}:2 r:2 {c}:2 r:2 {c}:2"


def riff(ch, busy=False):
    """A staccato 16th figure on the chord, like the race tunes' ostinatos."""
    a, b, c = RIFF[ch]
    if busy:
        return f"{a}:1 {a}:1 {b}:1 {c}:1 {b}:1 {a}:1 {b}:1 {c}:1 {a}:1 {a}:1 {b}:1 {c}:1 {b}:1 {c}:1 {b}:1 {a}:1"
    return f"{a}:1 r:1 {b}:1 {c}:1 r:2 {b}:1 r:1 {a}:1 r:1 {b}:1 {c}:1 r:2 {c}:1 r:1"


def bassline(ch):
    r, f = BASS[ch]
    return f"{r}:3 r:1 {r}:2 {f}:2 r:2 {r}:2 {f}:4"


def key_number(name):
    n = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[name[0]]
    i = 1
    while name[i] in "#b":
        n += 1 if name[i] == "#" else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def key_name(n):
    return ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"][n % 12] + str(n // 12 - 1)


def third_below(bar, scale=None):
    """The same line two scale steps lower (parallel thirds), for the harmony track."""
    scale = scale or SCALE
    out = []
    for tok in bar.split():
        name, ln = tok.split(":")
        if name == "r":
            out.append(tok)
            continue
        m = key_number(name) - 1
        steps = 0
        while True:
            if m % 12 in scale:
                steps += 1
                if steps == 2:
                    break
            m -= 1
        out.append(f"{key_name(m)}:{ln}")
    return " ".join(out)


ONE_DROP = {
    36: "........x.......",
    38: "........x.......",
    42: "x.oox.o.x.oox.o.",                               # hats: accents and ghosts
    40: "..............o.",
}
FILL = {
    36: "........x.......",
    38: "........x.o.x.xx",
    45: "......x.........",
    43: "...........x....",
    42: "x.oox.o.........",
}
CRASH = {**ONE_DROP, 57: "x..............."}

MEL_A = [
    "B5:4 D6:2 B5:2 A5:6 G5:2",
    "F5:2 G5:2 A5:4 G5:8",
    "F5:4 A5:2 C6:2 A5:4 F5:4",
    "G5:2 A5:2 B5:2 D6:2 B5:8",
    "D6:4 E6:2 D6:2 B5:4 G5:4",
    "A5:2 B5:2 A5:2 F5:2 G5:8",
    "E5:2 G5:2 C6:4 B5:2 A5:2 G5:4",
    "F#5:4 A5:4 D6:6 C6:2",
]
MEL_A3 = MEL_A[:6] + ["E5:2 G5:2 C6:4 E6:4 C6:4", "D6:4 C6:2 A5:2 F#5:4 A5:4"]
MEL_B = [
    "E6:6 D6:2 C6:4 G5:4",
    "A5:2 C6:2 E6:4 D6:8",
    "D6:4 B5:2 G5:2 D6:4 B5:4",
    "G5:2 A5:2 B5:4 r:8",
    "C6:4 E6:2 C6:2 A5:6 C6:2",
    "B5:2 A5:2 E5:4 r:8",
    "F5:2 A5:2 C6:4 F6:4 C6:4",
    "D6:6 C6:2 A5:4 F#5:4",
]

TRACKS = [
    {"channel": 0, "program": 9, "volume": 110, "velocity": 108, "gate": 0.75,
     "intro": [None, None], "loop": MEL_A + MEL_A + MEL_B + MEL_A3},
    {"channel": 5, "program": 9, "volume": 84, "velocity": 92, "gate": 0.75,
     "intro": [None, None], "loop": [None] * 8 + [third_below(b) for b in MEL_A] + [None] * 8
                                     + [third_below(b) for b in MEL_A3]},
    {"channel": 1, "program": 27, "volume": 80, "velocity": 96, "gate": 0.45,
     "intro": [skank("G"), skank("G")], "loop": [skank(c) for c in LOOP]},
    {"channel": 4, "program": 28, "volume": 62, "velocity": 86, "gate": 0.5,
     "intro": [None, riff("G")], "loop": [riff(c) for c in A + A + B] + [riff(c, True) for c in A]},
    {"channel": 3, "program": 35, "volume": 124, "velocity": 120, "gate": 0.85, "long": 4, "fall": 1400,
     "intro": [bassline("G"), bassline("G")], "loop": [bassline(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 100, "velocity": 100, "gate": 1.0,
     "intro": [ONE_DROP, FILL],
     "loop": [CRASH] + [ONE_DROP] * 6 + [FILL] + [ONE_DROP] * 7 + [FILL]
             + [CRASH] + [ONE_DROP] * 6 + [FILL] + [CRASH] + [ONE_DROP] * 6 + [FILL]},
]

"""Final results theme when the player didn't win the cup (updates patch): an original,
gentle "good try" tune. The winning theme is final_results.py.

Written for this project from scratch, not an arrangement of any existing tune.
G major, 96 bpm, warm and easy-going rather than sad: a music-box melody over nylon
guitar picking, soft contrabass, brushed hats and a light kick, a two-bar intro then a
16-bar loop that lifts at the end of each phrase. Played with the instruments Rare's
race tunes use (vgroup0).

Build: python3 tools/song_build.py updates/music/final_results_runner_up.py [--midi f.mid]
"""
NAME = "final_runner_up"
TEMPO = 96

CHORDS = ["G", "Em", "C", "D", "G", "Em", "Am", "D",
          "Em", "C", "G", "D", "C", "D", "G", "G"]
INTRO = ["G", "D"]
LOOP = CHORDS

PICK = {"G": ("G3", "D4", "G4", "B4"), "Em": ("E3", "B3", "E4", "G4"), "C": ("C3", "G3", "C4", "E4"),
        "D": ("D3", "A3", "D4", "F#4"), "Am": ("A2", "E3", "A3", "C4")}
ROOT = {"G": "G1", "Em": "E2", "C": "C2", "D": "D2", "Am": "A1"}


def picking(ch):
    a, b, c, d = PICK[ch]
    return f"{a}:2 {b}:2 {c}:2 {d}:2 {c}:2 {b}:2 {c}:2 {d}:2"


def bass(ch):
    return f"{ROOT[ch]}:6 {ROOT[ch]}:2 r:4 {ROOT[ch]}:4"


GROOVE = {36: "x.......x.......", 42: "o.o.o.o.o.o.o.o.", 54: "....o.......o..."}
LIFT = {36: "x.......x...x...", 42: "o.o.o.o.o.o.o.o.", 54: "....o.......o.o.", 81: "x..............."}

MELODY = [
    "B5:4 D6:2 B5:2 A5:4 G5:4",
    "G5:2 A5:2 B5:4 E5:8",
    "E5:2 G5:2 C6:4 B5:2 A5:2 G5:4",
    "F#5:4 A5:4 D6:8",
    "D6:4 B5:2 G5:2 A5:4 B5:4",
    "G5:2 F#5:2 E5:4 B5:6 A5:2",
    "A5:4 C6:2 A5:2 E5:4 A5:4",
    "F#5:8 r:4 D5:4",
    "E5:4 G5:2 B5:2 E6:6 D6:2",
    "C6:4 B5:2 A5:2 G5:4 E5:4",
    "D5:2 G5:2 B5:4 D6:4 B5:4",
    "A5:6 B5:2 F#5:8",
    "E5:2 G5:2 C6:4 E6:4 C6:4",
    "D6:4 C6:2 B5:2 A5:4 F#5:4",
    "G5:6 B5:2 D6:4 B5:4",
    "G5:12 r:4",
]

TRACKS = [
    {"channel": 0, "program": 10, "volume": 108, "pan": 64, "velocity": 106, "gate": 0.8,
     "intro": [None, None], "loop": MELODY},
    {"channel": 1, "program": 24, "volume": 82, "pan": 40, "velocity": 92, "gate": 0.7,
     "intro": [picking("G"), picking("D")], "loop": [picking(c) for c in CHORDS]},
    {"channel": 3, "program": 43, "volume": 104, "pan": 64, "velocity": 104, "gate": 0.8,
     "intro": [bass("G"), bass("D")], "loop": [bass(c) for c in CHORDS]},
    {"channel": 2, "program": 127, "volume": 84, "pan": 64, "velocity": 84, "gate": 1.0,
     "intro": [None, GROOVE], "loop": ([GROOVE] * 7 + [LIFT]) * 2},
]

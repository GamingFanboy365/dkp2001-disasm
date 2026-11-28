"""Final results theme (updates patch): an original victory anthem for the end of a cup.

Written for this project from scratch, not an arrangement of any existing tune.
C major, 108 bpm: a two-bar fanfare-like opening on strings over tom "timpani" and a
crash, then a proud 16-bar loop: the melody on strings, organ chords, contrabass,
a march snare, and tubular-bell accents at the ends of phrases. Played with the
instruments Rare's race tunes use (vgroup0).

Build: python3 tools/song_build.py updates/music/final_results.py [--midi final.mid]
"""
NAME = "final_results"
TEMPO = 108

CHORDS = ["C", "F", "G", "C", "Am", "F", "D", "G",
          "C", "F", "G", "Em", "F", "G", "C", "C"]
INTRO = ["C", "G"]
LOOP = CHORDS

ORGAN = {"C": "E4+G4", "F": "F4+A4", "G": "D4+G4", "Am": "E4+A4",   # two notes: the driver
         "D": "F#4+A4", "Em": "E4+G4"}                              # mixes 8 voices
ROOTS = {"C": "C2", "F": "F1", "G": "G1", "Am": "A1", "D": "D2", "Em": "E2"}
FIFTHS = {"C": "G2", "F": "C2", "G": "D2", "Am": "E2", "D": "A2", "Em": "B2"}


def organ(ch):
    return f"{ORGAN[ch]}:8 {ORGAN[ch]}:8"


def bass(ch):
    return f"{ROOTS[ch]}:4 {FIFTHS[ch]}:4 {ROOTS[ch]}:4 {FIFTHS[ch]}:2 {ROOTS[ch]}:2"


MARCH = {
    36: "x.......x.......",
    38: "....x..o....x.oo",
    42: "o.o.o.o.o.o.o.o.",
}
ROLL = {
    36: "x.......x.......",
    38: "....x...xoxoxxxx",
    57: "................",
}
OPENING = [
    {36: "x.......x.......", 41: "x...x...x.x.x.xx", 57: "x..............."},
    {36: "x.......x...x...", 45: "x.x.x.x.........", 43: "........x.x.x.x.", 57: "x..............."},
]
LOOP_DRUMS = ([{**MARCH, 57: "x..............."}] + [MARCH] * 6 + [ROLL]
              + [{**MARCH, 57: "x..............."}] + [MARCH] * 6 + [{**ROLL, 57: "x..............."}])

MELODY = [
    "C5:4 E5:2 G5:2 C6:6 B5:2",
    "A5:4 C6:4 F5:8",
    "G5:2 A5:2 B5:2 D6:2 G6:6 F6:2",
    "E6:8 C6:8",
    "E6:4 D6:2 C6:2 A5:6 C6:2",
    "F6:4 E6:2 D6:2 C6:4 A5:4",
    "F#5:2 A5:2 D6:4 C6:2 A5:2 F#5:4",
    "G5:8 r:4 D6:4",
    "E6:4 G6:2 E6:2 C6:6 E6:2",
    "F6:4 A6:4 F6:4 C6:4",
    "D6:4 B5:2 G5:2 D6:4 G6:4",
    "E6:6 D6:2 B5:4 G5:4",
    "A5:4 C6:2 F6:2 E6:4 D6:4",
    "D6:2 E6:2 F6:2 D6:2 B5:4 G5:4",
    "C6:6 G5:2 E5:2 G5:2 C6:4",
    "C6:12 r:4",
]
BELLS = [None, None, None, "C6:16", None, None, None, "G5:16",
         None, None, None, "E5:16", None, None, "C6:16", None]
FANFARE = ["G4+C5:2 G4+C5:2 G4+C5:2 E5:2 G5:8", "D5+G5:2 D5+G5:2 D5+G5:2 B5:2 D6:8"]

TRACKS = [
    {"channel": 0, "program": 40, "volume": 116, "pan": 64, "velocity": 112, "gate": 0.9,
     "intro": FANFARE, "loop": MELODY},
    {"channel": 1, "program": 19, "volume": 70, "pan": 40, "velocity": 84, "gate": 0.95,
     "intro": [organ("C"), organ("G")], "loop": [organ(c) for c in CHORDS]},
    {"channel": 3, "program": 43, "volume": 120, "pan": 64, "velocity": 116, "gate": 0.8,
     "intro": [bass("C"), bass("G")], "loop": [bass(c) for c in CHORDS]},
    {"channel": 2, "program": 127, "volume": 104, "pan": 64, "velocity": 104, "gate": 1.0,
     "intro": OPENING, "loop": LOOP_DRUMS},
    {"channel": 4, "program": 14, "volume": 82, "pan": 92, "velocity": 100, "gate": 0.95,
     "intro": [None, None], "loop": BELLS},
]

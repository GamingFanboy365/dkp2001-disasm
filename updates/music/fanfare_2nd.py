"""Finish fanfare for 2nd place (updates patch): a variation of the 1st place fanfare.

Written for this project (see fanfare_1st.py). The same rising call, then the answer
settles instead of climbing: F, then G, home to C an octave lower, with no crash at
the end. Same instruments, a touch quieter. Played once.

Build: python3 tools/song_build.py updates/music/fanfare_2nd.py [--midi f2.mid]
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("_results", os.path.join(os.path.dirname(__file__), "results.py"))
_r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r)
MAJOR = [0, 2, 4, 5, 7, 9, 11]

NAME = "fanfare_2nd"
TEMPO = 160
ONCE = True
INTRO = []
LOOP = ["C", "F", "G", "C"]

LEAD = [
    "G4:2 C5:2 E5:2 G5:2 C6:4 G5:2 C6:2",
    "A5:2 G5:2 F5:2 A5:2 C6:4 A5:2 F5:2",
    "G5:2 F5:2 E5:2 D5:2 B4:4 D5:4",
    "C5:12 r:4",
]
PAD = ["E4+G4:4 r:4 E4+G4:4 r:4", "F4+A4:4 r:4 F4+A4:4 r:4", "D4+G4:4 r:4 D4+F4:4 r:4", "E4+G4:12 r:4"]
BASS = ["C2:4 G1:2 C2:2 C2:4 G2:4", "F1:4 C2:2 F1:2 F1:4 A1:4", "G1:4 D2:2 G1:2 G1:4 B1:4", "C2:12 r:4"]
DRUMS = [
    {36: "x.......x.......", 38: "....x..o....x.o.", 42: "o.o.o.o.o.o.o.o.", 57: "x..............."},
    {36: "x.......x.......", 38: "....x..o....x.o.", 42: "o.o.o.o.o.o.o.o."},
    {36: "x.......x.......", 38: "....x.......x.xx", 42: "o.o.o.o.o.o....."},
    {36: "x...............", 51: "x..............."},
]

TRACKS = [
    {"channel": 0, "program": 41, "volume": 112, "velocity": 110, "gate": 0.9, "long": 6,
     "vibrato": 48, "loop": LEAD},
    {"channel": 5, "program": 40, "volume": 86, "velocity": 96, "gate": 0.9, "long": 6, "vibrato": 36,
     "loop": [_r.third_below(b, MAJOR) for b in LEAD]},
    {"channel": 1, "program": 19, "volume": 64, "velocity": 88, "gate": 0.8, "loop": PAD},
    {"channel": 3, "program": 43, "volume": 118, "velocity": 112, "gate": 0.8, "loop": BASS},
    {"channel": 2, "program": 127, "volume": 96, "velocity": 100, "gate": 1.0, "loop": DRUMS},
]

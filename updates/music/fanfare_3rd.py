"""Finish fanfare for 3rd place (updates patch): a shorter variation of the 1st place one.

Written for this project (see fanfare_1st.py). The rising call, cut short, then a
bittersweet turn through Ab and G (bVI-V, borrowed from C minor) before landing on C.
Three bars, lighter drums. Played once.

Build: python3 tools/song_build.py updates/music/fanfare_3rd.py [--midi f3.mid]
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("_results", os.path.join(os.path.dirname(__file__), "results.py"))
_r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r)
MIXED = [0, 2, 3, 5, 7, 8, 11]                       # C harmonic minor, for the turn

NAME = "fanfare_3rd"
TEMPO = 160
ONCE = True
INTRO = []
LOOP = ["C", "Ab", "C"]

LEAD = [
    "G4:2 C5:2 E5:2 G5:2 C6:4 G5:4",
    "Ab5:2 G5:2 F5:2 Eb5:2 D5:4 B4:4",
    "C5:12 r:4",
]
HARM = [
    "E4:2 G4:2 C5:2 E5:2 G5:4 E5:4",
    "F5:2 Eb5:2 D5:2 C5:2 B4:4 G4:4",
    "G4:12 r:4",
]
PAD = ["E4+G4:4 r:4 E4+G4:4 r:4", "Eb4+Ab4:4 r:4 D4+G4:4 r:4", "E4+G4:12 r:4"]
BASS = ["C2:4 G1:2 C2:2 C2:4 G2:4", "Ab1:4 Eb2:2 Ab1:2 G1:4 D2:4", "C2:12 r:4"]
DRUMS = [
    {36: "x.......x.......", 38: "....x.......x...", 42: "o.o.o.o.o.o.o.o."},
    {36: "x.......x.......", 38: "....x.......x.o.", 42: "o.o.o.o.o.o.o.o."},
    {36: "x...............", 51: "x..............."},
]

TRACKS = [
    {"channel": 0, "program": 41, "volume": 110, "velocity": 108, "gate": 0.9, "long": 6,
     "vibrato": 48, "loop": LEAD},
    {"channel": 5, "program": 40, "volume": 84, "velocity": 94, "gate": 0.9, "long": 6, "vibrato": 36,
     "loop": HARM},
    {"channel": 1, "program": 19, "volume": 62, "velocity": 86, "gate": 0.8, "loop": PAD},
    {"channel": 3, "program": 43, "volume": 116, "velocity": 110, "gate": 0.8, "loop": BASS},
    {"channel": 2, "program": 127, "volume": 92, "velocity": 96, "gate": 1.0, "loop": DRUMS},
]

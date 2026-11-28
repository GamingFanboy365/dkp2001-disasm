"""Finish fanfare for 1st place (updates patch): an original fanfare, played once.

Written for this project from scratch, not an arrangement of any existing tune. C
mixolydian at 160 bpm, four bars: a rising call on C, an answer over F, the climb
over Bb (the bVII-I cadence of the build's race tunes) and a held C chord with a crash.
Viola lead with a violin a third below, an organ chord pad, contrabass, march drums.
Its motif is shared by the 2nd and 3rd place fanfares (fanfare_2nd.py, fanfare_3rd.py).

Build: python3 tools/song_build.py updates/music/fanfare_1st.py [--midi f1.mid]
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("_results", os.path.join(os.path.dirname(__file__), "results.py"))
_r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r)
MIXO = [0, 2, 4, 5, 7, 9, 10]                         # C mixolydian

NAME = "fanfare_1st"
TEMPO = 160
ONCE = True
INTRO = []
LOOP = ["C", "F", "Bb", "C"]

LEAD = [
    "G4:2 C5:2 E5:2 G5:2 C6:4 G5:2 C6:2",
    "D6:2 C6:2 A5:2 C6:2 F6:4 C6:2 A5:2",
    "Bb5:2 A5:2 Bb5:2 D6:2 F6:4 E6:2 D6:2",
    "E6:12 r:4",
]
PAD = ["E4+G4:4 r:4 E4+G4:4 r:4", "F4+A4:4 r:4 F4+A4:4 r:4", "F4+Bb4:4 r:4 F4+D5:4 r:4", "E4+G4:12 r:4"]
BASS = ["C2:4 G1:2 C2:2 C2:4 G2:4", "F1:4 C2:2 F1:2 F1:4 A1:4", "Bb1:4 F1:2 Bb1:2 Bb1:4 D2:4", "C2:12 r:4"]
DRUMS = [
    {36: "x.......x.......", 38: "....x..o....x.o.", 42: "o.o.o.o.o.o.o.o.", 57: "x..............."},
    {36: "x.......x.......", 38: "....x..o....x.o.", 42: "o.o.o.o.o.o.o.o."},
    {36: "x.......x.......", 38: "....x...xoxoxxxx", 43: "..........x.x..."},
    {36: "x...............", 57: "x...............", 51: "....x..........."},
]

TRACKS = [
    {"channel": 0, "program": 41, "volume": 120, "velocity": 116, "gate": 0.9, "long": 6,
     "vibrato": 52, "swell": 1400, "loop": LEAD},
    {"channel": 5, "program": 40, "volume": 92, "velocity": 100, "gate": 0.9, "long": 6, "vibrato": 40,
     "loop": [_r.third_below(b, MIXO) for b in LEAD]},
    {"channel": 1, "program": 19, "volume": 70, "velocity": 92, "gate": 0.8, "loop": PAD},
    {"channel": 3, "program": 43, "volume": 122, "velocity": 118, "gate": 0.8, "loop": BASS},
    {"channel": 2, "program": 127, "volume": 104, "velocity": 106, "gate": 1.0, "loop": DRUMS},
]

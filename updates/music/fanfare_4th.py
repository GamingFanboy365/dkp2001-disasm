"""Finish jingle for 4th place (or retiring) (updates patch): an original, wry tune.

Written for this project from scratch, not an arrangement of any existing tune, and not
a variation of the podium fanfares: a good-natured "better luck next time". An
accordion sighs down chromatically over a walking-down bass (C, B, Bb, A, Ab, G), its
last note drooping with a pitch fall, then a cheeky two-note "ba-dum" on C. 132 bpm,
three bars. Played once.

Build: python3 tools/song_build.py updates/music/fanfare_4th.py [--midi f4.mid]
"""
NAME = "fanfare_4th"
TEMPO = 132
ONCE = True
INTRO = []
LOOP = ["C", "Ab", "C"]

TRACKS = [
    {"channel": 0, "program": 23, "volume": 116, "velocity": 108, "gate": 0.9, "long": 6, "fall": 1800,
     "loop": ["G5:4 F#5:4 F5:4 E5:4", "Eb5:4 D5:4 Db5:2 C5:6", "r:4 G4:1 r:1 C5:2 r:8"]},
    {"channel": 1, "program": 24, "volume": 74, "velocity": 90, "gate": 0.5,
     "loop": ["r:2 E4+G4:2 r:2 E4+G4:2 r:2 E4+G4:2 r:2 E4+G4:2",
              "r:2 Eb4+Ab4:2 r:2 Eb4+Ab4:2 r:2 D4+G4:2 r:2 D4+G4:2",
              "r:4 r:1 r:1 E4+G4:2 r:8"]},
    {"channel": 3, "program": 32, "volume": 120, "velocity": 112, "gate": 0.8,
     "loop": ["C2:4 B1:4 Bb1:4 A1:4", "Ab1:8 G1:8", "r:4 G1:1 r:1 C2:2 r:8"]},
    {"channel": 2, "program": 127, "volume": 92, "velocity": 96, "gate": 1.0,
     "loop": [{36: "x.......x.......", 42: "..o...o...o...o."},
              {36: "x.......x.......", 42: "..o...o...o...o.", 38: "............o..."},
              {36: "....x...........", 38: "......x........."}]},
]

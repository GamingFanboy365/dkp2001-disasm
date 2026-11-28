"""Finish jingle for 4th place (updates patch): an original, good-natured "good try".

Written for this project from scratch, not an arrangement of any existing tune, and not a
variation of the podium fanfares. Played the way Rare's tunes are (tools/rare_idiom.py):
here the castle tune's idiom, a clavinet (program 7) tumbling down in short notes over
low strings (program 40) stepping down chromatically, then a cheeky two-note "ba-dum"
on C. C major, 120 bpm, three bars. Played once.

Build: python3 tools/song_build.py updates/music/fanfare_4th.py [--midi fanfare_4th.mid]
"""
NAME = "fanfare_4th"
TEMPO = 120
ONCE = True
INTRO = []
LOOP = ["C", "G", "C"]

TRACKS = [
    {"channel": 0, "program": 7, "volume": 118, "velocity": 108, "gate": 0.7, "accent": 12,
     "loop": ["E5:1 r:1 D5:1 r:1 C5:1 r:1 A4:1 r:1 G4:2 r:2 F#4:2 r:2", "F4:1 r:1 F4:1 E4:1 r:2 Eb4:1 r:1 D4:3 r:5",
              "r:4 G4:1:100 r:1 C5:1:127 r:9"]},
    {"channel": 1, "program": 40, "volume": 110, "velocity": 116, "gate": 0.8, "accent": 10,
     "loop": ["C3:1 r:1 C3:1 r:1 B2:1 r:1 Bb2:1 r:1 A2:2 r:2 Ab2:2 r:2", "G2:1 r:1 G2:1 G2:1 r:2 G2:1 r:1 G2:3 r:5",
              "r:4 G2:1:110 r:1 C3:1:127 r:9"]},
    {"channel": 2, "program": 127, "volume": 92, "velocity": 96, "gate": 1.0,
     "loop": [{36: "x.......x.......", 42: "x.o.x.o.x.o.x.o."}, {36: "x.......x.......", 42: "x.o.x.o.x.o....."},
              {36: "....x...........", 38: "......x........."}]},
]

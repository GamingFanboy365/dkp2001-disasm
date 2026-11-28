"""Finish fanfare for 2nd place (updates patch): a variation of the 1st place fanfare.

Written for this project from scratch, not an arrangement of any existing tune, and played
the way Rare's own tunes are (tools/rare_idiom.py, NOTES.md): here the menu tune's idiom,
an organ lead (program 18) in short accented notes, three-note stabs (program 30) on the
syncopated steps, a bass on the 3+3+2, the kit pumping. The same pickup and call, then the answer settles instead of climbing: F, then G, home to C an octave lower, closing on the ride. Played once.

Build: python3 tools/song_build.py updates/music/fanfare_2nd.py [--midi fanfare_2nd.mid]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from rare_idiom import MENU_STABS, RARE_KIT, RARE_KIT_FILL, hits, hits_bar  # noqa: E402

NAME = "fanfare_2nd"
TEMPO = 150
ONCE = True
INTRO = []
LOOP = ["C"] * 4

TRACKS = [
    {"channel": 0, "program": 18, "volume": 118, "velocity": 108, "gate": 0.8, "accent": 12,
     "loop": ['G4:1 A4:1 B4:1 D5:1 C5:2 G4:1 C5:1 r:1 E5:2 G5:4 r:1', 'F5:2 E5:1 D5:1 r:1 C5:2 A4:1 r:1 A4:2 G4:1 r:1 G4:3', 'D5:2 B4:1 G4:1 r:1 B4:2 D5:1 r:1 F5:2 D5:1 r:1 B4:2 G4:1', 'C5:3 r:3 C5:1 C5:1 C5:4 r:4']},
    {"channel": 1, "program": 30, "volume": 96, "velocity": 110, "gate": 0.9,
     "loop": [hits("E4+G4+C5", "....x.xx.xx.x..."), hits("F4+A4+C5", MENU_STABS), hits("D4+G4+B4", MENU_STABS), hits("E4+G4+C5", "x.....x.........")]},
    {"channel": 3, "program": 43, "volume": 120, "velocity": 116, "gate": 0.8,
     "loop": ['r:4 C2:2:120 r:1 C2:1:100 G1:2:110 r:2 C2:2:118 r:2', 'F1:2:122 r:1 F1:2:100 r:1 C2:2:110 F1:2:118 r:2 C2:2:100 r:2', 'G1:2 r:1 G1:2 r:1 D2:2 G1:2 r:2 D2:2 r:2', 'C2:3:120 r:3 C2:1:100 C2:1:106 C2:4:116 r:4']},
    {"channel": 2, "program": 127, "volume": 100, "velocity": 104, "gate": 1.0,
     "loop": [{36: "....x...x...x...", 38: "......o...o...o.", 42: "....xoooxoooxooo", 57: "....x..........."}, RARE_KIT, RARE_KIT_FILL, {36: "x.....x.........", 51: "x..............."}]},
]

"""Finish fanfare for 1st place (updates patch): an original fanfare.

Written for this project from scratch, not an arrangement of any existing tune, and played
the way Rare's own tunes are (tools/rare_idiom.py, NOTES.md): here the menu tune's idiom,
an organ lead (program 18) in short accented notes, three-note stabs (program 30) on the
syncopated steps, a bass on the 3+3+2, the kit pumping. C major, 150 bpm, four bars inside the 6 s before the race hands over: a quick pickup into a proud call, an answer over F, the climb over Bb (the bVII-I of the build's race tunes) to C hit three times with a crash. Played once.

Build: python3 tools/song_build.py updates/music/fanfare_1st.py [--midi fanfare_1st.mid]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from rare_idiom import MENU_STABS, RARE_KIT, RARE_KIT_FILL, hits, hits_bar  # noqa: E402

NAME = "fanfare_1st"
TEMPO = 150
ONCE = True
INTRO = []
LOOP = ["C"] * 4

TRACKS = [
    {"channel": 0, "program": 18, "volume": 118, "velocity": 108, "gate": 0.8, "accent": 12,
     "loop": ['G4:1 A4:1 B4:1 D5:1 C5:2 G4:1 C5:1 r:1 E5:2 G5:4 r:1', 'F5:2 E5:1 D5:1 r:1 F5:2 A5:1 r:1 A5:2 G5:1 F5:1 G5:3', 'Bb5:2 A5:1 G5:1 r:1 F5:2 G5:1 r:1 A5:2 B5:1 r:1 B5:2 D6:1', 'C6:3 r:3 C6:1 C6:1 C6:4 r:4']},
    {"channel": 1, "program": 30, "volume": 96, "velocity": 110, "gate": 0.9,
     "loop": [hits("E4+G4+C5", "....x.xx.xx.x..."), hits("F4+A4+C5", MENU_STABS), hits_bar(("F4+Bb4+D5", "x.x...xx"), ("G4+B4+D5", ".xx.x...")), hits("E4+G4+C5", "x.....xx........")]},
    {"channel": 3, "program": 43, "volume": 120, "velocity": 116, "gate": 0.8,
     "loop": ['r:4 C2:2:120 r:1 C2:1:100 G1:2:110 r:2 C2:2:118 r:2', 'F1:2:122 r:1 F1:2:100 r:1 C2:2:110 F1:2:118 r:2 C2:2:100 r:2', 'Bb1:2 r:1 Bb1:2 r:1 F1:2 G1:2 r:1 G1:2 r:1 D2:2', 'C2:3:124 r:3 C2:1:110 C2:1:116 C2:4:127 r:4']},
    {"channel": 2, "program": 127, "volume": 100, "velocity": 104, "gate": 1.0,
     "loop": [{36: "....x...x...x...", 38: "......o...o...o.", 42: "....xoooxoooxooo", 57: "....x..........."}, RARE_KIT, RARE_KIT_FILL, {36: "x.....xx........", 38: "......xx........", 57: "x..............."}]},
]

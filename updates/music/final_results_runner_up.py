"""Final results theme when the player didn't win the cup (updates patch): an original,
warm "good try" tune. The winning theme is final_results.py.

Written for this project from scratch, not an arrangement of any existing tune. Played the
way Rare's own tunes are (tools/rare_idiom.py, NOTES.md): here the castle tune's idiom, a
clavinet lead (program 7) in short accented notes, a quiet sixteenth shimmer of strings
(program 41, soft, as the castle tune has it), guitar chops (program 27) on the off-beats,
punchy low strings (program 40) for the bass, a light kit. A minor turning to C major,
118 bpm, easy-going rather than sad. A two-bar intro, then a 16-bar loop: A in A minor,
B lifting into C.

Build: python3 tools/song_build.py updates/music/final_results_runner_up.py [--midi f.mid]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from rare_idiom import OFFBEATS, hits  # noqa: E402

NAME = "final_runner_up"
TEMPO = 118

A = ["Am", "F", "C", "G", "Am", "F", "G", "E"]
B = ["C", "G", "Am", "F", "C", "G", "F", "E"]
INTRO = ["Am", "E"]
LOOP = A + B

TONES = {"Am": ("A4", "C5", "E5"), "F": ("F4", "A4", "C5"), "C": ("G4", "C5", "E5"), "G": ("G4", "B4", "D5"),
         "E": ("G#4", "B4", "E5")}
CHOP = {"Am": "C4+E4", "F": "C4+F4", "C": "C4+E4", "G": "B3+D4", "E": "B3+E4"}
ROOT = {"Am": ("A2", "E2"), "F": ("F2", "C3"), "C": ("C3", "G2"), "G": ("G2", "D3"), "E": ("E2", "B2")}
KIT = {36: "x.......x.......", 38: "....o.......o...", 42: "x.o.x.o.x.o.x.o."}
KIT_TURN = {36: "x.......x.......", 38: "....o.......o.oo", 42: "x.o.x.o.x.o....."}


def shimmer(ch):
    a, b, c = TONES[ch]
    return " ".join(f"{n}:1:{v}" for n, v in zip([a, b, c, b] * 4, [52, 40, 46, 40] * 4))


def bass(ch):
    r, f = ROOT[ch]
    return f"{r}:1:127 r:1 {r}:1:104 r:1 {f}:2:118 r:2 {r}:1:124 r:1 {f}:1:104 r:1 {r}:2:116 r:2"


MEL_A = [
    "E5:1 r:1 A5:1 r:1 C6:2 B5:1 r:1 A5:2 E5:1 r:1 C5:2 E5:2",
    "F5:2 E5:1 C5:1 r:2 A4:1 C5:1 r:2 F5:2 E5:2 r:2",
    "G5:1 r:1 E5:1 r:1 C5:2 E5:1 r:1 G5:2 C6:1 r:1 B5:2 G5:2",
    "D5:2 B4:1 G4:1 r:2 B4:1 D5:1 r:2 G5:6",
    "E5:1 r:1 A5:1 r:1 C6:2 B5:1 r:1 A5:2 E5:1 r:1 C5:2 E5:2",
    "F5:2 A5:1 C6:1 r:2 A5:1 F5:1 r:2 C5:2 F5:4",
    "G5:1 r:1 B5:1 r:1 D6:2 B5:1 r:1 G5:2 F5:1 D5:1 r:2 B4:2",
    "G#5:2 E5:1 B4:1 r:2 D5:1 E5:1 r:2 E5:6",
]
MEL_B = [
    "C6:2 G5:1 E5:1 r:2 G5:1 C6:1 r:2 E6:6",
    "D6:2 B5:1 G5:1 r:2 B5:1 D6:1 r:2 G5:6",
    "C6:1 r:1 B5:1 r:1 A5:2 E5:1 r:1 A5:2 C6:1 r:1 E6:4",
    "D6:2 C6:1 A5:1 r:2 F5:1 A5:1 r:2 C6:6",
    "E6:1 r:1 D6:1 r:1 C6:2 G5:1 r:1 E5:2 G5:1 r:1 C6:4",
    "B5:2 A5:1 G5:1 r:2 D5:1 G5:1 r:2 B5:6",
    "A5:1 r:1 C6:1 r:1 F6:2 E6:1 r:1 D6:2 C6:1 r:1 A5:4",
    "G#5:2 B5:1 E6:1 r:2 D6:1 B5:1 r:2 G#5:6",
]

TRACKS = [
    {"channel": 0, "program": 7, "volume": 114, "velocity": 104, "gate": 0.75, "accent": 12,
     "intro": [None, None], "loop": MEL_A + MEL_B},
    {"channel": 4, "program": 41, "volume": 72, "velocity": 50, "gate": 0.9,
     "intro": [shimmer("Am"), shimmer("E")], "loop": [shimmer(c) for c in LOOP]},
    {"channel": 1, "program": 27, "volume": 84, "velocity": 104,
     "intro": [None, hits(CHOP["E"], OFFBEATS, 108, 84)], "loop": [hits(CHOP[c], OFFBEATS, 108, 84) for c in LOOP]},
    {"channel": 3, "program": 40, "volume": 112, "velocity": 120, "gate": 0.8,
     "intro": [bass("Am"), bass("E")], "loop": [bass(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 88, "velocity": 96, "gate": 1.0,
     "intro": [KIT, KIT_TURN], "loop": [KIT] * 7 + [KIT_TURN] + [KIT] * 7 + [KIT_TURN]},
]

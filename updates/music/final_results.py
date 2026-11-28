"""Final results theme when the player wins the cup (updates patch): an original anthem.

Written for this project from scratch, not an arrangement of any existing tune. Played
the way Rare's own tunes are (tools/rare_idiom.py, NOTES.md): here the menu tune's idiom,
an organ lead (program 18) in short accented notes, three-note stabs (program 30) on the
syncopated steps, a short held counter-line (program 19), a bass on the 3+3+2, the kit
pumping. C mixolydian, 132 bpm, heroic: the A section ends on the bVII-I cadence (Bb to
C), B climbs Ab-Bb-C. A two-bar intro, then a 24-bar loop: A, B, A.

Build: python3 tools/song_build.py updates/music/final_results.py [--midi final_results.mid]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from rare_idiom import MENU_STABS, hits  # noqa: E402

NAME = "final_results"
TEMPO = 132

A = ["C", "C", "Bb", "C", "F", "F", "Bb", "C"]
B = ["Ab", "Ab", "Bb", "Bb", "Ab", "Bb", "C", "C"]
INTRO = ["C", "Bb"]
LOOP = A + B + A

STAB = {"C": "E4+G4+C5", "Bb": "D4+F4+Bb4", "F": "F4+A4+C5", "Ab": "Eb4+Ab4+C5"}
ROOT = {"C": ("C2", "G1"), "Bb": ("Bb1", "F1"), "F": ("F1", "C2"), "Ab": ("Ab1", "Eb2")}
COUNTER = {"C": ("C5", "G4"), "Bb": ("Bb4", "F4"), "F": ("A4", "C5"), "Ab": ("Ab4", "Eb4")}
KIT = {36: "x...x...x...x...", 38: "..o...o...o...o.", 42: "xoooxoooxoooxooo"}
KIT_FILL = {36: "x...x...x...x...", 38: "..o...o...xoxoxx", 42: "xoooxoooxooo....", 45: "........x.......",
            43: "..........x....."}
KIT_CRASH = {**KIT, 57: "x..............."}


def bass(ch):
    r, f = ROOT[ch]
    return f"{r}:2:124 r:1 {r}:2:100 r:1 {f}:2:114 r:2 {r}:2:120 r:4"


def counter(ch):
    a, b = COUNTER[ch]
    return f"r:4 {a}:2:118 r:8 {b}:2:106"                    # between the stabs


MEL_A = [
    "C5:1 r:1 E5:1 r:1 G5:2 E5:1 r:1 G5:2 C6:1 r:1 C6:2 G5:2",
    "Bb5:2 G5:1 E5:1 r:2 G5:1 Bb5:1 r:2 C6:4 r:2",
    "D6:1 r:1 Bb5:1 r:1 F5:2 Bb5:1 r:1 D6:2 C6:1 Bb5:1 r:2 F5:2",
    "G5:2 E5:1 C5:1 r:2 E5:1 G5:1 r:2 C6:6",
    "A5:1 r:1 C6:1 r:1 F6:2 C6:1 r:1 A5:2 C6:1 A5:1 r:2 F5:2",
    "G5:2 A5:1 C6:1 r:2 A5:1 G5:1 r:2 F5:2 A5:4",
    "Bb5:1 r:1 D6:1 r:1 F6:2 D6:1 r:1 Bb5:2 C6:1 D6:1 r:2 F6:2",
    "E6:2 D6:1 C6:1 r:2 Bb5:1 G5:1 r:2 C6:6",
]
MEL_B = [
    "C6:1 r:1 Eb6:1 r:1 Ab5:2 C6:1 r:1 Eb6:2 F6:1 Eb6:1 r:2 C6:2",
    "Eb6:2 C6:1 Ab5:1 r:2 C6:1 Eb6:1 r:2 Ab5:6",
    "D6:1 r:1 F6:1 r:1 Bb5:2 D6:1 r:1 F6:2 G6:1 F6:1 r:2 D6:2",
    "F6:2 D6:1 Bb5:1 r:2 D6:1 F6:1 r:2 Bb5:6",
    "Ab5:2 G5:1 F5:1 r:2 Eb5:1 C5:1 r:2 Ab5:2 C6:4",
    "Bb5:2 C6:1 D6:1 r:2 F6:1 D6:1 r:2 Bb5:2 D6:4",
    "E6:1 r:1 G6:1 r:1 C6:2 G5:1 r:1 E6:2 G6:1 E6:1 r:2 C6:2",
    "G6:2 E6:1 C6:1 r:2 G5:1 C6:1 r:2 C6:6",
]
FANFARE = ["G4:1 A4:1 B4:1 D5:1 C5:2 G4:1 C5:1 r:1 E5:2 G5:4 r:1", "F5:2 D5:1 Bb4:1 r:1 D5:2 F5:1 r:1 Bb5:7"]

TRACKS = [
    {"channel": 0, "program": 18, "volume": 116, "velocity": 106, "gate": 0.8, "accent": 12,
     "intro": FANFARE, "loop": MEL_A + MEL_B + MEL_A},
    {"channel": 1, "program": 30, "volume": 92, "velocity": 110, "gate": 0.9,
     "intro": [hits(STAB["C"], "....x.xx.xx.x..."), hits(STAB["Bb"], MENU_STABS)],
     "loop": [hits(STAB[c], MENU_STABS) for c in LOOP]},
    {"channel": 4, "program": 19, "volume": 80, "velocity": 110, "gate": 0.9,
     "intro": [None, None], "loop": [counter(c) for c in LOOP]},
    {"channel": 3, "program": 43, "volume": 120, "velocity": 116, "gate": 0.8,
     "intro": [bass("C"), bass("Bb")], "loop": [bass(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 100, "velocity": 104, "gate": 1.0,
     "intro": [KIT, KIT_FILL],
     "loop": [KIT_CRASH] + [KIT] * 6 + [KIT_FILL] + [KIT_CRASH] + [KIT] * 6 + [KIT_FILL]
             + [KIT_CRASH] + [KIT] * 6 + [KIT_FILL]},
]

"""BEST TIMES theme (updates patch): an original chill jungle reggae for the Clock Race
best-times chart.

Written for this project from scratch (melody, bass, chords and drums), not an
arrangement of any existing tune, and its own piece (not the RESULTS reggae or the jungle
race theme). Played the way Rare's own tunes are (tools/rare_idiom.py, NOTES.md): here the
bayou tune's idiom, played softly as it is there: a muted-guitar lead (program 28) in
short accented notes, doubled a third below on the repeats, soft three-note stabs
(program 30) on the off-beats, a nylon-guitar pluck (program 24) marking the phrases, a
short contrabass line, and a one-drop with agogo bells for the jungle. D dorian, 84 bpm.
A two-bar intro, then a 32-bar loop: A, A' (doubled), B, A'' (doubled).

Build: python3 tools/song_build.py updates/music/best_times.py [--midi best_times.mid]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from rare_idiom import OFFBEATS, hits, third_below  # noqa: E402

NAME = "best_times"
TEMPO = 84

A = ["Dm", "G", "Dm", "G", "C", "G", "Am", "Am"]
B = ["F", "C", "G", "Dm", "F", "C", "Em", "A"]
INTRO = ["Dm", "G"]
LOOP = A + A + B + A

D_DORIAN = [2, 4, 5, 7, 9, 11, 0]
STAB = {"Dm": "D4+F4+A4", "G": "D4+G4+B4", "C": "E4+G4+C5", "Am": "E4+A4+C5", "F": "F4+A4+C5",
        "Em": "E4+G4+B4", "A": "E4+A4+C#5"}
ROOT = {"Dm": ("D2", "A1"), "G": ("G1", "D2"), "C": ("C2", "G1"), "Am": ("A1", "E2"), "F": ("F1", "C2"),
        "Em": ("E2", "B1"), "A": ("A1", "E2")}
KIT = {36: "........x.......", 38: "........o.......", 42: "x.o.x.o.x.o.x.o.", 67: "x.....o...o.....",
       68: "...o.......o..o."}
KIT_FILL = {36: "........x.......", 38: "........o.o.o.oo", 45: "..........x.....", 43: "............x...",
            67: "x.....o........."}
KIT_TAMB = {**KIT, 54: "x..............."}


def bass(ch):
    r, f = ROOT[ch]
    return f"{r}:2:118 r:2 {r}:1:92 r:1 {f}:2:106 r:4 {r}:2:112 {f}:2:96"


def pluck(ch, bar):
    r = ROOT[ch][0].replace("1", "3").replace("2", "3")
    return f"{r}:2:84 r:14" if bar % 2 == 0 else "r:16"


MEL_A = [
    "A4:1 r:1 D5:1 r:1 F5:2 E5:1 r:1 D5:2 C5:1 r:1 A4:2 C5:2",
    "B4:2 D5:1 G5:1 r:2 F5:1 E5:1 r:2 D5:2 B4:4",
    "F5:1 r:1 A5:1 r:1 G5:2 F5:1 r:1 E5:2 D5:1 r:1 F5:2 A5:2",
    "G5:2 F5:1 D5:1 r:2 B4:1 D5:1 r:2 G5:6",
    "E5:1 r:1 G5:1 r:1 C6:2 B5:1 r:1 G5:2 E5:1 r:1 G5:2 E5:2",
    "D5:2 B4:1 G4:1 r:2 B4:1 D5:1 r:2 F5:2 E5:4",
    "C5:1 r:1 E5:1 r:1 A5:2 G5:1 r:1 E5:2 C5:1 r:1 E5:2 A4:2",
    "B4:2 C5:1 D5:1 r:2 E5:1 C5:1 r:2 D5:6",
]
MEL_B = [
    "C5:1 r:1 F5:1 r:1 A5:2 G5:1 r:1 F5:2 A5:1 r:1 C6:2 A5:2",
    "G5:2 E5:1 C5:1 r:2 E5:1 G5:1 r:2 C6:6",
    "B5:1 r:1 A5:1 r:1 G5:2 D5:1 r:1 G5:2 B5:1 r:1 D6:2 B5:2",
    "A5:2 F5:1 D5:1 r:2 F5:1 A5:1 r:2 D5:6",
    "C5:1 r:1 F5:1 r:1 A5:2 G5:1 r:1 F5:2 A5:1 r:1 C6:2 A5:2",
    "E5:2 G5:1 C6:1 r:2 B5:1 G5:1 r:2 E5:2 G5:4",
    "G5:1 r:1 B5:1 r:1 E6:2 D6:1 r:1 B5:2 G5:1 r:1 E5:2 G5:2",
    "C#6:2 A5:1 E5:1 r:2 A5:1 C#6:1 r:2 E6:6",
]

TRACKS = [
    {"channel": 0, "program": 28, "volume": 114, "velocity": 96, "gate": 0.8, "accent": 14,
     "intro": [None, None], "loop": MEL_A + MEL_A + MEL_B + MEL_A},
    {"channel": 5, "program": 28, "volume": 92, "velocity": 88, "gate": 0.8, "accent": 14,
     "intro": [None, None],
     "loop": [None] * 8 + [third_below(b, D_DORIAN) for b in MEL_A] + [None] * 8
             + [third_below(b, D_DORIAN) for b in MEL_A]},
    {"channel": 1, "program": 30, "volume": 76, "velocity": 64,
     "intro": [hits(STAB["Dm"], OFFBEATS, 66, 52), hits(STAB["G"], OFFBEATS, 66, 52)],
     "loop": [hits(STAB[c], OFFBEATS, 66, 52) for c in LOOP]},
    {"channel": 4, "program": 24, "volume": 80, "velocity": 84,
     "intro": [None, None], "loop": [pluck(c, i) for i, c in enumerate(LOOP)]},
    {"channel": 3, "program": 43, "volume": 120, "velocity": 112, "gate": 0.85,
     "intro": [bass("Dm"), bass("G")], "loop": [bass(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 94, "velocity": 96, "gate": 1.0,
     "intro": [KIT, KIT_FILL],
     "loop": [KIT_TAMB] + [KIT] * 6 + [KIT_FILL] + [KIT_TAMB] + [KIT] * 6 + [KIT_FILL]
             + [KIT_TAMB] + [KIT] * 6 + [KIT_FILL] + [KIT_TAMB] + [KIT] * 6 + [KIT_FILL]},
]

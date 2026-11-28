"""BEST TIMES theme (updates patch): an original chill jungle reggae for the Clock Race
best-times chart.

Written for this project from scratch (melody, bass, chords and drums), not an
arrangement of any existing tune, and its own piece (not the RESULTS reggae or the
jungle race theme). In the style of the build's race tunes (NOTES.md: modal vamp harmony,
a long loop of varied 8-bar sections, the lead harmonised in thirds on its repeats, a
falling bass at phrase ends). D dorian, 80 bpm, laid back: a nylon-guitar lead, dulcimer
chops on the off-beats like a marimba, an organ "bubble", a deep acoustic bass, and a
one-drop with agogo bells and low toms for the jungle. A two-bar intro, then a 32-bar
loop: A, A' (harmonised), B, A'' (harmonised, a higher ending).
Played with the instruments Rare's race tunes use (vgroup0).

Build: python3 tools/song_build.py updates/music/best_times.py [--midi best.mid]
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("_results", os.path.join(os.path.dirname(__file__), "results.py"))
_r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r)
DORIAN = [2, 4, 5, 7, 9, 11, 0]                       # D dorian

NAME = "best_times"
TEMPO = 80

A = ["Dm", "G", "Dm", "G", "C", "G", "Am", "Am"]
B = ["F", "C", "G", "Dm", "F", "C", "Em", "A"]
INTRO = ["Dm", "G"]
LOOP = A + A + B + A

BASS = {"Dm": ("D2", "A1"), "G": ("G1", "D2"), "C": ("C2", "G1"), "Am": ("A1", "E2"), "F": ("F1", "C2"),
        "Em": ("E2", "B1"), "A": ("A1", "E2")}
CHOP = {"Dm": "F4+A4", "G": "G4+B4", "C": "E4+G4", "Am": "E4+A4", "F": "F4+A4", "Em": "E4+G4", "A": "A4+C#5"}
BUBBLE = {"Dm": "D4", "G": "D4", "C": "E4", "Am": "C4", "F": "C4", "Em": "E4", "A": "C#4"}


def bass(ch):
    r, f = BASS[ch]
    return f"{r}:4 r:2 {f}:2 {r}:2 r:2 {f}:1 r:1 {r}:2"


def chop(ch):
    c = CHOP[ch]
    return f"r:2 {c}:2 r:2 {c}:2 r:2 {c}:2 r:2 {c}:2"


def bubble(ch):
    n = BUBBLE[ch]
    return " ".join([f"r:1 {n}:1 r:2"] * 4)


ONE_DROP = {36: "........x.......", 38: "........o.......", 67: "x.....o...o.....", 68: "...o.......o..o.",
            42: "..o...o...o...o."}
FILL = {36: "........x.......", 38: "........o.......", 45: "..........x.....", 43: "............x...",
        41: "..............x.", 67: "x.....o........."}
TAMB = {**ONE_DROP, 54: "x..............."}

MEL_A = [
    "A4:3 C5:1 D5:4 r:2 F5:2 E5:2 D5:2",
    "B4:4 G4:2 A4:2 B4:6 r:2",
    "A4:2 C5:2 D5:2 F5:2 A5:6 G5:2",
    "F5:2 E5:2 D5:4 B4:8",
    "C5:3 E5:1 G5:4 r:2 E5:2 G5:2 A5:2",
    "B5:4 A5:2 G5:2 D5:8",
    "E5:2 F5:2 E5:2 C5:2 A4:4 C5:4",
    "D5:12 r:4",
]
MEL_A3 = MEL_A[:6] + ["E5:2 G5:2 A5:2 C6:2 B5:4 A5:4", "D6:12 r:4"]
MEL_B = [
    "C6:6 A5:2 F5:4 A5:4",
    "G5:4 E5:2 C5:2 G5:8",
    "B5:4 D6:2 B5:2 G5:4 D5:4",
    "F5:2 E5:2 D5:4 A4:4 r:4",
    "A5:6 C6:2 A5:4 F5:4",
    "E5:2 G5:2 C6:4 B5:2 A5:2 G5:4",
    "B5:4 G5:2 E5:2 B4:8",
    "C#5:4 E5:4 A5:6 r:2",
]

TRACKS = [
    {"channel": 0, "program": 24, "volume": 116, "velocity": 110, "gate": 0.8, "long": 6, "vibrato": 30,
     "intro": [None, None], "loop": MEL_A + MEL_A + MEL_B + MEL_A3},
    {"channel": 5, "program": 24, "volume": 82, "velocity": 92, "gate": 0.8,
     "intro": [None, None], "loop": [None] * 8 + [_r.third_below(b, DORIAN) for b in MEL_A] + [None] * 8
                                     + [_r.third_below(b, DORIAN) for b in MEL_A3]},
    {"channel": 1, "program": 15, "volume": 74, "velocity": 92, "gate": 0.45,
     "intro": [chop("Dm"), chop("G")], "loop": [chop(c) for c in LOOP]},
    {"channel": 4, "program": 16, "volume": 56, "velocity": 80, "gate": 0.4,
     "intro": [None, bubble("G")], "loop": [bubble(c) for c in LOOP]},
    {"channel": 3, "program": 32, "volume": 124, "velocity": 118, "gate": 0.85, "long": 4, "fall": 1200,
     "intro": [bass("Dm"), bass("G")], "loop": [bass(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 96, "velocity": 98, "gate": 1.0,
     "intro": [ONE_DROP, FILL],
     "loop": [TAMB] + [ONE_DROP] * 6 + [FILL] + [TAMB] + [ONE_DROP] * 6 + [FILL]
             + [TAMB] + [ONE_DROP] * 6 + [FILL] + [TAMB] + [ONE_DROP] * 6 + [FILL]},
]

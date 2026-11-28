"""Results theme (updates patch): an original island reggae for the RESULTS screen.

Written for this project from scratch (melody, bass, chords and drums), not an
arrangement of any existing tune. Played the way Rare's own tunes are
(tools/rare_idiom.py, NOTES.md): here the beach tune's idiom, two pianos (program 1) in
thirds playing a syncopated melody in short accented notes, a bright piano (program 3)
chopping the off-beats, a short contrabass line, a one-drop kit. G major, 96 bpm.
A two-bar intro, then a 16-bar loop: A over G-C-D, B lifting through Em and C.

Build: python3 tools/song_build.py updates/music/results.py [--midi results.mid]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from rare_idiom import OFFBEATS, ONE_DROP, ONE_DROP_FILL, hits, third_below  # noqa: E402

NAME = "results"
TEMPO = 96

A = ["G", "G", "C", "D", "G", "G", "C", "D"]
B = ["Em", "C", "G", "D", "Em", "C", "D", "D"]
INTRO = ["G", "D"]
LOOP = A + B

G_MAJOR = [7, 9, 11, 0, 2, 4, 6]
CHOP = {"G": "B4+D5", "C": "C5+E5", "D": "A4+D5", "Em": "B4+E5"}
ROOT = {"G": ("G1", "D2"), "C": ("C2", "G1"), "D": ("D2", "A1"), "Em": ("E2", "B1")}


def bass(ch):
    r, f = ROOT[ch]
    return f"{r}:2:124 r:2 {r}:1:96 r:1 {f}:2:112 r:4 {r}:2:118 {f}:2:100"


MELODY = [
    "B4:1 r:1 D5:1 r:1 G5:2 D5:1 r:1 E5:2 D5:1 B4:1 r:2 D5:2",
    "B4:2 A4:1 G4:1 r:2 A4:1 B4:1 r:2 D5:2 B4:4",
    "C5:1 r:1 E5:1 r:1 G5:2 E5:1 r:1 G5:2 A5:1 G5:1 r:2 E5:2",
    "F#5:2 E5:1 D5:1 r:2 A4:1 C5:1 r:2 D5:2 F#5:2 r:2",
    "B4:1 r:1 D5:1 r:1 G5:2 D5:1 r:1 E5:2 D5:1 B4:1 r:2 D5:2",
    "B4:2 A4:1 G4:1 r:2 B4:1 D5:1 r:2 G5:2 D5:4",
    "C5:1 r:1 E5:1 r:1 G5:2 E5:1 r:1 G5:2 A5:1 G5:1 r:2 E5:2",
    "D5:2 C5:1 B4:1 r:2 A4:1 F#4:1 r:2 G4:6",
    "G5:1 r:1 B5:1 r:1 G5:2 E5:1 r:1 B4:2 E5:1 G5:1 r:2 B5:2",
    "C6:2 B5:1 A5:1 r:2 G5:1 E5:1 r:2 C5:2 E5:4",
    "D5:1 r:1 G5:1 r:1 B5:2 A5:1 r:1 G5:2 D5:1 B4:1 r:2 D5:2",
    "F#5:2 E5:1 D5:1 r:2 F#5:1 A5:1 r:2 A5:2 F#5:4",
    "G5:1 r:1 B5:1 r:1 G5:2 E5:1 r:1 B4:2 E5:1 G5:1 r:2 B5:2",
    "C6:2 B5:1 A5:1 r:2 G5:1 E5:1 r:2 C5:2 E5:4",
    "A5:2 F#5:1 D5:1 r:2 E5:1 F#5:1 r:2 A5:2 D6:2 r:2",
    "C6:2 B5:1 A5:1 r:2 F#5:1 E5:1 r:2 D5:6",
]

TRACKS = [
    {"channel": 0, "program": 1, "volume": 112, "velocity": 100, "gate": 0.8, "accent": 14,
     "intro": [None, None], "loop": MELODY},
    {"channel": 5, "program": 1, "volume": 96, "velocity": 94, "gate": 0.8, "accent": 14,
     "intro": [None, None], "loop": [third_below(b, G_MAJOR) for b in MELODY]},
    {"channel": 1, "program": 3, "volume": 84, "velocity": 112,
     "intro": [hits(CHOP["G"], OFFBEATS, 116, 92), hits(CHOP["D"], OFFBEATS, 116, 92)],
     "loop": [hits(CHOP[c], OFFBEATS, 116, 92) for c in LOOP]},
    {"channel": 3, "program": 43, "volume": 122, "velocity": 116, "gate": 0.8,
     "intro": [bass("G"), bass("D")], "loop": [bass(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 100, "velocity": 104, "gate": 1.0,
     "intro": [ONE_DROP, ONE_DROP_FILL],
     "loop": [ONE_DROP] * 7 + [ONE_DROP_FILL] + [ONE_DROP] * 7 + [ONE_DROP_FILL]},
]

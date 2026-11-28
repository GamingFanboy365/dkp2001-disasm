"""Final results theme when the player wins the cup (updates patch): an original anthem.

Written for this project from scratch, not an arrangement of any existing tune, in the
style of the build's own race tunes (NOTES.md: modal harmony on a pedal bass, a long loop
of varied 8-bar sections, a busy 16th ostinato under the lead, the lead harmonised in
parallel thirds on its repeats, vibrato and bend swells on long notes). C mixolydian,
138 bpm, heroic: the verses end on the bVII-I cadence (Bb to C), the middle section
climbs Ab-Bb-C. A viola lead doubled by violin a third below on the repeats, a clavinet
arpeggio, contrabass, a march snare with ghost notes, tom fills, crashes, bell accents.
A two-bar fanfare intro, then a 32-bar loop: A, A' (harmonised), B, A'' (harmonised).
Played with the instruments Rare's race tunes use (vgroup0).

Build: python3 tools/song_build.py updates/music/final_results.py [--midi final.mid]
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location("_results", os.path.join(os.path.dirname(__file__), "results.py"))
_r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r)

NAME = "final_results"
TEMPO = 138

A = ["C", "C", "Bb", "C", "F", "F", "Bb", "C"]
B = ["Ab", "Ab", "Bb", "Bb", "Ab", "Bb", "C", "C"]
INTRO = ["C", "Bb"]
LOOP = A + A + B + A

_r.SCALE = [0, 2, 4, 5, 7, 9, 10]                     # C mixolydian, for the harmony
ARP = {"C": ("C4", "E4", "G4", "C5"), "Bb": ("Bb3", "D4", "F4", "Bb4"), "F": ("A3", "C4", "F4", "A4"),
       "Ab": ("Ab3", "C4", "Eb4", "Ab4")}
ROOT = {"C": ("C2", "C3"), "Bb": ("Bb1", "Bb2"), "F": ("F1", "F2"), "Ab": ("Ab1", "Ab2")}


def arp(ch):
    a, b, c, d = ARP[ch]
    return f"{a}:1 {b}:1 {c}:1 {d}:1 {c}:1 {b}:1 {a}:1 {b}:1 {c}:1 {d}:1 {c}:1 {b}:1 {a}:1 {b}:1 {c}:1 {d}:1"


def bass(ch):
    lo, hi = ROOT[ch]
    return f"{lo}:3 r:1 {lo}:2 {hi}:2 {lo}:3 r:1 {lo}:2 {hi}:2"


MARCH = {36: "x.......x.......", 38: "....x..o....x.oo", 42: "o.o.o.o.o.o.o.o."}
CRASH = {**MARCH, 57: "x..............."}
ROLL = {36: "x.......x.......", 38: "....x...xoxoxxxx", 41: "............x.x.", 43: "..........x....."}
OPENING = [
    {36: "x.......x.......", 41: "x...x...x.x.x.xx", 57: "x..............."},
    {36: "x.......x...x...", 45: "x.x.x.x.........", 43: "........x.x.x.x.", 57: "x..............."},
]

MEL_A = [
    "C5:2 E5:2 G5:4 C6:6 Bb5:2",
    "G5:2 E5:2 G5:4 C6:8",
    "D6:4 Bb5:2 F5:2 Bb5:6 C6:2",
    "D6:2 C6:2 Bb5:2 G5:2 C6:8",
    "C6:4 A5:2 F5:2 A5:4 C6:4",
    "F6:6 E6:2 D6:4 C6:4",
    "Bb5:2 C6:2 D6:4 F6:4 D6:4",
    "E6:12 r:4",
]
MEL_B = [
    "Eb6:6 C6:2 Ab5:4 C6:4",
    "Eb6:4 F6:2 Eb6:2 C6:8",
    "D6:6 Bb5:2 F5:4 Bb5:4",
    "D6:4 F6:2 D6:2 Bb5:8",
    "C6:4 Eb6:4 Ab6:4 G6:4",
    "F6:4 D6:4 Bb5:4 D6:4",
    "E6:4 G6:4 C7:6 Bb6:2",
    "C7:12 r:4",
]
FANFARE = ["G4+C5:2 G4+C5:2 G4+C5:2 E5:2 G5:8", "F4+Bb4:2 F4+Bb4:2 F4+Bb4:2 D5:2 F5:4 G5:4"]
BELLS = [None] * 7 + ["C6:16"] + [None] * 7 + ["G5:16"] + [None] * 7 + ["C6:16"] + [None] * 7 + ["C6:16"]

TRACKS = [
    {"channel": 0, "program": 41, "volume": 118, "velocity": 114, "gate": 0.92, "long": 6,
     "vibrato": 48, "swell": 1600, "intro": FANFARE, "loop": MEL_A + MEL_A + MEL_B + MEL_A},
    {"channel": 5, "program": 40, "volume": 92, "velocity": 100, "gate": 0.92, "long": 6, "vibrato": 40,
     "intro": [None, None],
     "loop": [None] * 8 + [_r.third_below(b) for b in MEL_A] + [None] * 8 + [_r.third_below(b) for b in MEL_A]},
    {"channel": 1, "program": 7, "volume": 66, "velocity": 88, "gate": 0.5,
     "intro": [None, arp("Bb")], "loop": [arp(c) for c in LOOP]},
    {"channel": 3, "program": 43, "volume": 122, "velocity": 118, "gate": 0.8,
     "intro": [bass("C"), bass("Bb")], "loop": [bass(c) for c in LOOP]},
    {"channel": 2, "program": 127, "volume": 106, "velocity": 106, "gate": 1.0,
     "intro": OPENING, "loop": [CRASH] + [MARCH] * 6 + [ROLL] + [CRASH] + [MARCH] * 6 + [ROLL]
                               + [CRASH] + [MARCH] * 6 + [ROLL] + [CRASH] + [MARCH] * 6 + [ROLL]},
    {"channel": 4, "program": 14, "volume": 84, "velocity": 100, "gate": 0.95,
     "intro": [None, None], "loop": BELLS},
]

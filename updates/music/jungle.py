"""Jungle theme (updates patch): an original tune for the jungle courses.

Written for this project from scratch: its own melody, bass and percussion, not an
arrangement of any existing tune. E dorian, 140 bpm, 4/4: a two-bar drum intro, then a
loop of a melody (A), a higher answering section (B), A again over a busier groove, and a
four-bar drum break. Played with the instruments Rare's race tunes use (vgroup0); the
program numbers below are those instruments.

Build: python3 tools/song_build.py updates/music/jungle.py [--midi jungle.mid]
Bars: "NOTE:LEN" in sixteenths (4 a beat), "r" a rest, "+" for notes together; drum bars
are 16-step patterns per drum key (x loud, o soft).
"""
NAME = "jungle"
TEMPO = 140

# the loop's chords, two to a section: A and B are 8 bars each
A_CHORDS = ["Em", "D", "C", "Bm", "Em", "D", "C", "D"]
B_CHORDS = ["C", "D", "Em", "Em", "C", "D", "Em", "D"]
BREAK_CHORDS = ["Em", "Em", "D", "D"]
INTRO = ["Em", "Em"]
LOOP = A_CHORDS + B_CHORDS + A_CHORDS + BREAK_CHORDS

ROOT = {"Em": "E", "D": "D", "C": "C", "Bm": "B"}
FIFTH = {"Em": "B", "D": "A", "C": "G", "Bm": "F#"}
THIRD = {"Em": "G", "D": "F#", "C": "E", "Bm": "D"}


def bass_bar(ch, busy=False):
    """Root on the beat, a push on the and-of-two, the fifth, then the octave."""
    r, f = ROOT[ch], FIFTH[ch]
    lo = 1 if r in ("B",) else 2
    if busy:
        return f"{r}{lo}:3 {r}{lo}:1 r:2 {r}{lo}:2 {f}{lo}:2 r:2 {r}{lo + 1}:2 {f}{lo}:2"
    return f"{r}{lo}:3 r:3 {r}{lo}:2 {f}{lo}:4 {r}{lo + 1}:2 {f}{lo}:2"


def ostinato_bar(ch):
    """Muted plucks: a rocking figure on the chord's root, fifth and third."""
    r, f, t = ROOT[ch], FIFTH[ch], THIRD[ch]
    return f"{r}4:2 {f}4:2 {r}5:2 {f}4:2 {t}4:2 {f}4:2 {r}5:2 {t}5:2"


GROOVE = {                       # the main jungle groove
    36: "x.....x...x.....",      # kick
    41: "......o.......o.",      # low tom
    45: "..o.......o...o.",      # high tom
    67: "x..x..x...x..x..",      # high agogo
    68: "..........o.....",      # low agogo
    42: "o.o.o.o.o.o.o.o.",      # shaker-ish closed hat
    54: "....x.......x...",      # tambourine on two and four
}
GROOVE_BUSY = {**GROOVE,
               42: "o.ooo.o.o.ooo.o.",
               43: "...o.......o....",      # mid tom
               }
FILL = {
    36: "x.......x.......",
    41: "........x.x.x.xx",
    43: "....x.x.........",
    45: "x.x.............",
    65: "..............x.",      # timbale
    57: "................",
}
BREAK = [
    {36: "x.....x...x.....", 41: "x.o.x.o.x.o.x.o.", 45: "..x...x...x...x.", 67: "x..x..x...x..x.."},
    {36: "x.....x...x.....", 41: "x.o.x.o.x.o.x.o.", 45: "..x...x...x...x.", 68: "x..x..x...x..x.."},
    {36: "x.....x...x.....", 43: "x.o.x.o.x.o.x.o.", 45: "..x.x.x...x.x.x.", 67: "x..x..x...x..x..", 80: "x..............."},
    {36: "x.......x.......", 41: "........x.x.x.xx", 43: "....x.x.x.......", 45: "x.x.x...........", 65: "..............x.", 81: "x..............."},
]

MELODY_A = [
    "E5:4 G5:2 A5:2 B5:6 A5:2",
    "F#5:4 A5:2 F#5:2 D5:8",
    "E5:2 G5:2 C6:4 B5:2 A5:2 G5:4",
    "F#5:12 r:4",
    "E5:2 E5:2 G5:2 B5:2 D6:4 B5:4",
    "A5:2 B5:2 A5:2 F#5:2 D5:4 E5:4",
    "G5:4 E5:2 G5:2 A5:4 B5:4",
    "A5:8 F#5:4 r:4",
]
MELODY_B = [
    "r:2 G5:2 C6:2 D6:2 E6:4 D6:4",
    "C6:2 B5:2 A5:4 F#5:8",
    "r:2 G5:2 B5:2 D6:2 E6:6 D6:2",
    "B5:12 r:4",
    "E6:4 D6:2 C6:2 B5:4 A5:4",
    "B5:2 A5:2 F#5:4 A5:4 D6:4",
    "E6:6 D6:2 B5:4 G5:4",
    "A5:4 B5:4 r:8",
]
# the answering guitar: short replies in the gaps of the melody
ANSWER_A = [
    "r:12 E5+B5:2 r:2", "r:12 D5+A5:2 r:2", "r:16", "r:12 B4+F#5:2 D5+A5:2",
    "r:16", "r:12 D5+F#5:2 r:2", "r:16", "r:8 D5+A5:2 r:2 D5+F#5:2 r:2",
]
ANSWER_B = [
    "C5+G5:2 r:14", "D5+A5:2 r:14", "r:12 E5+B5:2 r:2", "r:4 G5:2 A5:2 B5:4 r:4",
    "C5+G5:2 r:14", "D5+A5:2 r:14", "r:12 E5+B5:2 r:2", "r:4 F#5:2 G5:2 A5:4 r:4",
]

drums_loop = ([GROOVE] * 7 + [FILL]) + ([GROOVE] * 7 + [FILL]) + ([GROOVE_BUSY] * 7 + [FILL]) + BREAK

TRACKS = [
    {"channel": 0, "program": 15, "volume": 112, "pan": 64, "velocity": 110, "gate": 0.8,
     "intro": [None, None],
     "loop": MELODY_A + MELODY_B + MELODY_A + [None] * 4},
    {"channel": 1, "program": 28, "volume": 72, "pan": 40, "velocity": 90, "gate": 0.6,
     "intro": [None, ostinato_bar("Em")],
     "loop": [ostinato_bar(c) for c in A_CHORDS + B_CHORDS + A_CHORDS + BREAK_CHORDS]},
    {"channel": 2, "program": 127, "volume": 108, "pan": 64, "velocity": 100, "gate": 1.0,
     "intro": [GROOVE, FILL],
     "loop": drums_loop},
    {"channel": 3, "program": 43, "volume": 120, "pan": 64, "velocity": 118, "gate": 0.75,
     "intro": [None, bass_bar("Em")],
     "loop": [bass_bar(c) for c in A_CHORDS + B_CHORDS]
             + [bass_bar(c, busy=True) for c in A_CHORDS + BREAK_CHORDS]},
    {"channel": 4, "program": 24, "volume": 84, "pan": 92, "velocity": 96, "gate": 0.5,
     "intro": [None, None],
     "loop": ANSWER_A + ANSWER_B + ANSWER_A + [None] * 4},
]

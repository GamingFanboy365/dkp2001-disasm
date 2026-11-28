"""Results theme (updates patch): an original beach reggae tune for the RESULTS screen.

Written for this project from scratch (melody, bass, chords and drums), not an
arrangement of any existing tune. F major, 84 bpm, laid back: off-beat "skank" chops on
clean guitar, a melodic bass, a one-drop groove (kick and snare together on
the third beat), and a bell-like island melody. A one-bar pickup, then a 16-bar loop.
Played with the instruments Rare's race tunes use (vgroup0).

Build: python3 tools/song_build.py updates/music/results.py [--midi results.mid]
"""
NAME = "results"
TEMPO = 84

CHORDS = ["F", "Bb", "C", "F", "Dm", "Bb", "C", "C",
          "F", "Bb", "Gm", "C", "Am", "Dm", "Bb", "C"]
INTRO = ["F"]
LOOP = CHORDS

TRIAD = {"F": "F4+A4+C5", "Bb": "F4+Bb4+D5", "C": "E4+G4+C5", "Dm": "F4+A4+D5",
         "Gm": "G4+Bb4+D5", "Am": "E4+A4+C5"}
BASS = {"F": ("F2", "C3", "A2"), "Bb": ("Bb1", "F2", "D2"), "C": ("C2", "G2", "E2"),
        "Dm": ("D2", "A2", "F2"), "Gm": ("G1", "D2", "Bb1"), "Am": ("A1", "E2", "C2")}


def skank(ch):
    """Chords on the off-beats (the 'and' of each beat), short."""
    c = TRIAD[ch]
    return f"r:2 {c}:2 r:2 {c}:2 r:2 {c}:2 r:2 {c}:2"


def bassline(ch):
    r, f, t = BASS[ch]
    return f"{r}:3 r:1 {r}:2 {f}:2 r:2 {t}:2 {f}:3 r:1"


ONE_DROP = {
    36: "........x.......",       # kick on three
    38: "........x.......",       # with the snare
    42: "x.o.x.o.x.o.x.o.",       # hats
    54: "......o.......o.",       # tambourine flicks
}
ONE_DROP_FILL = {
    36: "........x.......",
    38: "........x...x.x.",
    45: "..........x.....",
    43: "............x...",
    41: "..............x.",
    42: "x.o.x.o.........",
}

MELODY = [
    "A5:4 C6:2 A5:2 G5:6 F5:2",
    "D5:4 F5:4 Bb5:6 A5:2",
    "G5:2 A5:2 G5:2 E5:2 C5:8",
    "r:4 F5:2 G5:2 A5:4 C6:4",
    "D6:4 C6:2 A5:2 F5:6 A5:2",
    "Bb5:4 A5:2 G5:2 F5:4 D5:4",
    "E5:2 F5:2 G5:4 C6:6 Bb5:2",
    "A5:2 G5:2 E5:4 r:8",
    "F5:2 A5:2 C6:4 A5:4 F5:4",
    "D6:6 C6:2 Bb5:4 F5:4",
    "G5:2 Bb5:2 D6:4 C6:2 Bb5:2 G5:4",
    "E5:4 G5:4 C6:8",
    "C6:4 A5:2 E5:2 A5:6 C6:2",
    "D6:2 C6:2 A5:4 F5:6 D5:2",
    "F5:4 G5:2 A5:2 Bb5:4 D6:4",
    "C6:6 Bb5:2 A5:4 G5:4",
]

TRACKS = [
    {"channel": 0, "program": 9, "volume": 104, "pan": 64, "velocity": 104, "gate": 0.7,
     "intro": [None], "loop": MELODY},
    {"channel": 1, "program": 27, "volume": 78, "pan": 36, "velocity": 96, "gate": 0.45,
     "intro": [skank("F")], "loop": [skank(c) for c in CHORDS]},
    {"channel": 2, "program": 127, "volume": 100, "pan": 64, "velocity": 96, "gate": 1.0,
     "intro": [ONE_DROP], "loop": [ONE_DROP] * 7 + [ONE_DROP_FILL] + [ONE_DROP] * 7 + [ONE_DROP_FILL]},
    {"channel": 4, "program": 35, "volume": 122, "pan": 64, "velocity": 120, "gate": 0.85,
     "intro": [bassline("F")], "loop": [bassline(c) for c in CHORDS]},
]

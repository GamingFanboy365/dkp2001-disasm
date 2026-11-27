"""Temple Tangle (level 37): our race layout on Rare's temple-courtyard ground.

The courtyard is 1024 units square: a carved border round the edge, a sand pad in
each corner, and a maze of lines worn into the paving. The race starts up the west
side, runs along the top, dives into the middle of the maze and snakes through it,
runs down the east side, then tangles back through the southern maze to the start.
Coordinates: x right, z down (as in the map pictures), y height.
Build: python3 tools/course_build.py updates/courses/temple_tangle.py
"""
NAME = "temple_tangle"
LEVEL = 37

# the racing line (x, z, y); the first point is the start hoop, flying towards the second
LINE = [
    (80, 640, 10),      # 0 start hoop, west side, flying north
    (78, 470, 12),      # 1
    (96, 330, 14),      # 2
    (170, 196, 12),     # 3 sweep right along the top
    (300, 150, 10),     # 4
    (440, 124, 10),     # 5
    (560, 210, 8),      # 6 dive into the maze
    (520, 330, 8),      # 7
    (390, 380, 8),      # 8 west...
    (250, 420, 8),      # 9
    (200, 520, 10),     # 10 ...hairpin back east
    (300, 600, 10),     # 11
    (480, 590, 10),     # 12
    (640, 530, 10),     # 13 north again
    (700, 400, 12),     # 14
    (700, 250, 12),     # 15
    (780, 140, 14),     # 16 round the top-right
    (910, 190, 14),     # 17 the east side, flying south
    (935, 380, 15),     # 18
    (935, 580, 15),     # 19
    (910, 780, 12),     # 20
    (800, 900, 10),     # 21 along the bottom
    (640, 930, 10),     # 22
    (500, 860, 8),      # 23 up into the southern maze
    (430, 740, 8),      # 24
    (300, 720, 8),      # 25
    (200, 820, 10),     # 26
    (110, 790, 10),     # 27 and round into the start
]
SPACING = 95                    # route point spacing (Rare's courses: 80-110)
ROUTE_OFFSETS = (0, 8, -8, 16, -16)   # the five AI routes, sideways from the line

# pylons in race order: (waypoint, side the pylon is on, distance from the line). Hidden
# checkpoints go to the wall on that side (L/R of the racer, or N/S/E/W)
PYLONS = [
    (3, "R", 40),       # first turn: keep it on your right
    (7, "W", 40),       # at z 330 its line clears the first corner (at z 210 it crossed it)
    (8, "L", 40),
    (10, "W", 48),      # the hairpin (its checkpoint line runs due west to the wall)
    (13, "L", 40),
    (16, "R", 40),
    (19, "R", 40),
    (22, "R", 40),
    (24, "L", 40),
    (26, "R", 40),
]

# HUD turn hints, just before the turns: 0 hard left, 1 left, 2 straight, 3 right, 4 hard right
ARROWS = [
    (2, 3), (5, 3), (7, 3), (9, 1), (12, 1), (15, 3), (20, 3), (23, 3), (25, 1),
]

# pickups: (kind, waypoint, sideways offset, height)
PICKUPS = [
    ("banana", 1, 0, 12), ("banana", 4, -10, 10), ("banana", 4, 10, 10),
    ("banana", 8, 0, 8), ("banana", 11, 0, 10), ("banana", 14, 0, 12),
    ("banana", 18, -12, 15), ("banana", 18, 12, 15), ("banana", 21, 0, 10),
    ("banana", 24, 0, 8), ("banana", 26, 0, 10), ("banana", 27, 0, 10),
    ("weapon", 2, -14, 14), ("weapon", 2, 14, 14),
    ("weapon", 7, 0, 10), ("weapon", 12, -14, 10), ("weapon", 12, 14, 10),
    ("weapon", 17, 0, 14), ("weapon", 20, -14, 12), ("weapon", 20, 14, 12),
    ("weapon13", 9, 0, 16), ("weapon14", 23, 0, 16),
    ("turbo", 15, 0, 12),
]
# boosts: ('air' or 'ground', waypoint, sideways offset)
BOOSTS = [("air", 1, 0), ("ground", 19, 0), ("ground", 22, 0)]

# scenery: Rare's own palm trees and stone pillars, placed (not altered); solid, so
# kept at least SCENERY_CLEARANCE from the line
SCENERY_CLEARANCE = 48
SCENERY = [
    ("pillar", 200, 240, 0), ("pillar", 360, 240, 0), ("pillar", 360, 500, 0),
    ("pillar", 560, 430, 0), ("pillar", 820, 380, 0), ("pillar", 820, 650, 0),
    ("pillar", 380, 820, 0), ("pillar", 600, 760, 0),
    ("palm", 40, 120, 24), ("palm", 980, 110, 24), ("palm", 990, 980, 24),
    ("palm", 620, 60, 24), ("palm", 520, 40, 24), ("palm", 180, 960, 24), ("palm", 860, 980, 24),
]
# invisible walls along both edges of the track (updates/code/walls.s): a plane more than
# this far from the racing line bounces back, as at the edge of Rare's world
TRACK_HALF_WIDTH = 72
# the pylons are hidden checkpoints: out of sight above the ground, at the edge of the map,
# so each one's pass line runs across the track and can't be missed
HIDDEN_PYLONS = {"height": 2000, "outside": 16}
BOUNDS = (30, 30, 994, 994)          # where the checkpoints go: just outside this box
HUD_MAP = True                       # draw its HUD course map (tab_sprites 111 in the updates build)
CAMERA = 3                       # the front-end fly-in takes every third route point

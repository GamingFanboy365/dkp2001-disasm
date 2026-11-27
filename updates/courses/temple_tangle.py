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
    (90, 660, 10),      # 0 start hoop, west side, flying north
    (88, 490, 12),      # 1
    (100, 330, 14),     # 2
    (165, 195, 12),     # 3 sweep right along the top
    (300, 128, 10),     # 4
    (450, 128, 10),     # 5
    (565, 215, 8),      # 6 dive into the maze
    (548, 360, 8),      # 7
    (455, 440, 8),      # 8 west...
    (345, 445, 8),      # 9
    (290, 530, 10),     # 10 ...hairpin back east
    (368, 602, 10),     # 11
    (520, 615, 10),     # 12
    (650, 545, 10),     # 13 north again
    (748, 405, 12),     # 14
    (758, 255, 12),     # 15
    (815, 135, 14),     # 16 round the top-right
    (925, 195, 14),     # 17 the east side, flying south
    (945, 400, 15),     # 18
    (945, 610, 15),     # 19
    (915, 800, 12),     # 20
    (800, 920, 10),     # 21 along the bottom
    (640, 945, 10),     # 22
    (500, 900, 8),      # 23 up into the southern maze
    (420, 790, 8),      # 24
    (290, 788, 8),      # 25
    (215, 870, 10),     # 26
    (120, 830, 10),     # 27 and round into the start
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
SCENERY_CLEARANCE = 80                # off the track (and beyond its walls)
SCENERY = [
    ("pillar", 720, 740, 0), ("pillar", 380, 280, 0), ("pillar", 800, 580, 0),
    ("pillar", 220, 660, 0), ("pillar", 220, 400, 0), ("pillar", 540, 740, 0), ("pillar", 660, 140, 0),
    ("palm", 40, 40, 24), ("palm", 660, 40, 24), ("palm", 340, 980, 24),
    ("palm", 980, 40, 24), ("palm", 980, 980, 24), ("palm", 240, 40, 24),
]
# invisible walls along both edges of the track (updates/code/walls.s): a plane more than
# this far from the racing line bounces back, as at the edge of Rare's world
TRACK_HALF_WIDTH = 56
GRASS_GAP = 56                       # grass between separate stretches of track
# the pylons are hidden checkpoints: out of sight above the ground, at the edge of the map,
# so each one's pass line runs across the track and can't be missed
HIDDEN_PYLONS = {"height": 2000, "outside": 16}
BOUNDS = (30, 30, 994, 994)          # where the checkpoints go: just outside this box
# its ground (python3 tools/course_build.py updates/courses/temple_tangle.py --ground ROM):
# Rare's metatiles from Classic Dogfight's overgrown temple, arranged to show the track
GROUND = {"source": "__map_jungle_01_lvl", "tiles": "__chr_jungle_01_lvl", "palette": "__pal_jungle_lvl"}
HUD_MAP = True                       # draw its HUD course map (tab_sprites 111 in the updates build)
CAMERA = 3                       # the front-end fly-in takes every third route point

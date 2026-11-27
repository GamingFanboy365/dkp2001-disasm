"""BEACH RACE 2 (level 2): Rare's race with AI routes that follow it.

Rare's 11 pylons lay out a figure-of-eight course over the island and its bridges, but
the course's AI route is an unrelated loop round the outside (over open water, not from
the start hoop): never finished. tools/course_convert.py draws the racing line from the
start hoop past each pylon in Rare's order, PASS_DISTANCE out on the side the pylon is
passed, and makes five AI routes along it (our routes, at build time, from your ROM's
extracted assets). The fixes build uses only those routes (FIX "beach-race-2-routes");
the updates build also turns the pylons into hidden checkpoints and adds walls.
"""
NAME = "beach_01"
LEVEL = 2
LINE_FROM_PYLONS = True
PASS_DISTANCE = 40
TRACK_HALF_WIDTH = 64

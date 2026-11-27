"""BOUNTY BEACH (level 1), updates patch: Rare's race without pylons.

tools/course_convert.py builds it from your ROM's extracted assets at build time: every
object Rare placed is kept except the pylons, which become hidden checkpoints, and
invisible walls follow the track (Rare's AI route 0) TRACK_HALF_WIDTH either side.
"""
NAME = "beach_00"
LEVEL = 1
TRACK_HALF_WIDTH = 64

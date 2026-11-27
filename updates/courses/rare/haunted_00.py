"""WHISPER WOODS (level 30), updates patch: Rare's race without pylons.

tools/course_convert.py builds it from your ROM's extracted assets at build time: every
object Rare placed is kept except the pylons, which become hidden checkpoints, and
invisible walls follow the track (Rare's AI route 0) TRACK_HALF_WIDTH either side.
"""
NAME = "haunted_00"
LEVEL = 30
TRACK_HALF_WIDTH = 64

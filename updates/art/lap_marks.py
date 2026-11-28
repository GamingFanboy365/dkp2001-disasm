"""Our lap letters (updates patch): L A P F I N, drawn for this project.

With Rare's HUD digits (__spr_hud_digits, used by reference) they make the lap text
shown at the bottom left in a race: LAP 1, LAP 2, ... and FINAL LAP on the last lap.
8x16 each, 4bpp, in the HUD palette (__pal_hud_icons) and drawn the way Rare's digits
are: yellow (13) strokes two pixels wide, a red top-left edge (10) and a black
lower-right shadow (1).

    python3 updates/art/lap_marks.py [--png OUT]  -> updates/art/lap_marks.bin (6 glyphs)
"""
import os
import sys

GLYPHS = {
    "L": [
        "........",
        ".aa.....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1aaa.",
        "adddddd1",
        "adddddd1",
        ".111111.",
        "........",
    ],
    "A": [
        "........",
        "..aaaa..",
        ".adddd1.",
        "add11dd1",
        "add1add1",
        "add1add1",
        "add1add1",
        "add1add1",
        "addaadd1",
        "adddddd1",
        "add11dd1",
        "add1add1",
        "add1add1",
        "add1add1",
        ".11..11.",
        "........",
    ],
    "P": [
        "........",
        ".aaaaa..",
        "addddd1.",
        "add11dd1",
        "add1add1",
        "add1add1",
        "add1add1",
        "addddd1.",
        "add111..",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        "add1....",
        ".11.....",
        "........",
    ],
    "F": [
        "........",
        ".aaaaaa.",
        "adddddd1",
        "adddddd1",
        "add11111",
        "add1....",
        "add1....",
        "add1aa..",
        "adddd1..",
        "adddd1..",
        "add111..",
        "add1....",
        "add1....",
        "add1....",
        ".11.....",
        "........",
    ],
    "I": [
        "........",
        ".aaaaaa.",
        "adddddd1",
        ".11dd11.",
        "..add1..",
        "..add1..",
        "..add1..",
        "..add1..",
        "..add1..",
        "..add1..",
        "..add1..",
        "..add1..",
        ".aadd1a.",
        "adddddd1",
        ".111111.",
        "........",
    ],
    "N": [
        "........",
        ".aa..aa.",
        "add1add1",
        "addd1dd1",
        "addd1dd1",
        "adddddd1",
        "adddddd1",
        "add1ddd1",
        "add1ddd1",
        "add1add1",
        "add1add1",
        "add1add1",
        "add1add1",
        "add1add1",
        ".11..11.",
        "........",
    ],
}
ORDER = "LAPFIN"                      # glyphs 12-17 after the timer's digits and marks


def tiles(rows):
    """An 8x16 glyph as two 4bpp tiles (top, bottom)."""
    out = bytearray()
    for r in rows:
        assert len(r) == 8 and len(rows) == 16, r
        v = [int(c, 16) if c != "." else 0 for c in r]
        out += bytes(v[x] | v[x + 1] << 4 for x in range(0, 8, 2))
    return bytes(out)


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lap_marks.bin")
    open(path, "wb").write(b"".join(tiles(GLYPHS[c]) for c in ORDER))
    if "--png" in sys.argv:                 # a preview: FINAL LAP and LAP, 4x
        from PIL import Image
        col = {"1": (0, 0, 0), "a": (240, 0, 0), "d": (248, 248, 0)}
        text = "FINAL LAP"
        im = Image.new("RGB", (8 * len(text) + 8, 20), (40, 90, 160))
        for i, c in enumerate(text):
            for y, r in enumerate(GLYPHS.get(c, ["." * 8] * 16)):
                for x, p in enumerate(r):
                    if p != ".":
                        im.putpixel((4 + 8 * i + x, 2 + y), col[p])
        im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(sys.argv[sys.argv.index("--png") + 1])

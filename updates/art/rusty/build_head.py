#!/usr/bin/env python3
"""Rusty's racer icon (updates patch): his head in profile in the icon frame the racers'
heads share, in the game's sprite format, from model.py (ours).

    python3 updates/art/rusty/build_head.py

writes head.bin (three levels of detail, as __spr_diddy_head, _01, _02 are laid out),
head_pal.bin (16 colours: 0 transparent, 1 the black frame, 2 the background, 3-15 the
head) and head.png (to look at). The frame is Rare's: a 20x20 square with notched
corners; the background is cyan, as Dixie's and DK's are (a contrast for his red comb).
Pieces as Diddy's icon has them: 16x16 at (8,8), 8x16 at (20,8), 16x8 at (8,20), 8x8 at
(20,20); then one 16x16 at (6,6); then one 8x8 at (3,3).
"""
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402
from build_sprite import rle, tiles_4bpp  # noqa: E402

BG = (0, 248, 248)
SEEDS = [(150, 52, 30), (228, 80, 32), (250, 150, 80), (248, 234, 200), (232, 36, 44),
         (252, 186, 40), (200, 140, 30), (255, 255, 255), (24, 20, 24), (110, 40, 24),
         (248, 214, 112), (196, 160, 70), (204, 56, 48)]


def frame(n):
    """Rare's icon frame, n x n: 1 the border (notched corners), 2 inside, 0 outside."""
    f = np.full((n, n), 2, np.uint8)
    f[0, :] = f[-1, :] = f[:, 0] = f[:, -1] = 1
    for y, x in ((0, 0), (0, n - 1), (n - 1, 0), (n - 1, n - 1)):
        f[y, x] = 0
    for y, x in ((1, 1), (1, n - 2), (n - 2, 1), (n - 2, n - 2)):
        f[y, x] = 1
    return f


def head_image(px):
    """The head in profile, facing left and a little toward us, framed on the face: about
    3.4 model units across the px-pixel square, so the top of the hat runs off the frame
    as the racers' icons crop theirs."""
    over = 8
    big = model.render((4, 140), px * over, scale=px * over / 4.2, mesh=model.build_head(),
                       focus=(0.55, 0.45, 0.0))
    return big.resize((px, px), Image.LANCZOS)


def icon(n, inner, pal):
    """An n x n icon of palette indices: frame, background, head."""
    f = frame(n).astype(int)
    head = head_image(inner)
    a = np.asarray(head).astype(float)
    ox, oy = (n - head.width) // 2, (n - head.height) // 2
    for y in range(head.height):
        for x in range(head.width):
            if a[y, x, 3] > 120 and f[oy + y, ox + x] == 2:
                rgb = a[y, x, :3] / (a[y, x, 3] / 255)
                d = ((pal - rgb) ** 2).sum(1)
                f[oy + y, ox + x] = 3 + int(d.argmin())
    return f.astype(np.uint8)


def palette():
    px = []
    for n in (18, 12):
        a = np.asarray(head_image(n)).astype(float)
        m = a[..., 3] > 120
        px.append(a[..., :3][m] / (a[..., 3:4][m] / 255))
    px = np.concatenate(px)
    c = np.array(SEEDS, float)
    for _ in range(10):
        lab = ((px[:, None] - c[None]) ** 2).sum(-1).argmin(1)
        for k in range(len(c)):
            if (lab == k).any():
                c[k] = 0.6 * px[lab == k].mean(0) + 0.4 * np.array(SEEDS[k])
    return np.clip(c, 0, 255)


def level(pieces, canvas, origin, radius, last):
    """pieces: (attr0, attr1, x, y, w, h) on `canvas` (indices); one frame."""
    frame_at = 16
    plist = struct.pack("<H", len(pieces))
    tiles, t = bytearray(), 0
    for a0, a1, x, y, w, h in pieces:
        plist += struct.pack("<HHH", a0, a1, t)
        sub = canvas[y:y + h, x:x + w]
        for ty in range(h // 8):
            for tx in range(w // 8):
                tiles += tiles_4bpp(sub[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8])
                t += 1
    chartab = (frame_at + len(plist) + 15) // 16 * 16
    blk = struct.pack("<H", len(tiles) // 32) + rle(bytes(tiles))
    body = struct.pack("<H", 1) + bytes(14) + blk
    body += bytes((-len(body)) % 16)
    total = chartab + len(body)
    hdr = struct.pack("<8H", chartab, 16, 0 if last else total // 16, origin, origin, radius, radius, frame_at)
    out = bytearray(hdr + plist)
    out += bytes(chartab - len(out))
    out += body
    assert len(out) == total
    return bytes(out)


def main():
    pal = palette()
    big = icon(20, 18, pal)
    c0 = np.zeros((32, 32), np.uint8)
    c0[8:28, 8:28] = big
    l0 = level([(0x0008, 0x4008, 8, 8, 16, 16), (0x8008, 0x0014, 20, 8, 8, 16),
                (0x4014, 0x0008, 8, 20, 16, 8), (0x0014, 0x0014, 20, 20, 8, 8)], c0, 8, 8, False)
    mid = icon(14, 12, pal)
    c1 = np.zeros((32, 32), np.uint8)
    c1[7:21, 7:21] = mid
    l1 = level([(0x0006, 0x4006, 6, 6, 16, 16)], c1, 6, 8, False)
    small = icon(7, 6, pal)
    c2 = np.zeros((16, 16), np.uint8)
    c2[3:10, 3:10] = small[:7, :7]
    l2 = level([(0x0003, 0x0003, 3, 3, 8, 8)], c2, 3, 4, True)
    data = l0 + l1 + l2
    # chain the levels: each header's "next" is relative to its own start
    open(os.path.join(HERE, "head.bin"), "wb").write(data)
    cols = [(0, 0, 0), (0, 0, 0), BG] + [tuple(int(v) for v in c) for c in pal]
    gba = b"".join(struct.pack("<H", (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10) for r, g, b in cols)
    open(os.path.join(HERE, "head_pal.bin"), "wb").write(gba)
    img = Image.new("RGB", (20, 20), (255, 0, 255))
    for y in range(20):
        for x in range(20):
            if big[y, x]:
                img.putpixel((x, y), cols[big[y, x]])
    img.resize((100, 100), Image.NEAREST).save(os.path.join(HERE, "head.png"))
    print(f"head.bin {len(data)} bytes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Rusty's course-menu picture (updates patch): him head-on in his plane, the propeller
spinning, as the racers' *small pictures are (diddysmall1, kongsmall...). From model.py.

    python3 updates/art/rusty/build_small.py

writes small_map.bin (two layers of 22x16 one-byte tile numbers: the two frames the menu
alternates), small_chars.bin (256-colour tiles, tile 0 blank), small_plt.bin (256 colours;
the menu loads 144-239, so the picture's colours are those) and small.png (to look at).
"""
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

W, H = 176, 128
VIEW = (9, 180)
SCALE = 15.2                                 # pixels per model unit
FOCUS = (0.5, 2.3, 0.0)                      # the model point at the picture's centre


def frame(phase):
    big = model.render(VIEW, W * 4, scale=SCALE * 4, mesh=model.build(phase=phase), focus=FOCUS)
    big = big.crop((0, (W * 4 - H * 4) // 2, W * 4, (W * 4 - H * 4) // 2 + H * 4))
    small = big.resize((W, H), Image.LANCZOS)
    a = np.asarray(small).astype(float)
    mask = a[..., 3] > 110
    rgb = np.clip(a[..., :3] / np.maximum(a[..., 3:4] / 255.0, 1e-3), 0, 255)
    edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
    rgb[edge] *= 0.55
    return rgb, mask


def main():
    frames = [frame(0), frame(4)]
    px = np.concatenate([rgb[m] for rgb, m in frames])
    strip = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8), "RGB")
    q = strip.quantize(colors=95, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:3 * 95]).reshape(95, 3)
    tiles = [bytes(64)]                                     # tile 0: blank
    index = {tiles[0]: 0}
    maps = bytearray()
    for rgb, mask in frames:
        d = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
        idx = (d.argmin(-1) + 145).astype(np.uint8)
        idx[~mask] = 0
        for ty in range(16):
            for tx in range(22):
                t = idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes()
                if t not in index:
                    index[t] = len(tiles)
                    tiles.append(t)
                maps.append(index[t])
    assert len(tiles) <= 256, len(tiles)
    open(os.path.join(HERE, "small_map.bin"), "wb").write(maps)
    open(os.path.join(HERE, "small_chars.bin"), "wb").write(b"".join(tiles))
    cols = [(0, 0, 0)] * 145 + [tuple(int(v) for v in c) for c in pal] + [(0, 0, 0)] * (256 - 240)
    gba = b"".join(struct.pack("<H", (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10) for r, g, b in cols)
    open(os.path.join(HERE, "small_plt.bin"), "wb").write(gba)
    img = Image.new("RGB", (W * 2 + 8, H), (255, 0, 255))
    for L in range(2):
        for ty in range(16):
            for tx in range(22):
                t = tiles[maps[L * 352 + ty * 22 + tx]]
                for k, v in enumerate(t):
                    if v:
                        img.putpixel((L * (W + 8) + tx * 8 + k % 8, ty * 8 + k // 8), cols[v])
    img.save(os.path.join(HERE, "small.png"))
    print(f"{len(tiles)} tiles")


if __name__ == "__main__":
    main()

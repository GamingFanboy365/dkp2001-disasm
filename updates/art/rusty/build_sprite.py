#!/usr/bin/env python3
"""Rusty's in-race sprite (updates patch): his plane from the 65 angles the game uses,
in the game's own sprite format, from model.py (ours).

    python3 updates/art/rusty/build_sprite.py

writes, next to this script:
  plane.bin      the sprite: three levels of detail back to back (64, 32, 16 pixels), as
                 the racers' __spr_*framesshort, _01, _02 are laid out
  plane_pal.bin  its 16 colours (colour 0 transparent), BGR555
  plane.png      the 65 full-size frames, for looking at

The format (as tools/export_preview.py and spr_update_vram read it): a header of hwords
{offset of the tile-block table, 16, offset of the next level / 16 (0: last), 0, 0,
radius, height}, then 65 frame offsets; each frame one OAM piece {count 1; attr0 0;
attr1 size << 14; tile 0}; the tile-block table (hword offsets / 16 from it); each block
{tile count, then run-length hwords: bit 7 set = (n & 0x7f) + 1 literal hwords follow,
clear = (n & 0x7f) + 1 copies of byte (n >> 8) twice; 0 ends}. Frame 0 looks straight
down, 64 straight up; 1-63 are 7 rings of elevation (67.5 down to -67.5 degrees) times 9
headings from behind (0) round the side with the nose to the left (90) to head-on (180).
"""
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

LEVELS = ((64, 3, 32), (32, 2, 16), (16, 1, 8))          # pixels, OBJ size code, radius


def view_of(f):
    if f == 0:
        return (90.0, 0.0)
    if f == 64:
        return (-90.0, 0.0)
    ring, step = (f - 1) // 9, (f - 1) % 9
    return (90.0 - 22.5 * (ring + 1), 22.5 * step)


SEEDS = [                                   # shading ramps per material, refined below
    (40, 30, 44),                           # the dark edge, tyres, pupils
    (22, 100, 130), (34, 170, 205), (120, 222, 240),       # teal: shade, body, light
    (196, 130, 20), (252, 206, 48), (255, 240, 150),       # yellow: shade, body, light
    (150, 32, 30), (218, 56, 44),                          # red: shade, body
    (178, 60, 26), (232, 96, 40), (250, 160, 90),          # rust: shade, body, light
    (250, 244, 230),                                       # cream and white
    (54, 100, 200),                                        # denim
    (130, 130, 146),                                       # metal, the dark disc
]


def palette(frames):
    """15 colours for every opaque pixel of every frame (index 0 is transparent): k-means
    seeded with the model's shading ramps, so each material keeps its own colours."""
    px = np.concatenate([np.asarray(f)[..., :3][np.asarray(f)[..., 3] > 0] for f in frames]).astype(float)
    centres = np.array(SEEDS, float)
    for _ in range(12):
        d = ((px[:, None, :] - centres[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for k in range(len(centres)):
            sel = px[lab == k]
            if len(sel):
                centres[k] = 0.6 * sel.mean(0) + 0.4 * np.array(SEEDS[k])
    return np.clip(centres, 0, 255).astype(int)


def index_frame(img, pal):
    a = np.asarray(img).astype(int)
    rgb, mask = a[..., :3], a[..., 3] > 0
    d = ((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1)
    idx = d.argmin(-1) + 1
    idx[~mask] = 0
    return idx.astype(np.uint8)


def tiles_4bpp(idx):
    n = idx.shape[0] // 8
    out = bytearray()
    for ty in range(n):
        for tx in range(n):
            t = idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            for row in t:
                for x in range(0, 8, 2):
                    out.append(int(row[x]) | int(row[x + 1]) << 4)
    return bytes(out)


def rle(data):
    """The game's run-length hwords for tile data (an even number of bytes)."""
    hw = [data[i:i + 2] for i in range(0, len(data), 2)]
    out = bytearray()
    i = 0
    while i < len(hw):
        j = i
        if hw[i][0] == hw[i][1]:
            while j < len(hw) and j - i < 128 and hw[j] == hw[i]:
                j += 1
            if j - i >= 2:
                out += struct.pack("<H", (hw[i][0] << 8) | (j - i - 1))
                i = j
                continue
        j = i
        while j < len(hw) and j - i < 128:
            if j + 1 < len(hw) and hw[j] == hw[j + 1] and hw[j][0] == hw[j][1]:
                break
            j += 1
        j = max(j, i + 1)
        out += struct.pack("<H", 0x80 | (j - i - 1))
        out += b"".join(hw[i:j])
        i = j
    out += struct.pack("<H", 0)
    return bytes(out)


def level(frames_idx, size_code, radius, last):
    nf = len(frames_idx)
    head = 14 + 2 * nf
    pieces_at = head
    pieces = struct.pack("<HHHH", 1, 0, size_code << 14, 0)          # one piece for every frame
    chartab = (pieces_at + len(pieces) + 15) // 16 * 16
    blocks, offs = bytearray(), []
    first = (2 * nf + 15) // 16 * 16
    for idx in frames_idx:
        t = tiles_4bpp(idx)
        blk = struct.pack("<H", len(t) // 32) + rle(t)
        while (len(blocks) + first) % 16:
            blocks.append(0)
        offs.append((first + len(blocks)) // 16)
        blocks += blk
    while len(blocks) % 16:
        blocks.append(0)
    table = b"".join(struct.pack("<H", o) for o in offs)
    table += bytes(first - len(table))
    body = table + bytes(blocks)
    total = chartab + len(body)
    hdr = struct.pack("<7H", chartab, 16, 0 if last else total // 16, 0, 0, radius, radius)
    hdr += b"".join(struct.pack("<H", pieces_at) for _ in range(nf))
    out = bytearray(hdr + pieces)
    out += bytes(chartab - len(out))
    out += body
    assert len(out) == total and total % 16 == 0
    return bytes(out)


def main():
    mesh = model.build()
    renders = {px: [model.sprite(view_of(f), px=px, mesh=mesh) for f in range(65)] for px, _, _ in LEVELS}
    pal = palette(renders[64])
    data = bytearray()
    for k, (px, code, radius) in enumerate(LEVELS):
        idx = [index_frame(im, pal) for im in renders[px]]
        data += level(idx, code, radius, k == len(LEVELS) - 1)
    open(os.path.join(HERE, "plane.bin"), "wb").write(data)
    gba = bytearray(2)
    for r, g, b in pal:
        gba += struct.pack("<H", (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
    open(os.path.join(HERE, "plane_pal.bin"), "wb").write(gba)
    sheet = Image.new("RGBA", (65 * 64, 64), (255, 0, 255, 255))
    for f, im in enumerate(renders[64]):
        sheet.alpha_composite(im, (f * 64, 0))
    sheet.convert("RGB").save(os.path.join(HERE, "plane.png"))
    print(f"plane.bin {len(data)} bytes; palette {len(gba)} bytes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Rusty on the character select (updates patch): standing on the spot where Candy Kong's
figure is in Rare's sepia backdrop, holding up a VICTORY sign (the sign is only here, not
in races). From model.py (ours).

    python3 updates/art/rusty/build_cutout.py

writes, next to this script:
  cutout.bin, cutout_info.bin   his colour cut-out (shown when his slot is highlighted):
                                256-colour tiles and the piece list, in the format of the
                                select's cut-outs (clr_*_char_0 / clr_*_info_0)
  cutout_pal.bin                its colours (192, as set_spr_pal loads them; 0 transparent)
  sepia.bin, sepia_info.bin     the same figure in the backdrop's own sepia tones, drawn
                                over Candy's figure while another racer is highlighted;
                                its colours are indices 192-223 (sepia_pal.bin, 32 colours)
  cutout.png                    a look at both on the screen

Where DK's arm reaches in front of that spot in the backdrop, Rusty is cut away (from DK's
own cut-out's shape), so his feet stand behind it; the rest of him shows whole.

A piece record (12 bytes): position step y, x (signed, the first from the plot origin),
attr0 high byte (shape, 256 colours), attr1 high byte (size), tile step (32-byte units),
width, height, 0, 0.
"""
import math
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

VIEW = (10, 180)                             # facing straight out, from a little above
OVER = 8                                     # render at 8x the screen
FEET = (66, 143)                             # where his feet stand on the screen
PX_PER_UNIT = 10.4
BOARD = (65, 45, 46, 21)                     # sign centre x, y, width, height (screen px)
ORIGIN = (-7, -1)                            # the select's plot origin for this slot (fix_char_offset)
SEPIA = [(96, 48, 16), (112, 64, 24), (120, 72, 24), (128, 80, 32), (136, 88, 40), (144, 96, 48),
         (152, 104, 48), (160, 112, 56), (160, 120, 64), (168, 128, 72), (176, 136, 80), (184, 144, 88),
         (192, 160, 104), (200, 168, 120), (208, 176, 136), (208, 184, 144), (216, 192, 152),
         (224, 200, 168), (224, 208, 176), (232, 216, 192), (232, 224, 208), (240, 232, 216),
         (240, 240, 224), (248, 248, 240)]                      # Rare's backdrop palette's ramp
SHAPES = [((64, 64), 0, 3), ((64, 32), 1, 3), ((32, 64), 2, 3), ((32, 32), 0, 2), ((32, 16), 1, 2),
          ((16, 32), 2, 2), ((16, 16), 0, 1), ((32, 8), 1, 1), ((8, 32), 2, 1), ((16, 8), 1, 0),
          ((8, 16), 2, 0), ((8, 8), 0, 0)]


def figure():
    """Rusty and his sign on a transparent screen-sized layer (240 x 160 at OVER x)."""
    mesh = model.build_standing()
    size = 1400
    scale = PX_PER_UNIT * OVER
    img = model.render(VIEW, size, scale=scale, mesh=mesh, focus=(0.3, 4.5, -0.3))
    M = model.view_matrix(*VIEW)
    fc = M @ np.array((0.3, 4.5, -0.3))
    def to_px(p):
        q = M @ np.array(p, float)
        return size / 2 + (q[0] - fc[0]) * scale, size / 2 - (q[1] - fc[1]) * scale
    feet = to_px((0.45, 0.0, 0.0))
    layer = Image.new("RGBA", (240 * OVER, 160 * OVER), (0, 0, 0, 0))
    ox, oy = int(FEET[0] * OVER - feet[0]), int(FEET[1] * OVER - feet[1])
    layer.alpha_composite(img, (ox, oy))
    top = to_px(model.POLE_TOP)
    sign(layer, (top[0] + ox) / OVER, (top[1] + oy) / OVER)
    return layer


def sign(layer, pole_x, pole_y):
    """The VICTORY board, a weathered plank nailed to the pole's top."""
    cx, cy, w, h = BOARD
    S = OVER
    b = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], 2 * S, fill=(70, 44, 24, 255))
    inner = [S, S, w * S - S - 1, h * S - S - 1]
    d.rounded_rectangle(inner, 2 * S, fill=(236, 206, 150, 255))
    for k in range(1, 3):                                   # planks, lit at the top
        y = k * h * S // 3
        d.line([(S, y), (w * S - S, y)], fill=(176, 132, 84, 255), width=max(1, S // 2))
    d.rectangle([S, S, w * S - S, S + S], fill=(250, 232, 190, 255))
    for x, y in ((2.5, 2.5), (w - 2.5, 2.5), (2.5, h - 2.5), (w - 2.5, h - 2.5)):
        d.ellipse([(x - 0.8) * S, (y - 0.8) * S, (x + 0.8) * S, (y + 0.8) * S], fill=(110, 110, 120, 255))
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(9.5 * S))
    except OSError:
        f = ImageFont.load_default()
    t = "VICTORY"
    tw = d.textlength(t, font=f)
    tx, ty = (w * S - tw) / 2, (h * S - 11 * S) / 2
    for dx in (-S, 0, S):                                   # a dark edge round the letters
        for dy in (-S, 0, S):
            d.text((tx + dx, ty + dy), t, font=f, fill=(90, 20, 16, 255))
    d.text((tx, ty), t, font=f, fill=(226, 44, 40, 255))
    b = b.rotate(-3, resample=Image.BICUBIC, expand=True)
    layer.alpha_composite(b, (int((cx - b.width / S / 2) * S), int((cy - b.height / S / 2) * S)))


def gang_mask():
    """Where DK's arm (his figure below y 118) reaches in front of Candy's spot, from his own
    select cut-out (which matches his figure in the backdrop exactly) at his slot's plot
    origin: Rusty is cut away there, so his feet stand behind it; the rest of him is whole
    (owner's call)."""
    syms = {}
    for line in open(os.path.join(HERE, "..", "..", "..", "maps", "symbols.txt")):
        p = line.split()
        if len(p) >= 3:
            syms.setdefault(p[-1], int(p[0], 16))
    rom = open(os.path.join(HERE, "..", "..", "..", "baserom.gba"), "rb").read()
    mask = np.zeros((160, 240), bool)
    for name, origin, below in (("clr_kong", (-7, -1), 118),):
        fr = syms[name + "_frames"] - 0x08000000
        ch, size, n, info = struct.unpack_from("<IHHI", rom, fr + 4)
        ch -= 0x08000000
        p = info - 0x08000000
        x, y = origin
        tile = 0
        for k in range(n):
            dy, dx, a0, a1, adv, w, h = struct.unpack_from("<hhBBHBB", rom, p + 12 * k)
            x, y = x + dx, y + dy
            for ty in range(h // 8):
                for tx in range(w // 8):
                    t = ch + (tile + 2 * (ty * (w // 8) + tx)) * 32
                    for yy in range(8):
                        for xx in range(8):
                            if rom[t + yy * 8 + xx]:
                                sx, sy = x + tx * 8 + xx, y + ty * 8 + yy
                                if 0 <= sx < 240 and below <= sy < 160:
                                    mask[sy, sx] = True
            tile += adv
    return mask


def to_screen(layer):
    small = layer.resize((240, 160), Image.LANCZOS)
    a = np.asarray(small).astype(float)
    mask = a[..., 3] > 110
    rgb = np.clip(a[..., :3] / np.maximum(a[..., 3:4] / 255.0, 1e-3), 0, 255)
    edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
    rgb[edge] *= 0.5
    mask &= ~gang_mask()                                    # his feet behind DK's arm
    return rgb, without_slivers(mask)


def without_slivers(mask, least=25):
    """Drop bits of him the racers in front cut off from the rest (under `least` pixels)."""
    seen = np.zeros(mask.shape, bool)
    keep = np.zeros(mask.shape, bool)
    for y0, x0 in np.argwhere(mask):
        if seen[y0, x0]:
            continue
        stack, part = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            part.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v, u = y + dy, x + dx
                if 0 <= v < mask.shape[0] and 0 <= u < mask.shape[1] and mask[v, u] and not seen[v, u]:
                    seen[v, u] = True
                    stack.append((v, u))
        if len(part) >= least:
            for y, x in part:
                keep[y, x] = True
    return keep


def quantize(rgb, mask, n):
    px = rgb[mask]
    strip = Image.fromarray(px.reshape(1, -1, 3).astype(np.uint8), "RGB")
    q = strip.quantize(colors=n, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:3 * n]).reshape(n, 3)
    idx = np.zeros(mask.shape, np.uint8)
    idx[mask] = np.array(q).reshape(-1) + 1
    return idx, pal


def sepia(rgb, mask):
    lum = (0.3 * rgb[..., 0] + 0.59 * rgb[..., 1] + 0.11 * rgb[..., 2]) / 255.0
    lum = np.clip((lum - 0.08) / 0.85, 0, 1) ** 0.9
    k = np.clip((lum * (len(SEPIA) - 1)).round().astype(int), 0, len(SEPIA) - 1)
    idx = np.zeros(mask.shape, np.uint8)
    idx[mask] = 192 + k[mask]
    return idx


def pieces(mask):
    """Cover the figure's 8x8 cells with OBJ pieces, biggest first."""
    cells = np.zeros((20, 30), bool)
    for ty in range(20):
        for tx in range(30):
            cells[ty, tx] = mask[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].any()
    out = []
    left = cells.copy()
    while left.any():
        best = None
        ty, tx = np.argwhere(left)[0]
        for (w, h), shape, size in SHAPES:
            cw, ch = w // 8, h // 8
            for y0 in range(max(0, ty - ch + 1), ty + 1):
                for x0 in range(max(0, tx - cw + 1), tx + 1):
                    if y0 + ch > 20 or x0 + cw > 30:
                        continue
                    blk = left[y0:y0 + ch, x0:x0 + cw]
                    filled = blk.sum()
                    if filled == 0 or not blk[ty - y0, tx - x0]:
                        continue
                    score = filled - 2.5 * (cw * ch - filled)
                    if best is None or score > best[0]:
                        best = (score, x0, y0, w, h, shape, size)
        _, x0, y0, w, h, shape, size = best
        left[y0:y0 + h // 8, x0:x0 + w // 8] = False
        out.append((x0 * 8, y0 * 8, w, h, shape, size))
    return out


def encode(idx, plist):
    tiles = bytearray()
    info = bytearray()
    px, py = ORIGIN
    for x, y, w, h, shape, size in plist:
        for ty in range(h // 8):
            for tx in range(w // 8):
                tiles += idx[y + ty * 8:y + ty * 8 + 8, x + tx * 8:x + tx * 8 + 8].astype(np.uint8).tobytes()
        adv = (w // 8) * (h // 8) * 2
        info += struct.pack("<hhBBHBBBB", y - py, x - px, 0x20 | shape << 6, size << 6, adv, w, h, 0, 0)
        px, py = x, y
    return bytes(tiles), bytes(info)


def main():
    rgb, mask = to_screen(figure())
    plist = pieces(mask)
    cidx, cpal = quantize(rgb, mask, 150)
    sidx = sepia(rgb, mask)
    ctiles, info = encode(cidx, plist)
    stiles, _ = encode(sidx, plist)
    open(os.path.join(HERE, "cutout.bin"), "wb").write(ctiles)
    open(os.path.join(HERE, "cutout_info.bin"), "wb").write(info)
    open(os.path.join(HERE, "sepia.bin"), "wb").write(stiles)
    gba = lambda c: struct.pack("<H", (int(c[0]) >> 3) | (int(c[1]) >> 3) << 5 | (int(c[2]) >> 3) << 10)
    pal = b"".join(gba(c) for c in [(0, 0, 0)] + [tuple(c) for c in cpal])
    pal += bytes(0x180 - len(pal))
    open(os.path.join(HERE, "cutout_pal.bin"), "wb").write(pal)
    sp = b"".join(gba(c) for c in SEPIA) + bytes(64 - 2 * len(SEPIA))
    open(os.path.join(HERE, "sepia_pal.bin"), "wb").write(sp)
    shot = Image.new("RGB", (480, 160), (60, 60, 60))
    full = [(0, 0, 0)] + [tuple(int(v) for v in c) for c in cpal]
    for y in range(160):
        for x in range(240):
            if cidx[y, x]:
                shot.putpixel((x, y), full[cidx[y, x]])
                shot.putpixel((240 + x, y), SEPIA[sidx[y, x] - 192])
    shot.save(os.path.join(HERE, "cutout.png"))
    print(f"{len(plist)} pieces, {len(ctiles)} bytes of tiles each, {len(cpal)} colours")


if __name__ == "__main__":
    main()

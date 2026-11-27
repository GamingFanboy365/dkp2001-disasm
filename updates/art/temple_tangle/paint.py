#!/usr/bin/env python3
"""Temple Tangle's course picture (the 96x96 image beside the course list).

Original art for this project, painted by this script (no source images): a
stepped stone temple in jungle, its courtyard paved and walled into a maze,
framed by vines. No characters. Lit from the upper left like the game's other
course pictures.

    python3 updates/art/temple_tangle/paint.py

writes, next to this script:
  picture.png   the picture, 96x96, 175 colours (what the game shows)
  preview.png   the same at 4x, for looking at
  tiles.bin     8bpp tiles in the menu's sprite order (64x64, 64x32, 32x64, 32x32)
  palette.bin   176 GBA colours (index 0 transparent, 1-175 the picture)
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
S = 4                      # supersampling
W = 96 * S
HORIZON = 34 * S           # where the courtyard meets the trees
rng = random.Random(37)    # fixed seed: the picture is the same every run


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    """k > 1 lightens towards a warm white, k < 1 darkens towards a cool shadow."""
    if k >= 1:
        return lerp(c, (255, 250, 220), min(1, k - 1))
    return lerp((18, 26, 56), c, max(0, k))


def layer():
    return Image.new("RGBA", (W, W), (0, 0, 0, 0))


def paste(base, top, blur=0):
    if blur:
        top = top.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(top)


# ---------------------------------------------------------------- sky and hills
def sky(img):
    a = np.zeros((W, W, 4), np.uint8)
    top, low = np.array((92, 178, 214)), np.array((238, 240, 176))
    for y in range(W):
        t = min(1, (y / (HORIZON + 6 * S)) ** 1.3)
        a[y, :, :3] = top + (low - top) * t
    a[..., 3] = 255
    img.alpha_composite(Image.fromarray(a, "RGBA"))
    glow = layer()
    d = ImageDraw.Draw(glow)
    for r in range(30 * S, 0, -2 * S):
        al = int(70 * (1 - r / (30 * S)))
        d.ellipse([74 * S - r, 6 * S - r, 74 * S + r, 6 * S + r], fill=(255, 252, 214, al))
    paste(img, glow, 2 * S)


def hills(img):
    for depth, col, base, amp in ((0, (128, 176, 160), 22, 7), (1, (88, 148, 112), 27, 6)):
        h = layer()
        d = ImageDraw.Draw(h)
        pts = [(0, W)]
        ph = rng.random() * 6
        for x in range(0, W + S, S):
            y = base * S - amp * S * (0.6 * math.sin(x / (17 * S) + ph) + 0.4 * math.sin(x / (7 * S) + 2 * ph))
            pts.append((x, y))
        pts.append((W, W))
        d.polygon(pts, fill=col + (255,))
        paste(img, h, 1 * S if depth == 0 else 0)


# ---------------------------------------------------------------- foliage
def leafball(d, x, y, r, col, light=1.0):
    """A clump of foliage: dark underside, mid body, lit upper-left speckles."""
    d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.9], fill=shade(col, 0.55) + (255,))
    d.ellipse([x - r * 0.92, y - r * 0.92, x + r * 0.85, y + r * 0.62], fill=col + (255,))
    for _ in range(int(r / S * 2.2)):
        a = rng.uniform(math.pi * 0.9, math.pi * 1.75)
        rr = rng.uniform(0.15, 0.75) * r
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr * 0.8
        s = rng.uniform(0.9, 2.0) * S
        d.ellipse([px - s, py - s, px + s, py + s], fill=shade(col, 1.0 + 0.45 * light) + (255,))
    for _ in range(int(r / S)):
        a = rng.uniform(0, math.pi)
        rr = rng.uniform(0.3, 0.8) * r
        px, py = x + math.cos(a) * rr, y + math.sin(a) * rr * 0.7
        s = rng.uniform(0.8, 1.6) * S
        d.ellipse([px - s, py - s, px + s, py + s], fill=shade(col, 0.7) + (255,))


def canopy(img):
    back = layer()
    d = ImageDraw.Draw(back)
    for i in range(16):
        x = rng.uniform(-4, 100) * S
        leafball(d, x, rng.uniform(25, 31) * S, rng.uniform(6, 10) * S, (70, 130, 70), 0.6)
    paste(img, back)
    front = layer()
    d = ImageDraw.Draw(front)
    for i in range(14):
        x = rng.uniform(-4, 100) * S
        if 30 * S < x < 66 * S:
            continue                       # leave room for the temple
        leafball(d, x, rng.uniform(30, 35) * S, rng.uniform(5, 8) * S, (54, 124, 52))
    paste(img, front)


# ---------------------------------------------------------------- the temple
STONE = (150, 146, 128)
MOSS = (70, 128, 44)
MORTAR = (52, 50, 58)
OUT = (28, 30, 44, 255)          # the dark edge round shapes, as in the game's pictures


def stones(d, box, col, rows):
    """Block courses on a face: mortar lines, a few lighter and darker stones."""
    x0, y0, x1, y1 = box
    d.rectangle([x0, y0, x1, y1], fill=shade(col, 0.45) + (255,))
    h = (y1 - y0) / rows
    for r in range(rows):
        yy = y0 + r * h
        off = (r % 2) * 3 * S
        x = x0 - off
        while x < x1:
            w = rng.uniform(4, 7) * S
            k = rng.uniform(0.88, 1.08)
            bx0, bx1 = max(x0, x) + S * 0.6, min(x1, x + w) - S * 0.6
            if bx1 > bx0:
                d.rectangle([bx0, yy + S * 0.6, bx1, yy + h - S * 0.6], fill=shade(col, k) + (255,))
                d.rectangle([bx0, yy + S * 0.6, bx1, yy + S * 1.2], fill=shade(col, k + 0.25) + (255,))
            x += w


def temple(img):
    t = layer()
    d = ImageDraw.Draw(t)
    cx, base = 48 * S, 37 * S
    tiers = [(30, 5), (24, 5), (18, 5), (12, 4)]    # half width, height (in pixels)
    y = base
    side = 5 * S                                     # depth of the shaded right face
    for i, (hw, hh) in enumerate(tiers):
        hw, hh = hw * S, hh * S
        top = y - hh
        # right face (shadow side), front face, top ledge
        d.polygon([(cx + hw, y), (cx + hw + side, y - side * 0.6), (cx + hw + side, top - side * 0.6),
                   (cx + hw, top)], fill=shade(STONE, 0.5) + (255,), outline=OUT)
        d.rectangle([cx - hw, top, cx + hw, y], fill=STONE + (255,))
        stones(d, (cx - hw, top, cx + hw, y), STONE, 2)
        d.polygon([(cx - hw, top), (cx + hw, top), (cx + hw + side, top - side * 0.6),
                   (cx - hw + side, top - side * 0.6)], fill=shade(STONE, 1.45) + (255,), outline=OUT)
        d.line([(cx - hw, top), (cx - hw, y)], fill=OUT, width=S)
        # moss hanging over the ledge
        for _ in range(5 + 2 * i):
            mx = rng.uniform(cx - hw, cx + hw)
            ml = rng.uniform(1.5, 3.5) * S
            d.rectangle([mx, top, mx + rng.uniform(1, 2.5) * S, top + ml], fill=MOSS + (255,))
            d.rectangle([mx, top, mx + S, top + ml * 0.6], fill=shade(MOSS, 1.3) + (255,))
        y = top
    # the shrine on top, with its dark doorway
    sw, sh = 7 * S, 7 * S
    d.rectangle([cx - sw, y - sh, cx + sw, y], fill=shade(STONE, 1.05) + (255,))
    d.polygon([(cx + sw, y), (cx + sw + side, y - side * 0.6), (cx + sw + side, y - sh - side * 0.6),
               (cx + sw, y - sh)], fill=shade(STONE, 0.6) + (255,))
    d.polygon([(cx - sw - S, y - sh), (cx + sw + S, y - sh), (cx + sw + side + S, y - sh - side * 0.6),
               (cx - sw + side - S, y - sh - side * 0.6)], fill=shade(STONE, 1.3) + (255,))
    d.rectangle([cx - 3 * S, y - 5 * S, cx + 3 * S, y], fill=(40, 34, 30, 255))
    d.ellipse([cx - 3 * S, y - 7 * S, cx + 3 * S, y - 3 * S], fill=(40, 34, 30, 255))
    # stairs down the front
    sy = y
    while sy < base:
        d.rectangle([cx - 4 * S, sy, cx + 4 * S, sy + S], fill=shade(STONE, 1.18) + (255,))
        d.rectangle([cx - 4 * S, sy + S, cx + 4 * S, sy + 2 * S], fill=shade(STONE, 0.8) + (255,))
        sy += 2 * S
    paste(img, t)


# ---------------------------------------------------------------- the courtyard maze
CAM_H, FOCAL, NEAR = 22.0, 60.0 * S, 6.0


def project(x, z, h=0.0):
    k = FOCAL / (z + NEAR)
    return 48 * S + x * k, HORIZON + (CAM_H - h) * k * 0.62


PAVE = (206, 128, 52)


def courtyard(img):
    g = layer()
    d = ImageDraw.Draw(g)
    far, near = 70.0, 0.0
    # paving, in rows that darken with distance, with joint lines
    zs = [far * (i / 40) ** 1.8 for i in range(41)][::-1]
    for i in range(len(zs) - 1):
        z0, z1 = zs[i], zs[i + 1]
        t = z1 / far
        col = lerp(shade(PAVE, 1.1), lerp(PAVE, (120, 150, 120), 0.45), t ** 0.7)
        a, b = project(-200, z0), project(200, z1)
        d.rectangle([0, a[1], W, b[1] + 1], fill=col + (255,))
    for gx in range(-60, 61, 6):
        d.line([project(gx, 0), project(gx, far)], fill=shade(PAVE, 0.82) + (255,), width=1)
    for z in range(0, 70, 5):
        d.line([project(-80, z), project(80, z)], fill=shade(PAVE, 0.82) + (255,), width=1)
    # speckle (grit and grass in the joints)
    for _ in range(600):
        x, y = rng.uniform(0, W), rng.uniform(HORIZON, W)
        c = rng.choice([shade(PAVE, 0.6), shade(PAVE, 0.6), shade(PAVE, 1.3), (150, 140, 120)])
        d.rectangle([x, y, x + S, y + S], fill=c + (255,))
    paste(img, g)

    # maze walls on a 6-unit grid; (x0, z0, x1, z1) along grid lines
    walls = [(-30, 6, -6, 6), (6, 6, 30, 6), (-3, 9, 12, 9), (-30, 6, -30, 24), (30, 6, 30, 30),
             (-18, 12, 18, 12), (-18, 12, -18, 30), (18, 12, 18, 24), (-6, 18, -6, 30),
             (6, 18, 24, 18), (-30, 30, -12, 30), (0, 24, 12, 24), (12, 24, 12, 36),
             (-24, 36, 6, 36), (24, 30, 24, 42), (-36, 42, 18, 42), (-36, 18, -36, 42),
             (36, 12, 36, 48), (-12, 48, 30, 48), (-42, 48, -24, 48)]
    walls.sort(key=lambda w: -max(w[1], w[3]))
    sh = layer()
    ds = ImageDraw.Draw(sh)
    wl = layer()
    dw = ImageDraw.Draw(wl)
    H, T = 2.6, 0.9                       # wall height, half thickness
    for x0, z0, x1, z1 in walls:
        if z0 == z1:
            xa, xb, za, zb = min(x0, x1) - T, max(x0, x1) + T, z0 - T, z0 + T
        else:
            xa, xb, za, zb = x0 - T, x0 + T, min(z0, z1) - T, max(z0, z1) + T
        # shadow cast down-right on the paving
        ds.polygon([project(xa, za), project(xb + 2.2, za), project(xb + 2.2, zb - 1.5), project(xa, zb - 1.5)],
                   fill=(60, 40, 20, 110))
        # near face, then the right side, then the lit top
        dw.polygon([project(xb, za), project(xb, zb), project(xb, zb, H), project(xb, za, H)],
                   fill=shade(STONE, 0.45) + (255,), outline=OUT)
        dw.polygon([project(xa, za), project(xb, za), project(xb, za, H), project(xa, za, H)],
                   fill=shade(STONE, 0.85) + (255,), outline=OUT)
        bx = xa + rng.uniform(1, 3)
        while bx < xb - 0.5:
            dw.line([project(bx, za, 0.2), project(bx, za, H - 0.2)], fill=shade(STONE, 0.5) + (255,), width=max(1, S // 2))
            bx += rng.uniform(2.5, 4.5)
        dw.line([project(xa, za, H * 0.5), project(xb, za, H * 0.5)], fill=shade(STONE, 0.6) + (255,), width=max(1, S // 2))
        dw.polygon([project(xa, za, H), project(xb, za, H), project(xb, zb, H), project(xa, zb, H)],
                   fill=shade(STONE, 1.5) + (255,), outline=OUT)
        # moss on some tops
        if rng.random() < 0.6:
            mx = rng.uniform(xa, xb)
            mz = rng.uniform(za, zb)
            p = project(mx, mz, H)
            r = FOCAL / (mz + NEAR) * 0.9
            dw.ellipse([p[0] - r, p[1] - r * 0.5, p[0] + r, p[1] + r * 0.5], fill=MOSS + (255,))
    paste(img, sh, 0.6 * S)
    paste(img, wl)


# ---------------------------------------------------------------- the critter
FROG = (40, 110, 220)


def blob(d, box, col, light=True):
    """A rounded shape: dark edge, body colour, a lit patch towards the upper left."""
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=col + (255,), outline=OUT, width=max(1, S // 2))
    if light:
        w, h = x1 - x0, y1 - y0
        d.ellipse([x0 + w * 0.15, y0 + h * 0.1, x0 + w * 0.6, y0 + h * 0.45], fill=shade(col, 1.35) + (255,))


def frog(img):
    """Our own jungle critter: a round blue tree frog with dark spots and big gold eyes,
    sitting on the nearest wall, looking out at the player."""
    f = layer()
    d = ImageDraw.Draw(f)
    bx, by = project(5, 9, 2.6)              # on top of a near wall, right of centre
    u = 1.35 * S                              # its scale
    cx, base = bx, by + 1.5 * u
    # shadow on the wall top
    d.ellipse([cx - 11 * u, base - 2 * u, cx + 11 * u, base + 2 * u], fill=(20, 24, 40, 120))
    # back legs, folded at the sides
    blob(d, [cx - 13 * u, base - 8 * u, cx - 4 * u, base + 1 * u], shade(FROG, 0.8))
    blob(d, [cx + 4 * u, base - 8 * u, cx + 13 * u, base + 1 * u], shade(FROG, 0.7))
    # body
    blob(d, [cx - 9 * u, base - 17 * u, cx + 9 * u, base], FROG)
    # pale belly
    d.ellipse([cx - 4.5 * u, base - 9.5 * u, cx + 4.5 * u, base - 1.5 * u], fill=(236, 214, 120, 255))
    d.ellipse([cx - 3 * u, base - 9 * u, cx + 1 * u, base - 6 * u], fill=(252, 238, 170, 255))
    # spots
    for sx, sy, r in ((-7, -11, 1.4), (7, -12, 1.2), (-7.5, -6.5, 1.0), (7, -7.5, 1.1)):
        d.ellipse([cx + (sx - r) * u, base + (sy - r) * u, cx + (sx + r) * u, base + (sy + r) * u], fill=(20, 26, 60, 255))
    # front legs, then feet with round toe pads
    for fx in (-4, 4):
        blob(d, [cx + (fx - 2) * u, base - 6 * u, cx + (fx + 2) * u, base + 0.5 * u], shade(FROG, 0.85))
    for fx in (-4, 4):
        for tx in (-1.6, 0, 1.6):
            x = cx + (fx + tx) * u
            d.ellipse([x - 1.1 * u, base - 1.4 * u, x + 1.1 * u, base + 0.8 * u], fill=shade(FROG, 1.2) + (255,), outline=OUT)
    # big eyes on top of the head
    for ex in (-4.5, 4.5):
        x, y = cx + ex * u, base - 16.5 * u
        blob(d, [x - 3.4 * u, y - 3.4 * u, x + 3.4 * u, y + 3 * u], FROG, light=False)
        d.ellipse([x - 2.5 * u, y - 2.5 * u, x + 2.5 * u, y + 2.2 * u], fill=(250, 196, 40, 255), outline=OUT)
        d.ellipse([x - 1.0 * u, y - 1.9 * u, x + 1.0 * u, y + 1.6 * u], fill=(16, 14, 20, 255))
        d.ellipse([x - 1.9 * u, y - 2.1 * u, x - 0.7 * u, y - 0.9 * u], fill=(255, 255, 255, 255))
    # a wide grin
    d.arc([cx - 6.5 * u, base - 16 * u, cx + 6.5 * u, base - 10 * u], 20, 160, fill=OUT, width=int(1.6 * S))
    paste(img, f)


# ---------------------------------------------------------------- vines and framing
LEAF = (60, 140, 48)


def leaf(d, x, y, ang, size, col, bend=0.25):
    """A pointed leaf along a curved midrib: lit half, shaded half, dark edge."""
    n = 14
    rib, left, right = [], [], []  # noqa
    for i in range(n + 1):
        t = i / n
        a = ang + bend * t * t
        px = x + sum(math.cos(ang + bend * (k / n) ** 2) for k in range(i)) * size / n
        py = y + sum(math.sin(ang + bend * (k / n) ** 2) for k in range(i)) * size / n
        w = size * 0.3 * math.sin(math.pi * min(1, t * 1.15)) ** 0.8
        nx, ny = -math.sin(a), math.cos(a)
        rib.append((px, py))
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    d.polygon(left + rib[::-1], fill=shade(col, 1.3) + (255,))
    d.polygon(right + rib[::-1], fill=shade(col, 0.75) + (255,))
    d.line(left + right[::-1] + [left[0]], fill=OUT, width=max(1, S // 2))
    d.line(rib, fill=shade(col, 0.55) + (255,), width=max(1, S // 2))


def vines(img):
    v = layer()
    d = ImageDraw.Draw(v)
    for x0, length, sway in ((4, 58, 1.0), (13, 30, -1.0), (84, 46, -1.0), (92, 70, 1.0), (24, 14, 1.0), (72, 20, -1.0)):
        pts = []
        for i in range(0, length + 1, 2):
            y = i * S
            x = x0 * S + sway * math.sin(i / 9.0) * 3 * S
            pts.append((x, y))
        d.line(pts, fill=(70, 92, 40, 255), width=int(1.6 * S))
        d.line([(p[0] - S * 0.4, p[1]) for p in pts], fill=(120, 150, 70, 255), width=max(1, S // 2))
        for i, (x, y) in enumerate(pts[1::2]):
            a = math.pi / 2 + (0.9 if i % 2 else -0.9) + rng.uniform(-0.3, 0.3)
            leaf(d, x, y, a, rng.uniform(4, 6.5) * S, lerp(LEAF, (90, 170, 60), rng.random()))
    # big leaves in the lower corners
    for x, y, a in ((0, 96, -0.9), (4, 96, -1.3), (-2, 86, -0.4), (96, 96, -2.2), (92, 96, -1.8), (98, 84, -2.7)):
        leaf(d, x * S, y * S, a, rng.uniform(15, 20) * S, lerp((40, 118, 40), LEAF, rng.random()))
    paste(img, v)


def finish(img):
    a = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:W, 0:W] / W - 0.5
    vig = 1 - 0.18 * (xx ** 2 + yy ** 2) ** 1.2
    a[..., :3] *= vig[..., None]
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA").convert("RGB")
    out = ImageEnhance.Color(out).enhance(1.4)        # the game's pictures are saturated
    out = ImageEnhance.Brightness(out).enhance(1.1)
    out = ImageEnhance.Contrast(out).enhance(1.12)
    return out.convert("RGBA")


def paint():
    img = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    sky(img)
    hills(img)
    canopy(img)
    temple(img)
    courtyard(img)
    frog(img)
    vines(img)
    img = finish(img)
    small = img.convert("RGB").resize((96, 96), Image.LANCZOS)
    # GBA colours are 5 bits per channel
    a = (np.asarray(small) >> 3 << 3) | 4
    small = Image.fromarray(a.astype(np.uint8), "RGB")
    pic = small.quantize(colors=175, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return pic


def save(pic):
    pal = pic.getpalette()[:175 * 3]
    idx = np.asarray(pic).astype(np.uint8) + 1                 # 1-175; 0 is transparent
    # the picture as the game shows it
    out = Image.fromarray(idx, "P")
    full = [0, 0, 0] + pal + [0, 0, 0] * (256 - 176)
    out.putpalette(full)
    out.save(os.path.join(HERE, "picture.png"))
    out.convert("RGB").resize((384, 384), Image.NEAREST).save(os.path.join(HERE, "preview.png"))
    # tiles: menu_image's four sprites, each in 8x8 tiles row by row (1D mapping)
    data = bytearray()
    for x0, y0, w, h in ((0, 0, 64, 64), (0, 64, 64, 32), (64, 0, 32, 64), (64, 64, 32, 32)):
        for ty in range(y0, y0 + h, 8):
            for tx in range(x0, x0 + w, 8):
                data += idx[ty:ty + 8, tx:tx + 8].tobytes()
    assert len(data) == 9216
    open(os.path.join(HERE, "tiles.bin"), "wb").write(data)
    gba = bytearray(2)                                          # index 0
    for i in range(175):
        r, g, b = (c >> 3 for c in pal[3 * i:3 * i + 3])
        gba += (r | g << 5 | b << 10).to_bytes(2, "little")
    assert len(gba) == 352
    open(os.path.join(HERE, "palette.bin"), "wb").write(gba)


if __name__ == "__main__":
    save(paint())

#!/usr/bin/env python3
"""The cup's FINAL RESULTS background (240x160).

Original art for this project, painted by this script (no source images, no
characters or trademarks): a tropical sunset stage. A warm sky over the sea, palms
framing the sides, bunting and confetti, a ribbon banner across the top for the title,
soft see-through strips where the four standings rows sit (the text and racer heads
are sprites drawn over them), and a little wooden podium on the sand. Lit from the upper left like the game's
menu art.

    python3 updates/art/cup_results/paint.py

writes, next to this script:
  picture.png   the background as the game shows it (240x160, 255 colours)
  preview.png   the same at 3x
  tiles.bin     8bpp tiles, duplicates removed
  map.bin       a 32x32 screen map (hword tile numbers) for the 30x20 tiles shown
  palette.bin   256 GBA colours (index 0 unused: it's the backdrop)
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
S = 4
W, H = 240 * S, 160 * S
rng = random.Random(2001)
OUT = (34, 22, 30, 255)

# where the sprites go (screen pixels): keep these areas calm
TITLE_Y = (4, 28)          # the title text, centred
BOARD = (14, 32, 226, 152)  # the four rows: 1ST at x 44, heads at 120, points at 176


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def shade(c, k):
    if k >= 1:
        return lerp(c, (255, 246, 214), min(1, k - 1))
    return lerp((26, 14, 40), c, max(0, k))


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def paste(base, top, blur=0):
    if blur:
        top = top.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(top)


def sky(img):
    a = np.zeros((H, W, 4), np.uint8)
    stops = [(0.0, (58, 34, 108)), (0.35, (186, 70, 112)), (0.62, (250, 150, 80)), (0.72, (255, 214, 120))]
    for y in range(H):
        t = y / H
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0] or i == len(stops) - 2:
                u = min(1, max(0, (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])))
                a[y, :, :3] = lerp(stops[i][1], stops[i + 1][1], u)
                break
    a[..., 3] = 255
    img.alpha_composite(Image.fromarray(a, "RGBA"))
    # the sun, low and soft, behind the board
    g = layer()
    d = ImageDraw.Draw(g)
    cx, cy = 120 * S, 116 * S
    for r in range(70 * S, 0, -3 * S):
        al = int(110 * (1 - r / (70 * S)) ** 1.5)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 236, 160, al))
    paste(img, g, 3 * S)
    # long streaky clouds
    c = layer()
    d = ImageDraw.Draw(c)
    for _ in range(9):
        y = rng.uniform(30, 90) * S
        x = rng.uniform(-40, 240) * S
        w = rng.uniform(40, 90) * S
        d.ellipse([x, y, x + w, y + rng.uniform(3, 6) * S], fill=(255, 190, 170, 130))
        d.ellipse([x + 6 * S, y - 2 * S, x + w * 0.7, y + 2 * S], fill=(255, 220, 200, 90))
    paste(img, c, 2 * S)


def sea(img):
    s = layer()
    d = ImageDraw.Draw(s)
    top = 116 * S
    for y in range(top, 147 * S, S):
        t = (y - top) / (H - top)
        d.rectangle([0, y, W, y + S], fill=lerp((214, 110, 120), (60, 40, 110), t ** 0.7) + (255,))
    # sun glitter on the water
    for _ in range(140):
        y = rng.uniform(117, 158) * S
        spread = (y / S - 112) * 2.2
        x = (120 + rng.uniform(-spread, spread)) * S
        w = rng.uniform(2, 7) * S
        d.rectangle([x, y, x + w, y + S * 0.8], fill=(255, 226, 150, 200))
    paste(img, s)


def palm(d, x0, y0, lean, height, scale=1.0):
    """A palm silhouette with a lit edge: curved trunk, a crown of fronds."""
    pts = []
    for i in range(21):
        t = i / 20
        pts.append((x0 + lean * t * t * S, y0 - height * t * S))
    for i in range(len(pts) - 1):
        w = (5 - 2.5 * i / 20) * S * scale
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        d.line([(x1, y1), (x2, y2)], fill=(52, 26, 44, 255), width=int(w))
        d.line([(x1 - w * 0.25, y1), (x2 - w * 0.25, y2)], fill=(120, 60, 62, 255), width=max(1, int(w * 0.3)))
        if i % 2 == 0:
            d.line([(x1 - w / 2, y1), (x1 + w / 2, y1 - S)], fill=(36, 18, 34, 255), width=S)
    tx, ty = pts[-1]
    for k in range(9):
        a = math.pi * (1.02 + k * 0.12) + rng.uniform(-0.06, 0.06)
        length = rng.uniform(28, 40) * S * scale
        upper, lower, rim = [], [], []
        for j in range(13):
            t = j / 12
            px = tx + math.cos(a) * length * t
            py = ty + math.sin(a) * length * t * 0.7 + (t * t) * 24 * S * scale
            dx = math.cos(a) * length / 12
            dy = math.sin(a) * length / 12 * 0.7 + 2 * t * 24 * S * scale / 12
            m = math.hypot(dx, dy) or 1
            nx, ny = -dy / m, dx / m
            w = math.sin(math.pi * min(1, t * 1.1)) * 7 * S * scale
            upper.append((px + nx * w, py + ny * w))
            lower.append((px - nx * w, py - ny * w))
        d.polygon(upper + lower[::-1], fill=(38, 20, 38, 255))
        # serrated leaflets along the lower edge
        for j in range(1, 12):
            (ux, uy), (lx, ly) = upper[j], lower[j]
            d.line([(lx, ly), (lx + (lx - ux) * 0.35, ly + (ly - uy) * 0.35 + 3 * S * scale)], fill=(38, 20, 38, 255), width=max(1, S))
        # backlit: a warm rim along the side facing the sun
        sun_side = upper if upper[6][1] > lower[6][1] else lower
        d.line(sun_side[1:11], fill=(255, 150, 90, 255), width=max(1, S // 2 * 2 // 2 + 1))
    d.ellipse([tx - 5 * S, ty - 4 * S, tx + 5 * S, ty + 5 * S], fill=(60, 30, 44, 255))


def palms(img):
    p = layer()
    d = ImageDraw.Draw(p)
    palm(d, 4 * S, 160 * S, 26, 150, 1.05)
    palm(d, 236 * S, 160 * S, -28, 140, 1.0)
    palm(d, -6 * S, 160 * S, 40, 108, 0.8)
    palm(d, 248 * S, 160 * S, -40, 100, 0.75)
    paste(img, p)


def bunting(img):
    b = layer()
    d = ImageDraw.Draw(b)
    cols = [(232, 60, 60), (250, 200, 40), (60, 170, 230), (80, 200, 90), (240, 120, 200)]
    for x0, x1, sag, y0 in ((2, 46, 6, 40), (194, 238, 6, 40)):
        pts = [(x0 + (x1 - x0) * t / 20, y0 + sag * math.sin(math.pi * t / 20)) for t in range(21)]
        d.line([(x * S, y * S) for x, y in pts], fill=(70, 40, 50, 255), width=S)
        for i in range(1, 20, 2):
            x, y = pts[i]
            c = cols[(i // 2 + (x0 > 0)) % len(cols)]
            tri = [(x * S - 4 * S, y * S), (x * S + 4 * S, y * S), (x * S, y * S + 9 * S)]
            d.polygon(tri, fill=c + (255,), outline=OUT)
            d.polygon([tri[0], (x * S, y * S), tri[2]], fill=shade(c, 1.25) + (255,))
    paste(img, b)


ROWS = (38, 66, 94, 122)    # the rows' top edges (text 16 high)


def plates(img):
    """A soft, see-through dark strip behind each standings row, so the text reads over
    the bright sky and sun; the scene shows between and through them."""
    p = layer()
    d = ImageDraw.Draw(p)
    for y in ROWS:
        d.rounded_rectangle([18 * S, (y - 4) * S, 222 * S, (y + 19) * S], 7 * S, fill=(24, 10, 40, 120))
        d.rounded_rectangle([18 * S, (y - 4) * S, 222 * S, (y - 3) * S], 2 * S, fill=(255, 220, 180, 50))
    paste(img, p, 0.6 * S)


def beach(img):
    """Sand along the bottom and a little three-step wooden podium (gold, silver and
    bronze trims), the sea behind."""
    b = layer()
    d = ImageDraw.Draw(b)
    top = 146 * S
    d.rectangle([0, top, W, H], fill=(232, 176, 120, 255))
    d.rectangle([0, top, W, top + S], fill=(255, 214, 160, 255))
    for _ in range(160):
        x, y = rng.uniform(0, W), rng.uniform(top + S, H)
        d.rectangle([x, y, x + S, y + S], fill=rng.choice([(206, 148, 100), (248, 200, 146)]) + (255,))
    steps = [(-30, -10, 7, (196, 200, 214)), (-10, 10, 12, (250, 210, 70)), (10, 30, 4, (214, 136, 74))]
    for x0, x1, h, trim in steps:
        X0, X1, Y0 = (120 + x0) * S, (120 + x1) * S, (153 - h) * S
        d.rectangle([X0 + 2 * S, Y0 + 2 * S, X1 + 2 * S, 160 * S], fill=(110, 60, 50, 140))
        d.rectangle([X0, Y0, X1, 160 * S], fill=(150, 88, 56, 255), outline=OUT)
        d.rectangle([X0, Y0, X1, Y0 + 2 * S], fill=trim + (255,))
        d.rectangle([X0, Y0 + 2 * S, X0 + 2 * S, 160 * S], fill=(190, 120, 80, 255))
        d.rectangle([X1 - 2 * S, Y0 + 2 * S, X1, 160 * S], fill=(110, 62, 44, 255))
    paste(img, b)


def banner(img):
    """A red ribbon with gold edges across the top, under the title."""
    b = layer()
    d = ImageDraw.Draw(b)
    y0, y1 = TITLE_Y[0] * S, TITLE_Y[1] * S
    x0, x1 = 40 * S, 200 * S
    # tails
    for sx, dirn in ((x0, -1), (x1, 1)):
        tail = [(sx, y0 + 6 * S), (sx + dirn * 26 * S, y0 + 6 * S), (sx + dirn * 18 * S, (y0 + y1) / 2 + 3 * S),
                (sx + dirn * 26 * S, y1 + 6 * S), (sx, y1 + 6 * S)]
        d.polygon(tail, fill=(150, 26, 40, 255), outline=OUT)
    d.rectangle([x0, y0 + 2 * S, x1, y1 + 2 * S], fill=(206, 40, 52, 255), outline=OUT)
    d.rectangle([x0, y0 + 2 * S, x1, y0 + 5 * S], fill=(238, 96, 96, 255))
    d.rectangle([x0, y1 - S, x1, y1 + 2 * S], fill=(150, 26, 40, 255))
    for yy in (y0 + 2 * S, y1 + S):
        d.line([(x0, yy), (x1, yy)], fill=(240, 196, 80, 255), width=S)
    paste(img, b)


def confetti(img):
    c = layer()
    d = ImageDraw.Draw(c)
    cols = [(255, 90, 90), (255, 214, 60), (90, 200, 255), (120, 230, 110), (255, 140, 220), (255, 255, 255)]
    bx0, by0, bx1, by1 = 14 * S, 30 * S, 226 * S, 160 * S
    n = 0
    while n < 36:
        x, y = rng.uniform(0, 240) * S, rng.uniform(0, 160) * S
        if bx0 - 4 * S < x < bx1 + 4 * S and by0 - 4 * S < y < by1 + 4 * S:
            continue                                        # not over the rows
        if 36 * S < x < 204 * S and y < 34 * S:
            continue                                        # nor the title
        col = rng.choice(cols)
        a = rng.uniform(0, math.pi)
        w, h = rng.uniform(1.0, 1.8) * S, rng.uniform(0.6, 1.0) * S
        pts = [(x + math.cos(a) * w - math.sin(a) * h, y + math.sin(a) * w + math.cos(a) * h),
               (x - math.cos(a) * w - math.sin(a) * h, y - math.sin(a) * w + math.cos(a) * h),
               (x - math.cos(a) * w + math.sin(a) * h, y - math.sin(a) * w - math.cos(a) * h),
               (x + math.cos(a) * w + math.sin(a) * h, y + math.sin(a) * w - math.cos(a) * h)]
        d.polygon(pts, fill=col + (255,))
        n += 1
    paste(img, c)


def paint():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sky(img)
    sea(img)
    beach(img)
    palms(img)
    bunting(img)
    plates(img)
    banner(img)
    confetti(img)
    out = img.convert("RGB")
    out = ImageEnhance.Color(out).enhance(1.15)
    small = out.resize((240, 160), Image.LANCZOS)
    a = (np.asarray(small) >> 3 << 3) | 4
    return Image.fromarray(a.astype(np.uint8), "RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT,
                                                               dither=Image.Dither.NONE)


def save(pic):
    pal = pic.getpalette()[:255 * 3]
    idx = np.asarray(pic).astype(np.uint8) + 1               # 1-255; 0 is the backdrop
    full = [0, 0, 0] + pal
    out = Image.fromarray(idx, "P")
    out.putpalette(full + [0] * (768 - len(full)))
    out.save(os.path.join(HERE, "picture.png"))
    out.convert("RGB").resize((720, 480), Image.NEAREST).save(os.path.join(HERE, "preview.png"))
    tiles, index = [], {}
    smap = [0] * (32 * 32)
    for ty in range(20):
        for tx in range(30):
            t = idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes()
            if t not in index:
                index[t] = len(tiles)
                tiles.append(t)
            smap[ty * 32 + tx] = index[t]
    assert len(tiles) <= 1024
    open(os.path.join(HERE, "tiles.bin"), "wb").write(b"".join(tiles))
    open(os.path.join(HERE, "map.bin"), "wb").write(b"".join(v.to_bytes(2, "little") for v in smap))
    gba = bytearray(2)
    for i in range(255):
        r, g, b = (c >> 3 for c in pal[3 * i:3 * i + 3])
        gba += (r | g << 5 | b << 10).to_bytes(2, "little")
    open(os.path.join(HERE, "palette.bin"), "wb").write(gba)
    print(len(tiles), "tiles", len(tiles) * 64, "bytes")


if __name__ == "__main__":
    save(paint())

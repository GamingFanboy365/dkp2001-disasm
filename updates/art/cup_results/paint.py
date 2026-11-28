#!/usr/bin/env python3
"""The cup's results backgrounds (240x160): race/ after each race (RESULTS), final/
after the cup (FINAL RESULTS).

Original art for this project, painted by this script (no source images, no
characters or trademarks). In the style of the game's menu backgrounds (bright
daylight, soft shaded clouds, smooth rendered shading, high colour): a sunny beach at
the end of a race. Blue sky and soft clouds, hazy green islands, a turquoise sea, sand,
two palms framing the scene, a string of checkered finish pennants, a shaded ribbon
banner across the top for the title, and soft see-through strips where the four standings rows sit (the text and
racer heads are sprites drawn over it).

BEST TIMES (Clock Race) is a jungle clearing: green-gold light through the canopy, a
stone ruin and a waterfall in the haze, tree trunks, vines, ferns, flowers, a parrot,
butterflies, sun flecks, a plane of our own design parked three-quarters toward us on a
patch of earth to the right (a supply crate and a fuel drum beside it), and a mossy
carved stone tablet for the title.

FINAL RESULTS is a trophy room instead: wood-panelled walls under spotlights, shelves of
gleaming trophies (generic cups of our own design: gold, silver, bronze), red velvet
curtains with gold tassels, a gold plaque for the title.

    python3 updates/art/cup_results/paint.py

writes, in race/, final/ and best/ next to this script:
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

import plane3d

HERE = os.path.dirname(os.path.abspath(__file__))
S = 4
W, H = 240 * S, 160 * S
rng = random.Random(2001)
OUT = (40, 36, 60, 255)
ROWS = (38, 66, 94, 122)        # the standings rows' top edges (text 16 high)
TITLE = (4, 28)                 # the title's band
HORIZON = 100                   # sea starts
SHORE = 136                     # sand starts


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def shade(c, k):
    if k >= 1:
        return lerp(c, (255, 255, 240), min(1, k - 1))
    return lerp((20, 30, 70), c, max(0, k))


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def paste(base, top, blur=0):
    if blur:
        top = top.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(top)


def vgrad(d, box, top, bottom):
    x0, y0, x1, y1 = box
    for y in range(int(y0), int(y1)):
        t = (y - y0) / max(1, y1 - y0)
        d.line([(x0, y), (x1, y)], fill=lerp(top, bottom, t) + (255,))


def sky(img):
    d = ImageDraw.Draw(img)
    vgrad(d, (0, 0, W, HORIZON * S), (40, 96, 214), (150, 214, 250))


def cloud(d, x, y, w, h):
    """A soft cumulus: lobes lit from the upper left, a blue-grey underside."""
    lobes = []
    for i in range(7):
        lx = x + (i / 6 - 0.5) * w * 0.9 + rng.uniform(-w * 0.05, w * 0.05)
        r = h * rng.uniform(0.45, 0.8) * (1 - abs(i / 6 - 0.5) * 0.9)
        lobes.append((lx, y - r * 0.3, r))
    for lx, ly, r in lobes:
        d.ellipse([lx - r, ly - r * 0.6 + h * 0.18, lx + r, ly + r * 0.6 + h * 0.18], fill=(176, 196, 226, 255))
    for lx, ly, r in lobes:
        d.ellipse([lx - r, ly - r * 0.7, lx + r, ly + r * 0.55], fill=(236, 244, 252, 255))
    for lx, ly, r in lobes:
        d.ellipse([lx - r * 0.75, ly - r * 0.65, lx + r * 0.25, ly], fill=(255, 255, 255, 255))


def clouds(img):
    c = layer()
    d = ImageDraw.Draw(c)
    for x, y, w, h in ((66, 52, 80, 20), (178, 48, 86, 22), (122, 80, 64, 14), (20, 88, 46, 10), (222, 86, 46, 10)):
        cloud(d, x * S, y * S, w * S, h * S)
    paste(img, c, 0.7 * S)


def sun_and_gulls(img):
    g = layer()
    d = ImageDraw.Draw(g)
    cx, cy = 214 * S, 14 * S
    for r in range(40 * S, 0, -2 * S):                        # glare
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 250, 210, int(70 * (1 - r / (40 * S)) ** 2)))
    d.ellipse([cx - 9 * S, cy - 9 * S, cx + 9 * S, cy + 9 * S], fill=(255, 252, 230, 255))
    paste(img, g, 2 * S)
    b = layer()
    d = ImageDraw.Draw(b)
    for x, y, w in ((70, 60, 7), (84, 56, 5), (160, 66, 6)):  # seagulls
        X, Y, Wd = x * S, y * S, w * S
        d.arc([X - Wd, Y - Wd * 0.5, X, Y + Wd * 0.5], 200, 340, fill=(250, 250, 255, 255), width=S)
        d.arc([X, Y - Wd * 0.5, X + Wd, Y + Wd * 0.5], 200, 340, fill=(250, 250, 255, 255), width=S)
    paste(img, b)


def sailboat(img):
    b = layer()
    d = ImageDraw.Draw(b)
    x, y = 44 * S, (HORIZON + 4) * S
    d.polygon([(x - 6 * S, y), (x + 6 * S, y), (x + 4 * S, y + 2.5 * S), (x - 4 * S, y + 2.5 * S)], fill=(150, 70, 50, 255))
    d.polygon([(x, y - 14 * S), (x, y - S), (x + 7 * S, y - S)], fill=(255, 255, 250, 255))
    d.polygon([(x - S, y - 11 * S), (x - S, y - S), (x - 6 * S, y - S)], fill=(250, 120, 90, 255))
    d.line([(x, y - 15 * S), (x, y)], fill=(90, 60, 50, 255), width=max(1, S // 2))
    paste(img, b, 0.4 * S)


def islands(img):
    i = layer()
    d = ImageDraw.Draw(i)
    for cx, w, h, col in ((70, 90, 12, (110, 160, 150)), (176, 120, 16, (96, 150, 130)), (130, 60, 8, (126, 172, 162))):
        pts = [((cx - w / 2) * S, HORIZON * S)]
        for k in range(31):
            t = k / 30
            yy = HORIZON - h * math.sin(math.pi * t) ** 0.8 * (1 + 0.15 * math.sin(t * 17))
            pts.append(((cx - w / 2 + w * t) * S, yy * S))
        pts.append(((cx + w / 2) * S, HORIZON * S))
        d.polygon(pts, fill=col + (255,))
        d.line(pts[1:-1], fill=shade(col, 1.2) + (255,), width=S)
    paste(img, i, 0.8 * S)


def sea(img):
    s = layer()
    d = ImageDraw.Draw(s)
    vgrad(d, (0, HORIZON * S, W, SHORE * S), (40, 150, 200), (60, 210, 210))
    for _ in range(170):
        y = rng.uniform(HORIZON + 1, SHORE - 2)
        x = rng.uniform(0, 240)
        w = rng.uniform(3, 10) * (0.4 + (y - HORIZON) / (SHORE - HORIZON))
        d.rectangle([x * S, y * S, (x + w) * S, (y + 0.6) * S], fill=(210, 250, 255, 170))
    paste(img, s)
    w = layer()
    d = ImageDraw.Draw(w)
    for _ in range(26):                                       # wave crests
        y = rng.uniform(HORIZON + 6, SHORE - 3)
        x = rng.uniform(0, 230)
        ln = rng.uniform(5, 14) * (0.5 + (y - HORIZON) / (SHORE - HORIZON))
        d.arc([x * S, (y - 1.2) * S, (x + ln) * S, (y + 1.2) * S], 190, 350, fill=(255, 255, 255, 220), width=S)
    paste(img, w, 0.3 * S)
    f = layer()
    d = ImageDraw.Draw(f)
    pts = [(x * S, (SHORE - 1 + 1.2 * math.sin(x / 9)) * S) for x in range(0, 241, 2)]
    d.line(pts, fill=(255, 255, 255, 230), width=2 * S)
    paste(img, f, 0.6 * S)


def sand(img):
    s = layer()
    d = ImageDraw.Draw(s)
    vgrad(d, (0, (SHORE + 1) * S, W, H), (246, 226, 170), (230, 196, 130))
    for k in range(5):                                        # wind ripples
        y0 = SHORE + 4 + k * 4.5
        pts = [(x * S, (y0 + 0.8 * math.sin(x / 7 + k)) * S) for x in range(0, 241, 2)]
        d.line(pts, fill=(226, 190, 128, 255), width=S)
        d.line([(x, y - S) for x, y in pts], fill=(255, 240, 200, 255), width=max(1, S // 2))
    for _ in range(240):
        x, y = rng.uniform(0, W), rng.uniform((SHORE + 2) * S, H)
        d.rectangle([x, y, x + S, y + S], fill=rng.choice([(222, 186, 124), (255, 238, 196)]) + (255,))
    for x, y in ((40, 150), (58, 156), (176, 152), (196, 157), (92, 158)):   # shells
        d.ellipse([(x - 2.2) * S, (y - 1.6) * S, (x + 2.2) * S, (y + 1.6) * S], fill=(250, 200, 190, 255), outline=(170, 110, 100, 255))
        d.line([(x * S, (y - 1.4) * S), (x * S, (y + 1.4) * S)], fill=(200, 140, 130, 255), width=max(1, S // 2))
    for i in range(6):                                        # footprints across the sand
        x, y = 150 + i * 9, 158 - i * 1.6
        d.ellipse([(x - 1.6) * S, (y - 1) * S, (x + 1.6) * S, (y + 1) * S], fill=(214, 172, 112, 255))
    paste(img, s)


def leaf(d, x, y, ang, length, width, droop, col):
    """A palm frond: a drooping midrib, leaflets either side, lit on top."""
    upper, lower, rib = [], [], []
    for j in range(15):
        t = j / 14
        px = x + math.cos(ang) * length * t
        py = y + math.sin(ang) * length * t + droop * t * t
        dx = math.cos(ang)
        dy = math.sin(ang) + 2 * droop * t / max(1, length)
        m = math.hypot(dx, dy)
        nx, ny = -dy / m, dx / m
        w = width * math.sin(math.pi * min(1, t * 1.05)) ** 0.7
        rib.append((px, py))
        upper.append((px + nx * w, py + ny * w))
        lower.append((px - nx * w, py - ny * w))
    top, bot = (upper, lower) if sum(p[1] for p in upper) < sum(p[1] for p in lower) else (lower, upper)
    d.polygon(top + rib[::-1], fill=shade(col, 1.25) + (255,))
    d.polygon(bot + rib[::-1], fill=shade(col, 0.72) + (255,))
    for j in range(2, 14, 2):
        for edge in (top, bot):
            ex, ey = edge[j]
            rx, ry = rib[j]
            d.line([(ex, ey), (ex + (ex - rx) * 0.3, ey + (ey - ry) * 0.3 + S)], fill=shade(col, 0.6) + (255,), width=S)
    d.line(rib, fill=shade(col, 0.55) + (255,), width=2)


def palm(img, base_x, lean, height, flip):
    p = layer()
    d = ImageDraw.Draw(p)
    trunk = []
    for i in range(25):
        t = i / 24
        trunk.append((base_x + lean * t * t * S, (164 - height * t) * S))
    for i in range(len(trunk) - 1):
        (x1, y1), (x2, y2) = trunk[i], trunk[i + 1]
        w = (6.5 - 3 * i / 24) * S
        d.line([(x1, y1), (x2, y2)], fill=(150, 100, 60, 255), width=int(w))
        d.line([(x1 - w * 0.25 * flip, y1), (x2 - w * 0.25 * flip, y2)], fill=(196, 148, 96, 255), width=max(1, int(w * 0.35)))
        if i % 2 == 0:                                        # the rings and bark
            d.line([(x1 - w / 2, y1), (x1 + w / 2, y1 - S)], fill=(110, 70, 46, 255), width=S)
            d.line([(x1 - w / 2, y1 + S), (x1 - w / 4, y1 + 2 * S)], fill=(176, 124, 76, 255), width=max(1, S // 2))
    tx, ty = trunk[-1]
    for k in range(4):
        cx, cy = tx + (k - 1.5) * 3 * S, ty + 3 * S + (k % 2) * 2 * S
        d.ellipse([cx - 2.6 * S, cy - 2.6 * S, cx + 2.6 * S, cy + 2.6 * S], fill=(110, 76, 40, 255), outline=OUT)
        d.ellipse([cx - 1.6 * S, cy - 1.8 * S, cx, cy - 0.2 * S], fill=(170, 126, 70, 255))
    for a in (-2.9, -2.4, -1.9, -1.2, -0.7, -0.25, 0.25):
        aa = a if flip > 0 else math.pi - a
        leaf(d, tx, ty, aa, rng.uniform(30, 40) * S, rng.uniform(5, 7) * S, rng.uniform(10, 20) * S,
             lerp((40, 150, 50), (80, 190, 60), rng.random()))
    paste(img, p)


def pennants(img):
    """A string of checkered finish pennants between the palms."""
    p = layer()
    d = ImageDraw.Draw(p)
    pts = [(x, 34 + 8 * math.sin(math.pi * (x - 30) / 180)) for x in range(30, 211, 2)]
    d.line([(x * S, y * S) for x, y in pts], fill=(90, 70, 60, 255), width=S)
    for i in range(6, len(pts) - 4, 7):
        x, y = pts[i]
        X, Y = x * S, y * S
        d.polygon([(X - 5 * S, Y), (X + 5 * S, Y), (X, Y + 11 * S)], fill=(250, 250, 250, 255), outline=OUT)
        for cy in range(3):
            for cx in range(4):
                if (cx + cy) % 2:
                    bx, by = X - 4 * S + cx * 2.5 * S, Y + cy * 2.6 * S
                    shrink = cy * 1.4 * S
                    lo, hi = max(bx, X - 5 * S + shrink), min(bx + 2.5 * S, X + 5 * S - shrink)
                    if hi > lo:
                        d.rectangle([lo, by, hi, by + 2.6 * S], fill=(30, 30, 40, 255))
    paste(img, p)


def banner(img):
    """A shaded red ribbon with gold edges across the top, for the title (centred on the
    title text, y 8-24)."""
    b = layer()
    d = ImageDraw.Draw(b)
    y0, y1 = TITLE[0] * S, TITLE[1] * S
    x0, x1 = 34 * S, 206 * S
    for sx, dirn in ((x0, -1), (x1, 1)):
        tail = [(sx, y0 + 4 * S), (sx + dirn * 24 * S, y0 + 4 * S), (sx + dirn * 16 * S, (y0 + y1) / 2 + 2 * S),
                (sx + dirn * 24 * S, y1 + 5 * S), (sx, y1 + 5 * S)]
        d.polygon(tail, fill=(160, 30, 44, 255), outline=OUT)
    for y in range(int(y0), int(y1 + S)):
        t = (y - y0) / (y1 - y0 + S)
        k = 1.35 - 0.8 * t if t < 0.4 else 1.0 - 0.45 * (t - 0.4)
        d.line([(x0, y), (x1, y)], fill=shade((220, 44, 56), k) + (255,))
    d.rectangle([x0, y0, x1, y1 + S], outline=OUT)
    for yy, c in ((y0 + S, (255, 220, 110)), (y1, (210, 150, 50))):
        d.line([(x0 + S, yy), (x1 - S, yy)], fill=c + (255,), width=S)
    paste(img, b)


def plates(img, tint=(16, 30, 80, 85)):
    """Soft see-through strips behind the four standings rows."""
    p = layer()
    d = ImageDraw.Draw(p)
    for y in ROWS:
        d.rounded_rectangle([20 * S, (y - 4) * S, 220 * S, (y + 19) * S], 8 * S, fill=tint)
        d.rounded_rectangle([22 * S, (y - 4) * S, 218 * S, (y - 2.5) * S], 2 * S, fill=(255, 255, 255, 60))
    paste(img, p, 0.6 * S)


# ---------------------------------------------------------------- the trophy room
GOLD = (236, 184, 48)
SILVER = (196, 204, 222)
BRONZE = (204, 124, 64)


def wall(img):
    d = ImageDraw.Draw(img)
    vgrad(d, (0, 0, W, H), (120, 52, 34), (64, 26, 22))
    for x in range(0, 240, 20):                               # panels
        X = x * S
        d.rectangle([X + S, 6 * S, X + 19 * S, 160 * S], outline=(56, 22, 18, 255), width=S)
        d.line([(X + 2 * S, 7 * S), (X + 2 * S, 159 * S)], fill=(150, 76, 50, 255), width=max(1, S // 2))
        for _ in range(4):                                    # grain
            gx = X + rng.uniform(4, 17) * S
            d.line([(gx, 8 * S), (gx + rng.uniform(-2, 2) * S, 158 * S)], fill=(96, 40, 28, 255), width=max(1, S // 2))
    li = layer()
    dl = ImageDraw.Draw(li)
    for cx in (60, 180):                                      # spotlights
        dl.polygon([((cx - 8) * S, 0), ((cx + 8) * S, 0), ((cx + 44) * S, H), ((cx - 44) * S, H)], fill=(255, 220, 150, 46))
    dl.ellipse([40 * S, 20 * S, 200 * S, 170 * S], fill=(255, 200, 130, 40))
    paste(img, li, 6 * S)


def trophy(d, cx, base_y, h, metal, kind):
    """A cup trophy of our own: a rounded bowl with handles (or a star on a column), a
    stem and a stepped base, glossy: lit edge, specular streak, dark rim."""
    hi, lo = shade(metal, 1.45), shade(metal, 0.55)
    bw = h * 0.42
    by = base_y - h * 0.22                                    # the base
    d.rectangle([cx - bw * 0.7, by, cx + bw * 0.7, base_y], fill=(60, 34, 30, 255), outline=OUT)
    d.rectangle([cx - bw * 0.7, by, cx - bw * 0.5, base_y], fill=(110, 70, 56, 255))
    d.rectangle([cx - bw * 0.45, by - h * 0.06, cx + bw * 0.45, by], fill=metal + (255,), outline=OUT)
    d.rectangle([cx - bw * 0.12, by - h * 0.22, cx + bw * 0.12, by - h * 0.06], fill=metal + (255,), outline=OUT)
    top = by - h * 0.22
    if kind == "star":
        r = h * 0.3
        cy = top - r
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        d.polygon(pts, fill=metal + (255,), outline=OUT)
        d.polygon([pts[9], pts[0], pts[1], (cx, cy)], fill=hi + (255,))
        return
    bowl_top = top - h * 0.5
    for sx in (-1, 1):                                        # handles
        d.arc([cx + sx * bw * 0.35 - bw * 0.35, bowl_top + h * 0.06, cx + sx * bw * 0.35 + bw * 0.35, bowl_top + h * 0.34],
              90 if sx > 0 else -90 + 0, 270 if sx > 0 else 90, fill=lo + (255,), width=max(1, int(h * 0.05)))
    d.chord([cx - bw * 0.5, bowl_top - h * 0.25, cx + bw * 0.5, top + h * 0.02], 0, 180, fill=metal + (255,), outline=OUT)
    d.rectangle([cx - bw * 0.52, bowl_top - h * 0.02, cx + bw * 0.52, bowl_top + h * 0.03], fill=hi + (255,), outline=OUT)
    d.chord([cx - bw * 0.5, bowl_top - h * 0.25, cx + bw * 0.5, top + h * 0.02], 100, 170, fill=lo + (255,))
    d.line([(cx - bw * 0.3, bowl_top + h * 0.08), (cx - bw * 0.22, bowl_top + h * 0.3)], fill=(255, 255, 240, 255),
           width=max(1, int(h * 0.05)))                       # the specular streak


def shelves(img):
    s = layer()
    d = ImageDraw.Draw(s)
    metals = [GOLD, SILVER, BRONZE]
    for row, (y, h) in enumerate(((58, 22), (100, 24), (142, 26))):
        d.rectangle([0, y * S, W, (y + 4) * S], fill=(150, 84, 52, 255), outline=OUT)
        d.rectangle([0, y * S, W, (y + 1) * S], fill=(200, 128, 84, 255))
        d.rectangle([0, (y + 4) * S, W, (y + 7) * S], fill=(40, 16, 14, 120))
        x = 8 + row * 6
        while x < 236:
            kind = "star" if rng.random() < 0.25 else "cup"
            hh = h * rng.uniform(0.75, 1.0)
            trophy(d, x * S, y * S, hh * S, rng.choice(metals), kind)
            x += rng.uniform(17, 24)
    paste(img, s)
    # a soft glow on the shelves
    g = layer()
    ImageDraw.Draw(g).ellipse([20 * S, 30 * S, 220 * S, 160 * S], fill=(255, 210, 140, 30))
    paste(img, g, 8 * S)


def curtains(img):
    c = layer()
    d = ImageDraw.Draw(c)
    for side in (-1, 1):                                      # side drapes
        x0 = 0 if side < 0 else W
        for k in range(6):
            xx = x0 - side * k * 4 * S
            col = lerp((170, 20, 36), (120, 10, 26), k % 2)
            d.rectangle([min(xx, xx - side * 4 * S), 0, max(xx, xx - side * 4 * S), (60 - k * 6) * S], fill=col + (255,))
    for k in range(12):                                       # the swag across the top
        x = k * 20 * S
        d.chord([x - 4 * S, -12 * S, x + 24 * S, 14 * S], 0, 180, fill=(190, 26, 44, 255), outline=OUT)
        d.chord([x, -10 * S, x + 20 * S, 9 * S], 20, 160, fill=(222, 70, 80, 255))
    for x in range(0, 241, 20):                               # gold tassels
        d.line([(x * S, 10 * S), (x * S, 17 * S)], fill=(230, 180, 60, 255), width=S)
        d.ellipse([(x - 2) * S, 16 * S, (x + 2) * S, 21 * S], fill=(240, 196, 70, 255), outline=OUT)
    paste(img, c)


def plaque(img):
    """A gold plaque for the title."""
    p = layer()
    d = ImageDraw.Draw(p)
    x0, y0, x1, y1 = 36 * S, 3 * S, 204 * S, 29 * S
    d.rounded_rectangle([x0 + 2 * S, y0 + 3 * S, x1 + 2 * S, y1 + 3 * S], 5 * S, fill=(30, 10, 10, 140))
    for y in range(int(y0), int(y1)):
        t = (y - y0) / (y1 - y0)
        k = 1.4 - 0.9 * t if t < 0.35 else 0.95 - 0.35 * (t - 0.35)
        d.line([(x0 + 3 * S, y), (x1 - 3 * S, y)], fill=shade((210, 150, 40), k) + (255,))
    d.rounded_rectangle([x0, y0, x1, y1], 5 * S, outline=OUT, width=S)
    d.rounded_rectangle([x0 + 3 * S, y0 + 3 * S, x1 - 3 * S, y1 - 3 * S], 3 * S, outline=(120, 70, 20, 255), width=S)
    for x in (x0 + 7 * S, x1 - 7 * S):                        # screws
        d.ellipse([x - 1.6 * S, (y0 + y1) / 2 - 1.6 * S, x + 1.6 * S, (y0 + y1) / 2 + 1.6 * S], fill=(250, 220, 140, 255), outline=OUT)
    paste(img, p)


VP = (120, 74)                  # the room's vanishing point
BACK = (72, 38, 168, 104)       # the back wall (x0, y0, x1, y1)


def room(img):
    """The room in one-point perspective: ceiling, side walls, back wall, marble floor."""
    d = ImageDraw.Draw(img)
    bx0, by0, bx1, by1 = (v * S for v in BACK)
    # ceiling: dark wood, lighter towards the back
    vgrad(d, (0, 0, W, by0), (56, 26, 22), (120, 66, 44))
    d.polygon([(0, by0), (bx0, by0), (0, 0)], fill=(70, 34, 26, 255))
    # side walls: warm panelling, darker near the viewer
    for side in (-1, 1):
        xa, xb = (0, bx0) if side < 0 else (W, bx1)
        for k in range(60):
            t = k / 60
            x = xa + (xb - xa) * t
            yt = 0 + (by0 - 0) * t
            yb = H + (by1 - H) * t
            col = lerp((70, 30, 24), (150, 80, 50), t)
            d.line([(x, yt), (x, yb)], fill=col + (255,), width=int(abs(xb - xa) / 60) + 2)
    # back wall
    vgrad(d, (bx0, by0, bx1, by1), (170, 96, 60), (120, 62, 40))
    for k in range(1, 8):                                     # its panels
        x = bx0 + (bx1 - bx0) * k / 8
        d.line([(x, by0 + 4 * S), (x, by1 - 2 * S)], fill=(100, 52, 34, 255), width=max(1, S // 2))
    # the floor: a marble checkerboard in perspective, shinier at the back
    fl = np.zeros((H, W, 4), np.uint8)
    vy = VP[1] * S
    for y in range(int(by1), H):
        z = 1.0 / ((y - vy) / (H - vy))                       # depth: 1 at the front edge
        for x in range(0, W, 2):
            xw = (x - VP[0] * S) * z / (S * 22)
            zw = z * 3.2
            chk = (int(math.floor(xw)) + int(math.floor(zw))) & 1
            base = (236, 226, 208) if chk else (120, 34, 40)
            shine = max(0.0, 1 - abs(x - VP[0] * S) / (W * 0.45)) * (1 / z) * 0.35
            c = lerp(base, (255, 250, 236), min(1, shine))
            fl[y, x:x + 2, :3] = lerp(c, (60, 30, 30), min(0.45, (z - 1) * 0.08))
            fl[y, x:x + 2, 3] = 255
    paste(img, Image.fromarray(fl, "RGBA"))
    d = ImageDraw.Draw(img)
    for side in (-1, 1):                                      # skirting along the walls
        xa, xb = (0, bx0) if side < 0 else (W, bx1)
        d.line([(xa, H), (xb, by1)], fill=(60, 26, 20, 255), width=2 * S)


def alcove(img):
    """An arched alcove in the back wall: red velvet, a pedestal, the champion's cup."""
    a = layer()
    d = ImageDraw.Draw(a)
    cx = VP[0] * S
    x0, x1, y0, y1 = cx - 22 * S, cx + 22 * S, (BACK[1] + 4) * S, BACK[3] * S
    d.rectangle([x0, y0 + 20 * S, x1, y1], fill=(110, 14, 30, 255))
    d.pieslice([x0, y0, x1, y0 + 44 * S], 180, 360, fill=(110, 14, 30, 255))
    for k in range(7):                                        # velvet folds
        x = x0 + (k + 0.5) * (x1 - x0) / 7
        d.line([(x, y0 + 12 * S), (x, y1)], fill=(150, 30, 46, 255), width=S)
    d.arc([x0, y0, x1, y0 + 44 * S], 180, 360, fill=(230, 180, 70, 255), width=2 * S)
    d.line([(x0, y0 + 22 * S), (x0, y1)], fill=(230, 180, 70, 255), width=2 * S)
    d.line([(x1, y0 + 22 * S), (x1, y1)], fill=(230, 180, 70, 255), width=2 * S)
    # pedestal
    d.rectangle([cx - 10 * S, y1 - 14 * S, cx + 10 * S, y1], fill=(232, 228, 220, 255), outline=OUT)
    d.rectangle([cx - 12 * S, y1 - 16 * S, cx + 12 * S, y1 - 13 * S], fill=(250, 248, 240, 255), outline=OUT)
    d.rectangle([cx + 5 * S, y1 - 13 * S, cx + 10 * S, y1], fill=(190, 186, 180, 255))
    trophy(d, cx, y1 - 16 * S, 34 * S, GOLD, "cup")
    paste(img, a)
    li = layer()
    dl = ImageDraw.Draw(li)
    dl.polygon([(cx - 6 * S, 0), (cx + 6 * S, 0), (cx + 30 * S, y1), (cx - 30 * S, y1)], fill=(255, 236, 180, 50))
    paste(img, li, 3 * S)


def cabinets(img):
    """Glass display cabinets along both side walls, trophies shrinking with distance."""
    c = layer()
    d = ImageDraw.Draw(c)
    bx0, by0, bx1, by1 = BACK
    metals = [GOLD, SILVER, BRONZE]
    for side in (-1, 1):
        x_near, x_far = (2, bx0 - 4) if side < 0 else (238, bx1 + 4)
        def at(t, y_front, y_back):                           # a point on the wall at depth t
            x = x_near + (x_far - x_near) * t
            y = y_front + (y_back - y_front) * t
            return x * S, y * S
        # cabinet body
        d.polygon([at(0, 14, by0 + 6), at(1, by0 + 6, by0 + 6)[0:1] + (at(1, 14, by0 + 6)[1],),
                   at(1, 150, by1 - 4), at(0, 150, by1 - 4)], fill=(40, 20, 22, 255))
        # shelves and trophies, back to front so the near ones overlap
        for ys_front, ys_back in ((52, 58), (92, 80), (132, 100)):
            p0, p1 = at(0, ys_front, ys_back), at(1, ys_front, ys_back)
            d.line([p0, p1], fill=(220, 190, 140, 255), width=max(1, int(1.5 * S)))
            for k in range(6, 0, -1):
                t = (k - 0.5) / 6
                x, y = at(t, ys_front, ys_back)
                scale = 1 - 0.6 * t
                trophy(d, x, y, 22 * S * scale, metals[(k + int(ys_front)) % 3], "star" if k % 3 == 0 else "cup")
        # glass: a pane tint and glints
        pane = layer()
        dp = ImageDraw.Draw(pane)
        dp.polygon([at(0, 14, by0 + 6), at(1, by0 + 6, by0 + 6), at(1, 150, by1 - 4), at(0, 150, by1 - 4)],
                   fill=(170, 210, 240, 34))
        for k in range(3):
            t = 0.15 + k * 0.28
            xa, ya = at(t, 20, by0 + 8)
            xb, yb = at(t + 0.12, 140, by1 - 6)
            dp.line([(xa, ya), (xb, yb)], fill=(255, 255, 255, 90), width=2 * S)
        c.alpha_composite(pane)
        # the cabinet's frame
        d = ImageDraw.Draw(c)
        d.line([at(0, 14, by0 + 6), at(1, by0 + 6, by0 + 6)], fill=(200, 150, 80, 255), width=S)
        d.line([at(0, 150, by1 - 4), at(1, by1 - 4, by1 - 4)], fill=(200, 150, 80, 255), width=S)
    paste(img, c)


def ceiling_lights(img):
    l = layer()
    d = ImageDraw.Draw(l)
    for x, y, r in ((60, 10, 7), (120, 18, 6), (180, 10, 7)):
        d.ellipse([(x - r) * S, (y - r * 0.4) * S, (x + r) * S, (y + r * 0.4) * S], fill=(255, 250, 220, 255))
        d.polygon([((x - r) * S, y * S), ((x + r) * S, y * S), ((x + r * 4) * S, 160 * S), ((x - r * 4) * S, 160 * S)],
                  fill=(255, 230, 170, 28))
    paste(img, l, 2 * S)


def side_curtains(img):
    c = layer()
    d = ImageDraw.Draw(c)
    for side in (-1, 1):
        x0 = 0 if side < 0 else W
        for k in range(5):
            xx = x0 - side * k * 3.5 * S
            col = lerp((180, 22, 40), (120, 10, 26), k % 2)
            d.rectangle([min(xx, xx - side * 3.5 * S), 0, max(xx, xx - side * 3.5 * S), (70 - k * 9) * S], fill=col + (255,))
        d.ellipse([(x0 - side * 16 * S) - 3 * S, 64 * S, (x0 - side * 16 * S) + 3 * S, 70 * S], fill=(240, 196, 70, 255), outline=OUT)
    paste(img, c)


def paint_final():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    room(img)
    alcove(img)
    cabinets(img)
    ceiling_lights(img)
    side_curtains(img)
    plates(img, (20, 8, 16, 95))
    plaque(img)
    return finish(img)


# ---------------------------------------------------------------- best times: a jungle clearing
BEST_ROWS = (40, 61, 82, 103, 124)  # the chart's rows (updates/code/best.s), text 16 high
BEST_X = (8, 170)               # the rows' extent; the plane sits to the right
TEAL = (52, 168, 184)
CREAM = (246, 232, 196)
ORANGE = (240, 128, 40)
SUNNY = (250, 208, 64)


def j_backdrop(img):
    """Green-gold light filtering down through the canopy."""
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c = lerp((176, 222, 150), (70, 140, 86), min(1, t * 1.6)) if t < 0.62 else lerp((70, 140, 86), (34, 84, 50), (t - 0.62) / 0.38)
        d.line([(0, y), (W, y)], fill=c + (255,))
    g = layer()
    gd = ImageDraw.Draw(g)
    for r, a in ((110, 60), (80, 70), (50, 90)):
        gd.ellipse([(120 - r) * S, (8 - r * 0.6) * S, (120 + r) * S, (8 + r * 0.6) * S], fill=(255, 244, 180, a))
    paste(img, g, 10 * S)


def j_canopy_layer(img, base, col, haze, seed, size):
    r = random.Random(seed)
    p = layer()
    d = ImageDraw.Draw(p)
    x = -10
    while x < 250:
        w = r.uniform(size * 0.7, size * 1.3)
        top = base - r.uniform(0, size * 0.8)
        d.ellipse([(x - w) * S, top * S, (x + w) * S, (top + w * 1.4) * S], fill=col + (255,))
        d.ellipse([(x - w * 0.7) * S, (top + w * 0.1) * S, (x + w * 0.4) * S, (top + w * 0.6) * S],
                  fill=shade(col, 1.18) + (255,))
        x += w * 1.1
    d.rectangle([0, (base + size * 0.5) * S, W, H], fill=col + (255,))
    paste(img, p, haze * S)


def j_ruin(img):
    """A stepped stone ruin far off in the haze, half swallowed by the trees."""
    p = layer()
    d = ImageDraw.Draw(p)
    stone, lit = (128, 150, 132), (170, 190, 166)
    for k in range(5):
        w = 34 - k * 6
        y0 = 92 - k * 8
        d.rectangle([(120 - w) * S, y0 * S, (120 + w) * S, (y0 + 8) * S], fill=stone + (255,))
        d.rectangle([(120 - w) * S, y0 * S, (120 + w) * S, (y0 + 1.5) * S], fill=lit + (255,))
        for bx in range(int(120 - w) + 4, int(120 + w), 7):
            d.line([(bx * S, (y0 + 2) * S), (bx * S, (y0 + 8) * S)], fill=(100, 120, 104, 255), width=S // 2)
    d.rectangle([114 * S, 52 * S, 126 * S, 60 * S], fill=(60, 74, 62, 255))       # the shrine's door
    d.rectangle([116 * S, 92 * S, 124 * S, 100 * S], fill=(150, 168, 148, 255))   # the stair
    paste(img, p, 1.2 * S)
    m = layer()                                                                   # haze over it
    ImageDraw.Draw(m).rectangle([0, 40 * S, W, 104 * S], fill=(150, 200, 150, 36))
    paste(img, m, 6 * S)


def j_trunk(img, x, w, lean, col):
    p = layer()
    d = ImageDraw.Draw(p)
    pts_l, pts_r = [], []
    for i in range(21):
        t = i / 20
        cx = x + lean * t
        ww = w * (1.0 - 0.35 * t)
        y = (160 - 170 * t)
        pts_l.append(((cx - ww / 2) * S, y * S))
        pts_r.append(((cx + ww / 2) * S, y * S))
    d.polygon(pts_l + pts_r[::-1], fill=col + (255,))
    d.polygon(pts_l + [((a + b) / 2, y) for (a, y), (b, _) in zip([q[0:1] + (q[1],) for q in pts_l], pts_r)][::-1],
              fill=shade(col, 1.25) + (255,))
    for i in range(3, 20, 3):                                       # bark
        (lx, y), (rx, _) = pts_l[i], pts_r[i]
        d.line([(lx + S, y), (rx - S, y + 2 * S)], fill=shade(col, 0.7) + (255,), width=S)
    for sx in (-1, 1):                                              # buttress roots
        bx = (x + sx * w * 0.5) * S
        d.polygon([(bx, 132 * S), (bx + sx * w * 0.9 * S, 160 * S), (bx - sx * w * 0.2 * S, 160 * S)],
                  fill=shade(col, 0.9) + (255,))
    paste(img, p)


def j_bushes(img):
    """Leafy clumps along the edge of the clearing."""
    p = layer()
    d = ImageDraw.Draw(p)
    r = random.Random(21)
    for bx in range(-6, 250, 22):
        by = r.uniform(122, 136)
        for _ in range(6):
            a = r.uniform(-2.9, -0.25)
            leaf(d, bx * S, by * S, a, r.uniform(12, 20) * S, r.uniform(3.5, 5.5) * S, r.uniform(2, 6) * S,
                 lerp((40, 116, 52), (96, 176, 70), r.random()))
    paste(img, p)


def j_rays(img):
    p = layer()
    d = ImageDraw.Draw(p)
    for x, w, a in ((70, 14, 46), (104, 9, 40), (150, 16, 44), (196, 10, 36)):
        d.polygon([(x * S, 0), ((x + w) * S, 0), ((x + w + 34) * S, 150 * S), ((x + 22) * S, 150 * S)],
                  fill=(255, 246, 190, a))
    paste(img, p, 4 * S)


def j_vines(img, seed=7):
    r = random.Random(seed)
    p = layer()
    d = ImageDraw.Draw(p)
    for x in (6, 20, 44, 200, 216, 232, 92, 150):
        length = r.uniform(30, 80)
        sway = r.uniform(-6, 6)
        pts = [((x + sway * math.sin(t * 2.2)) * S, length * t * S) for t in [k / 30 for k in range(31)]]
        d.line(pts, fill=(54, 96, 40, 255), width=int(1.6 * S))
        d.line([(a + S * 0.5, b) for a, b in pts], fill=(110, 160, 70, 255), width=max(1, S // 2))
        for k in range(4, 31, 5):
            vx, vy = pts[k]
            side = 1 if k % 2 else -1
            d.ellipse([vx + side * S - 2.5 * S, vy - 1.5 * S, vx + side * S + 2.5 * S, vy + 1.5 * S],
                      fill=(70, 150, 60, 255), outline=(34, 80, 36, 255))
    paste(img, p)


def j_ground(img):
    """A grassy clearing; a patch of bare earth where the plane stands."""
    p = layer()
    d = ImageDraw.Draw(p)
    vgrad(d, (0, 134 * S, W, H), (88, 150, 64), (52, 110, 44))
    d.ellipse([168 * S, 140 * S, 250 * S, 166 * S], fill=(150, 120, 76, 255))
    d.ellipse([172 * S, 141 * S, 244 * S, 150 * S], fill=(176, 146, 96, 255))
    r = random.Random(5)
    for _ in range(260):
        x, y = r.uniform(0, 240), r.uniform(136, 160)
        if 172 < x < 244 and 142 < y < 160:
            continue
        h = r.uniform(2, 5)
        d.line([(x * S, y * S), ((x + r.uniform(-1, 1)) * S, (y - h) * S)],
               fill=lerp((60, 120, 44), (150, 210, 90), r.random()) + (255,), width=max(1, S // 2))
    paste(img, p)


def j_foliage(img):
    """Big leaves and ferns framing the clearing; a few flowers."""
    p = layer()
    d = ImageDraw.Draw(p)
    r = random.Random(11)
    for x, y, angs in ((-4, 150, (-1.0, -0.6, -0.2, -1.4)), (-6, 26, (0.1, 0.5, 0.9)),
                       (246, 20, (2.9, 2.5, 2.2)), (100, 164, (-1.9, -1.5, -1.2))):
        for a in angs:
            leaf(d, x * S, y * S, a, r.uniform(26, 40) * S, r.uniform(7, 10) * S, r.uniform(4, 10) * S,
                 lerp((30, 110, 46), (70, 160, 60), r.random()))
    for fx, fy, c in ((18, 132, (232, 60, 60)), (30, 138, (250, 140, 40)), (112, 150, (236, 70, 120))):
        for k in range(5):
            a = k * 2 * math.pi / 5
            px, py = (fx + 2.6 * math.cos(a)) * S, (fy + 2.6 * math.sin(a)) * S
            d.ellipse([px - 2 * S, py - 2 * S, px + 2 * S, py + 2 * S], fill=c + (255,), outline=shade(c, 0.6) + (255,))
        d.ellipse([(fx - 1.2) * S, (fy - 1.2) * S, (fx + 1.2) * S, (fy + 1.2) * S], fill=(255, 230, 90, 255))
    paste(img, p)


def plane(img):
    """Our plane, parked three-quarters toward us (updates/art/cup_results/plane3d.py)."""
    sh = layer()
    ImageDraw.Draw(sh).ellipse(P2([(164, 143), (236, 157)]), fill=(40, 60, 30, 120))
    paste(img, sh, S)
    pic, (ax, ay) = plane3d.render(6.4 * S)
    p = layer()
    p.alpha_composite(pic, (int(191 * S - ax), int(151 * S - ay)))
    paste(img, p)


def j_waterfall(img, x=150):
    """A thin waterfall down a rock face beyond the trees, with mist and a pool."""
    p = layer()
    d = ImageDraw.Draw(p)
    rock = [(x - 10, 48), (x - 4, 44), (x + 6, 45), (x + 13, 49), (x + 16, 62), (x + 14, 76), (x + 19, 92),
            (x + 18, 108), (x - 18, 112), (x - 20, 94), (x - 15, 80), (x - 17, 64)]
    d.polygon(P2(rock), fill=(112, 128, 110, 255), outline=(80, 94, 78, 255))
    r = random.Random(13)
    for _ in range(30):                                                   # moss and ferns on the rock
        mx, my = x + r.uniform(-18, 18), r.uniform(48, 108)
        if abs(mx - x) < 5:
            continue
        rr = r.uniform(1.2, 3)
        d.ellipse(P2([(mx - rr, my - rr * 0.7), (mx + rr, my + rr * 0.7)]),
                  fill=lerp((60, 120, 56), (110, 170, 80), r.random()) + (255,))
    for k in range(6):
        y = 54 + k * 9
        d.line(P2([(x - 13 + k * 0.4, y), (x + 14 - k * 0.2, y - 2)]), fill=(94, 108, 92, 255), width=S)
    r = random.Random(9)
    for k in range(22):
        xx = x + r.uniform(-4, 4)
        d.line(P2([(xx, 47), (xx + r.uniform(-1, 1), 106)]), fill=lerp((190, 226, 244), (255, 255, 255), r.random()) + (255,),
               width=max(1, int(r.uniform(0.8, 1.8) * S)))
    d.ellipse(P2([(x - 16, 102), (x + 16, 112)]), fill=(130, 196, 214, 255))
    paste(img, p, 0.3 * S)
    m = layer()
    ImageDraw.Draw(m).ellipse(P2([(x - 18, 96), (x + 18, 114)]), fill=(255, 255, 255, 130))
    paste(img, m, 3 * S)


def P2(pts):
    return [(x * S, y * S) for x, y in pts]


def j_parrot(img, x, y):
    """A bright parrot on a branch."""
    p = layer()
    d = ImageDraw.Draw(p)
    d.line(P2([(x - 12, y + 7), (x + 10, y + 5)]), fill=(96, 70, 44, 255), width=2 * S)
    d.ellipse(P2([(x - 3, y - 6), (x + 4, y + 6)]), fill=(220, 40, 40, 255), outline=OUT)
    d.polygon(P2([(x - 2, y + 2), (x + 3, y + 3), (x + 1, y + 13), (x - 1, y + 13)]), fill=(40, 90, 220, 255), outline=OUT)
    d.ellipse(P2([(x - 3, y - 1), (x + 2, y + 5)]), fill=(250, 210, 50, 255))
    d.ellipse(P2([(x - 1, y - 10), (x + 5, y - 3)]), fill=(230, 50, 44, 255), outline=OUT)
    d.ellipse(P2([(x + 1.5, y - 8.5), (x + 3.5, y - 6.5)]), fill=(255, 255, 255, 255))
    d.point(P2([(x + 2.6, y - 7.4)]), fill=(0, 0, 0, 255))
    d.polygon(P2([(x + 4.5, y - 7), (x + 7.5, y - 5.5), (x + 4.5, y - 4)]), fill=(240, 230, 200, 255), outline=OUT)
    paste(img, p)


def j_props(img):
    """By the plane: a supply crate and a fuel drum. Mossy rocks and mushrooms in front."""
    p = layer()
    d = ImageDraw.Draw(p)
    x0, y0 = 128, 140                                                    # crate
    d.rectangle(P2([(x0, y0), (x0 + 16, y0 + 14)]), fill=(196, 150, 90, 255), outline=OUT)
    d.polygon(P2([(x0, y0), (x0 + 4, y0 - 3), (x0 + 20, y0 - 3), (x0 + 16, y0)]), fill=(222, 180, 116, 255), outline=OUT)
    d.polygon(P2([(x0 + 16, y0), (x0 + 20, y0 - 3), (x0 + 20, y0 + 11), (x0 + 16, y0 + 14)]), fill=(150, 108, 60, 255), outline=OUT)
    for k in (4, 9):
        d.line(P2([(x0 + 1, y0 + k), (x0 + 15, y0 + k)]), fill=(130, 92, 52, 255), width=S // 2)
    d.line(P2([(x0 + 1, y0 + 1), (x0 + 15, y0 + 13)]), fill=(150, 108, 60, 255), width=S)
    dx, dy = 151, 137                                                    # drum
    d.rectangle(P2([(dx, dy), (dx + 9, dy + 16)]), fill=(200, 60, 44, 255), outline=OUT)
    d.rectangle(P2([(dx + 1, dy), (dx + 3, dy + 16)]), fill=(240, 120, 96, 255))
    for k in (4, 11):
        d.line(P2([(dx, dy + k), (dx + 9, dy + k)]), fill=(120, 30, 24, 255), width=S // 2)
    d.ellipse(P2([(dx, dy - 1.5), (dx + 9, dy + 1.5)]), fill=(220, 90, 70, 255), outline=OUT)
    for rx, ry, rw in ((40, 150, 16), (62, 154, 10), (120, 152, 12)):     # rocks
        d.ellipse(P2([(rx - rw / 2, ry - rw / 3), (rx + rw / 2, ry + rw / 3)]), fill=(120, 124, 110, 255), outline=OUT)
        d.ellipse(P2([(rx - rw / 2.5, ry - rw / 3), (rx + rw / 4, ry - rw / 8)]), fill=(90, 150, 70, 255))
    for mx, my in ((52, 146), (56, 148), (130, 148)):                     # mushrooms
        d.rectangle(P2([(mx - 0.6, my), (mx + 0.6, my + 3)]), fill=(240, 230, 210, 255))
        d.pieslice(P2([(mx - 2.5, my - 2), (mx + 2.5, my + 2)]), 180, 360, fill=(220, 70, 50, 255), outline=OUT)
    paste(img, p)


def j_butterflies(img):
    p = layer()
    d = ImageDraw.Draw(p)
    for x, y, c in ((112, 44, (250, 200, 60)), (158, 66, (120, 200, 250)), (90, 134, (250, 140, 200))):
        d.ellipse(P2([(x - 3, y - 2.5), (x, y + 0.5)]), fill=c + (255,), outline=OUT)
        d.ellipse(P2([(x, y - 2.5), (x + 3, y + 0.5)]), fill=c + (255,), outline=OUT)
        d.line(P2([(x, y - 2), (x, y + 2)]), fill=(40, 30, 30, 255), width=max(1, S // 2))
    paste(img, p)


def j_dapple(img):
    """Sun flecks through the leaves."""
    p = layer()
    d = ImageDraw.Draw(p)
    r = random.Random(17)
    for _ in range(70):
        x, y = r.uniform(0, 240), r.uniform(40, 160)
        w = r.uniform(1.5, 4)
        d.ellipse(P2([(x - w, y - w * 0.5), (x + w, y + w * 0.5)]), fill=(255, 250, 200, int(r.uniform(30, 70))))
    paste(img, p, 0.6 * S)


def stone_tablet(img):
    """A carved stone tablet across the top for BEST TIMES and the course name, mossy."""
    p = layer()
    d = ImageDraw.Draw(p)
    x0, y0, x1, y1 = 54 * S, 1 * S, 186 * S, 35 * S
    d.rounded_rectangle([x0, y0, x1, y1], 3 * S, fill=(150, 146, 120, 255), outline=OUT)
    vgrad(d, (x0 + S, y0 + S, x1 - S, y1 - S), (178, 172, 142), (120, 116, 94))
    d.rounded_rectangle([x0 + 3 * S, y0 + 3 * S, x1 - 3 * S, y1 - 3 * S], 2 * S, outline=(92, 88, 70, 255), width=S)
    d.line([(x0 + 4 * S, y0 + 4 * S), (x1 - 4 * S, y0 + 4 * S)], fill=(206, 200, 168, 255), width=S // 2)
    r = random.Random(3)
    for _ in range(40):                                                   # moss
        mx = r.choice([r.uniform(54, 70), r.uniform(170, 186), r.uniform(54, 186)])
        my = r.choice([r.uniform(1, 6), r.uniform(28, 35)]) if 70 < mx < 170 else r.uniform(1, 35)
        rr = r.uniform(1, 2.6)
        d.ellipse([(mx - rr) * S, (my - rr) * S, (mx + rr) * S, (my + rr) * S],
                  fill=lerp((60, 120, 50), (120, 170, 70), r.random()) + (230,))
    for cx in (62, 178):                                                   # carved spirals at the ends
        pts = []
        for i in range(60):
            t = i / 59 * 3.2 * math.pi
            rr = 0.4 + 1.6 * t / math.pi
            pts.append(((cx + rr * math.cos(t)) * S, (18 + rr * math.sin(t)) * S))
        d.line(pts, fill=(84, 80, 62, 255), width=S)
        d.line([(x + S // 2, y + S // 2) for x, y in pts], fill=(196, 190, 158, 255), width=max(1, S // 2))
    for cx in range(76, 168, 8):                                           # a carved band of steps along the foot
        d.line([(cx * S, 31 * S), ((cx + 4) * S, 31 * S), ((cx + 4) * S, 29 * S), ((cx + 8) * S, 29 * S)],
               fill=(98, 94, 74, 255), width=max(1, S // 2))
    paste(img, p)
    sh = layer()
    ImageDraw.Draw(sh).rectangle([x0 + 2 * S, y1, x1 + 2 * S, y1 + 2 * S], fill=(0, 30, 0, 90))
    paste(img, sh, S)


def best_plates(img):
    p = layer()
    d = ImageDraw.Draw(p)
    for y in BEST_ROWS:
        d.rounded_rectangle([BEST_X[0] * S, (y - 2) * S, BEST_X[1] * S, (y + 17) * S], 6 * S, fill=(8, 34, 16, 56))
    paste(img, p, 0.6 * S)


def paint_best():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    j_backdrop(img)
    j_canopy_layer(img, 46, (120, 172, 140), 3, 1, 18)
    j_ruin(img)
    j_waterfall(img)
    j_canopy_layer(img, 98, (74, 138, 92), 1.5, 2, 13)
    for x, w, lean, c in ((30, 11, 3, (96, 82, 62)), (60, 7, -2, (84, 76, 60)), (178, 8, 2, (90, 80, 60)),
                          (222, 13, -4, (100, 84, 62))):
        j_trunk(img, x, w, lean, c)
    j_rays(img)
    j_canopy_layer(img, 118, (52, 118, 62), 0.6, 4, 12)
    j_bushes(img)
    j_ground(img)
    j_dapple(img)
    j_vines(img)
    j_parrot(img, 224, 66)
    j_props(img)
    plane(img)
    j_foliage(img)
    j_butterflies(img)
    best_plates(img)
    stone_tablet(img)
    return finish(img)


def finish(img):
    out = ImageEnhance.Color(img.convert("RGB")).enhance(1.1)
    small = out.resize((240, 160), Image.LANCZOS)
    a = (np.asarray(small) >> 3 << 3) | 4
    return Image.fromarray(a.astype(np.uint8), "RGB").quantize(colors=255, method=Image.Quantize.MEDIANCUT,
                                                               dither=Image.Dither.NONE)


def paint():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sky(img)
    sun_and_gulls(img)
    clouds(img)
    islands(img)
    sea(img)
    sailboat(img)
    sand(img)
    palm(img, 4 * S, 16, 116, 1)
    palm(img, 236 * S, -16, 112, -1)
    pennants(img)
    plates(img, (255, 255, 255, 70))
    banner(img)
    return finish(img)


def save(pic, where):
    os.makedirs(where, exist_ok=True)
    pal = pic.getpalette()[:255 * 3]
    idx = np.asarray(pic).astype(np.uint8) + 1
    full = [0, 0, 0] + pal
    out = Image.fromarray(idx, "P")
    out.putpalette(full + [0] * (768 - len(full)))
    out.save(os.path.join(where, "picture.png"))
    out.convert("RGB").resize((720, 480), Image.NEAREST).save(os.path.join(where, "preview.png"))
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
    open(os.path.join(where, "tiles.bin"), "wb").write(b"".join(tiles))
    open(os.path.join(where, "map.bin"), "wb").write(b"".join(v.to_bytes(2, "little") for v in smap))
    gba = bytearray(2)
    for i in range(255):
        r, g, b = (c >> 3 for c in pal[3 * i:3 * i + 3])
        gba += (r | g << 5 | b << 10).to_bytes(2, "little")
    open(os.path.join(where, "palette.bin"), "wb").write(gba)
    print(len(tiles), "tiles", len(tiles) * 64, "bytes")


if __name__ == "__main__":
    save(paint(), os.path.join(HERE, "race"))
    save(paint_final(), os.path.join(HERE, "final"))
    save(paint_best(), os.path.join(HERE, "best"))

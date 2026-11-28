#!/usr/bin/env python3
"""The cup's results backgrounds (240x160): race/ after each race (RESULTS), final/
after the cup (FINAL RESULTS).

Original art for this project, painted by this script (no source images, no
characters or trademarks). In the style of the game's menu backgrounds (bright
daylight, soft shaded clouds, smooth rendered shading, high colour): a sunny beach at
the end of a race. Blue sky and soft clouds, hazy green islands, a turquoise sea, sand,
two palms framing the scene, a string of checkered finish pennants, a shaded ribbon
banner across the top for the title, a stone podium with gold, silver and bronze
bands, and soft see-through strips where the four standings rows sit (the text and
racer heads are sprites drawn over it).

FINAL RESULTS is a trophy room instead: wood-panelled walls under spotlights, shelves of
gleaming trophies (generic cups of our own design: gold, silver, bronze), red velvet
curtains with gold tassels, a gold plaque for the title.

    python3 updates/art/cup_results/paint.py

writes, in race/ and final/ next to this script:
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
    for i in range(6):                                        # footprints to the podium
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


def podium(img):
    p = layer()
    d = ImageDraw.Draw(p)
    d.ellipse([(120 - 40) * S, 152 * S, (120 + 40) * S, 162 * S], fill=(180, 140, 90, 140))
    for x0, x1, h, band in ((-34, -12, 9, (200, 206, 222)), (-12, 12, 15, (250, 206, 60)), (12, 34, 6, (214, 140, 80))):
        X0, X1, Y0 = (120 + x0) * S, (120 + x1) * S, (156 - h) * S
        d.rectangle([X0, Y0, X1, 160 * S], fill=(232, 232, 236, 255), outline=OUT)
        d.rectangle([X0 + S, Y0 + S, X0 + 3 * S, 160 * S], fill=(255, 255, 255, 255))
        d.rectangle([X1 - 4 * S, Y0 + S, X1 - S, 160 * S], fill=(186, 190, 206, 255))
        d.rectangle([X0, Y0 + 2 * S, X1, Y0 + 4.5 * S], fill=band + (255,))
        d.rectangle([X0, Y0 + 2 * S, X1, Y0 + 3 * S], fill=shade(band, 1.3) + (255,))
    paste(img, p)


def banner(img):
    """A shaded red ribbon with gold edges across the top, for the title."""
    b = layer()
    d = ImageDraw.Draw(b)
    y0, y1 = TITLE[0] * S, TITLE[1] * S
    x0, x1 = 34 * S, 206 * S
    for sx, dirn in ((x0, -1), (x1, 1)):
        tail = [(sx, y0 + 6 * S), (sx + dirn * 24 * S, y0 + 6 * S), (sx + dirn * 16 * S, (y0 + y1) / 2 + 4 * S),
                (sx + dirn * 24 * S, y1 + 7 * S), (sx, y1 + 7 * S)]
        d.polygon(tail, fill=(160, 30, 44, 255), outline=OUT)
    for y in range(int(y0 + 2 * S), int(y1 + 3 * S)):
        t = (y - y0) / (y1 - y0 + 3 * S)
        k = 1.35 - 0.8 * t if t < 0.4 else 1.0 - 0.45 * (t - 0.4)
        d.line([(x0, y), (x1, y)], fill=shade((220, 44, 56), k) + (255,))
    d.rectangle([x0, y0 + 2 * S, x1, y1 + 3 * S], outline=OUT)
    for yy, c in ((y0 + 3 * S, (255, 220, 110)), (y1 + 2 * S, (210, 150, 50))):
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


def paint_final():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    wall(img)
    shelves(img)
    curtains(img)
    plates(img)
    plaque(img)
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
    podium(img)
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

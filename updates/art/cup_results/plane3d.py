"""Our plane for the BEST TIMES background (updates patch): a small 3D model, original design
(a stubby teal monoplane, red cowling, yellow wings, an orange stripe, a two-blade prop),
rendered three-quarters from the front: flat-shaded faces, depth-sorted, outlined.
Used by paint.py; render(scale) -> (RGBA image, the point under the wheels).
"""
import math
import numpy as np
from PIL import Image, ImageDraw

TEAL = (52, 168, 184); CREAM = (246, 232, 196); ORANGE = (240, 128, 40); SUNNY = (250, 208, 64)
RED = (214, 56, 48); DARK = (60, 40, 40); WHITE = (238, 238, 242); WOOD = (170, 120, 70); TYRE = (44, 44, 52)
GLASS = (170, 224, 248)


def box(x0, x1, y0, y1, z0, z1, col):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]
    return [([v[i] for i in q], col) for q in f]


def wing(xr0, xr1, xt0, xt1, y, zt, th, col):
    """A tapered wing from the root (z=0) to the tip (z=zt): chord xr0..xr1 at the root, xt0..xt1 at the tip."""
    top = [(xr0, y + th, 0), (xr1, y + th, 0), (xt1, y + th * 0.6, zt), (xt0, y + th * 0.6, zt)]
    bot = [(x, yy - th - (0 if i < 2 else -th * 0.8), z) for i, (x, yy, z) in enumerate(top)]
    bot = [(top[0][0], y, 0), (top[1][0], y, 0), (top[2][0], y + th * 0.1, zt), (top[3][0], y + th * 0.1, zt)]
    faces = [(top, col), (bot[::-1], col)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(([top[i], bot[i], bot[j], top[j]][::-1], col))
    return faces


def fuselage():
    prof = [(-6.0, 0.35, 0.55), (-4.5, 0.6, 0.75), (-2.5, 0.95, 1.05), (-0.5, 1.35, 1.45), (1.2, 1.55, 1.6),
            (2.6, 1.5, 1.55), (3.2, 1.45, 1.5)]                         # x, half-width, half-height
    n = 20
    rings = []
    for x, w, h in prof:
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            ring.append((x, h * math.sin(a) + 0.15, w * math.cos(a)))
        rings.append(ring)
    faces = []
    for i in range(len(rings) - 1):
        for k in range(n):
            q = [rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % n], rings[i][(k + 1) % n]]
            ym = sum(p[1] for p in q) / 4
            col = TEAL
            if ym < -0.55:
                col = CREAM
            elif -0.1 < ym < 0.4 and 1 <= i <= 5:
                col = ORANGE
            faces.append((q, col))
    faces.append((rings[0][::-1], TEAL))                                # tail cap
    # cowling: a red ring from x 3.2 to 4.0, open front with the engine
    cow = []
    for x, w, h in ((3.2, 1.5, 1.55), (3.9, 1.45, 1.45), (4.1, 1.2, 1.2)):
        cow.append([(x, h * math.sin(2 * math.pi * k / n) + 0.15, w * math.cos(2 * math.pi * k / n)) for k in range(n)])
    for i in range(2):
        for k in range(n):
            faces.append(([cow[i][k], cow[i + 1][k], cow[i + 1][(k + 1) % n], cow[i][(k + 1) % n]], RED))
    faces.append(([(4.05, p[1] * 0.98 + 0.003, p[2] * 0.98) for p in cow[2]][::-1], DARK))
    # spinner: a cone
    tip = (4.9, 0.15, 0)
    base = [(4.1, 0.45 * math.sin(2 * math.pi * k / 10) + 0.15, 0.45 * math.cos(2 * math.pi * k / 10)) for k in range(10)]
    for k in range(10):
        faces.append(([base[k], tip, base[(k + 1) % 10]], WHITE))
    return faces


def plane_faces():
    f = fuselage()
    f += wing(-0.2, 2.4, 0.6, 2.0, -1.05, 6.2, 0.22, SUNNY)              # right wing
    f += [([(x, y, -z) for x, y, z in q][::-1], c) for q, c in wing(-0.2, 2.4, 0.6, 2.0, -1.05, 6.2, 0.22, SUNNY)]
    f += wing(-6.0, -4.7, -5.8, -5.1, 0.1, 2.6, 0.1, SUNNY)              # tailplane
    f += [([(x, y, -z) for x, y, z in q][::-1], c) for q, c in wing(-6.0, -4.7, -5.8, -5.1, 0.1, 2.6, 0.1, SUNNY)]
    f += box(-5.9, -4.6, 0.5, 2.7, -0.1, 0.1, TEAL)                     # fin
    f += box(-6.15, -5.6, 0.5, 2.6, -0.11, 0.11, ORANGE)                # rudder
    # windscreen: a wedge leaning back, then the open cockpit behind it
    ws = [(0.7, 1.62, -0.6), (0.7, 1.62, 0.6), (0.1, 2.25, 0.5), (0.1, 2.25, -0.5)]
    f.append((ws, GLASS))
    f.append((ws[::-1], GLASS))
    f.append(([(0.1, 2.25, -0.5), (0.1, 2.25, 0.5), (0.1, 1.62, 0.6), (0.1, 1.62, -0.6)], GLASS))
    f += box(-1.6, 0.1, 1.62, 1.72, -0.55, 0.55, DARK)                  # the cockpit opening
    f += box(-1.9, -1.6, 1.62, 2.0, -0.45, 0.45, TEAL)                  # a low headrest
    for z in (-2.3, 2.3):                                               # struts and wheels
        f += box(1.3, 1.6, -2.4, -1.0, z - 0.1, z + 0.1, (90, 90, 100))
        n = 12
        for side in (-0.28, 0.28):
            disc = [(1.45 + 0.8 * math.cos(2 * math.pi * k / n), -2.6 + 0.8 * math.sin(2 * math.pi * k / n), z + side) for k in range(n)]
            f.append((disc if side > 0 else disc[::-1], TYRE))
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            p0 = (1.45 + 0.8 * math.cos(a0), -2.6 + 0.8 * math.sin(a0))
            p1 = (1.45 + 0.8 * math.cos(a1), -2.6 + 0.8 * math.sin(a1))
            f.append(([(p0[0], p0[1], z - 0.28), (p1[0], p1[1], z - 0.28), (p1[0], p1[1], z + 0.28), (p0[0], p0[1], z + 0.28)], TYRE))
        f += box(0.7, 2.2, -2.3, -1.9, z - 0.35, z + 0.35, SUNNY)       # spat over the wheel
    # propeller: two blades at a slant, just in front of the cowling
    for s in (1, -1):
        a = math.radians(62)
        dy, dz = math.sin(a) * s, math.cos(a) * s
        root, tipp = 0.4, 2.7
        w = 0.28
        nz, ny = -math.sin(a), math.cos(a)                              # across the blade
        q = [(4.35, 0.15 + dy * root + ny * w, dz * root + nz * w), (4.35, 0.15 + dy * tipp + ny * w * 0.6, dz * tipp + nz * w * 0.6),
             (4.35, 0.15 + dy * tipp - ny * w * 0.6, dz * tipp - nz * w * 0.6), (4.35, 0.15 + dy * root - ny * w, dz * root - nz * w)]
        f.append((q, WOOD))
        f.append((q[::-1], WOOD))
    return f


def render(scale, yaw=216.0, pitch=22.0, light=(-0.35, 0.85, 0.4)):
    """-> RGBA image of the plane, and its anchor (the point under the wheels)."""
    faces = plane_faces()
    ty, py = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(ty), 0, math.sin(ty)], [0, 1, 0], [-math.sin(ty), 0, math.cos(ty)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(py), -math.sin(py)], [0, math.sin(py), math.cos(py)]])
    R = Rx @ Ry
    L = np.array(light) / np.linalg.norm(light)
    items = []
    for q, col in faces:
        P = np.array(q) @ R.T
        a, b = P[1] - P[0], P[2] - P[0]
        nrm = np.cross(a, b)
        if np.linalg.norm(nrm) < 1e-9:
            continue
        nrm /= np.linalg.norm(nrm)
        if nrm[2] <= 0:                                                 # facing away
            continue
        nw = (np.array(np.cross(np.array(q[1]) - q[0], np.array(q[2]) - q[0])))
        nw = nw / (np.linalg.norm(nw) or 1)
        k = 0.5 + 0.62 * max(0.0, float(nw @ L)) + 0.12 * nrm[2]
        c = tuple(min(255, int(ch * k)) for ch in col)
        items.append((P[:, 2].mean(), P, c))
    items.sort(key=lambda t: t[0])
    pts = np.concatenate([it[1] for it in items])
    minx, maxx = pts[:, 0].min(), pts[:, 0].max()
    miny, maxy = (-pts[:, 1]).min(), (-pts[:, 1]).max()
    pad = 4
    Wd, Hd = int((maxx - minx) * scale) + 2 * pad, int((maxy - miny) * scale) + 2 * pad
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _, P, c in items:
        xy = [((x - minx) * scale + pad, (-y - miny) * scale + pad) for x, y, _ in P]
        d.polygon(xy, fill=c + (255,))
        d.line(xy + [xy[0]], fill=c + (255,), width=1)
    # silhouette outline
    a = np.asarray(im)[:, :, 3] > 0
    edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    arr = np.asarray(im).copy()
    arr[edge] = (40, 36, 60, 255)
    out = Image.fromarray(arr)
    ground = ((np.array([1.45, -3.4, 0]) @ R.T))
    anchor = ((ground[0] - minx) * scale + pad, (-ground[1] - miny) * scale + pad)
    return out, anchor

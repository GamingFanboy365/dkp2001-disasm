"""Rusty and his plane as a small 3D model (updates patch; original design, ours).

Rusty is a rooster farmer: rust-red feathers, a cream chest, a red comb, a straw hat
tilted back, a yellow beak and red wattle, denim overalls. His plane is the teal monoplane
parked on the BEST TIMES screen (updates/art/cup_results/plane3d.py): red cowling, yellow
wings, an orange stripe. Built from smooth lofted shapes and rendered with a depth buffer,
soft wrap-around light and a dark edge, the way the game's own racers were pre-rendered.

    render(view, size) -> RGBA image of the model seen from `view`

`view` is (elevation, heading) in degrees: elevation 90 looks straight down, -90 straight
up; heading 0 is from behind, 90 from the side with the nose to the left (as the game's
frames have it), 180 head-on. The plane's nose is +x, up is +y.
"""
import math

import numpy as np
from PIL import Image, ImageFilter

TEAL = (34, 178, 210)
CREAM = (248, 234, 200)
ORANGE = (244, 132, 44)
SUNNY = (255, 214, 48)
RED = (216, 52, 44)
DARK = (56, 40, 44)
WHITE = (242, 242, 246)
TYRE = (48, 48, 58)
RUST = (228, 80, 32)
RUST_LIGHT = (248, 146, 72)
TAIL_GREEN = (36, 104, 84)
TAIL_BLUE = (36, 70, 110)
COMB = (232, 36, 44)
BEAK = (252, 180, 36)
DENIM = (58, 112, 214)
STRAW = (248, 214, 112)
BAND = (204, 56, 48)
EYE = (255, 255, 255)
PUPIL = (24, 20, 24)
GLASS = (176, 226, 248)
METAL = (150, 150, 164)


class Mesh:
    def __init__(self):
        self.tris = []                      # (3x3 vertices, 3x3 normals, colour, lit)

    def add(self, v, n, col, lit=True):
        self.tris.append((np.array(v, float), np.array(n, float), col, lit))


def _grid(m, P, N, C, closed_u=True, lit=True):
    """Triangles from a grid of points P[i][j], normals N[i][j], colours C[i][j]."""
    nv, nu = len(P), len(P[0])
    for i in range(nv - 1):
        for j in range(nu - (0 if closed_u else 1)):
            j2 = (j + 1) % nu
            col = C[i][j]
            for tri in (((i, j), (i + 1, j), (i + 1, j2)), ((i, j), (i + 1, j2), (i, j2))):
                m.add([P[a][b] for a, b in tri], [N[a][b] for a, b in tri], col, lit)


def ellipsoid(m, centre, radii, col, rot=None, segs=(24, 16), colour_fn=None):
    R = np.eye(3) if rot is None else np.array(rot)
    nu, nv = segs
    P, N, C = [], [], []
    for i in range(nv + 1):
        th = math.pi * i / nv
        rp, rn, rc = [], [], []
        for j in range(nu):
            ph = 2 * math.pi * j / nu
            u = np.array([math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)])
            rp.append(R @ (u * radii) + centre)
            n = R @ (u / radii)
            rn.append(n / (np.linalg.norm(n) or 1))
            rc.append(colour_fn(u) if colour_fn else col)
        P.append(rp), N.append(rn), C.append(rc)
    _grid(m, P, N, C)


def loft(m, sections, colour_fn, segs=24, power=2.0):
    """A body along x: sections are (x, y_centre, half_height, half_width); cross sections are
    superellipses (power 2 = ellipse). colour_fn(x, angle) gives the colour."""
    P, N, C = [], [], []
    xs = [s[0] for s in sections]
    for k, (x, yc, hh, hw) in enumerate(sections):
        rp, rc = [], []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            ca, sa = math.cos(a), math.sin(a)
            e = 2.0 / power
            y = yc + hh * math.copysign(abs(sa) ** e, sa)
            z = hw * math.copysign(abs(ca) ** e, ca)
            rp.append(np.array([x, y, z]))
            rc.append(colour_fn(x, a))
        P.append(rp), C.append(rc)
    for k in range(len(P)):                       # normals from the neighbouring points
        rn = []
        for j in range(segs):
            a = P[max(k - 1, 0)][j]
            b = P[min(k + 1, len(P) - 1)][j]
            c = P[k][(j - 1) % segs]
            d = P[k][(j + 1) % segs]
            n = np.cross(b - a, d - c)
            if np.linalg.norm(n) < 1e-9:
                n = np.array([1.0 if k else -1.0, 0, 0])
            n = -n / np.linalg.norm(n)
            centre = np.array([P[k][0][0], sections[k][1], 0])
            if np.dot(n, P[k][j] - centre) < 0:
                n = -n
            rn.append(n)
        N.append(rn)
    _grid(m, P, N, C)
    for k, sgn in ((0, -1), (len(P) - 1, 1)):     # caps
        c = np.mean(P[k], axis=0)
        n = np.array([sgn, 0, 0.0])
        for j in range(segs):
            j2 = (j + 1) % segs
            tri = [c, P[k][j], P[k][j2]] if sgn > 0 else [c, P[k][j2], P[k][j]]
            m.add(tri, [n] * 3, C[k][j])


def disc(m, centre, normal, radius, col, segs=24, ring=None, lit=True, inner=0.0):
    c = np.array(centre, float)
    nrm = np.array(normal, float) / np.linalg.norm(normal)
    a = np.cross(nrm, [0, 1, 0] if abs(nrm[1]) < 0.9 else [1, 0, 0])
    a /= np.linalg.norm(a)
    b = np.cross(nrm, a)
    for k in range(segs):
        t0, t1 = 2 * math.pi * k / segs, 2 * math.pi * (k + 1) / segs
        o0 = c + radius * (math.cos(t0) * a + math.sin(t0) * b)
        o1 = c + radius * (math.cos(t1) * a + math.sin(t1) * b)
        i0 = c + inner * (math.cos(t0) * a + math.sin(t0) * b)
        i1 = c + inner * (math.cos(t1) * a + math.sin(t1) * b)
        colour = ring(k) if ring else col
        for tri in ((i0, o0, o1), (i0, o1, i1)):
            m.add(list(tri), [nrm] * 3, colour, lit)
            m.add(list(tri)[::-1], [-nrm] * 3, colour, lit)


def wing(m, root, tip, y, span, th, col, dihedral=0.25, sweep=0.0, segs=8):
    """A rounded wing from z=0 to z=span (sign = side): an airfoil-ish lofted slab whose
    chord shrinks from root to tip; root/tip are (x_lead, x_trail)."""
    s = 1 if span > 0 else -1
    P, N, C = [], [], []
    rows = 9
    for i in range(rows + 1):
        t = i / rows
        z = span * t
        lead = root[0] + (tip[0] - root[0]) * t - sweep * t
        trail = root[1] + (tip[1] - root[1]) * t
        if t > 0.8:                                     # round the tip
            r = math.sqrt(max(0.0, 1 - ((t - 0.8) / 0.2) ** 2))
            mid = (lead + trail) / 2
            lead, trail = mid + (lead - mid) * r, mid + (trail - mid) * r
        yy = y + dihedral * abs(z) / abs(span) * abs(span) * 0.1
        tt = th * (1 - 0.5 * t)
        rp, rn, rc = [], [], []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            x = (lead + trail) / 2 + (lead - trail) / 2 * math.cos(a)
            yv = yy + tt * math.sin(a) * (1.0 if math.sin(a) > 0 else 0.45)
            rp.append(np.array([x, yv, z]))
            n = np.array([math.cos(a) * tt, math.sin(a) * abs(lead - trail) / 2, 0])
            rn.append(n / (np.linalg.norm(n) or 1))
            rc.append(col)
        P.append(rp), N.append(rn), C.append(rc)
    if s < 0:
        P, N, C = P, N, C
    _grid(m, P, N, C)


def add_head(m, hc, icon=False):
    """Rusty's head at hc: rust feathers, cream cheeks, wattle, beak, big eyes with brows,
    the comb through a straw hat tilted back. icon=True exaggerates the face for his 20-pixel
    racer icon (bigger eyes and pupils, a bolder beak, a narrower brim), as the game's own
    icons do."""
    e, pu, bk, brim = (1.45, 1.9, 1.15, 0.75) if icon else (1.0, 1.0, 1.0, 1.0)
    ellipsoid(m, hc, (1.5, 1.48, 1.42), RUST, segs=(28, 18),
              colour_fn=lambda u: RUST_LIGHT if u[1] > 0.45 else (CREAM if (u[0] > 0.7 and u[1] < -0.15) else RUST))
    for z in (0.48, -0.48):
        ellipsoid(m, hc + (1.18, 0.28, z * 1.1 * (1.1 if icon else 1)), np.array((0.36, 0.5, 0.36)) * e, EYE, segs=(12, 10))
        ellipsoid(m, hc + (1.48 + (0.18 if icon else 0), 0.24, z * (1.1 if icon else 1)),
                  np.array((0.13, 0.25, 0.16)) * pu, PUPIL, segs=(8, 6))
        rot = [[1, 0, 0], [0, math.cos(0.4 * np.sign(z)), -math.sin(0.4 * np.sign(z))],
               [0, math.sin(0.4 * np.sign(z)), math.cos(0.4 * np.sign(z))]]
        ellipsoid(m, hc + (1.25, 0.86 + (0.2 if icon else 0), z * 1.15), np.array((0.24, 0.1, 0.36)) * (1.3 if icon else 1),
                  (90, 30, 18) if icon else (110, 40, 24), rot=rot, segs=(10, 6))
    ellipsoid(m, hc + (1.75 + (0.1 if icon else 0), -0.22, 0), np.array((0.85, 0.3, 0.36)) * bk, BEAK, segs=(14, 8))
    ellipsoid(m, hc + (1.55, -0.48, 0), np.array((0.6, 0.18, 0.3)) * bk, (232, 150, 30), segs=(12, 6))
    ellipsoid(m, hc + (1.3, -0.98, 0), np.array((0.25, 0.48, 0.2)) * bk, COMB, segs=(10, 8))   # wattle
    # the comb, three bumps standing up through a straw hat tilted back
    for k, (dx, r) in enumerate(((0.55, 0.36), (0.05, 0.44), (-0.45, 0.36))):
        ellipsoid(m, hc + (dx, 1.72 + (0.12 if k == 1 else 0), 0), (r * 1.1, r * 1.1, 0.19), COMB, segs=(12, 8))
    tilt = -0.3
    rot = [[math.cos(tilt), -math.sin(tilt), 0], [math.sin(tilt), math.cos(tilt), 0], [0, 0, 1]]
    ellipsoid(m, hc + (-0.35, 1.18, 0), (1.55 * brim, 0.11, 1.5 * brim), STRAW, rot=rot, segs=(28, 6))   # brim
    ellipsoid(m, hc + (-0.45, 1.42, 0), (0.85, 0.4, 0.82), STRAW, rot=rot, segs=(20, 10),
              colour_fn=lambda u: BAND if -0.6 < u[1] < -0.1 else STRAW)
    return m


def build_head():
    """Just Rusty's head, its face exaggerated for his racer icon."""
    m = Mesh()
    add_head(m, np.array([0.0, 0.0, 0.0]), icon=True)
    return m


def build(propeller_spin=True):
    m = Mesh()

    # ---------------------------------------------------------------- the plane
    def hull(x, a):
        y = math.sin(a)
        if y < -0.5:
            return CREAM
        if -0.15 < y < 0.2 and -3.6 < x < 2.6:
            return ORANGE
        return TEAL
    loft(m, [(-4.6, 0.55, 0.25, 0.22), (-4.0, 0.45, 0.55, 0.45), (-3.0, 0.3, 0.95, 0.85),
             (-1.8, 0.15, 1.3, 1.2), (-0.6, 0.05, 1.55, 1.45), (0.8, 0.0, 1.65, 1.55),
             (2.0, 0.0, 1.62, 1.55), (2.8, 0.0, 1.55, 1.5)], hull, segs=28)
    # cowling: a red ring with the dark engine inside, a white spinner
    loft(m, [(2.75, 0.0, 1.62, 1.62), (3.3, 0.0, 1.75, 1.75), (3.75, 0.0, 1.7, 1.7), (3.95, 0.0, 1.5, 1.5)],
         lambda x, a: RED if x < 3.85 else (180, 40, 36), segs=28)
    disc(m, (3.96, 0.0, 0), (1, 0, 0), 1.48, DARK, segs=28)
    ellipsoid(m, (4.15, 0.0, 0), (0.75, 0.62, 0.62), WHITE, segs=(16, 10))
    if propeller_spin:                                 # the spinning disc, as the game draws them
        disc(m, (4.35, 0.0, 0), (1, 0, 0), 1.95, WHITE, segs=32, inner=0.55,
             ring=lambda k: (232, 92, 72) if k % 8 in (0, 1) else (248, 244, 240), lit=False)
    # wings, tailplane, fin with an orange rudder
    for sp in (5.4, -5.4):
        wing(m, (2.0, -0.6), (1.4, 0.3), -0.95, sp, 0.42, SUNNY, sweep=0.2)
    for sp in (2.3, -2.3):
        wing(m, (-3.2, -4.4), (-3.7, -4.3), 0.25, sp, 0.18, SUNNY)
    loft(m, [(-4.55, 1.05, 0.65, 0.12), (-4.05, 1.1, 0.7, 0.16), (-3.35, 0.75, 0.4, 0.15), (-3.0, 0.55, 0.22, 0.12)],
         lambda x, a: ORANGE if x < -4.25 else TEAL, segs=12)
    # wing roundels of ours (an orange ring, a cream centre) and a windscreen
    for z in (3.9, -3.9):
        disc(m, (0.9, -0.42, z), (0, 1, 0), 0.72, (240, 96, 56), segs=16, inner=0.36)
        disc(m, (0.9, -0.415, z), (0, 1, 0), 0.36, CREAM, segs=12)
    loft(m, [(1.6, 1.9, 0.05, 0.9), (1.75, 2.2, 0.32, 0.85), (1.9, 2.0, 0.42, 0.8)],
         lambda x, a: GLASS, segs=12, power=3)
    # undercarriage: struts and spatted wheels
    for z in (1.9, -1.9):
        loft(m, [(1.15, -1.4, 0.08, 0.08), (1.2, -2.2, 0.08, 0.08)], lambda x, a: METAL, segs=6)
        ellipsoid(m, (1.2, -2.6, z), (0.78, 0.78, 0.32), TYRE, segs=(16, 8))
        ellipsoid(m, (1.2, -2.35, z), (1.0, 0.55, 0.42), SUNNY, segs=(16, 8),
                  colour_fn=lambda u: SUNNY if u[1] > -0.2 else TYRE)
    ellipsoid(m, (-4.2, -0.05, 0), (0.25, 0.25, 0.12), TYRE, segs=(10, 6))

    # ---------------------------------------------------------------- Rusty
    # chest and overalls (a bib with straps), rust shoulders
    def body(u):
        if u[1] > 0.55:
            return RUST
        if u[0] > 0.6 and u[1] > -0.1 and abs(u[2]) < 0.35:
            return CREAM                                 # his chest feathers above the bib
        if abs(u[2]) > 0.62:
            return RUST
        return DENIM
    ellipsoid(m, (0.2, 2.1, 0), (1.25, 1.35, 1.3), DENIM, segs=(24, 16), colour_fn=body)
    for z in (0.55, -0.55):                              # straps' buttons
        ellipsoid(m, (1.3, 2.6, z), (0.16, 0.16, 0.16), SUNNY, segs=(8, 6))
    # wings as arms, resting forward on the cockpit rim
    for z in (1.15, -1.15):
        rot = [[math.cos(-0.5), -math.sin(-0.5), 0], [math.sin(-0.5), math.cos(-0.5), 0], [0, 0, 1]]
        ellipsoid(m, (0.95, 2.0, z * 1.05), (1.0, 0.45, 0.38), RUST, rot=rot, segs=(14, 8),
                  colour_fn=lambda u: RUST_LIGHT if u[1] > 0.3 else RUST)
    add_head(m, np.array([0.5, 4.05, 0.0]))
    # tail feathers rising behind him
    for k, (ang, col) in enumerate(((0.9, TAIL_BLUE), (0.65, TAIL_GREEN), (0.4, TAIL_BLUE), (0.2, RUST))):
        rot = [[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]]
        ellipsoid(m, (-1.25 - 0.15 * k, 2.7 + 0.05 * k, (k - 1.5) * 0.28), (1.0, 0.24, 0.12), col, rot=rot,
                  segs=(12, 6))
    return m


CENTRE_Y = 1.9                                          # wheels to comb, centred
LIGHT = np.array([-0.35, 0.8, 0.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
FILL = np.array([0.3, -0.7, 0.3])
FILL = FILL / np.linalg.norm(FILL)


def view_matrix(elevation, heading):
    """World -> camera: x right, y up, z toward the viewer. Heading 0 looks from behind."""
    h = math.radians(heading)
    e = math.radians(elevation)
    eye = np.array([-math.cos(e) * math.cos(h), math.sin(e), -math.cos(e) * math.sin(h)])
    fwd = -eye
    up = np.array([0.0, 1.0, 0.0])
    if abs(abs(e) - math.pi / 2) < 1e-6:
        up = np.array([1.0, 0.0, 0.0])                 # the poles: nose to the top of the screen
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up2 = np.cross(right, fwd)
    return np.array([right, up2, -fwd])


def render(view, size=256, scale=None, mesh=None, focus=None):
    """Orthographic, z-buffered, smooth-shaded render -> RGBA (size x size), centred on the
    model's middle (or on the world point `focus`)."""
    mesh = mesh or build()
    M = view_matrix(*view)
    scale = scale or size / 12.0
    img = np.zeros((size, size, 3), float)
    alpha = np.zeros((size, size), bool)
    zbuf = np.full((size, size), -1e9)
    cx, cy = size / 2, size / 2 + CENTRE_Y * scale      # the model's middle at the frame's
    if focus is not None:
        fc = M @ np.array(focus, float)
        cx, cy = size / 2 - fc[0] * scale, size / 2 + fc[1] * scale
    Lc, Fc = M @ LIGHT, M @ FILL
    H = (Lc + [0, 0, 1]) / np.linalg.norm(Lc + [0, 0, 1])
    for v, n, col, lit in mesh.tris:
        P = v @ M.T
        N = n @ M.T
        sx = cx + P[:, 0] * scale
        sy = cy - P[:, 1] * scale
        x0, x1 = int(max(0, math.floor(sx.min()))), int(min(size - 1, math.ceil(sx.max())))
        y0, y1 = int(max(0, math.floor(sy.min()))), int(min(size - 1, math.ceil(sy.max())))
        if x0 > x1 or y0 > y1:
            continue
        den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
        if abs(den) < 1e-12:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((sy[1] - sy[2]) * (xs - sx[2]) + (sx[2] - sx[1]) * (ys - sy[2])) / den
        w1 = ((sy[2] - sy[0]) * (xs - sx[2]) + (sx[0] - sx[2]) * (ys - sy[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * P[0, 2] + w1 * P[1, 2] + w2 * P[2, 2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > sub)
        if not win.any():
            continue
        nx = w0[..., None] * N[0] + w1[..., None] * N[1] + w2[..., None] * N[2]
        nx /= np.linalg.norm(nx, axis=-1, keepdims=True) + 1e-9
        flip = nx[..., 2] < 0
        nx[flip] = -nx[flip]
        if lit:
            wrap = np.clip((nx @ Lc + 0.35) / 1.35, 0, 1)        # soft wrap-around light
            fill = np.clip(nx @ Fc, 0, 1)
            rim = 0.84 + 0.16 * np.clip(nx[..., 2], 0, 1)        # darker toward the silhouette
            k = (0.58 + 0.52 * wrap + 0.34 * fill) * rim
            spec = np.clip(nx @ H, 0, 1) ** 10 * 0.16
        else:
            k = np.ones(nx.shape[:2])
            spec = np.zeros(nx.shape[:2])
        c = np.array(col, float)[None, None, :] * k[..., None] + 255 * spec[..., None]
        sub[win] = z[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = np.clip(c, 0, 255)[win]
        alpha[y0:y1 + 1, x0:x1 + 1][win] = True
    out = np.zeros((size, size, 4), np.uint8)
    out[..., :3] = img.astype(np.uint8)
    out[..., 3] = alpha * 255
    return Image.fromarray(out, "RGBA")


def sprite(view, px=64, oversample=4, mesh=None):
    """The model at sprite size: rendered big, scaled down, hard-edged, with a dark rim like
    the game's racers -> RGBA px x px (alpha 0 or 255)."""
    big = render(view, px * oversample, mesh=mesh)
    small = big.resize((px, px), Image.LANCZOS)
    a = np.asarray(small).astype(float)
    mask = a[..., 3] > 110
    rgb = a[..., :3] / np.maximum(a[..., 3:4] / 255.0, 1e-3)
    rgb = np.clip(rgb, 0, 255)
    edge = mask & ~(np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1))
    rgb[edge] *= 0.55
    out = np.zeros((px, px, 4), np.uint8)
    out[..., :3] = rgb.astype(np.uint8)
    out[..., 3] = mask * 255
    return Image.fromarray(out, "RGBA")

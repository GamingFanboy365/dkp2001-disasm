#!/usr/bin/env python3
"""Build a course's object list and AI network from a course description.

    python3 tools/course_build.py updates/courses/temple_tangle.py

writes updates/courses/temple_tangle.s (assembled into the updates build) and
prints a summary. `--preview OUT.png ROM` also draws the course on its ground
map, with the racing line, pylons, pickups and scenery.

A description is a small Python file (see updates/courses/temple_tangle.py):

  NAME, LEVEL     label stem and the level whose tab_levels entry uses it
  LINE            the racing line: closed loop of (x, z, y) waypoints in world
                  units. The first point is the start hoop; the race flies from
                  it towards the second. A Catmull-Rom spline through them is
                  resampled every SPACING units into the AI routes.
  ROUTE_OFFSETS   sideways offsets of the five AI routes from the line
  PYLONS          (waypoint, side, distance): a pylon beside the line at that
                  waypoint, on the 'L' or 'R' of the racer; the racer must pass
                  between the pylon and the line... i.e. keep the pylon on that
                  side. Numbered in race order.
  ARROWS          (waypoint, code): HUD turn hints, 0 hard left .. 4 hard right
  PICKUPS         (kind, waypoint, offset, height): bananas, powerups, turbos
  BOOSTS          (kind, waypoint, offset): 'air' (booster) or 'ground'
  SCENERY         (kind, x, z, scale): palm trees, pillars...
  CAMERA          every how many route points the front-end fly-in takes one

Object formats: NOTES.md ("Course objects"). Everything here is ours.
"""
import importlib.util
import math
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# object types (tab_types)
T_START, T_HOOP, T_PYLON = 4, 5, 52
T_BANANA, T_TURBO = 32, 31
T_POWERUP = {"weapon": 27, "weapon13": 29, "weapon14": 30}
T_BOOSTER, T_GROUNDBOOST, T_ARROW = 57, 63, 76
T_SCENERY = {"palm": 89, "pillar": 90, "palm_tall": 15}


def heading_byte(dx, dz):
    """The record byte b for a direction, where the game's heading is (128 - b) << 8 and a
    heading h points along (sin h, cos h) in (x, z)."""
    h = math.atan2(dx, dz) / (2 * math.pi) * 256
    return int(round(128 - h)) & 255


def catmull_loop(pts, spacing):
    """Closed Catmull-Rom spline through pts (x, z, y), resampled about every `spacing` units.
    Returns the samples and, for each input waypoint, the index of its sample."""
    n = len(pts)
    dense, marks = [], []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        marks.append(len(dense))
        for k in range(40):
            t = k / 40
            t2, t3 = t * t, t * t * t
            dense.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                      + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)))
    # resample by arc length
    out, out_marks, acc = [dense[0]], {0: 0}, 0.0
    mark_at = {m: i for i, m in enumerate(marks)}
    for i in range(1, len(dense)):
        acc += math.dist(dense[i][:2], dense[i - 1][:2])
        if i in mark_at:
            # a waypoint is always a route point; drop a sample that landed just before it
            # (Rare's routes never have very short segments, and ai_steer divides by length)
            if len(out) > 1 and math.dist(out[-1][:2], dense[i][:2]) < spacing * 0.5:
                out.pop()
            out_marks[mark_at[i]] = len(out)
            out.append(dense[i])
            acc = 0
        elif acc >= spacing:
            out.append(dense[i])
            acc = 0
    return out, [out_marks[i] for i in range(n)]


PYLON_INFO = []      # (order, x, z, pass ray, strike ray, margin, live range) for check()
RUNUP = 570          # how far behind the hoop the planes start (init_start_pos)


def deg_byte(deg):
    """Record byte for a bearing in degrees (0 = +z, 90 = +x), as heading_byte."""
    return int(round(128 - deg / 360 * 256)) & 255


def angdiff(a, b):
    return (a - b + 180) % 360 - 180


def bearing(px, pz, x, z):
    return math.degrees(math.atan2(x - px, z - pz))


def racer_paths(c, line):
    """Each AI route, plus wider ones for racers that drift, densely sampled, with the
    run-up into the start in front: [(index into line, x, z), ...] per path."""
    paths = []
    n = len(line)
    offs = list(c.ROUTE_OFFSETS) + [max(c.ROUTE_OFFSETS) + 10, min(c.ROUTE_OFFSETS) - 10]
    for off in offs:
        pts = []
        (hx, hz, _), f, l = frame(line, 0)
        for k in range(RUNUP, 0, -10):                      # the run-up, index -1
            pts.append((-1, hx - f[0] * k + l[0] * off, hz - f[1] * k + l[1] * off))
        for i in range(n):
            (x0, z0, _), f0, l0 = frame(line, i)
            (x1, z1, _), f1, l1 = frame(line, (i + 1) % n)
            for k in range(8):
                t = k / 8
                pts.append((i, x0 + (x1 - x0) * t + (l0[0] + (l1[0] - l0[0]) * t) * off,
                               z0 + (z1 - z0) * t + (l0[1] + (l1[1] - l0[1]) * t) * off))
        paths.append(pts)
    return paths


def live_range(c, line, marks, order):
    """Route indices while pylon `order` is the live one: from the previous pylon (or the
    start, run-up included) to a little past this one."""
    lo = marks[c.PYLONS[order - 1][0]] if order else -1
    return lo, marks[c.PYLONS[order][0]] + 3


def in_live(i, live):
    return live[0] <= i <= live[1] or (live[0] == -1 and i == -1)


def strike_ray(paths, live, px, pz, a):
    """The strike ray facing away from the line (within 110 degrees of opposite the pass ray)
    that keeps furthest from every racer's bearing while the pylon is live."""
    bearings = [bearing(px, pz, x, z) for path in paths for i, x, z in path if in_live(i, live)]
    best = None
    for k in range(-110, 111, 2):
        b = a + 180 + k
        m = min(abs(angdiff(br, b)) for br in bearings)
        if best is None or m > best[1] or (m == best[1] and abs(k) < abs(best[2])):
            best = (b % 360, m, k)
    return best[0], best[1]


def crossings(px, pz, ray, pts):
    """Positions where the game's test fires for a ray: the bearing crosses it (the sign of
    the difference changes, within 90 degrees of it)."""
    out, prev = [], None
    for x, z in pts:
        d = angdiff(bearing(px, pz, x, z), ray)
        if prev is not None and (d < 0) != (prev < 0) and abs(d) <= 90:
            out.append((x, z))
        prev = d
    return out


def frame(line, i):
    """Point i of the line, its forward unit vector and its left unit vector (in x, z)."""
    n = len(line)
    a, b = line[(i - 1) % n], line[(i + 1) % n]
    dx, dz = b[0] - a[0], b[1] - a[1]
    m = math.hypot(dx, dz) or 1
    fx, fz = dx / m, dz / m
    # x right, z down (as in the map pictures): the racer's left is (fz, -fx)
    return line[i], (fx, fz), (fz, -fx)


def load(path):
    spec = importlib.util.spec_from_file_location("course", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(c):
    line, marks = catmull_loop(c.LINE, c.SPACING)
    objs = []                                       # (type, x, y, z, data bytes)

    def at(wp, offset=0.0):
        (x, z, y), f, l = frame(line, marks[wp])
        return x + l[0] * offset, z + l[1] * offset, y, f, l

    # start: hoop at the first waypoint, four start positions just behind it
    x, z, y, f, l = at(0)
    hb = heading_byte(*f)
    objs.append((T_HOOP, x, 0, z, [hb]))
    for slot, (side, h) in enumerate(((-17, 5), (-7, 13), (7, 13), (17, 5))):
        objs.append((T_START, x + l[0] * side, h, z + l[1] * side, [slot, hb]))
    # pylons, in race order
    paths = racer_paths(c, line)
    hidden = getattr(c, "HIDDEN_PYLONS", None)
    for order, (wp, side, dist) in enumerate(c.PYLONS):
        off = dist if side == "L" else -dist
        px, pz, _, f, l = at(wp, off)
        lx, lz, _, _, _ = at(wp)
        if hidden:
            # a checkpoint: out of sight above the ground, just outside the wall on that
            # side, so its pass line spans the track and nobody can get round its far end
            compass = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
            sx, sz = compass.get(side) or ((l[0], l[1]) if side == "L" else (-l[0], -l[1]))
            x0, z0, x1, z1 = c.BOUNDS
            ts = [t for t in ((x0 - lx) / sx if sx < 0 else (x1 - lx) / sx if sx > 0 else 1e9,
                              (z0 - lz) / sz if sz < 0 else (z1 - lz) / sz if sz > 0 else 1e9)]
            t = min(ts) + hidden["outside"]
            px, pz = lx + sx * t, lz + sz * t
        # pass ray: from the pylon towards the line
        if hidden:
            m = math.hypot(lx - px, lz - pz)
            ax, az = (lx - px) / m, (lz - pz) / m
        else:
            ax, az = -l[0] * (1 if side == "L" else -1), -l[1] * (1 if side == "L" else -1)
        a_deg = math.degrees(math.atan2(ax, az))
        # strike ray: the direction no racer's bearing comes near while this pylon is live
        live = live_range(c, line, marks, order)
        b_deg, margin = strike_ray(paths, live, px, pz, a_deg)
        # flip byte: 0 when the pass ray points to the racer's left
        left = (ax * l[0] + az * l[1]) > 0
        objs.append((T_PYLON, px, hidden["height"] if hidden else 0, pz,
                     [deg_byte(a_deg), order, deg_byte(b_deg), 0 if left else 1]))
        PYLON_INFO.append((order, px, pz, a_deg, b_deg, margin, live, (lx, lz)))
    for wp, code in c.ARROWS:
        x, z, _, f, l = at(wp)
        objs.append((T_ARROW, x, 0, z, [code]))
    for kind, wp, off, h in c.PICKUPS:
        x, z, _, f, l = at(wp, off)
        if kind == "banana":
            objs.append((T_BANANA, x, h, z, []))
        elif kind == "turbo":
            objs.append((T_TURBO, x, h, z, [0]))
        else:
            objs.append((T_POWERUP[kind], x, h, z, []))
    for kind, wp, off in c.BOOSTS:
        x, z, y, f, l = at(wp, off)
        objs.append((T_BOOSTER if kind == "air" else T_GROUNDBOOST, x, y if kind == "air" else 0, z,
                     [heading_byte(*f)]))
    for kind, x, z, scale in c.SCENERY:
        objs.append((T_SCENERY[kind], x, 0, z, [scale]))
    return line, marks, objs


def check(c, line, objs):
    """Solid scenery must stay off the racing line; pylons must be in front of the hoop."""
    problems = []
    for t, x, y, z, d in objs:
        if t in T_SCENERY.values():
            near = min(math.dist((x, z), p[:2]) for p in line)
            if near < c.SCENERY_CLEARANCE:
                problems.append(f"scenery at ({x:.0f}, {z:.0f}) is {near:.0f} units from the line")
    # separate stretches of track need grass between them, or they merge into one (and the
    # walls let you cut across): any two line points far apart round the lap must be at
    # least two half-widths plus GRASS_GAP apart
    if hasattr(c, "TRACK_HALF_WIDTH"):
        need = 2 * c.TRACK_HALF_WIDTH + getattr(c, "GRASS_GAP", 40)
        dense = []
        for i in range(len(line)):
            (x0, z0, _), (x1, z1, _) = line[i], line[(i + 1) % len(line)]
            for k in range(4):
                dense.append((x0 + (x1 - x0) * k / 4, z0 + (z1 - z0) * k / 4))
        cum = [0.0]
        for i in range(1, len(dense)):
            cum.append(cum[-1] + math.dist(dense[i], dense[i - 1]))
        lap = cum[-1] + math.dist(dense[-1], dense[0])
        worst = {}
        for i in range(len(dense)):
            for j in range(i + 1, len(dense)):
                along = min(cum[j] - cum[i], lap - (cum[j] - cum[i]))
                if along > need * 2.2:
                    d = math.dist(dense[i], dense[j])
                    if d < need:
                        key = (round(dense[i][0], -2), round(dense[i][1], -2))
                        if key not in worst or d < worst[key][0]:
                            worst[key] = (d, dense[i], dense[j])
        for d, a_, b_ in sorted(worst.values())[:6]:
            problems.append(f"track at {a_[0]:.0f},{a_[1]:.0f} is {d:.0f} units from track at "
                            f"{b_[0]:.0f},{b_[1]:.0f} (needs {need:.0f})")
    # every racer path must pass each pylon (cross its pass ray) and never strike it while live
    paths = racer_paths(c, line)
    for order, px, pz, a, b, margin, live, spot in PYLON_INFO:
        if margin < 20:
            problems.append(f"pylon {order}: racers' bearings come within {margin:.0f} degrees of its strike ray")
        for k, path in enumerate(paths):
            pts = [(x, z) for i, x, z in path if in_live(i, live)]
            passes, strikes = crossings(px, pz, a, pts), crossings(px, pz, b, pts)
            if strikes:
                problems.append(f"pylon {order}: path {k} strikes it at {strikes[0][0]:.0f},{strikes[0][1]:.0f}")
            if not passes:
                problems.append(f"pylon {order}: path {k} never passes it")
            elif math.dist(passes[0], spot) > 120:
                problems.append(f"pylon {order}: path {k} passes it early, at {passes[0][0]:.0f},{passes[0][1]:.0f}")
    # pylon 0 keeps last lap's bearing when a lap starts (the game doesn't reset it), so a
    # racer at the hoop must not look like it crossed a ray
    if PYLON_INFO:
        order, px, pz, a, b, margin, live, spot = PYLON_INFO[0]
        (hx, hz, _), f, l = frame(line, 0)
        hb = bearing(px, pz, hx, hz)
        if abs(angdiff(hb, a)) <= 90 or abs(angdiff(hb, b)) <= 90:
            pass   # the stale bearing is from just past the pass ray: same side unless the hoop is near a ray
        for ray in (a, b):
            if abs(angdiff(hb, ray)) < 15:
                problems.append(f"pylon 0: the hoop is only {abs(angdiff(hb, ray)):.0f} degrees off one of its rays")
    # the planes start about 570 units behind the hoop and fly in: keep that run-up clear
    (hx, hz, _), f, l = frame(line, 0)
    for t, x, y, z, d in objs:
        if t in T_SCENERY.values():
            along = (x - hx) * -f[0] + (z - hz) * -f[1]
            side = abs((x - hx) * l[0] + (z - hz) * l[1])
            if 0 < along < 620 and side < 17 + c.SCENERY_CLEARANCE:
                problems.append(f"scenery at ({x:.0f}, {z:.0f}) is in the start run-up")
    return problems


def wall_grid(c, line):
    """The track's walls as a 64x64 grid of 16-unit cells (the game's world is 1024 units
    across): 0 for a cell on the track (within TRACK_HALF_WIDTH of the racing line), else
    0x80 | the direction back to the nearest point of the line, in 128ths of a turn (the
    game's 16-bit heading >> 9)."""
    segs = [(line[i - 1][:2], line[i][:2]) for i in range(len(line))]
    grid = bytearray(64 * 64)
    for j in range(64):
        for i in range(64):
            px, pz = 16 * i + 8, 16 * j + 8
            best = None
            for (ax, az), (bx, bz) in segs:
                dx, dz = bx - ax, bz - az
                t = max(0, min(1, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz or 1)))
                qx, qz = ax + dx * t, az + dz * t
                d = math.hypot(px - qx, pz - qz)
                if best is None or d < best[0]:
                    best = (d, qx, qz)
            d, qx, qz = best
            if d > c.TRACK_HALF_WIDTH:
                h = math.atan2(qx - px, qz - pz) / (2 * math.pi) * 128
                grid[j * 64 + i] = 0x80 | (int(round(h)) & 127)
    return grid


def hud_map(c, line):
    """The race HUD's course map: 64x64 pixels, one per 16 world units (act_hud_map puts
    a racer's arrow at its position / 16), drawn like Rare's: a white track (colour 5 of
    the HUD palette) with a dark grey edge (3), and a black and white start line (1, 5).
    Returns the 4096 pixel colour indices, row by row."""
    segs = [(line[i - 1][:2], line[i][:2]) for i in range(len(line))]
    half = c.TRACK_HALF_WIDTH * 0.6 if hasattr(c, "TRACK_HALF_WIDTH") else 48
    (hx, hz, _), f, l = frame(line, 0)
    px_ = bytearray(64 * 64)
    for v in range(64):
        for u in range(64):
            x, z = 16 * u + 8, 16 * v + 8
            d = min(math.dist((x, z), (ax + (bx - ax) * t, az + (bz - az) * t))
                    for (ax, az), (bx, bz) in segs
                    for t in [max(0, min(1, ((x - ax) * (bx - ax) + (z - az) * (bz - az)) /
                                         (((bx - ax) ** 2 + (bz - az) ** 2) or 1)))])
            if d <= half:
                along = (x - hx) * f[0] + (z - hz) * f[1]
                side = (x - hx) * l[0] + (z - hz) * l[1]
                if abs(along) < 12 and abs(side) <= half + 4:   # the start line: a checker strip
                    px_[v * 64 + u] = 1 if (int((side + 200) // 16) + (along > 0)) % 2 else 5
                else:
                    px_[v * 64 + u] = 5
            elif d <= half + 16:
                px_[v * 64 + u] = 3
    return px_


def sprite_blob(pixels):
    """A one-frame 64x64 4bpp sprite in the game's format (as __spr_hud_map_*): header,
    frame list, one OAM piece (64x64 at 32, 32), then the tiles, run-length coded as
    spr_update_vram reads them (see rle_tiles in tools/export_preview.py)."""
    import struct
    tiles = bytearray()
    for ty in range(8):
        for tx in range(8):
            for y in range(8):
                for x in range(0, 8, 2):
                    a = pixels[(ty * 8 + y) * 64 + tx * 8 + x]
                    b = pixels[(ty * 8 + y) * 64 + tx * 8 + x + 1]
                    tiles.append(a | b << 4)
    hw = [tiles[i] | tiles[i + 1] << 8 for i in range(0, len(tiles), 2)]
    cmds = []
    i = 0
    while i < len(hw):
        j = i
        while j < len(hw) and j - i < 128 and hw[j] == hw[i] and (hw[i] & 255) == hw[i] >> 8:
            j += 1
        if j - i >= 2:                                  # a run of one repeated byte
            cmds.append((hw[i] & 255) << 8 | (j - i - 1))
            i = j
            continue
        j = i
        lit = []
        while j < len(hw) and len(lit) < 128:
            if j + 1 < len(hw) and hw[j] == hw[j + 1] and (hw[j] & 255) == hw[j] >> 8:
                break
            lit.append(hw[j])
            j += 1
        cmds.append(0x80 | (len(lit) - 1))
        cmds += lit
        i = j
    blob = struct.pack("<16H", 32, 0, 0, 32, 32, 32, 32, 16, 1, 32, 0xC020, 0, 0, 0, 0, 0)
    blob += struct.pack("<8H", 1, 0, 0, 0, 0, 0, 0, 0)
    blob += struct.pack("<H", 64) + struct.pack(f"<{len(cmds)}H", *cmds) + struct.pack("<H", 0)
    return blob


def emit(c, line, objs, path):
    for t, x, y, z, d in objs:
        # the object list's x, y, z are unsigned hwords (obj_gen uses ldrh)
        if not (0 <= round(x) < 65536 and 0 <= round(y) < 65536 and 0 <= round(z) < 65536):
            sys.exit(f"object type {t} at ({x:.0f}, {y:.0f}, {z:.0f}): coordinates must be 0-65535")
    name = c.NAME
    out = [f"@ {name}: generated by tools/course_build.py from {os.path.basename(path)[:-2]}.py.",
           "@ Ours (updates patch). Edit the .py description, not this file.", "",
           "\t.section .fixes, \"ax\", %progbits", "\t.balign 4", f"obj_{name}:"]
    for i, (t, x, y, z, d) in enumerate(objs):
        out.append(f"\t.hword\t_{name}_r{i} - obj_{name}, {round(x)}, {round(y)}, {round(z)}")
    out.append("\t.hword\t0, 0, 0, 0")
    for i, (t, x, y, z, d) in enumerate(objs):
        data = "".join(f", {b}" for b in d)
        out += [f"_{name}_r{i}:", f"\t.hword\t{t}"]
        if d:
            out.append(f"\t.byte\t{', '.join(str(b) for b in d)}")
        out.append("\t.balign 2")
    # AI network: five racing routes plus the camera fly-in path
    routes = []
    for off in c.ROUTE_OFFSETS:
        pts = []
        for i in range(len(line)):
            (x, z, y), f, l = frame(line, i)
            pts.append((1, round(x + l[0] * off), round(y), round(z + l[1] * off)))
        routes.append(("p", pts))
    cam = []
    for i in range(0, len(line), c.CAMERA):
        (x, z, y), f, l = frame(line, i)
        yaw = math.degrees(math.atan2(f[0], -f[1]))           # 0 looks along -z, 90 along +x
        cam.append((3, round(x), round(y + 14), round(z), -10, round(yaw)))
    cam = cam[:32]
    routes.append(("c", cam))
    out += ["\t.balign 4", f"net_{name}:", f"\t.hword\t{len(routes)}"]
    out += [f"\t.hword\t_{name}_route{i} - net_{name}" for i in range(len(routes))]
    for i, (kind, pts) in enumerate(routes):
        out += [f"_{name}_route{i}:", f"\t.hword\t{len(pts)}"]
        for p in pts:
            out.append("\t.hword\t" + ", ".join(str(v) for v in p))
        if kind == "p":
            # ai_steer takes a segment's end as point i + 1 without wrapping, so on the
            # last segment it reads the 8 bytes after the route: make them the first point
            out.append("\t.hword\t" + ", ".join(str(v) for v in pts[0]) + "\t@ (not counted: closes the loop for ai_steer)")
    out.append("\t.balign 4")
    if getattr(c, "HUD_MAP", False):
        blob = sprite_blob(hud_map(c, line))
        out += ["@ the race HUD's course map (a sprite in the game's format)", "\t.balign 4",
                f"spr_hud_map_{name}:"]
        for i in range(0, len(blob), 16):
            out.append("\t.byte\t" + ", ".join(str(b) for b in blob[i:i + 16]))
        out.append("\t.balign 4")
    if hasattr(c, "TRACK_HALF_WIDTH"):
        grid = wall_grid(c, line)
        out += [f"@ the track's walls (updates/code/walls.s): 64x64 cells of 16 units, row by row",
                f"walls_{name}:"]
        for j in range(64):
            out.append("\t.byte\t" + ", ".join(str(b) for b in grid[j * 64:(j + 1) * 64]))
        out.append("\t.balign 4")
    open(path, "w").write("\n".join(out) + "\n")


def ground(c, line, rom_path):
    """A new level map (32x32 metatiles) that shows the track: paving where the race goes,
    grass elsewhere, made only of metatiles Rare used in GROUND["source"] (with that course's
    tile list, so they draw as they do there). Every 32-unit cell gets the metatile whose
    4x4 tiles best match the track at 8-unit detail (paving within TRACK_HALF_WIDTH of the
    racing line, grass outside), preferring plain paving and plain grass and avoiding
    stonework. Needs your ROM, to see what the tiles look like. Returns (map, metatiles)."""
    import random
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import course_audit as ca
    rom = ca.Rom(rom_path)
    g = c.GROUND
    lst = ca.SYM[g["tiles"]]
    bank = rom.u32(lst) + 2
    ids = [rom.u16(lst + 6 + 2 * i) for i in range(min(rom.u16(lst + 4), 256))]
    pal = [rom.u16(ca.SYM[g["palette"]] + 2 * i) for i in range(256)]
    pal = [((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8) for v in pal]
    frs = ca.SYM["__frs_dkp"]

    def tile_class(i):
        if i >= len(ids):
            return "O"
        px = rom.b[bank + 64 * ids[i] - 0x08000000:bank + 64 * ids[i] + 64 - 0x08000000]
        r = sum(pal[p][0] for p in px) / 64
        gg = sum(pal[p][1] for p in px) / 64
        b = sum(pal[p][2] for p in px) / 64
        if gg > 150 and r < 120:
            return "G"                          # grass
        if gg > r + 25 and gg > b + 25 and gg > 90:
            return "g"                          # leafy overgrowth
        if r > 170 and gg > 110 and b < 90 and abs(r - gg) < 40:
            return "Y"                          # yellow stones
        if 100 < r < 200 and 60 < gg < 160 and b < 90 and r > gg:
            return "P"                          # paving
        return "O"                              # stonework, border...
    tc = [tile_class(i) for i in range(256)]
    src = ca.SYM[g["source"]]
    used = {rom.u16(src + 4 + 2 * k) for k in range(1024)}
    metas = {m: [rom.b[frs + 16 * m + k - 0x08000000] for k in range(16)] for m in sorted(used)}
    # the plainest paving: the paving tiles the source course uses most
    from collections import Counter
    pc = Counter(t for ts in metas.values() for t in ts if tc[t] == "P")
    plain = {t for t, _ in pc.most_common(6)}
    segs = [(line[i - 1][:2], line[i][:2]) for i in range(len(line))]

    def dist(x, z):
        best = 1e9
        for (ax, az), (bx, bz) in segs:
            dx, dz = bx - ax, bz - az
            t = max(0, min(1, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz or 1)))
            best = min(best, math.hypot(x - ax - dx * t, z - az - dz * t))
        return best
    track = [[dist(8 * i + 4, 8 * j + 4) <= c.TRACK_HALF_WIDTH for i in range(128)] for j in range(128)]
    rng = random.Random(c.LEVEL)
    out = []
    for r in range(32):
        for q in range(32):
            want = [track[r * 4 + k // 4][q * 4 + k % 4] for k in range(16)]
            best = None
            for m, ts in metas.items():
                sc = 0.0
                for k, t in enumerate(ts):
                    ch = tc[t]
                    if ch == "O":
                        sc += 8
                    elif (ch in "PY") != want[k]:
                        sc += 4 if (k % 4 in (0, 3) or k // 4 in (0, 3)) else 2
                    elif ch == "P" and t not in plain:
                        sc += 0.6
                    elif ch == "Y":
                        sc += 0.6
                    elif ch == "g":
                        sc += 1.5
                sc += rng.random() * 0.4
                if best is None or sc < best[0]:
                    best = (sc, m)
            out.append(best[1])
    return out, metas


def preview(c, line, objs, rom_path, out):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import course_audit as ca
    from PIL import Image, ImageDraw
    rom = ca.Rom(rom_path)
    lvl = ca.ADDR[rom.u32(ca.SYM["tab_levels"] + 36 * c.LEVEL + 16)].replace("__map_", "")
    base = os.path.join(os.environ.get("PREVIEW_DIR", ""), "levels", lvl + ".png")
    im = Image.open(base).convert("RGB") if os.path.exists(base) else Image.new("RGB", (1024, 1024), (90, 90, 90))
    d = ImageDraw.Draw(im)
    for off, col in zip(c.ROUTE_OFFSETS, ((255, 255, 0), (255, 200, 0), (255, 150, 0), (255, 100, 0), (255, 60, 0))):
        pts = []
        for i in range(len(line)):
            (x, z, y), f, l = frame(line, i)
            pts.append((x + l[0] * off, z + l[1] * off))
        d.line(pts + [pts[0]], fill=col, width=2)
    cols = {T_HOOP: (0, 255, 0), T_START: (255, 0, 0), T_PYLON: (0, 160, 255), T_BANANA: (255, 255, 120),
            T_ARROW: (255, 255, 255), T_BOOSTER: (255, 0, 255), T_GROUNDBOOST: (255, 0, 160), T_TURBO: (0, 255, 255)}
    for t, x, y, z, dd in objs:
        col = cols.get(t, (255, 140, 0) if t in T_POWERUP.values() else (0, 90, 0))
        r = 10 if t in (T_PYLON, T_HOOP) else 6
        d.ellipse([x - r, z - r, x + r, z + r], fill=col, outline=(0, 0, 0))
        if t == T_PYLON:
            d.text((x + 12, z - 6), str(dd[1]), fill=(255, 255, 255))
    im.save(out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    c = load(src)
    line, marks, objs = build(c)
    for p in check(c, line, objs):
        print("warning:", p)
    emit(c, line, objs, src[:-3] + ".s")
    length = sum(math.dist(line[i][:2], line[i - 1][:2]) for i in range(len(line)))
    short = min(math.dist(line[i][:2], line[i - 1][:2]) for i in range(len(line)))
    if short < c.SPACING * 0.45:
        print(f"warning: shortest route segment is {short:.0f} units")
    print(f"{c.NAME}: {len(objs)} objects, {len(line)} route points, lap {length:.0f} units")
    if "--ground" in sys.argv:
        rom_path = sys.argv[sys.argv.index("--ground") + 1]
        m, _ = ground(c, line, rom_path)
        path = src[:-3] + "_ground.s"
        lines = [f"@ {c.NAME}'s ground: generated by tools/course_build.py --ground from {os.path.basename(src)}.",
                 f"@ Ours (updates patch): a 32x32 level map whose entries are Rare's metatiles (from",
                 f"@ {c.GROUND['source']}, drawn with {c.GROUND['tiles']}), arranged to show the track.",
                 "", "\t.section .fixes, \"ax\", %progbits", "\t.balign 4", f"map_{c.NAME}:",
                 "\t.hword\t32, 32"]
        for r in range(32):
            lines.append("\t.hword\t" + ", ".join(str(v) for v in m[r * 32:(r + 1) * 32]))
        lines.append("\t.balign 4")
        open(path, "w").write("\n".join(lines) + "\n")
        print("wrote", path)
    if "--preview" in sys.argv:
        i = sys.argv.index("--preview")
        preview(c, line, objs, sys.argv[i + 2], sys.argv[i + 1])


if __name__ == "__main__":
    main()

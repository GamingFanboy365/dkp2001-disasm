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
    for order, (wp, side, dist) in enumerate(c.PYLONS):
        off = dist if side == "L" else -dist
        px, pz, _, f, l = at(wp, off)
        # pass ray: from the pylon towards the line
        ax, az = -l[0] * (1 if side == "L" else -1), -l[1] * (1 if side == "L" else -1)
        a_deg = math.degrees(math.atan2(ax, az))
        # strike ray: the direction no racer's bearing comes near while this pylon is live
        live = live_range(c, line, marks, order)
        b_deg, margin = strike_ray(paths, live, px, pz, a_deg)
        # flip byte: 0 when the pass ray points to the racer's left
        left = (ax * l[0] + az * l[1]) > 0
        objs.append((T_PYLON, px, 0, pz, [deg_byte(a_deg), order, deg_byte(b_deg), 0 if left else 1]))
        PYLON_INFO.append((order, px, pz, a_deg, b_deg, margin, live))
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
    # every racer path must pass each pylon (cross its pass ray) and never strike it while live
    paths = racer_paths(c, line)
    for order, px, pz, a, b, margin, live in PYLON_INFO:
        if margin < 20:
            problems.append(f"pylon {order}: racers' bearings come within {margin:.0f} degrees of its strike ray")
        for k, path in enumerate(paths):
            pts = [(x, z) for i, x, z in path if in_live(i, live)]
            passes, strikes = crossings(px, pz, a, pts), crossings(px, pz, b, pts)
            if strikes:
                problems.append(f"pylon {order}: path {k} strikes it at {strikes[0][0]:.0f},{strikes[0][1]:.0f}")
            if not passes:
                problems.append(f"pylon {order}: path {k} never passes it")
            elif math.dist(passes[0], (px, pz)) > 160:
                problems.append(f"pylon {order}: path {k} passes it early, at {passes[0][0]:.0f},{passes[0][1]:.0f}")
    # pylon 0 keeps last lap's bearing when a lap starts (the game doesn't reset it), so a
    # racer at the hoop must not look like it crossed a ray
    if PYLON_INFO:
        order, px, pz, a, b, margin, live = PYLON_INFO[0]
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


def emit(c, line, objs, path):
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
    out.append("\t.balign 4")
    open(path, "w").write("\n".join(out) + "\n")


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
    print(f"{c.NAME}: {len(objs)} objects, {len(line)} route points, lap {length:.0f} units")
    if "--preview" in sys.argv:
        i = sys.argv.index("--preview")
        preview(c, line, objs, sys.argv[i + 2], sys.argv[i + 1])


if __name__ == "__main__":
    main()

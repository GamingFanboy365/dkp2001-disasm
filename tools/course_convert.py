#!/usr/bin/env python3
"""Updates build: turn one of Rare's finished races from pylons to walls.

    python3 tools/course_convert.py updates/courses/rare/beach_00.py OUTDIR

Reads the course's object list and AI network from assets/ (extracted from your own
ROM: nothing of Rare's is in this repository) and writes, for the build:
  OUTDIR/NAME_obj.bin    Rare's object list with every pylon taken out and hidden
                         checkpoints added in their place (Rare's own records are kept
                         byte for byte; only the entry table is new)
  OUTDIR/NAME_walls.bin  the track's wall grid (updates/code/walls.s), from Rare's AI
                         route 0 and the description's TRACK_HALF_WIDTH
The checkpoints are the hidden kind Temple Tangle has (see tools/course_build.py):
out of sight above the ground at the edge of the map, one at the point of Rare's racing
line nearest each of their pylons, in Rare's order, each on whichever side passes the
builder's checks against all of Rare's AI routes. `--check` prints those checks.
"""
import importlib.util
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import course_build as cb  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PYLON_TYPES = range(52, 57)


def read_objects(path):
    b = open(path, "rb").read()
    ents, i = [], 0
    while True:
        off, x, y, z = struct.unpack_from("<4H", b, i)
        if off == 0:
            break
        ents.append((off, x, y, z, struct.unpack_from("<H", b, off)[0]))
        i += 8
    return b, ents


def read_network(path):
    b = open(path, "rb").read()
    n = struct.unpack_from("<H", b, 0)[0]
    routes = []
    for r in range(n):
        o = struct.unpack_from("<H", b, 2 + 2 * r)[0]
        cnt = struct.unpack_from("<H", b, o)[0]
        routes.append([struct.unpack_from("<4h", b, o + 2 + 8 * i) for i in range(cnt)])
    return routes


class Course:
    """What course_build's checks and wall grid need, from Rare's data."""


def convert(desc, check=False):
    spec = importlib.util.spec_from_file_location("course", desc)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    objb, ents = read_objects(os.path.join(ROOT, "assets", "objects", f"obj_{d.NAME}.bin"))
    pylons = sorted((e for e in ents if e[4] in PYLON_TYPES), key=lambda e: objb[e[0] + 3])
    net = None
    if getattr(d, "LINE_FROM_PYLONS", False):
        # Rare's AI route doesn't follow the course: draw the racing line from the start
        # hoop past each pylon in Rare's order, PASS_DISTANCE out on its pass side, and
        # make new AI routes along it
        hoop = next(e for e in ents if e[4] == 5)
        wps = [(hoop[1], hoop[3], 10)]
        for off, x, y, z, t in pylons:
            a = math.radians((128 - objb[off + 2]) % 256 / 256 * 360)
            wps.append((x + math.sin(a) * d.PASS_DISTANCE, z + math.cos(a) * d.PASS_DISTANCE, 10))
        line, _ = cb.catmull_loop(wps, 95)
        racing = []
        for off_ in (0, 8, -8, 16, -16):
            pts = []
            for i in range(len(line)):
                (x, z, y), f, l = cb.frame(line, i)
                pts.append((1, round(x + l[0] * off_), round(y), round(z + l[1] * off_)))
            racing.append(pts)
        net = bytearray(struct.pack("<H", len(racing)))
        offs = []
        body = bytearray()
        start = 2 + 2 * len(racing)
        for r in racing:
            offs.append(start + len(body))
            body += struct.pack("<H", len(r)) + b"".join(struct.pack("<4h", *p) for p in r)
            body += struct.pack("<4h", *r[0])     # ai_steer reads one point past the end
        net += b"".join(struct.pack("<H", o) for o in offs) + body
    else:
        routes = read_network(os.path.join(ROOT, "assets", "ai_networks", f"{d.NAME}.bin"))
        racing = [r for r in routes if len(r) == len(routes[0])][:5]   # not the camera path
        line = [(p[1], p[3], p[2]) for p in racing[0]]                # (x, z, y)

    c = Course()
    c.TRACK_HALF_WIDTH = d.TRACK_HALF_WIDTH
    c.BOUNDS = getattr(d, "BOUNDS", (24, 24, 1000, 1000))
    c.ROUTE_OFFSETS = (0,)
    c.SPACING = 100
    # checkpoints at the route point nearest each of Rare's pylons, in their order
    wps = []
    for off, x, y, z, t in pylons:
        i = min(range(len(line)), key=lambda k: math.dist((x, z), line[k][:2]))
        wps.append(i)
    c.PYLONS = [(i, None, 0) for i in wps]
    wps_ = wps
    marks = list(range(len(line)))

    # the racers' paths: every AI route (and the line pushed wider), with the run-up
    def paths():
        out = []
        for r in racing:
            pts = [(p[1], p[3]) for p in r]
            (hx, hz, _), f, l = cb.frame(line, 0)
            dense = [(-1, hx - f[0] * k, hz - f[1] * k) for k in range(cb.RUNUP, 0, -10)]
            for i in range(len(pts)):
                (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % len(pts)]
                for k in range(8):
                    dense.append((i, x0 + (x1 - x0) * k / 8, z0 + (z1 - z0) * k / 8))
            out.append(dense)
        return out
    racer = paths()

    def try_side(order, wp, side):
        lx, lz, _ = line[wp]
        _, f, l = cb.frame(line, wp)
        compass = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
        sx, sz = compass.get(side) or ((l[0], l[1]) if side == "L" else (-l[0], -l[1]))
        x0, z0, x1, z1 = c.BOUNDS
        ts = [(x0 - lx) / sx if sx < 0 else (x1 - lx) / sx if sx > 0 else 1e9,
              (z0 - lz) / sz if sz < 0 else (z1 - lz) / sz if sz > 0 else 1e9]
        t = min(ts) + 16
        px, pz = lx + sx * t, lz + sz * t
        m = math.hypot(lx - px, lz - pz)
        a = math.degrees(math.atan2((lx - px) / m, (lz - pz) / m))
        lo = wps[order - 1] if order else -1
        live = (lo, wp + 3)
        b, margin = cb.strike_ray(racer, live, px, pz, a)
        bad = 0 if margin >= 20 else 1
        for path in racer:
            pts = [(x, z) for i, x, z in path if cb.in_live(i, live)]
            ps, ss = cb.crossings(px, pz, a, pts), cb.crossings(px, pz, b, pts)
            if ss or not ps or math.dist(ps[0], (lx, lz)) > 120:
                bad += 1
        return bad, (px, pz, a, b, side)

    checkpoints, report = [], []
    for order, wp in enumerate(wps):
        best = min((try_side(order, wp, s) + (s,) for s in ("L", "R", "N", "S", "E", "W")), key=lambda r: r[0])
        bad, (px, pz, a, b, side), _ = best
        report.append(f"checkpoint {order} at route point {wp}: {side}, {bad} problem(s)")
        checkpoints.append((px, pz, a, b))

    # the new object list: our entry table, then Rare's whole list (its records keep their
    # bytes), then our checkpoint records
    keep = [e for e in ents if e[4] not in PYLON_TYPES]
    n = len(keep) + len(checkpoints) + 1
    table = bytearray()
    base = 8 * n
    for off, x, y, z, t in keep:
        table += struct.pack("<4H", base + off, x, y, z)
    if len(objb) % 2:
        objb += b"\0"                      # keep our records hword-aligned
    recs = bytearray()
    rec_base = base + len(objb)
    for k, (px, pz, a, b) in enumerate(checkpoints):
        table += struct.pack("<4H", rec_base + len(recs), round(px), 2000, round(pz))
        recs += struct.pack("<H4B", 52, cb.deg_byte(a), k, cb.deg_byte(b), 0)
    table += bytes(8)
    out = bytes(table) + objb + bytes(recs)
    walls = cb.wall_grid(c, line)
    # with new routes, check them against Rare's own pylons too (the fixes build keeps those)
    if net is not None:
        prev = -1
        for k, (off, x, y, z, t) in enumerate(pylons):
            a = (128 - objb[off + 2]) % 256 / 256 * 360
            b = (128 - objb[off + 4]) % 256 / 256 * 360
            for n_, path in enumerate(racer):
                pts = [(px_, pz_) for i, px_, pz_ in path if cb.in_live(i, (prev, wps_[k] + 3))]
                if cb.crossings(x, z, b, pts) or not cb.crossings(x, z, a, pts):
                    report.append(f"Rare's pylon {k}: route {n_} strikes or misses it")
            prev = wps_[k]
    return d, out, walls, report, net


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    d, objs, walls, report, net = convert(sys.argv[1])
    os.makedirs(sys.argv[2], exist_ok=True)
    if net is not None:
        open(os.path.join(sys.argv[2], f"{d.NAME}_net.bin"), "wb").write(net)
    open(os.path.join(sys.argv[2], f"{d.NAME}_obj.bin"), "wb").write(objs)
    open(os.path.join(sys.argv[2], f"{d.NAME}_walls.bin"), "wb").write(walls)
    if "--check" in sys.argv:
        print("\n".join(report))


if __name__ == "__main__":
    main()

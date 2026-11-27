#!/usr/bin/env python3
"""Course audit: what each of the 41 courses contains, read from your ROM.

    python3 tools/course_audit.py build/dkp.gba [--objects LEVEL]

For each course (levels 1-41, `tab_levels`) it lists the object list (`obj_*`, read by
`obj_gen`): objects counted by class, start positions, start hoops, pylons, and the AI
network (`__net_*`): its route count and points per route.

Object list format (obj_gen, object.c:335-350): 8-byte entries
  +0 hword  offset of the object's record, from the start of the list (0 ends the list)
  +2 hword  x, +4 y, +6 z, in whole units (the game shifts them left 8)
The record starts with an hword object type (1..99); the object's +76 points just past it,
at its type-specific data. The type picks a class through tab_types (4 bytes per type, hword
class) and tab_classes (16 bytes per class: init, act, react, ...), named here by the init
function.
"""
import os
import struct
import sys
from collections import Counter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BASE = 0x08000000


def symbols():
    by_name, by_addr = {}, {}
    for line in open(os.path.join(ROOT, "maps", "symbols.txt")):
        p = line.split()
        if len(p) >= 3:
            a = int(p[0], 16)
            by_name.setdefault(p[-1], a)
            if not p[-1].startswith((".", "$", "L_")):
                by_addr.setdefault(a, p[-1])
    return by_name, by_addr


SYM, ADDR = symbols()


class Rom:
    def __init__(self, path):
        self.b = open(path, "rb").read()

    def u16(self, a):
        return struct.unpack_from("<H", self.b, a - BASE)[0]

    def s16(self, a):
        return struct.unpack_from("<h", self.b, a - BASE)[0]

    def u32(self, a):
        return struct.unpack_from("<I", self.b, a - BASE)[0]


def class_name(rom, typ):
    cls = rom.u16(SYM["tab_types"] + 4 * typ)
    init = rom.u32(SYM["tab_classes"] + 16 * cls)
    name = ADDR.get(init & ~1, f"class{cls}") if init else f"type{typ}(no init)"
    return name[5:] if name.startswith("init_") else name


def objects(rom, lst):
    out, a = [], lst
    while True:
        off = rom.u16(a)
        if off == 0:
            return out
        rec = lst + off
        typ = rom.u16(rec)
        out.append((typ, class_name(rom, typ), rom.u16(a + 2), rom.u16(a + 4), rom.u16(a + 6), rec))
        a += 8


def network(rom, net):
    n = rom.u16(net)
    return [rom.u16(net + rom.u16(net + 2 + 2 * i)) for i in range(n)]


def level_names(rom):
    """select_strings: course names by level (pointers to C strings)."""
    names = {}
    base = SYM.get("select_strings")
    if base is None:
        return names
    for lv in range(1, 42):
        p = rom.u32(base + 4 * (lv - 1))
        if BASE <= p < BASE + len(rom.b):
            s = rom.b[p - BASE:rom.b.index(b"\0", p - BASE)]
            names[lv] = s.decode("latin-1")
    return names


def slots(rom):
    """select_indices (int[12][6], level - 1): rows 4-8 Racing worlds 1-5, rows 9-11 stories 1-3,
    rows 2-3 the Dog Fight and Battle lists. Returns level -> slot codes like R3-2 or S1-4."""
    out = {}
    si = SYM["select_indices"]
    for row in range(2, 12):
        tag = {2: "D", 3: "B"}.get(row) or (f"R{row - 3}" if row <= 8 else f"S{row - 8}")
        for k in range(6):
            v = rom.u32(si + 24 * row + 4 * k)
            if v or k == 0:
                out.setdefault(v + 1, []).append(f"{tag}-{k + 1}" if row <= 3 else f"{tag}-{k + 1}")
    return out


def metatiles(rom, lv):
    """Distinct metatiles in the course's 32x32 level map. The placeholder maps (a plain fill
    stamped with the course's slot code, e.g. "R3-2") use 26-188; drawn maps use 269-1008."""
    m = rom.u32(SYM["tab_levels"] + 36 * lv + 16)
    return len({rom.u16(m + 4 + 2 * i) for i in range(1024)})


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rom = Rom(sys.argv[1])
    names = level_names(rom)
    tl = SYM["tab_levels"]
    if "--objects" in sys.argv:
        lv = int(sys.argv[sys.argv.index("--objects") + 1])
        lst = rom.u32(tl + 36 * lv + 28)
        print(f"level {lv} {ADDR.get(lst, hex(lst))}")
        for typ, cls, x, y, z, rec in objects(rom, lst):
            data = rom.b[rec + 2 - BASE:rec + 18 - BASE].hex(" ")
            print(f"  type {typ:2d} {cls:22s} at ({x:5d},{y:5d},{z:5d})  data {data}")
        return
    sl = slots(rom)
    print(f"{'lv':>2} {'name':20s} {'slot':9s} {'map':10s} starts hoops pylons  routes (points)  other objects")
    for lv in range(1, 42):
        lst, net = rom.u32(tl + 36 * lv + 28), rom.u32(tl + 36 * lv + 32)
        objs = objects(rom, lst)
        c = Counter(cls for _, cls, *_ in objs)
        starts = c.pop("start_pos", 0)
        hoops = c.pop("starthoop", 0)
        pylons = c.pop("pylon", 0)
        routes = network(rom, net)
        other = ", ".join(f"{k} {v}" for k, v in sorted(c.items()))
        mt = metatiles(rom, lv)
        print(f"{lv:2d} {names.get(lv, '')[:20]:20s} {','.join(sl.get(lv, ['-'])):9s} {('stub ' if mt < 200 else 'drawn') + f'{mt:5d}':10s}"
              f" {starts:6d} {hoops:5d} {pylons:6d}  {len(routes)} {routes}  {other}")


if __name__ == "__main__":
    main()

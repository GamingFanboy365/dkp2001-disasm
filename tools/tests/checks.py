#!/usr/bin/env python3
"""Play-through checks for the original and patched ROMs, in headless mGBA.

    python3 tools/tests/checks.py CHECK ROM [ROM ...]

CHECK is one of:
  tracks     every debug-menu track, flown for ~40 s, plus a front-end tour
  frontend   the 20 front-end race starts (5 modes x 4 entries)
  clock      the 32 Clock Race courses (every world's and story's 4 courses)
  finish     every debug-menu track with the computer flying the player's plane,
             reporting which complete a race (courses without routes won't)
  picks      character select: each of the six picks, and who flies the race
  stories    the three stories: who flies each
  dogfight   Dog Fights and K. Rool's Gold fights (updates build): lives and endings
  all        tracks, frontend, clock, picks, stories

Each run reports emulator faults (illegal instructions, unmapped memory). The
boot-time stdio writes to ROM are harmless and not reported. Patched ROMs (any
ROM other than the original, sha1 6a76def6...) boot into the logos, so their
scripts press L+R on the Nintendo logo first (opening the debug menu, where the
original boots) and run everything else 100 frames later.

Needs tools/romtest/romtest built (see tools/romtest/README.md).
"""
import bisect
import concurrent.futures as cf
import hashlib
import os
import re
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ROMTEST = os.path.join(ROOT, "tools", "romtest", "romtest")
ORIGINAL_SHA1 = "6a76def610829ac1502afb58740e38b5e6926b3d"
OFFSET = 100                    # patched builds: frames added after L+R on the logo
CHARS = ["Cranky", "Diddy", "Krunch", "K. Rool", "Dixie", "Kong", "Rusty"]   # Rusty: updates build
EWRAM, IWRAM = 0x02000000, 0x03000000

# RAM addresses (maps/symbols.txt)
GAME_LEVEL, PLAYERS, MONITOR, SYS_MODE = 0x02002A84, 0x02003B04, 0x02003B18, 0x030033A4


def load_symbols():
    syms, funcs = {}, []
    for line in open(os.path.join(ROOT, "maps", "symbols.txt")):
        p = line.split()
        if len(p) >= 3:
            syms.setdefault(p[-1], int(p[0], 16))
            if p[-2] in "tT" and not p[-1].startswith(("L_", "_", "$", ".")):
                funcs.append((int(p[0], 16), p[-1]))
    funcs.sort()
    return syms, funcs


SYMS, FUNCS = load_symbols()
FUNC_ADDRS = [a for a, _ in FUNCS]


def func_name(pc):
    pc = (pc & ~1) - 4
    i = bisect.bisect_right(FUNC_ADDRS, pc) - 1
    return f"{FUNCS[i][1]}+{pc - FUNCS[i][0]:#x}" if i >= 0 else hex(pc)


def course_names(rom):
    """Course names by level, from select_strings (char*, level - 1) in the ROM."""
    b = open(rom, "rb").read()
    table = SYMS["select_strings"] - 0x08000000
    base = os.path.join(ROOT, "baserom.gba")
    if os.path.exists(base):                 # the table and its strings may have moved in a
        bb = open(base, "rb").read()         # patched build: find level 2's name, then the
        p = struct.unpack_from("<I", bb, table + 4)[0] - 0x08000000     # entry pointing to it
        name = bb[p:bb.index(b"\0", p) + 1]
        q = struct.unpack_from("<I", b, table + 4)[0] - 0x08000000
        at = -1 if 0 <= q < len(b) and b[q:q + len(name)] == name else b.find(name)
        while at >= 0:
            i = b.find(struct.pack("<I", 0x08000000 + at))
            if i >= 4 and i % 4 == 0:
                table = i - 4
                break
            at = b.find(name, at + 1)
    out = {}
    for lv in range(1, 42):
        p = struct.unpack_from("<I", b, table + 4 * (lv - 1))[0] - 0x08000000
        out[lv] = b[p:b.index(b"\0", p)].decode("latin-1").title()
    return out


def is_patched(rom):
    return hashlib.sha1(open(rom, "rb").read()).hexdigest() != ORIGINAL_SHA1


def play(rom, frames, script, every=0, poke=None, ram=False, shots=None):
    """Run the ROM; returns (faults, hashes, ram bytes or None)."""
    script = list(script)
    if is_patched(rom):
        script = ["20:L:20", "25:R:15"] + [
            f"{int(s.split(':', 1)[0]) + OFFSET}:{s.split(':', 1)[1]}" for s in script]
        frames += OFFSET
        if poke:
            poke = ",".join(f"{int(p.split(':', 1)[0]) + OFFSET}:{p.split(':', 1)[1]}"
                            for p in poke.split(","))
    env = dict(os.environ, PROBLEMS="1")
    if poke:
        env["POKE"] = poke
    ramfile = None
    if ram:
        fd, ramfile = tempfile.mkstemp(suffix=".bin")
        os.close(fd)
        env["RAM_OUT"] = ramfile
    args = [ROMTEST, rom, str(frames), str(every)]
    if shots:
        args += ["--ppm", shots]
    out = subprocess.run(args + script, capture_output=True, text=True, env=env).stdout
    faults, hashes = [], []
    for line in out.splitlines():
        m = re.match(r"problem pc=([0-9a-f]+) frame=(\d+) count=(\d+) (.*)", line)
        if m:
            f = int(m.group(2))
            if f > 3 and "std+" not in func_name(int(m.group(1), 16)):
                faults.append(f"{func_name(int(m.group(1), 16))} frame {f - (OFFSET if is_patched(rom) else 0)}"
                              f" x{m.group(3)} {m.group(4)[:44]}")
        elif re.match(r"\s*\d+ [0-9a-f]{16}$", line):
            hashes.append(line.split()[1])
    data = None
    if ramfile:
        data = open(ramfile, "rb").read()
        os.remove(ramfile)
    return faults, hashes, data


def rd(data, addr, fmt="<I"):
    off = addr - EWRAM if addr < IWRAM else 0x40000 + addr - IWRAM
    return struct.unpack_from(fmt, data, off)[0]


def track_script(k):
    """Debug menu: track k is reached by pressing A k times, then START."""
    st = 60 + 12 * k + 30
    return st, [f"{40 + 12 * i}:A" for i in range(1, k + 1)] + [f"{st}:START"]


FRONTEND = ["200:START", "800:START", "860:DOWN", "900:DOWN", "960:A"]  # race, pause, QUIT


def check_tracks(rom):
    jobs = {}
    for k in range(40):
        st, t = track_script(k)
        jobs[f"track {k:2d}"] = (st + 2400, t + [f"{st + 300}:A:2000", f"{st + 500}:LEFT:60",
                                                 f"{st + 800}:RIGHT:90", f"{st + 1000}:B:10",
                                                 f"{st + 1100}:UP:80", f"{st + 1300}:R:20"])
    t = FRONTEND + [f"{1150 + i * 90}:RIGHT" for i in range(8)] + [f"{1900 + i * 90}:LEFT" for i in range(8)]
    t += ["2700:A"] + [f"{2900 + i * 80}:RIGHT" for i in range(10)] + ["3800:A"]
    t += [f"{4000 + i * 60}:DOWN" for i in range(5)] + ["4400:A", "4700:A"]
    jobs["front-end tour"] = (5400, t)
    return run_jobs(rom, jobs, lambda r: "")


def mode_script(mode, item):
    t = FRONTEND + [f"{1240 + 90 * i}:RIGHT" for i in range(mode)] + ["1800:A", "2100:A"]
    if mode == 1:   # Stories has no character select; its list needs slower presses
        t = FRONTEND + ["1240:RIGHT", "1800:A"] + [f"{1850 + 100 * i}:DOWN" for i in range(1, item + 1)] + ["2200:A"]
    else:
        t += [f"{2300 + 60 * i}:DOWN" for i in range(item)] + ["2600:A"]
    return t


def check_frontend(rom):
    jobs = {f"mode {m} item {j}": (5400, mode_script(m, j) + ["3200:A", "3500:A:2500", "3700:LEFT:100"])
            for m in range(5) for j in range(4)}
    return run_jobs(rom, jobs, lambda r: f"level {rd(r, GAME_LEVEL, '<i')}")


def check_clock(rom):
    jobs = {}
    for k in range(32):
        a = 2400 + 60 * k
        t = FRONTEND + [f"{1240 + 90 * i}:RIGHT" for i in range(4)] + ["1800:A", "2100:A"]
        t += [f"{2300 + 60 * i}:DOWN" for i in range(k)]
        t += [f"{a}:A", f"{a + 600}:A", f"{a + 900}:A:2000", f"{a + 1500}:B:6"]
        jobs[f"clock {k:2d}"] = (a + 3000, t)
    return run_jobs(rom, jobs, lambda r: f"level {rd(r, GAME_LEVEL, '<i')}")


def check_finish(rom):
    """A finished race moves on (to the title, or into a new race with the laps reset), so
    each track is sampled at six points and the most laps seen is reported."""
    def state(r):
        mon = rd(r, MONITOR) - EWRAM
        in_title = (SYMS["title"] | 1) == rd(r, SYS_MODE)
        return in_title, (r[mon + 86] if 0 < mon < 0x40000 and not in_title else 0)

    def one(k):
        st, t = track_script(k)
        poke = f"{st + 60}:03003398|40"
        faults, laps, finished, level = [], 0, False, 0
        for f in (st + 3000, st + 4500, st + 6000, st + 8000, st + 10000, st + 12000):
            fl, _, data = play(rom, f, t, poke=poke, ram=True)
            faults = faults or fl
            level = level or rd(data, GAME_LEVEL, "<i")
            in_title, n = state(data)
            laps = max(laps, n)
            finished |= in_title or n >= 3
        return k, faults, laps, finished, level

    names = course_names(rom)
    bad = 0
    with cf.ThreadPoolExecutor(max(1, os.cpu_count() or 4)) as ex:
        for k, faults, laps, finished, level in ex.map(one, range(40)):
            bad += bool(faults)
            flag = "FAULTS" if faults else "ok"
            print(f"  track {k:2d} {names.get(level, level)!s:22.22} {flag:7s} {'finished' if finished else f'most laps seen {laps}'}"
                  + (f"  {faults[:2]}" if faults else ""))
    return bad


def check_picks(rom):
    jobs = {}                                # RIGHT presses from the start (Diddy): Krash, K. Rool,
    for n in range(7):                       # Dixie, Cranky, then Kong (or Rusty, then Kong, in
        t = FRONTEND + ["1800:A"] + [f"{2100 + k * 100}:RIGHT" for k in range(n)] + ["2900:A", "3300:A", "3700:A", "4100:A"]
        jobs[f"RIGHT x{n}"] = (5200, t)      # the updates build, where his slot sits between)
    return run_jobs(rom, jobs, lambda r: f"flies as {CHARS[rd(r, rd(r, PLAYERS) + 130, '<H')]}")


def check_stories(rom):
    jobs = {}
    for j, name in enumerate(["King of Kongs", "Back to the Light", "K. Rool's Gold"]):
        t = mode_script(1, j) + [f"{2600 + k * 120}:A" for k in range(46)]
        jobs[name] = (9000 if j == 2 else 3500, t)
    return run_jobs(rom, jobs, lambda r: f"level {rd(r, GAME_LEVEL, '<i')}, flies as {CHARS[rd(r, rd(r, PLAYERS) + 130, '<H')]}")


def check_dogfight(rom):
    base = FRONTEND + ["1240:RIGHT", "1330:RIGHT", "1800:A", "2100:A"]
    jobs = {}
    for j in range(4):
        t = base + [f"{2300 + 60 * i}:DOWN" for i in range(j)] + ["2600:A", "3200:A", "3500:A:12000"]
        t += [f"{3800 + k * 150}:B:4" for k in range(80)]
        t += [f"{3900 + k * 600}:LEFT:50" for k in range(20)] + [f"{4200 + k * 600}:RIGHT:30" for k in range(20)]
        jobs[f"arena {j}"] = (15000, t)

    def detail(r):
        mon = rd(r, MONITOR)
        state = rd(r, mon + 80)
        state = {3: "fighting", 4: "won (FINISH)", 5: "shot down (RETIRE)"}.get(state, f"state {state}")
        return f"{state}, hits taken {list(r[mon - EWRAM + 94:mon - EWRAM + 98])}"
    return run_jobs(rom, jobs, detail)


def run_jobs(rom, jobs, detail):
    def one(item):
        name, job = item
        frames, script = job[0], job[1]
        poke = job[2] if len(job) > 2 else None
        faults, hashes, data = play(rom, frames, script, every=500, poke=poke, ram=True)
        frozen = len(hashes) >= 4 and len(set(hashes[-4:])) == 1
        return name, faults, frozen, detail(data)
    bad = 0
    with cf.ThreadPoolExecutor(max(1, os.cpu_count() or 4)) as ex:
        for name, faults, frozen, info in ex.map(one, jobs.items()):
            flag = "FAULTS" if faults else ("frozen" if frozen else "ok")
            bad += bool(faults)
            print(f"  {name:20s} {flag:7s} {info}" + (f"  {faults[:2]}" if faults else ""))
    return bad


CHECKS = {"tracks": check_tracks, "frontend": check_frontend, "clock": check_clock,
          "finish": check_finish, "picks": check_picks, "stories": check_stories,
          "dogfight": check_dogfight}


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in list(CHECKS) + ["all"]:
        sys.exit(__doc__)
    names = ["tracks", "frontend", "clock", "picks", "stories"] if sys.argv[1] == "all" else [sys.argv[1]]
    bad = 0
    for rom in sys.argv[2:]:
        for n in names:
            print(f"{n}: {rom}{' (patched: L+R to the debug menu first)' if is_patched(rom) else ''}")
            bad += CHECKS[n](rom)
    print("faults found" if bad else "no faults")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

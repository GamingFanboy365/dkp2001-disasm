#!/usr/bin/env python3
"""Render the game's graphics to viewable PNGs (one-way, for browsing).

    python3 tools/export_preview.py baserom.gba maps/symbols.txt OUTDIR

Writes OUTDIR/
  frontend_sprites/<name>/<name>_NN.png   title/menu sprite frames, composed from their OAM pieces
  ingame_sprites/<name>/<level>.png        every frame of every in-game sprite, side by side
  backgrounds/<name>.png                   menu/title backgrounds composed from their tilemaps
  palettes/<name>.png                      palette swatches
  sound/<group>/<sample>.wav               copied from assets/ if present

The editable sources are under assets/ (tile sheets, .pal, .wav); this tool
only shows what they look like in the game.
"""
import os
import re
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfx  # noqa: E402

OBJ_SIZES = {0: [(8, 8), (16, 16), (32, 32), (64, 64)],
             1: [(16, 8), (32, 8), (32, 16), (64, 32)],
             2: [(8, 16), (8, 32), (16, 32), (32, 64)],
             3: [(8, 8)] * 4}
GREY = [(i * 17, i * 17, i * 17) for i in range(16)]


class Rom:
    def __init__(self, path, symbols):
        self.d = open(path, "rb").read()
        self.sym = {}
        self.addr = {}
        for line in open(symbols):
            p = line.split()
            if len(p) >= 3 and p[-2] not in "aAUw" and not p[-1].startswith(("$", ".")):
                a = int(p[0], 16)
                if 0x08000000 <= a < 0x08000000 + len(self.d):
                    self.sym.setdefault(p[-1], a)
                    self.addr.setdefault(a, p[-1])
        self.sorted = sorted(self.addr)

    def ok(self, a, n=1):
        return 0x08000000 <= a and a + n <= 0x08000000 + len(self.d)

    def b(self, a, n):
        return self.d[a - 0x08000000:a - 0x08000000 + n]

    def u8(self, a):
        return self.d[a - 0x08000000]

    def u16(self, a):
        return struct.unpack_from("<H", self.d, a - 0x08000000)[0]

    def s16(self, a):
        return struct.unpack_from("<h", self.d, a - 0x08000000)[0]

    def s8(self, a):
        return struct.unpack_from("<b", self.d, a - 0x08000000)[0]

    def u32(self, a):
        return struct.unpack_from("<I", self.d, a - 0x08000000)[0]

    def size(self, name):
        import bisect
        a = self.sym[name]
        i = bisect.bisect_right(self.sorted, a)
        return (self.sorted[i] if i < len(self.sorted) else 0x08000000 + len(self.d)) - a

    def palette(self, name):
        if name not in self.sym:
            return None
        return gfx.palette_from_bin(self.b(self.sym[name], min(self.size(name), 512)))


def tile_pixels(data, off, bpp):
    """8x8 indices of the tile at byte offset off."""
    out = []
    for y in range(8):
        row = []
        for x in range(8):
            if bpp == 8:
                row.append(data[off + y * 8 + x] if off + y * 8 + x < len(data) else 0)
            else:
                i = off + y * 4 + x // 2
                v = data[i] if i < len(data) else 0
                row.append((v >> 4) if x & 1 else (v & 15))
        out.append(row)
    return out


class Canvas:
    """Sparse RGBA canvas; index 0 is transparent for sprites."""

    def __init__(self):
        self.px = {}

    def tile(self, x0, y0, pix, pal, transparent=True, hflip=False, vflip=False, bank=0):
        for y in range(8):
            for x in range(8):
                v = pix[7 - y if vflip else y][7 - x if hflip else x]
                if transparent and v == 0:
                    continue
                c = pal[(bank * 16 + v) % len(pal)] if pal else GREY[v % 16]
                self.px[(x0 + x, y0 + y)] = c

    def save(self, path, bg=(255, 0, 255), pad=1):
        if not self.px:
            return False
        xs = [p[0] for p in self.px]
        ys = [p[1] for p in self.px]
        x0, y0 = min(xs) - pad, min(ys) - pad
        w, h = max(xs) - x0 + 1 + pad, max(ys) - y0 + 1 + pad
        rows = [[self.px.get((x + x0, y + y0), bg) for x in range(w)] for y in range(h)]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        gfx.write_png(path, w, h, rows, rgb=True)
        return True


def hstack(canvases, gap=4):
    out = Canvas()
    x = 0
    for c in canvases:
        if not c.px:
            continue
        xs = [p[0] for p in c.px]
        ys = [p[1] for p in c.px]
        mx, my = min(xs), min(ys)
        for (px, py), col in c.px.items():
            out.px[(px - mx + x, py - my)] = col
        x += max(xs) - mx + 1 + gap
    return out


def rle_tiles(rom, block):
    """Decode an in-game sprite tile block (see spr_update_vram in sprite_ram.c)."""
    ntiles = rom.u16(block)
    out = bytearray()
    p = block + 4
    c = rom.u16(block + 2)
    guard = 0
    while c and guard < 100000:
        n = (c & 0x7F) + 1
        if c & 0x80:
            out += rom.b(p, n * 2)
            p += n * 2
        else:
            v = c >> 8
            out += bytes((v, v)) * n
        c = rom.u16(p)
        p += 2
        guard += 1
    return bytes(out), ntiles


def pick_palette(rom, name):
    pals = [n[6:] for n in rom.sym if n.startswith("__pal_")]
    base = re.sub(r"_0[12]$", "", name)
    if base in pals:
        return rom.palette("__pal_" + base)
    best = max((p for p in pals if base.startswith(p) or p.startswith(base)), key=len, default=None)
    if best:
        return rom.palette("__pal_" + best)
    if base.startswith("hud"):
        return rom.palette("__pal_hud_icons")
    return None


def ingame_sprites(rom, out):
    n = 0
    for name in sorted(s for s in rom.sym if s.startswith("__spr_")):
        L = rom.sym[name]
        try:
            chartab = L + rom.u16(L)
            first = rom.u16(L + 14)
            nframes = (first - 14) // 2
            if not 0 < nframes <= 256:
                continue
            pal = pick_palette(rom, name[6:])
            frames = []
            for f in range(nframes):
                pt = L + rom.u16(L + 14 + 2 * f)
                count = rom.u16(pt)
                block = chartab + rom.u16(chartab + 2 * f) * 16
                tiles, _ = rle_tiles(rom, block)
                c = Canvas()
                for k in range(min(count, 64)):
                    q = pt + 2 + 6 * k
                    a0, a1, t = rom.u16(q), rom.u16(q + 2), rom.u16(q + 4)
                    y, x = rom.s8(q), rom.s8(q + 2)
                    w, h = OBJ_SIZES[a0 >> 14][a1 >> 14]
                    hf, vf = bool(a1 & 0x1000), bool(a1 & 0x2000)
                    for ty in range(h // 8):
                        for tx in range(w // 8):
                            idx = t + ty * (w // 8) + tx
                            dx = (w // 8 - 1 - tx) if hf else tx
                            dy = (h // 8 - 1 - ty) if vf else ty
                            c.tile(x + dx * 8, y + dy * 8, tile_pixels(tiles, idx * 32, 4), pal, hflip=hf, vflip=vf)
                frames.append(c)
            base = re.sub(r"_0[12]$", "", name[6:])
            if hstack(frames).save(os.path.join(out, "ingame_sprites", base, name[6:] + ".png")):
                n += 1
        except (IndexError, KeyError, struct.error):
            continue
    return n


def frontend_sprites(rom, out):
    chars = {a for n, a in rom.sym.items() if "_char" in n}
    infos = {a for n, a in rom.sym.items() if "_info" in n}
    seen, n = set(), 0
    for a in range(0x08017730, 0x084D8644 - 16, 4):
        c, i = rom.u32(a), rom.u32(a + 8)
        if c not in chars or i not in infos or (c, i) in seen:
            continue
        count = rom.u16(a + 6)
        if not 1 <= count <= 64:
            continue
        seen.add((c, i))
        cname = rom.addr[c]
        base = re.sub(r"_char(_\d+)?$", "", cname)
        pal = rom.palette(base + "_plt") or rom.palette("__pal_" + base)
        data = rom.b(c, rom.size(cname))
        canvas = Canvas()
        x = y = tile = 0
        for k in range(count):
            q = i + 12 * k
            y += rom.s16(q)
            x += rom.s16(q + 2)
            b4, b5 = rom.u8(q + 4), rom.u8(q + 5)
            bpp = 8 if b4 & 0x20 else 4
            w, h = OBJ_SIZES[b4 >> 6][b5 >> 6]
            hf, vf = bool(b5 & 0x10), bool(b5 & 0x20)
            for ty in range(h // 8):
                for tx in range(w // 8):
                    off = (tile + (ty * (w // 8) + tx) * (bpp // 4)) * 32
                    dx = (w // 8 - 1 - tx) if hf else tx
                    dy = (h // 8 - 1 - ty) if vf else ty
                    canvas.tile(x + dx * 8, y + dy * 8, tile_pixels(data, off, bpp), pal, hflip=hf, vflip=vf)
            tile += rom.u16(q + 6)
        m = re.search(r"_char_(\d+)$", cname)
        idx = int(m.group(1)) if m else 0
        if canvas.save(os.path.join(out, "frontend_sprites", base, f"{base}_{idx:02d}.png")):
            n += 1
    return n


def backgrounds(rom, out):
    n = 0
    for name in sorted(rom.sym):
        if not name.endswith("_chars"):
            continue
        base = name[:-6]
        if base + "_map" not in rom.sym:
            continue
        chars = rom.b(rom.sym[name], rom.size(name))
        count = rom.u32(rom.sym[base + "_num_chars"]) if base + "_num_chars" in rom.sym else 0
        bpp = 8 if count and len(chars) // max(count, 1) >= 64 else 4
        pal = (rom.palette(base + "_plt") or rom.palette("__pal_" + base)
               or rom.palette(re.sub(r"\d+$", "", base) + "_plt"))
        affine = base + "_map_size_x" not in rom.sym and rom.size(base + "_map") == 4096 and bpp == 8
        if affine:  # rotation/scaling background: 64x64 map of 1-byte tile numbers
            ma = rom.sym[base + "_map"]
            c = Canvas()
            for ty in range(64):
                for tx in range(64):
                    t = rom.u8(ma + ty * 64 + tx)
                    c.tile(tx * 8, ty * 8, tile_pixels(chars, t * 64, 8), pal, transparent=True)
            if c.save(os.path.join(out, "backgrounds", base + ".png"), pad=0):
                n += 1
            continue
        if base + "_map_size_x" in rom.sym:
            mw, mh = rom.u16(rom.sym[base + "_map_size_x"]), rom.u16(rom.sym[base + "_map_size_y"])
        else:
            entries = rom.size(base + "_map") // 2
            mw = 32 if entries % 32 == 0 else 30
            mh = min(entries // mw, 32)
        ma = rom.sym[base + "_map"]
        c = Canvas()
        for ty in range(mh):
            for tx in range(mw):
                e = rom.u16(ma + 2 * (ty * mw + tx))
                t = e & 0x3FF
                c.tile(tx * 8, ty * 8, tile_pixels(chars, t * 8 * bpp, bpp), pal, transparent=False,
                       hflip=bool(e & 0x400), vflip=bool(e & 0x800), bank=0 if bpp == 8 else e >> 12)
        if c.save(os.path.join(out, "backgrounds", base + ".png"), pad=0):
            n += 1
    for name in sorted(rom.sym):
        if name.endswith("_image") and rom.size(name) == 240 * 160 * 2:
            os.makedirs(os.path.join(out, "backgrounds"), exist_ok=True)
            gfx.bitmap_to_png(rom.b(rom.sym[name], 240 * 160 * 2), 240, os.path.join(out, "backgrounds", name + ".png"))
            n += 1
    return n


def palettes(rom, out):
    n = 0
    for name in sorted(rom.sym):
        if not (name.startswith("__pal_") or name.endswith("_plt")):
            continue
        pal = rom.palette(name)
        if not pal:
            continue
        cols = 16
        rows = [[pal[min((y // 8) * cols + x // 8, len(pal) - 1)] if (y // 8) * cols + x // 8 < len(pal) else (0, 0, 0)
                 for x in range(cols * 8)] for y in range(((len(pal) + cols - 1) // cols) * 8)]
        os.makedirs(os.path.join(out, "palettes"), exist_ok=True)
        gfx.write_png(os.path.join(out, "palettes", name.lstrip("_") + ".png"), cols * 8, len(rows), rows, rgb=True)
        n += 1
    return n


def main():
    rom = Rom(sys.argv[1], sys.argv[2])
    out = sys.argv[3]
    shutil.rmtree(out, ignore_errors=True)
    print("front-end sprite frames:", frontend_sprites(rom, out))
    print("in-game sprite sheets:", ingame_sprites(rom, out))
    print("backgrounds:", backgrounds(rom, out))
    print("palettes:", palettes(rom, out))
    snd = 0
    for root, _, files in os.walk("assets/sound/samples"):
        for f in files:
            if f.endswith(".wav"):
                dst = os.path.join(out, "sound", os.path.relpath(root, "assets/sound/samples"), f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(os.path.join(root, f), dst)
                snd += 1
    print("sound samples:", snd)


if __name__ == "__main__":
    main()

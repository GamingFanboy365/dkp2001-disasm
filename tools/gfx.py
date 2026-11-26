#!/usr/bin/env python3
"""Asset converters for the build. Python standard library only.

    python3 tools/gfx.py png2bin  in.4bpp.png|in.8bpp.png|in.rgb555.png  out.bin
    python3 tools/gfx.py pal2bin  in.pal  out.bin
    python3 tools/gfx.py wav2bin  in.wav  out.bin

The reverse directions (bin -> png/pal/wav) are used by tools/dkp_split.py when
extracting assets, and are exact: converting back gives the original bytes.

Formats
  *.4bpp.png / *.8bpp.png  GBA tiles (8x8, row-major) laid out as an indexed PNG
                           tile sheet. Pixel values are palette indices; the PNG
                           palette is only there for viewing.
  *.rgb555.png             16-bit bitmap (GBA BGR555) as an RGB PNG.
  *.pal                    JASC-PAL text palette (GBA BGR555 colours).
  *.wav                    8-bit mono PCM; the GBA stores signed samples.
"""
import struct
import sys
import zlib

# ---------------------------------------------------------------- PNG

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(path, width, height, rows, bit_depth=8, palette=None, rgb=False, transparent=None):
    """rows: list of lists of pixel values (indices, or (r, g, b) if rgb).
    transparent: palette index to mark fully transparent (tRNS)."""
    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter: none
        if rgb:
            for r, g, b in row:
                raw += bytes((r, g, b))
        elif bit_depth == 8:
            raw += bytes(row)
        elif bit_depth == 4:
            for x in range(0, width, 2):
                hi = row[x]
                lo = row[x + 1] if x + 1 < width else 0
                raw.append((hi << 4) | lo)
        else:
            raise ValueError(bit_depth)
    ctype = 2 if rgb else 3
    out = PNG_SIG + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8 if rgb else bit_depth, ctype, 0, 0, 0))
    if not rgb:
        pal = list(palette or [(i * 17, i * 17, i * 17) for i in range(16)])
        n = 1 << bit_depth
        pal = (pal + [(0, 0, 0)] * n)[:n]
        out += _chunk(b"PLTE", b"".join(bytes(c) for c in pal))
        if transparent is not None:
            out += _chunk(b"tRNS", bytes(255 if i != transparent else 0 for i in range(transparent + 1)))
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(out)


def read_png(path):
    """Returns (width, height, color_type, bit_depth, rows). Indexed or RGB(A)."""
    data = open(path, "rb").read()
    if data[:8] != PNG_SIG:
        raise ValueError(f"{path}: not a PNG")
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat += body
    w, h, depth, ctype, _, _, interlace = ihdr
    if interlace:
        raise ValueError(f"{path}: interlaced PNGs are not supported")
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = max(1, chans * depth // 8)
    stride = (w * chans * depth + 7) // 8
    raw = zlib.decompress(idat)
    rows, prev = [], bytearray(stride)
    for y in range(h):
        ft = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                line[i] = (line[i] + a) & 0xFF
            elif ft == 2:
                line[i] = (line[i] + b) & 0xFF
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 0xFF
            elif ft == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else b if pb <= pc else c
                line[i] = (line[i] + pr) & 0xFF
        prev = line
        if ctype == 3 or ctype == 0:
            if depth == 8:
                rows.append(list(line))
            else:
                per = 8 // depth
                mask = (1 << depth) - 1
                px = []
                for byte in line:
                    for k in range(per):
                        px.append((byte >> (8 - depth * (k + 1))) & mask)
                rows.append(px[:w])
        else:
            rows.append([tuple(line[x * chans:x * chans + 3]) for x in range(w)])
    return w, h, ctype, depth, rows


# ---------------------------------------------------------------- tiles

def gba_rgb(c):
    """BGR555 -> (r, g, b), 5-bit channels widened so that >> 3 restores them."""
    return tuple((((c >> s) & 31) << 3) | (((c >> s) & 31) >> 2) for s in (0, 5, 10))


def rgb_gba(r, g, b):
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def palette_from_bin(data):
    return [gba_rgb(struct.unpack_from("<H", data, i)[0]) for i in range(0, len(data) - 1, 2)]


def tiles_to_png(data, bpp, path, width_tiles=None, palette=None):
    tile_bytes = 8 * bpp
    n = len(data) // tile_bytes
    if n * tile_bytes != len(data) or n == 0:
        raise ValueError("not a whole number of tiles")
    wt = width_tiles if width_tiles and n % width_tiles == 0 else next(
        w for w in (16, 8, 4, 2, 1) if n % w == 0)
    ht = n // wt
    rows = [[0] * (wt * 8) for _ in range(ht * 8)]
    for t in range(n):
        tx, ty = (t % wt) * 8, (t // wt) * 8
        base = t * tile_bytes
        for y in range(8):
            for x in range(8):
                if bpp == 8:
                    v = data[base + y * 8 + x]
                else:
                    b = data[base + y * 4 + x // 2]
                    v = (b >> 4) if x & 1 else (b & 15)
                rows[ty + y][tx + x] = v
    pal = palette
    if pal is not None and bpp == 4:
        pal = pal[:16]
    write_png(path, wt * 8, ht * 8, rows, bit_depth=bpp, palette=pal)


def png_to_tiles(path, bpp):
    w, h, ctype, depth, rows = read_png(path)
    if ctype not in (0, 3):
        raise ValueError(f"{path}: must be an indexed (palette) PNG, not RGB")
    if w % 8 or h % 8:
        raise ValueError(f"{path}: size must be a multiple of 8")
    out = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            for y in range(8):
                row = rows[ty * 8 + y]
                if bpp == 8:
                    out += bytes(row[tx * 8:tx * 8 + 8])
                else:
                    for x in range(0, 8, 2):
                        lo, hi = row[tx * 8 + x], row[tx * 8 + x + 1]
                        if lo > 15 or hi > 15:
                            raise ValueError(f"{path}: 4bpp image uses colour index > 15")
                        out.append(lo | (hi << 4))
    return bytes(out)


def bitmap_to_png(data, width, path):
    px = [struct.unpack_from("<H", data, i)[0] for i in range(0, len(data), 2)]
    if any(p & 0x8000 for p in px):
        raise ValueError("bit 15 set; not representable")
    h = len(px) // width
    write_png(path, width, h, [[gba_rgb(px[y * width + x]) for x in range(width)] for y in range(h)], rgb=True)


def png_to_bitmap(path):
    w, h, ctype, depth, rows = read_png(path)
    if ctype not in (2, 6):
        raise ValueError(f"{path}: must be an RGB PNG")
    return b"".join(struct.pack("<H", rgb_gba(*p)) for row in rows for p in row)


# ---------------------------------------------------------------- palettes

def pal_to_jasc(data, path):
    cols = palette_from_bin(data)
    with open(path, "w", newline="\r\n") as f:
        f.write(f"JASC-PAL\n0100\n{len(cols)}\n")
        for r, g, b in cols:
            f.write(f"{r} {g} {b}\n")


def jasc_to_pal(path):
    lines = open(path).read().split()
    if lines[0] != "JASC-PAL":
        raise ValueError(f"{path}: not a JASC-PAL file")
    n = int(lines[2])
    vals = list(map(int, lines[3:3 + 3 * n]))
    return b"".join(struct.pack("<H", rgb_gba(*vals[i:i + 3])) for i in range(0, 3 * n, 3))


# ---------------------------------------------------------------- sound

def sample_to_wav(data, rate, path, loop=None):
    pcm = bytes(b ^ 0x80 for b in data)  # signed -> unsigned
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate, 1, 8)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(pcm)) + pcm + (b"\0" if len(pcm) & 1 else b"")
    if loop is not None:  # 'smpl' chunk so samplers/editors see the loop point
        smpl = struct.pack("<9I", 0, 0, 1000000000 // rate, 60, 0, 0, 0, 1, 0)
        smpl += struct.pack("<6I", 0, 0, loop, len(data) - 1, 0, 0)
        chunks += b"smpl" + struct.pack("<I", len(smpl)) + smpl
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks)


def wav_to_sample(path):
    d = open(path, "rb").read()
    if d[:4] != b"RIFF" or d[8:12] != b"WAVE":
        raise ValueError(f"{path}: not a WAV file")
    pos, fmt = 12, None
    while pos < len(d):
        tag, n = d[pos:pos + 4], struct.unpack("<I", d[pos + 4:pos + 8])[0]
        body = d[pos + 8:pos + 8 + n]
        if tag == b"fmt ":
            fmt = struct.unpack("<HHIIHH", body[:16])
            if fmt[0] != 1 or fmt[1] != 1 or fmt[5] != 8:
                raise ValueError(f"{path}: must be 8-bit mono PCM")
        elif tag == b"data":
            return bytes(b ^ 0x80 for b in body)
        pos += 8 + n + (n & 1)
    raise ValueError(f"{path}: no data chunk")


# ---------------------------------------------------------------- CLI

SUFFIXES = (".4bpp.png", ".8bpp.png", ".rgb555.png", ".pal", ".wav")


def convert(src):
    if src.endswith(".4bpp.png"):
        return png_to_tiles(src, 4)
    if src.endswith(".8bpp.png"):
        return png_to_tiles(src, 8)
    if src.endswith(".rgb555.png"):
        return png_to_bitmap(src)
    if src.endswith(".pal"):
        return jasc_to_pal(src)
    if src.endswith(".wav"):
        return wav_to_sample(src)
    raise ValueError(f"{src}: unknown asset type")


def bin_name(src):
    for suf in SUFFIXES:
        if src.endswith(suf):
            return src[:-len(suf)] + ".bin"
    raise ValueError(src)


def main():
    if sys.argv[1] == "build":  # build OUTDIR SRC... : convert many at once
        import os
        outdir = sys.argv[2]
        for src in sys.argv[3:]:
            dst = os.path.join(outdir, bin_name(src))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(convert(src))
        return
    cmd, src, dst = sys.argv[1:4]
    if cmd == "png2bin":
        if src.endswith(".4bpp.png"):
            out = png_to_tiles(src, 4)
        elif src.endswith(".8bpp.png"):
            out = png_to_tiles(src, 8)
        elif src.endswith(".rgb555.png"):
            out = png_to_bitmap(src)
        else:
            sys.exit(f"{src}: name must end in .4bpp.png, .8bpp.png or .rgb555.png")
    elif cmd == "pal2bin":
        out = jasc_to_pal(src)
    elif cmd == "wav2bin":
        out = wav_to_sample(src)
    else:
        sys.exit(f"unknown command {cmd}")
    with open(dst, "wb") as f:
        f.write(out)


if __name__ == "__main__":
    main()

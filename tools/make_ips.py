#!/usr/bin/env python3
"""Make or apply an IPS patch. Python standard library only.

    python3 tools/make_ips.py create original.gba patched.gba out.ips
    python3 tools/make_ips.py apply  original.gba patch.ips out.gba

IPS records are 3-byte offset, 2-byte size, data (or size 0 + RLE run). The
file may also end with a 3-byte truncation size after "EOF" (a common
extension), which is written when the patched ROM is shorter.
"""
import struct
import sys

EOF_OFFSET = 0x454F46  # "EOF": a record can't start here
MAX_RECORD = 0xFFFF


def create(orig, new):
    out = bytearray(b"PATCH")
    n = len(new)
    i = 0
    while i < n:
        if i < len(orig) and orig[i] == new[i]:
            i += 1
            continue
        # a run of differing bytes, bridging gaps of up to 5 equal bytes
        # (a new record costs 5 bytes of header)
        j = last = i
        while j < n and j - i < MAX_RECORD:
            if j >= len(orig) or orig[j] != new[j]:
                last = j
            elif j - last > 5:
                break
            j += 1
        j = last + 1
        start = i
        if start == EOF_OFFSET:  # step back one byte so the offset isn't "EOF"
            start -= 1
        if start > 0xFFFFFF:
            raise ValueError("ROM too large for IPS (16 MiB limit)")
        chunk = new[start:j]
        while chunk:
            piece, chunk = chunk[:MAX_RECORD], chunk[MAX_RECORD:]
            if len(piece) > 8 and piece.count(piece[0]) == len(piece):
                out += struct.pack(">I", start)[1:] + b"\0\0" + struct.pack(">H", len(piece)) + piece[:1]
            else:
                out += struct.pack(">I", start)[1:] + struct.pack(">H", len(piece)) + piece
            start += len(piece)
        i = j
    out += b"EOF"
    if len(new) < len(orig):
        out += struct.pack(">I", len(new))[1:]
    return bytes(out)


def apply(orig, patch):
    if patch[:5] != b"PATCH":
        raise ValueError("not an IPS patch")
    rom = bytearray(orig)
    p = 5
    while patch[p:p + 3] != b"EOF":
        off = int.from_bytes(patch[p:p + 3], "big")
        size = int.from_bytes(patch[p + 3:p + 5], "big")
        p += 5
        if size:
            data = patch[p:p + size]
            p += size
        else:
            run = int.from_bytes(patch[p:p + 2], "big")
            data = patch[p + 2:p + 3] * run
            p += 3
        if off + len(data) > len(rom):
            rom.extend(b"\0" * (off + len(data) - len(rom)))
        rom[off:off + len(data)] = data
    p += 3
    if len(patch) >= p + 3:
        del rom[int.from_bytes(patch[p:p + 3], "big"):]
    return bytes(rom)


def main():
    cmd = sys.argv[1]
    a = open(sys.argv[2], "rb").read()
    b = open(sys.argv[3], "rb").read()
    if cmd == "create":
        ips = create(a, b)
        if apply(a, ips) != b:
            sys.exit("internal error: patch does not reproduce the target")
        open(sys.argv[4], "wb").write(ips)
        print(f"{sys.argv[4]}: {len(ips)} bytes")
    elif cmd == "apply":
        open(sys.argv[4], "wb").write(apply(a, b))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Convert a GBA ELF into a .gba ROM image. Standard library only.

Usage:
    python3 tools/elf2gba.py input.elf output.gba [--fix-header]

Copies every loadable segment with file contents to its load (physical)
address, relative to the ROM base 0x08000000, filling gaps with zeros,
like `objcopy -O binary`. With --fix-header the header checksum at 0xBD is
recomputed (useful after patching header fields).
"""
import argparse
import struct
import sys

ROM_BASE = 0x08000000
ROM_MAX = 32 * 1024 * 1024


def header_checksum(rom):
    c = 0
    for b in rom[0xA0:0xBD]:
        c = (c - b) & 0xFF
    return (c - 0x19) & 0xFF


def elf_to_rom(data):
    if data[:4] != b"\x7fELF" or data[4] != 1 or data[5] != 1:
        sys.exit("not a 32-bit little-endian ELF")
    e_phoff, = struct.unpack_from("<I", data, 0x1C)
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 0x2A)
    segs = []
    for i in range(e_phnum):
        p_type, p_offset, _vaddr, p_paddr, p_filesz = struct.unpack_from("<IIIII", data, e_phoff + i * e_phentsize)
        if p_type == 1 and p_filesz:  # PT_LOAD with bytes in the file
            if not ROM_BASE <= p_paddr < ROM_BASE + ROM_MAX:
                sys.exit(f"segment at {p_paddr:#x} is outside cartridge ROM")
            segs.append((p_paddr - ROM_BASE, data[p_offset:p_offset + p_filesz]))
    if not segs:
        sys.exit("no loadable ROM segments")
    size = max(off + len(b) for off, b in segs)
    rom = bytearray(size)
    for off, b in segs:
        rom[off:off + len(b)] = b
    return rom


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("elf")
    ap.add_argument("gba")
    ap.add_argument("--fix-header", action="store_true", help="recompute the header checksum")
    a = ap.parse_args()
    rom = elf_to_rom(open(a.elf, "rb").read())
    if len(rom) >= 0xC0:
        want = header_checksum(rom)
        if a.fix_header:
            rom[0xBD] = want
        elif rom[0xBD] != want:
            print(f"warning: header checksum is {rom[0xBD]:#04x}, expected {want:#04x} (use --fix-header)")
        title = rom[0xA0:0xAC].rstrip(b"\0").decode("ascii", "replace")
        code = rom[0xAC:0xB0].decode("ascii", "replace")
        print(f"{title} [{code}]  {len(rom)} bytes")
    open(a.gba, "wb").write(rom)


if __name__ == "__main__":
    main()

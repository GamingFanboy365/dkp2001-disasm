#!/usr/bin/env python3
"""Print the unused K. Rool story text from your ROM.

    python3 tools/story_text.py baserom.gba [--raw]

The old assembly front-end's story mode (src/title/title_story.s) shows the
"K. Rool's Gold" story a page at a time in its small font. Nothing in the
build reaches that mode, so the text is never seen. It's stored in the font's
own encoding; the krool_text_page_* tables (maps/symbols.txt) point at its
lines. This prints it as prose with the speakers named, or with --raw keeps
the original line breaks.

Encoding: 0x00-0x19 A-Z, 0x20-0x39 a-z, 0xFE space, 0xFF new line,
0x00 end of a passage, punctuation as in PUNCT, and 0xF7-0xFC switch the
speaker (the portrait shown). Python standard library only.
"""
import os
import struct
import sys

ROM_BASE = 0x08000000
PUNCT = {0x1A: ".", 0x1B: ",", 0x1D: "!", 0x1E: "?", 0x3B: "'", 0x5F: "-",
         0x3E: "(", 0x3F: ")", 0xFE: " "}
SPEAKERS = {0xF7: "", 0xF8: "K. Rool", 0xF9: "Nikiki", 0xFA: "Nakaka",
            0xFB: "Nukuku", 0xFC: "Nokoko"}  # 0xF7: the narrator


def symbols(path):
    out = {}
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) >= 3 and p[-1].startswith("krool_text_page_"):
                out[int(p[-1].rsplit("_", 1)[1])] = int(p[0], 16)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    raw = "--raw" in sys.argv
    rom = open(args[0], "rb").read()
    here = os.path.dirname(os.path.abspath(__file__))
    pages = symbols(os.path.join(here, "..", "maps", "symbols.txt"))
    ptrs = set()
    for addr in pages.values():
        for p in struct.unpack_from("<9I", rom, addr - ROM_BASE):
            if ROM_BASE <= p < ROM_BASE + len(rom):
                ptrs.add(p)
    start = min(ptrs) - ROM_BASE
    end = rom.index(b"\0", max(ptrs) - ROM_BASE)
    out = []
    for c in rom[start:end]:
        if c <= 0x19:
            out.append(chr(65 + c))
        elif 0x20 <= c <= 0x39:
            out.append(chr(97 + c - 0x20))
        elif c in PUNCT:
            out.append(PUNCT[c])
        elif c == 0xFF:
            out.append("\n" if raw else " ")
        elif c == 0:
            out.append("\n\n")
        elif c in SPEAKERS:
            name = SPEAKERS[c]
            out.append(f"\n\n{name}: " if name else "\n\n")
        else:
            out.append(f"<{c:02X}>")
    text = "".join(out)
    if not raw:
        text = "\n".join(" ".join(line.split()) for line in text.split("\n"))
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    print(text.strip())


if __name__ == "__main__":
    main()

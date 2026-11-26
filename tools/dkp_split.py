#!/usr/bin/env python3
"""Split the Diddy Kong Pilot (2001) debug ELF into per-source-file listings.

Usage:
    python3 tools/dkp_split.py path/to/Diddy_Kong_Pilot_2001.elf [outdir]

Writes (outdir defaults to the repo root):
    baserom.gba        ROM image rebuilt from the ELF's loadable sections (gitignored)
    asm/<source>.s     annotated disassembly for each original source module
    maps/modules.txt   code address range -> original source file
    maps/assets.txt    ROM address -> original asset file (from .stab N_SOL records)
    maps/symbols.txt   every symbol, sorted by address (nm -n -S)

Module boundaries come from .debug_aranges (C files) and .stab N_SO/N_SOL
records (hand-written assembly). Needs arm-none-eabi binutils and pyelftools.
"""
import bisect
import hashlib
import os
import re
import struct
import subprocess
import sys

from elftools.elf.elffile import ELFFile

OBJDUMP = os.environ.get("OBJDUMP", "arm-none-eabi-objdump")
OBJCOPY = os.environ.get("OBJCOPY", "arm-none-eabi-objcopy")
NM = os.environ.get("NM", "arm-none-eabi-nm")
ROM_SECTIONS = [".boot", ".text32", ".text", ".rodata", ".data"]
CODE_SECTIONS = [".boot", ".text32", ".text"]

LIB_RE = re.compile(r".*/src/((?:newlib|gcc)/.*)$")


def clean_path(p):
    p = p.replace("\\", "/")
    m = LIB_RE.match(p)
    if m:
        return "lib/" + m.group(1)
    for pre in ("//d/project/dkp/", "/cygdrive/d/project/dkp/", "./"):
        if p.startswith(pre):
            p = p[len(pre):]
    if p in ("dp-bit.c", "fp-bit.c"):
        return "lib/gcc/" + p
    if p == "crt0.s":
        return "src/crt0.s"
    return p


def read_stabs(elf):
    """Yield (type, value, string) for N_SO (0x64) and N_SOL (0x84) records."""
    st = elf.get_section_by_name(".stab").data()
    ss = elf.get_section_by_name(".stabstr").data()
    strbase = nextbase = 0
    for i in range(len(st) // 12):
        strx, typ, _oth, _desc, val = struct.unpack_from("<IBBhI", st, i * 12)
        if typ == 0:  # per-unit header; val = size of this unit's string table
            strbase, nextbase = nextbase, nextbase + val
            continue
        if typ in (0x64, 0x84):
            end = ss.index(b"\0", strbase + strx)
            s = ss[strbase + strx:end].decode("latin-1")
            if s and not s.endswith("/"):
                yield typ, val, s


def build_modules(elf, stabs):
    starts = {}
    info = elf.get_section_by_name(".debug_info").data()
    # This GCC 2.9 DWARF is too old for pyelftools' DIE parser, but the
    # aranges parse fine, and the CU name is the first inline string after
    # the 11-byte CU header.
    for e in elf.get_dwarf_info().get_aranges().entries:
        m = re.search(rb"[\x20-\x7e]{3,}", info[e.info_offset + 11:e.info_offset + 400])
        starts.setdefault(e.begin_addr, clean_path(m.group().decode()))
    temp_unit = None
    for typ, val, s in stabs:
        if typ == 0x64:
            if "TEMP/" in s.upper():
                temp_unit = val  # cpp'd .S file; its real name follows as N_SOL
                continue
            starts.setdefault(val, clean_path(s))
        elif typ == 0x84 and temp_unit is not None and s.endswith(".S"):
            starts[temp_unit] = clean_path(s)
            temp_unit = None
    # libgcc1.S (_call_via_rX) has no debug records at all.
    starts.setdefault(0x0805CD8C, "lib/gcc/libgcc1.S")

    mods = []
    for name in CODE_SECTIONS:
        sec = elf.get_section_by_name(name)
        lo, hi = sec["sh_addr"], sec["sh_addr"] + sec["sh_size"]
        pts = sorted(a for a in starts if lo <= a < hi)
        if not pts or pts[0] != lo:
            pts.insert(0, lo)
        for i, a in enumerate(pts):
            b = pts[i + 1] if i + 1 < len(pts) else hi
            if b > a:
                mods.append((a, b, starts.get(a, f"unknown/{name.strip('.')}_{a:08x}.s")))
    out = []
    for a, b, n in mods:  # carve the front-end sprite data out of the audio.S range
        if a < TEXT_DATA[0] < b:
            out += [(a, TEXT_DATA[0], n), (TEXT_DATA[0], TEXT_DATA[1], "data:text_sprites")]
            if TEXT_DATA[1] < b:
                # Nintendo's AGBPrint debug library (no debug records name it)
                out.append((TEXT_DATA[1], b, "lib/agbprint.c"))
        else:
            out.append((a, b, n))
    return out


class Memory:
    def __init__(self, elf):
        self.secs = []
        for name in ROM_SECTIONS:
            s = elf.get_section_by_name(name)
            self.secs.append((s["sh_addr"], s.data()))

    def _find(self, a, n):
        for base, data in self.secs:
            if base <= a and a + n <= base + len(data):
                return data, a - base
        return None, None

    def u8(self, a):
        d, o = self._find(a, 1)
        return None if d is None else d[o]

    def u16(self, a):
        d, o = self._find(a, 2)
        return None if d is None else struct.unpack_from("<H", d, o)[0]

    def u32(self, a):
        d, o = self._find(a, 4)
        return None if d is None else struct.unpack_from("<I", d, o)[0]

    def cstring(self, a, maxlen=60):
        d, o = self._find(a, 1)
        if d is None:
            return None
        end = d.find(b"\0", o, o + 256)
        if end < 0 or end - o < 2:
            return None
        s = d[o:end]
        if not all(32 <= c < 127 or c in (9, 10) for c in s):
            return None
        s = s.decode().replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace('"', '\\"')
        return '"' + (s if len(s) <= maxlen else s[:maxlen] + "...") + '"'


def decode_thumb_halfwords(hws):
    """Disassemble standalone 16-bit Thumb halfwords (ARMv4T has no Thumb-2)."""
    if not hws:
        return {}
    order = sorted(set(hws))
    # Pad each halfword with nops so nothing pairs with it and a Thumb-2 IT
    # (0xbfxx) can't make the following entries conditional.
    blob = b"".join(struct.pack("<HHHHHHHH", h, *([0x46C0] * 7)) for h in order)
    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), f"dkp_hw_{os.getpid()}.bin")
    with open(tmp, "wb") as f:
        f.write(blob)
    try:
        out = subprocess.run([OBJDUMP, "-D", "-b", "binary", "-m", "armv4t", "-M", "force-thumb", tmp],
                             capture_output=True, text=True, check=True).stdout
    finally:
        os.unlink(tmp)
    res = {}
    for line in out.splitlines():
        m = re.match(r"^\s*([0-9a-f]+):\s+([0-9a-f]{4})\s+(.*)$", line)
        if m and int(m.group(1), 16) % 16 == 0:
            res[int(m.group(2), 16)] = m.group(3).strip()
    return res


INSN_RE = re.compile(r"^\s*([0-9a-f]{7,8}):\t([0-9a-f]{4} [0-9a-f]{4}|[0-9a-f]{8}|[0-9a-f]{4})\s*\t?(.*)$")
LABEL_RE = re.compile(r"^([0-9a-f]{8}) <(.+)>:$")
LINE_RE = re.compile(r"^(\S+?\.(?:c|s|S|h)):(\d+)(.*)$")
POOL_RE = re.compile(r"\[pc, #-?\d+\].*?@ \(?([0-9a-f]{7,8})")
POOL_LDR_RE = re.compile(r"^(ldr(?:eq|ne|cs|cc|hs|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)?)\t(r\d+|sl|fp|ip|sp|lr), \[pc, #-?\d+\]$")
BRANCH_RE = re.compile(r"^(b[a-z]*)(?:\.n|\.w)?\t([0-9a-f]+) <[^>]*>$")
IDENT_RE = re.compile(r"^[A-Za-z_][\w.]*$")
BAD_TEXT = ("UNDEFINED", "UNPREDICTABLE", "illegal", "undefined", "<", "??")

# Original layout. The linker script flows sections in this order, so an
# unmodified build lands on exactly these addresses.
HEADER = (0x08000004, 0x080000C0)        # ROM header: data, not code
TEXT32_VMA = (0x03000000, 0x03002EAC)    # IWRAM code, stored in ROM at TEXT32_LMA
TEXT32_LMA = 0x080000F4
CODE_ROM = (0x08000000, 0x0805E6C8)      # .boot + ROM copy of .text32 + .text
DATA_ROM = (0x0805E6D0, 0x084D8644)      # .rodata + .data
TEXT_DATA = (0x08017730, 0x0805886C)     # front-end sprites linked into .text after audio.S
# Data regions, in ROM order, and the file each is written to.
DATA_REGIONS = [(TEXT_DATA[0], TEXT_DATA[1], "data/text_sprites.s"),
                (0x0805E6D0, 0x0826034C, "data/rodata.s"),
                (0x0826034C, 0x084D8644, "data/data.s")]
INLINE_MAX = 64                          # data chunks smaller than this stay in the .s file


def in_data(v):
    return any(lo <= v < hi for lo, hi, _ in DATA_REGIONS)
# Objects known to hold pointers that the heuristics can't prove.
FORCE_POINTER_OBJECTS = {"lconv"}
IWRAM_COPY = (0x08006094, 0x080064E8)    # main.c, whose pool holds the copy-end pointer
BSS = [(".bss", 0x02000000, 0x0200E360), (".bss32", 0x03002EAC, 0x030065C8)]


class Item:
    __slots__ = ("addr", "size", "mode", "asm", "comment", "pre", "kind", "target", "level", "expr")

    def __init__(self, addr, size, mode, asm, kind, comment="", target=None):
        self.addr, self.size, self.mode, self.asm = addr, size, mode, asm
        self.kind, self.comment, self.target, self.pre = kind, comment, target, []
        self.level, self.expr = 0, None


def rom_to_vma(a):
    if TEXT32_LMA <= a < TEXT32_LMA + (TEXT32_VMA[1] - TEXT32_VMA[0]):
        return a - TEXT32_LMA + TEXT32_VMA[0]
    return a


def collect(lines, mem, extra_data=()):
    """Turn objdump output into a sorted list of Items plus objdump's label names."""
    data_words = set(range(HEADER[0], HEADER[1], 4)) | set(extra_data)
    last_cmp = last_pool_val = None
    for line in lines:
        m = INSN_RE.match(line)
        if not m:
            if LABEL_RE.match(line):
                last_cmp = last_pool_val = None
            continue
        text = m.group(3)
        pm = POOL_RE.search(text)
        if pm:
            t = int(pm.group(1), 16)
            data_words.add(t)
            last_pool_val = mem.u32(t)
        elif " " in m.group(2):
            # objdump paired two Thumb halfwords as Thumb-2; look for a
            # pc-relative load hidden in the pair.
            a = int(m.group(1), 16)
            for sub in (a, a + 2):
                h = mem.u16(sub)
                if h is not None and h & 0xF800 == 0x4800:
                    data_words.add(((sub + 4) & ~3) + (h & 0xFF) * 4)
        cm = re.match(r"cmp\s+r\d+, #(\d+)", text)
        if cm:
            last_cmp = int(cm.group(1))
        if re.match(r"mov\s+pc, r\d+", text) and last_cmp is not None and last_pool_val:
            for k in range(last_cmp + 1):
                data_words.add(last_pool_val + 4 * k)
            last_cmp = None

    # objdump decodes Thumb as Thumb-2 (pairs, IT blocks). Re-decode every
    # 16-bit halfword standalone; ARMv4T Thumb is strictly 16-bit (BL aside).
    hws = []
    for line in lines:
        m = INSN_RE.match(line)
        if m and len(m.group(2)) != 8 and not m.group(3).startswith("bl\t"):
            a = int(m.group(1), 16)
            hws.extend([mem.u16(a), mem.u16(a + 2)] if " " in m.group(2) else [mem.u16(a)])
    thumb16 = decode_thumb_halfwords([h for h in hws if h is not None and h < 0xE800])

    def thumb_item(a):
        h = mem.u16(a)
        if h & 0xF800 == 0x4800:  # ldr rd, [pc, #imm]: keep it a labelled pool load
            rd, imm = (h >> 8) & 7, (h & 0xFF) * 4
            return Item(a, 2, "thumb", f"ldr\tr{rd}, [pc, #{imm}]", "poolload", target=((a + 4) & ~3) + imm)
        if h >= 0xE800:
            return Item(a, 2, "thumb", None, "raw", "undefined on ARMv4T")
        t = thumb16.get(h)
        is_pc_branch = t and re.match(r"^b[a-z.]*\s+(?!r\d|sl|fp|ip|sp|lr|pc)", t) and not t.startswith(("bic", "bx"))
        if t is None or is_pc_branch or any(x in t for x in BAD_TEXT):
            return Item(a, 2, "thumb", None, "raw", t or "")
        return Item(a, 2, "thumb", re.split(r"\s*@", t)[0].rstrip(), "insn")

    items, labels, pending = {}, {}, []
    skip_until = 0
    for line in lines:
        if line.startswith("Disassembly of section") or re.match(r"^[\w.$]+\(\):$", line):
            continue
        lm = LINE_RE.match(line)
        if lm:
            pending.append(f"@ {clean_path(lm.group(1))}:{lm.group(2)}{lm.group(3)}")
            continue
        lab = LABEL_RE.match(line)
        if lab:
            labels.setdefault(int(lab.group(1), 16), lab.group(2))
            continue
        m = INSN_RE.match(line)
        if not m:
            continue
        a, raw, text = int(m.group(1), 16), m.group(2), m.group(3)
        size = 2 if len(raw) == 4 else 4
        mode = "arm" if len(raw) == 8 else "thumb"
        new = []
        for off in range(0, size, 2):
            sub = a + off
            if skip_until - 4 <= sub < skip_until:
                continue
            if sub in data_words:
                new.append(Item(sub, 4, mode, f".word 0x{mem.u32(sub):08x}", "data"))
                skip_until = sub + 4
            elif off == 0 and (mode == "arm" or text.startswith("bl\t") or (size == 2 and BRANCH_RE.match(text.split("\t@")[0].rstrip()))):
                new.append(make_insn(a, size, mode, text))
                break
            elif size == 2:
                h = mem.u16(a)
                if h & 0xF800 == 0x4800:  # ldr rd, [pc, #imm]: decode directly
                    rd, imm = (h >> 8) & 7, (h & 0xFF) * 4
                    new.append(Item(a, 2, mode, f"ldr\tr{rd}, [pc, #{imm}]", "poolload",
                                    target=((a + 4) & ~3) + imm))
                else:
                    new.append(thumb_item(a))
            else:
                new.append(thumb_item(sub))
        if new:
            new[0].pre = pending
            pending = []
        for it in new:
            items[it.addr] = it

    # Pool / table words that objdump's decoding stepped over (it decodes data
    # at whatever alignment the previous label left it): evict the overlapping
    # items and make the word a data item. Bytes left over become raw bytes.
    order = sorted(items)
    for t in sorted(data_words):
        if t in items and items[t].kind == "data":
            continue
        v = mem.u32(t)
        if v is None or not any(lo <= t < hi for lo, hi in ((0x08000000, 0x0805E6D0), TEXT32_VMA)):
            continue
        i = bisect.bisect_right(order, t) - 1
        mode = items[order[i]].mode if i >= 0 and order[i] in items else "thumb"
        while i >= 0 and order[i] < t + 4:
            a0 = order[i]
            if a0 in items and a0 + items[a0].size > t:
                pre = items.pop(a0).pre
                if pre and t not in items:
                    pass
            i += 1
            if i >= len(order):
                break
        items[t] = Item(t, 4, mode, f".word 0x{v:08x}", "data")
        order = sorted(items)
    labels = {a: n for a, n in labels.items() if not in_data(a)}
    return [items[k] for k in sorted(items) if not in_data(k)], labels


def make_insn(a, size, mode, text):
    t = re.split(r"\s*@", text)[0].rstrip()
    if not t or any(x in text for x in BAD_TEXT if x != "<"):
        return Item(a, size, mode, None, "raw", t)
    bm = BRANCH_RE.match(t)
    if bm:
        return Item(a, size, mode, bm.group(1), "branch", target=int(bm.group(2), 16))
    if "<" in t:
        return Item(a, size, mode, None, "raw", t)
    pm = POOL_RE.search(text)
    if pm and POOL_LDR_RE.match(t):
        return Item(a, size, mode, t, "poolload", target=int(pm.group(1), 16))
    return Item(a, size, mode, t, "insn")


def raw_text(it, mem):
    if it.mode == "arm" and it.size == 4 and it.kind != "data":
        return f".inst 0x{mem.u32(it.addr):08x}"
    if it.size == 4 and it.kind == "data":
        return f".word 0x{mem.u32(it.addr):08x}"
    return ".hword " + ", ".join(f"0x{mem.u16(it.addr + k):04x}" for k in range(0, it.size, 2))


class Symbols:
    """Names for every address the source refers to, and pointer -> expression."""

    def __init__(self, elf, nm, items, labels, mem):
        self.mem = mem
        self.lma_end_refs = None  # set while resolving AgbMain's IWRAM copy
        self.used = set()
        self.code = {}      # addr -> label in code (item starts only)
        self.data = {}      # addr -> label in .rodata/.data
        self.ram = {}       # addr -> label in .bss/.bss32
        self.starts = {it.addr: it for it in items}
        self.funcs = set()  # ELF function symbols (thumb ones stored without bit 0)
        self.sizes = {}
        for sym in elf.get_section_by_name(".symtab").iter_symbols():
            t = sym["st_info"]["type"]
            # Functions, plus global labels (hand-written asm routines are untyped).
            if t in ("STT_FUNC", "STT_LOPROC") or (sym["st_info"]["bind"] == "STB_GLOBAL" and sym["st_shndx"] != "SHN_ABS"):
                self.funcs.add(sym["st_value"] & ~1)
            if sym["st_size"]:
                self.sizes.setdefault(sym["st_value"], sym["st_size"])

        for a in sorted(labels):
            self._name(self.code, a, labels[a])
        for it in items:
            if it.kind == "branch" and it.target in self.starts:
                self._name(self.code, it.target, None, "L_")
            if it.kind == "poolload" and it.target in self.starts:
                self._name(self.code, it.target, None, "_")

        for ln in nm.splitlines():
            p = ln.split()
            if len(p) < 3 or p[-2] in "aAUw" or p[-1].startswith(("$", ".")):
                continue
            a = int(p[0], 16)
            if in_data(a):
                self._name(self.data, a, p[-1], "D_")
            elif any(lo <= a < hi for _, lo, hi in BSS):
                self._name(self.ram, a, p[-1], "B_")
        self._name(self.data, DATA_ROM[1], "__data_rom_end")
        for sec, lo, hi in BSS:
            if lo not in self.ram:
                self._name(self.ram, lo, None, "B_")
        self._sorted()

    def _sorted(self):
        self.code_sorted = sorted(self.code)
        self.data_sorted = sorted(self.data)
        self.ram_sorted = sorted(self.ram)

    def _name(self, table, a, name, prefix="L_"):
        if a in table:
            return table[a]
        if not name or not IDENT_RE.match(name) or name in self.used:
            name = f"{prefix}{a:08x}"
        if name in self.used:
            return None
        self.used.add(name)
        table[a] = name
        return name

    # --- classification ---
    def is_exact(self, v, ram_ok=True):
        """v is a pointer to the start of something with a name (high confidence)."""
        if not v & 0xFFFF:
            return False  # 0x02000000, 0x08010000...: far more common in tiles/maps than as pointers
        if v in self.data:
            return True
        if v in self.ram:
            return ram_ok
        return (v & ~1) in self.funcs and (v & ~1) in self.starts

    @staticmethod
    def in_range(v):
        return (CODE_ROM[0] <= v <= DATA_ROM[1] or TEXT32_VMA[0] <= v < TEXT32_VMA[1]
                or any(lo <= v < hi for _, lo, hi in BSS))

    def expr(self, v, create=True):
        """Symbolic expression for pointer value v, or None if it isn't one."""
        def near(table, srt, v, lo):
            i = bisect.bisect_right(srt, v) - 1
            if i >= 0 and srt[i] >= lo:
                a = srt[i]
                return table[a] if a == v else f"{table[a]}+0x{v - a:x}"
            return None

        if v == TEXT32_LMA + (TEXT32_VMA[1] - TEXT32_VMA[0]) and self.lma_end_refs is not None:
            return "__text32_lma_end"
        if TEXT32_LMA <= v < TEXT32_LMA + (TEXT32_VMA[1] - TEXT32_VMA[0]):
            return "__text32_lma" + (f"+0x{v - TEXT32_LMA:x}" if v != TEXT32_LMA else "")
        if (CODE_ROM[0] <= v < CODE_ROM[1] or TEXT32_VMA[0] <= v < TEXT32_VMA[1]) and not in_data(v):
            base = v & ~1
            it = self.starts.get(base)
            if v & 1 and it is not None and it.mode == "thumb" and it.kind not in ("data",):
                n = self.code.get(base) or (create and self._name(self.code, base, None, "L_"))
                if n:
                    if create:
                        self._sorted()
                    return f"{n}+1"
            if not v & 1 and it is not None:
                n = self.code.get(v) or (create and self._name(self.code, v, None, "L_"))
                if n:
                    if create:
                        self._sorted()
                    return n
            lo = TEXT32_VMA[0] if v < 0x08000000 else CODE_ROM[0]
            return near(self.code, self.code_sorted, v, lo)
        if in_data(v) or v == DATA_ROM[1]:
            if v in self.data:
                return self.data[v]
            i = bisect.bisect_right(self.data_sorted, v) - 1
            if i >= 0:
                a = self.data_sorted[i]
                if a in self.sizes and v < a + self.sizes[a]:
                    return f"{self.data[a]}+0x{v - a:x}"
            if create:
                self._name(self.data, v, None, "D_")
                self._sorted()
                return self.data[v]
            return near(self.data, self.data_sorted, v, next(lo for lo, hi, _ in DATA_REGIONS if lo <= v <= hi))
        for _, lo, hi in BSS:
            if lo <= v < hi:
                return near(self.ram, self.ram_sorted, v, lo)
        return None


def choose_data_pointers(syms, mem):
    """Pick which words in .rodata/.data are pointers.

    A word is symbolized if it points exactly at a named symbol, or if it lies
    in an object (the span up to the next data symbol) that looks like a
    pointer table: mostly exact hits, or mostly pointer-like words. Graphics,
    samples and music data only match by coincidence and are left alone.
    """
    owners = syms.data_sorted[:]
    cand = {}
    for lo, hi, _ in DATA_REGIONS:
        for a in range(lo, hi, 4):
            v = mem.u32(a)
            if v is not None and syms.in_range(v):
                cand[a] = v
    stats = {}
    for a, v in cand.items():
        i = bisect.bisect_right(owners, a) - 1
        o = owners[i] if i >= 0 else DATA_ROM[0]
        s = stats.setdefault(o, [0, 0])
        s[0] += 1
        s[1] += syms.is_exact(v, ram_ok=False)
    chosen = {}
    for a, v in cand.items():
        i = bisect.bisect_right(owners, a) - 1
        o = owners[i] if i >= 0 else DATA_ROM[0]
        end = owners[i + 1] if i + 1 < len(owners) else DATA_ROM[1]
        n_ptr, n_exact = stats[o]
        n_words = max(1, (end - o) // 4)
        blob = n_ptr >= 10 and n_exact / n_ptr < 0.1
        table = ((n_exact >= 1 and n_exact / n_ptr >= 0.5)       # e.g. instrument info: sample + loop pointers
                 or (n_words >= 2 and n_ptr / n_words >= 0.75)   # pointer tables
                 or end - o == 4                                 # one-word objects like __ptr_ram_sin
                 or syms.data.get(o) in FORCE_POINTER_OBJECTS)
        if (syms.is_exact(v, ram_ok=False) and not blob) or table:
            chosen[a] = v

    # Format fields: if most objects of a family (same name ignoring numbers,
    # e.g. __chr_lake_00_lvl, __chr_lake_01_lvl, ...) hold an exact pointer at
    # the same offset, that offset is a pointer field in all of them.
    fams = {}
    for i, o in enumerate(owners):
        end = owners[i + 1] if i + 1 < len(owners) else DATA_ROM[1]
        fams.setdefault(re.sub(r"_?\d+", "#", syms.data[o]), []).append((o, end))
    for objs in fams.values():
        if len(objs) < 3:
            continue
        for off in range(0, 32, 4):
            hits = [o + off for o, e in objs if o + off + 4 <= e and syms.is_exact(mem.u32(o + off) or 0, ram_ok=False)]
            if len(hits) >= 0.6 * len(objs):
                for a in hits:
                    chosen[a] = mem.u32(a)
    return chosen



class AssetNamer:
    """Decides where each data object's bytes live under assets/.

    Title-screen assets keep the file names recorded in the stabs (N_SOL),
    the rest are grouped by naming family; C objects use their source file.
    """

    def __init__(self, stabs, cvars):
        self.nsol = sorted((v, s) for t, v, s in stabs if t == 0x84 and v >= 0x08000000
                           and not s.endswith((".s", ".S", ".c", ".h", ".inc")))
        self.nsol_addrs = [a for a, _ in self.nsol]
        self.cvars = cvars  # addr -> (name, type, cu)
        self.names = set()

    def _nsol_dir(self, name, addr):
        i = bisect.bisect_right(self.nsol_addrs, addr) - 1
        if i < 0:
            return None
        a, path = self.nsol[i]
        base = re.sub(r"\(.*\)|\..*$", "", os.path.basename(path)).lower()
        key = re.sub(r"[^a-z0-9]", "", base)[:5]
        if addr == a or re.sub(r"[^a-z0-9]", "", name.lower()).startswith(key):
            d = os.path.dirname(re.sub(r"^src/", "", path))
            return f"{d}/{os.path.splitext(os.path.basename(path))[0]}".replace("(", "_").replace(")", "")
        return None

    def path(self, name, addr):
        n = name
        m = re.match(r"^(.+?)_(chars|num_chars|map|map_size_x|map_size_y|image|plt|pal)$", n)
        if m and (f"{m.group(1)}_chars" in self.names or f"{m.group(1)}_image" in self.names):
            return f"backgrounds/menu/{m.group(1)}/{n}.bin"
        m = re.match(r"^__(spr|pal|chr|map|frs|net|ani)_(.+)$", n)
        if m:
            kind, rest = m.groups()
            if kind == "spr":
                return f"sprites/{re.sub(r'_[0-9]+$', '', rest)}/{rest}.bin"
            return {"pal": "palettes", "chr": "backgrounds/tiles", "map": "backgrounds/maps",
                    "frs": "backgrounds", "net": "ai_networks", "ani": "animations"}[kind] + f"/{rest}.bin"
        m = re.match(r"^vgroup(\d+)_p(\d+)_smp$", n)
        if m:
            return f"sound/samples/vgroup{m.group(1)}/p{m.group(2)}.bin"
        m = re.match(r"^v(\d+)_t(\d+)_keysplit$", n)
        if m:
            return f"sound/keysplits/{n}.bin"
        m = re.match(r"^three_(.+)_trk(\d+)$", n)
        if m:
            return f"sound/music/{m.group(1)}/trk{m.group(2)}.bin"
        d = self._nsol_dir(n, addr)
        if d:
            return f"{d}/{n}.bin"
        m = re.match(r"^(.+?)_(char|info|frames|plt)(_\d+)?$", n)
        if m:
            top = "menu_sprites" if TEXT_DATA[0] <= addr < TEXT_DATA[1] else "title/sprites"
            return f"{top}/{m.group(1)}/{n}.bin"
        if n.startswith("tab_"):
            return f"tables/{n}.bin"
        if n.startswith("obj_"):
            return f"objects/{n}.bin"
        if n.endswith("_data"):
            return f"menu_graphics/{n}.bin"
        if addr in self.cvars:
            cu = os.path.splitext(os.path.basename(self.cvars[addr][2]))[0]
            return f"tables/{cu}/{n}.bin"
        return f"misc/{n}.bin"


def inline_bytes(bs):
    """Assembler lines for a short run of bytes: strings as .ascii, else .byte."""
    out, i = [], 0
    while i < len(bs):
        j = i
        while j < len(bs) and (32 <= bs[j] < 127 or bs[j] in (9, 10)):
            j += 1
        if j - i >= 4 and (j == len(bs) or bs[j] == 0):
            text = bs[i:j].decode().replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
            if j < len(bs):
                out.append(f'\t.asciz "{text}"')
                i = j + 1
            else:
                out.append(f'\t.ascii "{text}"')
                i = j
            continue
        k = i
        while k < len(bs) and k - i < 16:
            # stop a .byte row where a string starts
            jj = k
            while jj < len(bs) and (32 <= bs[jj] < 127 or bs[jj] in (9, 10)):
                jj += 1
            if jj - k >= 4 and (jj == len(bs) or bs[jj] == 0) and k > i:
                break
            k += 1
        out.append("\t.byte " + ", ".join(f"0x{x:02x}" for x in bs[i:k]))
        i = k
    return out


ASSETS = None  # AssetNamer, set in main()
ASSET_META = {}  # assets/ path -> (start, length, owner name, owner address)


def emit_data(out, lo, hi, rel, syms, mem, data_exprs, data_numeric, linemap, comment_for):
    L = [f"@ {rel}  [{lo:08x}-{hi:08x}]",
         "@ Labels and pointers are here; larger blocks of bytes are in assets/ (see the .incbin paths).", ""]
    labels = [a for a in syms.data_sorted if lo <= a < hi]
    words = sorted(a for a in data_exprs if lo <= a < hi and data_exprs[a] and a not in data_numeric)
    events = sorted(set(labels) | set(words))
    cur = lo
    owner = None
    written = {}

    def chunk(a, b):
        if b <= a:
            return
        bs = mem_bytes(mem, a, b)
        if b - a < INLINE_MAX or owner is None:
            L.extend(inline_bytes(bs))
            return
        name, oaddr = owner
        path = ASSETS.path(name, oaddr)
        k = written.get(path, 0)
        written[path] = k + 1
        if k:
            path = re.sub(r"\.bin$", f".{k + 1}.bin", path)
        full = os.path.join(out, "assets", path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(bs)
        ASSET_META[path] = (a, b - a, name, oaddr)
        L.append(f'\t.incbin "assets/{path}"')

    for e in events:
        if e < cur:
            if e in syms.data:  # label inside a word emitted just above
                L.append(f"\t.set {syms.data[e]}, . - {cur - e}")
            continue
        chunk(cur, e)
        cur = e
        if e in syms.data:
            # Labels this tool made up (D_...) mark pointer targets inside an
            # object; its bytes stay with the object's file.
            if owner is None or not syms.data[e].startswith("D_"):
                owner = (syms.data[e], e)
            cv = ASSETS.cvars.get(e)
            L.append("")
            L.append(f"{syms.data[e]}:  @ {e:08x}" + (f"  {cv[1]}  ({cv[2]})" if cv else ""))
        if e in words:
            v = mem.u32(e)
            c = comment_for(v)
            L.append(f"\t.word {data_exprs[e]}" + (f"\t@ {c}" if c else ""))
            linemap[(rel, len(L))] = e
            cur = e + 4
    chunk(cur, hi)
    if hi in syms.data and hi == DATA_ROM[1]:
        L.append(f"{syms.data[hi]}:")
    return L


def mem_bytes(mem, a, b):
    d, o = mem._find(a, b - a)
    return bytes(d[o:o + (b - a)])


OBJ_SIZES = {0: [(8, 8), (16, 16), (32, 32), (64, 64)],
             1: [(16, 8), (32, 8), (32, 16), (64, 32)],
             2: [(8, 16), (8, 32), (16, 32), (32, 64)]}


def convert_assets(out, mem, syms):
    """Turn whole-object asset files into editable formats where the format is
    known, verifying each converts back to identical bytes."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gfx
    by_name = {n: a for a, n in syms.data.items()}

    def obj_len(addr):
        i = bisect.bisect_right(syms.data_sorted, addr)
        nxt = syms.data_sorted[i] if i < len(syms.data_sorted) else DATA_ROM[1]
        return nxt - addr

    def obj_bytes(name):
        a = by_name.get(name)
        return mem_bytes(mem, a, a + obj_len(a)) if a is not None else None

    # Front-end sprites: 16-byte frame records {u8 *char; u16 words, count; info *; 0}
    sprite_tiles = {}
    char_addrs = {a for a, n in syms.data.items() if "_char" in n}
    info_addrs = {a for a, n in syms.data.items() if "_info" in n}
    for lo, hi, _ in DATA_REGIONS:
        for a in range(lo, hi - 12, 4):
            c, i = mem.u32(a), mem.u32(a + 8)
            if c in char_addrs and i in info_addrs and 1 <= mem.u16(a + 6) <= 64:
                b4, b5 = mem.u8(i + 4), mem.u8(i + 5)
                shape, size = b4 >> 6, b5 >> 6
                w = OBJ_SIZES.get(shape, OBJ_SIZES[0])[size][0] // 8
                sprite_tiles.setdefault(c, (8 if b4 & 0x20 else 4, w))

    done = {"png": 0, "pal": 0, "wav": 0}
    for path, (start, length, name, oaddr) in sorted(ASSET_META.items()):
        if start != oaddr or length != obj_len(oaddr) or re.search(r"\.\d+\.bin$", path):
            continue  # only whole objects
        full = os.path.join(out, "assets", path)
        data = open(full, "rb").read()
        stem = full[:-4]
        try:
            if re.search(r"_(plt|pal)$", name) or path.startswith("palettes/"):
                if len(data) % 2:
                    continue
                gfx.pal_to_jasc(data, stem + ".pal")
                new, kind = stem + ".pal", "pal"
            elif oaddr in sprite_tiles:
                bpp, w = sprite_tiles[oaddr]
                base = re.sub(r"_char(_\d+)?$", "", name)
                pal = obj_bytes(f"{base}_plt") or obj_bytes(f"__pal_{base}")
                gfx.tiles_to_png(data, bpp, stem + f".{bpp}bpp.png", w, gfx.palette_from_bin(pal) if pal else None)
                new, kind = stem + f".{bpp}bpp.png", "png"
            elif name.endswith("_chars") and f"{name[:-6]}_num_chars" in by_name:
                count = mem.u32(by_name[f"{name[:-6]}_num_chars"])
                if not count or len(data) % count or (len(data) // count) not in (32, 64):
                    continue
                bpp = 4 if len(data) // count == 32 else 8
                pal = (obj_bytes(f"{name[:-6]}_plt") or obj_bytes(f"__pal_{name[:-6]}")
                       or obj_bytes(re.sub(r"\d+$", "", name[:-6]) + "_plt"))
                gfx.tiles_to_png(data, bpp, stem + f".{bpp}bpp.png", 16, gfx.palette_from_bin(pal) if pal else None)
                new, kind = stem + f".{bpp}bpp.png", "png"
            elif name.endswith("_image") and len(data) == 240 * 160 * 2:
                gfx.bitmap_to_png(data, 240, stem + ".rgb555.png")
                new, kind = stem + ".rgb555.png", "png"
            elif re.match(r"^vgroup\d+_p\d+_smp$", name):
                inf = by_name.get(name[:-4] + "_inf")
                rate, loop = 11025, None
                if inf is not None and mem.u32(inf + 0x10) == oaddr:
                    rate = mem.u32(inf + 8) or rate
                    lp = mem.u32(inf + 0x14)
                    loop = lp if lp < len(data) else None
                gfx.sample_to_wav(data, rate, stem + ".wav", loop)
                new, kind = stem + ".wav", "wav"
            else:
                continue
        except ValueError:
            continue
        if gfx.convert(new) != data:
            os.remove(new)
            continue
        os.remove(full)
        done[kind] += 1
    print(f"  assets converted: {done['png']} PNG, {done['pal']} palettes, {done['wav']} WAV; "
          f"{sum(1 for p in ASSET_META if os.path.exists(os.path.join(out, 'assets', p)))} left as .bin")


def emit(out, mods, items, syms, mem, data_ptrs, data_numeric, elf):
    """Write asm/, data/ and rom.s. Returns {(file, line): addr}."""
    by_mod = {n: [] for _, _, n in mods}
    smods = sorted(mods)
    bounds = [m[0] for m in smods]
    for it in items:
        i = bisect.bisect_right(bounds, it.addr) - 1
        if i >= 0 and it.addr < smods[i][1]:
            by_mod[smods[i][2]].append(it)

    # Resolve every expression first so that labels created on the way exist
    # before anything is written.
    for it in items:
        if it.kind == "data" and it.expr is None:
            # AgbMain copies [__text32_lma, __text32_lma_end) to IWRAM; that end
            # address happens to equal the start of .text, but means the copy end.
            syms.lma_end_refs = True if IWRAM_COPY[0] <= it.addr < IWRAM_COPY[1] else None
            it.expr = syms.expr(mem.u32(it.addr)) or ""
            syms.lma_end_refs = None
    data_exprs = {a: syms.expr(v) for a, v in data_ptrs.items()}

    def comment_for(v):
        s = mem.cstring(v) if in_data(v) else None
        return s or ""

    linemap, files, count = {}, [], {}
    for a, b, n in mods:
        if n.startswith("data:"):
            files.append(f"data/{n[5:]}.s")
            continue
        count[n] = count.get(n, 0) + 1
        fname = n if count[n] == 1 else re.sub(r"(\.[cSs])$", rf".{count[n]}\1", n)
        rel = os.path.join("asm", re.sub(r"\.c$", ".c.s", fname))
        files.append(rel)
        L = [f"@ {n}  [{a:08x}-{b:08x}]", "@ Generated by tools/dkp_split.py from the 2001 debug ELF.", ""]
        mode = None
        cur = a
        prev_kind = None

        def gap(lo, hi):
            # Split at labels that fall inside the raw bytes.
            j = bisect.bisect_left(syms.code_sorted, lo)
            while j < len(syms.code_sorted) and syms.code_sorted[j] < hi:
                cut = syms.code_sorted[j]
                raw_bytes(lo, cut)
                L.append(f"{syms.code[cut]}:  @ {cut:08x}")
                lo = cut
                j += 1
            raw_bytes(lo, hi)

        def raw_bytes(lo, hi):
            while lo < hi:
                d, o = mem._find(lo, 1)
                k = min(hi - lo, 16)
                bs = d[o:o + k]
                if not any(bs):
                    z = lo
                    while z < hi and mem.u8(z) == 0:
                        z += 1
                    L.append(f"\t.space {z - lo}")
                    lo = z
                else:
                    L.append("\t.byte " + ", ".join(f"0x{x:02x}" for x in bs))
                    lo += k

        for it in by_mod[n]:
            if not a <= it.addr < b or it.addr < cur:
                continue
            if it.addr > cur:
                gap(cur, it.addr)
            if it.mode != mode and it.kind != "data":
                L.append(f"\t.{it.mode}")
                mode = it.mode
            if it.kind == "data" and prev_kind != "data" and it.addr % 4 == 0:
                # Start of a literal pool / table: keeps it aligned if the code
                # before it is edited (emits nothing in the original layout).
                L.append("\t.balign 4")
            L.extend(it.pre)
            lab = syms.code.get(it.addr)
            if lab:
                if lab.startswith(("L_", "_")):
                    L.append(f"{lab}:")
                else:
                    L += ["", f"{lab}:  @ {it.addr:08x}"]
            body, note = render(it, syms, mem, comment_for)
            L.append(f"\t{body}" + (f"\t@ {note}" if note else ""))
            linemap[(rel, len(L))] = it.addr
            cur = it.addr + it.size
            prev_kind = it.kind
            for inner in range(it.addr + 1, cur):  # labels inside this item
                if inner in syms.code:
                    L.append(f"\t.set {syms.code[inner]}, . - {cur - inner}")
        if cur < b:
            gap(cur, b)
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("\n".join(L) + "\n")

    # Data regions: labels, pointers, small chunks inline, the rest as asset files.
    for lo, hi, rel in DATA_REGIONS:
        L = emit_data(out, lo, hi, rel, syms, mem, data_exprs, data_numeric, linemap, comment_for)
        with open(os.path.join(out, rel), "w") as f:
            f.write("\n".join(L) + "\n")

    # .bss / .bss32: named RAM, so code can refer to it symbolically.
    L = ["@ Uninitialised RAM. EWRAM .bss at 0x02000000, IWRAM .bss32 after .text32.", ""]
    for sec, lo, hi in BSS:
        L.append(f'\t.section {sec}, "aw", %nobits')
        cur = lo
        for a in [x for x in syms.ram_sorted if lo <= x < hi]:
            if a > cur:
                L.append(f"\t.space 0x{a - cur:x}")
            L.append(f"{syms.ram[a]}:  @ {a:08x}")
            cur = a
        L.append(f"\t.space 0x{hi - cur:x}")
        L.append("")
    with open(os.path.join(out, "data/bss.s"), "w") as f:
        f.write("\n".join(L) + "\n")

    R = ["@ Top-level build file: every module in ROM order.",
         "@ Assemble with --defsym SHIFT_CODE=n / SHIFT_DATA=n to move code / data (relocation test).",
         "\t.syntax unified", "\t.global _start", ""]
    last_sec = None
    for (a, b, n), rel in zip(mods, files):
        sec = ".boot" if 0x08000000 <= a < TEXT32_LMA else ".text32" if a < 0x08000000 else ".text"
        if sec != last_sec:
            if last_sec == ".text":
                pass
            flags = {".boot": '"ax"', ".text32": '"awx"', ".text": '"ax"'}[sec]
            R.append(f"\n\t.section {sec}, {flags}, %progbits")
            R.append("\t.balign 4")
            if sec == ".text":
                R += ["\t.ifdef SHIFT_CODE", "\t.space SHIFT_CODE", "\t.endif"]
            last_sec = sec
        R.append(f'\t.include "{rel}"')
    R += ["\t.ifdef SHIFT_DATA", "\t.space SHIFT_DATA", "\t.endif",
          "", '\t.section .rodata, "a", %progbits', "\t.balign 4", '\t.include "data/rodata.s"',
          "", '\t.section .data, "aw", %progbits', "\t.balign 4", '\t.include "data/data.s"',
          "", '\t.include "data/bss.s"', ""]
    with open(os.path.join(out, "rom.s"), "w") as f:
        f.write("\n".join(R))
    return linemap


def render(it, syms, mem, comment_for):
    """(body, comment) for an item at its current demotion level."""
    k, lvl = it.kind, it.level
    if k == "raw":
        return raw_text(it, mem), it.comment
    if k == "branch":
        lab = syms.code.get(it.target)
        if lvl == 0 and lab:
            return f"{it.asm} {lab}", ""
        return raw_text(it, mem), f"{it.asm} 0x{it.target:x}"
    if k == "poolload":
        lab = syms.code.get(it.target)
        pool = syms.starts.get(it.target)
        v = mem.u32(it.target)
        eq = (pool.expr if pool is not None and pool.expr else f"0x{v:08x}") if v is not None else ""
        if lvl == 0 and lab:
            m = POOL_LDR_RE.match(it.asm)
            return f"{m.group(1)}\t{m.group(2)}, {lab}", f"={eq}"
        if lvl <= 1:
            return it.asm, f"={eq}"
        return raw_text(it, mem), it.asm
    if k == "data":
        v = mem.u32(it.addr)
        if lvl == 0 and it.expr:
            return f".word {it.expr}", comment_for(v)
        return f".word 0x{v:08x}", comment_for(v)
    if lvl == 0:
        return it.asm, it.comment
    return raw_text(it, mem), it.asm


def build(out):
    r = subprocess.run(["make", "-C", out, "-s", "build/dkp.gba"], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if "--assets-only" in sys.argv:
        # Regenerate everything in a scratch copy (verifying the build there),
        # then copy only assets/ and baserom.gba into the repo. Source files,
        # including any you have edited, are left alone.
        import shutil
        import tempfile
        tmp = tempfile.mkdtemp(prefix="dkp_assets_")
        for f in ("Makefile", "ld_script.ld", "dkp.sha1"):
            shutil.copy(os.path.join(repo, f), tmp)
        shutil.copytree(os.path.join(repo, "tools"), os.path.join(tmp, "tools"),
                        ignore=shutil.ignore_patterns("romtest", "__pycache__"))
        os.makedirs(os.path.join(tmp, "assets"))  # keep the Makefile's assets/ check quiet
        generate(args[0], tmp)
        shutil.rmtree(os.path.join(repo, "assets"), ignore_errors=True)
        shutil.copytree(os.path.join(tmp, "assets"), os.path.join(repo, "assets"))
        shutil.copy(os.path.join(tmp, "baserom.gba"), repo)
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"assets/ written to {repo}")
        return
    generate(args[0], args[1] if len(args) > 1 else repo)


def generate(elf_path, out):
    elf = ELFFile(open(elf_path, "rb"))
    stabs = list(read_stabs(elf))
    mem = Memory(elf)

    rom = os.path.join(out, "baserom.gba")
    subprocess.run([OBJCOPY, "-O", "binary"] + sum((["-j", s] for s in ROM_SECTIONS), []) + [elf_path, rom], check=True)
    base = open(rom, "rb").read()
    print(f"baserom.gba  {len(base)} bytes  sha1 {hashlib.sha1(base).hexdigest()}")

    os.makedirs(os.path.join(out, "maps"), exist_ok=True)
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    mods = build_modules(elf, stabs)
    with open(os.path.join(out, "maps/modules.txt"), "w") as f:
        f.write("# start     end         size     source\n")
        for a, b, n in mods:
            f.write(f"{a:08x}  {b:08x}  {b - a:7x}  {n}\n")
    with open(os.path.join(out, "maps/assets.txt"), "w") as f:
        f.write("# address   included file (from .stab N_SOL)\n")
        seen = set()
        for typ, val, s in sorted(stabs, key=lambda t: t[1]):
            if typ == 0x84 and val >= 0x08000000 and not s.endswith((".s", ".S", ".c", ".h", ".inc")):
                if (val, s) not in seen:
                    seen.add((val, s))
                    f.write(f"{val:08x}  {s}\n")
    nm = subprocess.run([NM, "-n", "-S", elf_path], capture_output=True, text=True, check=True).stdout
    with open(os.path.join(out, "maps/symbols.txt"), "w") as f:
        f.write(nm)

    dump = subprocess.run([OBJDUMP, "-d", "-l", "-m", "armv4t"] + sum((["-j", s] for s in CODE_SECTIONS), []) + [elf_path],
                          capture_output=True, text=True, check=True).stdout
    # Tables inside hand-written asm (e.g. fe_title.s's diddys_chardata): an
    # aligned word in code equal to the exact address of a named symbol is a
    # pointer, not two instructions.
    named = {}
    for ln in nm.splitlines():
        p_ = ln.split()
        if len(p_) >= 3 and p_[-2] not in "aAUw" and not p_[-1].startswith(("$", ".")):
            named[int(p_[0], 16)] = p_[-1]
    extra = set()
    for lo, hi in ((0x08000000, CODE_ROM[1]), TEXT32_VMA):
        for a in range(lo, hi, 4):
            if in_data(a) or HEADER[0] <= a < HEADER[1]:
                continue
            v = mem.u32(a)
            if v and v & 0xFFFF and (v in named or (v & 1 and v - 1 in named)) and Symbols.in_range(v):
                extra.add(a)
    items, labels = collect(dump.splitlines(), mem, extra)
    starts = [it.addr for it in items]
    by_addr = {it.addr: it for it in items}
    syms = Symbols(elf, nm, items, labels, mem)
    global ASSETS
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dwarf2
    _, dies = dwarf2.parse(elf)
    cvars = {}
    for d in dies.values():
        loc = d.attrs.get("location")
        if d.tag == "variable" and isinstance(loc, (bytes, bytearray)) and loc[:1] == b"\x03":
            a = struct.unpack_from("<I", loc, 1)[0]
            if in_data(a):
                cvars[a] = (d.attrs.get("name"), dwarf2.type_name(dies, d.attrs.get("type")),
                            clean_path(d.cu.attrs.get("name", "")))
    ASSETS = AssetNamer(stabs, cvars)
    ASSETS.names = set(syms.data.values())
    import shutil
    shutil.rmtree(os.path.join(out, "assets"), ignore_errors=True)
    data_ptrs = choose_data_pointers(syms, mem)
    data_numeric = set()

    for rnd in range(16):
        linemap = emit(out, mods, items, syms, mem, data_ptrs, data_numeric, elf)
        rc, log = build(out)
        all_errs = re.findall(r"^((?:asm|data)/[^:]+):(\d+): Error: (.*)$", log, re.M)
        # A line that fails to assemble emits no bytes, shifting everything
        # after it, so positional errors may just be knock-on effects. Only
        # act on them once nothing else is failing.
        positional = ("invalid offset", "out of range", "too big")
        firm = [(f, n) for f, n, m in all_errs if not any(x in m for x in positional)]
        errs = firm or [(f, n) for f, n, m in all_errs]
        bad = set()
        if errs:
            bad = {linemap[(f, int(n))] for f, n in errs if (f, int(n)) in linemap}
            unknown = [e for e in errs if (e[0], int(e[1])) not in linemap]
            print(f"round {rnd}: {len(errs)} assembler errors")
            if unknown:
                print("unmapped:", unknown[:10])
                for f_, n_ in unknown[:5]:
                    print(open(os.path.join(out, f_)).read().split("\n")[int(n_) - 1])
                sys.exit(1)
        elif rc != 0:
            print("\n".join(l for l in log.splitlines() if "rror" in l or "undefined" in l)[:4000])
            sys.exit(1)
        else:
            built = open(os.path.join(out, "build/dkp.gba"), "rb").read()
            if built == base:
                lv = {}
                for it in items:
                    key = it.kind if it.level == 0 else f"{it.kind}->demoted"
                    lv[key] = lv.get(key, 0) + 1
                sym_words = sum(1 for it in items if it.kind == "data" and it.level == 0 and it.expr)
                print(f"round {rnd}: MATCH")
                print("  items: " + ", ".join(f"{k} {v}" for k, v in sorted(lv.items())))
                print(f"  symbolic words: {sym_words} in code, {len(data_ptrs) - len(data_numeric)} in data")
                convert_assets(out, mem, syms)
                import shutil
                shutil.rmtree(os.path.join(out, "build"), ignore_errors=True)
                rc, log = build(out)
                built = open(os.path.join(out, "build/dkp.gba"), "rb").read() if rc == 0 else b""
                if built != base:
                    print("\n".join(l for l in log.splitlines() if "rror" in l)[:3000])
                    sys.exit("build from converted assets does not match")
                print("  build from converted assets: MATCH")
                return
            if len(built) != len(base):
                sys.exit(f"round {rnd}: ROM size {len(built)} != {len(base)}: layout changed, not a local mismatch")
            words = set(data_ptrs)
            for k in range(len(base)):
                if built[k] != base[k]:
                    v = rom_to_vma(0x08000000 + k)
                    w = v & ~3
                    if w in words and in_data(v):
                        bad.add(w)
                        continue
                    i = bisect.bisect_right(starts, v) - 1
                    if i >= 0:
                        bad.add(starts[i])
            print(f"round {rnd}: {len(bad)} mismatches")
        progress = False
        for a in bad:
            it = by_addr.get(a)
            if it is not None and it.kind != "raw" and it.level < 2:
                it.level += 1
                progress = True
            elif it is None and a in data_ptrs and a not in data_numeric:
                data_numeric.add(a)
                progress = True
        if not progress:
            print("no progress; giving up")
            print("\n".join(l for l in log.splitlines() if "rror" in l or "undefined" in l)[:4000])
            sys.exit(1)
    sys.exit("did not converge")


if __name__ == "__main__":
    main()

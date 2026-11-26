#!/usr/bin/env python3
"""Minimal DWARF 2 reader for the 2001 GCC 2.9 debug info.

pyelftools and binutils both trip over this file's .debug_info; this reader
only understands what GCC 2.9 emits, which is all we need: types, struct
layouts, variables and functions.

    python3 tools/dwarf2.py ELF [--types | --vars | --structs NAME...]
"""
import struct
import sys

from elftools.elf.elffile import ELFFile

TAGS = {0x01: "array_type", 0x04: "enumeration_type", 0x05: "formal_parameter", 0x0B: "lexical_block",
        0x0D: "member", 0x0F: "pointer_type", 0x11: "compile_unit", 0x13: "structure_type",
        0x15: "subroutine_type", 0x16: "typedef", 0x17: "union_type", 0x18: "unspecified_parameters",
        0x1D: "inlined_subroutine", 0x21: "subrange_type", 0x24: "base_type", 0x26: "const_type",
        0x28: "enumerator", 0x2E: "subprogram", 0x34: "variable", 0x35: "volatile_type", 0x0A: "label"}
ATS = {0x01: "sibling", 0x02: "location", 0x03: "name", 0x0B: "byte_size", 0x10: "stmt_list", 0x11: "low_pc",
       0x12: "high_pc", 0x13: "language", 0x1B: "comp_dir", 0x1C: "const_value", 0x20: "inline", 0x25: "producer",
       0x27: "prototyped", 0x2F: "upper_bound", 0x31: "abstract_origin", 0x38: "data_member_location",
       0x3A: "decl_file", 0x3B: "decl_line", 0x3C: "declaration", 0x3E: "encoding", 0x3F: "external",
       0x40: "frame_base", 0x49: "type", 0x0D: "bit_size", 0x0C: "bit_offset", 0x22: "lower_bound",
       0x33: "accessibility", 0x32: "accessibility", 0x34: "artificial", 0x2A: "return_addr"}


def uleb(d, o):
    r = s = 0
    while True:
        b = d[o]; o += 1
        r |= (b & 0x7F) << s; s += 7
        if b < 0x80:
            return r, o


def sleb(d, o):
    r = s = 0
    while True:
        b = d[o]; o += 1
        r |= (b & 0x7F) << s; s += 7
        if b < 0x80:
            if b & 0x40:
                r -= 1 << s
            return r, o


class DIE:
    __slots__ = ("off", "tag", "attrs", "children", "parent", "cu")

    def __repr__(self):
        return f"<{self.tag} {self.attrs.get('name', '')} @{self.off:#x}>"


def parse(elf):
    info = elf.get_section_by_name(".debug_info").data()
    abbr = elf.get_section_by_name(".debug_abbrev").data()
    dies = {}
    cus = []
    # Abbrev tables here are not zero-terminated; each ends where the next
    # CU's table begins.
    starts, o = [], 0
    while o < len(info):
        length, _, ao = struct.unpack_from("<IHI", info, o)
        starts.append(ao)
        o += 4 + length
    bounds = sorted(set(starts)) + [len(abbr)]
    off = 0
    while off < len(info):
        length, ver, aoff, psize = struct.unpack_from("<IHIB", info, off)
        end = off + 4 + length
        # abbrev table for this CU
        table = {}
        o = aoff
        limit = next(b for b in bounds if b > aoff)
        while o < limit:
            code, o = uleb(abbr, o)
            if code == 0:
                break
            tag, o = uleb(abbr, o)
            ch = abbr[o]; o += 1
            specs = []
            while True:
                at, o = uleb(abbr, o)
                fm, o = uleb(abbr, o)
                if at == 0 and fm == 0:
                    break
                specs.append((at, fm))
            table.setdefault(code, (tag, ch, specs))
        o = off + 11
        stack = []
        cu = None
        prev = prev_specs = None
        while o < end:
            doff = o
            code, o = uleb(info, o)
            if code == 0:
                if stack:
                    stack.pop()
                continue
            if code not in table:
                raise ValueError(f"bad abbrev {code} at {doff:#x} in CU @{off:#x} {cu and cu.attrs.get('name')}; "
                                 f"previous DIE {prev!r} specs {prev_specs}")
            tag, ch, specs = table[code]
            prev, prev_specs = None, specs
            d = DIE()
            d.off, d.tag, d.attrs, d.children = doff, TAGS.get(tag, hex(tag)), {}, []
            d.parent = stack[-1] if stack else None
            for at, fm in specs:
                if fm == 0x01: v = struct.unpack_from("<I", info, o)[0]; o += 4
                elif fm == 0x03: n = struct.unpack_from("<H", info, o)[0]; v = info[o + 2:o + 2 + n]; o += 2 + n
                elif fm == 0x04: n = struct.unpack_from("<I", info, o)[0]; v = info[o + 4:o + 4 + n]; o += 4 + n
                elif fm == 0x05: v = struct.unpack_from("<H", info, o)[0]; o += 2
                elif fm == 0x06: v = struct.unpack_from("<I", info, o)[0]; o += 4
                elif fm == 0x07: v = struct.unpack_from("<Q", info, o)[0]; o += 8
                elif fm == 0x08:
                    e = info.index(b"\0", o); v = info[o:e].decode("latin-1"); o = e + 1
                elif fm == 0x09: n, o = uleb(info, o); v = info[o:o + n]; o += n
                elif fm == 0x0A: n = info[o]; v = info[o + 1:o + 1 + n]; o += 1 + n
                elif fm == 0x0B: v = info[o]; o += 1
                elif fm == 0x0C: v = info[o]; o += 1
                elif fm == 0x0D: v, o = sleb(info, o)
                elif fm == 0x0F: v, o = uleb(info, o)
                elif fm == 0x10: v = struct.unpack_from("<I", info, o)[0]; o += 4
                elif fm == 0x11: v = off + info[o]; o += 1
                elif fm == 0x12: v = off + struct.unpack_from("<H", info, o)[0]; o += 2
                elif fm == 0x13: v = off + struct.unpack_from("<I", info, o)[0]; o += 4
                elif fm == 0x15: v, o = uleb(info, o); v += off
                else:
                    raise ValueError(f"form {fm:#x} at {o:#x}")
                d.attrs[ATS.get(at, hex(at))] = v
            if cu is None:
                cu = d
                cus.append(d)
            d.cu = cu
            if d.parent is not None:
                d.parent.children.append(d)
            dies[doff] = d
            prev = d
            if ch:
                stack.append(d)
        off = end
    return cus, dies


def member_offset(m):
    loc = m.attrs.get("data_member_location")
    if isinstance(loc, (bytes, bytearray)) and loc and loc[0] == 0x23:  # DW_OP_plus_uconst
        return uleb(loc, 1)[0]
    return loc


def type_name(dies, ref, depth=0):
    if ref is None:
        return "void"
    t = dies[ref]
    n = t.attrs.get("name")
    if t.tag in ("base_type", "typedef") and n:
        return n
    if t.tag in ("structure_type", "union_type", "enumeration_type"):
        return f"{t.tag.split('_')[0]} {n or '<anon>'}"
    if t.tag == "pointer_type":
        return type_name(dies, t.attrs.get("type"), depth + 1) + "*"
    if t.tag in ("const_type", "volatile_type"):
        return t.tag.split("_")[0] + " " + type_name(dies, t.attrs.get("type"), depth + 1)
    if t.tag == "array_type":
        dims = "".join(f"[{c.attrs.get('upper_bound', -1) + 1}]" for c in t.children if c.tag == "subrange_type")
        return type_name(dies, t.attrs.get("type"), depth + 1) + dims
    if t.tag == "subroutine_type":
        return "func"
    return t.tag


def type_size(dies, ref):
    if ref is None:
        return 0
    t = dies[ref]
    if "byte_size" in t.attrs:
        return t.attrs["byte_size"]
    if t.tag == "pointer_type":
        return 4
    if t.tag in ("typedef", "const_type", "volatile_type"):
        return type_size(dies, t.attrs.get("type"))
    if t.tag == "array_type":
        n = 1
        for c in t.children:
            if c.tag == "subrange_type":
                n *= c.attrs.get("upper_bound", -1) + 1
        return n * type_size(dies, t.attrs.get("type"))
    return 0


def main():
    elf = ELFFile(open(sys.argv[1], "rb"))
    cus, dies = parse(elf)
    mode = sys.argv[2] if len(sys.argv) > 2 else "--vars"
    if mode == "--vars":
        for d in dies.values():
            if d.tag == "variable" and isinstance(d.attrs.get("location"), (bytes, bytearray)):
                loc = d.attrs["location"]
                if loc and loc[0] == 0x03:  # DW_OP_addr
                    a = struct.unpack_from("<I", loc, 1)[0]
                    print(f"{a:08x} {type_size(dies, d.attrs.get('type')):6d} {d.attrs.get('name')}: "
                          f"{type_name(dies, d.attrs.get('type'))}  [{d.cu.attrs.get('name')}]")
    elif mode == "--structs":
        want = set(sys.argv[3:])
        seen = set()
        for d in dies.values():
            if d.tag in ("structure_type", "union_type") and d.attrs.get("name") and (not want or d.attrs["name"] in want):
                if d.attrs["name"] in seen or not d.children:
                    continue
                seen.add(d.attrs["name"])
                print(f"{d.tag.split('_')[0]} {d.attrs['name']} {{  // {d.attrs.get('byte_size')} bytes")
                for m in d.children:
                    if m.tag == "member":
                        off_ = member_offset(m); print(f"    /* {off_ if off_ is not None else -1:#05x} */ {type_name(dies, m.attrs.get('type'))} {m.attrs.get('name')};")
                print("};")


if __name__ == "__main__":
    main()

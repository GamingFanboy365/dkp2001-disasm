#!/usr/bin/env python3
"""Static reachability over the source: what can never run or be shown.

    python3 tools/reachability.py [--path NAME]

Follows every call, branch, fall-through, literal pool, pointer and jump table
from _start through asm/ and data/ (the original build: .ifdef FIXES branches
are skipped) and lists the code and data nothing can reach. With --path NAME it
prints the chain of references that reaches NAME. Used for UNUSED.md.

Limits: code copied to RAM and called through computed addresses (the sound
driver's ARM code) and data reached by pointer arithmetic (the smaller
__spr_*_01/_02 sprite versions) look unreachable but are not; they are left
out of the report.
"""
import collections
import glob
import re
import sys
import re

ANCHOR = re.compile(r'^([A-Za-z_][\w.]*):\s+@ ([0-9a-f]{8})')
LABEL = re.compile(r'^([A-Za-z_][\w.]*|\d+):')


def size_of(s, mode):
    if s.startswith('.word') or s.startswith('.inst') or s.startswith('.4byte'):
        return 4 * (s.count(',') + 1)
    if s.startswith('.hword') or s.startswith('.2byte'):
        return 2 * (s.count(',') + 1)
    if s.startswith('.byte'):
        return s.count(',') + 1
    if s.startswith('.space'):
        return int(s.split()[1], 0)
    if s.startswith('.asciz') or s.startswith('.ascii'):
        body = s[s.index('"') + 1:s.rindex('"')]
        n = len(body.encode().decode('unicode_escape'))
        return n + (1 if s.startswith('.asciz') else 0)
    if s.startswith('.'):
        return 0
    if mode == 'arm':
        return 4
    return 4 if re.match(r'^bl\s', s) else 2


def addresses(lines):
    """[(line_index, address or None, mode)]"""
    out, addr, mode, skip = [], None, 'thumb', 0
    for i, l in enumerate(lines):
        s = l.split('@')[0].strip()
        if s.startswith('.ifdef FIXES'):
            skip = 1; out.append((i, addr, mode)); continue
        if s.startswith('.else') and skip:
            skip = 0; out.append((i, addr, mode)); continue
        if s.startswith('.endif'):
            skip = 0; out.append((i, addr, mode)); continue
        if skip:
            out.append((i, None, mode)); continue
        m = ANCHOR.match(l)
        if m:
            addr = int(m.group(2), 16)
        if s in ('.arm', '.thumb'):
            mode = s[1:]
        if s.startswith('.balign') and addr is not None:
            addr = (addr + 3) & ~3
        out.append((i, addr, mode))
        if addr is not None and s and not LABEL.match(s) and not s.startswith('.set'):
            addr += size_of(s, mode)
    return out
TOKEN = re.compile(r'\b([A-Za-z_][\w.]*)\b')

def parse():  # noqa: C901
    nodes = {}          # name -> dict(file, kind, line, size_lines)
    owner = {}          # label -> node it belongs to
    refs = collections.defaultdict(set)
    files = sorted(glob.glob('asm/**/*.s', recursive=True) + glob.glob('asm/**/*.S', recursive=True) + glob.glob('data/*.s'))
    files = [f for f in files if not f.endswith('fixes.s')]
    per_file = {}
    for f in files:
        L = open(f).read().split('\n')
        is_data = f.startswith('data/')
        cur = None; skip = 0; body = []; last_stop = True
        for i, l in enumerate(L):
            s = l.split('@')[0].rstrip()
            st = s.strip()
            if st.startswith('.ifdef FIXES'): skip = 1; continue
            if st.startswith('.else') and skip: skip = 0; continue
            if st.startswith('.endif'): skip = 0; continue
            if skip: continue
            m = LABEL.match(l)
            if m:
                name = m.group(1)
                local = bool(re.match(r'^L_[0-9a-f]{8}$', name)) and not is_data
                if not local:
                    # code falls through into the next label unless the last
                    # instruction was an unconditional jump or return
                    if cur and not is_data and not last_stop:
                        refs[cur].add(name)
                    cur = name
                    nodes.setdefault(name, dict(file=f, kind='data' if is_data else 'code', line=i + 1))
                owner[name] = cur or name
                continue
            ms = re.match(r'^\s*\.set\s+([A-Za-z_][\w.]*),', st)
            if ms:
                owner[ms.group(1)] = cur; nodes.setdefault(ms.group(1), dict(file=f, kind='data' if is_data else 'code', line=i + 1)); continue
            if st and not st.startswith(('.thumb', '.arm', '.balign', '.syntax', '.global', '.section')):
                last_stop = bool(re.match(r'^(b|bx|bal)\s|^pop\s.*\bpc\b|^ldm\w*\s.*\bpc\b|^(mov|add|sub)\w*\s+pc,|^\.(word|byte|hword|inst|asciz|ascii|space|incbin)', st))
            if cur and st and not st.startswith(('.thumb', '.arm', '.balign', '.syntax', '.global', '.section')):
                if st.startswith('.incbin'):
                    nodes[cur].setdefault('assets', []).append(st.split('"')[1]); continue
                for t in TOKEN.findall(st.split('\t', 1)[1] if '\t' in st else st):
                    refs[cur].add(t)
    # resolve tokens to owner nodes
    edges = collections.defaultdict(set)
    for n, ts in refs.items():
        for t in ts:
            if t in owner and owner[t] != n:
                edges[n].add(owner[t])
    return nodes, owner, edges

def reachable(edges, roots):
    seen = set(); stack = list(roots)
    while stack:
        n = stack.pop()
        if n in seen: continue
        seen.add(n); stack.extend(edges.get(n, ()))
    return seen



def node_sizes():
    size = {}
    for f in source_files():
        L = open(f).read().split('\n')
        st = [(a, LABEL.match(L[i]).group(1)) for i, a, m in addresses(L)
              if a is not None and LABEL.match(L[i]) and not LABEL.match(L[i]).group(1).isdigit()]
        for (a, n), (b, _) in zip(st, st[1:]):
            if b >= a:
                size.setdefault(n, b - a)
    return size


def source_files():
    files = sorted(glob.glob('asm/**/*.s', recursive=True) + glob.glob('asm/**/*.S', recursive=True) + glob.glob('data/*.s'))
    return [f for f in files if not f.endswith('fixes.s')]


def main():
    nodes, owner, edges = parse()
    if '--path' in sys.argv:
        target = sys.argv[sys.argv.index('--path') + 1]
        par = {'_start': None}
        q = collections.deque(['_start'])
        while q:
            n = q.popleft()
            for m in edges.get(n, ()):
                if m not in par:
                    par[m] = n
                    q.append(m)
        if target not in par:
            print(f'{target}: unreachable' if target in nodes else f'{target}: no such label')
            return
        p = []
        while target:
            p.append(target)
            target = par[target]
        print(' <- '.join(p))
        return
    R = reachable(edges, ['_start'])
    size = node_sizes()
    fam = lambda n: re.sub(r'(_(char|info|frames|plt|pal|chars|map|num_chars|map_size_x|map_size_y|data|image)(_\d+)?)$', '', n)
    groups = collections.defaultdict(list)
    for n, info in nodes.items():
        if info['kind'] != 'data' or info['file'] == 'data/bss.s' or re.match(r'^_[0-9a-f]{8}$', n) or re.match(r'^__spr_.*_0[12]$', n):
            continue
        groups[fam(n)].append(n)
    print('Unreferenced data (families with no reachable member):')
    rows = [(sum(size.get(n, 0) for n in ns), k) for k, ns in groups.items() if not any(n in R for n in ns)]
    for tot, k in sorted(rows, reverse=True):
        if tot >= 64:
            print(f'  {tot:7d}  {k}')
    print('Unreferenced code (game code; libraries and the RAM-resident sound driver left out):')
    for n, info in sorted(nodes.items(), key=lambda kv: kv[1]['file']):
        if (info['kind'] == 'code' and n not in R and not re.match(r'^_[0-9a-f]{8}$', n)
                and 'audio/code' not in info['file'] and not info['file'].startswith('asm/lib/') and size.get(n, 0) >= 4):
            print(f"  {size.get(n, 0):5d}  {info['file']}: {n}")


if __name__ == '__main__':
    main()

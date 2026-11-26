# Diddy Kong Pilot (2001) disassembly

A disassembly of the 2001 Rare build of *Diddy Kong Pilot* for the Game Boy Advance
(ROM header `DK-PILOT`, maker `01`, game code `RARE`), produced from an unstripped debug ELF.

This repo contains **no ROM, no ELF and no game assets** (graphics, sound, level data). Bring your
own copy of the ELF; the tools extract everything else from it.

## What the ELF gives us

The ELF is a debug build with nearly everything a disassembly needs:

| Info | Source in ELF | Used for |
|---|---|---|
| ~42k symbols (functions, globals, local labels, constants) | `.symtab` | names in listings, `maps/symbols.txt` |
| Address range of every C file | `.debug_aranges` | splitting code into modules |
| Line numbers for every C instruction | `.debug_line` | `@ src/file.c:123` annotations |
| Address of every hand-written `.s` file | `.stab` N_SO | splitting assembly modules |
| ROM address of every included graphics file (`.spr`, `.pal`, `.map`, `.hex`) | `.stab` N_SOL | `maps/assets.txt` |
| Compiler | DWARF producer | `GNU C 2.9-arm-000512` (Nintendo SDK GCC) |

The source tree had about 60 C files (game logic, actors, menus) under `src/`, hand-written
ARM/Thumb assembly for the title screens (`src/title/*.s`) and the sound driver
(`src/audio/code/audio.S`), plus newlib and libgcc.

`objcopy` of the ELF's loadable sections gives a 5,080,644-byte ROM with a valid header checksum:

```
sha1 6a76def610829ac1502afb58740e38b5e6926b3d  baserom.gba
```

## Building

Requirements: `arm-none-eabi-binutils`, `make`, Python 3, `pyelftools`.

```bash
sudo apt-get install binutils-arm-none-eabi make
```

```bash
pip install pyelftools
```

First extract the game's assets (graphics, sound, level data) from your own ELF into `assets/`.
This takes about 30 seconds and doesn't touch any source files:

```bash
python3 tools/dkp_split.py path/to/Diddy_Kong_Pilot_2001.elf --assets-only
```

Then build and check that the rebuilt ROM is byte-identical:

```bash
make compare
```

Expected output: `build/dkp.gba: OK` (sha1 `6a76def610829ac1502afb58740e38b5e6926b3d`).

To regenerate *all* the source from the ELF (this overwrites `asm/`, `data/`, `assets/` and
`maps/`, including any edits):

```bash
python3 tools/dkp_split.py path/to/Diddy_Kong_Pilot_2001.elf
```

### Just want a playable .gba?

`tools/elf2gba.py` converts the ELF straight to a ROM. It uses only the Python standard library,
with no ARM toolchain needed:

```bash
python3 tools/elf2gba.py Diddy_Kong_Pilot_2001.elf dkp2001.gba
```

## Layout

```
rom.s              top-level file: includes every module in ROM order
asm/src/...        one assembly file per original source file (C modules are named foo.c.s)
asm/lib/...        newlib / libgcc
data/text_sprites.s front-end sprite data that was linked into .text after the sound driver
data/rodata.s      .rodata: labels, pointers, small tables and strings inline; the rest from assets/
data/data.s        .data: same
data/bss.s         .bss (EWRAM) and .bss32 (IWRAM), labelled
assets/            (not in git) every larger block of data as its own file, extracted from your ELF
ld_script.ld       section layout (flows; .text32 runs from IWRAM at 0x03000000)
maps/modules.txt   address range -> source file, for all code
maps/assets.txt    ROM address -> original asset filename
maps/symbols.txt   nm -n -S output of the original ELF
tools/dkp_split.py generator for asm/, data/, assets/, maps/, rom.s
tools/gfx.py       PNG / PAL / WAV <-> binary converters (used by the build; stdlib only)
tools/dwarf2.py    reader for this ELF's DWARF 2 (types, structs, variables)
tools/export_preview.py  renders sprites/backgrounds/palettes to viewable PNGs
tools/elf2gba.py   standalone ELF -> .gba converter
tools/romtest/     headless mGBA runner (screen hashes, screenshots, RAM dumps)
tools/reloc_test.py
```

## Pointers are symbolic

Code and data can be edited and moved. Every address the game stores is written as a symbol,
never as a number:

```asm
	ldr	r2, _0800632c	@ =__text32_lma
	...
_0800632c:
	.word __text32_lma
```

```asm
tab_classes:  @ 0816acac
	.byte 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
	.word init_player+1
	.word act_player+1
```

- **Literal-pool loads** are emitted as `ldr rX, _<addr>`, so the assembler computes the offset;
  the comment shows the loaded value.
- **Pool words, jump tables and data pointers** are written as `label`, `label+offset` or
  `label+1` (for Thumb function pointers).
- **Data in `.rodata`/`.data`**: a word counts as a pointer if it points exactly at a named symbol
  or function. It also counts if it sits in a pointer table: a one-word object, or an object that
  is mostly pointers. Finally, it counts if it is a field that most objects of its family hold at
  the same offset (e.g. every `__chr_*` tile set starts with a pointer to `__chr_dkp`). Tile,
  sample and music data that only *look* like addresses stay as bytes.
- **The linker script** has no fixed addresses after `.boot`. Sections flow one after another, so
  an unmodified build lands on the original addresses, and anything that grows pushes what follows.

### Relocation test

`make compare` only shows the labels land on the original addresses. To show nothing still
depends on a hard-coded address, build with padding inserted and play the game:

```bash
make shifted SHIFT_CODE=0x1000
```

```bash
make shifted SHIFT_DATA=0x1000
```

```bash
python3 tools/reloc_test.py tools/romtest/romtest
```

`reloc_test.py` first plays a front-end tour: it quits a race into the title screen, cycles every
game mode, every character and the world list, then starts a race. It then starts each of the 40
tracks from the debug menu. Each run uses the same inputs on the original and both shifted ROMs,
and the screen is compared every 25–50 frames. Result: the **front-end is identical, and 40/40
tracks pass**. 39 tracks are identical, and Jungle 03 differs only because of an original-game
out-of-bounds read (below), whose result depends on which bytes follow the track's data.

## Assets

Every byte of the ROM lives in a named source file: code in `asm/`, labels and pointers in `data/`,
and every data block of 64 bytes or more in `assets/`, named after its symbol. `assets/` holds the
game's own graphics and sound, so it isn't committed; `--assets-only` extracts it from your ELF. Title-screen files
keep the names recorded in the debug info (`src/title/gfx/game_mode_icons/bookicon.spr` →
`assets/title/gfx/game_mode_icons/bookicon/`). There are 1,838 asset files; 98% of the data bytes
are in them.

Where the format is known, assets are stored in editable formats and converted back at build time
(`tools/gfx.py`, into `build/assets/`). Every conversion is checked to give back the exact bytes:

| Format | Files | What |
|---|---|---|
| `*.8bpp.png`, `*.4bpp.png` | 776 | Tile sheets: title/menu sprites (bit depth and width from each sprite's OAM pieces), menu and title backgrounds. Indexed PNG; the pixel values are what the game uses, and the embedded palette is for viewing. |
| `*.rgb555.png` | 1 | The 16-bit full-screen bitmap (`CharSelect_image`). |
| `*.pal` | 114 | JASC palettes, 16 or 256 colours. |
| `*.wav` | 187 | Instrument samples: 8-bit signed PCM, at the rate from their `Sampinf` record, with the loop point in a `smpl` chunk. |
| `*.bin` | 761 | Formats not yet converted: in-game sprites (run-length compressed 4bpp, see below), level tile banks and maps, music sequences, sprite layout records, tables. |

Editing rules: keep PNGs indexed (palette mode) with the same width/height multiple of 8, and keep
WAVs 8-bit mono. A bigger or smaller asset is fine, because pointers are symbolic and everything
after it moves.

To look at everything as the game draws it, run:

```bash
python3 tools/export_preview.py baserom.gba maps/symbols.txt preview
```

This renders composed sprite frames, every in-game sprite (decoded), menu/title backgrounds from
their tilemaps, every level's course, distant ground and sky, palette swatches, and the songs as
MIDI files.

### Formats worked out so far

- **Front-end sprites** (`*_frames`, `*_info_N`, `*_char_N`, `*_plt`). A frame record is 16 bytes:
  tile pointer, size in words, piece count, info pointer. Each info piece is 12 bytes: relative y
  and x, OAM attr0/attr1 high bytes (shape, size, 8bpp, flips), the tile advance, and w/h.
- **In-game sprites** (`__spr_*`, `__spr_*_01`, `_02`). These are a chain of resolution levels,
  and the game picks one by distance (`spr_draw`). Level header: +0 offset of the tile-block table,
  +4 level length in 16-byte units, +14 per-frame offsets to piece lists. A piece list is a u16
  count followed by 6-byte OAM pieces. A tile block is a u16 tile count, then a run-length stream
  of u16 control words: bit 7 set copies `(c&0x7f)+1` halfwords, clear repeats byte `c>>8`. A
  zero word ends it (`spr_update_vram`).
- **Menu backgrounds** (`<name>_plt`, `_num_chars`, `_chars`, `_map_size_x/y`, `_map`). 8bpp tiles
  with u16 map entries. `diddytitle*` are 64×64 rotation backgrounds with byte-sized map entries.
- **Levels** (`tab_levels`, 9 words per level: palette, ground tiles, sky tiles, distant-ground
  map, course map, sky map, sky gradient, object placements, AI network). See `bg_init` in
  `background.c`; the display is mode 2, with two rotating/scaling layers.
  - Tile sets (`__chr_<level>_lvl`, `__chr_<level>_sky`) are a pointer to the shared bank
    `__chr_dkp` (a u16 count, then 5,196 8bpp tiles), a u16 count (≤ 256), and u16 bank indices.
  - Maps (`__map_<level>_lvl|gnd|sky`) are a u16 width and height in metatiles, then u16 metatile
    numbers. A metatile is 4×4 tiles: 8 u16 in `__frs_dkp`, each holding two 1-byte tile numbers.
    `_lvl` is the 128×128-tile (1024×1024 px) course the 3D floor is drawn from.
- **Music** (`tune_list` → `Songinf {tracks, ppqn, track pointers, vmap, samplist}`). Tracks use
  the sound driver's own opcodes (`midi_commands` in `audio.S`):
  - 0: tempo (3 bytes, µs per quarter note)
  - 1–4: delay (1–4 byte ticks)
  - 5/6: note on/off (channel, note, velocity)
  - 7: controller
  - 8: program change
  - 9: channel pressure
  - 10: pitch wheel
  - 11: end of track
  `export_preview.py` writes them out as standard MIDI files.

## Bug fixes

See [FIXES.md](FIXES.md): `make fixed` builds the fixed ROM and `make patch` makes an IPS patch.

## Bugs found so far

- **Jungle 03: computer players read past their waypoint network.** `ai_steer` (act_comp_player.c)
  indexes past the end of `__net_jungle_03` (a 0x26-byte network) into the next data, which is
  `english_table`, the text-pointer table. It then uses halves of those pointers as waypoint
  coordinates. The AI on that track is steering by garbage.
- **Unfinished tracks.** Desert 00, 02 and 03 have placeholder ground: grids stamped with their slot
  names "S3-2", "R4-1" and "R5-3". Jungle 03 is a maze whose AI network is a stub (see above).
- **Asserts trap.** Failed `ASSERT`s print through `AGBPrintf` and then hit an `0xEFFF` undefined
  instruction (223 sites). On hardware or an emulator without a debugger attached, that's a hang
  or crash rather than a message.
- **newlib stdio state is in ROM.** `impure_data` was linked into `.data`, which sits in ROM in
  this build, so `__sinit` re-initialises stdio on every debug print (its writes are dropped).
  Harmless to gameplay, but every `printf` pays for it.

## Status / roadmap

- [x] Rebuild ROM from ELF, map every code byte to its original source file
- [x] Annotated per-module listings with symbols, line numbers, pools, and jump tables
- [x] Asset map with original filenames
- [x] Reassemblable source with `make compare` producing a byte-identical ROM
- [x] Standalone Python ELF -> .gba converter
- [ ] Data/code separation for the remaining tables inside `audio.S` and `tab_trig.s`
- [x] Symbolic pointers in code and data, flowing linker layout, relocation test 40/40
- [x] Headless mGBA test harness (`tools/romtest`)
- [x] Split all data into named asset files, extracted from your own ELF (not committed)
- [x] Editable formats for sprites/backgrounds (PNG), palettes (.pal), samples (.wav)
- [x] Front-end sprite data that was hidden in the audio.S code range is now data, with symbolic
      pointers; tables inside hand-written title asm are now symbolic too
- [x] Decode level graphics (rendered by `export_preview.py`) and music (exported as MIDI)
- [ ] Editable formats for level maps and music (round-trip through the build)
- [ ] Editable format for in-game sprites (needs an encoder that reproduces the original RLE)
- [ ] Matching decompilation of the C modules. The compiler is the same GCC 2.9 lineage
      `agbcc` derives from, and line tables give the source line for every instruction.
- [ ] Bug-fix build of the game, distributed as an `.ips` patch against the ELF-derived ROM

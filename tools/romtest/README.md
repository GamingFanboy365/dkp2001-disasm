# romtest

Runs a ROM headlessly in [mGBA](https://mgba.io) with scripted button presses and prints a hash
of the screen every N frames. Two ROMs that behave identically print identical hashes. That's
how the relocation test (`tools/reloc_test.py`) checks shifted builds, and how bug fixes can be
checked for side effects.

```
romtest ROM FRAMES EVERY [--ppm PREFIX] [FRAME:KEY[:HOLD] ...]
```

- `KEY` is `A B SELECT START RIGHT LEFT UP DOWN R L`, held for `HOLD` frames (default 6).
- `--ppm PREFIX` also saves each checkpoint as `PREFIX_<frame>.ppm`.
- `RAM_OUT=file` in the environment dumps EWRAM (256 KiB) then IWRAM (32 KiB) after the last frame;
  with `RAM_VIDEO` also set, palette RAM, VRAM and OAM follow.
- The last line, `stores-to-rom N`, counts writes the game made to ROM addresses.

Example: boot the debug menu, start Beach 00, and hold A to fly.

```bash
./romtest ../../baserom.gba 1500 100 200:START 500:A:900
```

## Building

mGBA is built as a static library with every frontend and optional dependency turned off. You
need mGBA source, `cmake`, `ninja` and a C compiler:

```bash
cmake -G Ninja -S path/to/mgba -B path/to/mgba/build -DCMAKE_BUILD_TYPE=Release -DBUILD_QT=OFF -DBUILD_SDL=OFF -DBUILD_STATIC=ON -DBUILD_SHARED=OFF -DBUILD_GL=OFF -DBUILD_GLES2=OFF -DBUILD_GLES3=OFF -DUSE_FFMPEG=OFF -DUSE_LIBZIP=OFF -DUSE_MINIZIP=OFF -DUSE_PNG=OFF -DUSE_SQLITE3=OFF -DUSE_LUA=OFF -DUSE_ELF=OFF -DUSE_EPOXY=OFF -DUSE_DISCORD_RPC=OFF -DUSE_EDITLINE=OFF -DUSE_LZMA=OFF -DUSE_ZLIB=OFF -DENABLE_SCRIPTING=OFF -DM_CORE_GB=OFF -DBUILD_LTO=OFF
```

```bash
ninja -C path/to/mgba/build
```

```bash
make -C tools/romtest MGBA_SRC=path/to/mgba MGBA_BUILD=path/to/mgba/build
```

The Makefile copies the exact `-D` defines libmgba was built with. Without them `struct mCore`
has a different layout and the program crashes on its first call.

## Execution coverage (`cover`)

`cover.c` is romtest plus an execution hook. It ORs every executed instruction address
(ROM and IWRAM code) into the bitmap file `$COVER`, so many runs accumulate into one picture.
That's how [UNUSED.md](../../UNUSED.md) tells code that ran from code that never did. It needs
three small hooks in mGBA (instruction execution, loads and stores):

```bash
patch -p1 -d path/to/mgba < tools/romtest/mgba-trace-hooks.patch
```

```bash
ninja -C path/to/mgba/build
```

Then build `cover` like romtest, with `cover.c` instead of `romtest.c`, and run it with
`COVER=coverage.bin`. The hooks are null unless a program sets them, so the patched library
behaves exactly like the original.

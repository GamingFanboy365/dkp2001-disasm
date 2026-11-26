# Bug fixes

Fixes live in the assembly behind `.ifdef FIXES`, next to the original code they replace, so the
normal build stays byte-identical to the original game.

```bash
make fixed
```

```bash
make patch
```

- `make fixed` builds `build_fixed/dkp.gba`.
- `make patch` writes `build_fixed/dkp2001_fixes.ips`, an IPS patch for the ROM made from the
  2001 ELF (`tools/elf2gba.py`, sha1 `6a76def610829ac1502afb58740e38b5e6926b3d`).
- `tools/make_ips.py apply` can apply it without other tools.

## Conventions

- Each fix has a short id (`FIX "farm-start-slots"`) and a comment explaining the bug.
- Keep a fix the same size as the code it replaces (`.fill` to pad), so nothing after it moves
  and the IPS stays a few bytes. The build is relocatable, so a fix that needs more room can
  grow; the game still works, but the patch then rewrites most of the ROM. Moving larger new
  code to the end of the ROM keeps the patch small.
- Check a fix with `tools/romtest` (play the affected track or menu) and run
  `tools/reloc_test.py` to make sure nothing else changed.

## Fixes

| Id | Bug | Fix |
|---|---|---|
| `farm-start-slots` | Starting the **Farm 02** track (debug menu) hangs on a black screen. Its level has six start positions (slots 0–5); `init_start_pos` (act_startpos.c:31) asserts `idx < 4` and the assert traps. | Start positions beyond the four racers are ignored (the object is freed, as for the others). |

## Known bugs not fixed yet

- **Jungle 03 AI**: `ai_steer` reads past the end of the track's 0x26-byte waypoint network
  (`__net_jungle_03`) into the text-pointer table that follows.
- **Grip grab weapon**: `act_weapon_grip_grab` reads through a null pointer (seen on track 24).
- **Asserts hang**: 223 assert sites print through AGBPrint and then execute `0xEFFF`, an
  undefined instruction. Without a debugger that is a hang.
- **stdio in ROM**: newlib's `impure_data` was linked into ROM, so every debug `printf`
  re-initialises stdio and the assert message path runs on garbage state.

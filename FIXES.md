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
| `asserts` | A failed `ASSERT` (223 sites) prints through `AGBPrintf` and then executes `0xEFFF`, an undefined instruction, so the game hangs. The print itself corrupts memory, because newlib's stdio state (`impure_data`) was linked into ROM and can't be initialised. | Failed asserts are skipped, as in a release build, and the game carries on. Each block becomes a branch to its continuation, padded to the original size; the padding holds the small helper routines of the fixes below. |
| `grip-grab-null` | The **grip grab** weapon (`act_weapon_grip_grab`) keeps positioning itself on its target after the target is gone, and spawns its trail at its parent when there is none. Both read through a null pointer (from BIOS memory), giving a garbage sprite and particle position. Seen on track 24. | If the target is gone, the weapon ends: its sound stops and it is freed, using the function's own exit path. Without a parent, the trail spawns at the weapon. |
| `ai-routes` | Each computer player follows the AI route numbered after it (`o+156/o+160` = player number). 29 of the 40 courses have a one-route network (by map name: all of Keep, Lake, Swamp and Jungle, Desert 00–02, Beach 02, Lava 01–02, Snow 02–03, Farm 01, 02 and 04, Haunted 02–03), so players 1–3 read past the network and steer by whatever follows; on **Jungle 03** that's the text-pointer table. | `ai_steer` uses route 0 when the network has fewer routes than the player number (it is clamped where routes are used, because players are set up before the level's network is loaded). |

All four keep their code the same size, so the patch only touches the changed bytes (about 5 KB).

### Testing done

- **Bug scan:** `tools/romtest` with `PROBLEMS=1` plays the front-end tour and all 40 tracks, and
  reports every illegal instruction and every access to unmapped memory. The original has the
  Farm 02 hang and the grip-grab null reads. The fixed ROM has none (apart from newlib stdio
  writes to ROM, which are harmless).
- **Nothing else changes:**
  - `farm-start-slots`, `asserts` and `grip-grab-null` only run when the bug happens. With those
    three, the fixed ROM plays frame-for-frame identically to the original on the front-end tour
    and every track except Farm 02.
  - `ai-routes` runs every frame, so it adds a few CPU cycles. `game_process` samples `VCOUNT`
    between stages, so the simulation depends on how long each frame takes, and any extra cycles
    change exact replays. (A test build with the same extra cycles and no logic change diverges
    the same way.)
  - Its logic is checked directly instead: on a course with enough routes it reads exactly the
    same route data as the original, plus the route count.
- **Relocation:** `python3 tools/reloc_test.py tools/romtest/romtest --fixed` passes on the
  front-end and **40/40 tracks with no exceptions**. Jungle 03, the original's one exception, now
  plays identically when code or data move, so its AI no longer depends on stray memory.

## Known bugs not fixed yet

- **No AI network at all**: Beach 03, Farm 03 (the course loaded by the Farm 02 slot) and
  Haunted 01 have a network with zero routes, so even route 0 reads the next level's data. A
  proper fix needs waypoints for those tracks.
- **Unfinished tracks**: Desert 00, 02 and 03 have placeholder ground (see the README).
- **stdio in ROM**: harmless now that failed asserts don't print, but debug `printf`s still
  re-initialise stdio every time.

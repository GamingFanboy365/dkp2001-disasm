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
- `make patch` writes `build_fixed/dkp2001_fixes.ips` and copies it to
  `patches/dkp2001_fixes.ips`, which is committed. It's an IPS patch for the ROM made from the
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
| `race-music` | The races are silent. `game_init` stops the menu music and nothing starts any other, although the ROM has six course themes (`tune_list`) and `act_hud.c` already speeds the music up by 14% when the final-lap banner shows. | `game_init` starts the course's theme instead (table `race_tunes` in `asm/fixes.s`): Beach → beach, Lava → lava, Snow → snow, K. Rool's Keep → castle, Swamp → bayou, Haunted → haunted. Worlds without a theme borrow one: Lake → beach, Farm and Jungle → bayou, Desert → lava. Edit the table to change them. |
| `fe-camera-pan` | Starting a race from the **front-end** hangs or crashes on most courses, **Dog Fights** included. A front-end start plays a camera fly-in that `act_camera.c` reads from the course's AI network, taking it to be the sixth route (`campan_load2`). Only six courses have a six-route network with a real fly-in path (Beach 00, Lava 00, Snow 00, Farm 00, Farm 05, Haunted 00). On every other course the game reads route data or garbage as a path of hundreds of points into a 32-point buffer (`pts`), which overwrites RAM, including `game_level`, the object pointers and the sound driver's state. It then traps in `campan_start_seg` ("pts[cur_pt].segs != 0") or the sound driver, or jumps to garbage. 9 of 20 front-end race starts tested hang. | The fly-in path is used only when the network has six routes. Otherwise the camera does the normal race-start pan, which the debug menu uses on every course. |
| `timing-meter` | The row of **stars and circles along the bottom of the screen** in races. It's the developers' CPU-time meter (game.c:274–298). `game_process` samples `VCOUNT` after each stage of the frame and puts a star (sprite tile 7) on the bottom row at the x position of that scanline, plus reference stars and circles (tile 11) at fixed positions. It writes straight into OAM slots 100–103 and 120–127, over any real sprites there. | The meter isn't drawn. The `VCOUNT` sampling stays, because the game's timing depends on it. |

All but `race-music` keep their code the same size. `race-music` adds 84 bytes of new code and
data in a `.fixes` section after all the game's data (`asm/fixes.s`), reached through a
trampoline in an assert block's dead space, because the end of the ROM is out of `bl` range. So
nothing moves, and the patch only touches the changed bytes (about 5 KB).

### Testing done

- **Bug scan:** `tools/romtest` with `PROBLEMS=1` plays the front-end tour and all 40 tracks, and
  reports every illegal instruction and every access to unmapped memory. The original has the
  Farm 02 hang and the grip-grab null reads. The fixed ROM has none (apart from newlib stdio
  writes to ROM, which are harmless).
- **Nothing else changes:**
  - `farm-start-slots`, `asserts` and `grip-grab-null` only run when the bug happens. With those
    three, the fixed ROM plays frame-for-frame identically to the original on the front-end tour
    and every track except Farm 02.
  - `ai-routes` (a few cycles more) and `timing-meter` (a few hundred fewer) change how long
    each frame takes. `game_process` samples `VCOUNT` between stages, so the simulation depends
    on frame timing, and any change in cycles changes exact replays. (A test build with the
    same extra cycles and no logic change diverges the same way.)
  - Their logic is checked directly instead. On a course with enough routes, `ai-routes` reads
    exactly the same route data as the original, plus the route count. `timing-meter` only
    skips OAM writes; in screenshots the bottom-row markers are gone and nothing else changes.
  - `fe-camera-pan` only runs when a race starts from the front-end; see the front-end race
    starts below.
- **Music:** recording mGBA's sound output (`AUDIO_OUT=` in `tools/romtest`), races on every
  world are 2–5× louder with the fix. Reading `audio_cur_tune` mid-race shows the original has
  no tune (-1) and the fixed ROM has the course's tune.
- **Front-end race starts:** 20 scripted starts from the front-end (five game modes, four
  courses each, Dog Fights included). Each runs about 45 seconds into the race. The original hangs
  on 9 of them; the fixed ROM runs all 20 with no faults.
- **Relocation:** `python3 tools/reloc_test.py tools/romtest/romtest --fixed` passes on the
  front-end and **40/40 tracks with no exceptions**. Jungle 03, the original's one exception, now
  plays identically when code or data move, so its AI no longer depends on stray memory.

## Known bugs not fixed yet

- **Dog Fights has no dogfight rules.** Now that it starts, Dog Fights is an ordinary race on an
  arena course (Classic Dogfight is Jungle 01). Nothing outside the menu reads the chosen mode, so
  the dogfight game itself was never written in this build.
- **No AI network at all**: Beach 03, Farm 03 (the course loaded by the Farm 02 slot) and
  Haunted 01 have a network with zero routes, so even route 0 reads the next level's data. A
  proper fix needs waypoints for those tracks.
- **Unfinished tracks**: Desert 00, 02 and 03 have placeholder ground (see the README).
- **stdio in ROM**: harmless now that failed asserts don't print, but debug `printf`s still
  re-initialise stdio every time.

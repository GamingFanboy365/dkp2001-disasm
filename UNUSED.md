# Unused content

Things in the 2001 build that you can't get to by playing it normally. Playing normally counts the
debug level-select menu the build boots into, the front-end reached from the pause menu's QUIT,
every mode in it, and all 40 debug-menu courses.

Every claim here is backed by one of two kinds of evidence:

- **Unreferenced:** found by static reachability over the whole source. The tool follows every
  call, branch, fall-through, pointer, literal pool and jump table from `_start`. Nothing that
  reaches this content exists, so no input can show it.
- **Never ran:** reachable in the code, but never executed in 101 scripted mGBA sessions covering
  every front-end mode, list entry and course (instruction coverage from `tools/romtest`). This
  is strong evidence, but not proof.

Sizes are ROM bytes. Asset names are the developers' own (see `maps/assets.txt`); run
`tools/export_preview.py` to see the graphics.

## Music

- **Six course themes are never played.** These are `three_beach_tune_001`, `three_snow_tune_002`,
  `three_lava_tune_003`, `three_bayou_tune_005`, `three_haunted_tune_006` and
  `three_castle_tune_008`, listed in `tune_list`. Only the menu theme (`three_menu_tune_004`) is
  ever started; `game_init` stops it and the races are silent. *Never ran.* The fix patch plays
  them (see FIXES.md).
- **Final-lap speed-up.** `act_hud.c` speeds the music up by 14% when the final-lap banner shows,
  which can't be heard while nothing is playing.

## Intro, logos and Japanese warning

*Unreferenced.* The build boots straight into the debug menu, and none of these screens is wired
in:

| What | Code | Data |
|---|---|---|
| Nintendo and Rare logo screens | `logo_init`, `logo_process` (title_logo.c) | `Nintendo_Logo` (7 KB), `Rare_Logo` (9 KB) |
| Intro animation | (none left) | `introanim`, `introanim2`, `introanim3`, `introanim4`: 65 KB of sprite frames |
| Japanese health/warning screen | `menu_main_init_jap_warning` (menu_main.c) | `jap_warning` (7 KB) |

## The old assembly front-end

The game has two front-ends:

- **The one you see** is written in C (`src/menu/*.c`).
- **An older one** is hand-written assembly (`src/title/*.s`). Its title screen code still runs
  (the flying Diddy plane on the title comes from `fe_title.s`), but its other states never do.

**Never ran.** These are reachable only through `fe_title.s`'s own state table (`state_jt`):

| State | Code |
|---|---|
| Story mode, with map, path and cut scenes | `title_story.s`: `story_mode`, `init_story`, `init_map`, `plot_cut_scene`, … (1.4 KB) |
| Level select ("FREE FLY" / "PYLON RACING") | `title_levsel.s`: `level_select`, `init_levsel`, … (0.6 KB) |
| Dogfight select | `title_dogfight.s`: `dogfight_select`, `init_dogfight`, … (0.7 KB) |
| Small-font text renderer | `smallfont.s`: `plot_small_text`, … |

**Unreferenced:** `init_story`, `init_dogfight`, `start_game` (title_charsel.s),
`plot_backok_icons`, and several sprite helpers in `fe_sprite.s`.

**Its graphics are unreferenced too.** They're also the most interesting part of this list:

- **Character select for twelve racers:** full 32-frame rotating plane sprites for each
  (`*sel` under `title/gfx/char_select_planes/full_rotations/`, 419 KB in all). The racers are
  Diddy, Dixie, Donkey Kong ("kong"), Funky, Cranky, K. Rool, and six Mario characters:
  **Mario, Peach, Bowser, Wario, Toad and Yoshi**.
- **Racer portraits:** "front" pictures and head portraits for the same cast (`mario_front`,
  `peach_front`, …, `mario_data`, `peach_data`, …, `qmark` for an unknown slot), plus
  `diddyselect`, `peachselect` and `daisyselect`. **Daisy** appears only here.
- **K. Rool story cut scenes:** `kroolpic1`–`3`, `krool_talking`, `krool_looking`,
  `krool_temple`, `krool_lost_island`, `krool_find_map`, `krool_stone_map`,
  `krool_all_the_guardians`, the four coloured guards, the podium and its colour variants, and
  the story text pages and scene scripts (`krool_text`, `krool_stage0`–`3`, `krool_end_stage`,
  `krool_talking_anim`, `krool_doors_open_anim`, `krool_overlays`).
- **Story map pieces:** `beach_grow`, `keep_grow`, `haunted_woods_02`, `genie_lamp_anim`.
- **Old title and menu art:** `KroolBG` (Krool's Gold background, 21 KB), `CharSelect` (the
  full-screen 16-bit clock picture, 97 KB), `twit_bunch`, `bamboobarrel`, `cloudburst`,
  `blast1`, `backok`, the `Heads` palette.

## Courses

- **Placeholder ground.** Desert 00, 02 and 03 have no real course. Their ground is a grid stamped
  with the slot name ("S3-2", "R4-1", "R5-3"). Desert 01, from the same tiles, is real.
- **No computer-player routes.** Beach 03, Farm 03 (the course loaded by the debug menu's "Farm 02"
  slot) and Haunted 01 have AI networks with zero routes. 29 other courses have only a stub
  network with one three-point route.
- **Six start positions.** The course in the "Farm 02" slot has six start positions for four
  racers. The original hangs on it; fixed in the patch.
- **Palettes for courses that don't exist.** `__pal_test_lvl`, `__pal_test_sky` and
  `__pal_valley_lvl` are unreferenced. "Valley" isn't one of the build's worlds.
- **Per-world sky palettes.** `__pal_beach_sky`, `__pal_lava_sky`, … for all ten worlds are
  unreferenced. The game uses the `__pal_grad_sky_*` gradients instead.

## Unused game code

*Unreferenced.* Library code (newlib, libgcc) is left out.

| Function | File | Notes |
|---|---|---|
| `state_level_save`, `state_level_load`, `state_level_kill`, `state_level_set_award` | state_level.c | Empty stubs: progress saving was never implemented. |
| `state_slot_save`, `state_slot_load`, `state_slot_kill` | state_slot.c | Empty stubs. |
| `init_beacon`, `act_beacon`, `react_beacon` | act_beacon.c | A "beacon" object type that no level uses. |
| `act_beach_gun` | act_beach.c | A gun object for the beach. |
| `act_null` | act_null.c | An empty object type. |
| `campan_load`, `campan_output` | camera_pan.c | Loading and writing out camera-pan paths: a development tool. |
| `test_path` | testpath.s | A test camera path, as data. |
| `tend_towards` | plane.c | |
| `ram_asin`, `ram_mulx`, `ram_sin_interp`, `ram_cos_interp`, `ram_tan_interp` | dkp_math.s | IWRAM maths routines. |
| `menu_anim_set_frame`, `menu_anim_get_frame`, `menu_anim_set_fromdata_handle`, `menu_anim_set_mode_handle` | menu_anim.c | |
| `menu_text_set_dy_handle` | menu_text.c | |
| `spr_set_animation`, `spr_get_palette_blend` | sprite.c | |
| `obj_cleanup` | object.c | |
| `AGBAssert` | agbprint.c | Nintendo's assert helper; the game's asserts use their own code. |

## Reachable, but never ran in testing

*Never ran.* These may be reachable in situations the test sessions didn't create:

- **`multi.c`** (`multi_interrupt`, `multi_test`): link-cable multiplayer. It needs a second GBA,
  so it can't be tested here.
- **`user_control_camera`** (act_camera.c): a manually controlled camera, probably a debug mode.
- **`menu_spline_init`, `menu_spline_process`** (menu_spline.c): spline-driven menu movement.
- **`race_fail_player`** (act_race_monitor.c): never triggered.
- **`convert_to_comp_player`** (act_comp_player.c): handing a player over to the AI.

## Debug features still in the build

- **Debug boot.** The build boots into a debug level-select menu ("Level / Player / Blend")
  instead of the title screen. A (+) and B (−) change the course, and the up/down arrows pick a
  row.
- **AGBPrint debug output.** `AGBPrintf` writes to the debugger's print buffer; asserts and the
  sound driver's `AE_*` messages use it.
- **222 `ASSERT`s** and the sound driver's error checks stop the game with an undefined
  instruction (`0xEFFF`) when they fail.
- **CPU-time meter.** In races, `game_process` (game.c:274–298) draws a row of stars along the
  bottom of the screen, one per frame stage, each at the x position of the scanline that stage
  finished on, plus reference stars and circles. These are the stars and dots at the bottom of
  every race screen. The fix patch hides it.
- **Dog Fights is only a menu.** Its arenas start as ordinary races; nothing outside the menu
  reads the chosen mode.
- **`impure_data` in ROM.** newlib's stdio state was linked into ROM, so every debug print
  re-initialises stdio.

---

To reproduce this:

- `python3 tools/reachability.py` lists the unreferenced code and data.
- `python3 tools/reachability.py --path NAME` shows how something is reached.
- `tools/romtest/cover.c` (see `tools/romtest/README.md`) records execution coverage.

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
| Nintendo and Rare logo screens, with the intro animation | `logo_init`, `logo_process` (title_logo.c): Nintendo logo, then Rare logo with planes flying over, then `init_title` | `Nintendo_Logo` (7 KB), `Rare_Logo` (9 KB), `introanim`–`introanim4` (65 KB of sprite frames) |
| Japanese tilt-calibration prompt | `menu_main_init_jap_warning` (menu_main.c) | `jap_warning` (7 KB): 「ちゅうい！GBAを水平にもちながらAボタンをおしてください。」, "Caution! Hold the GBA level and press A", the Japanese version of the English Options screen "Hold Gameboy flat and press A or Start", which is used |

The fix patches boot through the logos and intro to the title, and move the debug menu to L+R.
`logo_process` loads `introanim4`'s palette but never draws its frames.

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
- **The whole K. Rool's Gold story text** (`krool_text_page_0`–`100`, about 2,200 words in the
  old front-end's font encoding). K. Rool finds a temple tablet that maps the way to Eldorado,
  the City of Gold, and reaches its gate on a tiny island. Four Guardians of the Gate (Nikiki,
  Nakaka, Nukuku and Nokoko) each set him a test to win one of the magic stones that open the
  doors; the first is collecting four keys among mines in Crackpot Keep. It ends with the doors
  opening on a sea of gold. Print it from your ROM with `python3 tools/story_text.py baserom.gba`.
- **Story map pieces:** `beach_grow`, `keep_grow`, `haunted_woods_02`, `genie_lamp_anim`.
- **Old title and menu art:** `KroolBG` (Krool's Gold background, 21 KB), `CharSelect` (a
  full-screen 16-bit sky, sea and hills backdrop, 97 KB), `twit_bunch`, `bamboobarrel`, `cloudburst`,
  `blast1`, `backok`, the `Heads` palette.

## Courses

- **Worlds and stories are sets of four courses.** The Clock Race menu ("Select World") lists
  each Racing world and each story with four courses, from one row of `select_indices` each.
  Racing and Stories start the first course of the chosen row. The world and story names are in
  the course-name table (`select_strings`) as levels 42–49, past the last course (`tab_levels`
  stops at 41), so none of them is a course of its own.

  | World / story | Its four courses |
  |---|---|
  | Sleepy Shores | Bounty Beach, Farm Attract, Jet Set Jungle, Beach Race 2 |
  | Kongo Kingdom | Swoop Swamp, Jungle Race 2, Magma Mainland, Haunted Race 2 |
  | Western Wastes | Lake Race 1, Lava Race 2, Swamp Race 2, Crackpot Keep |
  | Island of Eggs | Vulture Valley, Keep Race 2, Lake Race 2, Chicken Chase |
  | Polar Plateau | Frosty Lake, Farm Race 2, Desert Race 2, Snow Race 2 |
  | King of Kongs | Beach Barricade, Hair Raising Rescue, Peaceful Passage, Cranky Panky |
  | Back to the Light | Grub Grab, Farm Feud, Swamp Swoop, Dark Tower |
  | K. Rool's Gold | Classic Dogfight, Fly Like the Wind, Snowball Snapshot, Flawed Genie'us |

  In the original, Kongo Kingdom, Western Wastes and Island of Eggs hang on starting (the
  front-end camera bug, fixed in the patch). Island of Eggs' first course, Vulture Valley (Desert
  02), is one of the placeholder-ground courses.
- **Placeholder ground.** 18 courses have no real course: their ground is a plain fill stamped
  with the course's slot in the menus (e.g. Lava Race 2 "R3-2", Flawed Genie'us "S3-4"; all four
  Desert courses but Wasteland Wipe Out). Every code matches the slot. See `COURSES.md`.
- **No computer-player routes.** Beach 03, Farm 03 (the course loaded by the debug menu's "Farm 02"
  slot) and Haunted 01 have AI networks with zero routes. 29 other courses have only a stub
  network with one three-point route.
- **Six start positions.** The course in the "Farm 02" slot has six start positions for four
  racers. The original hangs on it; fixed in the patch.
- **Course maps.** The race HUD's course map comes from a switch in `init_hud_map`. Lava 01, Lake
  01 and Haunted 02 have finished maps in the sprite table (each matching its course) but no
  case, so they showed none; Snow 01's sprite-table slot pointed at Snow 00's map although its own
  (`__spr_hud_map_snow_01`) is there. All four are wired in by the fix patches. Farm 03's map is
  a copy of Farm 00's with "1/3" stamped on it, not its course, so it stays unused.
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
- **The camera-path editor** (`user_control_camera` in act_camera.c, `menu_spline_init` and
  `menu_spline_process` in menu_spline.c, `campan_addpt`): a developer tool for laying out the
  camera fly-in paths. It is reachable: hold Select while choosing a course in the front-end, and
  the race starts with the camera flying free under the player's control (`SPLINE_EDIT`); leaving
  such a race goes to the spline menu instead of the front-end. Not a game feature.
- **`race_fail_player`** (act_race_monitor.c): never triggered.
- **`convert_to_comp_player`** (act_comp_player.c): handing a player over to the AI.

## Debug features still in the build

- **Debug boot.** The build boots into a debug level-select menu ("Level / Player / Blend")
  instead of its own logos and title screen (the fix patches boot normally and open this menu
  with L+R). A (+) and B (−) change the course, and the up/down arrows pick a
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
  reads the chosen mode. (The fix patch adds a dogfight of its own design.)
- **Donkey Kong as a pilot.** His race sprites (`__spr_kongframesshort`), head portrait, voice
  and weapon entries all exist, but `setup_player_data` only allows five characters, so picking
  him flies Cranky; and the character select's RIGHT never reaches him. The fix patch makes him
  playable.
- **Redneck Kong's colour cut-out** (`clr_red`) is still on the character select, over the spot
  the background now gives Candy Kong; neither has any race data. Its slot is used as Diddy in
  the original (the slot number is taken as a character number).
- **Stories is only a menu too.** The front-end lists three stories, King of Kongs, Back to the
  Light and K. Rool's Gold, but picking one just starts the first of its four courses (above)
  with its star as pilot (Diddy, Dixie and K. Rool, though the original's table numbers them
  wrongly): Beach Barricade, Grub Grab and Classic Dogfight; none of the story text
  or cut scenes above is shown. Highlighting Back to
  the Light hangs the original, so the third story can't be reached. The fix patch fixes that and
  plays K. Rool's Gold's story mode, up to its first task. Only K. Rool's Gold has story data.
- **`impure_data` in ROM.** newlib's stdio state was linked into ROM, so every debug print
  re-initialises stdio.

---

To reproduce this:

- `python3 tools/reachability.py` lists the unreferenced code and data.
- `python3 tools/reachability.py --path NAME` shows how something is reached.
- `tools/romtest/cover.c` (see `tools/romtest/README.md`) records execution coverage.

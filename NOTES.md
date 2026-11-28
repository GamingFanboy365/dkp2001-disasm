# Working notes

What we've learned about how the game works, the decisions made, and the plan. Kept so the
project doesn't depend on anyone's memory of past sessions. Symbol names are in
`maps/symbols.txt`; struct and field offsets below are byte offsets.

## Decisions (from the project's owner)

- **Two patches.** `dkp2001_fixes.ips`: bug fixes and content the build already has (`FIXES`).
  `dkp2001_updates.ips`: the same plus our own new work (`UPDATES`). Each applies to the
  original ROM on its own.
- **Rare's assets are never modified**: no edits, recolours or redraws. They may be used as they
  are, by reference. New work is our own and lives in `updates/` (see `updates/README.md`).
- **Nothing copied** from elsewhere; no new drawings of Nintendo's characters. Original assets
  must match the game's look (its palettes, shading rules, detail) without imitating its art.
- **Accuracy first.** Restorations only where the build itself is complete and shows the intent;
  anything that's our design is labelled as such. Don't present guesses as Rare's intent.
- **No ROM, ELF or extracted assets in the repo**, and no mention of outside wiki pages the owner
  pointed us to. Patched ROMs are sent to the owner directly, never committed.
- **Boot:** the game boots through its own logos to the title; the debug menu is on L+R.
- **Rare-style humour** is welcome in the updates patch (credits, tips), kept to its own corner.
- Wanted: a complete version of the game. Plan below.

## Engine

**Main loop** (`AgbMain`, main.c): reads keys (`sys_joycnt` held, `sys_joytrg` pressed; A 1,
B 2, Select 4, Start 8, Right 0x10, Left 0x20, Up 0x40, Down 0x80, R 0x100, L 0x200),
reads the tilt sensor, then calls `sys_mode` (a function pointer: `logo_process`, `title`,
`menu_process` (debug menu), `game_process`, ...). `sys_flags` (0x03003398) holds global flags:
0x100 = race started from the front-end, 0x40 = the computer flies the player's plane (attract
demo), 0x20/0x80/0x04 race-state bits.

**Front-ends.** Two of them:
- the old hand-written one (`src/title/*.s`): `title` dispatches on `TITLE_STATE` through
  `state_jt`: 2 game-type carousel, 3 zoom, 4 character select, 5 story mode, 6 dogfight
  select, 7 level select, 8 controls. Uses `LOCAL_MEM` (0x020000ec) as shared scratch.
- the C one (`src/menu/*.c`): course and story lists. `menu_main_state`: 7 starts the chosen
  race (`game_init`), 8 hands back to the old character select. `virtual_mode` /
  `current_mode`: 0 Racing, 1 Stories, 2 Dog Fights, 3 Battles, 4 Clock Race (5 Options in
  the carousel). These stay set during a race; nothing outside the menu reads them except our
  code.
- `select_indices` (one row of 6 per world or story, `level - 1`): rows 0-3 the mode lists,
  4-8 the five Racing worlds (4 courses each), 9-11 the three stories (4 courses each).
  `select_strings`: course names by level, then world names (42-46) and story names (47-49).
- Character select slots (after `FIX "charsel"`): 0 Cranky, 1 Diddy, 2 Kong, 3 Krash,
  4 K. Rool, 5 Dixie, 6 Redneck (unreachable). Game character numbers: 0 Cranky, 1 Diddy,
  2 Krunch, 3 K. Rool, 4 Dixie, 5 Kong. `setup_player_data` maps a character to its sprite set
  (`tab_sprites` 5, 1, 4, 6, 2, 3).

**Courses.** `tab_levels[level]`, 9 words: level palette, level tiles (`__chr_*_lvl`), sky
tiles, ground map (`__map_*_gnd`), level map (`__map_*_lvl`), sky map, sky gradient
(`__pal_grad_sky_*`), object list (`obj_*`), AI network (`__net_*`). Levels 1-41 (no 0).
Tiles are 4x4 metatiles (`__frs_dkp`) over the tile bank (`__chr_dkp`). World positions are
8.8 fixed point; maps are about 1024 units across.

**AI network** (`__net_*`): hword route count N, then N hword offsets (bytes, from the network
start) to routes. A route is an hword point count, then 8-byte points: hword flags (bit 1 is
tested when skipping points), x, y, z in whole units (`ai_steer` reads point i at
route + 2 + 8i). Computer player n follows route n (fixed to fall back to route 0). A six-route
network's last route is instead the front-end camera fly-in path, in 12-byte records (an hword,
then x, y, z, two angles; `campan_load2`).

**Objects.** Each object (from `obj_new`, free list `object_free_list`, next at +4): +0 hword
flags, +2 hword type (1 player, 2 computer player), +32/+36/+40 x/y/z (8.8), +44/+48/+52
velocity, +60 heading (16-bit angle; forward is (sin, cos) in x, z), +76 pointer to its
level-object record, +80 flags (bit 3 armed), +84 player number, +104 speed, +130 character
(after `setup_player_data`), +134/+136/+138 weapon stack, +140 weapon count, +164 race
progress, +168/+172 route point and lap. `players[0..3]` (0x02003b04); player 0 is the human.

**Race monitor** (`monitor`, 0x02003b18): +80 state (0 intro, 1 GET READY, 2 GO, 3 racing,
4 finished, 5 retired), +84 strikes allowed (3), +85 laps (3), +86+p laps done, +94+p pylon
strikes (the dogfight's hits), +106+p place, +131 show-the-strike-counter timer, +136 the
player's place shown by the HUD, +140 end timer (then object 75 returns to the front-end).
Laps come from `act_starthoop` (`race_complete_lap`), strikes from `act_pylon`
(`race_fail_player` on the third).

**Course objects** (record data at the object's +76; angles: a byte b gives heading
(128 - b) << 8, so b = 0 faces -z, 64 +x, 128 +z, 192 -x; forward for heading h is
(sin h, cos h) in (x, z)):
- `start_pos` (types 4, 35): byte 0 player slot 0-3, byte 1 heading. The plane starts about
  570 units *behind* the marker and flies in during the intro, reaching it around GO, so the
  run-up must be clear. The marker object is then freed.
- `starthoop` (5): byte 0 = travel direction (128 - b). A lap counts when a plane crosses the
  hoop's line from behind to in front within about 64 units sideways (no height check). On a
  lap, pylons not yet taken become strikes (`race_complete_lap`).
- `pylon` (52-56): byte 0 the pass ray A, byte 1 its order (pylons are taken in order:
  only pylon `monitor+98+p` is live), byte 2 the strike ray B (normally A + 128), byte 3
  sprite flip (0 = flipped). A pass or strike happens when the bearing from the pylon to the
  plane crosses that ray (within 90 degrees of it). Third strike fails the race.
  `monitor+128` counts pylons.
- `powerup`: no data; the type is the kind. 27 random weapon 1-10, 29 weapon 13, 30 weapon
  14, 28 nothing. Respawns after about 1.4 s.
- `banana` (32): no data; +1 banana. `turbo` (31): byte 0 scale; boost 4 on touch.
- `booster` (57): byte 0 direction; boosts a plane heading within about 56 degrees of it.
  `groundboost` (63): the same, only below 8 units high.
- `directional_arrow` (76): byte 0 HUD arrow 0-4; invisible trigger, human only.
- `static` (33 no collision; 15, 49, 50, 66, 87-90, 94 solid): byte 0 scale, times 4 into the
  sprite's scale where 256 is full size (0 gives 48); the sprite is the type's `tab_types` entry.
- **Place** = laps, then pylons resolved, then distance to the next pylon. The computer
  players' `+164` progress is from their route and only used to aim weapons.

**Controls** (`plr_ctrl`, 16 bytes per player): +0 buttons (1 accelerate, 2 fire, 0x300 hard
turn), +8 stick x, +12 stick y. Computer players fill it in `ai_steer` / `ai_think`.

**Weapons**: ids 1-10 from powerups (`react_powerup`: random 1-10), 13 and 14 from special
powerups; `move_player`'s switch fires them. `ai_think` knows 1-8.

**Sprites**: `tab_sprites`, 8-byte entries (pointer, then palette etc.). Read entries from the
ROM, not by counting `.word` lines in `data/rodata.s` (entry 0 has no pointer). Notable: 99-114
HUD course maps, 121 GO, 122 GET READY, 123 FINISH, 124 RETIRE.

**Sound**: `audio_new_fx(id, ...)`; ids are the `SFX_*` names in `maps/symbols.txt`
(e.g. 55 `SFX_MISS`, 60 `SFX_CRANKY_LOVELY`). Tunes (`tune_list`): 0 beach, 1 snow, 2 lava,
3 menu, 4 bayou, 5 haunted, 6 castle.

**Story mode** (old front-end, `title_story.s`): `krool_story_info` -> stage list
(`krool_stage0`; 4 bytes per stage: text command, scene command; 0xFFFF starts a game);
`krool_text_page_N` text in the small font's encoding (`tools/story_text.py`). Only K. Rool's
Gold has story data.

## Patch mechanics

- Fixes go next to the code they replace, under `.ifdef FIXES` (updates: `.ifdef UPDATES`),
  tagged `FIX "<id>"`, same size where possible (`.fill`).
- New code goes in the `.fixes` section at the end of the ROM (`asm/fixes.s`,
  `updates/code/*.s`). The ROM end is out of BL range, so it's reached through small
  trampolines (`ldr rX, 1f; bx rX; .word target+1`) placed in the dead space of the 222 skipped
  assert blocks (`fix_assert_*`); a free one is just a `b` and a `.fill`.
- Same-size data changes (tables, pointers) go in `data/*.s` under `.ifdef FIXES`.
- After any change: `make compare` (original byte-identical), `make patch`, and the tests.

## Testing

- `tools/romtest/romtest`: headless mGBA. `PROBLEMS=1` lists emulator faults, `RAM_OUT`
  (+ `RAM_VIDEO`) dumps memory, `AUDIO_OUT` records sound, `POKE` writes memory, `--ppm`
  screenshots. See `tools/romtest/README.md`.
- `tools/reloc_test.py tools/romtest/romtest [--fixed|--updated]`: relocation test.
- The patched builds boot into the logos: scripts written for the debug menu press L+R on the
  Nintendo logo first and shift everything 100 frames (as `reloc_test.py` does). The boot-time
  stdio writes to ROM (`std+*`, `__sinit`) are harmless.
- `tools/tests/checks.py` holds the regular checks: every track from the debug menu with faults
  reported; the 20 front-end race starts (5 modes x 4); the 32 Clock Race courses; races run to
  the finish with the computer flying (`POKE` `sys_flags |= 0x40` before GO); the character
  picks; the stories; the dogfight endings. Copy the ROM somewhere first if a rebuild might run
  at the same time.

## Plan for the updates patch

1. **Course audit**: done, `COURSES.md` (`tools/course_audit.py`). 6 finished races, 12 built
   arenas/tasks, 4 drawn but empty, 18 placeholders whose ground is stamped with their menu
   slot (R = Racing world-course, S = story-course).
2. **Course tools**: decode the object lists fully; a level editor (layout, objects, routes).
3. **Computer racers on every course**: proper AI routes for the 29 stub and 3 empty networks.
4. **Finish the unfinished courses**: layouts for the 18 placeholders (our design, from the
   tile bank by reference), objects so every course can be completed. The owner wants the
   placeholder course names (Lava Race 2, Desert Race 2, ...) changed in the updates patch when
   we build them; not before.
5. **Clock Race** (timer, best times; needs save support) and **Battles** rules.
6. **K. Rool's Gold's later chapters**: task rules, and the task result fed back into the story.
7. Original graphics and music as needed; credits with Rare-style humour.

**Race flow** (researched for the cups):
- Menu start (`menu_main` state 7, menu_main.c:248): `game_level`, `sys_flags |= 0x100`,
  `sys_oam_start = 16`, `sys_mode = game_init`. 0x100 = the *preview*: camera fly-in and the
  course name (`plot_big_text(buf, 120, 136)` via `__ptr_plot_big_text`, game.c:157-165;
  big font: A-Z 0-25, digits 41-50, space 254, end 255; no `/`). A/Start: game.c:326 clears
  0x100 and calls `game_init` again = the race. B: back to the menu.
- Racing plays only the world's first course (`menu_mode_get_level`, menu_mode.c:503).
- End: state 4/5, +140 = 384 frames, then `act_fader` (object 75) sets `sys_flags` bit 1,
  `game_process` (game.c:342-357) calls `bg_done` and `init_title` (carousel, GAME_MODE 0).
  Clock Race too; its list index is `local_level` (0-31), reset by `menu_main_init`.
- Places: `calculate_race_positions` (laps, pylons, distance) -> monitor +106+p, +136.
  No finishing order is kept; computer laps keep counting after the finish.
- Lap banners: sprites 22/23 (`act_hud_position`), unused 95 "1ST", 96 "FINAL LAP",
  98 "LAP 2". HUD digits: 117 `hud_digits`, 118 `hud_nums` (0-9 and ':'). No race clock;
  `setup_timer` (act_haunted.c:255) draws M:SS with `hud_nums`. `sys_counter` 0x0300339c.
- Unused award coins per course: `levels` (0x0200df50), `state_level_get_award` (stub).

**Rare's music style in this build** (from the seven race tunes' note data; a guide for ours):
- Brisk (107-165 bpm); short intros (0-4 bars, the loop starting at bar 2-4); long loops of
  32-62 bars, built from 8-bar sections that come back varied.
- Modal keys (dorian, mixolydian, minor); vamp harmony: the bass holds the tonic for bars at
  a time, moving by half-step or to IV/V for colour, rather than functional chord cycles.
- Thin harmony (1-3 notes at once) over busy staccato 16th ostinatos/arpeggios (12-18 notes a
  bar); leads sparser (2-7 notes a bar), often long notes.
- Harmonised doubling: a line copied in parallel 3rds/6ths on a second track of the same
  instrument (the beach tune's pianos). Pan (CC 10) is in the data but the driver ignores it.
- Expression: modulation (CC 1, vibrato) and pitch bends on leads: a swell up and back on a
  long note, a fall at a phrase end (bend centre 8192, 0-16383, as low byte then high byte);
  wide velocities (accents, ghost notes on hats); volume swells (CC 7) on pads.
- The driver's controllers: 1, 7, 102/103 (loop), 126/127 (mono/poly); 8 voices with effects.

**Laying out a course** (`tools/course_build.py`, learned on Temple Tangle): a pylon's
pass and strike tests are rays of unlimited length from the pylon, checked only by the
racer's bearing. So a strike ray that points across another part of the course gives
strikes there while the pylon is live (from the previous pylon until it's passed). The
builder picks each strike ray clear of every racer's bearing over that stretch, checks each
AI route (and wider drifting lines) passes every pylon once and never strikes it, and keeps
solid scenery off the line and out of the 570-unit start run-up. Pylons 40+ units off the line.

**ai_steer reads one point past a route.** A segment's end is point i + 1 with no wrap, so
the last segment ends at whatever 8 bytes follow the route (in our layout, the next route's
header: a point near the map's top-left corner). Rare's courses survive it; ours with walls
didn't (every racer flew into the corner after the start line). `course_build.py` writes
the route's first point again after it, uncounted. Also: pure pursuit on a 48-unit circle;
very short segments are avoided. Object-list coordinates are unsigned (0-65535).

**Music** (`audio.S`, `src/audio/inf_inc.c`): a song (`Songinf`) is {track count, ticks per
beat (384), tracks, program map, sample list}; the race tunes all use `vgroup0` (programs 1-43
melodic, roughly General MIDI numbering, 127 the drum kit with GM drum keys: 36 kick,
38 snare, 39 clap, 41/43/45 toms, 42/44/46 hats, 51/59 ride, 54 tambourine, 55 splash,
57 crash, 65 timbale, 67/68 agogo, 80/81 triangle). Track bytes: 0 tempo, 1-4 delay, 5 note
on, 6 off, 7 controller (7 volume, 10 pan, 102 loop point, 103 loop back), 8 program,
11 end. The driver mixes 8 channels shared with sound effects. `audio_tune_list_ref`
(RAM) points at the song list, set at start-up; the updates build points it at ours.
The owner asked: no arrangement of existing DK music; every tune ours from scratch.

**Later, from the owner:**
- A finishing fanfare: one for 1st, variations for 2nd and 3rd, another for 4th (done:
  `finish-fanfares`, tunes 11-14).
- A race timer that counts up, and a positions/ranking system (results).
- Racing mode: a world is a cup of its four courses in the Clock Race list's order. After
  each race: the fanfare, the rankings, then the next course; after the fourth, the final
  results over a background of ours. The intro shows "RACE 1 OF 4", "RACE 2 OF 4",
  "RACE 3 OF 4", then "FINAL RACE" centred at the top in the course-name font, only in Racing mode. The lap on screen (done:
  LAP 1, LAP 2, FINAL LAP; the owner chose text over 1/3 marks on the map; top left under the
  timer, since the item box and banana counter use the bottom left). The
  rankings can reuse Rare's small racer icons (the menus' *small* character pictures, or the
  in-race *_head sprites), by reference.
- **Cups (done, `updates/code/cup.s`)**: RESULTS after every race (that race's order, head, time,
  points earned 10/6/3/1); after the fourth race's RESULTS, FINAL RESULTS (ranked by cup
  points, showing total points and total time) over our background
  (`updates/art/cup_results/paint.py`, Rare's menu-background style: bright, rendered; the
  owner wants more detail), then the world list. Points AND times, as in Mario Kart and
  Banjo-Pilot. Cup state at 0x0203ff00.
- **Race timer (next)**: counts up from GO in Racing and Clock Race; shown top left with
  Rare's small yellow `hud_digits` (sprite 117, 8x16, no separator) plus our own ' and "
  marks in the same style: 1'23"45. Each racer's time recorded when its third lap ends;
  unfinished racers at the end get an estimate from their progress. Big `hud_nums` (118,
  16x24 with ':') is the other digit set.
- Clock Race becomes time trials: best time per course (needs saving), opponents kept;
  finishing a course returns to the course list where it was chosen. The owner's design:
  after a Clock Race, a chart of the course's top 5 times with three-letter initials
  entered for a new one, and the Clock Race course list showing "BEST TIME" (done:
  `best-times`; the owner asked for a jungle background with a parked plane of our own,
  diagonal-front, and a chill jungle reggae; big font for the title only).
- Temple Tangle's HUD course map (new art) and an original jungle tune (none in the build;
  the jungle courses borrow the bayou theme). The tune list skips 007; nothing of it survives.
- An original farmer character (a farm animal, our own design) for the unused seventh
  character-select slot that was Redneck Kong's; Rare's Redneck sprite stays in the ROM. It
  needs a full in-race sprite set. Candy Kong's figure is part of Rare's sepia backdrop and
  can't be painted out; our art would sit over that slot instead. The owner's idea for that
  art: the farmer holding up a sign ("Victory" or similar), a nod to the slot's history.
  The sign is only for the character select screen, not in races. He needs a racer head
  icon of ours for the rankings (Candy's head sprite, 45, stays unused, untouched). The farmer is a new
  animal character, not a Kong.
- Placeholder courses get new names one at a time, only when each is built.
- No blue pylons on any course in the updates patch: every race gets hidden checkpoints and
  invisible walls along its track, as Temple Tangle has. For Rare's finished races the
  racing line can come from their own AI route 0, and their grounds already show the track
  (islands, lava, snow); each course's track width needs fitting to its ground.

Open questions: the Stories crash the owner saw (not reproduced on mGBA; on hold);
whether K. Rool's Gold's first task should be its first course (Classic Dogfight) or the
Crackpot Keep task its text describes.

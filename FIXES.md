# Bug fixes

Fixes live in the assembly behind `.ifdef FIXES`, next to the original code they replace, so the
normal build stays byte-identical to the original game. New design that goes beyond the build
(the dogfight) is behind `.ifdef UPDATES` as well, so there are two patched builds:

```bash
make fixed
```

```bash
make updated
```

```bash
make patch
```

- `make fixed` builds `build_fixed/dkp.gba`: the fixes and restored content (`FIXES`).
- `make updated` builds `build_updated/dkp.gba`: the same plus the updates (`FIXES` and
  `UPDATES`).
- `make patch` builds both and writes `patches/dkp2001_fixes.ips` and
  `patches/dkp2001_updates.ips`, which are committed, with the patched ROMs' sha1s. Both are IPS
  patches for the ROM made from the 2001 ELF (`tools/elf2gba.py`, sha1
  `6a76def610829ac1502afb58740e38b5e6926b3d`); each applies to the original on its own.
- `tools/make_ips.py apply` can apply them without other tools.

In the tables below, everything under **Fixes** is in both patches; everything under **New
behaviour** is only in the updates patch.

## Conventions

- Each fix has a short id (`FIX "farm-start-slots"`) and a comment explaining the bug.
- Keep a fix the same size as the code it replaces (`.fill` to pad), so nothing after it moves
  and the IPS stays a few bytes. The build is relocatable, so a fix that needs more room can
  grow; the game still works, but the patch then rewrites most of the ROM. Moving larger new
  code to the end of the ROM keeps the patch small.
- Check a fix with `tools/romtest` (play the affected track or menu) and run
  `tools/reloc_test.py` to make sure nothing else changed.
- `python3 tools/tests/checks.py all build_fixed/dkp.gba` replays the checks below (every
  track, the 20 front-end starts, the 32 Clock Race courses, the six character picks, the
  stories); `finish` and `dogfight` are run on their own. It handles the L+R boot itself.

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
| `audio-stop-channel` | A bug in the **sound driver**. When a music note's one-shot sample runs out before the note is released, `uan_set_channel_to_stopped` should set the channel's state to stopped (16) through `r0`, as the empty case next to it does. It writes through `r8` instead, an unrelated register. The channel plays on past the end of the sample, into whatever data follows, and the byte lands at a stray address. The menu music never hit this path; the race music does (seen on Lake 01 with the beach theme, 3½ minutes in). | Writes through `r0`. |
| `krools-gold-story` | **K. Rool's Gold plays its story.** The old front-end's story mode tells it in pictures and text (title card, temple, tablet, the flight to the island, the gate, the Guardian Nikiki and the first task), but nothing in this build starts it: the Stories menu just starts a race. | Picking K. Rool's Gold in Stories hands over to the story mode (as `menu_main` hands over to the old character select) instead of starting the race. A advances the text. When the story reaches its first task it starts the race the menu would have: K. Rool's Gold on Lava 01 (a dogfight, with the updates patch). The story's own code had only a placeholder there (`game_level` 1). The later chapters (the other three Guardians and the ending) need the task's result to come back into the story, which nothing in the build does, so they are still unreached. |
| `boot-logos` | The build **boots straight into the debug menu** ("Level / Player / Blend"). The game's own boot sequence is complete but never called: `logo_init` starts `logo_process`, which shows the Nintendo logo, then the Rareware logo with the intro animation (`introanim`, `introanim2`, `introanim3`), and ends in `init_title`, the title screen; A or START skips it. | `AgbMain` calls `logo_init` instead of `menu_init`. The debug menu is still there: pressing **L+R** together on the logos or the title screen's game-type carousel opens it (checked once per frame from the main loop, so it can't fire in a race or a menu). |
| `hud-maps` | The race HUD shows **no course map** on Lava 01, Lake 01 and Haunted 02, and **Snow 00's map on Snow 01**. Their maps are finished and in the sprite table (each matches its course's layout), but `init_hud_map`'s switch on `game_level` has no case for the first three, and the sprite table's Snow 01 slot points at Snow 00's map instead of `__spr_hud_map_snow_01`. | A hook before the switch picks the three maps (sprites 100, 106, 114); the Snow 01 slot points at its own map. Farm 03's map is a placeholder (Farm 00's with "1/3" on it) and stays unused. |
| `charsel` | The **character select** (old front-end, `title_charsel.s`) picks the wrong pilot, and its colour highlights don't line up with the sepia group picture. (1) Its seven slots are in screen order (Cranky, Redneck, Diddy, Kong, Krash, K. Rool, Dixie) and the slot number goes straight into `CHAR_SELECTED`, but the rest of the game numbers characters Cranky 0, Diddy 1, Krunch 2, K. Rool 3, Dixie 4, Kong 5. So Diddy flew as Krunch, Krash as Dixie, K. Rool as Cranky, Dixie as Diddy; only Cranky was right. Its voice tables have only six entries, in the order Cranky, Diddy, Kong, Krash, K. Rool, Dixie: written before Redneck Kong's cut-out was slotted in at 1, so every slot from Diddy on also played the wrong voice. (2) The background was redrawn with Candy Kong in that slot, but the colour cut-outs still include Redneck, and no character data exists for either. (3) RIGHT never reaches Kong, and a race can't fly him anyway: `setup_player_data` takes the character mod 5, so Kong (5) flew as Cranky, although his race sprites work and every other per-character table has six entries. (4) All the cut-outs are drawn 7 pixels right and 1 down of the figures they highlight (measured against the background: 5 of 7 match best at exactly that shift). | The slots are reordered (data only) to the voice tables' order, Cranky, Diddy, Kong, Krash, K. Rool, Dixie, with Redneck's cut-out moved to a seventh slot the cursor never reaches; the cursor tables follow the screen left to right, and RIGHT reaches Kong. On leaving the screen the slot becomes the character number. Races take characters mod 6, so Kong flies as Donkey Kong. The cut-outs and the cursor arrow are drawn at -7, -1, and Cranky's (an older, hunched pose) at +12, -4, where it covers his figure best. Every pick now flies as the character picked. |
| `story-pilots` | In the **Stories** menu, highlighting **Back to the Light** hangs the game and draws a broken graphic, so **K. Rool's Gold** below it can't be reached; and the stories are flown by the wrong characters (Krunch, nobody, Cranky). Each story's pilot comes from `story_planes` = 2, 6, 5, which is in the character select's slot order (0 Cranky, 1 Redneck, 2 Diddy, 3 Kong, 4 Krash, 5 K. Rool, 6 Dixie): Diddy, Dixie and K. Rool. The rest of the game reads it as character numbers, where 2 is Krunch, 5 is Kong (Cranky in a race) and 6 is past every per-character table: highlighting it played a garbage sound id (the driver trapped) and copied garbage into video memory for its plane. | The table holds the same three in character numbers: King of Kongs Diddy, Back to the Light Dixie, K. Rool's Gold K. Rool. The stories' stars agree with the published descriptions of the game's story mode, and K. Rool's Gold's with its story text. |
| `story-overlays`, `story-sprites`, `story-next-stage` | Bugs in the old front-end's **story mode** (`title_story.s`, `fe_sprite.s`), which never ran in this build. (1) A cut scene without overlay animation, such as the K. Rool's Gold title card, never sets the overlay-list pointer, and the same bytes are partly cleared by `init_story` and reused as a path number by map scenes, so `plot_cut_scene` walked a stray address. (2) `sprite_frame_plot` saves five registers but leaves through `sprite_plot`'s exit, which restores seven, so it returned to a garbage address; only the story uses it. (3) `move_map` and `fade_stuff` call `next_stage` and then keep using registers it has clobbered (`move_map` stored through them). | (1) A scene with no overlay animation draws an empty list. (2) `sprite_frame_plot` saves r8 and r9 as `sprite_plot` does (in `main.c`'s dead assert space, within branch range). (3) After `next_stage` they return. |

### New behaviour (updates patch only)

These are **new design, not restored content**: the build has no dogfight game code, so nothing
says how Rare meant a dogfight to play. Their code is in `updates/` (see `updates/README.md`),
with only tagged hooks in the game's source.

| Id | What | How |
|---|---|---|
| `dogfight-opponents` | **Dog Fights has opponents.** This build has no dogfight game: the mode is a menu that starts an ordinary race on an arena course, and nothing outside the menu knows which mode was chosen. The three computer planes had no start positions on most arenas (they sat at 0,0,0), then flew the arena's stub route along the ground, far from the player. | Only in a dogfight: when the menu's `virtual_mode` is Dog Fights (it stays set during the race), or for the K. Rool's Gold story, whose course (Lava 01) is a dogfight course. **Start:** the computer planes line up 160–200 units ahead of the player, spread 48 units apart at its height, facing it (`init_start_pos`). **Steering:** `ai_steer` aims at the player's plane instead of the route. Player 1 aims straight at it; players 2 and 3 aim where it will be 24 and 48 frames later, so they cut across its nose. The game's own steering, collision avoidance and speed code do the rest. **Weapons:** the arenas have no powerups, so a plane with no weapon gets a random one (types 1–8), on average every couple of seconds. That includes the player. Each computer plane's race progress is set just behind the player's, or just ahead when the player is behind it, so `ai_think` aims its forward or rear weapons at the player. |
| `dogfight-scoring` | **The dogfight has rules and an ending.** | Every plane has **3 lives**, kept in the race monitor's pylon-strike bytes (`monitor+94+player`). Any hit that makes a plane tumble (`player_tumble`, from a weapon or a shot) costs a life, friendly fire included. **You:** the race's strike counter (top left) slides in with the pylon-miss sound to show your lives; losing the last one ends the fight like a failed race (**RETIRE**, then the menu). **Opponents:** one with no lives left tumbles, vanishes a second later (out of drawing and collisions) and drops its weapons. The place indicator shows 1 + opponents still flying (4th, 3rd, 2nd, then 1st). When the last one has fallen, the fight ends like a won race (**FINISH** with the fanfare; the computer flies your plane; then the menu). Laps and pylon strikes don't count in a dogfight. Pause → RESTART starts the fight over with everyone back. |
| `temple-tangle` | **Kongo Kingdom's second course becomes Temple Tangle.** Level 37 has a drawn courtyard (a stone temple yard with a maze worn into its paving) but no race on it, the placeholder name "JUNGLE RACE 2" and the "?" picture. One course at a time: no other course is renamed. | **Name:** `select_strings` (both rows) points at our string in `updates/text/course_names.s`; Rare's string stays in the ROM. **Picture:** entry 36 of the course-picture tables (`pals`, `D_084d7920`) points at our 96x96 picture, painted by `updates/art/temple_tangle/paint.py`: the temple, the maze, vines, and a blue tree frog of our own. No Rare art or characters in it. **The race** (our layout, `updates/courses/temple_tangle.py`, built by `tools/course_build.py`): level 37's object list and AI network point at ours. A 4,300-unit lap that runs up the west side, along the top, snakes through the middle of the maze (with a hairpin), down the east side and back through the southern maze. Start hoop and four start positions, 9 turn arrows, 12 bananas, 10 powerups, a turbo, boosts, and Rare's own palm trees and stone pillars placed as scenery. Five AI routes and the front-end camera fly-in. **No pylons to dodge:** its 10 pylons are hidden checkpoints (out of sight above the ground, at the edge of the map), whose pass lines span the track, so they still give the race order but can't be missed. **Walls along the track** (`course-walls`, below) keep everyone on it. The computer racers fly all three laps with no strikes (about 1 min 50 s). **HUD map:** drawn by the builder from the racing line in Rare's style (white track, grey edge, a checkered start line); in the updates build, sprite 111 (Farm 03's unused map copy) points at it and Temple Tangle is in the hud-maps table. **Ground:** a new level map of ours made only of Rare's metatiles from Classic Dogfight's overgrown temple (drawn with that course's tile list), arranged by the builder (`--ground`) so the path is paving and everything else grass, with Rare's ragged overgrown edges between; the track is 112 units wide with grass between every stretch. Rare's courtyard map stays in the ROM. |
| `course-walls` | **Invisible walls along the track** (courses that have them: Temple Tangle). | `updates/code/walls.s`, called every frame from the race monitor's hook once the race is under way (from GO; the planes fly in from off the track before that). A 64x64 grid of 16-unit cells, generated from the course's racing line, marks the track (`TRACK_HALF_WIDTH` either side). A plane off it is put back onto it. The player's plane stops dead, as on flying into a tree (`player_collide`) but without being knocked down: speed to zero, heading unchanged, and the wall sound if it hit at speed. Computer planes are only slid back, so they keep their line. |
| `jungle-theme` | **The jungle courses get a theme of their own.** The build has no jungle music (the race tunes skip number 007, and nothing of it survives); the fixes patch has the jungle courses borrow the bayou theme. | An original tune of ours (`updates/music/jungle.py`, built by `tools/song_build.py`): E dorian, 140 bpm, a melody on a plucked lead over muted-guitar plucks, contrabass and hand percussion (toms, agogo bells, timbale, tambourine), with guitar answers; a two-bar intro and a 48-second loop. It plays the instruments Rare's race tunes use. It's tune 7 in a copy of the song list (Rare's seven plus ours) that the sound driver uses in the updates build; `race_tunes` gives it to levels 34-37. Not an arrangement of any existing tune. |

All but `race-music` and the two dogfight entries keep their code the same size. `race-music` adds 84 bytes of new code and
data in a `.fixes` section after all the game's data (`asm/fixes.s`), reached through a
trampoline in an assert block's dead space, because the end of the ROM is out of `bl` range.
The dogfight code adds about 1.2 KB there in the same way, called through trampolines in the dead
assert space of `act_camera.c`, `act_weapon.c`, `act_starthoop.c`, `act_pylon.c` and
`act_race_monitor.c`. So nothing moves, and the patch only touches the changed bytes (about 7 KB).

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
- **Dog Fights:** in all four arenas the opponents start ahead of the player and reach it within
  about 15–30 seconds. Traced over 90 seconds, the three computer planes got and used 9, 4 and 7
  weapons, and hit the player. 2½-minute armed fights in each arena (player turning and firing)
  run with no faults.
- **Dog Fights scoring:** in long scripted fights in all four arenas and K. Rool's Gold, lives
  are counted for every plane, the player's last life gives RETIRE, and all three opponents
  down gives FINISH (one scripted player won 3–0 on its last life; a test build where the player
  can't be hit always wins). Each ending returns to the front-end with no faults. Pause →
  RESTART after two opponents were downed brings them back with full lives.
- **Boot:** the fixed ROMs show the Nintendo logo, the Rareware logo with the intro animation,
  then the title, with no faults and with sound. L+R on the logos or the title opens the debug
  menu, which looks exactly as the original's boot screen and starts races as before; L+R in a
  race does nothing. `tools/reloc_test.py --fixed` and `--updated` open the debug menu with L+R.
- **Course maps:** Lava 01, Lake 01, Snow 01 and Haunted 02 raced with their maps showing and the
  plane markers moving over them, with no faults.
- **Character select:** each of the six characters picked, a race started and the plane's
  character read back from RAM: all six fly as picked (the original got one of six right).
  Cut-out alignment checked in screenshots against the background.
- **Stories:** each of the three stories can be highlighted and started with no faults, showing
  and flying its star (Diddy, Dixie, K. Rool; checked from RAM); the original hangs on
  highlighting Back to the Light. K. Rool's Gold plays the story's first
  chapter (40 stages, A to advance) and then its dogfight, and returning to the menu afterwards,
  through the title screen's attract demo and back into Stories, runs with no faults.
- **Sound driver:** the Lake 01 session that hit `audio-stop-channel` runs clean with the fix.
  With the dogfight code switched off, the fault still happened on the same frame, so it is a
  driver bug and not the dogfight code.
- **Relocation:** `python3 tools/reloc_test.py tools/romtest/romtest --fixed` passes on the
  front-end and **40/40 tracks with no exceptions**. Jungle 03, the original's one exception, now
  plays identically when code or data move, so its AI no longer depends on stray memory.

## Known bugs not fixed yet

- **Dog Fights has no scoreboard of its own.** The patch reuses the race HUD: the strike counter
  for your lives and the place indicator for opponents left.
- **K. Rool's Gold's later chapters.** The story continues after the first task (Nakaka,
  Nukuku, Nokoko and the ending, with three more "start a game" points per Guardian for
  retries), but nothing tells the story whether a task was won, and the tasks' rules (keys,
  mines, a time limit) don't exist in the race code. Print the text with `tools/story_text.py`.
- **No AI network at all**: Beach 03, Farm 03 (the course loaded by the Farm 02 slot) and
  Haunted 01 have a network with zero routes, so even route 0 reads the next level's data. A
  proper fix needs waypoints for those tracks.
- **Unfinished tracks**: Desert 00, 02 and 03 have placeholder ground (see the README).
- **stdio in ROM**: harmless now that failed asserts don't print, but debug `printf`s still
  re-initialise stdio every time.

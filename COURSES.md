# Courses

What each of the build's 41 courses contains, read from the ROM. To reproduce it:

```bash
python3 tools/course_audit.py build/dkp.gba
```

`--objects LEVEL` lists one course's objects with their positions and data.

## Where courses come from

- `tab_levels[level]` (levels 1-41) points to each course's palette, tile list, sky tiles,
  ground, level and sky maps, sky gradient, object list and AI network (see `NOTES.md`).
- The **level map** is 32x32 metatiles (4x4 tiles each, `__frs_dkp`), 1024 units across. The
  **tile list** (`__chr_*_lvl`) is a short list of tile numbers in the shared tile bank
  (`__chr_dkp`), so every world's terrain tiles are available to any course.
- The **object list** (`obj_*`, read by `obj_gen`) is 8-byte entries: the offset of the object's
  record, then x, y, z. The record starts with the object type, which picks a class through
  `tab_types` and `tab_classes`.
- The menus' course lists are `select_indices` (`int[12][6]`, `level - 1`): Racing worlds 1-5
  (Sleepy Shores, Kongo Kingdom, Western Wastes, Island of Eggs, Polar Plateau), the three
  stories (King of Kongs, Back to the Light, K. Rool's Gold), the Dog Fights and the Battles.
  Below, **R2-3** means Racing world 2, third course; **S1-4** story 1, fourth course;
  **D** Dog Fights, **B** Battles.

## The placeholder courses carry their slot codes

18 courses have no real ground. Their level map is a plain fill in the world's colours with a
code painted across it in big letters, using between 26 and 188 different metatiles; drawn maps
use 269 to 1008. Every code is that course's place in the menus. For example, Lava Race 2's
ground says "R3-2", and it is the second course of world 3 (Western Wastes). Flawed Genie'us
says "S3-4", and it is the fourth course of K. Rool's Gold. All 18 match. So the build
records where each unfinished course was meant to go, even though none of them was built.

| Level | Course | Code painted on the ground = menu slot |
|---|---|---|
| 4 | Flawed Genie'us | S3-4 |
| 7 | Lava Race 2 | R3-2 |
| 10 | Snowball Snapshot | S3-3 |
| 11 | Snow Race 2 | R5-4 |
| 14 | Crackpot Keep | R3-4 (Dark Tower's keep is drawn in the middle) |
| 15 | Keep Race 2 | R4-2 |
| 16 | Peaceful Passage | S1-3 |
| 18 | Lake Race 1 | R3-1 |
| 19 | Lake Race 2 | R4-3 |
| 22 | Cranky Panky | S1-4 |
| 24 | Farm Race 2 | R5-2 |
| 28 | Swoop Swamp | R2-1 |
| 29 | Swamp Race 2 | R3-3 |
| 33 | Haunted Race 2 | R2-4 |
| 36 | Jet Set Jungle | R1-3 |
| 38 | Fly Like the Wind | S3-2 |
| 40 | Vulture Valley | R4-1 |
| 41 | Desert Race 2 | R5-3 |

They have one start position and a stub AI network (one 3-point route, or none). Only Peaceful
Passage has anything else: three start positions, powerups and some scenery.

## Finished races

Ground, start hoop, pylons, four start positions, bananas, powerups and boosts, and AI routes
for four computer racers plus the front-end's camera path:

| Level | Course | Slot | Pylons | Route points |
|---|---|---|---|---|
| 1 | Bounty Beach | R1-1 | 6 | 30 |
| 2 | Beach Race 2 | R1-4 | 11 | 16 (no camera path) |
| 5 | Magma Mainland | R2-3 | 9 | 28 |
| 8 | Frosty Lake | R5-1 | 6 | 30 |
| 20 | Chicken Chase | R4-4 | 7 | 32 |
| 30 | Whisper Woods | none (debug menu only) | 6 | 33 |

Farm Attract (level 25, R1-2) has a drawn farm map, four start positions and six 14-point
routes, but no hoop, pylons or pickups: it's a stage for the attract demo, not a race.

## Built arenas and story tasks

Drawn ground and their own special objects, but no race objects (their rules are elsewhere,
or missing):

| Level | Course | Slot | Objects |
|---|---|---|---|
| 3 | Beach Barricade | S1-1 | a beach gun, scenery, 6 classless objects |
| 6 | Classic Dogfight | S3-1 | 4 starts, 9 classless objects |
| 9 | Dawn Duel | D-2 | 4 starts, five 18-point routes, scenery |
| 12 | Dark Tower | S2-4 | 25 classless objects (6 types) |
| 17 | Focal Feud | D-4 | 4 starts, scenery, 5 classless objects |
| 21 | Hatch Match | B-1 | chickens, egg generators, nests, powerups |
| 23 | Farm Feud | S2-2 | 6 starts, scenery, 2 classless objects |
| 26 | Swamp Swoop | S2-3 | 25 frog points, a swamp gun, a lily pad |
| 27 | Swamp Showdown | B-3 | 4 target beasts, 8 classless objects |
| 31 | Hair Raising Rescue | S1-2 | 41 happy-soul generators, a magic well, a soul eater |
| 32 | Ghost Grasp 2 | B-2 | 38 happy-soul generators, a magic well |
| 34 | Grub Grab | S2-1 | 13 crow points, 14 grub holes, the royal bird |

Drawn but empty (one or four start positions, nothing else): Classic Variation (13, D-3),
Classic Dogfight (35, D-1), Jungle Race 2 (37, R2-2), Wasteland Wipe Out (39, B-4).

"Classless" objects are placed in the course but their type has no class in `tab_types`
(types 6, 14, 16, 17, 21-26, 34, 36, 46, 48, 59, 65, 97). `obj_gen` gives them an object and
nothing else: their code isn't in this build.

## What this means

- **Racing:** of the 20 world slots, 6 have finished races (5 with a slot, plus Farm Attract's
  stage); 13 are placeholders and one (Jungle Race 2) is drawn but empty.
- **Stories:** 5 of the 12 story slots are placeholders (two in King of Kongs, three in
  K. Rool's Gold). The other 7 are built arenas whose task rules are mostly missing.
- The placeholder codes tell us where each course belongs. They don't tell us what it looked
  like: any layout we make for one is our own design (updates patch, `updates/courses/`), built
  from the tiles already in the bank and never by altering Rare's maps.

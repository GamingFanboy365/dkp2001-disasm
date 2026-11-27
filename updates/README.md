# updates/

Everything in this folder is **new work made for this project**, for the updates patch
(`patches/dkp2001_updates.ips`). None of it comes from the original game, Rare or Nintendo.
It was written by Claude (an AI) at the direction of the project's owner.

The rest of the repository is the disassembly of Rare's 2001 build (`asm/`, `data/`) and the
fixes patch (`asm/fixes.s`), which only repairs and restores what that build already contains.
This folder is kept separate so it's always clear what is theirs and what is ours.

## Rules

- **Rare's assets are never modified.** Their graphics, music, sound and text are used, if at
  all, by reference from the player's own ROM, exactly as they are. Nothing here copies, edits,
  recolours or redraws them.
- **Nothing copied from anywhere else**, and no new drawings of Nintendo's characters.
- **Original assets follow the game's look**: built from the colours of the palettes they sit
  in, drawn to the same rules as the surrounding art (shading ramps, light direction, detail),
  and checked in in-game screenshots next to the originals. Each keeps its editable source
  next to it.
- **Labelled as ours.** Anything here is our design, not a reconstruction of what Rare meant.
  `FIXES.md` lists it under "New behaviour (updates patch only)".

## Layout

| Folder | What goes there |
|---|---|
| `code/` | New game code, assembled only with `UPDATES` (after `asm/fixes.s`, in the same `.fixes` section at the end of the ROM). It reaches the game through small hooks in `asm/src`, each tagged `FIX "<id>"` and wrapped in `.ifdef UPDATES`. |
| `courses/` | New course data: layouts, object placements, AI routes. |
| `art/` | Original graphics, with their source images. |
| `music/` | Original music and sounds, with their sources. |
| `text/` | New text: credits, tips. |

## Contents

| File | What |
|---|---|
| `text/course_names.s` | New course names: level 37 is **Temple Tangle**. |
| `art/temple_tangle/` | Temple Tangle's course picture: `paint.py` paints it (no source images), and writes `picture.png`, `tiles.bin` and `palette.bin`. `art/pictures.s` puts it in the ROM. |
| `courses/temple_tangle.py` | Temple Tangle's race: racing line, hidden checkpoints, pickups, scenery, walls, HUD map, and its ground (`temple_tangle_ground.s`, made with `--ground` from your ROM: a map of Rare's metatiles, arranged by us). `tools/course_build.py` turns it into `temple_tangle.s` (the game's object-list and AI-network formats); the Makefile reruns it when the `.py` changes. |
| `code/walls.s` | Invisible walls along a course's track (`course-walls` in `FIXES.md`). |
| `code/dogfight.s` | Dog Fights (and K. Rool's Gold's fight): opponents that hunt the player, weapons for everyone, three lives each, the place indicator as a score, and the endings. See `dogfight-opponents` and `dogfight-scoring` in `FIXES.md`. |

## Building

```bash
make updated
```

```bash
make patch
```

`make updated` builds `build_updated/dkp.gba` (fixes plus this folder); `make patch` writes both
patches.

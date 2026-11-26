@ New code and data for the bug-fix build (assembled only with FIXES).
@ It goes in its own section after all the game's data, at the end of the ROM,
@ so adding it moves nothing else and the IPS patch stays small. The ROM end is
@ out of BL range from most code, so callers reach it through small trampolines
@ placed in the dead space of failed-assert blocks (see FIXES.md).

	.section .fixes, "ax", %progbits
	.thumb
	.balign 4

@ FIX "race-music": the races are silent. game_init() stopped the menu music
@ and never started anything, although the ROM has six course themes
@ (tune_list) and act_hud.c already speeds the music up on the final lap.
@ Called in place of game_init's audio_halt_tune(): starts the course's
@ theme from race_tunes, or stops the music if the course has none.
fix_race_music_far:
	ldr	r0, 1f
	ldr	r0, [r0, #0]			@ game_level
	cmp	r0, #RACE_TUNES_COUNT
	bhs	2f
	ldr	r1, 3f
	ldrb	r0, [r1, r0]			@ race_tunes[game_level]
	cmp	r0, #NO_TUNE
	beq	2f
	ldr	r1, 4f
	bx	r1				@ audio_start_tune(tune), returns to game_init
2:	ldr	r1, 5f
	bx	r1				@ audio_halt_tune()
	.balign 4
1:	.word	game_level
3:	.word	race_tunes
4:	.word	audio_start_tune+1
5:	.word	audio_halt_tune+1

@ tune_list order: 0 beach, 1 snow, 2 lava, 3 menu, 4 bayou, 5 haunted, 6 castle
	.equ	BEACH, 0
	.equ	SNOW, 1
	.equ	LAVA, 2
	.equ	MENU, 3
	.equ	BAYOU, 4
	.equ	HAUNTED, 5
	.equ	CASTLE, 6
	.equ	NO_TUNE, 0xff

@ One entry per game_level (tab_levels index). Worlds without a theme of their
@ own borrow the closest one; edit freely.
race_tunes:
	.byte	NO_TUNE					@  0 (unused)
	.byte	BEACH, BEACH, BEACH, BEACH		@  1- 4 beach_00-03
	.byte	LAVA, LAVA, LAVA			@  5- 7 lava_00-02
	.byte	SNOW, SNOW, SNOW, SNOW			@  8-11 snow_00-03
	.byte	CASTLE, CASTLE, CASTLE, CASTLE		@ 12-15 keep_00-03 (K. Rool's keep)
	.byte	BEACH, BEACH, BEACH, BEACH		@ 16-19 lake_00-03 (no theme: water, like beach)
	.byte	BAYOU, BAYOU, BAYOU, BAYOU, BAYOU, BAYOU	@ 20-25 farm_00-05 (no theme: country, like bayou)
	.byte	BAYOU, BAYOU, BAYOU, BAYOU		@ 26-29 swamp_00-03 (bayou = swamp)
	.byte	HAUNTED, HAUNTED, HAUNTED, HAUNTED	@ 30-33 haunted_00-03
	.byte	BAYOU, BAYOU, BAYOU, BAYOU		@ 34-37 jungle_00-03 (no theme: jungle swamp, like bayou)
	.byte	LAVA, LAVA, LAVA, LAVA			@ 38-41 desert_00-03 (no theme: hot, like lava)
	.equ	RACE_TUNES_COUNT, . - race_tunes
	.balign 4

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

@ Front-end modes and the K. Rool's Gold course (used by the dogfight and
@ the story code).
	.equ	MODE_STORIES, 1
	.equ	KROOLS_GOLD_LEVEL, 6		@ Stories > K. Rool's Gold: Lava 01, a dogfight course


@ FIX "story-overlays": the old front-end's story mode draws a cut scene's
@ overlay sprites from a list at LOCAL_MEM+0x20. A scene without overlay
@ animation (init_cut_scene with 31, e.g. the K. Rool's Gold title card)
@ never sets that pointer, and the same bytes are a path number in map
@ scenes and partly cleared by init_story, so plot_cut_scene walked a stray
@ address, drew garbage sprites and crashed. Called from plot_cut_scene:
@ r5 = the overlay list, or an empty list when the scene has no overlay
@ animation (LOCAL_MEM+0x24 = 0). Keeps r4.
	.thumb_func
fix_cut_overlays_far:
	ldr	r5, =LOCAL_MEM
	ldr	r3, [r5, #0x24]
	cmp	r3, #0
	beq	1f
	ldr	r5, [r5, #0x20]
	bx	lr
1:	adr	r5, story_no_overlays
	bx	lr
	.ltorg
	.balign 4
story_no_overlays:				@ seven empty overlay slots
	.word	0, 0, 0, 0, 0, 0, 0

@ FIX "story-next-stage": move_map and fade_stuff call next_stage and then
@ carry on with registers it has clobbered (move_map stored through them,
@ fade_stuff could start a second stage). These go to the next stage and
@ then return from the caller (its frame is still on the stack).
	.thumb_func
fix_map_next_far:
	ldr	r3, =next_stage+1
	bl	2f
	ldr	r3, =move_map_out+1
	bx	r3
	.thumb_func
fix_fade_next_far:
	ldr	r3, =next_stage+1
	bl	2f
	ldr	r3, =fade_stuff_out+1
	bx	r3
2:	bx	r3
	.ltorg

@ FIX "krools-gold-story": the old front-end's story mode (title_story.s)
@ tells the K. Rool's Gold story in pictures and text, but nothing starts
@ it: the Stories menu just starts a race. Picking K. Rool's Gold now plays
@ the story first. When it reaches its first task it starts the race the
@ menu would have (Lava 01, a dogfight), where the story itself only had a
@ placeholder (game_level 1). Later chapters need the race's result to
@ come back into the story, which nothing does, so they stay unreached.

@ In place of menu_mode_get_level when menu_main starts the chosen race:
@ for K. Rool's Gold, hands over to the story instead (as menu_main hands
@ over to the old character select) and leaves menu_main.
	.thumb_func
fix_story_launch_far:
	push	{r4, lr}
	ldr	r3, =menu_mode_get_level+1
	bl	9f
	ldr	r1, =virtual_mode
	ldr	r1, [r1, #0]
	cmp	r1, #MODE_STORIES
	bne	1f
	cmp	r0, #KROOLS_GOLD_LEVEL
	bne	1f
	ldr	r1, =game_level
	str	r0, [r1, #0]
	ldr	r0, =LOCAL_MEM			@ a clean slate for the old front-end
	movs	r1, #0
	movs	r2, #0x34
2:	subs	r2, #1
	strb	r1, [r0, r2]
	bne	2b
	ldr	r3, =init_title+1
	bl	9f
	ldr	r3, =init_story+1
	bl	9f
	ldr	r0, =TITLE_STATE
	movs	r1, #5				@ story mode
	strb	r1, [r0, #0]
	pop	{r4}
	pop	{r3}				@ (menu_main's return into the race start)
	ldr	r3, =L_08012148+1		@ menu_main's exit
	bx	r3
1:	pop	{r4}
	pop	{r3}
	bx	r3
9:	bx	r3
	.ltorg

@ In place of the story's game_init when it reaches a task: start K. Rool's
@ Gold's course as the menu starts a race (front-end flag, sprites from 16,
@ game_init next frame).
	.thumb_func
fix_story_game_far:
	ldr	r0, =game_level
	movs	r1, #KROOLS_GOLD_LEVEL
	str	r1, [r0, #0]
	ldr	r2, =sys_flags
	ldr	r0, [r2, #0]
	movs	r1, #1
	lsls	r1, r1, #8
	orrs	r0, r1
	str	r0, [r2, #0]
	ldr	r1, =sys_oam_start
	movs	r0, #16
	strh	r0, [r1, #0]
	ldr	r1, =sys_mode
	ldr	r0, =game_init+1
	str	r0, [r1, #0]
	bx	lr
	.ltorg

@ FIX "charsel": the old front-end's character select. Its seven slots were
@ in screen order (Cranky, Redneck, Diddy, Kong, Krash, K. Rool, Dixie) and
@ the slot number went straight into CHAR_SELECTED, but the rest of the game
@ numbers characters Cranky 0, Diddy 1, Krunch 2, K. Rool 3, Dixie 4,
@ Kong 5, so most picks flew someone else; and the coloured cut-outs were
@ drawn 7 pixels right and 1 down of the sepia figures they highlight.
@ title_charsel.s now orders the slots Cranky, Diddy, Kong, Krash, K. Rool,
@ Dixie (the order of its voice tables) with Redneck unreachable at 6.

@ In place of start_game's menu_main_init: slot -> character number.
	.thumb_func
fix_charsel_start_far:
	ldr	r0, =CHAR_SELECTED
	ldrb	r1, [r0, #0]
	cmp	r1, #6
	bhs	1f
	adr	r2, charsel_characters
	ldrb	r1, [r2, r1]
	strb	r1, [r0, #0]
1:	ldr	r3, =menu_main_init+1
	bx	r3				@ returns to start_game
	.ltorg
	.balign 4
charsel_characters:				@ by slot
	.byte	0, 1, 5, 2, 3, 4		@ Cranky, Diddy, Kong, Krunch, K. Rool, Dixie
	.balign 4

@ In place of plot_char's "movs r0, #0; movs r1, #0": r0, r1 = the position
@ that lines the slot's cut-out up with its sepia figure. Measured against
@ the background: -7, -1 for all but Cranky, whose cut-out is an older,
@ hunched pose that best covers his figure at +12, -4.
	.thumb_func
fix_char_offset_far:
	ldr	r0, =CHAR_SELECTED
	ldrb	r0, [r0, #0]
	cmp	r0, #0
	bne	1f
	movs	r0, #12
	movs	r1, #4
	negs	r1, r1
	bx	lr
1:	movs	r0, #7
	negs	r0, r0
	movs	r1, #1
	negs	r1, r1
	bx	lr
	.ltorg

@ FIX "boot-logos": called from the main loop every frame in place of
@ AGBPrintFlush1Block. On the logos and intro (logo_process) or the title
@ screen's game-type carousel (title, TITLE_STATE 2), pressing L+R together
@ opens the debug menu, which the build used to boot into. Then flushes the
@ debug print buffer as before. r0-r3 are free here.
	.equ	KEY_R, 0x100
	.equ	KEY_L, 0x200
	.thumb_func
fix_debug_combo_far:
	push	{lr}
	ldr	r0, =sys_joycnt
	ldrh	r0, [r0, #0]
	ldr	r1, =KEY_L | KEY_R
	ands	r0, r1
	cmp	r0, r1				@ both held
	bne	9f
	ldr	r0, =sys_joytrg
	ldrh	r0, [r0, #0]
	tst	r0, r1				@ and one just pressed
	beq	9f
	ldr	r0, =sys_mode
	ldr	r0, [r0, #0]
	ldr	r1, =logo_process+1
	cmp	r0, r1
	beq	1f
	ldr	r1, =title+1
	cmp	r0, r1
	bne	9f
	ldr	r1, =TITLE_STATE
	ldrb	r1, [r1, #0]
	cmp	r1, #2				@ the game-type carousel
	bne	9f
1:	ldr	r3, =menu_init+1
	bl	2f
9:	ldr	r3, =AGBPrintFlush1Block+1
	bl	2f
	pop	{r0}
	bx	r0
2:	bx	r3
	.ltorg

@ FIX "hud-maps": init_hud_map picks the course map shown in a race with a
@ switch on game_level. Lava 01, Lake 01 and Haunted 02 have finished maps
@ in the sprite table (100, 106 and 114, each matching its course's layout)
@ but no case, so they showed none. Called in place of the switch's
@ "ldr r0, =game_level; ldr r0, [r0]": for those three, r6 = the map and
@ init_hud_map carries on at L_0800a07a; otherwise r0 = game_level for the
@ switch as before. (Farm 03's map, 111, is a copy of Farm 00's with "1/3"
@ on it, not its course, so it stays unused.)
	.thumb_func
fix_hud_map_far:
	ldr	r0, =game_level
	ldr	r0, [r0, #0]
	adr	r1, hud_map_extra
1:	ldrb	r2, [r1, #0]
	cmp	r2, #0
	beq	2f				@ not one of them
	cmp	r2, r0
	beq	3f
	adds	r1, #2
	b	1b
2:	bx	lr
3:	ldrb	r6, [r1, #1]
	ldr	r1, =L_0800a07a+1
	bx	r1
	.ltorg
hud_map_extra:					@ game_level, sprite
	.byte	6, 100				@ Lava 01
	.byte	17, 106				@ Lake 01
	.byte	32, 114				@ Haunted 02
	.ifdef UPDATES
	.byte	37, 111				@ Temple Tangle (updates: our map, in sprite 111)
	.endif
	.byte	0, 0
	.balign 4

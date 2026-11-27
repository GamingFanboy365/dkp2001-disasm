@ Updates patch: cups and the Clock Race return (new design, not Rare's).
@ Written for this project. The build has no cup or series code: picking a Racing
@ world plays only its first course, and every race returns to the game-type carousel.
@
@ Racing: a world is a cup of its four courses, in the order its Clock Race list shows
@ them (select_indices rows 4-8). Each race's intro says RACE 1 OF 4, RACE 2 OF 4,
@ RACE 3 OF 4 or FINAL RACE top right in the course-name font. When the player
@ finishes (or retires: last), the finishing order is taken and points given; after
@ the race the standings are shown with the racers' heads, then the next course's
@ intro starts. After the fourth race: the final standings, then the world list.
@ Clock Race: after a race, back to the course list at the course that was picked.
@
@ State lives in a small block at the top of work RAM (nothing else uses it), checked
@ by a signature. Hooks: game_init's course-name plot (cup_plot_name), game_process's
@ return to the title (cup_race_over), and the race monitor's per-frame hook
@ (cup_watch, from fix_df_positions_far).

	.section .fixes, "ax", %progbits
	.thumb
	.balign 2

	.equ	CUP, 0x0203ff00			@ our block (top of EWRAM; unused by the game)
	.equ	C_MAGIC, 0			@ word: CUP_MAGIC when valid
	.equ	C_MODE, 4			@ 0 Racing cup, 4 Clock Race, 0xff none
	.equ	C_WORLD, 5
	.equ	C_RACE, 6			@ 0-3
	.equ	C_TOKEN, 7			@ 1: a race we know about is under way
	.equ	C_NEXT, 8			@ 1: the next preview continues the cup
	.equ	C_DONE, 9			@ 1: this race's result is taken
	.equ	C_PHASE, 10			@ results screen: 0 set up, 1 showing
	.equ	C_LEVEL, 12			@ hword: Clock Race list position
	.equ	C_TIMER, 14			@ hword: frames on the results screen
	.equ	C_POINTS, 16			@ 4 bytes: points per player
	.equ	C_ORDER, 20			@ 4 bytes: this race's finishing order (player numbers)
	.equ	C_SORT, 24			@ 4 bytes: standings (player numbers)
	.equ	C_TEXT, 32			@ 16 bytes: text being plotted
	.equ	CUP_MAGIC, 0x31505543		@ "CUP1"

	.equ	MODE_RACING, 0
	.equ	MODE_CLOCK, 4
	.equ	MON_STATE, 80
	.equ	MON_PLACE, 106
	.equ	PLR_CHAR, 130
	.equ	KEY_A, 1
	.equ	KEY_START, 8
	.equ	TUNE_MENU, 3
	.equ	G_SPACE, 254
	.equ	G_END, 255
	.equ	G_DIGIT, 41			@ big font: digit d is glyph 41 + d

@ ---------------------------------------------------------------- the race's intro
@ Called in place of game_init's `bl _call_via_r3` that plots the course name
@ (r0 text, r1 120, r2 136; r3, plot_big_text, is used by the trampoline). Plots it, then notes the race and,
@ in a cup, plots which race it is.
	.thumb_func
cup_plot_name_far:
	push	{r4, r5, lr}
	bl	cup_plot			@ the course name, as before (the trampoline used r3)
	ldr	r4, =CUP
	ldrb	r0, [r4, #C_NEXT]
	cmp	r0, #0
	bne	2f
	@ a race picked from the menus: start afresh
	ldr	r0, =CUP_MAGIC
	str	r0, [r4, #C_MAGIC]
	movs	r1, #0xff
	ldr	r0, =current_mode
	ldr	r0, [r0, #0]
	cmp	r0, #MODE_RACING
	beq	1f
	cmp	r0, #MODE_CLOCK
	bne	3f
1:	adds	r1, r0, #0
3:	strb	r1, [r4, #C_MODE]
	ldr	r0, =current_select
	ldr	r0, [r0, #0]
	strb	r0, [r4, #C_WORLD]
	movs	r0, #0
	strb	r0, [r4, #C_RACE]
	str	r0, [r4, #C_POINTS]
	ldr	r0, =local_level
	ldr	r0, [r0, #0]
	strh	r0, [r4, #C_LEVEL]
2:	movs	r0, #0
	strb	r0, [r4, #C_NEXT]
	strb	r0, [r4, #C_DONE]
	movs	r0, #1
	strb	r0, [r4, #C_TOKEN]
	ldrb	r0, [r4, #C_MODE]
	cmp	r0, #MODE_RACING
	bne	9f
	@ RACE n OF 4 / FINAL RACE, top right (the name and this need more sprites)
	ldr	r1, =sys_oam_start
	movs	r0, #40
	strh	r0, [r1, #0]
	ldrb	r0, [r4, #C_RACE]
	lsls	r0, r0, #2
	adr	r1, race_texts
	ldr	r0, [r1, r0]
	movs	r1, #172
	movs	r2, #10
	bl	cup_plot
9:	pop	{r4, r5}
	pop	{r0}
	bx	r0

@ r0 text, r1 centre x, r2 top y: plot_big_text through its pointer
cup_plot:
	ldr	r3, =__ptr_plot_big_text
	ldr	r3, [r3, #0]
cup_bx_r3:
	bx	r3
cup_bx_r2:
	bx	r2
	.ltorg

	.balign 4
race_texts:
	.word	text_race1, text_race2, text_race3, text_final
text_race1:	.byte	17, 0, 2, 4, G_SPACE, G_DIGIT + 1, G_SPACE, 14, 5, G_SPACE, G_DIGIT + 4, G_END
text_race2:	.byte	17, 0, 2, 4, G_SPACE, G_DIGIT + 2, G_SPACE, 14, 5, G_SPACE, G_DIGIT + 4, G_END
text_race3:	.byte	17, 0, 2, 4, G_SPACE, G_DIGIT + 3, G_SPACE, 14, 5, G_SPACE, G_DIGIT + 4, G_END
text_final:	.byte	5, 8, 13, 0, 11, G_SPACE, 17, 0, 2, 4, G_END			@ FINAL RACE
text_results:	.byte	17, 4, 18, 20, 11, 19, 18, G_END				@ RESULTS
text_final_results: .byte 5, 8, 13, 0, 11, G_SPACE, 17, 4, 18, 20, 11, 19, 18, G_END
text_places:	.byte	G_DIGIT + 1, 18, 19, G_END				@ 1ST
		.byte	G_DIGIT + 2, 13, 3, G_END				@ 2ND
		.byte	G_DIGIT + 3, 17, 3, G_END				@ 3RD
		.byte	G_DIGIT + 4, 19, 7, G_END				@ 4TH
race_points:	.byte	10, 6, 3, 1						@ points for 1st-4th (ours)
	.balign 2

@ ---------------------------------------------------------------- the finish
@ Every frame of a race (race monitor). The first frame the player has finished
@ (state 4) or retired (5): take the finishing order from the race places, the player
@ last if retired, and give the points.
	.thumb_func
cup_watch:
	push	{r4, r5, r6, r7, lr}
	ldr	r4, =CUP
	ldr	r0, [r4, #C_MAGIC]
	ldr	r1, =CUP_MAGIC
	cmp	r0, r1
	bne	9f
	ldrb	r0, [r4, #C_MODE]
	cmp	r0, #MODE_RACING
	bne	9f
	ldrb	r0, [r4, #C_TOKEN]
	cmp	r0, #0
	beq	9f
	ldrb	r0, [r4, #C_DONE]
	cmp	r0, #0
	bne	9f
	ldr	r5, =monitor
	ldr	r5, [r5, #0]
	ldr	r6, [r5, #MON_STATE]
	cmp	r6, #4
	blt	9f
	@ order[place - 1] = player; a clash goes to the next free slot
	movs	r0, #0xff
	lsls	r1, r0, #8
	orrs	r0, r1
	lsls	r1, r0, #16
	orrs	r0, r1
	str	r0, [r4, #C_ORDER]
	movs	r7, #0				@ player
1:	adds	r0, r5, r7
	adds	r0, #MON_PLACE
	ldrb	r0, [r0, #0]
	subs	r0, #1
	cmp	r0, #3
	bls	2f
	movs	r0, #0
2:	adds	r1, r4, #0
	adds	r1, #C_ORDER
	ldrb	r2, [r1, r0]
	cmp	r2, #0xff
	beq	3f
	adds	r0, #1
	movs	r2, #3
	ands	r0, r2
	b	2b
3:	strb	r7, [r1, r0]
	adds	r7, #1
	cmp	r7, #3
	ble	1b
	cmp	r6, #5
	bne	5f
	@ retired: the player goes last, the others keep their order
	adds	r1, r4, #0
	adds	r1, #C_ORDER
	movs	r0, #0				@ read index
	movs	r2, #0				@ write index
4:	ldrb	r3, [r1, r0]
	cmp	r3, #0
	beq	6f
	strb	r3, [r1, r2]
	adds	r2, #1
6:	adds	r0, #1
	cmp	r0, #3
	ble	4b
	movs	r3, #0
	strb	r3, [r1, #3]
5:	@ points
	ldr	r6, =race_points
	movs	r7, #0
7:	adds	r0, r4, #0
	adds	r0, #C_ORDER
	ldrb	r0, [r0, r7]			@ player in place r7
	ldrb	r1, [r6, r7]
	adds	r2, r4, #0
	adds	r2, #C_POINTS
	ldrb	r3, [r2, r0]
	adds	r3, r3, r1
	strb	r3, [r2, r0]
	adds	r7, #1
	cmp	r7, #3
	ble	7b
	movs	r0, #1
	strb	r0, [r4, #C_DONE]
9:	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

@ ---------------------------------------------------------------- after a race
@ Called in place of game_process's `bl init_title` once a race has faded out.
	.thumb_func
cup_race_over_far:
	push	{r4, lr}
	ldr	r4, =CUP
	ldr	r0, [r4, #C_MAGIC]
	ldr	r1, =CUP_MAGIC
	cmp	r0, r1
	bne	8f
	ldrb	r0, [r4, #C_TOKEN]
	cmp	r0, #0
	beq	8f
	movs	r1, #0
	strb	r1, [r4, #C_TOKEN]
	ldrb	r0, [r4, #C_MODE]
	cmp	r0, #MODE_CLOCK
	beq	5f
	cmp	r0, #MODE_RACING
	bne	8f
	ldrb	r0, [r4, #C_DONE]
	cmp	r0, #0
	beq	7f				@ quit before the finish: the cup's over
	movs	r0, #0
	strb	r0, [r4, #C_PHASE]
	ldr	r0, =cup_results+1		@ the standings screen
	ldr	r1, =sys_mode
	str	r0, [r1, #0]
	b	9f
5:	@ Clock Race: back to the course list where the course was picked
	movs	r0, #0xff
	strb	r0, [r4, #C_MODE]
	ldr	r3, =menu_main_init+1
	bl	cup_bx_r3
	ldrh	r1, [r4, #C_LEVEL]
	ldr	r0, =local_level
	str	r1, [r0, #0]
	movs	r0, #0
	ldr	r3, =menu_mode_highlight+1
	bl	cup_bx_r3
	movs	r0, #TUNE_MENU
	ldr	r3, =audio_start_tune+1
	bl	cup_bx_r3
	b	9f
7:	movs	r0, #0
	str	r0, [r4, #C_MAGIC]
8:	ldr	r3, =init_title+1
	bl	cup_bx_r3
9:	pop	{r4}
	pop	{r0}
	bx	r0
	.ltorg

@ ---------------------------------------------------------------- the standings
@ A sys_mode of its own: our screen, drawn with sprites only (Rare's big font for the
@ text, Rare's racer heads). A or Start: the next race, or after the fourth, the
@ world list.
	.thumb_func
cup_results:
	push	{r4, r5, r6, r7, lr}
	ldr	r4, =CUP
	ldrb	r0, [r4, #C_PHASE]
	cmp	r0, #0
	bne	1f
	bl	results_draw
	movs	r0, #1
	strb	r0, [r4, #C_PHASE]
	movs	r0, #0
	strh	r0, [r4, #C_TIMER]
1:	ldrh	r0, [r4, #C_TIMER]
	adds	r0, #1
	strh	r0, [r4, #C_TIMER]
	cmp	r0, #45				@ a moment before a press counts
	blt	9f
	ldr	r0, =sys_joytrg
	ldrh	r0, [r0, #0]
	movs	r1, #KEY_A | KEY_START
	tst	r0, r1
	beq	9f
	ldrb	r0, [r4, #C_RACE]
	cmp	r0, #3
	bge	5f
	@ the next course: as the menu starts a race
	adds	r0, #1
	strb	r0, [r4, #C_RACE]
	movs	r1, #1
	strb	r1, [r4, #C_NEXT]
	ldrb	r1, [r4, #C_WORLD]
	adds	r1, #4				@ select_indices row 4 + world
	movs	r2, #24
	muls	r1, r2
	lsls	r0, r0, #2
	adds	r1, r1, r0
	ldr	r2, =select_indices
	ldr	r0, [r2, r1]
	adds	r0, #1
	ldr	r1, =game_level
	str	r0, [r1, #0]
	ldr	r2, =sys_flags
	ldr	r0, [r2, #0]
	lsrs	r0, r0, #8			@ clear the last race's low flags
	lsls	r0, r0, #8
	movs	r1, #128
	lsls	r1, r1, #1			@ 0x100: start with the course's intro
	orrs	r0, r1
	str	r0, [r2, #0]
	ldr	r1, =sys_oam_start
	movs	r0, #16
	strh	r0, [r1, #0]
	ldr	r0, =game_init+1
	ldr	r1, =sys_mode
	str	r0, [r1, #0]
	b	9f
5:	@ the cup's over: back to the world list
	movs	r0, #0
	str	r0, [r4, #C_MAGIC]
	ldr	r1, =sys_oam_start
	strh	r0, [r1, #0]
	ldr	r3, =menu_main_init+1
	bl	cup_bx_r3
	movs	r0, #TUNE_MENU
	ldr	r3, =audio_start_tune+1
	bl	cup_bx_r3
9:	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

@ Set up the screen and draw the standings (r4 = CUP).
results_draw:
	push	{r4, r5, r6, r7, lr}
	@ sprites only, no fade, a plain backdrop; the game's sprites kept off the OAM
	ldr	r0, =0x04000000
	ldr	r1, =0x1040			@ mode 0, OBJ on, 1D tiles
	strh	r1, [r0, #0]
	ldr	r0, =0x04000050
	movs	r1, #0
	strh	r1, [r0, #0]			@ BLDCNT
	strh	r1, [r0, #4]			@ BLDY
	ldr	r0, =0x05000000
	ldr	r1, =RESULTS_BACKDROP
	strh	r1, [r0, #0]
	ldr	r0, =sys_oam_start
	movs	r1, #128
	strh	r1, [r0, #0]
	ldr	r0, =0x07000000			@ every sprite hidden
	movs	r1, #2
	lsls	r1, r1, #8			@ attr0 0x200
	movs	r2, #128
1:	strh	r1, [r0, #0]
	adds	r0, #8
	subs	r2, #1
	bne	1b
	ldr	r1, =OAM_PTR
	ldr	r0, =0x07000000
	str	r0, [r1, #0]
	ldr	r1, =OBJVRAM_PTR
	ldr	r0, =0x06016000
	str	r0, [r1, #0]
	ldr	r0, =__ptr_init_big_font
	ldr	r1, [r0, #0]
	movs	r0, #15
	bl	cup_bx_r1
	@ the title
	ldrb	r0, [r4, #C_RACE]
	cmp	r0, #3
	bge	2f
	ldr	r0, =text_results
	b	3f
2:	ldr	r0, =text_final_results
3:	movs	r1, #120
	movs	r2, #8
	bl	cup_plot
	@ standings: this race's order, then stable-sorted by points (most first)
	ldr	r0, [r4, #C_ORDER]
	str	r0, [r4, #C_SORT]
	adds	r5, r4, #0
	adds	r5, #C_SORT
	movs	r6, #1
4:	adds	r7, r6, #0
5:	cmp	r7, #0
	beq	7f
	subs	r0, r7, #1
	ldrb	r1, [r5, r0]			@ the one above
	ldrb	r2, [r5, r7]
	adds	r3, r4, #0
	adds	r3, #C_POINTS
	ldrb	r1, [r3, r1]
	ldrb	r2, [r3, r2]
	cmp	r2, r1
	ble	7f
	ldrb	r1, [r5, r0]			@ swap
	ldrb	r2, [r5, r7]
	strb	r2, [r5, r0]
	strb	r1, [r5, r7]
	subs	r7, #1
	b	5b
7:	adds	r6, #1
	cmp	r6, #3
	ble	4b
	@ one row per racer
	movs	r6, #0
8:	movs	r7, #28
	muls	r7, r6
	adds	r7, #38				@ r7 = the row's top
	ldr	r0, =text_places			@ 1ST..4TH
	lsls	r1, r6, #2
	adds	r0, r0, r1
	movs	r1, #44
	adds	r2, r7, #0
	bl	cup_plot
	ldrb	r0, [r5, r6]			@ the racer
	ldr	r1, =players
	lsls	r0, r0, #2
	ldr	r0, [r1, r0]
	adds	r0, #PLR_CHAR
	ldrh	r0, [r0, #0]			@ its character
	adds	r1, r6, #0			@ slot
	movs	r2, #92				@ x
	adds	r3, r7, #0			@ y
	bl	draw_head
	@ points: "nn PTS"
	ldrb	r0, [r5, r6]
	adds	r1, r4, #0
	adds	r1, #C_POINTS
	ldrb	r0, [r1, r0]
	adds	r1, r4, #0
	adds	r1, #C_TEXT
	movs	r2, #0				@ tens
9:	cmp	r0, #10
	blt	10f
	subs	r0, #10
	adds	r2, #1
	b	9b
10:	cmp	r2, #0
	beq	11f
	adds	r2, #G_DIGIT
	strb	r2, [r1, #0]
	adds	r1, #1
11:	adds	r0, #G_DIGIT
	strb	r0, [r1, #0]
	movs	r0, #G_SPACE
	strb	r0, [r1, #1]
	movs	r0, #15				@ P
	strb	r0, [r1, #2]
	movs	r0, #19				@ T
	strb	r0, [r1, #3]
	movs	r0, #18				@ S, unless it's 1 PT
	strb	r0, [r1, #4]
	movs	r0, #G_END
	strb	r0, [r1, #5]
	cmp	r2, #0
	bne	12f
	ldrb	r2, [r1, #0]
	cmp	r2, #G_DIGIT + 1
	bne	12f
	strb	r0, [r1, #4]
12:
	adds	r0, r4, #0
	adds	r0, #C_TEXT
	movs	r1, #176
	adds	r2, r7, #0
	bl	cup_plot
	adds	r6, #1
	cmp	r6, #3
	ble	8b
	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
cup_bx_r1:
	bx	r1
	.ltorg

@ draw_head(character r0, slot r1, x r2, y r3): Rare's head sprite for a racer
@ (get_player_head's choice), decoded from its sprite data into OBJ VRAM at
@ slot * 16 tiles, its palette into OBJ palette bank `slot`, and its pieces written
@ at OAM_PTR (which moves on).
draw_head:
	push	{r4, r5, r6, r7, lr}
	sub	sp, #12
	str	r1, [sp, #0]
	str	r2, [sp, #4]
	str	r3, [sp, #8]
	cmp	r0, #5
	bls	1f
	movs	r0, #1
1:	lsls	r0, r0, #2
	adr	r2, head_sprites
	ldr	r4, [r2, r0]			@ r4 = the sprite
	adr	r2, head_palettes
	ldr	r5, [r2, r0]			@ r5 = its palette
	@ palette: 16 colours to OBJ bank `slot`
	ldr	r0, =0x05000200
	lsls	r2, r1, #5
	adds	r0, r0, r2
	movs	r2, #0
2:	ldrh	r3, [r5, r2]
	strh	r3, [r0, r2]
	adds	r2, #2
	cmp	r2, #32
	blt	2b
	@ tiles: run-length decoded (as spr_update_vram) to OBJ VRAM + slot * 512
	ldrh	r0, [r4, #0]
	adds	r6, r4, r0			@ r6 = the frame's tile table
	ldrh	r0, [r6, #0]
	lsls	r0, r0, #4
	adds	r6, r6, r0			@ r6 = the tile block
	ldr	r7, =0x06010000
	lsls	r0, r1, #9
	adds	r7, r7, r0			@ r7 = destination
	adds	r6, #2
3:	ldrh	r0, [r6, #0]			@ command
	adds	r6, #2
	cmp	r0, #0
	beq	6f
	movs	r1, #0x7f
	ands	r1, r0
	adds	r1, #1				@ count
	movs	r2, #0x80
	tst	r0, r2
	beq	4f
5:	ldrh	r2, [r6, #0]			@ literal hwords
	strh	r2, [r7, #0]
	adds	r6, #2
	adds	r7, #2
	subs	r1, #1
	bne	5b
	b	3b
4:	lsrs	r0, r0, #8			@ a run of one byte value
	lsls	r2, r0, #8
	orrs	r0, r2
7:	strh	r0, [r7, #0]
	adds	r7, #2
	subs	r1, #1
	bne	7b
	b	3b
6:	@ pieces: frame 0's OAM records (attr0, attr1, tile), placed at x, y
	ldrh	r0, [r4, #14]
	adds	r6, r4, r0			@ r6 = the frame
	ldrh	r5, [r6, #0]			@ r5 = piece count
	adds	r6, #2
	ldr	r7, =OAM_PTR
	ldr	r7, [r7, #0]
8:	ldrh	r0, [r6, #0]			@ attr0: y in the low byte
	ldr	r1, [sp, #8]
	lsls	r2, r0, #24
	asrs	r2, r2, #24
	adds	r1, r1, r2
	movs	r2, #0xff
	ands	r1, r2
	lsrs	r0, r0, #8
	lsls	r0, r0, #8
	orrs	r0, r1
	strh	r0, [r7, #0]
	ldrh	r0, [r6, #2]			@ attr1: x in the low 9 bits
	ldr	r1, [sp, #4]
	lsls	r2, r0, #23
	asrs	r2, r2, #23
	adds	r1, r1, r2
	ldr	r2, =0x1ff
	ands	r1, r2
	lsrs	r0, r0, #9
	lsls	r0, r0, #9
	orrs	r0, r1
	strh	r0, [r7, #2]
	ldrh	r0, [r6, #4]			@ attr2: tile + slot * 16, palette bank slot
	ldr	r1, [sp, #0]
	lsls	r2, r1, #4
	adds	r0, r0, r2
	lsls	r1, r1, #12
	orrs	r0, r1
	strh	r0, [r7, #4]
	adds	r6, #6
	adds	r7, #8
	subs	r5, #1
	bne	8b
	ldr	r0, =OAM_PTR
	str	r7, [r0, #0]
	add	sp, #12
	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

	.balign 4
@ by game character (0 Cranky, 1 Diddy, 2 Krunch, 3 K. Rool, 4 Dixie, 5 Kong), as
@ get_player_head picks them
head_sprites:
	.word	__spr_cranky_head, __spr_diddy_head, __spr_krunch_head
	.word	__spr_krool_head, __spr_dixie_head, __spr_donkey_head
head_palettes:
	.word	__pal_cranky_head, __pal_diddy_head, __pal_krunch_head
	.word	__pal_krool_head, __pal_dixie_head, __pal_donkey_head
	.equ	RESULTS_BACKDROP, 0x4022	@ deep blue (BGR555); the final results get art later

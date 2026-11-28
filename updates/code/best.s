@ Updates patch: Clock Race best times (new design, not Rare's).
@ Written for this project. The build saves nothing (state_level_save and friends are
@ empty stubs, and the cartridge names no save type), so this adds a small save of its
@ own in battery-backed SRAM: the signature below tells emulators and flash carts the
@ cartridge has SRAM; our table lives at its start.
@
@ Each course (by game level) keeps its five best Clock Race times, each with three
@ initials and the racer who set it. After a Clock Race the player finished (or retired),
@ BEST TIMES shows the course's chart over a jungle clearing: a time good enough goes in
@ at its place, and the player enters initials (Up/Down pick a letter, A or Right the
@ next, B or Left back); A or Start then returns to the course list. The Clock Race
@ course list shows the highlighted course's best time under the courses, in the menu's
@ own small font (Rare's menu text system, by reference).
@ Only Clock Race: Racing cups, Stories and the debug menu are unchanged.

	.section .fixes, "ax", %progbits
	.balign 4
	.ascii	"SRAM_V113"			@ the save type, as cartridges name it
	.balign 4
save_magic:
	.ascii	"DKB1"
	.thumb
	.balign 2

	.equ	SRAM, 0x0e000000		@ 8-bit bus: bytes only
	.equ	S_BASE, 0x200			@ ours from here (the boot code writes 0x55 at 0, 0xaa at 0x100)
	.equ	S_RECS, 16			@ the table: by game level (1-41)
	.equ	REC_SIZE, 40			@ 5 x {time (3 bytes, frames), initials (3), racer, 0}
	.equ	S_END, S_RECS + 42 * REC_SIZE
	.equ	BEST, 0x0203ff70		@ our state, in the cup block's spare bytes
	.equ	B_LEVEL, 0			@ the course
	.equ	B_RANK, 1			@ the new time's row (0-4), 5 none
	.equ	B_CURSOR, 2			@ the initial being entered (3: done)
	.equ	B_PHASE, 3			@ 0 set up, 1 showing
	.equ	B_TIMER, 4			@ hword: frames shown
	.equ	B_OAM, 8			@ word: the OAM entry after the fixed part
	.equ	B_NAME, 12			@ 32 bytes: the course name (big font)
	.equ	B_REC, 48			@ 40 bytes: the course's records
	.equ	B_LETTER, 88			@ 3 bytes: one initial, to plot
	.equ	BEST_MENU, 0x0203ffd0		@ the menu line
	.equ	M_HANDLE, 0			@ its menu text handle, 0 none
	.equ	M_LEVEL, 1			@ the course it shows
	.equ	M_SAVE, 4			@ 24 bytes: menu text handle 0's settings
	.equ	M_TEXT, 28			@ 24 bytes: the line
	.equ	ROW_Y, 40			@ the first row; rows 21 apart
	.equ	ROW_GAP, 21
	.equ	INIT_X, 76			@ the initials' left edge (9 apart)
	.equ	KEY_B, 2
	.equ	KEY_RIGHT, 16
	.equ	KEY_LEFT, 32
	.equ	KEY_UP, 64
	.equ	KEY_DOWN, 128
	.equ	TUNE_BEST, 15			@ updates/music/tune_list.s
	.equ	SMALL_BANK, 14			@ the small font's palette bank
	.equ	SF_WHITE, 247			@ small font colours (smallfont_plt)
	.equ	SF_CREAM, 252
	.equ	SF_GREEN, 250
	.equ	PLACE_X, 14			@ the rows' columns (the plane is to the right)
	.equ	HEAD_X, 52
	.equ	TIME_X, 116
	.equ	B_VRAM, 92			@ word: OBJVRAM_PTR after the fixed part
	.equ	MENU_FONT_SMALL, 2		@ the menu's small font (world names, NOVICE)
	.equ	MENU_TEXT_PAL, 15
	.equ	HANDLE_SIZE, 132		@ menu_text.c: a text handle
	.equ	H_CHARS, 88

@ ---------------------------------------------------------------- the save
@ Makes sure the save holds our table; a blank or foreign one is cleared (every time
@ empty). Keeps r4-r7.
best_check:
	push	{r4, lr}
	ldr	r0, =0x04000204			@ WAITCNT: SRAM at 8 cycles, as cartridges want
	ldrh	r1, [r0, #0]
	movs	r2, #3
	orrs	r1, r2
	strh	r1, [r0, #0]
	ldr	r0, =SRAM + S_BASE
	ldr	r1, =save_magic
	movs	r2, #0
1:	ldrb	r3, [r0, r2]
	ldrb	r4, [r1, r2]
	cmp	r3, r4
	bne	2f
	adds	r2, #1
	cmp	r2, #4
	blt	1b
	b	9f
2:	movs	r2, #S_RECS
	ldr	r3, =S_END
	movs	r4, #0xff
3:	strb	r4, [r0, r2]
	adds	r2, #1
	cmp	r2, r3
	blt	3b
	movs	r2, #0
4:	ldrb	r3, [r1, r2]
	strb	r3, [r0, r2]
	adds	r2, #1
	cmp	r2, #4
	blt	4b
9:	pop	{r4}
	pop	{r0}
	bx	r0
	.ltorg

@ r0 = level -> r0 = its records in the save.
rec_addr:
	movs	r1, #REC_SIZE
	muls	r0, r1
	adds	r0, #S_RECS
	ldr	r1, =SRAM + S_BASE
	adds	r0, r0, r1
	bx	lr

@ best_load(level r0): its records into BEST + B_REC.
best_load:
	push	{r4, lr}
	adds	r4, r0, #0
	bl	best_check
	adds	r0, r4, #0
	bl	rec_addr
	ldr	r1, =BEST + B_REC
	movs	r2, #0
1:	ldrb	r3, [r0, r2]
	strb	r3, [r1, r2]
	adds	r2, #1
	cmp	r2, #REC_SIZE
	blt	1b
	pop	{r4}
	pop	{r0}
	bx	r0

@ best_store(level r0): BEST + B_REC into the save.
best_store:
	push	{r4, lr}
	adds	r4, r0, #0
	bl	best_check
	adds	r0, r4, #0
	bl	rec_addr
	ldr	r1, =BEST + B_REC
	movs	r2, #0
1:	ldrb	r3, [r1, r2]
	strb	r3, [r0, r2]
	adds	r2, #1
	cmp	r2, #REC_SIZE
	blt	1b
	pop	{r4}
	pop	{r0}
	bx	r0

@ r0 = a record -> r0 = its time (EMPTY_TIME if none).
rec_time:
	ldrb	r1, [r0, #2]
	lsls	r1, r1, #8
	ldrb	r2, [r0, #1]
	orrs	r1, r2
	lsls	r1, r1, #8
	ldrb	r2, [r0, #0]
	orrs	r1, r2
	adds	r0, r1, #0
	bx	lr
	.ltorg

@ ---------------------------------------------------------------- the chart
@ From the race's end (cup_race_over_far, Clock Race, the player finished or retired).
best_start:
	ldr	r0, =game_level
	ldr	r0, [r0, #0]
	ldr	r1, =BEST
	strb	r0, [r1, #B_LEVEL]
	movs	r0, #0
	strb	r0, [r1, #B_PHASE]
	ldr	r1, =BEST_MENU			@ the menu line: shown afresh on the way back
	movs	r0, #0xff
	strb	r0, [r1, #M_LEVEL]
	ldr	r0, =best_screen+1		@ a sys_mode of its own
	ldr	r1, =sys_mode
	str	r0, [r1, #0]
	bx	lr

	.thumb_func
best_screen:
	push	{r4, r5, r6, r7, lr}
	ldr	r4, =BEST
	ldrb	r0, [r4, #B_PHASE]
	cmp	r0, #0
	bne	1f
	bl	best_setup
	movs	r0, #1
	strb	r0, [r4, #B_PHASE]
	movs	r0, #0
	strh	r0, [r4, #B_TIMER]
1:	ldrh	r0, [r4, #B_TIMER]
	adds	r0, #1
	strh	r0, [r4, #B_TIMER]
	ldrb	r1, [r4, #B_RANK]
	cmp	r1, #5
	bhs	5f
	ldrb	r1, [r4, #B_CURSOR]
	cmp	r1, #3
	bhs	5f
	bl	best_edit
	b	9f
5:	cmp	r0, #45				@ a moment before a press counts
	blt	9f
	ldr	r0, =sys_joytrg
	ldrh	r0, [r0, #0]
	movs	r1, #KEY_A | KEY_START
	tst	r0, r1
	beq	9f
	movs	r0, #0
	strb	r0, [r4, #B_PHASE]
	bl	clock_return			@ back to the course list (updates/code/cup.s)
9:	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

@ Set up the screen (r4 = BEST): the records, the new time in its place, the fixed part.
best_setup:
	push	{r4, r5, r6, r7, lr}
	bl	screen_setup
	movs	r0, #2				@ the jungle clearing (cup_results/paint.py)
	bl	results_background
	ldrb	r0, [r4, #B_LEVEL]
	bl	best_load
	movs	r0, #5
	strb	r0, [r4, #B_RANK]
	movs	r0, #0
	strb	r0, [r4, #B_CURSOR]
	adds	r7, r4, #0
	adds	r7, #B_REC
	ldr	r0, =CUP
	ldr	r5, [r0, #C_FINISH]		@ the player's time; 0 if retired
	cmp	r5, #0
	beq	20f
	movs	r6, #0
1:	lsls	r0, r6, #3
	adds	r0, r7, r0
	bl	rec_time
	cmp	r5, r0
	blo	2f				@ better than this row's (an empty one is 0xffffff)
	adds	r6, #1
	cmp	r6, #5
	blt	1b
	b	20f
2:	lsls	r3, r6, #3			@ rows from here move down one (the last drops)
	movs	r2, #32
3:	subs	r2, #1
	cmp	r2, r3
	blt	4f
	ldrb	r0, [r7, r2]
	adds	r1, r2, #0
	adds	r1, #REC_SIZE / 5
	strb	r0, [r7, r1]
	b	3b
4:	adds	r0, r7, r3			@ the new row: the time, AAA, the racer
	strb	r5, [r0, #0]
	lsrs	r1, r5, #8
	strb	r1, [r0, #1]
	lsrs	r1, r5, #16
	strb	r1, [r0, #2]
	movs	r1, #0
	strb	r1, [r0, #3]
	strb	r1, [r0, #4]
	strb	r1, [r0, #5]
	strb	r1, [r0, #7]
	ldr	r1, =players
	ldr	r1, [r1, #0]
	adds	r1, #PLR_CHAR
	ldrh	r1, [r1, #0]
	strb	r1, [r0, #6]
	strb	r6, [r4, #B_RANK]
20:	@ BEST TIMES (the big font: the title only) and the course's name (small font)
	movs	r0, #SMALL_BANK
	ldr	r3, =init_small_font+1
	bl	best_bx_r3
	ldr	r0, =text_best_times
	movs	r1, #120
	movs	r2, #4
	bl	cup_plot
	ldrb	r0, [r4, #B_LEVEL]
	adds	r1, r4, #0
	adds	r1, #B_NAME + 1
	ldr	r3, =menu_mode_get_old_level_text+1
	bl	best_bx_r3
	adds	r0, r4, #0
	adds	r0, #B_NAME
	movs	r1, #SF_CREAM
	strb	r1, [r0, #0]
	movs	r1, #120
	movs	r2, #24
	movs	r3, #1
	bl	small_text
	@ the rows: place (HUD digit + small suffix), head, initials, time
	movs	r6, #0
5:	movs	r5, #ROW_GAP
	muls	r5, r6
	adds	r5, #ROW_Y			@ r5 = the row's top
	adds	r0, r6, #1			@ 1-5 in Rare's HUD digits
	movs	r1, #PLACE_X
	adds	r2, r5, #0
	bl	draw_glyph
	ldr	r0, =text_suffixes		@ st nd rd th th
	lsls	r1, r6, #2
	adds	r0, r0, r1
	movs	r1, #PLACE_X + 9
	adds	r2, r5, #7
	movs	r3, #0
	bl	small_text
	lsls	r0, r6, #3
	adds	r0, r7, r0
	bl	rec_time
	ldr	r1, =EMPTY_TIME
	cmp	r0, r1
	beq	8f				@ an empty row: just -'--"--
	lsls	r0, r6, #3			@ the racer's head
	adds	r0, r7, r0
	ldrb	r0, [r0, #6]
	adds	r1, r6, #0			@ slot
	movs	r2, #HEAD_X - 18
	adds	r3, r5, #0
	subs	r3, #10
	bl	draw_head
	ldrb	r0, [r4, #B_RANK]
	cmp	r0, r6
	beq	7f				@ the row being entered: drawn as it changes
	lsls	r0, r6, #3			@ the initials
	adds	r0, r7, r0
	adds	r0, #3
	ldr	r1, =CUP + C_TEXT
	movs	r2, #SF_WHITE
	strb	r2, [r1, #0]
	ldrb	r2, [r0, #0]
	strb	r2, [r1, #1]
	ldrb	r2, [r0, #1]
	strb	r2, [r1, #2]
	ldrb	r2, [r0, #2]
	strb	r2, [r1, #3]
	movs	r2, #G_END
	strb	r2, [r1, #4]
	adds	r0, r1, #0
	movs	r1, #INIT_X
	adds	r2, r5, #4
	movs	r3, #0
	bl	small_text
7:	lsls	r0, r6, #3
	adds	r0, r7, r0
	bl	rec_time
8:	movs	r1, #TIME_X			@ the time
	adds	r2, r5, #0
	ldr	r3, =OAM_PTR
	ldr	r3, [r3, #0]
	bl	draw_time
	ldr	r1, =OAM_PTR
	str	r0, [r1, #0]
	adds	r6, #1
	cmp	r6, #4
	ble	5b
	@ a new record: say so. The chart's own tune (updates/music/best_times.py)
	movs	r0, #TUNE_BEST
	ldrb	r1, [r4, #B_RANK]
	cmp	r1, #5
	bhs	10f
	ldr	r0, =text_new_record
	movs	r1, #(PLACE_X + TIME_X + 50) / 2	@ under the rows
	movs	r2, #148
	movs	r3, #1
	bl	small_text
	movs	r0, #TUNE_BEST
10:	ldr	r3, =audio_start_tune+1
	bl	best_bx_r3
	ldr	r0, =OAM_PTR			@ the initials being entered go after this
	ldr	r0, [r0, #0]
	str	r0, [r4, #B_OAM]
	ldr	r0, =OBJVRAM_PTR
	ldr	r0, [r0, #0]
	str	r0, [r4, #B_VRAM]
	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

@ Entering initials (r4 = BEST), each frame: Up/Down change the letter, A or Right go to
@ the next, B or Left back. After the third, the records are saved. Then the three are
@ drawn (small font), the current one blinking.
best_edit:
	push	{r4, r5, r6, r7, lr}
	ldrb	r0, [r4, #B_RANK]
	lsls	r0, r0, #3
	adds	r7, r4, r0
	adds	r7, #B_REC + 3			@ r7 = the row's initials
	ldrb	r6, [r4, #B_CURSOR]
	ldr	r0, =sys_joytrg
	ldrh	r5, [r0, #0]
	ldrb	r0, [r7, r6]			@ the letter, 0-25
	movs	r1, #KEY_UP
	tst	r5, r1
	beq	1f
	adds	r0, #1
	cmp	r0, #25
	ble	1f
	movs	r0, #0
1:	movs	r1, #KEY_DOWN
	tst	r5, r1
	beq	2f
	subs	r0, #1
	bpl	2f
	movs	r0, #25
2:	strb	r0, [r7, r6]
	movs	r1, #KEY_A | KEY_RIGHT
	tst	r5, r1
	beq	3f
	adds	r6, #1
	strb	r6, [r4, #B_CURSOR]
	cmp	r6, #3
	blt	4f
	ldrb	r0, [r4, #B_LEVEL]		@ all three: keep them
	bl	best_store
	movs	r0, #0
	strh	r0, [r4, #B_TIMER]
	b	4f
3:	movs	r1, #KEY_B | KEY_LEFT
	tst	r5, r1
	beq	4f
	cmp	r6, #0
	beq	4f
	subs	r6, #1
	strb	r6, [r4, #B_CURSOR]
4:	@ draw the three, in the sprites and video memory after the fixed part
	ldr	r0, [r4, #B_OAM]
	ldr	r1, =OAM_PTR
	str	r0, [r1, #0]
	ldr	r0, [r4, #B_VRAM]
	ldr	r1, =OBJVRAM_PTR
	str	r0, [r1, #0]
	movs	r6, #0
5:	adds	r1, r4, #0
	adds	r1, #B_LETTER
	movs	r0, #SF_WHITE
	strb	r0, [r1, #0]
	ldrb	r0, [r7, r6]
	strb	r0, [r1, #1]
	movs	r0, #G_END
	strb	r0, [r1, #2]
	adds	r0, r1, #0
	movs	r1, #9
	muls	r1, r6
	adds	r1, #INIT_X
	ldrb	r2, [r4, #B_RANK]
	movs	r3, #ROW_GAP
	muls	r2, r3
	adds	r2, #ROW_Y + 4
	movs	r3, #0
	bl	small_text
	ldrb	r0, [r4, #B_CURSOR]
	cmp	r0, r6
	bne	6f
	ldrh	r0, [r4, #B_TIMER]		@ the current one blinks
	movs	r1, #16
	tst	r0, r1
	beq	6f
	ldr	r0, =OAM_PTR
	ldr	r0, [r0, #0]
	subs	r0, #8
	movs	r1, #2
	lsls	r1, r1, #8			@ attr0 0x200: hidden
	strh	r1, [r0, #0]
6:	adds	r6, #1
	cmp	r6, #2
	ble	5b
	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

@ small_text(text r0, x r1, y r2, centred r3): Rare's small font (plot_small_text, which
@ uses r8-r11 unsaved: kept here). One sprite per 32 pixels, at OAM_PTR / OBJVRAM_PTR.
small_text:
	push	{r4, r5, r6, r7, lr}
	mov	r4, r8
	mov	r5, r9
	mov	r6, sl
	mov	r7, fp
	push	{r4, r5, r6, r7}
	ldr	r4, =plot_small_text+1
	bl	best_bx_r4
	pop	{r4, r5, r6, r7}
	mov	r8, r4
	mov	r9, r5
	mov	sl, r6
	mov	fp, r7
	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0

@ draw_glyph(glyph r0, x r1, y r2): one of load_glyphs' 8x16 glyphs at OAM_PTR.
draw_glyph:
	push	{r4, lr}
	ldr	r4, =OAM_PTR
	ldr	r3, [r4, #0]
	movs	r2, r2				@ y
	lsls	r2, r2, #24
	lsrs	r2, r2, #24
	movs	r4, #128
	lsls	r4, r4, #8			@ 0x8000: tall shape
	orrs	r2, r4
	strh	r2, [r3, #0]
	strh	r1, [r3, #2]			@ x, size 0
	ldr	r4, =CUP
	ldrh	r1, [r4, #C_TB]
	lsls	r0, r0, #1
	adds	r1, r1, r0
	ldrb	r2, [r4, #C_PB]
	lsls	r2, r2, #12
	orrs	r1, r2
	strh	r1, [r3, #4]
	adds	r3, #8
	ldr	r4, =OAM_PTR
	str	r3, [r4, #0]
	pop	{r4}
	pop	{r0}
	bx	r0
best_bx_r3:
	bx	r3
best_bx_r4:
	bx	r4
	.ltorg

	.balign 2
text_best_times:	.byte	1, 4, 18, 19, G_SPACE, 19, 8, 12, 4, 18, G_END	@ BEST TIMES
@ small font: A-Z 0-25, ! 29, a-z 32-57; 247 + n picks its colour n (0 white, 5 cream...)
text_new_record:	.byte	SF_GREEN, 13, 4, 22, G_SPACE, 17, 4, 2, 14, 17, 3, 29, G_END	@ NEW RECORD!
text_suffixes:	.byte	SF_CREAM, 32 + 18, 32 + 19, G_END			@ st
		.byte	SF_CREAM, 32 + 13, 32 + 3, G_END			@ nd
		.byte	SF_CREAM, 32 + 17, 32 + 3, G_END			@ rd
		.byte	SF_CREAM, 32 + 19, 32 + 7, G_END			@ th
		.byte	SF_CREAM, 32 + 19, 32 + 7, G_END			@ th
	.balign 2

@ ---------------------------------------------------------------- the menu line
@ In place of menu_mode_draw's menu_coin_draw (fix_best_menu, menu_text.c.s): that,
@ then on the Clock Race course list, BEST TIME and the highlighted course's best
@ (BEST TIME 1'23''45, or -'--''-- if none) in the menu's small font, under the
@ courses; elsewhere, none.
	.thumb_func
best_menu_far:
	push	{r4, r5, r6, r7, lr}
	ldr	r3, =menu_coin_draw+1
	bl	best_bx_r3
	ldr	r4, =BEST_MENU
	ldr	r0, =current_mode
	ldr	r0, [r0, #0]
	cmp	r0, #MODE_CLOCK
	bne	8f
	ldr	r0, =current_language
	ldr	r0, [r0, #0]
	cmp	r0, #0
	bne	8f				@ (English only)
	ldr	r0, =virtual_mode		@ a world's course list: rows 4-8
	ldr	r1, [r0, #0]
	cmp	r1, #4
	blt	8f
	cmp	r1, #8
	bgt	8f
	movs	r0, #24
	muls	r1, r0
	ldr	r0, =current_select
	ldr	r0, [r0, #0]
	cmp	r0, #3
	bhi	8f
	lsls	r0, r0, #2
	adds	r1, r1, r0
	ldr	r0, =select_indices
	ldr	r5, [r0, r1]
	adds	r5, #1				@ r5 = the course's game level
	bl	menu_line_valid
	cmp	r0, #0
	beq	1f
	ldrb	r0, [r4, #M_LEVEL]
	cmp	r0, r5
	beq	9f				@ already showing it
1:	bl	best_menu_remove
	adds	r0, r5, #0
	strb	r0, [r4, #M_LEVEL]
	bl	best_load			@ (BEST + B_REC; the chart isn't showing)
	ldr	r0, =BEST + B_REC
	bl	rec_time
	bl	menu_line_text
	@ print it with handle 0's settings for the small font, then put them back
	ldr	r6, =handles
	movs	r2, #0
2:	ldrb	r3, [r6, r2]
	adds	r1, r4, #M_SAVE
	strb	r3, [r1, r2]
	adds	r2, #1
	cmp	r2, #24
	blt	2b
	movs	r0, #0
	movs	r1, #MENU_FONT_SMALL
	ldr	r3, =menu_text_set_font_handle+1
	bl	best_bx_r3
	movs	r0, #0
	movs	r1, #10
	movs	r2, #145
	ldr	r3, =menu_text_set_xy_handle+1
	bl	best_bx_r3
	adds	r0, r4, #0
	adds	r0, #M_TEXT
	ldr	r3, =menu_text_printf+1
	bl	best_bx_r3
	strb	r0, [r4, #M_HANDLE]
	movs	r2, #0
3:	adds	r1, r4, #M_SAVE
	ldrb	r3, [r1, r2]
	strb	r3, [r6, r2]
	adds	r2, #1
	cmp	r2, #24
	blt	3b
	ldrb	r0, [r4, #M_HANDLE]
	movs	r1, #MENU_TEXT_PAL
	ldr	r3, =menu_text_set_palette_handle+1
	bl	best_bx_r3
	ldrb	r0, [r4, #M_HANDLE]
	movs	r1, #0
	ldr	r3, =menu_text_set_shadow_handle+1
	bl	best_bx_r3
	ldrb	r0, [r4, #M_HANDLE]
	movs	r1, #0
	ldr	r3, =menu_text_set_callback_handle+1
	bl	best_bx_r3
	b	9f
8:	bl	best_menu_remove
9:	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

@ In place of menu_mode_kill's menu_coin_kill (fix_best_menu_kill): that, then the
@ line goes.
	.thumb_func
best_menu_kill_far:
	push	{r4, lr}
	ldr	r3, =menu_coin_kill+1
	bl	best_bx_r3
	ldr	r4, =BEST_MENU
	bl	best_menu_remove
	pop	{r4}
	pop	{r0}
	bx	r0

@ r4 = BEST_MENU: r0 = 1 if our line's handle is live (in use and still our text).
menu_line_valid:
	ldrb	r0, [r4, #M_HANDLE]
	cmp	r0, #0
	beq	9f
	cmp	r0, #31
	bhi	8f
	movs	r1, #HANDLE_SIZE
	muls	r0, r1
	ldr	r1, =handles
	adds	r1, r1, r0
	movs	r2, #0
	ldrsh	r0, [r1, r2]
	cmp	r0, #0
	beq	8f
	adds	r1, #H_CHARS
	ldrb	r0, [r1, #0]
	cmp	r0, #'B'
	bne	8f
	ldrb	r0, [r1, #1]
	cmp	r0, #'E'
	bne	8f
	ldrb	r0, [r1, #2]
	cmp	r0, #'S'
	bne	8f
	ldrb	r0, [r1, #3]
	cmp	r0, #'T'
	bne	8f
	movs	r0, #1
	bx	lr
8:	movs	r0, #0
9:	bx	lr

@ r4 = BEST_MENU: removes our line if it's live.
best_menu_remove:
	push	{lr}
	bl	menu_line_valid
	cmp	r0, #0
	beq	1f
	ldrb	r0, [r4, #M_HANDLE]
	ldr	r3, =menu_text_remove+1
	bl	best_bx_r3
1:	movs	r0, #0
	strb	r0, [r4, #M_HANDLE]
	pop	{r0}
	bx	r0
	.ltorg

@ The line for a best time (r0, frames or EMPTY_TIME) at BEST_MENU + M_TEXT:
@ BEST TIME 1'23''45 (the small font has ' but no ").
menu_line_text:
	push	{r4, r5, r6, lr}
	ldr	r5, =BEST_MENU + M_TEXT
	ldr	r1, =text_menu_best
	movs	r2, #0
1:	ldrb	r3, [r1, r2]
	strb	r3, [r5, r2]
	adds	r2, #1
	cmp	r2, #10
	blt	1b
	adds	r5, #10
	ldr	r1, =EMPTY_TIME
	cmp	r0, r1
	bne	2f
	ldr	r0, =empty_time_glyphs
	b	3f
2:	bl	time_glyphs			@ -> CUP + C_DIGITS
	ldr	r0, =CUP + C_DIGITS
3:	movs	r2, #0				@ glyphs -> characters
4:	ldrb	r3, [r0, r2]
	cmp	r3, #10
	bne	5f
	movs	r3, #39				@ '
	b	7f
5:	cmp	r3, #11
	bne	6f
	movs	r3, #39				@ '' for "
	strb	r3, [r5, #0]
	adds	r5, #1
	b	7f
6:	cmp	r3, #G_DASH
	bne	8f
	movs	r3, #'-'
	b	7f
8:	adds	r3, #'0'
7:	strb	r3, [r5, #0]
	adds	r5, #1
	adds	r2, #1
	cmp	r2, #7
	blt	4b
	movs	r3, #0
	strb	r3, [r5, #0]
	pop	{r4, r5, r6}
	pop	{r0}
	bx	r0
	.ltorg

text_menu_best:
	.ascii	"BEST TIME "
	.balign 2

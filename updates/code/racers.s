@ Updates patch: the racers (ours). Names on the character select, and the seventh racer,
@ Rusty (a rooster farmer of our own design, in the slot that was once Redneck Kong's).
@ See NOTES.md ("The farmer") and FIXES.md (`racer-names`).

	.section .fixes, "ax", %progbits
	.thumb
	.balign 2

@ ---------------------------------------------------------------- names on the select
@ In place of char_select's `bl plot_char`: the highlighted racer's name centred at the
@ bottom in the big font (plotted first, so it sits in front of the cut-outs), then the
@ cut-out as before. The slot becomes a character through the fixes build's
@ charsel_characters (asm/fixes.s); slot 6 is character 6, Rusty.
	.thumb_func
fix_charsel_text_far:
	push	{r4, lr}
	ldr	r0, =OBJ_ATTR_0			@ plain sprites, as the title text has them
	movs	r1, #0
	strh	r1, [r0, #0]
	strh	r1, [r0, #2]
	strh	r1, [r0, #4]
	ldr	r0, =CHAR_SELECTED
	ldrb	r0, [r0, #0]
	cmp	r0, #6
	bhs	1f
	ldr	r1, =charsel_characters
	ldrb	r0, [r1, r0]
1:	cmp	r0, #6
	bhi	2f
	lsls	r0, r0, #2
	ldr	r1, =racer_names
	ldr	r0, [r1, r0]
	movs	r1, #120
	movs	r2, #141
	ldr	r3, =plot_big_text+1
	bl	racers_bx_r3
2:	ldr	r3, =plot_char+1
	bl	racers_bx_r3
	@ Rusty in sepia over Candy Kong's figure, unless he is the one highlighted
	ldr	r0, =CHAR_SELECTED
	ldrb	r0, [r0, #0]
	cmp	r0, #6
	beq	3f
	ldr	r0, =rusty_sepia_plt		@ his sepia tones: OBJ colours 192-223
	ldr	r1, =0x05000380
	movs	r2, #0
4:	ldrh	r3, [r0, r2]
	strh	r3, [r1, r2]
	adds	r2, #2
	cmp	r2, #64
	blt	4b
	ldr	r0, =OBJ_ATTR_0
	movs	r1, #0
	strh	r1, [r0, #0]
	strh	r1, [r0, #2]
	strh	r1, [r0, #4]
	movs	r0, #7				@ the select's plot origin for the slots
	negs	r0, r0
	movs	r1, #1
	negs	r1, r1
	ldr	r2, =rusty_sepia_frames
	movs	r3, #0
	ldr	r4, =sprite_plot+1
	bl	racers_bx_r4
3:	pop	{r4}
	pop	{r0}
	bx	r0
racers_bx_r4:
	bx	r4
racers_bx_r3:
	bx	r3
	.ltorg

@ ---------------------------------------------------------------- the select's voices
@ sel_char_sounds (confirm) and sel_char_sounds2 (the cursor arriving), by slot, as Rare's
@ six, then Rusty's crow and cluck (updates/sound/rusty).
	.balign 4
sel_char_sounds_7:
	.word	0x3b, 0x10, 0x01, 0x16, 0x1c, 0x07, 105
sel_char_sounds2_7:
	.word	0x3c, 0x0f, 0x00, 0x15, 0x1d, 0x09, 112

@ ---------------------------------------------------------------- the course menu's picture
@ In place of menu_plane_init_plane (r0 = the character): as Rare's, with seven racers. The
@ picture's colours (144-239) to the BG palette, its tiles to 0x06008000, and its two
@ 22x16 layers of byte tile numbers (the two frames) into the screen blocks at 0x0600d800
@ and 0x0600e000, 32 bytes a row.
	.thumb_func
menu_plane_init_7:
	push	{r4, r5, r6, r7, lr}
	adds	r7, r0, #0
	cmp	r7, #6
	bls	1f
	movs	r7, #1
1:	lsls	r4, r7, #2
	ldr	r2, =0x040000d4
	ldr	r0, =plts_7
	ldr	r0, [r0, r4]
	movs	r1, #144
	lsls	r1, r1, #1
	adds	r0, r0, r1
	str	r0, [r2, #0]
	ldr	r0, =0x05000120
	str	r0, [r2, #4]
	ldr	r0, =0x80000060
	str	r0, [r2, #8]
	ldr	r0, [r2, #8]
	ldr	r0, =chars_7
	ldr	r0, [r0, r4]
	str	r0, [r2, #0]
	ldr	r0, =0x06008000
	str	r0, [r2, #4]
	ldr	r0, =num_chars_7
	ldr	r0, [r0, r4]
	ldr	r0, [r0, #0]
	lsls	r0, r0, #5
	movs	r1, #128
	lsls	r1, r1, #24
	orrs	r0, r1
	str	r0, [r2, #8]
	ldr	r0, [r2, #8]
	ldr	r5, =maps_7
	ldr	r5, [r5, r4]			@ layer A's rows
	movs	r0, #176
	lsls	r0, r0, #1
	adds	r6, r5, r0			@ layer B's (11 x 16 hwords later)
	ldr	r1, =0x0600d800
	ldr	r3, =0x0600e000
	movs	r4, #16
2:	movs	r2, #11
3:	ldrh	r0, [r5, #0]
	strh	r0, [r1, #0]
	ldrh	r0, [r6, #0]
	strh	r0, [r3, #0]
	adds	r5, #2
	adds	r6, #2
	adds	r1, #2
	adds	r3, #2
	subs	r2, #1
	bne	3b
	adds	r1, #10
	adds	r3, #10
	subs	r4, #1
	bne	2b
	ldr	r0, =current_plane
	str	r7, [r0, #0]
	ldr	r1, =B_0200de88
	movs	r0, #0
	str	r0, [r1, #0]
	pop	{r4, r5, r6, r7}
	pop	{r0}
	bx	r0
	.ltorg

	.balign 4
maps_7:
	.word	crankysmall_map, diddysmall1_map, krunchsmall_map, kroolsmall_map, dixieysmall_map
	.word	kongsmall_map, rusty_small_map
chars_7:
	.word	crankysmall_chars, diddysmall1_chars, krunchsmall_chars, kroolsmall_chars
	.word	dixieysmall_chars, kongsmall_chars, rusty_small_chars
plts_7:
	.word	crankysmall_plt, diddysmall1_plt, krunchsmall_plt, kroolsmall_plt, dixieysmall_plt
	.word	kongsmall_plt, rusty_small_plt
num_chars_7:
	.word	crankysmall_num_chars, diddysmall1_num_chars, krunchsmall_num_chars, kroolsmall_num_chars
	.word	dixieysmall_num_chars, kongsmall_num_chars, rusty_small_num_chars

@ ---------------------------------------------------------------- Rusty in the race
@ In place of setup_player_data's character loop (r1 = character, r5 = the plane): the
@ character wrapped to 0-6, stored at o+130, and r1 = its sprite (Rare's switch, plus
@ Rusty's plane, sprite 126).
	.thumb_func
fix_racer_sprite_far:
1:	cmp	r1, #6
	ble	2f
	subs	r1, #7
	b	1b
2:	adds	r0, r5, #0
	adds	r0, #130
	strh	r1, [r0, #0]
	ldr	r0, =racer_sprites
	ldrb	r1, [r0, r1]
	bx	lr
	.ltorg
@ In place of get_player_head (r0 = a plane -> r0 = its racer's head sprite), from the farm
@ eggs' and haunted souls' HUDs: Rare's heads, then Rusty's (sprite 127). (A leaf: lr is
@ the caller's.)
	.thumb_func
get_player_head_7:
	adds	r0, #130
	ldrh	r0, [r0, #0]
	cmp	r0, #6
	bls	1f
	movs	r0, #3				@ (Rare's default: K. Rool's head)
1:	ldr	r1, =racer_heads
	ldrb	r0, [r1, r0]
	bx	lr
	.ltorg
racer_heads:					@ by character, as get_player_head's switch, then Rusty
	.byte	46, 47, 52, 51, 48, 49, 127
	.balign 2

racer_sprites:					@ by character, as setup_player_data's switch
	.byte	5, 1, 4, 6, 2, 3, 126		@ Cranky, Diddy, Krunch, K. Rool, Dixie, DK, Rusty
	.balign 2

	.equ	R_SP, 254			@ big font: space
	.equ	R_DOT, 39			@ .
	.equ	R_END, 255
	.balign 4
racer_names:					@ by character: 0 Cranky .. 5 DK, 6 Rusty (ours)
	.word	name_cranky, name_diddy, name_krunch, name_krool, name_dixie, name_dk, name_rusty
name_cranky:	.byte	2, 17, 0, 13, 10, 24, R_END			@ CRANKY
name_diddy:	.byte	3, 8, 3, 3, 24, R_END				@ DIDDY
name_krunch:	.byte	10, 17, 20, 13, 2, 7, R_END			@ KRUNCH
name_krool:	.byte	10, R_DOT, R_SP, 17, 14, 14, 11, R_END		@ K. ROOL
name_dixie:	.byte	3, 8, 23, 8, 4, R_END				@ DIXIE
name_dk:	.byte	3, 10, R_END					@ DK
name_rusty:	.byte	17, 20, 18, 19, 24, R_END			@ RUSTY
	.balign 2

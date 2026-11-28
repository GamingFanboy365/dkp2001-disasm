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
	pop	{r4}
	pop	{r0}
	bx	r0
racers_bx_r3:
	bx	r3
	.ltorg

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

@ Updates patch: new names for courses we finish (our own, not Rare's).
@ Written for this project. Rare's name strings stay in the ROM untouched;
@ select_strings (data/data.s) points at these instead, under UPDATES.
@ The menu font is capitals, digits and a little punctuation.

	.section .fixes, "ax", %progbits

@ Level 37, Kongo Kingdom's second course (its ground is stamped as no
@ placeholder: Rare drew a temple courtyard with a maze worn into its paving,
@ but placed no race on it; the build named it "JUNGLE RACE 2").
course_name_37:
	.asciz	"TEMPLE TANGLE"
	.balign	4

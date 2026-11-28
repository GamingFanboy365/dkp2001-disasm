@ Updates patch: Rusty's voice (ours; updates/sound/rusty/voice.py), as sound effects
@ 105-112 at the end of the effects list (vgroup127_samplist). Each record copies the
@ layout of Rare's effect records: {0x20, 3, 8000 Hz, root key 60, the sample, its length
@ - 1, its end, 0, 0, 0x63 x4, 0 x4}; samples are signed 8-bit.

	.section .fixes, "ax", %progbits
	.macro	rusty_sfx name
	.balign	4
rusty_\name\()_inf:
	.word	0x20, 3, 8000, 60, rusty_\name\()_smp, rusty_\name\()_end - rusty_\name\()_smp - 1
	.word	rusty_\name\()_end - 1, 0, 0, 0x63, 0x63, 0x63, 0x63, 0, 0, 0, 0
rusty_\name\()_smp:
	.incbin	"updates/sound/rusty/\name\().bin"
rusty_\name\()_end:
	.endm

	rusty_sfx crow			@ 105
	rusty_sfx cheer			@ 106
	rusty_sfx whoop			@ 107
	rusty_sfx yeehaw		@ 108
	rusty_sfx brawk			@ 109
	rusty_sfx squawk1		@ 110
	rusty_sfx squawk2		@ 111
	rusty_sfx cluck			@ 112
	.balign	4

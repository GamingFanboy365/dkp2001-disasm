@ Updates patch: the song list with our tunes added (ours).
@ The sound driver keeps a pointer to the list in RAM (audio_tune_list_ref), set at
@ start-up; in the updates build it points here instead of at Rare's tune_list, which
@ stays in the ROM unchanged. Rare's seven tunes keep their numbers (0-6).

	.section .fixes, "ax", %progbits
	.balign 4
tune_list_updates:
	.word	three_beach_tune_001		@ 0 beach
	.word	three_snow_tune_002		@ 1 snow
	.word	three_lava_tune_003		@ 2 lava
	.word	three_menu_tune_004		@ 3 menu
	.word	three_bayou_tune_005		@ 4 bayou
	.word	three_haunted_tune_006		@ 5 haunted
	.word	three_castle_tune_008		@ 6 castle
	.word	jungle_tune			@ 7 jungle (updates/music/jungle.py)

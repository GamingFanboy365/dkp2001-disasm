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
	.word	results_tune			@ 8 RESULTS (updates/music/results.py)
	.word	final_results_tune		@ 9 FINAL RESULTS, cup won (final_results.py)
	.word	final_runner_up_tune		@ 10 FINAL RESULTS, not won (final_results_runner_up.py)
	.word	fanfare_1st_tune		@ 11 finish, 1st (fanfare_1st.py; played once)
	.word	fanfare_2nd_tune		@ 12 finish, 2nd (fanfare_2nd.py)
	.word	fanfare_3rd_tune		@ 13 finish, 3rd (fanfare_3rd.py)
	.word	fanfare_4th_tune		@ 14 finish, 4th or retired (fanfare_4th.py)
	.word	best_times_tune			@ 15 BEST TIMES, Clock Race (best_times.py)

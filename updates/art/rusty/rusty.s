@ Updates patch: Rusty's graphics (ours; updates/art/rusty/model.py, build_sprite.py).

	.section .fixes, "ax", %progbits
	.balign	16
__spr_rusty:					@ tab_sprites 126: his plane, 3 levels x 65 frames
	.incbin	"updates/art/rusty/plane.bin"
	.balign	4
__pal_rusty:					@ tab_palettes 92
	.incbin	"updates/art/rusty/plane_pal.bin"
	.balign	16
__spr_rusty_head:				@ tab_sprites 127: his racer icon (build_head.py)
	.incbin	"updates/art/rusty/head.bin"
	.balign	4
__pal_rusty_head:				@ tab_palettes 93
	.incbin	"updates/art/rusty/head_pal.bin"
	.balign	4

@ The character select (build_cutout.py): his colour cut-out (slot 6, highlighted) and the
@ same figure in the backdrop's sepia, drawn over Candy Kong's figure otherwise. Frames as
@ the select's clr_*_frames: {1 frame, 1, 0, 0}, then {tiles, tile bytes / 4, pieces,
@ piece list, 0}.
	.balign	4
rusty_cut_frames:
	.byte	1, 1, 0, 0
	.word	rusty_cut_char
	.hword	(rusty_cut_char_end - rusty_cut_char) / 4, (rusty_cut_info_end - rusty_cut_info) / 12
	.word	rusty_cut_info, 0
rusty_sepia_frames:
	.byte	1, 1, 0, 0
	.word	rusty_sepia_char
	.hword	(rusty_sepia_char_end - rusty_sepia_char) / 4, (rusty_cut_info_end - rusty_cut_info) / 12
	.word	rusty_cut_info, 0
rusty_cut_info:
	.incbin	"updates/art/rusty/cutout_info.bin"
rusty_cut_info_end:
	.balign	4
rusty_cut_char:
	.incbin	"updates/art/rusty/cutout.bin"
rusty_cut_char_end:
	.balign	4
rusty_sepia_char:
	.incbin	"updates/art/rusty/sepia.bin"
rusty_sepia_char_end:
	.balign	4
rusty_cut_plt:					@ 192 colours, as set_spr_pal loads them
	.incbin	"updates/art/rusty/cutout_pal.bin"
	.balign	4
rusty_sepia_plt:				@ OBJ colours 192-223
	.incbin	"updates/art/rusty/sepia_pal.bin"
	.balign	4

@ The course menu's picture (build_small.py): him head-on in his plane, two frames.
rusty_small_map:
	.incbin	"updates/art/rusty/small_map.bin"
	.balign	4
rusty_small_chars:
	.incbin	"updates/art/rusty/small_chars.bin"
rusty_small_chars_end:
	.balign	4
rusty_small_num_chars:
	.word	(rusty_small_chars_end - rusty_small_chars) / 64
rusty_small_plt:
	.incbin	"updates/art/rusty/small_plt.bin"
	.balign	4

@ Updates patch: original course pictures (ours; see each folder's paint.py).
@ menu_image_set_image copies 176 colours (index 0 transparent, 1-175 the
@ picture) to OBJ palette 0 and 9216 bytes of 8bpp tiles to OBJ VRAM.

	.section .fixes, "ax", %progbits
	.balign	4
temple_tangle_palette:
	.incbin	"updates/art/temple_tangle/palette.bin"
	.balign	4
temple_tangle_tiles:
	.incbin	"updates/art/temple_tangle/tiles.bin"
	.balign	4

@ The cup's FINAL RESULTS background (updates/art/cup_results/paint.py): 8bpp tiles,
@ a 32x32 screen map and 255 colours, for background 0 (updates/code/cup.s).
	.balign	4
cup_bg_tiles:
	.incbin	"updates/art/cup_results/tiles.bin"
cup_bg_tiles_end:
	.balign	4
cup_bg_map:
	.incbin	"updates/art/cup_results/map.bin"
	.balign	4
cup_bg_palette:
	.incbin	"updates/art/cup_results/palette.bin"
	.balign	4

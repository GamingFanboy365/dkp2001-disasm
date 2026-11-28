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

@ The cup's results backgrounds (updates/art/cup_results/paint.py): 8bpp tiles, a 32x32
@ screen map and 255 colours each, for background 0 (updates/code/cup.s). race/ is
@ shown after each race (RESULTS), final/ after the cup (FINAL RESULTS).
	.balign	4
cup_race_tiles:
	.incbin	"updates/art/cup_results/race/tiles.bin"
cup_race_tiles_end:
	.balign	4
cup_race_map:
	.incbin	"updates/art/cup_results/race/map.bin"
	.balign	4
cup_race_palette:
	.incbin	"updates/art/cup_results/race/palette.bin"
	.balign	4
cup_final_tiles:
	.incbin	"updates/art/cup_results/final/tiles.bin"
cup_final_tiles_end:
	.balign	4
cup_final_map:
	.incbin	"updates/art/cup_results/final/map.bin"
	.balign	4
cup_final_palette:
	.incbin	"updates/art/cup_results/final/palette.bin"
	.balign	4

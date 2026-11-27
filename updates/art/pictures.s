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

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

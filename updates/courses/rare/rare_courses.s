@ Updates patch: Rare's finished races without pylons (ours: the transformation only).
@ tools/course_convert.py makes these files in the build folder from your ROM's
@ extracted assets (assets/objects, assets/ai_networks) and updates/courses/rare/*.py:
@ each course's object list with its pylons replaced by hidden checkpoints, and the
@ wall grid for its track. Nothing of Rare's is in this repository.

	.section .fixes, "ax", %progbits
	.balign 4
obj_beach_01_walled:
	.incbin "updates/beach_01_obj.bin"
	.balign 4
walls_beach_01:
	.incbin "updates/beach_01_walls.bin"
	.balign 4
obj_beach_00_walled:
	.incbin "updates/beach_00_obj.bin"
	.balign 4
walls_beach_00:
	.incbin "updates/beach_00_walls.bin"
	.balign 4
obj_lava_00_walled:
	.incbin "updates/lava_00_obj.bin"
	.balign 4
walls_lava_00:
	.incbin "updates/lava_00_walls.bin"
	.balign 4
obj_snow_00_walled:
	.incbin "updates/snow_00_obj.bin"
	.balign 4
walls_snow_00:
	.incbin "updates/snow_00_walls.bin"
	.balign 4
obj_farm_00_walled:
	.incbin "updates/farm_00_obj.bin"
	.balign 4
walls_farm_00:
	.incbin "updates/farm_00_walls.bin"
	.balign 4
obj_haunted_00_walled:
	.incbin "updates/haunted_00_obj.bin"
	.balign 4
walls_haunted_00:
	.incbin "updates/haunted_00_walls.bin"
	.balign 4

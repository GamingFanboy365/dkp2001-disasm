@ Top-level build file: every module in ROM order.
@ Assemble with --defsym SHIFT_CODE=n / SHIFT_DATA=n to move code / data (relocation test).
	.syntax unified
	.global _start


	.section .boot, "ax", %progbits
	.balign 4
	.include "asm/src/crt0.s"

	.section .text32, "awx", %progbits
	.balign 4
	.include "asm/src/sys_irq.s"
	.include "asm/src/sys_tilt.s"
	.include "asm/src/sprite_ram.c.s"
	.include "asm/src/background_ram.c.s"
	.include "asm/src/object_ram.c.s"
	.include "asm/src/dkp_math.s"

	.section .text, "ax", %progbits
	.balign 4
	.ifdef SHIFT_CODE
	.space SHIFT_CODE
	.endif
	.include "asm/src/os_math.s"
	.include "asm/src/tab_trig.s"
	.include "asm/src/title/fe_title.s"
	.include "asm/src/title/title_charsel.s"
	.include "asm/src/title/title_story.s"
	.include "asm/src/title/title_dogfight.s"
	.include "asm/src/title/title_levsel.s"
	.include "asm/src/title/title_control.s"
	.include "asm/src/title/bgutil.s"
	.include "asm/src/title/bigfont.s"
	.include "asm/src/title/smallfont.s"
	.include "asm/src/title/text.s"
	.include "asm/src/title/fe_sprite.s"
	.include "asm/src/main.c.s"
	.include "asm/src/game.c.s"
	.include "asm/src/title_logo.c.s"
	.include "asm/src/random.c.s"
	.include "asm/src/background.c.s"
	.include "asm/src/object.c.s"
	.include "asm/src/menu.c.s"
	.include "asm/src/particle.c.s"
	.include "asm/src/sprite.c.s"
	.include "asm/src/animation.c.s"
	.include "asm/src/act_player.c.s"
	.include "asm/src/act_comp_player.c.s"
	.include "asm/src/act_camera.c.s"
	.include "asm/src/act_null.c.s"
	.include "asm/src/act_static.c.s"
	.include "asm/src/act_hud.c.s"
	.include "asm/src/act_keep.c.s"
	.include "asm/src/act_farm.c.s"
	.include "asm/src/act_haunted.c.s"
	.include "asm/src/act_bounce_bomb.c.s"
	.include "asm/src/camera_pan.c.s"
	.include "asm/src/act_beacon.c.s"
	.include "asm/src/act_powerup.c.s"
	.include "asm/src/act_starthoop.c.s"
	.include "asm/src/act_startpos.c.s"
	.include "asm/src/act_beachhut.c.s"
	.include "asm/src/act_bonusitem.c.s"
	.include "asm/src/act_banana.c.s"
	.include "asm/src/act_pylon.c.s"
	.include "asm/src/act_race_monitor.c.s"
	.include "asm/src/act_tideanim.c.s"
	.include "asm/src/plane.c.s"
	.include "asm/src/act_groundboost.c.s"
	.include "asm/src/act_fader.c.s"
	.include "asm/src/act_directional_arrow.c.s"
	.include "asm/src/act_boost.c.s"
	.include "asm/src/act_pause.c.s"
	.include "asm/src/act_beach.c.s"
	.include "asm/src/act_weapon.c.s"
	.include "asm/src/act_swamp.c.s"
	.include "asm/src/act_jungle.c.s"
	.include "asm/src/title/multi.c.s"
	.include "asm/src/audio/c_inc.c.s"
	.include "asm/src/menu/menu_main.c.s"
	.include "asm/src/menu/menu_text.c.s"
	.include "asm/src/menu/menu_anim.c.s"
	.include "asm/src/menu/menu_oam.c.s"
	.include "asm/src/menu/menu_plane.c.s"
	.include "asm/src/menu/menu_image.c.s"
	.include "asm/src/menu/menu_background.c.s"
	.include "asm/src/menu/menu_border.c.s"
	.include "asm/src/menu/menu_coin.c.s"
	.include "asm/src/menu/menu_mode.c.s"
	.include "asm/src/menu/menu_spline.c.s"
	.include "asm/src/state/state_main.c.s"
	.include "asm/src/state/state_level.c.s"
	.include "asm/src/state/state_slot.c.s"
	.include "asm/src/state/state_game.c.s"
	.include "asm/src/audio/code/audio.S"
	.include "data/text_sprites.s"
	.include "asm/lib/agbprint.c.s"
	.include "asm/lib/newlib/libc/string/memcpy.c.s"
	.include "asm/lib/newlib/libc/string/memset.c.s"
	.include "asm/lib/newlib/libc/stdio/vsprintf.c.s"
	.include "asm/lib/newlib/libc/stdio/vfprintf.c.s"
	.include "asm/lib/newlib/libc/stdio/wsetup.c.s"
	.include "asm/lib/newlib/libc/stdlib/dtoa.c.s"
	.include "asm/lib/newlib/libc/stdio/fflush.c.s"
	.include "asm/lib/newlib/libc/stdio/findfp.c.s"
	.include "asm/lib/newlib/libc/stdlib/mallocr.c.s"
	.include "asm/lib/newlib/libc/stdio/fvwrite.c.s"
	.include "asm/lib/newlib/libc/stdio/fwalk.c.s"
	.include "asm/lib/newlib/libc/locale/locale.c.s"
	.include "asm/lib/newlib/libc/stdio/makebuf.c.s"
	.include "asm/lib/newlib/libc/stdlib/mallocr.2.c.s"
	.include "asm/lib/newlib/libc/stdlib/mbtowc_r.c.s"
	.include "asm/lib/newlib/libc/string/memchr.c.s"
	.include "asm/lib/newlib/libc/string/memmove.c.s"
	.include "asm/lib/newlib/libc/stdlib/mlock.c.s"
	.include "asm/lib/newlib/libc/stdlib/mprec.c.s"
	.include "asm/lib/newlib/libm/math/s_isinf.c.s"
	.include "asm/lib/newlib/libm/math/s_isnan.c.s"
	.include "asm/lib/newlib/libc/reent/sbrkr.c.s"
	.include "asm/lib/newlib/libc/stdio/stdio.c.s"
	.include "asm/lib/newlib/libc/string/strcmp.c.s"
	.include "asm/lib/newlib/libc/string/strlen.c.s"
	.include "asm/lib/newlib/libc/sys/arm/syscalls.c.s"
	.include "asm/lib/newlib/libc/reent/writer.c.s"
	.include "asm/lib/newlib/libc/stdlib/mallocr.3.c.s"
	.include "asm/lib/newlib/libc/reent/closer.c.s"
	.include "asm/lib/newlib/libc/errno/errno.c.s"
	.include "asm/lib/newlib/libc/reent/fstatr.c.s"
	.include "asm/lib/newlib/libc/sys/arm/libcfunc.c.s"
	.include "asm/lib/newlib/libc/reent/lseekr.c.s"
	.include "asm/lib/newlib/libc/reent/readr.c.s"
	.include "asm/lib/gcc/libgcc1.S"
	.include "asm/lib/gcc/libgcc2.c.s"
	.include "asm/lib/gcc/dp-bit.c.s"
	.include "asm/lib/gcc/fp-bit.c.s"
	.include "asm/lib/gcc/libgcc2.2.c.s"
	.include "asm/lib/gcc/libgcc2.3.c.s"
	.ifdef SHIFT_DATA
	.space SHIFT_DATA
	.endif

	.section .rodata, "a", %progbits
	.balign 4
	.include "data/rodata.s"

	.section .data, "aw", %progbits
	.balign 4
	.include "data/data.s"

	.include "data/bss.s"

	.ifdef FIXES
	.include "asm/fixes.s"
	.endif
	.ifdef UPDATES
	.include "updates/code/dogfight.s"	@ our own additions (see updates/README.md)
	.include "updates/code/walls.s"	@ invisible walls round a course
	.include "updates/code/cup.s"	@ cups and the Clock Race return
	.include "updates/code/best.s"	@ Clock Race best times (saved)
	.include "updates/text/course_names.s"	@ new course names
	.include "updates/art/pictures.s"	@ new course pictures
	.include "updates/courses/temple_tangle.s"	@ generated from temple_tangle.py
	.include "updates/courses/temple_tangle_ground.s"	@ its ground (course_build.py --ground)
	.include "updates/music/tune_list.s"	@ the song list with our tunes
	.include "updates/music/jungle.s"	@ generated from jungle.py
	.include "updates/music/results.s"
	.include "updates/music/final_results.s"
	.include "updates/music/final_results_runner_up.s"
	.include "updates/music/fanfare_1st.s"	@ the finish fanfares (played once)
	.include "updates/music/fanfare_2nd.s"
	.include "updates/music/fanfare_3rd.s"
	.include "updates/music/fanfare_4th.s"
	.include "updates/courses/rare/rare_courses.s"	@ Rare's races without pylons (made at build time)
	.endif

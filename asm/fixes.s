@ New code and data for the bug-fix build (assembled only with FIXES).
@ It goes in its own section after all the game's data, at the end of the ROM,
@ so adding it moves nothing else and the IPS patch stays small. The ROM end is
@ out of BL range from most code, so callers reach it through small trampolines
@ placed in the dead space of failed-assert blocks (see FIXES.md).

	.section .fixes, "ax", %progbits
	.thumb
	.balign 4

@ FIX "race-music": the races are silent. game_init() stopped the menu music
@ and never started anything, although the ROM has six course themes
@ (tune_list) and act_hud.c already speeds the music up on the final lap.
@ Called in place of game_init's audio_halt_tune(): starts the course's
@ theme from race_tunes, or stops the music if the course has none.
fix_race_music_far:
	ldr	r0, 1f
	ldr	r0, [r0, #0]			@ game_level
	cmp	r0, #RACE_TUNES_COUNT
	bhs	2f
	ldr	r1, 3f
	ldrb	r0, [r1, r0]			@ race_tunes[game_level]
	cmp	r0, #NO_TUNE
	beq	2f
	ldr	r1, 4f
	bx	r1				@ audio_start_tune(tune), returns to game_init
2:	ldr	r1, 5f
	bx	r1				@ audio_halt_tune()
	.balign 4
1:	.word	game_level
3:	.word	race_tunes
4:	.word	audio_start_tune+1
5:	.word	audio_halt_tune+1

@ tune_list order: 0 beach, 1 snow, 2 lava, 3 menu, 4 bayou, 5 haunted, 6 castle
	.equ	BEACH, 0
	.equ	SNOW, 1
	.equ	LAVA, 2
	.equ	MENU, 3
	.equ	BAYOU, 4
	.equ	HAUNTED, 5
	.equ	CASTLE, 6
	.equ	NO_TUNE, 0xff

@ One entry per game_level (tab_levels index). Worlds without a theme of their
@ own borrow the closest one; edit freely.
race_tunes:
	.byte	NO_TUNE					@  0 (unused)
	.byte	BEACH, BEACH, BEACH, BEACH		@  1- 4 beach_00-03
	.byte	LAVA, LAVA, LAVA			@  5- 7 lava_00-02
	.byte	SNOW, SNOW, SNOW, SNOW			@  8-11 snow_00-03
	.byte	CASTLE, CASTLE, CASTLE, CASTLE		@ 12-15 keep_00-03 (K. Rool's keep)
	.byte	BEACH, BEACH, BEACH, BEACH		@ 16-19 lake_00-03 (no theme: water, like beach)
	.byte	BAYOU, BAYOU, BAYOU, BAYOU, BAYOU, BAYOU	@ 20-25 farm_00-05 (no theme: country, like bayou)
	.byte	BAYOU, BAYOU, BAYOU, BAYOU		@ 26-29 swamp_00-03 (bayou = swamp)
	.byte	HAUNTED, HAUNTED, HAUNTED, HAUNTED	@ 30-33 haunted_00-03
	.byte	BAYOU, BAYOU, BAYOU, BAYOU		@ 34-37 jungle_00-03 (no theme: jungle swamp, like bayou)
	.byte	LAVA, LAVA, LAVA, LAVA			@ 38-41 desert_00-03 (no theme: hot, like lava)
	.equ	RACE_TUNES_COUNT, . - race_tunes
	.balign 4

@ FIX "dogfight-opponents": Dog Fights starts an ordinary race on an arena
@ course, and nothing outside the menu knows the mode was chosen. The three
@ computer planes had no start positions on most arenas (they sat at 0,0,0)
@ and then flew the course's stub route along the ground, far from the
@ player, so the player never met them. In a dogfight (see df_mode):
@   - they start ahead of the player, spread out at its height and facing it;
@   - they hunt the player instead of flying the route, and everyone gets
@     weapons now and then, since the arenas have no powerups.
@ FIX "dogfight-scoring": and the fight has rules and an ending. Every plane
@ has three lives, kept in the race monitor's pylon-strike bytes, so the
@ player's are shown by the race's own strike counter. A hit (player_tumble)
@ costs a life. A computer plane with none left tumbles and then vanishes;
@ downing all three ends the fight as a won race does (FINISH). Losing the
@ player's last life ends it as a failed race does (RETIRE). Laps and pylon
@ strikes don't count in a dogfight.
@ This is new design: the build has no dogfight game code to restore.

	.equ	MODE_STORIES, 1
	.equ	MODE_DOGFIGHT, 2
	.equ	KROOLS_GOLD_LEVEL, 6		@ Stories > K. Rool's Gold: Lava 01, a dogfight course
	.equ	OBJ_COMP_PLAYER, 2		@ object type, o+2
	.equ	DF_FAR_SHIFT, 9216		@ aim vectors longer than 96 units are scaled down
	.equ	DF_LIVES, 3			@ = monitor+84, the strikes the counter shows
	.equ	DF_FALL_FRAMES, 60		@ a downed plane vanishes after its tumble
	.equ	MON_STATE, 80			@ race monitor fields
	.equ	MON_RACING, 3
	.equ	MON_FINISHED, 4
	.equ	MON_HITS, 94			@ + player number: pylon strikes, here hits taken
	.equ	MON_SHOW_COUNTER, 131
	.equ	MON_PLACE, 136			@ the player's place, shown by the HUD
	.equ	MON_END_TIMER, 140

@ r0 = 1 in a dogfight, else 0: Dog Fights, or the K. Rool's Gold story.
@ Uses r0 and r1 only.
	.thumb_func
df_mode:
	ldr	r1, =virtual_mode
	ldr	r1, [r1, #0]
	cmp	r1, #MODE_DOGFIGHT
	beq	1f
	cmp	r1, #MODE_STORIES
	bne	2f
	ldr	r1, =game_level
	ldr	r1, [r1, #0]
	cmp	r1, #KROOLS_GOLD_LEVEL
	bne	2f
1:	movs	r0, #1
	bx	lr
2:	movs	r0, #0
	bx	lr
	.ltorg

df_bx_r3:
	bx	r3
df_bx_r4:
	bx	r4

@ Called from ai_steer (act_comp_player.c:242) with r5 = the computer
@ player and r7/sl/r6 = its x/y/z offset to the route target (8.8 fixed).
@ Returns r0 = players and r1 = 3, which the caller expects; r2-r4 are free.
@ In a dogfight:
@   - a downed plane counts down its fall, then is taken out of drawing and
@     collisions, and does nothing more;
@   - arms the computer player (and, on player 1's turn, the human) now and
@     then: whoever has no weapon gets a random one (types 1-8, the ones
@     ai_think knows how to use), on average every couple of seconds;
@   - sets its race progress just behind the human's (or just ahead, when
@     the human is behind it), so ai_think picks the human as the target for
@     its forward (or rear) weapons, and its speed stays put;
@   - aims it at the human's plane, or for players 2 and 3 at where the
@     human will be 24 or 48 frames on, so they try to cut across its nose.
	.thumb_func
fix_dogfight_steer_far:
	push	{r4, lr}
	bl	df_mode
	cmp	r0, #0
	beq	df_steer_out
	ldr	r0, =players
	ldr	r1, [r0, #0]			@ players[0], the human
	cmp	r1, r5
	beq	df_steer_out
	ldr	r4, =monitor
	ldr	r4, [r4, #0]
	ldr	r2, [r5, #84]			@ player number (1-3)
	adds	r4, r4, r2
	adds	r4, #MON_HITS			@ r4 = its hits taken
	ldrb	r0, [r4, #0]
	cmp	r0, #DF_LIVES
	blo	df_steer_alive
	beq	df_steer_out			@ gone
	subs	r0, #1				@ falling
	strb	r0, [r4, #0]
	cmp	r0, #DF_LIVES
	bne	df_steer_out
	adds	r0, r5, #0			@ fall over: vanish
	ldr	r3, =obj_remove_draw+1
	bl	df_bx_r3
	adds	r0, r5, #0
	ldr	r3, =obj_remove_hit+1
	bl	df_bx_r3
	b	df_steer_out
df_steer_alive:
	ldr	r0, =players
	ldr	r1, [r0, #0]
	ldr	r2, [r0, #4]
	cmp	r2, r5				@ on player 1's turn, arm the human too
	bne	1f
	adds	r0, r1, #0
	bl	df_arm
1:	adds	r0, r5, #0
	bl	df_arm
	ldr	r1, =players
	ldr	r1, [r1, #0]			@ r1 = human
	ldr	r0, [r5, #84]			@ player number (1-3)
	adr	r2, df_lead
	ldrb	r0, [r2, r0]			@ r0 = frames of lead
	ldr	r2, [r1, #44]			@ offset to the aim point, whole units:
	muls	r2, r0				@ human position + velocity * lead - own position
	ldr	r3, [r1, #32]
	adds	r2, r2, r3
	ldr	r3, [r5, #32]
	subs	r2, r2, r3
	asrs	r2, r2, #8
	ldr	r3, [r1, #48]
	muls	r3, r0
	ldr	r4, [r1, #36]
	adds	r3, r3, r4
	ldr	r4, [r5, #36]
	subs	r3, r3, r4
	asrs	r3, r3, #8
	ldr	r4, [r1, #52]
	muls	r4, r0
	ldr	r0, [r1, #40]
	adds	r4, r4, r0
	ldr	r0, [r5, #40]
	subs	r4, r4, r0
	asrs	r4, r4, #8
	ldr	r0, [r5, #44]			@ is the aim point in front (velocity . offset > 0)?
	muls	r0, r2
	ldr	r7, [r5, #52]
	muls	r7, r4
	adds	r0, r0, r7
	movs	r7, #164			@ race progress = human's -256 (in front) or +256
	ldr	r1, [r1, r7]
	subs	r1, #128
	subs	r1, #128
	cmp	r0, #0
	bgt	1f
	adds	r1, #255
	adds	r1, #255
	adds	r1, #2
1:	str	r1, [r5, r7]
	adds	r0, r2, #0			@ r0 = squared length
	muls	r0, r2
	adds	r1, r3, #0
	muls	r1, r3
	adds	r0, r0, r1
	adds	r1, r4, #0
	muls	r1, r4
	adds	r0, r0, r1
	movs	r1, #0				@ r1 = shift that keeps the 8.8 vector short
	ldr	r7, =DF_FAR_SHIFT		@ (ai_steer squares it in 32 bits)
1:	cmp	r0, r7
	ble	2f
	lsrs	r0, r0, #2
	adds	r1, #1
	b	1b
2:	lsls	r2, r2, #8
	asrs	r2, r1
	lsls	r3, r3, #8
	asrs	r3, r1
	lsls	r4, r4, #8
	asrs	r4, r1
	adds	r7, r2, #0			@ new target offset
	mov	sl, r3
	adds	r6, r4, #0
df_steer_out:
	ldr	r0, =players
	movs	r1, #3
	pop	{r4}
	pop	{r2}
	bx	r2
	.ltorg
df_lead:					@ frames of lead, by player number
	.byte	0, 0, 24, 48
	.balign 4

@ r0 = a player: if it has no weapon, 1 in 128 calls gives it a random
@ weapon (1-8), pushed on its weapon stack as react_powerup does.
@ Keeps r4-r7.
	.thumb_func
df_arm:
	push	{r4, lr}
	adds	r4, r0, #0
	adds	r4, #134			@ r4 = weapon stack: +0 +2 +4 slots, +6 count
	ldrh	r0, [r4, #6]
	cmp	r0, #0
	bne	1f
	ldr	r3, =rnd_rand+1
	bl	df_bx_r3
	lsrs	r1, r0, #16
	lsls	r1, r1, #25			@ low 7 bits of the high half
	bne	1f
	lsrs	r0, r0, #29			@ top 3 bits: weapon 1-8
	adds	r0, #1
	ldrh	r1, [r4, #2]
	strh	r1, [r4, #4]
	ldrh	r1, [r4, #0]
	strh	r1, [r4, #2]
	strh	r0, [r4, #0]
	ldrh	r0, [r4, #6]
	adds	r0, #1
	strh	r0, [r4, #6]
	subs	r4, #134
	ldr	r0, [r4, #80]			@ armed flag, as react_powerup sets it
	movs	r1, #8
	orrs	r0, r1
	str	r0, [r4, #80]
1:	pop	{r4}
	pop	{r0}
	bx	r0
	.ltorg

@ In place of player_tumble(r0 = the plane hit), from the weapons and
@ plane.c. In a dogfight, while the fight is on, the hit costs a life:
@ the human's strike counter slides in (with the pylon-miss sound) and its
@ last life fails the race; a computer plane with no lives left falls
@ (see fix_dogfight_steer_far) and drops its weapons (when all three are
@ gone, fix_df_positions_far ends the race won). Then tumbles the plane as
@ before.
	.thumb_func
fix_df_hit_far:
	push	{r0, r4, r5, r6, r7, lr}
	bl	df_mode
	cmp	r0, #0
	beq	df_hit_out
	ldr	r4, =monitor
	ldr	r4, [r4, #0]
	ldr	r0, [r4, #MON_STATE]
	cmp	r0, #MON_RACING
	bne	df_hit_out
	ldr	r5, [sp, #0]			@ the plane hit
	ldr	r6, [r5, #84]			@ player number
	cmp	r6, #3
	bhi	df_hit_out
	adds	r7, r4, r6
	adds	r7, #MON_HITS
	ldrb	r0, [r7, #0]
	cmp	r0, #DF_LIVES
	bhs	df_hit_out			@ already down
	adds	r0, #1
	cmp	r6, #0
	bne	df_hit_cpu
	strb	r0, [r7, #0]			@ the human loses a life
	adds	r1, r4, #0
	adds	r1, #MON_SHOW_COUNTER
	movs	r2, #90
	strb	r2, [r1, #0]
	cmp	r0, #DF_LIVES
	blo	1f
	ldr	r3, =race_fail_player+1		@ none left: RETIRE
	bl	df_bx_r3
	b	df_hit_out
1:	movs	r0, #55				@ the pylon-miss sound
	movs	r1, #80
	movs	r2, #128
	lsls	r2, r2, #9
	movs	r3, #20
	ldr	r4, =audio_new_fx_with_dur+1
	bl	df_bx_r4
	b	df_hit_out
df_hit_cpu:
	cmp	r0, #DF_LIVES
	blo	df_hit_store
	movs	r0, #DF_LIVES + DF_FALL_FRAMES	@ down: falls, then vanishes
	strb	r0, [r7, #0]
	movs	r0, #0				@ drops its weapons
	adds	r1, r5, #0
	adds	r1, #140
	strh	r0, [r1, #0]
	b	df_hit_out
df_hit_store:
	strb	r0, [r7, #0]
df_hit_out:
	pop	{r0, r4, r5, r6, r7}
	pop	{r3}
	mov	lr, r3
	ldr	r3, =player_tumble+1
	bx	r3				@ player_tumble(plane), returns to the caller
	.ltorg

@ r4 = the race monitor: end the fight won, as race_complete_lap ends a
@ race the player has finished (FINISH banner, the computer flies the
@ player's plane, then the end-of-race menu).
	.thumb_func
df_win:
	push	{lr}
	movs	r0, #1				@ 1st: no opponents left
	adds	r1, r4, #0
	adds	r1, #MON_PLACE
	strb	r0, [r1, #0]
	movs	r0, #MON_FINISHED
	str	r0, [r4, #MON_STATE]
	ldr	r2, =op_mask
	ldr	r0, [r2, #0]
	movs	r1, #0x80
	bics	r0, r1
	str	r0, [r2, #0]
	ldr	r2, =sys_flags
	ldr	r0, [r2, #0]
	movs	r1, #0x20
	orrs	r0, r1
	movs	r1, #0x84
	bics	r0, r1
	str	r0, [r2, #0]
	movs	r0, #192			@ 384 frames to the end-of-race menu
	lsls	r0, r0, #1
	adds	r1, r4, #0
	adds	r1, #MON_END_TIMER
	str	r0, [r1, #0]
	ldr	r0, =players
	ldr	r0, [r0, #0]
	ldr	r3, =convert_to_comp_player+1
	bl	df_bx_r3
	pop	{r0}
	bx	r0
	.ltorg

@ In place of calculate_race_positions(r0 = the race monitor) from
@ act_race_monitor: in a dogfight, while the fight is on, the place the HUD
@ shows is 1 + the computer planes still flying (4th down to 1st), since
@ race positions mean nothing there; once the last downed plane has
@ finished falling, the fight is won.
	.thumb_func
fix_df_positions_far:
	push	{r4, r5, r6, lr}
	adds	r4, r0, #0
	ldr	r3, =calculate_race_positions+1
	bl	df_bx_r3
	bl	df_mode
	cmp	r0, #0
	beq	3f
	ldr	r0, [r4, #MON_STATE]
	cmp	r0, #MON_RACING
	bne	3f
	movs	r5, #1				@ r5 = place: 1 + planes still flying
	movs	r2, #0				@ r2 = planes still flying or falling
	movs	r6, #1
1:	ldr	r0, =players
	lsls	r1, r6, #2
	ldr	r0, [r0, r1]
	cmp	r0, #0
	beq	2f
	adds	r0, r4, r6
	adds	r0, #MON_HITS
	ldrb	r0, [r0, #0]
	cmp	r0, #DF_LIVES
	beq	2f				@ gone
	bhi	4f				@ falling
	adds	r5, #1				@ flying
4:	adds	r2, #1
2:	adds	r6, #1
	cmp	r6, #3
	ble	1b
	adds	r0, r4, #0
	adds	r0, #MON_PLACE
	strb	r5, [r0, #0]
	cmp	r2, #0				@ the last one has finished falling: won
	bne	3f
	bl	df_win
3:	pop	{r4, r5, r6}
	pop	{r0}
	bx	r0
	.ltorg

@ In place of race_complete_lap(r0 = player) from act_starthoop: no laps
@ in a dogfight.
	.thumb_func
fix_df_lap_far:
	push	{r0, lr}
	bl	df_mode
	cmp	r0, #0
	pop	{r0}
	pop	{r3}
	mov	lr, r3
	bne	1f
	ldr	r3, =race_complete_lap+1
	bx	r3
1:	bx	lr
	.ltorg

@ In place of act_pylon's "cmp r4, #0x3fff" before its "bgt no strike":
@ in a dogfight, sets "gt" so a missed pylon is never a strike.
	.thumb_func
fix_df_pylon_far:
	push	{r1, r2, r3, lr}
	bl	df_mode
	cmp	r0, #0
	beq	1f
	movs	r0, #1
	cmp	r0, #0				@ "gt"
	b	2f
1:	ldr	r0, =0x3fff
	cmp	r4, r0
2:	pop	{r1, r2, r3}
	pop	{r0}
	bx	r0
	.ltorg

@ Called from init_start_pos in place of obj_free(r0 = the start-position
@ object), after it has placed a player: puts each computer player ahead of
@ the human player. Done after every start position, so the formation wins
@ over any grid slots of the arena's own whatever order they load in (once
@ the human's start position has loaded, the formation is in the right place).
@ Then frees the object as before.
	.thumb_func
fix_dogfight_spawn_far:
	push	{r0, r4, r5, r6, r7, lr}
	bl	df_mode
	cmp	r0, #0
	beq	df_spawn_out
	ldr	r4, =players
	ldr	r4, [r4, #0]			@ players[0]
	ldr	r0, [r4, #60]			@ heading
	lsls	r0, r0, #16
	asrs	r0, r0, #16
	ldr	r3, =__ptr_ram_sin
	ldr	r3, [r3, #0]
	bl	df_bx_r3			@ sin(heading), 4.12
	lsls	r6, r0, #16
	asrs	r6, r6, #16
	ldr	r0, [r4, #60]
	lsls	r0, r0, #16
	asrs	r0, r0, #16
	ldr	r3, =__ptr_ram_cos
	ldr	r3, [r3, #0]
	bl	df_bx_r3			@ cos(heading)
	lsls	r7, r0, #16
	asrs	r7, r7, #16
	movs	r5, #1				@ players 1-3
1:	ldr	r0, =players
	lsls	r1, r5, #2
	ldr	r3, [r0, r1]			@ r3 = players[i]
	cmp	r3, #0
	beq	2f
	ldrh	r0, [r3, #2]
	cmp	r0, #OBJ_COMP_PLAYER
	bne	2f
	adr	r0, df_formation
	subs	r1, r5, #1
	lsls	r1, r1, #1
	ldrsb	r2, [r0, r1]			@ ahead / 4 (units)
	adds	r1, #1
	ldrsb	r1, [r0, r1]			@ to the side / 4
	lsls	r2, r2, #2
	lsls	r1, r1, #2
	adds	r0, r6, #0			@ x = x0 + (sin*ahead + cos*side) >> 4
	muls	r0, r2
	mov	ip, r0
	adds	r0, r7, #0
	muls	r0, r1
	add	r0, ip
	asrs	r0, r0, #4
	ldr	r2, [r4, #32]
	adds	r0, r0, r2
	str	r0, [r3, #32]
	ldr	r0, [r4, #36]			@ y = y0
	str	r0, [r3, #36]
	subs	r0, r5, #1			@ z = z0 + (cos*ahead - sin*side) >> 4
	lsls	r0, r0, #1
	adr	r2, df_formation
	ldrsb	r2, [r2, r0]
	lsls	r2, r2, #2
	adds	r0, r7, #0
	muls	r0, r2
	mov	ip, r0
	adds	r0, r6, #0
	muls	r0, r1
	mov	r2, ip
	subs	r0, r2, r0
	asrs	r0, r0, #4
	ldr	r2, [r4, #40]
	adds	r0, r0, r2
	str	r0, [r3, #40]
	movs	r0, #0
	str	r0, [r3, #56]
	str	r0, [r3, #64]
	ldr	r0, [r4, #60]			@ facing the player
	movs	r2, #128
	lsls	r2, r2, #8
	adds	r0, r0, r2
	lsls	r0, r0, #16
	asrs	r0, r0, #16
	str	r0, [r3, #60]
2:	adds	r5, #1
	cmp	r5, #3
	ble	1b
df_spawn_out:
	pop	{r0, r4, r5, r6, r7}
	pop	{r3}
	mov	lr, r3
	ldr	r3, =obj_free+1
	bx	r3				@ obj_free(object), returns to init_start_pos
	.ltorg
	.balign 4
df_formation:					@ per computer player: ahead/4, side/4 (units)
	.byte	40, -12				@ 160 ahead, 48 left
	.byte	50, 0				@ 200 ahead
	.byte	40, 12				@ 160 ahead, 48 right
	.balign 4

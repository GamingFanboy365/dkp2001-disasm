@ Uninitialised RAM. EWRAM .bss at 0x02000000, IWRAM .bss32 after .text32.

	.section .bss, "aw", %nobits
errno:  @ 02000000
	.space 0x4
OBJVRAM_PTR:  @ 02000004
	.space 0x4
OAM_PTR:  @ 02000008
	.space 0x4
OAM_ROTATEPTR:  @ 0200000c
	.space 0x1
BIG_FONT_PAL:  @ 0200000d
	.space 0x1
TITLE_STATE:  @ 0200000e
	.space 0x1
GAME_MODE:  @ 0200000f
	.space 0x1
BIG_FONT_TABLE:  @ 02000010
	.space 0xcc
CHAR_SELECTED:  @ 020000dc
	.space 0x1
SPLINE_EDIT:  @ 020000dd
	.space 0x3
SMALL_FONT_PAL:  @ 020000e0
	.space 0x1
SMALL_FONT_COL:  @ 020000e1
	.space 0x1
OBJ_ATTR_0:  @ 020000e2
	.space 0x2
OBJ_ATTR_1:  @ 020000e4
	.space 0x2
OBJ_ATTR_2:  @ 020000e6
	.space 0x2
STORY_STAGE:  @ 020000e8
	.space 0x4
LOCAL_MEM:  @ 020000ec
	.space 0x80
SCRATCH_MEM:  @ 0200016c
	.space 0x40
hdma_buffer:  @ 020001ac
	.space 0x2800
math_randseed:  @ 020029ac
	.space 0x4
joytrg_a_delay:  @ 020029b0
	.space 0x4
joytrg_b_delay:  @ 020029b4
	.space 0x4
joytrg_l_delay:  @ 020029b8
	.space 0x4
joytrg_r_delay:  @ 020029bc
	.space 0x4
audio_stopped:  @ 020029c0
	.space 0x4
plr_ctrl:  @ 020029c4
	.space 0x60
plr_ctrl_new:  @ 02002a24
	.space 0x60
game_level:  @ 02002a84
	.space 0x4
ai_network:  @ 02002a88
	.space 0x4
vcount:  @ 02002a8c
	.space 0x400
vcount_p:  @ 02002e8c
	.space 0x4
tmp_cmp_player:  @ 02002e90
	.space 0x4
logo_state:  @ 02002e94
	.space 0x4
logo_timer:  @ 02002e98
	.space 0x8
state:  @ 02002ea0
	.space 0x9c4
next:  @ 02003864
	.space 0x4
left:  @ 02003868
	.space 0x4
pal_bg:  @ 0200386c
	.space 0x4
pal_skygradient:  @ 02003870
	.space 0x4
vtab_bd:  @ 02003874
	.space 0x140
vtab_bldalpha:  @ 020039b4
	.space 0x140
map_lvl0:  @ 02003af4
	.space 0x4
map_lvl1:  @ 02003af8
	.space 0x4
map_sky:  @ 02003afc
	.space 0x4
op_mask:  @ 02003b00
	.space 0x4
players:  @ 02003b04
	.space 0x10
camera:  @ 02003b14
	.space 0x4
monitor:  @ 02003b18
	.space 0x4
object_draw_list:  @ 02003b1c
	.space 0x4
object_process_list:  @ 02003b20
	.space 0x4
object_hit_hash:  @ 02003b24
	.space 0x400
objectv:  @ 02003f24
	.space 0x6800
object_free_list:  @ 0200a724
	.space 0x4
cursor_x:  @ 0200a728
	.space 0x4
cursor_y:  @ 0200a72c
	.space 0x4
level_num:  @ 0200a730
	.space 0x4
menu:  @ 0200a734
	.space 0x4
ptcl_data:  @ 0200a738
	.space 0x800
ptcl_palette:  @ 0200af38
	.space 0x2
ptcl_sv:  @ 0200af3a
	.space 0x80
ptcl_sp:  @ 0200afba
	.space 0x2
spr_info:  @ 0200afbc
	.space 0x1000
spr_list:  @ 0200bfbc
	.space 0x100
spr_firstfree:  @ 0200c0bc
	.space 0x4
spr_numleft:  @ 0200c0c0
	.space 0x4
anim_blockv:  @ 0200c0c4
	.space 0x404
pts:  @ 0200c4c8
	.space 0x380
num_pts:  @ 0200c848
	.space 0x4
get_pts:  @ 0200c84c
	.space 0x4
looping:  @ 0200c850
	.space 0x8
pre_calc:  @ 0200c858
	.space 0x60
cur_pt:  @ 0200c8b8
	.space 0x4
cur_seg_pt:  @ 0200c8bc
	.space 0x4
delta:  @ 0200c8c0
	.space 0x4
transfercount:  @ 0200c8c4
	.space 0x4
errorcount:  @ 0200c8c8
	.space 0x4
unreperrorcount:  @ 0200c8cc
	.space 0x4
audio_num_channels:  @ 0200c8d0
	.space 0x4
audio_timer_ref:  @ 0200c8d4
	.space 0x4
audio_playback_freq_ref:  @ 0200c8d8
	.space 0x4
audio_freq_mult:  @ 0200c8dc
	.space 0x4
audio_buff_size_ref:  @ 0200c8e0
	.space 0x4
audio_fx_samplist_ref:  @ 0200c8e4
	.space 0x4
audio_tune_list_ref:  @ 0200c8e8
	.space 0x4
audio_unique_id:  @ 0200c8ec
	.space 0x4
audio_error_print:  @ 0200c8f0
	.space 0x4
menu_main_timer:  @ 0200c8f4
	.space 0x4
menu_main_state:  @ 0200c8f8
	.space 0x4
local_level:  @ 0200c8fc
	.space 0x4
handles:  @ 0200c900
	.space 0x1080
oams:  @ 0200d980
	.space 0x400
real_oams:  @ 0200dd80
	.space 0x4
max_oams:  @ 0200dd84
	.space 0x4
menu_anim_handles:  @ 0200dd88
	.space 0xb0
count.21:  @ 0200de38
	.space 0x4
x:  @ 0200de3c
	.space 0x4
y:  @ 0200de40
	.space 0x4
rotate:  @ 0200de44
	.space 0x4
invscale:  @ 0200de48
	.space 0x4
dx:  @ 0200de4c
	.space 0x4
dy:  @ 0200de50
	.space 0x4
wobble:  @ 0200de54
	.space 0x4
yp_actual:  @ 0200de58
	.space 0x4
yp_target:  @ 0200de5c
	.space 0x4
rotate_actual:  @ 0200de60
	.space 0x4
rotate_target:  @ 0200de64
	.space 0x4
scale_actual:  @ 0200de68
	.space 0x4
scale_target:  @ 0200de6c
	.space 0x4
scaleinc:  @ 0200de70
	.space 0x4
xp_actual:  @ 0200de74
	.space 0x4
xp_target:  @ 0200de78
	.space 0x4
interpx:  @ 0200de7c
	.space 0x4
interpy:  @ 0200de80
	.space 0x4
current_plane:  @ 0200de84
	.space 0x4
B_0200de88:  @ 0200de88
	.space 0x4
current_image:  @ 0200de8c
	.space 0x4
coin_handle:  @ 0200de90
	.space 0x8
select_text_handles:  @ 0200de98
	.space 0x18
select_text_shadow_handle:  @ 0200deb0
	.space 0x8
world_text_handle:  @ 0200deb8
	.space 0x4
text_difficulty_handle:  @ 0200debc
	.space 0x4
shadow_buffer:  @ 0200dec0
	.space 0x4
current_select:  @ 0200dec4
	.space 0x4
current_mode:  @ 0200dec8
	.space 0x4
current_character:  @ 0200decc
	.space 0x4
init_character:  @ 0200ded0
	.space 0x4
virtual_mode:  @ 0200ded4
	.space 0x4
x_actual:  @ 0200ded8
	.space 0x18
x_target:  @ 0200def0
	.space 0x18
select_x:  @ 0200df08
	.space 0x18
select_y:  @ 0200df20
	.space 0x18
flipped:  @ 0200df38
	.space 0x4
current_language:  @ 0200df3c
	.space 0x4
B_0200df40:  @ 0200df40
	.space 0x4
B_0200df44:  @ 0200df44
	.space 0x4
state_main:  @ 0200df48
	.space 0x8
levels:  @ 0200df50
	.space 0xa8
slots:  @ 0200dff8
	.space 0x10
game:  @ 0200e008
	.space 0x4
sls:  @ 0200e00c
	.space 0x4
sl_chardata:  @ 0200e010
	.space 0x100
sl_charbase:  @ 0200e110
	.space 0x80
sl_base:  @ 0200e190
	.space 0x4
sl_start:  @ 0200e194
	.space 0x4
sl_left:  @ 0200e198
	.space 0x40
sl_right:  @ 0200e1d8
	.space 0x40
pls:  @ 0200e218
	.space 0x4
pl_palidx:  @ 0200e21c
	.space 0x40
pl_base:  @ 0200e25c
	.space 0x4
pl_start:  @ 0200e260
	.space 0x4
pl_left:  @ 0200e264
	.space 0x10
pl_right:  @ 0200e274
	.space 0x14
heap_end.63:  @ 0200e288
	.space 0x4
monitor_stdin:  @ 0200e28c
	.space 0x4
monitor_stdout:  @ 0200e290
	.space 0x4
monitor_stderr:  @ 0200e294
	.space 0x4
openfiles:  @ 0200e298
	.space 0xa0
thenan.3:  @ 0200e338
	.space 0x18
B_0200e350:  @ 0200e350
	.space 0x10

	.section .bss32, "aw", %nobits
SMALL_FONT_AREA:  @ 03002eac
	.space 0xa0
sys_oam:  @ 03002f4c
	.space 0x400
sys_irq_table:  @ 0300334c
	.space 0x3c
sys_irq_flag:  @ 03003388
	.space 0x2
sys_joycnt:  @ 0300338a
	.space 0x2
sys_joytrg:  @ 0300338c
	.space 0x2
sys_joydbl:  @ 0300338e
	.space 0x2
sys_xcnt:  @ 03003390
	.space 0x2
sys_ycnt:  @ 03003392
	.space 0x2
sys_xmid:  @ 03003394
	.space 0x2
sys_ymid:  @ 03003396
	.space 0x2
sys_flags:  @ 03003398
	.space 0x4
sys_counter:  @ 0300339c
	.space 0x4
sys_oam_start:  @ 030033a0
	.space 0x4
sys_mode:  @ 030033a4
	.space 0x4
oam_z:  @ 030033a8
	.space 0x200
audio_buff_tog:  @ 030035a8
	.space 0x4
audio_cur_tune:  @ 030035ac
	.space 0x4
audio_new_tune:  @ 030035b0
	.space 0x4
audio_delta_time:  @ 030035b4
	.space 0x80
audio_delta_time_dec:  @ 03003634
	.space 0x4
audio_ppqn:  @ 03003638
	.space 0x4
audio_tempo:  @ 0300363c
	.space 0x4
audio_buffers:  @ 03003640
	.space 0x480
audio_precalc_buff:  @ 03003ac0
	.space 0x2c0
audio_pitchbend:  @ 03003d80
	.space 0x40
audio_modulation:  @ 03003dc0
	.space 0x80
audio_chan_vols:  @ 03003e40
	.space 0x10
audio_monophonic_op:  @ 03003e50
	.space 0x10
audio_chan_notes:  @ 03003e60
	.space 0x1200
audio_chan_fx:  @ 03005060
	.space 0x90
audio_chan_dly:  @ 030050f0
	.space 0xc
audio_chan_id:  @ 030050fc
	.space 0xc
audio_num_tracks:  @ 03005108
	.space 0x4
audio_vmap_ptr:  @ 0300510c
	.space 0x4
audio_voices:  @ 03005110
	.space 0x40
audio_samp_list:  @ 03005150
	.space 0x4
audio_midi_tracks:  @ 03005154
	.space 0x40
audio_ram_code_blk:  @ 03005194
	.space 0x13ec
audio_loop_ptrs:  @ 03006580
	.space 0x40
audio_tune_vol:  @ 030065c0
	.space 0x4
audio_fx_vol:  @ 030065c4
	.space 0x4


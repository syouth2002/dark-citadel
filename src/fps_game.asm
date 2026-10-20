; ============================================================================
;  DARK CITADEL - game layer: enemies (scaled sprites), shooting, status
; ============================================================================
E_T     equ 0           ; type: 0 free, 1..4 enemies, 5..8 pickups (T_*)
E_X     equ 1           ; x 8.8
E_Y     equ 3           ; y 8.8
E_HP    equ 5
E_ST    equ 6           ; 0 idle, 1 chase, 2 attack, 3 dying, 4 dead
E_TM    equ 7
E_AN    equ 8
E_DEP   equ 9           ; perpendicular depth 8.8 (this frame)
E_CS    equ 11          ; first screen column (signed)
E_CE    equ 12          ; last screen column (signed)
E_VIS   equ 13          ; 1 = in view, 2 = drawn, +4 = at least one column on screen
E_TOP   equ 14          ; top view row
E_HS    equ 15          ; height in rows

I_FIRE  equ 10h
I_ALT   equ 20h             ; SHIFT / trigger B: the other weapon
AXE_REACH equ 300           ; the axe reaches ~1.2 cells

T_HUSK   equ 1
T_ORB    equ 2
T_BRUTE  equ 3          ; from floor 4: slow, tough, hits hard
T_STALK  equ 4          ; from floor 7: fast, darts sideways, fragile
T_WARDEN equ 5          ; floor 12: the boss, guards the exit
T_ITEM   equ 6          ; first pickup type
T_HEALTH equ 6
T_AMMO   equ 7
T_KEYO   equ 8
T_KEYV   equ 9
T_OIL    equ 10         ; lantern oil: the light reaches further for a while
T_BLOAT  equ 11         ; from floor 5: slow; swells and bursts near the player
T_TURRET equ 12         ; from floor 9: does not move, fires whenever it sees you
T_BAT    equ 13         ; from floor 3: fast and erratic, fragile
OIL_TIME equ 400        ; frames (about a minute)

; ----------------------------------------------------------------------------
;  game / floor setup
; ----------------------------------------------------------------------------
new_game:
        ld a,100
        ld (v_hp),a
        ld a,(v_debug)              ; a debug game starts with 99 rounds,
        or a                        ; others by the difficulty
        ld a,99
        jr nz,ng_1
        ld a,(v_diff)
        ld e,a
        ld d,0
        ld hl,ng_ammo
        add hl,de
        ld a,(hl)
ng_1:   ld (v_ammo),a
        ld hl,0
        ld (v_gsecs),hl
        xor a
        ld (v_deaths),a
        ld (v_tkills),a
        ld (v_hurt),a
        ld a,(v_pw)                 ; from a password: its health, its rounds
        or a
        jr z,ng_2
        ld a,(v_pwhp)
        ld (v_hp),a
        ld a,(v_pwammo)
        ld (v_ammo),a
ng_2:   ld a,(v_startlv)            ; 0, or the floor chosen (debug, password)
        ld (v_level),a
        jp start_level
ng_ammo: defb 50,30,0               ; rounds at the start: EASY, NORMAL, HARD

restart_level:
        ld a,100
        ld (v_hp),a
        xor a
        ld (v_hurt),a
        ld a,(v_diff)               ; rounds made up to: EASY 30, 3 more
        cp 2                        ; a floor; NORMAL 20, 2 more a floor;
        jr z,start_level            ; HARD none
        ld c,a
        ld a,(v_level)
        ld b,a
        add a,a
        dec c
        jr z,rl_h
        add a,b
        add a,10
rl_h:   add a,20
        ld b,a
        ld a,(v_ammo)
        cp b
        jr nc,start_level
        ld a,b
        ld (v_ammo),a

; load floor v_level: map, objects, player, colours
start_level:
        call floor_tune
        ld hl,0
        ld (v_fsecs),hl
        ld a,1
        ld (v_timing),a             ; the clock runs while on a floor
        ld (v_firelock),a           ; (no shot until SPACE is let go)
        ld a,(v_ammo)               ; the gun, or the axe if out of rounds
        or a
        ld a,0
        jr nz,sl_wp
        inc a
sl_wp:  ld (v_weapon),a
        ld hl,0
        ld (v_oil),hl
        xor a
        ld (v_flasht),a
        ld a,LANTERN
        call set_lantern
        xor a
        ld (v_kills),a
        ld (v_dead),a
        ld (v_fire_cd),a
        ld (v_flash),a
        ld (v_keys),a
        ld (v_items),a
        ld (v_lvdone),a
        ld (v_msg_t),a
        ld (v_nenemy),a
        ld (v_nitems),a
        ld a,2
        ld (v_hud_dirty),a
        ld (v_mm_dirty),a
        ld a,0FFh
        ld (v_pcell),a
        ld (v_pcell+1),a
        ld a,2                      ; the view: both pages in full
        ld (v_vfull),a
        xor a                       ; auto map: nothing seen yet
        ld (v_newn),a
        ld hl,v_seen
        ld de,v_seen+1
        ld bc,MAPS*MAPN-1
        ld (hl),a
        ldir
        ld hl,v_enemies
        ld de,v_enemies+1
        ld bc,NEN*16-1
        ld (hl),0
        ldir
        ; level table entry (8 bytes)
        ld a,(v_level)
        add a,a
        add a,a
        add a,a
        ld e,a
        ld d,0
        xor a
        ld (v_boss),a
        ld (v_hcnt),a
        ld (v_acnt),a
        ld (v_xdone),a
        ld ix,level_tbl
        add ix,de
        ld hl,v_map                 ; walls all round (and outside), the
        ld de,v_map+1               ; floor inside
        ld bc,MAPS*MAPN-1
        ld (hl),1
        ldir
        ld hl,v_map+MAPS+1
        ld c,MAPN-2
sl_f:   push hl
        ld b,MAPN-2
sl_f1:  ld (hl),0
        inc hl
        djnz sl_f1
        pop hl
        ld de,MAPS
        add hl,de
        dec c
        jr nz,sl_f
        ld l,(ix+0)                 ; the walls: runs (tools/fps_mapcode.py)
        ld h,(ix+1)
sl_r:   ld a,(hl)
        cp 0FFh
        jr z,sl_s
        ld c,a                      ; x | down << 5 | type << 6
        inc hl
        ld b,(hl)                   ; y | (length-1) << 5
        inc hl
        ld a,(hl)                   ; (length-1) >> 3 | door << 2
        inc hl
        push hl
        push af
        and 3
        add a,a
        add a,a
        add a,a
        ld e,a
        ld a,b
        rlca
        rlca
        rlca
        and 7
        or e
        inc a
        ld (v_qv),a                 ; length
        pop af
        rrca
        rrca
        and 31
        ld (v_qv+1),a               ; the door's place (1..), 0 none
        ld a,b
        and 31
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,c
        and 31
        or l
        ld l,a
        ld de,v_map
        add hl,de                   ; the first cell
        ld de,1
        bit 5,c
        jr z,sl_r1
        ld e,MAPS                   ; (down)
sl_r1:  ld a,c
        rlca
        rlca
        and 3                       ; wall type
        ld c,a
        ld a,(v_qv)
        ld b,a
sl_r2:  ld a,(v_qv+1)
        dec a
        ld (v_qv+1),a
        ld a,c
        jr nz,sl_r3
        ld a,4                      ; the door in this wall
sl_r3:  ld (hl),a
        add hl,de
        djnz sl_r2
        pop hl
        jr sl_r
sl_s:   inc hl                      ; special cells: locked doors, the exit
sl_s1:  ld a,(hl)
        cp 0FFh
        jr z,sl_o0
        ld c,a
        inc hl
        ld a,(hl)
        inc hl
        push hl
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,c
        and 31
        or l
        ld l,a
        ld de,v_map
        add hl,de
        ld a,c
        rlca
        rlca
        rlca
        and 7
        add a,4
        ld (hl),a
        pop hl
        jr sl_s1
sl_o0:
        ld a,(ix+5)
        ld (v_px+1),a
        ld a,80h
        ld (v_px),a
        ld (v_py),a
        ld a,(ix+6)
        ld (v_py+1),a
        xor a
        ld (v_pa),a
        ld a,(ix+7)
        ld (v_grp),a
        ld b,(ix+4)
        ld l,(ix+2)
        ld h,(ix+3)
        ld ix,v_enemies
sl_o:   ld a,(hl)                   ; x | (type & 7) << 5
        ld c,a
        and 31
        ld (ix+E_X+1),a
        ld (ix+E_X),80h
        inc hl
        ld a,(hl)                   ; y | (type >> 3) << 5
        ld d,a                      ; (B counts the objects)
        and 31
        ld (ix+E_Y+1),a
        ld (ix+E_Y),80h
        inc hl
        ld a,d
        rrca
        rrca
        and 8
        ld d,a
        ld a,c
        rlca
        rlca
        rlca
        and 7
        or d
        ld (ix+E_T),a
        call is_foe
        jr nc,sl_it
        push hl
        call ty_idx
        ld hl,e_hp-1            ; health by type
        add a,l
        ld l,a
        jr nc,sl_h1
        inc h
sl_h1:  ld a,(hl)
        pop hl
        ld (ix+E_HP),a
        ld a,(ix+E_T)
        cp T_WARDEN
        jr nz,sl_nw
        ld a,1                      ; a boss on this floor (asleep)
        ld (v_boss),a
        ld (v_bossix),ix
sl_nw:
        ld a,(v_nenemy)
        inc a
        ld (v_nenemy),a
        jr sl_n
sl_it:  cp T_HEALTH                  ; NORMAL / HARD: half the health items
        ld de,v_hcnt                ; and half the ammo items
        jr z,sl_i0                  ; (the 1st, 3rd ... stay)
        cp T_AMMO
        jr nz,sl_i1
        ld de,v_acnt
sl_i0:  ld a,(v_diff)
        or a
        jr z,sl_i1
        ld a,(de)
        xor 1
        ld (de),a
        jr nz,sl_i1
        ld (ix+E_T),a
        jr sl_n
sl_i1:  ld a,(v_nitems)
        inc a
        ld (v_nitems),a
sl_n:   ld de,16
        add ix,de
        dec b
        jp nz,sl_o
        ld a,(v_xdone)              ; then the extra enemies: NORMAL the first
        or a                        ; half (rounded up), HARD all
        jr nz,sl_x9
        inc a
        ld (v_xdone),a
        ld a,(v_diff)
        or a
        jr z,sl_x9
        ld c,a
        ld a,(v_level)
        add a,a
        ld e,a
        ld d,0
        ld hl,extra_tbl
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld b,(hl)
        inc hl
        dec c
        jr nz,sl_x1
        inc b
        srl b
sl_x1:  inc b
        dec b
        jp nz,sl_o
sl_x9:  push ix                     ; the slots in use
        pop hl
        ld de,-v_enemies
        add hl,de
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,h
        ld (v_nobj),a
        ; view: plane 1 = colour group of this floor, plane 0 cleared; repaint all
        ld a,80h
        call view_reset
        ld a,0C0h
        call view_reset
        ld hl,v_ptop0
        ld b,NCOL
        call st_zero
        ld hl,v_ptop1
        ld b,NCOL
        call st_zero
        ld hl,v_pbot0
        ld b,NCOL
        call st_vh
        ld hl,v_pbot1
        ld b,NCOL
        jp st_vh

st_zero:
        ld (hl),0
        inc hl
        djnz st_zero
        ret

; A = page high byte: view rows -> plane 0 = 0, plane 1 = group byte
view_reset:
        ld h,a
        ld l,0
        ld de,VY0*40
        add hl,de
        ld b,VH
vr_1:   push bc
        push hl
        ld b,32
vr_2:   ld (hl),0
        set 5,h
        ld a,(v_grp)
        ld (hl),a
        res 5,h
        inc hl
        djnz vr_2
        pop hl
        ld de,40
        add hl,de
        pop bc
        djnz vr_1
        ret

; ----------------------------------------------------------------------------
;  doors / exit:  A = cell value, HL = cell pointer
; ----------------------------------------------------------------------------
door_touch:
        cp 4
        ret c
        jr z,dt_open
        cp 5
        jr nz,dt_v
        ld a,(v_keys)
        bit 0,a
        jr nz,dt_open
        ld hl,s_need_o
        jp show_msg
dt_v:   cp 6
        jr nz,dt_x
        ld a,(v_keys)
        bit 1,a
        jr nz,dt_open
        ld hl,s_need_v
        jp show_msg
dt_x:   cp 7
        ret nz
        ld a,(v_boss)
        or a
        jr z,dt_x1
        ld hl,s_barred              ; the warden bars the way
        jp show_msg
dt_x1:  ld a,1
        ld (v_lvdone),a
        ret
dt_open:
        ld (hl),0
        ld de,v_seen-v_map      ; on the map it is floor now
        add hl,de
        ld a,(hl)
        or a
        jr z,dto_1
        ld (hl),80h
dto_1:  ld a,2
        ld (v_mm_dirty),a       ; the map changed
        ld (v_vfull),a          ; (and the view)
        jp snd_door

; HL = message, shown for a while on the status line
show_msg:
        ld (v_msg),hl
        ld a,20
        ld (v_msg_t),a
        ld a,2
        ld (v_hud_dirty),a
        ret

; ----------------------------------------------------------------------------
;  floor finished: tally, then the next floor (or the ending)
; ----------------------------------------------------------------------------
intermission:
        xor a
        ld (v_timing),a
        ld (v_record),a
        ld a,(v_kills)              ; totals
        ld hl,v_tkills
        add a,(hl)
        ld (hl),a
        ld a,(v_debug)              ; (not from a debug or a password game)
        ld hl,v_pw
        or (hl)
        jr nz,in_1
        ld a,(v_level)              ; the last floor: a new best time?
        inc a
        cp NLEVEL
        jr c,in_1
        call best_get
        ld a,h
        or l
        jr z,in_new
        ld de,(v_gsecs)
        or a
        sbc hl,de
        jr c,in_1
        jr z,in_1
in_new: call best_ptr
        ld de,(v_gsecs)
        ld (hl),e
        inc hl
        ld (hl),d
        ld a,1
        ld (v_record),a
in_1:   ld a,2
        call bgm_start
        ld a,(v_level)              ; the last floor: dawn first
        inc a
        cp NLEVEL
        call nc,ending
        ld a,80h
        call im_page
        ld a,0C0h
        call im_page
im_w1:  call read_input             ; wait for SPACE released, then pressed
        ld a,(v_inp)
        and I_FIRE
        jr nz,im_w1
im_w2:  call read_input
        ld a,(v_inp_new)
        and I_FIRE
        jr z,im_w2
        ld a,(v_level)
        inc a
        cp NLEVEL
        jr nc,im_end
        ld (v_level),a
        jp start_level
im_end: call title
        jp new_game

; ----------------------------------------------------------------------------
;  title: choose the map mode (full map / auto map), SPACE starts
; ----------------------------------------------------------------------------
title:
        xor a
        ld (v_debug),a
        ld (v_god),a
        ld (v_startlv),a
        ld (v_cheat),a
        ld (v_pw),a
        ld (v_lastkey),a
        ld a,2
        call bgm_start
        ld a,80h
        call ti_page
        ld a,0C0h
        call ti_page
ti_w1:  call read_input             ; SPACE released first
        ld a,(v_inp)
        and I_FIRE
        jr nz,ti_w1
ti_w2:  call read_input
        ld a,(v_lastkey)            ; P: a password
        and 0DFh
        cp 'P'
        jp z,ti_pw
        ld a,(v_inp_new)
        ld b,a
        and 0Fh                     ; a direction pressed: the hidden command
        jr z,ti_w3
        ld c,a
        ld a,(v_cheat)
        ld e,a
        ld d,0
        ld hl,cheat_seq
        add hl,de
        ld a,c
        cp (hl)
        jr nz,ti_c0
        ld a,e
        inc a
        cp 8
        jp z,debug_menu
        jr ti_c1
ti_c0:  xor a                       ; wrong: start again (an extra "up"
        dec c                       ; still counts as the start)
        jr nz,ti_c1
        inc a
        ld c,e
        dec c
        dec c
        jr nz,ti_c1
        inc a
ti_c1:  ld (v_cheat),a
ti_w3:  ld a,b                       ; left / right: the difficulty
        and 0Ch                     ; (round and round: the hidden command,
        jr z,ti_w4                  ; left right left right, leaves it be)
        ld c,1
        and 8
        jr nz,ti_d1
        inc c                       ; (left: 2 on = 1 back)
ti_d1:  ld a,(v_diff)
        add a,c
        cp 3
        jr c,ti_d2
        sub 3
ti_d2:  ld (v_diff),a
        push bc                     ; (only that line: quick, no key missed)
        ld a,80h
        call ti_diff
        ld a,0C0h
        call ti_diff
        pop bc
ti_w4:  ld a,b
        and I_FIRE
        jp z,ti_w2
        ret
; the password: right -> start there; wrong -> say so, the title again
ti_pw:  call pw_entry
        ret z
        ld a,80h
        call pw_wrong
        ld a,0C0h
        call pw_wrong
        ld b,0
tw_1:   push bc
        call read_input             ; (a moment to read it)
        pop bc
        djnz tw_1
        jp title
pw_wrong:
        ld (v_tgt_h),a
        ld a,10
        call set_color
        ld hl,s_pwbad
        ld de,(8 << 8) | (VY0+70)
        jp draw_text

; up up down down left right left right
cheat_seq: defb 1,1,2,2,4,8,4,8

ti_page:
        push af
        call im_clear
        pop af
        push af
        ld h,a                      ; clear the status and floor lines
        ld l,0
        ld de,(VY0+VH)*40
        add hl,de
        push hl
        call tp_clr
        pop hl
        set 5,h                     ; (plane 1)
        call tp_clr
        pop af
        push af
        ld h,a                      ; clear the map panel
        ld l,0
        ld de,MM_Y*40+MM_X
        add hl,de
        ld b,MM_H*3
tp_1:   push bc
        push hl
        ld b,MM_W/2
tp_2:   ld (hl),0
        set 5,h
        ld (hl),0
        res 5,h
        inc hl
        djnz tp_2
        pop hl
        ld de,40
        add hl,de
        pop bc
        djnz tp_1
        pop af
        ld (v_tgt_h),a
        ld hl,s_ti_nofl             ; (no floor on the title)
        ld de,(15 << 8) | L4_Y
        call draw_text
        ld a,(v_tgt_h)              ; the logo, straight onto the page
        ld d,a
        ld e,VY0*40
        ld hl,logo_p0
        push de
        call unlz
        pop de
        set 5,d                     ; (plane 1)
        ld hl,logo_p1
        call unlz
        ld a,7
        call set_color
        ld hl,s_ti_keys
        ld de,(4 << 8) | (VY0+50)
        call draw_text
        ld hl,s_ti_keys2
        ld de,(6 << 8) | (VY0+60)
        call draw_text
        ld hl,s_ti_pw
        ld de,(8 << 8) | (VY0+70)
        call draw_text
        ld hl,s_ti_df
        ld de,(5 << 8) | (VY0+80)
        call draw_text
        ld a,(v_tgt_h)
        call ti_diff
        ld de,(10 << 8) | (VY0+100)
        jp im_sp

; A = page: the difficulty's name and its best time on the title
ti_diff:
        ld (v_tgt_h),a
        ld a,14
        call set_color
        call diff_name
        ld de,(18 << 8) | (VY0+80)
        call draw_text
        ld hl,s_ti_nobest
        ld de,(9 << 8) | (VY0+90)
        call draw_text
        call best_get               ; (this difficulty's)
        ld a,h
        or l
        ret z
        push hl
        ld hl,s_best
        ld de,(9 << 8) | (VY0+90)
        call draw_text
        pop hl
        ld de,(19 << 8) | (VY0+90)
        jp draw_time
s_ti_nobest: defb "               ",0

; HL -> this difficulty's best time / HL = it (0: none yet)
best_ptr:
        ld a,(v_diff)
        add a,a
        ld e,a
        ld d,0
        ld hl,v_best
        add hl,de
        ret
best_get:
        call best_ptr
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ret
; HL = the difficulty's name (6 characters)
diff_name:
        ld a,(v_diff)
        ld e,a
        add a,a
        add a,a
        add a,a
        sub e                       ; * 7
        ld e,a
        ld d,0
        ld hl,s_diffs
        add hl,de
        ret
s_diffs:    defb "EASY  ",0,"NORMAL",0,"HARD  ",0
s_ti_df:    defb "DIFFICULTY <        >",0

tp_clr: ld d,h
        ld e,l
        inc de
        ld bc,(MSG_Y+6-VY0-VH)*40-1
        ld (hl),0
        ldir
        ret

s_ti_nofl:  defb "              ",0
s_ti_keys:  defb "ARROWS MOVE    SPACE FIRE",0
s_ti_keys2: defb "SHIFT  CHANGE WEAPON",0
s_ti_pw:    defb "P  ENTER PASSWORD",0
s_pwl:      defb "PASSWORD         ",0    ; (covers "P  ENTER PASSWORD")
s_pwbad:    defb "WRONG PASSWORD   ",0

im_page:
        call im_clear
        jr im_txt
im_clear:
        ld (v_tgt_h),a
        ld h,a                      ; clear the view (both planes)
        ld l,0
        ld de,VY0*40
        add hl,de
        ld b,VH
im_c1:  push bc
        push hl
        ld b,32
im_c2:  ld (hl),0
        set 5,h
        ld (hl),0
        res 5,h
        inc hl
        djnz im_c2
        pop hl
        ld de,40
        add hl,de
        pop bc
        djnz im_c1
        ret
im_txt: ld a,(v_level)
        inc a
        cp NLEVEL
        jp nc,im_fin
        ld a,14
        call set_color
        ld hl,s_floor
        ld de,(10 << 8) | (VY0+24)
        call draw_text
        ld a,(v_level)
        inc a
        ld de,(16 << 8) | (VY0+24)
        call draw_num2
        ld a,15
        call set_color
        ld hl,s_kills
        ld de,(10 << 8) | (VY0+44)
        call draw_text
        ld a,(v_kills)
        ld de,(16 << 8) | (VY0+44)
        call draw_num2
        ld a,(v_nenemy)
        ld de,(19 << 8) | (VY0+44)
        call draw_num2
        ld hl,s_itemsl
        ld de,(10 << 8) | (VY0+56)
        call draw_text
        ld a,(v_items)
        ld de,(16 << 8) | (VY0+56)
        call draw_num2
        ld a,(v_nitems)
        ld de,(19 << 8) | (VY0+56)
        call draw_num2
        ld hl,s_timel
        ld de,(10 << 8) | (VY0+68)
        call draw_text
        ld hl,(v_fsecs)
        ld de,(16 << 8) | (VY0+68)
        call draw_time
        call pw_make
        ld a,14
        call set_color
        ld hl,s_pwl
        ld de,(10 << 8) | (VY0+78)
        call draw_text
        ld hl,v_pwtext
        ld de,(19 << 8) | (VY0+78)
        call draw_text
        ld e,VY0+90
        jr im_sp
im_fin: ld a,13
        call set_color
        ld hl,s_end1
        ld de,(5 << 8) | (VY0+10)
        call draw_text
        ld a,15
        call set_color
        ld hl,s_tot1
        ld de,(7 << 8) | (VY0+28)
        call draw_text
        ld hl,s_tot2
        ld de,(7 << 8) | (VY0+38)
        call draw_text
        ld hl,s_tot3
        ld de,(7 << 8) | (VY0+48)
        call draw_text
        ld hl,s_best
        ld de,(7 << 8) | (VY0+58)
        call draw_text
        ld hl,(v_gsecs)
        ld de,(19 << 8) | (VY0+28)
        call draw_time
        ld a,(v_tkills)
        ld de,(19 << 8) | (VY0+38)
        call draw_num3
        ld a,(v_deaths)
        ld de,(19 << 8) | (VY0+48)
        call draw_num3
        call best_get
        ld de,(19 << 8) | (VY0+58)
        call draw_time
        ld a,(v_record)
        or a
        jr z,if_1
        ld a,14
        call set_color
        ld hl,s_record
        ld de,(11 << 8) | (VY0+70)
        call draw_text
if_1:   ld a,13
        call set_color
        ld hl,s_end2
        ld de,(6 << 8) | (VY0+84)
        call draw_text
        ld e,VY0+98
im_sp:  ld d,10
        push de
        ld a,7
        call set_color
        pop de
        ld hl,s_space
        jp draw_text

; ----------------------------------------------------------------------------
;  debug menu (hidden command on the title): floor, sound test, invincible
;  rows: 0 floor, 1 sound, 2 invincible, 3 start, 4 exit (to the title)
; ----------------------------------------------------------------------------
NSND    equ NSFX+NVOICE+5           ; effects, voices, tunes
debug_menu:
        ld a,1
        ld (v_debug),a
        xor a
        ld (v_dsel),a
        ld (v_dfloor),a
        ld (v_dsnd),a
        ld a,80h
        call dm_page
        ld a,0C0h
        call dm_page
dm_lp:  call read_input
        ld a,(v_inp_new)
        ld b,a
        or a
        jr z,dm_lp
        ld hl,v_dsel
        bit 0,b                     ; up
        jr z,dm_1
        ld a,(hl)
        dec a
        jp p,dm_1a
        ld a,4
dm_1a:  ld (hl),a
dm_1:   bit 1,b                     ; down
        jr z,dm_2
        ld a,(hl)
        inc a
        cp 5
        jr c,dm_1b
        xor a
dm_1b:  ld (hl),a
dm_2:   ld a,b
        and 0Ch                     ; left / right: change the value
        jr z,dm_4
        ld c,1
        bit 2,b
        jr z,dm_3
        ld c,-1
dm_3:   ld a,(hl)
        or a
        jr nz,dm_3s
        ld a,(v_dfloor)             ; floor 1..12
        add a,c
        cp NLEVEL
        jr c,dm_3f
        ld a,0
        bit 7,c
        jr z,dm_3f
        ld a,NLEVEL-1
dm_3f:  ld (v_dfloor),a
        jr dm_4
dm_3s:  cp 1
        jr nz,dm_3g
        ld a,(v_dsnd)               ; sound 1..15
        add a,c
        cp NSND
        jr c,dm_3t
        ld a,0
        bit 7,c
        jr z,dm_3t
        ld a,NSND-1
dm_3t:  ld (v_dsnd),a
        jr dm_4
dm_3g:  cp 2
        jr nz,dm_4
        ld a,(v_god)
        xor 1
        ld (v_god),a
dm_4:   bit 4,b                     ; SPACE
        jr z,dm_6
        ld a,(v_dsel)
        cp 4
        jp z,title                  ; EXIT: back to the title (normal mode)
        cp 3
        jr z,dm_go
        cp 1
        jr nz,dm_6
        ld a,(v_dsnd)               ; play the sound
        cp NSFX
        jr nc,dm_5
        call snd_play
        jr dm_6
dm_5:   sub NSFX
        cp NVOICE
        jr nc,dm_5m
        call voice_play
        jr dm_6
dm_5m:  sub NVOICE
        call bgm_start
dm_6:   ld a,80h
        call dm_vals
        ld a,0C0h
        call dm_vals
        jp dm_lp
dm_go:  ld a,(v_dfloor)
        ld (v_startlv),a
        ret                         ; (back to the caller of title: new game)

dm_page:
        push af
        call im_clear
        pop af
        ld (v_tgt_h),a
        ld a,10
        call set_color
        ld hl,s_dbg
        ld de,(11 << 8) | (VY0+8)
        call draw_text
        ld a,15
        call set_color
        ld hl,s_dbg1
        ld de,(6 << 8) | (VY0+28)
        call draw_text
        ld hl,s_dbg2
        ld de,(6 << 8) | (VY0+40)
        call draw_text
        ld hl,s_dbg3
        ld de,(6 << 8) | (VY0+52)
        call draw_text
        ld hl,s_dbg4
        ld de,(6 << 8) | (VY0+64)
        call draw_text
        ld hl,s_dbg7
        ld de,(6 << 8) | (VY0+76)
        call draw_text
        ld a,7
        call set_color
        ld hl,s_dbg5
        ld de,(1 << 8) | (VY0+90)
        call draw_text
        ld hl,s_dbg6
        ld de,(2 << 8) | (VY0+100)
        call draw_text
        ld a,(v_tgt_h)
; the values and the cursor, on page A
dm_vals:
        ld (v_tgt_h),a
        ld b,0
dv_c:   push bc                     ; cursor column
        ld a,(v_dsel)
        cp b
        ld a,14
        ld hl,s_mark
        jr z,dv_c1
        ld hl,s_nomark
dv_c1:  push hl
        call set_color
        pop hl
        pop bc
        push bc
        ld a,b
        add a,a
        add a,b
        add a,a
        add a,a                     ; 12 rows apart
        add a,VY0+28
        ld e,a
        ld d,4
        call draw_text
        pop bc
        inc b
        ld a,b
        cp 5
        jr nz,dv_c
        ld a,15
        call set_color
        ld a,(v_dfloor)
        inc a
        ld de,(18 << 8) | (VY0+28)
        call draw_num2
        ld a,(v_dsnd)
        inc a
        ld de,(18 << 8) | (VY0+40)
        call draw_num2
        ld a,(v_dsnd)               ; its name (10 characters)
        ld l,a
        ld h,0
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl
        add hl,de
        add hl,hl
        add hl,de                   ; * 11
        ld de,s_snd
        add hl,de
        ld de,(21 << 8) | (VY0+40)
        call draw_text
        ld hl,s_off
        ld a,(v_god)
        or a
        jr z,dv_g
        ld hl,s_on
dv_g:   ld de,(18 << 8) | (VY0+52)
        jp draw_text

s_dbg:   defb "DEBUG MODE",0
s_dbg1:  defb "FLOOR",0
s_dbg2:  defb "SOUND",0
s_dbg3:  defb "INVINCIBLE",0
s_dbg4:  defb "START",0
s_dbg7:  defb "EXIT",0
s_dbg5:  defb "UP DOWN SELECT  LEFT RIGHT SET",0
s_dbg6:  defb "SPACE  PLAY / START / EXIT",0
s_on:    defb "ON ",0
s_off:   defb "OFF",0
s_mark:  defb ">",0
s_nomark: defb " ",0
s_debug: defb "DEBUG",0
s_debugi: defb "INV  ",0
s_snd:   defb "SHOT      ",0
         defb "HURT      ",0
         defb "PICKUP    ",0
         defb "KEY       ",0
         defb "DOOR      ",0
         defb "EMPTY     ",0
         defb "SWING     ",0
         defb "HUSK HIT  ",0
         defb "HUSK DIE  ",0
         defb "HUSK CLAW ",0
         defb "ORB HIT   ",0
         defb "ORB DIE   ",0
         defb "ORB SHOT  ",0
         defb "BRUTE HIT ",0
         defb "BRUTE DIE ",0
         defb "STALK HIT ",0
         defb "STALK DIE ",0
         defb "WARDN HIT ",0
         defb "WARDN DIE ",0
         defb "BLOAT HIT ",0
         defb "BLOAT POP ",0
         defb "BLOAT SWEL",0
         defb "TURRET HIT",0
         defb "TURRET SHT",0
         defb "TURRET DIE",0
         defb "BAT SQUEAK",0
         defb "BAT DIE   ",0
         defb "MUSIC 1   ",0
         defb "MUSIC 2   ",0
         defb "MUSIC 3   ",0
         defb "MUSIC 4   ",0
         defb "MUSIC 5   ",0

#ifdef VTEST
; (the voice test build has no room for these: stand-ins)
pw_make:
ending: ret
pw_entry:
        or 1
        ret
#else
; ----------------------------------------------------------------------------
;  passwords: 5 characters for the next floor, health, rounds, difficulty.
;  24 bits: checksum (6) | difficulty (2) | floor (4) | rounds (7) |
;  health / 4 (5), scrambled, 5 bits a character from the low end
; ----------------------------------------------------------------------------
PW_K0   equ 0A3h
PW_K1   equ 0C5h
PW_K2   equ 09h
pw_make:
        ld a,(v_level)
        inc a
        ld d,a                      ; the next floor (1..NLEVEL-1)
        ld a,(v_hp)
        add a,3
        srl a
        srl a
        ld e,a                      ; health / 4, rounded up (1..25)
        ld a,(v_ammo)
        ld c,a
        ld a,(v_diff)
        ld h,a
        call pw_sum
        add a,a
        add a,a
        or h
        ld b,a                      ; checksum << 2 | difficulty
        ld h,0
        ld l,c
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,l
        or e
        ld l,a
        ld a,d
        rlca
        rlca
        rlca
        rlca
        or h
        ld h,a
        ld e,b
        ld a,l
        xor PW_K0
        ld l,a
        ld a,h
        xor PW_K1
        ld h,a
        ld a,e
        xor PW_K2
        ld e,a
        ld ix,v_pwtext
        ld b,5
pm_1:   ld a,l
        and 31
        push hl
        ld hl,pw_abc
        add a,l
        ld l,a
        jr nc,pm_2
        inc h
pm_2:   ld a,(hl)
        pop hl
        ld (ix+0),a
        inc ix
        ld c,5
pm_3:   srl e
        rr h
        rr l
        dec c
        jr nz,pm_3
        djnz pm_1
        ld (ix+0),0
        ret
; D floor, C rounds, E health/4, H difficulty -> A checksum (6 bits)
pw_sum: ld a,d
        add a,c
        add a,e
        add a,d
        add a,h
        add a,h
        add a,h
        add a,7
        and 63
        ret

; v_pwtext (5 characters) -> Z and v_startlv, v_pwhp, v_pwammo, v_diff, v_pw
; if right
pw_check:
        ld hl,0
        ld e,l
        ld ix,v_pwtext+4
        ld b,5
pc_1:   ld c,5                      ; make room for 5 more bits
pc_2:   add hl,hl
        rl e
        dec c
        jr nz,pc_2
        ld a,(ix+0)
        push hl
        call pw_idx
        pop hl
        ret nz                      ; not one of the 32 characters
        or l
        ld l,a
        dec ix
        djnz pc_1
        ld a,l
        xor PW_K0
        ld l,a
        ld a,h
        xor PW_K1
        ld h,a
        ld a,e
        xor PW_K2
        ld b,a                      ; checksum << 2 | difficulty
        ld a,l
        and 31
        ld e,a                      ; health / 4
        ld a,h
        rrca
        rrca
        rrca
        rrca
        and 15
        ld d,a                      ; floor
        add hl,hl
        add hl,hl
        add hl,hl
        ld c,h
        res 7,c                     ; rounds
        ld a,b
        and 3
        cp 3
        jr z,pc_bad
        ld h,a                      ; difficulty
        call pw_sum
        ld l,a
        ld a,b
        rrca
        rrca
        and 63
        cp l
        ret nz
        ld a,d                      ; floor 1..NLEVEL-1 (from the 2nd on)
        dec a
        cp NLEVEL-1
        jr nc,pc_bad
        ld a,c
        cp 100
        jr nc,pc_bad
        ld a,e
        dec a
        cp 25
        jr nc,pc_bad
        ld a,d
        ld (v_startlv),a
        ld a,b
        and 3
        ld (v_diff),a
        ld a,c
        ld (v_pwammo),a
        ld a,e
        add a,a
        add a,a
        ld (v_pwhp),a
        ld a,1
        ld (v_pw),a
        xor a                       ; Z: right
        ret
pc_bad: or 1                        ; NZ: wrong
        ret

; A = a character -> Z and A = its number (0..31), NZ if not one of them
pw_idx: ld hl,pw_abc
        ld c,0
pwi_1:   cp (hl)
        jr z,pwi_2
        inc hl
        inc c
        bit 5,c
        jr z,pwi_1
        or 1                        ; (NZ)
        ret
pwi_2:   ld a,c
        cp a                        ; (Z)
        ret
pw_abc: defb "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

; type 5 characters on the title (shown as they come) -> Z if right
pw_entry:
        xor a
        ld (v_lastkey),a
        ld (v_pwn),a
        ld hl,v_pwtext
        ld b,5
pe_0:   ld (hl),'-'
        inc hl
        djnz pe_0
        ld (hl),0
pe_lp:  call pe_show
pe_k:   call read_input
        ld a,(v_lastkey)
        or a
        jr z,pe_k
        ld b,a
        xor a
        ld (v_lastkey),a
        ld a,b
        cp 'a'
        jr c,pe_1
        and 0DFh                    ; (either case)
pe_1:   push af
        call pw_idx
        pop bc
        jr nz,pe_k                  ; not a password character
        ld a,(v_pwn)
        ld e,a
        ld d,0
        ld hl,v_pwtext
        add hl,de
        ld (hl),b
        inc a
        ld (v_pwn),a
        cp 5
        jr nz,pe_lp
        call pe_show
        jp pw_check
pe_show:
        ld a,80h
        call pe_s1
        ld a,0C0h
pe_s1:  ld (v_tgt_h),a
        ld a,14
        call set_color
        ld hl,s_pwl
        ld de,(8 << 8) | (VY0+70)
        call draw_text
        ld hl,v_pwtext
        ld de,(17 << 8) | (VY0+70)
        jp draw_text

; ----------------------------------------------------------------------------
;  the ending: dawn breaks over the citadel, a few words, then the tally
; ----------------------------------------------------------------------------
ending:
        xor a                       ; the view in the first colour group
        ld (v_grp),a                ; (black, purple, orange, pink)
        ld (v_eskip),a
        ld a,80h
        call view_reset
        ld a,0C0h
        call view_reset
        ld hl,dawn_bands            ; the sky lights up from the horizon
en_b:   ld a,(hl)
        cp 0FFh
        jr z,en_s
        inc hl
        ld c,(hl)                   ; rows
        inc hl
        ld e,(hl)                   ; even rows' pattern
        inc hl
        ld d,(hl)                   ; odd rows'
        inc hl
        push hl
en_r:   push af
        push bc
        push de
        call en_row
        pop de
        pop bc
        pop af
        inc a
        dec c
        jr nz,en_r
        ld a,25
        call wait_n
        pop hl
        jr en_b
en_s:   ld hl,sun_w                 ; the sun on the horizon
        ld a,68
en_s1:  ld c,(hl)                   ; half its width (bytes) on this row
        inc hl
        push hl
        push af
        ld a,16
        sub c
        ld b,a                      ; first column
        sla c                       ; width
        pop af
        push af
        call en_seg
        pop af
        pop hl
        inc a
        cp 80
        jr c,en_s1
        ld a,40
        call wait_n
        ld hl,s_dawn                ; the words, a letter at a time
        ld e,VY0+84
en_t1:  ld a,(hl)                   ; (column; FFh: the end)
        cp 0FFh
        jr z,en_w
        ld d,a
        inc hl
en_t2:  ld a,(hl)
        inc hl
        or a
        jr z,en_t3
        ld (v_qv),a                 ; one letter
        xor a
        ld (v_qv+1),a
        push hl
        push de
        ld a,80h
        call en_ch
        pop de
        push de
        ld a,0C0h
        call en_ch
        ld a,4
        call wait_n
        pop de
        pop hl
        inc d
        jr en_t2
en_t3:  ld a,e
        add a,8
        ld e,a
        ld a,30
        call wait_n
        jr en_t1
en_w:   ld a,80h                    ; PRESS SPACE (on the message line)
        call en_ps
        ld a,0C0h
        call en_ps
en_w1:  call read_input
        ld a,(v_inp)
        and I_FIRE
        jr nz,en_w1
en_w2:  call read_input
        ld a,(v_inp_new)
        and I_FIRE
        jr z,en_w2
        ret
en_ps:  ld (v_tgt_h),a
        ld hl,s_blank               ; (whatever the line said before)
        ld de,(1 << 8) | MSG_Y
        call draw_text
        ld a,7
        call set_color
        ld hl,s_space
        ld de,(1 << 8) | MSG_Y
        jp draw_text
en_ch:  ld (v_tgt_h),a
        ld a,15
        call set_color
        ld hl,v_qv
        jp draw_text
; A = view row: the whole row in pattern E (even rows) / D (odd), both pages
en_row: ld b,0
        ld c,32
        bit 0,a
        jr z,en_g
        ld e,d
        jr en_g
; A = view row, B = first column, C = columns: solid (the sun), both pages
en_seg: ld e,0FFh
en_g:   add a,VY0
        ld l,a
        ld h,0
        add hl,hl
        push de
        ld de,ROWTBL
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld l,b
        ld h,0
        add hl,de                   ; offset in a page
        pop de
        ld a,80h
        call en_g1
        ld a,0C0h
en_g1:  push hl
        add a,h
        ld h,a
        ld b,c
en_g2:  ld (hl),e
        inc hl
        djnz en_g2
        pop hl
        ret
; wait A x 16 ms (SPACE: no more waiting - the ending is skipped through)
wait_n: ld b,a
wn_1:   ld a,(v_eskip)
        or a
        ret nz
        push bc
        call read_input
        pop bc
        ld a,(v_inp_new)
        and I_FIRE
        ld (v_eskip),a
        ld a,(v_ticks)
        ld c,a
wn_2:   ld a,(v_ticks)
        sub c
        cp 8
        jr c,wn_2
        djnz wn_1
        ret

; bands of the dawn sky, from the horizon up: first row, rows, patterns
dawn_bands:
        defb 72,8,0EEh,0BBh         ; pink and orange
        defb 64,8,0AAh,0AAh         ; orange
        defb 54,10,099h,066h        ; orange and purple
        defb 42,12,055h,055h        ; purple
        defb 30,12,044h,011h        ; purple, thinning out
        defb 0FFh
sun_w:  defb 1,2,2,3,3,3,4,4,4,4,5,5
s_dawn: defb 5,"THE WARDEN HAS FALLEN.",0
        defb 5,"YOUR LANTERN BURNS OUT",0
        defb 6,"AS DAWN BREAKS OVER",0
        defb 7,"THE DARK CITADEL.",0
        defb 0FFh

#endif

; HL = seconds -> "MM:SS" at (D, E), at most 99:59
draw_time:
        push de
        ld de,60
        ld b,0
dtm_1:  or a
        sbc hl,de
        jr c,dtm_2
        inc b
        ld a,b
        cp 99
        jr c,dtm_1
        ld hl,59                    ; 99 minutes or more
        jr dtm_3
dtm_2:  add hl,de
dtm_3:  pop de
        push hl
        push de
        ld a,b
        call draw_num2
        pop de
        inc d
        inc d
        push de
        ld hl,s_colon
        call draw_text
        pop de
        inc d
        pop hl
        ld a,l
        jp draw_num2

; ----------------------------------------------------------------------------
;  shooting (hitscan at the view centre)
; ----------------------------------------------------------------------------
player_fire:
        ld a,(v_hurt)
        or a
        jr z,pf_h
        dec a
        ld (v_hurt),a
        jr nz,pf_h
        ld a,2
        ld (v_hud_dirty),a
pf_h:   ld hl,(v_oil)               ; lantern oil burning
        ld a,h
        or l
        jr z,pf_o
        dec hl
        ld (v_oil),hl
        ld a,h
        or l
        jr nz,pf_o
        ld a,LANTERN                ; burnt out
        call set_lantern
        ld a,2
        ld (v_hud_dirty),a
pf_o:   ld hl,v_flasht
        ld a,(hl)
        or a
        jr z,pf_f
        dec (hl)
pf_f:   ld a,(v_msg_t)
        or a
        jr z,pf_m
        dec a
        ld (v_msg_t),a
        jr nz,pf_m
        ld a,2
        ld (v_hud_dirty),a
pf_m:   ld a,(v_fire_cd)
        or a
        jr z,pf_0
        dec a
        ld (v_fire_cd),a
pf_0:   ld a,(v_flash)
        or a
        jr z,pf_1
        dec a
        ld (v_flash),a
pf_1:   ld a,(v_inp_new)            ; SHIFT: the other weapon
        and I_ALT
        jr z,pf_1a
        ld a,(v_weapon)
        xor 1
        ld (v_weapon),a
        ld a,4
        ld (v_fire_cd),a
        ld a,2
        ld (v_hud_dirty),a
        call snd_empty
pf_1a:  ld a,(v_inp)
        and I_FIRE
        jr nz,pf_2
        ld (v_firelock),a           ; released
        ret
pf_2:   ld a,(v_firelock)           ; the SPACE that started the floor
        or a                        ; does not fire
        ret nz
        ld a,(v_fire_cd)
        or a
        ret nz
        ld a,(v_weapon)
        or a
        jr nz,pf_axe
        ld a,(v_ammo)
        or a
        jp z,pf_empty
        dec a
        ld (v_ammo),a
        jr nz,pf_g1
        inc a                       ; the last round: the axe next
        ld (v_weapon),a
pf_g1:  ld a,5
        ld (v_fire_cd),a
        ld a,2
        ld (v_flash),a
        ld (v_hud_dirty),a
        call snd_shot
        ; nearest live enemy covering column 16 and in front of the wall there
        ld hl,(v_zbuf+32)
        jr pf_aim
pf_axe: ld a,8                      ; the axe: a slower blow, close only
        ld (v_fire_cd),a
        ld a,3
        ld (v_flash),a
        call snd_swing
        ld hl,(v_zbuf+32)
        ld de,AXE_REACH
        or a
        sbc hl,de
        add hl,de
        jr c,pf_aim
        ex de,hl
pf_aim: ld (v_s_dep),hl         ; best depth so far (wall, or the axe's reach)
        ld iy,0
        ld ix,v_enemies
        ld a,(v_nobj)
        ld b,a
pf_lp:  ld a,(ix+E_T)
        or a
        jr z,pf_nx
        call is_foe
        jr nc,pf_nx
        ld a,(ix+E_VIS)
        or a
        jr z,pf_nx
        ld a,(ix+E_ST)
        cp 3
        jr nc,pf_nx
        ld a,(ix+E_CS)
        cp 17
        jp p,pf_nx              ; cs > 16
        ld a,(ix+E_CE)
        cp 16
        jp m,pf_nx              ; ce < 16
        ld l,(ix+E_DEP)
        ld h,(ix+E_DEP+1)
        ld de,(v_s_dep)
        or a
        sbc hl,de
        jr nc,pf_nx
        add hl,de
        ld (v_s_dep),hl
        push ix
        pop iy
pf_nx:  ld de,16
        add ix,de
        djnz pf_lp
        push iy
        pop hl
        ld a,h
        or l
        ret z
        ld a,(v_weapon)             ; damage: 1 (gun), 2 (axe)
        inc a
        ld b,a
pf_dm:  dec (iy+E_HP)
        jr z,pf_kill
        djnz pf_dm
        ld (v_flashix),iy           ; it flashes for a moment
        ld a,3
        ld (v_flasht),a
        call snd_hit
        ld a,2
        ld (v_hud_dirty),a          ; (the warden's health bar)
        ld a,(iy+E_ST)          ; wake it up
        or a
        ret nz
        ld (iy+E_ST),1
        ret
pf_kill:
        ld a,(iy+E_T)
        cp T_BLOAT                  ; a bloater shot down bursts where it is
        jr nz,kill_iy
        ld (iy+E_ST),2
        ld (iy+E_TM),1
        ret
; IY = enemy: it falls (the warden: the exit opens), a kill
kill_iy:
        ld a,(iy+E_T)
        cp T_WARDEN
        call z,boss_down
        ld (iy+E_ST),3
        ld (iy+E_TM),5
        ld hl,v_kills
        inc (hl)
        ld a,2
        ld (v_hud_dirty),a
        jp snd_kill
pf_empty:
        ld a,(v_inp_new)
        and I_FIRE
        ret z
        jp snd_empty

; ----------------------------------------------------------------------------
;  enemy behaviour
; ----------------------------------------------------------------------------
update_enemies:
        ld ix,v_enemies
        ld a,(v_nobj)               ; (only the slots in use)
        ld b,a
ue_lp:  push bc
        ld a,(ix+E_T)
        or a
        call nz,enemy_one
        ld de,16
        add ix,de
        pop bc
        djnz ue_lp
        ret

enemy_one:
        inc (ix+E_AN)
        ld a,(ix+E_ST)
        cp 3
        jr c,eo_live
        ret nz                  ; dead: lies there
        dec (ix+E_TM)           ; dying
        ret nz
        ld (ix+E_ST),4
        ret
eo_live:
        ld a,(ix+E_T)
        call is_foe
        jr nc,eo_item
        ld a,(ix+E_ST)
        or a
        jr nz,eo_lv1
        bit 2,(ix+E_VIS)         ; idle until the player can see it
        jr nz,eo_wk
        ld a,(ix+E_T)            ; (a turret: until it sees the player,
        cp T_TURRET              ; within 8 cells, in the dark too)
        ret nz
        ld a,(ix+E_AN)
        and 7
        ret nz
        call to_player
        ld a,h
        cp 8
        ret nc
        call los
        ret nz
eo_wk:  ld (ix+E_ST),1
        ld a,(ix+E_T)
        cp T_TURRET
        ret nz
        ld (ix+E_TM),20          ; (the turret: its first bolt soon)
        ret
eo_lv1: call to_player
        ld a,(ix+E_ST)
        jp eo_act

; HL = rough distance from object IX to the player (v_e_dx / v_e_dy set)
to_player:
        ld hl,(v_px)
        ld e,(ix+E_X)
        ld d,(ix+E_X+1)
        or a
        sbc hl,de
        ld (v_e_dx),hl
        ld hl,(v_py)
        ld e,(ix+E_Y)
        ld d,(ix+E_Y+1)
        or a
        sbc hl,de
        ld (v_e_dy),hl
        jp rough_dist            ; HL = distance 8.8

; pickups: health, ammo, orange key, violet key
eo_item:
        ld a,(v_px+1)               ; not in or next to its cell: too far
        sub (ix+E_X+1)
        inc a
        cp 3
        ret nc
        ld a,(v_py+1)
        sub (ix+E_Y+1)
        inc a
        cp 3
        ret nc
        call to_player
        ld de,150
        or a
        sbc hl,de
        ret nc                   ; not close enough
        ld a,(ix+E_T)
        cp T_HEALTH
        jr nz,ei_a
        ld a,(v_hp)
        cp 100
        ret nc                   ; full health: leave it
        add a,25
        cp 101
        jr c,ei_h
        ld a,100
ei_h:   ld (v_hp),a
        ld hl,s_got_h
        jr ei_take
ei_a:   cp T_AMMO
        jr nz,ei_k
        ld a,(v_diff)               ; (HARD: half)
        cp 2
        ld b,12
        jr nz,ei_a0
        ld b,6
ei_a0:  ld a,(v_ammo)
        add a,b
        cp 100
        jr c,ei_a1
        ld a,99
ei_a1:  ld (v_ammo),a
        ld hl,s_got_a
        jr ei_take
ei_k:   cp T_OIL
        jr nz,ei_k0
        ld hl,OIL_TIME              ; lantern oil: a brighter lantern for a while
        ld (v_oil),hl
        ld a,LANTERN+2
        call set_lantern
        ld hl,s_got_l
        jr ei_take
ei_k0:  sub T_KEYO               ; 0 orange, 1 violet
        ld b,a
        inc b
        ld a,0
        scf
ei_k1:  rla
        djnz ei_k1
        ld hl,v_keys
        or (hl)
        ld (hl),a
        ld hl,s_got_o
        ld a,(ix+E_T)
        cp T_KEYO
        jr z,ei_take
        ld hl,s_got_v
ei_take:
        call show_msg
        ld a,(ix+E_T)
        ld (ix+E_T),0
        ld hl,v_items
        inc (hl)
        cp T_OIL
        jp z,snd_pick
        cp T_KEYO
        jp nc,snd_key
        jp snd_pick
eo_act: cp 2
        jp z,eo_attack
        ; chase
        ld a,(ix+E_T)
        cp T_ORB
        jp z,eo_orb
        cp T_WARDEN
        jp z,eo_ward
        cp T_TURRET
        jp z,eo_tur
        cp T_BLOAT
        jr nz,ea_1
        push hl                     ; the bloater: within a cell, it swells
        ld de,256
        or a
        sbc hl,de
        pop hl
        jr nc,eo_walk
        ld (ix+E_ST),2
        ld (ix+E_TM),12
        ld a,VO_BLOAT_SWELL
        jp voice_play
ea_1:   ; husk, brute, stalker, bat: walk up and strike
        push hl
        ld de,220
        or a
        sbc hl,de
        pop hl
        jr nc,eo_walk
        ld (ix+E_ST),2
        call e_par
        inc hl
        ld a,(hl)                   ; wind-up before the blow
        ld (ix+E_TM),a
        ret
eo_walk:
        call e_par
        ld c,(hl)                   ; speed
        ld a,(ix+E_T)
        cp T_BAT
        jr z,eo_bat
        cp T_STALK
        jp nz,enemy_step
        ld a,(ix+E_AN)              ; the stalker: sides in turn
        and 8
        ld b,24
        jr zigzag
; the bat: wider and quicker; every 8 frames it may switch side (3 in 4)
eo_bat: ld a,(ix+E_AN)
        and 7
        jr nz,eb_1
        call rand
        cp 192
        jr nc,eb_1
        inc (ix+E_TM)               ; (its side: bit 0)
eb_1:   ld a,(ix+E_TM)
        and 1
        ld b,36
; C = speed, B = dart, A = side (0: +): run along the main axis towards the
; player and dart along the other one - a zigzag that is hard to aim at
zigzag: push af
        push bc
        ld hl,(v_e_dx)
        call abs16
        ex de,hl
        ld hl,(v_e_dy)
        call abs16
        or a
        sbc hl,de                   ; |dy| - |dx|
        ld hl,0
        ld de,v_e_dy                ; (the dart goes along y)
        jr c,eo_s1
        ld (v_e_dx),hl              ; y is the main axis: run along y only
        ld de,v_e_dx                ; (the dart goes along x)
        jr eo_s2
eo_s1:  ld (v_e_dy),hl              ; x is the main axis: run along x only
eo_s2:  pop bc
        push bc
        push de
        call enemy_step
        pop de
        pop bc
        pop af
        ld hl,0
        ld (v_e_dx),hl
        ld (v_e_dy),hl
        ld hl,1
        or a
        jr z,eo_s3
        ld hl,-1
eo_s3:  ex de,hl
        ld (hl),e
        inc hl
        ld (hl),d
        ld c,b
        jp enemy_step

; the turret: fires every so often while it sees the player (the lens
; lights up first)
eo_tur: inc (ix+E_TM)
        ld a,(ix+E_TM)
        cp 28
        ret c
        call los
        ret nz
        ld (ix+E_ST),2
        ld (ix+E_TM),8
        ret

; A = type -> C: an enemy (1-5, 11-13), NC: an item
is_foe: cp T_ITEM
        ret c
        cp T_BLOAT
        ccf
        ret
; A = an enemy's type -> 1..8 (the tables by kind: 11-13 follow the warden)
ty_idx: cp T_BLOAT
        ret c
        sub T_BLOAT-6
        ret

; IX = enemy -> HL = its abilities: speed, wind-up, damage
e_par:  ld a,(ix+E_T)
        call ty_idx
        dec a
        ld l,a
        add a,a
        add a,l
        ld l,a
        ld h,0
        ld de,e_tbl
        add hl,de
        ret
e_tbl:  defb 18,6,8                 ; husk
        defb 12,5,5                 ; orb (keeps away and shoots)
        defb 10,9,20                ; brute: slow, slow blow, hits hard
        defb 38,3,5                 ; stalker: fast, quick, light
        defb 0,0,0                  ; (the warden: its own ways)
        defb 26,0,0                 ; bloater: rolls at you (its burst: burst)
        defb 0,0,0                  ; turret: does not move (eo_tur)
        defb 60,2,4                 ; bat: very fast, quick, light
e_hp:   defb 3,4,8,2,30,6,10,1      ; shots to bring them down

eo_orb: ; sentinel: keep some distance, shoot now and then
        inc (ix+E_TM)
        ld a,(ix+E_TM)
        cp 30
        jr c,eo_o1
        push hl                 ; shoots whenever the line to the player is clear
        call los
        pop hl
        jr nz,eo_o1
        ld (ix+E_ST),2
        ld (ix+E_TM),5
        ret
eo_o1:  ld a,h
        cp 3
        ret c                   ; closer than 3 cells: hover
        ld c,12
        jp enemy_step
; the warden: walks up slowly; strikes when close, throws a bolt from afar
eo_ward:
        ld a,(v_boss)
        cp 1
        call z,boss_wake
        push hl                     ; its music while the player is in its
        call los                    ; line of fire
        call boss_mus
        pop hl
        inc (ix+E_TM)
        ld a,(ix+E_TM)
        cp 25
        jr c,ew_1
        push hl
        call los
        pop hl
        jr nz,ew_1
        ld (ix+E_ST),2              ; a bolt (or a blow, if close by then)
        ld (ix+E_TM),6
        ret
ew_1:   push hl
        ld de,220
        or a
        sbc hl,de
        pop hl
        jr nc,ew_2
        ld (ix+E_ST),2              ; a blow
        ld (ix+E_TM),8
        ret
ew_2:   ld c,12
        jp enemy_step
ew_hit: ld (ix+E_TM),0
        ld de,320
        or a
        sbc hl,de
        jr nc,ew_bolt
        call los
        ret nz
        call snd_claw
        ld a,15
        jp hurt_player
ew_bolt:
        call los
        ret nz
        call snd_eshot
        call rand
        cp 170
        ret nc
        ld a,10
        jp hurt_player

; the warden wakes: its health bar
boss_wake:
        ld a,2
        ld (v_boss),a
        ld (v_hud_dirty),a
        ret

; Z: the player is in the warden's line of fire -> its music; out of it
; for a while (about a second) -> the floor's music again
boss_mus:
        jr nz,bm_out
        ld a,25
        ld (v_bmus_t),a
        ld a,(v_bmus)
        or a
        ret nz
        inc a
        ld (v_bmus),a
        ld a,3
        jp bgm_start
bm_out: ld a,(v_bmus)
        or a
        ret z
        ld hl,v_bmus_t
        dec (hl)
        ret nz
; the floor's music (the last floor has its own)
floor_tune:
        xor a
        ld (v_bmus),a
        ld a,(v_level)
        cp NLEVEL-1
        ld a,4
        jr z,ft_1
        ld a,(v_level)
        and 1
ft_1:   jp bgm_start

; the warden falls: the exit opens, the floor's music again
boss_down:
        xor a
        ld (v_boss),a
        call floor_tune
        ld hl,s_wfall
        jp show_msg

eo_attack:
        dec (ix+E_TM)
        ret nz
        ld (ix+E_ST),1
        ld a,(ix+E_T)
        cp T_WARDEN
        jp z,ew_hit
        cp T_ORB
        jr z,eo_shot
        cp T_BLOAT
        jp z,burst
        cp T_TURRET
        jr z,eo_tshot
        ld de,320               ; claw reaches ~1.25 cells
        or a
        sbc hl,de
        ret nc
        call los                ; not through walls or closed doors
        ret nz
        ld a,(ix+E_T)
        cp T_BAT
        jr nz,ea_c
        ld a,VO_BAT_HIT         ; (the bat's bite: a squeak)
        call voice_play
        jr ea_c2
ea_c:   call snd_claw
ea_c2:  call e_par
        inc hl
        inc hl
        ld a,(hl)               ; damage
        jp hurt_player
eo_shot:
        ld (ix+E_TM),0
        call los
        ret nz
        call snd_eshot
        call rand
        cp 120
        ret nc
        ld a,5
        jp hurt_player
eo_tshot:                       ; the turret's bolt
        ld (ix+E_TM),0
        call los
        ret nz
        ld a,VO_TUR_SHOT
        call voice_play
        call rand
        cp 150
        ret nc
        ld a,8
        jp hurt_player

; IX = a bloater bursting (HL = distance to the player): 25 to the player
; within 1.5 cells if in sight, 3 to the other enemies near it (bloaters
; among them burst soon after); then it is gone
burst:  ld de,384
        or a
        sbc hl,de
        jr nc,bu_1
        call los
        jr nz,bu_1
        ld a,25
        call hurt_player
bu_1:   ld iy,v_enemies
        ld a,(v_nobj)
        ld b,a
bu_lp:  push bc
        ld a,(iy+E_T)
        call is_foe
        jr nc,bu_nx
        ld a,(iy+E_ST)
        cp 3
        jr nc,bu_nx
        push iy                     ; (not itself)
        pop hl
        push ix
        pop de
        or a
        sbc hl,de
        jr z,bu_nx
        ld l,(iy+E_X)               ; how far from the bloater
        ld h,(iy+E_X+1)
        ld e,(ix+E_X)
        ld d,(ix+E_X+1)
        or a
        sbc hl,de
        ld (v_e_dx),hl
        ld l,(iy+E_Y)
        ld h,(iy+E_Y+1)
        ld e,(ix+E_Y)
        ld d,(ix+E_Y+1)
        or a
        sbc hl,de
        ld (v_e_dy),hl
        call rough_dist
        ld de,384
        or a
        sbc hl,de
        jr nc,bu_nx
        ld a,(iy+E_T)
        cp T_BLOAT
        jr nz,bu_d
        ld (iy+E_ST),2              ; another bloater: it bursts soon
        ld (iy+E_TM),4
        jr bu_nx
bu_d:   ld a,2
        ld (v_hud_dirty),a          ; (the warden's gauge)
        ld a,(iy+E_HP)
        sub 3
        jr c,bu_k
        jr z,bu_k
        ld (iy+E_HP),a
        ld a,(iy+E_ST)              ; (awake now)
        or a
        jr nz,bu_nx
        ld (iy+E_ST),1
        jr bu_nx
bu_k:   ld (iy+E_HP),0
        call kill_iy
bu_nx:  ld de,16
        add iy,de
        pop bc
        dec b
        jp nz,bu_lp
        push ix                     ; and the bloater itself
        pop iy
        jp kill_iy

; line of sight from enemy IX to the player: Z = clear, NZ = blocked.
; Samples 31 points along the line (v_e_dx / v_e_dy from to_player).
los:    ld hl,(v_e_dx)
        ld b,5
ls_1:   sra h
        rr l
        djnz ls_1
        ld (v_s_du),hl          ; x step = dx / 32
        ld hl,(v_e_dy)
        ld b,5
ls_2:   sra h
        rr l
        djnz ls_2
        ld (v_s_u),hl           ; y step = dy / 32
        ld l,(ix+E_X)
        ld h,(ix+E_X+1)
        ld e,(ix+E_Y)
        ld d,(ix+E_Y+1)
        ld b,31
ls_lp:  push bc
        ld bc,(v_s_du)
        add hl,bc
        ex de,hl
        ld bc,(v_s_u)
        add hl,bc
        ex de,hl
        push hl
        push de
        ld e,h                  ; x cell (D = y cell)
        call map_at
        pop de
        pop hl
        pop bc
        ret nz                  ; wall or closed door in between
        djnz ls_lp
        xor a
        ret

; HL = max(|dx|,|dy|) + min/2 of (v_e_dx, v_e_dy)
rough_dist:
        ld hl,(v_e_dx)
        call abs16
        ex de,hl
        ld hl,(v_e_dy)
        call abs16
        or a
        sbc hl,de
        jr nc,rd_1
        add hl,de               ; |dy| < |dx|: swap
        ex de,hl
        jr rd_2
rd_1:   add hl,de
rd_2:   srl d                   ; HL = max, DE = min
        rr e
        add hl,de
        ret

abs16:  bit 7,h
        ret z
        xor a
        sub l
        ld l,a
        ld a,0
        sbc a,h
        ld h,a
        ret

; move enemy IX toward the player by C (1/256 cell) per axis, with walls
enemy_step:
        ld hl,(v_e_dx)
        ld b,0
        bit 7,h
        jr nz,es_xn
        ld a,h
        or l
        jr z,es_y
        ld b,c
        jr es_x
es_xn:  ld a,c
        neg
        ld b,a
es_x:   ld a,b                  ; try x
        ld l,(ix+E_X)
        ld h,(ix+E_X+1)
        call add_s8
        push hl
        ld e,h
        ld d,(ix+E_Y+1)
        call map_at
        pop hl
        jr nz,es_y
        ld (ix+E_X),l
        ld (ix+E_X+1),h
es_y:   ld hl,(v_e_dy)
        ld b,0
        bit 7,h
        jr nz,es_yn
        ld a,h
        or l
        ret z
        ld b,c
        jr es_y2
es_yn:  ld a,c
        neg
        ld b,a
es_y2:  ld a,b
        ld l,(ix+E_Y)
        ld h,(ix+E_Y+1)
        call add_s8
        push hl
        ld d,h
        ld e,(ix+E_X+1)
        call map_at
        pop hl
        ret nz
        ld (ix+E_Y),l
        ld (ix+E_Y+1),h
        ret

; HL += signed A
add_s8: ld e,a
        rla
        sbc a,a
        ld d,a
        add hl,de
        ret

; A = damage
hurt_player:
        push af
        call hurt_side
        pop af
        ld b,a
        ld a,(v_diff)               ; NORMAL: half as much again, HARD: twice
        or a
        jr z,hp_g
        ld c,b
        dec a
        jr nz,hp_x
        srl c
hp_x:   ld a,b
        add a,c
        ld b,a
hp_g:   ld a,(v_god)
        or a
        jr z,hp_0
        ld b,0                      ; invincible (debug)
hp_0:   ld a,(v_hp)
        sub b
        jr nc,hp_1
        xor a
hp_1:   ld (v_hp),a
        ld a,2
        ld (v_hud_dirty),a
        ld a,4
        ld (v_hurt),a
        call snd_hurt
        ld a,(v_hp)
        or a
        ret nz
        ld a,1
        ld (v_dead),a
        ld hl,v_deaths
        inc (hl)
        xor a
        ld (v_dchoice),a            ; continue, unless changed
        ret

; ----------------------------------------------------------------------------
;  sprites: camera transform, then draw far to near
; ----------------------------------------------------------------------------
; HL = (DE * BC) >> 8; DE signed 16 bit, BC signed 8.8 with |BC| <= 1.0
mulc:   ld a,d
        xor b
        ld (v_e_sgn),a
        bit 7,d
        jr z,mc_1
        xor a
        sub e
        ld e,a
        ld a,0
        sbc a,d
        ld d,a
mc_1:   bit 7,b
        jr z,mc_2
        xor a
        sub c
        ld c,a
        ld a,0
        sbc a,b
        ld b,a
mc_2:   ld a,b
        or a
        jr z,mc_3
        ex de,hl                ; |coefficient| = 1.0
        jr mc_4
mc_3:   ld a,c
        call umul8_16
mc_4:   ld a,(v_e_sgn)
        bit 7,a
        ret z
        xor a
        sub l
        ld l,a
        ld a,0
        sbc a,h
        ld h,a
        ret

calc_sprites:
        ld ix,v_enemies
        ld a,(v_nobj)
        ld b,a
cs_lp:  push bc
        ld (ix+E_VIS),0
        ld a,(ix+E_T)
        or a
        call nz,calc_one
        ld de,16
        add ix,de
        pop bc
        djnz cs_lp
        ret

calc_one:
        ; relative position
        ld l,(ix+E_X)
        ld h,(ix+E_X+1)
        ld de,(v_px)
        or a
        sbc hl,de
        ld (v_e_dx),hl
        ld l,(ix+E_Y)
        ld h,(ix+E_Y+1)
        ld de,(v_py)
        or a
        sbc hl,de
        ld (v_e_dy),hl
        ; far beyond the lantern's light: nothing to work out
        call abs16
        ld a,h
cl_c2:  cp 9                        ; (patched: set_lantern)
        ret nc
        ld hl,(v_e_dx)
        call abs16
        ld a,h
cl_c1:  cp 9
        ret nc
        ; cos / sin of the view angle
        ld a,(v_pa)
        ld l,a
        ld h,0
        add hl,hl
        ld de,cos_tbl
        add hl,de
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld (v_qv),bc                ; cos
        ld de,512-1
        add hl,de                   ; (sin_tbl follows cos_tbl: 512 bytes on)
        ld c,(hl)
        inc hl
        ld b,(hl)                   ; sin
        push bc
        ld de,(v_e_dy)
        call mulc                   ; dy*s
        ld (v_s_dep),hl
        ld bc,(v_qv)
        ld de,(v_e_dx)
        call mulc                   ; dx*c
        ld de,(v_s_dep)
        add hl,de
        ld (v_s_dep),hl             ; depth = dx*c + dy*s
        pop bc                      ; (sin)
        ; behind, too close, or in the dark beyond the lantern: not seen
        bit 7,h
        ret nz
        ld de,64
        or a
        sbc hl,de
        ret c
        add hl,de
        ld a,h                      ; (the lantern's reach: patched into lt_c1)
        ld hl,lt_c1+1
        cp (hl)
        ret nc
        ; the side: lateral = dy*c - dx*s  (+ = right)
        ld de,(v_e_dx)
        call mulc                   ; dx*s
        ld (v_e_lat),hl
        ld bc,(v_qv)
        ld de,(v_e_dy)
        call mulc                   ; dy*c
        ld de,(v_e_lat)
        or a
        sbc hl,de
        ld (v_e_lat),hl
        ; inside the field of view (|lat| <= 1.25 depth)
        ld hl,(v_e_lat)
        call abs16
        push hl                 ; |lat|
        ld hl,(v_s_dep)
        ld d,h
        ld e,l
        srl d
        rr e
        srl d
        rr e
        add hl,de
        pop de
        or a
        sbc hl,de
        ret c
        ; column offset = |lat|/depth * 27.7 ; reduce to depth < 512 first
        ld hl,(v_s_dep)
co_sh:  ld a,h
        cp 2
        jr c,co_ok
        srl h
        rr l
        srl d
        rr e
        jr co_sh
co_ok:  push hl                 ; reduced depth
        ex de,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; |lat| * 64
        pop de
        call div16              ; HL = |lat|*64/depth (0..80)
        ld a,l
        ld e,111
        call mulq               ; offset = H
        ld a,(v_e_lat+1)
        bit 7,a
        ld a,h
        jr z,co_r
        neg
co_r:   add a,16
        ld (v_s_col),a          ; centre column (signed)
        ; size: 3/4 of the wall height at this depth, bottom on the floor line
        ld hl,(v_s_dep)
        ld a,h
        cp 2
        jr nc,co_far
        ld a,l                  ; nearer than 2 cells: own tables, can
        srl h                   ; exceed the view (clipped when drawn)
        rra
        srl h
        rra
        ld e,a
        ld d,0
        ld hl,spr_hs
        add hl,de
        ld a,(hl)
        ld (ix+E_HS),a
        ld de,128
        add hl,de
        ld a,(hl)
        ld (ix+E_TOP),a
        ld a,(ix+E_HS)
        jr co_sz
co_far: call ht_lookup          ; A = rows
        ld c,a
        srl a
        srl a
        ld b,a
        ld a,c
        sub b                   ; 3/4
        cp 3
        ret c                   ; too far to matter
        ld (ix+E_HS),a
        ld a,c
        add a,VH
        srl a
        sub (ix+E_HS)
        ld (ix+E_TOP),a
        ld a,(ix+E_HS)
co_sz:  ld c,a
        ld a,(ix+E_T)
        cp T_WARDEN
        ld a,c
        jr nz,co_sz2
        srl a                       ; the warden: half as tall again, growing
        ld b,a                      ; upwards (not far above the view's top)
        ld a,(ix+E_TOP)
        add a,30
        cp b
        jr nc,co_g1
        ld b,a
co_g1:  ld a,c
        add a,b
        jr c,co_g2
        cp 252
        jr c,co_g3
co_g2:  ld a,251
co_g3:  ld (ix+E_HS),a
        ld d,a
        sub c                       ; how much it grew
        ld b,a
        ld a,(ix+E_TOP)
        sub b
        ld (ix+E_TOP),a
        ld a,d
co_sz2: add a,4
        rrca
        rrca
        rrca
        and 1Fh
        jr nz,co_w
        inc a
co_w:   ld c,a                  ; width in columns
        srl a
        ld b,a
        ld a,(v_s_col)
        sub b
        ld (ix+E_CS),a
        add a,c
        dec a
        ld (ix+E_CE),a
        bit 7,a
        ret nz                  ; entirely left of the view
        ld a,(ix+E_CS)
        cp 32
        jp p,co_off             ; entirely right
        ld hl,(v_s_dep)
        ld (ix+E_DEP),l
        ld (ix+E_DEP+1),h
        ld (ix+E_VIS),1
        ret
co_off: ret

; HL = perpendicular distance 8.8 -> A = wall rows (tables)
ht_lookup:
        ld a,h
        cp 8
        jr nc,hl_far
        ld a,l
        srl h
        rra
        srl h
        rra
        srl h
        rra
        ld e,a
        ld d,0
        ld hl,ht_near
        add hl,de
        ld a,(hl)
        ret
hl_far: add a,a
        add a,a
        ld e,a
        ld a,l
        rlca
        rlca
        and 3
        or e
        cp 128
        jr c,hl_f1
        ld a,127
hl_f1:  ld e,a
        ld d,0
        ld hl,ht_far
        add hl,de
        ld a,(hl)
        ret

draw_sprites:
ds_next:
        ; farthest visible enemy not yet drawn
        ld iy,0
        ld hl,0
        ld ix,v_enemies
        ld a,(v_nobj)
        ld b,a
ds_f:   ld a,(ix+E_VIS)
        cp 1
        jr nz,ds_fn
        ld e,(ix+E_DEP)
        ld d,(ix+E_DEP+1)
        push hl
        or a
        sbc hl,de
        pop hl
        jr nc,ds_fn
        ex de,hl
        push ix
        pop iy
ds_fn:  ld de,16
        add ix,de
        djnz ds_f
        push iy
        pop hl
        ld a,h
        or l
        ret z
        push iy
        pop ix
        ld (ix+E_VIS),2
        call draw_one
        jr ds_next

draw_one:
        ; texture: type, frame
        ld a,(ix+E_ST)
        ld c,3
        cp 3
        jr nc,do_t
        ld c,2
        cp 2
        jr z,do_t
        ld a,(ix+E_AN)
        rrca
        and 1
        ld c,a
do_t:   ld a,(ix+E_T)
        dec a
        add a,a
        add a,a
        add a,c
        add a,a
        ld e,a
        ld d,0
        ld hl,tex_tbl
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld de,pat4                  ; colours as they are
        bit 7,h
        jr z,do_m1
        res 7,h                     ; a glowing item: 1, 2 -> 3
        ld de,map_glow
do_m1:  ld (v_s_ptr),hl
        ld a,(v_flasht)             ; the enemy just hit: all bright
        or a
        jr z,do_m2
        ld hl,(v_flashix)
        push ix
        pop bc
        or a
        sbc hl,bc
        jr nz,do_m2
        ld de,map_flash
do_m2:  ld (v_smap),de
        ; row runs for 12 texel rows (Bresenham over the height)
        ld a,(ix+E_HS)
        ld d,a
        ld hl,v_s_runs
        ld b,12
        ld e,0                  ; error
do_r1:  ld c,0
        ld a,e
        add a,d
do_r2:  cp 12
        jr c,do_r3
        sub 12
        inc c
        jr do_r2
do_r3:  ld e,a
        ld (hl),c
        inc hl
        djnz do_r1
        ; texel column step 8.8 = 2048 / width
        ld a,(ix+E_CE)
        sub (ix+E_CS)
        inc a
        ld (v_s_ws),a
        ld e,a
        ld d,0
        ld hl,2048
        call div16
        ld (v_s_du),hl
        srl h
        rr l
        ld (v_s_u),hl
        ; columns
        ld a,(ix+E_CS)
        ld (v_s_col),a
        ld a,(v_s_ws)
        ld b,a
do_c:   push bc
        ld a,(v_s_col)
        bit 7,a
        jr nz,do_cn
        cp 32
        jr nc,do_cn
        ; behind a wall?
        add a,a
        ld l,a
        ld h,0
        ld de,v_zbuf
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld l,(ix+E_DEP)
        ld h,(ix+E_DEP+1)
        or a
        sbc hl,de
        jr nc,do_cn
        set 2,(ix+E_VIS)
        call sprite_col
do_cn:  ld hl,(v_s_u)
        ld de,(v_s_du)
        add hl,de
        ld (v_s_u),hl
        ld hl,v_s_col
        inc (hl)
        pop bc
        djnz do_c
        ret

; draw texel column (v_s_u >> 8) of the sprite at screen column v_s_col
sprite_col:
        ld a,(v_s_col)
        call mark_dirty
        ld a,(v_back_h)
        ld h,a
        ld l,0
        ld de,VY0*40
        add hl,de
        ld a,(v_s_col)
        ld e,a
        ld d,0
        add hl,de
        ld (v_vaddr),hl
        ld a,(v_s_u+1)
        and 7
        ld e,a
        ld d,0
        ld hl,(v_s_ptr)
        add hl,de
        ld (v_t_dst),hl         ; texel pointer (steps by 8)
        ld a,(ix+E_TOP)         ; top row, may be above the view (negative)
        add a,32
        ld (v_s_top),a          ; current row + 32
        ld hl,v_s_runs
        ld b,12
sc_lp:  push bc
        push hl
        ld a,(v_s_top)
        cp VH+32
        jr nc,sc_end            ; the rest is below the view
        ld c,(hl)               ; run
        ld a,c
        or a
        jr z,sc_nx
        ld hl,(v_t_dst)
        ld a,(hl)
        cp 0FFh
        jr z,sc_nx
        and 3
        ld e,a
        ld d,0
        ld hl,(v_smap)              ; (pat4, map_glow or map_flash)
        add hl,de
        ld a,(hl)
        ld (v_s_skip),a
        ld a,(v_s_top)
        sub 32                  ; row
        jr nc,sc_c1
        add a,c                 ; starts above the view: rows left
        jr nc,sc_nx
        jr z,sc_nx
        ld c,a
        xor a
        jr sc_c2
sc_c1:  ld b,a                  ; ends below the view: shorten
        ld a,VH
        sub b
        cp c
        jr nc,sc_c3
        ld c,a
sc_c3:  ld a,b
sc_c2:  call row_addr
        ld a,(v_s_skip)
        ld b,a
        ld a,c
        ld c,b
        call fill_seg
sc_nx:  pop hl
        ld a,(v_s_top)
        add a,(hl)
        ld (v_s_top),a
        inc hl
        push hl
        ld hl,(v_t_dst)
        ld de,8
        add hl,de
        ld (v_t_dst),hl
        pop hl
        pop bc
        djnz sc_lp
        ret
sc_end: pop hl
        pop bc
        ret

map_glow:  defb 00h,0FFh,0FFh,0FFh
map_flash: defb 0FFh,0FFh,0FFh,0FFh

; A = column: force a full repaint of its ceiling / floor next time (this page)
mark_dirty:
        ld e,a
        ld d,0
        ld a,(v_back_h)
        cp 80h
        ld hl,v_ptop0
        jr z,md_1
        ld hl,v_ptop1
md_1:   add hl,de
        ld (hl),0
        ld de,NCOL
        add hl,de
        ld (hl),VH
        add hl,de
        ld (hl),1                   ; cdirty: drawn again next time
        add hl,de
        ld (hl),0                   ; pshd: the wall too
        ret

; ----------------------------------------------------------------------------
;  where a blow / a bolt came from (enemy IX; v_e_dx, v_e_dy = player - it):
;  1 ahead, 2 right, 3 behind, 4 left, shown at that edge of the view
; ----------------------------------------------------------------------------
hurt_side:
        ld a,(v_pa)
        ld l,a
        ld h,0
        add hl,hl
        push hl
        ld de,cos_tbl
        add hl,de
        ld c,(hl)
        inc hl
        ld b,(hl)                   ; BC = cos
        pop hl
        ld de,sin_tbl
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        push de                     ; sin
        push bc                     ; cos
        ld de,(v_e_dx)
        call mulc                   ; dx cos
        ex de,hl
        pop bc
        push bc
        push de
        ld de,(v_e_dy)
        call mulc                   ; dy cos
        ld (v_s_u),hl
        pop de
        pop bc                      ; (cos, no longer needed)
        pop bc                      ; sin
        push de
        push bc
        ld de,(v_e_dy)
        call mulc                   ; dy sin
        pop bc
        pop de
        add hl,de                   ; ahead of the player: -(dx cos + dy sin)
        call neg_hl
        push hl
        ld de,(v_e_dx)
        call mulc                   ; dx sin
        ld de,(v_s_u)
        or a
        sbc hl,de                   ; to the right: dx sin - dy cos
        pop de                      ; DE = ahead, HL = right
        push hl
        push de
        call abs16
        ex de,hl
        call abs16                  ; HL = |ahead|, DE = |right|
        or a
        sbc hl,de
        pop de
        pop hl
        jr c,hs_lr
        ld a,1                      ; ahead or behind
        bit 7,d
        jr z,hs_s
        ld a,3
        jr hs_s
hs_lr:  ld a,2                      ; right or left
        bit 7,h
        jr z,hs_s
        ld a,4
hs_s:   ld (v_hdir),a
        ld a,4
        ld (v_hdirt),a
        ret

neg_hl: xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ret

; the mark at that edge: bright bars (the view's colour 3), repainted later
draw_hurtdir:
        ld a,(v_hdirt)
        or a
        ret z
        dec a
        ld (v_hdirt),a
        ld a,(v_hdir)
        cp 2
        ld c,31                     ; right: the last column
        jr z,hd_col
        cp 4
        ld c,0                      ; left: the first
        jr z,hd_col
        cp 1
        ld a,VY0                    ; ahead: along the top
        jr z,hd_row
        ld a,VY0+VH-4               ; behind: along the bottom
hd_row: ld c,8
hd_r1:  push af
        push bc
        ld a,c
        call mark_dirty
        pop bc
        pop af
        push af
        call hd_at                  ; HL = row A, column C
        ld b,4
hd_r2:  ld (hl),0FFh
        ld de,40
        add hl,de
        djnz hd_r2
        pop af
        inc c                       ; columns 8..23
        ld b,a
        ld a,c
        cp 24
        ld a,b
        jr c,hd_r1
        ret
hd_col: push bc
        ld a,c
        call mark_dirty
        pop bc
        ld a,VY0+24
        call hd_at
        ld b,64
hd_c1:  ld (hl),0FFh
        ld de,40
        add hl,de
        djnz hd_c1
        ret
; A = screen row, C = view column -> HL = its byte on the back page
hd_at:  ld l,a
        ld h,0
        add hl,hl
        ld de,ROWTBL
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(v_back_h)
        add a,d
        ld d,a
        ld h,0
        ld l,c
        add hl,de
        ret

; ----------------------------------------------------------------------------
;  pause (STOP): the clock stops, the music too; STOP again goes on
; ----------------------------------------------------------------------------
pause:
        xor a
        ld (v_timing),a
        inc a
        ld (v_paused),a
        ld a,80h
        call pz_msg
        ld a,0C0h
        call pz_msg
pz_w:   call read_input
        ld a,(v_inp_new)
        and 40h
        jr z,pz_w
        xor a
        ld (v_paused),a
        inc a
        ld (v_timing),a
        ld a,2
        ld (v_hud_dirty),a
        ret
pz_msg: ld (v_tgt_h),a
        ld a,15
        call set_color
        ld hl,s_paused
        ld de,(1 << 8) | MSG_Y
        jp draw_text

; ----------------------------------------------------------------------------
;  weapon at the bottom centre of the view (bytes 14..17 = 16 pixels, last 24 rows)
; ----------------------------------------------------------------------------
; the picture in hand -> HL
wp_img: ld hl,tex_gun
        ld a,(v_weapon)
        or a
        jr z,wi_1
        ld hl,tex_axe
wi_1:   ld a,(v_flash)
        or a
        ret z
        ld de,tex_gunf-tex_gun      ; the shot / the swing
        add hl,de
        ret

; before the view is drawn: if this page shows another picture than the one
; to draw now, its columns are repainted in full (the old one goes away);
; otherwise the view under it stays as it was and the picture goes on again
wp_check:
        call wp_img
        ld a,(v_back_h)
        cp 80h
        ld de,v_wimg0
        jr z,wc_1
        ld de,v_wimg1
wc_1:   ld a,(de)
        cp l
        jr nz,wc_2
        inc de
        ld a,(de)
        cp h
        ret z
        dec de
wc_2:   ld a,l
        ld (de),a
        inc de
        ld a,h
        ld (de),a
        ld a,14
        call mark_dirty
        ld a,15
        call mark_dirty
        ld a,16
        call mark_dirty
        ld a,17
        jp mark_dirty

draw_weapon:
        call wp_img
        ld a,(v_flash)              ; rows clear at the top: 6, or 2 while
        or a                        ; firing / swinging
        ld c,6
        jr z,dw_0
        ld c,2
dw_0:   ld a,c
        add a,a
        add a,a
        add a,a                     ; (8 bytes a row)
        ld e,a
        ld d,0
        add hl,de
dw_1:   ex de,hl                ; DE = (mask, plane0) pairs
        ld a,(v_back_h)
        ld h,a
        ld l,0
        ld a,c
        add a,VY0+VH-24
        push de
        ld e,a
        ld d,0
        push hl
        ld h,d
        ld l,e
        add hl,hl
        add hl,hl
        add hl,de                   ; * 5
        add hl,hl
        add hl,hl
        add hl,hl                   ; * 40
        ex de,hl
        pop hl
        add hl,de
        ld de,14
        add hl,de
        pop de
        ld a,24
        sub c
        ld b,a
        ld c,40-3
dw_r:
        ld a,(de)               ; mask: 1 = keep the view behind
        inc de
        and (hl)
        ex de,hl
        or (hl)
        ex de,hl
        ld (hl),a
        inc de
        inc hl
        ld a,(de)
        inc de
        and (hl)
        ex de,hl
        or (hl)
        ex de,hl
        ld (hl),a
        inc de
        inc hl
        ld a,(de)
        inc de
        and (hl)
        ex de,hl
        or (hl)
        ex de,hl
        ld (hl),a
        inc de
        inc hl
        ld a,(de)
        inc de
        and (hl)
        ex de,hl
        or (hl)
        ex de,hl
        ld (hl),a
        inc de
        ld a,b
        ld b,0
        add hl,bc               ; the next row
        ld b,a
        djnz dw_r
        ret

; ----------------------------------------------------------------------------
;  status area
; ----------------------------------------------------------------------------
; the lines under the view (the map panel takes the right from MM_Y down,
; so the lines from there on stay left of column 30)
STATUS_Y equ VY0+VH+6           ; HEALTH  AMMO  KILLS
L2_Y     equ STATUS_Y+10        ; WEAPON  KEY
MSG_Y    equ STATUS_Y+20        ; messages (at most 28 characters)
L4_Y     equ 166                ; DARK CITADEL  FLOOR nn  (DEBUG)
L5_Y     equ 180                ; SPC:FIRE  SHIFT:WEAPON

draw_status:
        ld a,(v_hud_dirty)
        or a
        ret z
        dec a
        ld (v_hud_dirty),a
        ld a,(v_back_h)
        ld (v_tgt_h),a
        ; HEALTH 100  AMMO 99  KILLS 00/00
        ld a,14
        call set_color
        ld hl,s_hp
        ld de,(1 << 8) | STATUS_Y
        call draw_text
        ld hl,s_ammo
        ld de,(13 << 8) | STATUS_Y
        call draw_text
        ld hl,s_kills
        ld de,(22 << 8) | STATUS_Y
        call draw_text
        ld a,(v_hurt)
        or a
        ld a,15
        jr z,ds_hp
        ld a,10                 ; red while being hurt
ds_hp:  call set_color
        ld a,(v_hp)
        ld de,(8 << 8) | STATUS_Y
        call draw_num3
        ld a,15
        call set_color
        ld a,(v_ammo)
        ld de,(18 << 8) | STATUS_Y
        call draw_num2
        ld a,(v_kills)
        ld de,(28 << 8) | STATUS_Y
        call draw_num2
        ld a,(v_nenemy)
        ld de,(31 << 8) | STATUS_Y
        call draw_num2
        ; WEAPON GUN  KEY O V
        ld a,14
        call set_color
        ld hl,s_weapon
        ld de,(1 << 8) | L2_Y
        call draw_text
        ld hl,s_key
        ld de,(13 << 8) | L2_Y
        call draw_text
        ld a,15
        call set_color
        ld hl,s_wgun
        ld a,(v_weapon)
        or a
        jr z,st_w1
        ld hl,s_waxe
st_w1:  ld de,(8 << 8) | L2_Y
        call draw_text
        ld a,2                      ; the keys held: an orange O, a violet V
        call set_color
        ld hl,s_ko
        ld a,(v_keys)
        bit 0,a
        jr nz,st_k1
        ld hl,s_kn
st_k1:  ld de,(17 << 8) | L2_Y
        call draw_text
        ld a,11
        call set_color
        ld hl,s_kv
        ld a,(v_keys)
        bit 1,a
        jr nz,st_k2
        ld hl,s_kn
st_k2:  ld de,(19 << 8) | L2_Y
        call draw_text
        ld a,14                     ; OIL while the lantern burns brighter
        call set_color
        ld hl,(v_oil)
        ld a,h
        or l
        ld hl,s_oil
        jr nz,st_o1
        ld hl,s_nooil
st_o1:  ld de,(23 << 8) | L2_Y
        call draw_text
        ; FLOOR nn (after the fixed "DARK CITADEL"), DEBUG / INV
        ld a,14
        call set_color
        ld hl,s_floorl
        ld de,(15 << 8) | L4_Y
        call draw_text
        ld a,15
        call set_color
        ld a,(v_level)
        inc a
        ld de,(21 << 8) | L4_Y
        call draw_num2
        ld a,10
        call set_color
        ld hl,s_nodebug
        ld a,(v_debug)
        or a
        jr nz,st_d0
        call diff_name              ; the difficulty
        jr st_d1
st_d0:  ld a,(v_debug)
        ld hl,s_debug
        ld a,(v_god)
        or a
        jr z,st_d1
        ld hl,s_debugi
st_d1:  ld de,(24 << 8) | L4_Y
        call draw_text
        ; message line: slain > timed message > the warden > all clear
        ld a,10
        call set_color
        ld hl,s_blank
        ld a,(v_dead)
        or a
        jr z,st_m0
        ld hl,s_dead
        ld de,(1 << 8) | MSG_Y
        call draw_text
        jp dead_opts
st_m0:  ld a,(v_msg_t)
        or a
        jr z,st_m1
        ld a,15
        call set_color
        ld hl,(v_msg)
        jr st_m2
st_m1:  ld a,(v_boss)
        cp 2
        jr nz,st_m1b
        ld a,10
        call set_color
        ld hl,s_wbar
        ld de,(1 << 8) | MSG_Y
        call draw_text
        jp boss_bar
st_m1b: ld a,(v_kills)
        ld b,a
        ld a,(v_nenemy)
        cp b
        jr nz,st_m2
        ld a,13
        call set_color
        ld hl,s_clear
st_m2:  ld de,(1 << 8) | MSG_Y
        jp draw_text

; the warden's health: a gauge on the message line - a grey frame, filled
; red in proportion (80 pixels at full health)
BAR_X   equ 8
BAR_W   equ 20                      ; bytes
boss_bar:
        ld hl,(v_bossix)
        ld de,E_HP
        add hl,de
        ld l,(hl)
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,3
        call div16                  ; pixels to fill = health * 8 / 3
        ld a,l
        ld (v_qv),a
        ld de,(BAR_X << 8) | MSG_Y
        call vaddr
        call bb_full                ; top edge
        call bb_in
        call bb_in
        call bb_in
bb_full:
        push hl
        ld b,BAR_W
bf_1:   ld (hl),0FFh                ; grey: plane 0 = 3, plane 1 = 1
        set 5,h
        ld (hl),055h
        res 5,h
        inc hl
        djnz bf_1
        jr bb_next
bb_in:  push hl
        ld a,(v_qv)
        ld c,a                      ; pixels still to fill
        ld b,BAR_W
bi_1:   ld a,c
        cp 4
        jr c,bi_2
        ld a,4
bi_2:   push hl
        ld hl,bar_px
        add a,l
        ld l,a
        jr nc,bi_3
        inc h
bi_3:   ld e,(hl)
        pop hl
        ld (hl),e                   ; red (2 in both planes)
        set 5,h
        ld (hl),e
        res 5,h
        inc hl
        ld a,c
        sub 4
        jr nc,bi_4
        xor a
bi_4:   ld c,a
        djnz bi_1
        pop hl                      ; grey ends
        push hl
        set 7,(hl)                  ; (grey = 3 in plane 0, 1 in plane 1)
        set 6,(hl)
        set 5,h
        res 7,(hl)
        set 6,(hl)
        res 5,h
        ld de,BAR_W-1
        add hl,de
        set 1,(hl)
        set 0,(hl)
        set 5,h
        res 1,(hl)
        set 0,(hl)
bb_next:
        pop hl
        ld de,40
        add hl,de
        ret
bar_px: defb 000h,080h,0A0h,0A8h,0AAh   ; 0..4 red pixels from the left

; slain: the two choices on the message line, the chosen one marked
dead_opts:
        ld b,0                      ; 0 continue, 1 title
do_lp:  push bc
        ld a,(v_dchoice)
        cp b
        ld a,15
        ld hl,s_mark
        jr z,do_1
        ld a,7
        ld hl,s_nomark
do_1:   push hl
        call set_color
        pop hl
        pop bc
        push bc
        ld a,b
        or a
        ld d,8
        jr z,do_2
        ld d,19
do_2:   ld e,MSG_Y
        push de
        call draw_text
        pop de
        inc d
        pop bc
        push bc
        ld hl,s_cont
        ld a,b
        or a
        jr z,do_3
        ld hl,s_totitle
do_3:   call draw_text
        pop bc
        inc b
        ld a,b
        cp 2
        jr nz,do_lp
        ret

; A = 0..255 -> three digits at (D,E)
draw_num3:
        ld c,0
dn3_1:  cp 100
        jr c,dn3_2
        sub 100
        inc c
        jr dn3_1
dn3_2:  push af
        push de
        ld a,c
        add a,'0'
        push af
        call vaddr
        ld (v_t_dst),hl
        pop af
        call dn_g
        pop de
        inc d
        pop af
        jp draw_num2

s_hp:    defb "HEALTH",0
s_ammo:  defb "AMMO",0
s_kills: defb "KILLS   /",0
s_blank:  defb "                            ",0
s_dead:  defb "SLAIN                       ",0
s_cont:  defb "CONTINUE",0
s_wgun:  defb "GUN",0
s_paused: defb "PAUSED - STOP TO GO ON      ",0
s_oil:   defb "OIL",0
s_nooil: defb "   ",0
s_floorl: defb "FLOOR",0
s_weapon: defb "WEAPON",0
s_key:   defb "KEY",0
s_nodebug: defb "     ",0
s_waxe:  defb "AXE",0
s_barred: defb "THE WARDEN BARS THE WAY     ",0
s_wfall: defb "THE WARDEN HAS FALLEN       ",0
s_wbar:   defb "WARDEN                      ",0
s_totitle: defb "TITLE",0
s_clear:  defb "ALL CLEAR - FIND THE EXIT   ",0
s_need_o:  defb "NEED THE ORANGE KEY         ",0
s_need_v:  defb "NEED THE VIOLET KEY         ",0
s_got_h:  defb "HEALTH +25                  ",0
s_got_a:  defb "AMMO +12                    ",0
s_got_o:  defb "ORANGE KEY                  ",0
s_got_l:  defb "LANTERN OIL                 ",0
s_got_v:  defb "VIOLET KEY                  ",0
s_ko:    defb "O",0
s_kv:    defb "V",0
s_kn:    defb " ",0
s_floor: defb "FLOOR    CLEARED",0
s_itemsl: defb "ITEMS   /",0
s_space: defb "PRESS SPACE",0
s_timel: defb "TIME",0
s_colon: defb ":",0
s_tot1:  defb "TOTAL TIME",0
s_tot2:  defb "KILLS",0
s_tot3:  defb "DEATHS",0
s_record: defb "NEW RECORD",0
s_best:  defb "BEST TIME",0
s_end1:  defb "THE CITADEL HAS FALLEN",0
s_end2:  defb "THANK YOU FOR PLAYING",0

; ----------------------------------------------------------------------------
;  sound effects: three independent PSG channels
;    A = the player's own actions, B = getting hurt, C = enemies
;  Each effect is a list of 16 ms steps: period low, period high (bit 7 =
;  noise on, bit 6 = tone off), noise period (0 = keep), volume; volume FFh
;  ends it.  The first step plays at once, the rest from the timer interrupt.
; ----------------------------------------------------------------------------
SFX_SHOT equ 0
SFX_HURT equ 1
SFX_PICK equ 2
SFX_KEY equ 3
SFX_DOOR equ 4
SFX_EMPTY equ 5
SFX_SWING equ 6
NSFX      equ 7

; enemies speak through the speech chip (tools/voices.py)
VO_HUSK_HIT  equ 0
VO_HUSK_DIE  equ 1
VO_HUSK_CLAW equ 2
VO_ORB_HIT   equ 3
VO_ORB_DIE   equ 4
VO_ORB_SHOT  equ 5
VO_BRUTE_HIT equ 6
VO_BRUTE_DIE equ 7
VO_STALK_HIT equ 8
VO_STALK_DIE equ 9
VO_WARD_HIT  equ 10
VO_WARD_DIE  equ 11
VO_BLOAT_HIT equ 12
VO_BLOAT_POP equ 13
VO_BLOAT_SWELL equ 14
VO_TUR_HIT   equ 15
VO_TUR_SHOT  equ 16
VO_TUR_DIE   equ 17
VO_BAT_HIT   equ 18
VO_BAT_DIE   equ 19
NVOICE       equ 20

; IY = enemy hit / killed
snd_hit:   ld hl,vo_hit-1
           jr vo_ty
snd_kill:  ld hl,vo_die-1
vo_ty:     ld a,(iy+E_T)            ; each kind has its own voice
           call ty_idx
           add a,l
           ld l,a
           jr nc,vo_t1
           inc h
vo_t1:     ld a,(hl)
           jr vo_go
snd_claw:  ld a,VO_HUSK_CLAW
           jr vo_go
snd_eshot: ld a,VO_ORB_SHOT
vo_go:     jp voice_play
vo_hit:    defb VO_HUSK_HIT,VO_ORB_HIT,VO_BRUTE_HIT,VO_STALK_HIT,VO_WARD_HIT
           defb VO_BLOAT_HIT,VO_TUR_HIT,VO_BAT_HIT
vo_die:    defb VO_HUSK_DIE,VO_ORB_DIE,VO_BRUTE_DIE,VO_STALK_DIE,VO_WARD_DIE
           defb VO_BLOAT_POP,VO_TUR_DIE,VO_BAT_DIE

snd_shot:   ld a,SFX_SHOT
           jr snd_play
snd_hurt:   ld a,SFX_HURT
           jr snd_play
snd_pick:   ld a,SFX_PICK
           jr snd_play
snd_key:    ld a,SFX_KEY
           jr snd_play
snd_door:   ld a,SFX_DOOR
           jr snd_play
snd_swing:  ld a,SFX_SWING
           jr snd_play
snd_empty:  ld a,SFX_EMPTY

; A = effect: start it on its channel and play the first step now
snd_play:
        push hl
        push de
        push bc
        ld l,a
        ld h,0
        ld e,l
        ld d,h
        add hl,hl
        add hl,de               ; 3 bytes per entry: channel, data
        ld de,sfx_tbl
        add hl,de
        ld c,(hl)               ; channel 0..2
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        di
        ld a,c
        call ch_ptr             ; HL = &channel pointer
        ld (hl),e
        inc hl
        ld (hl),d
        ld a,c
        call ch_step
        ei
        pop bc
        pop de
        pop hl
        ret

; A = channel -> HL = address of its data pointer (v_sfx_p + 2*A)
ch_ptr: add a,a
        add a,v_sfx_p & 0FFh
        ld l,a
        ld a,0
        adc a,v_sfx_p >> 8
        ld h,a
        ret

; timer interrupt, every 16 ms
sfx_tick:
        push de
        xor a
        call ch_step
        ld a,1
        call ch_step
        call bgm_tick
        pop de
        ret

; ----------------------------------------------------------------------------
;  background music on PSG channel C (tools/music.py)
; ----------------------------------------------------------------------------
; A = tune
bgm_start:
        push hl
        push de
        add a,a
        ld e,a
        ld d,0
        ld hl,bgm_tbl
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        di
        ld (v_bgm_s),de
        ld (v_bgm_p),de
        ld a,1
        ld (v_bgm_t),a          ; first note on the next tick
        ei
        pop de
        pop hl
        ret

; sound interrupt: next note when due, volume envelope
bgm_tick:
        ld hl,(v_bgm_p)
        ld a,h
        or l
        ret z                   ; no tune yet
        ld a,(v_paused)
        or a
        jr z,bt_go
        ld a,10                 ; paused: silent, the tune waits
        out (0A0h),a
        xor a
        out (0A1h),a
        ret
bt_go:
        ld a,(v_bgm_t)
        dec a
        ld (v_bgm_t),a
        jr nz,bt_env
        ld a,(hl)
        cp 0FFh
        jr nz,bt_1
        ld hl,(v_bgm_s)         ; loop
        ld a,(hl)
bt_1:   inc hl
        ld b,(hl)
        inc hl
        ld (v_bgm_p),hl
        ld c,a
        ld a,b
        ld (v_bgm_t),a
        ld a,c
        or a
        jr z,bt_rest
        dec a
        add a,a
        ld e,a
        ld d,0
        ld hl,bgm_per
        add hl,de
        ld a,4
        out (0A0h),a
        ld a,(hl)
        out (0A1h),a
        ld a,5
        out (0A0h),a
        inc hl
        ld a,(hl)
        out (0A1h),a
        ld a,21                 ; volume 10, decaying to 6
        jr bt_v
bt_rest:
        xor a
        jr bt_v
bt_env: ld a,(v_bgm_v)
        cp 13
        jr c,bt_out
        dec a
bt_v:   ld (v_bgm_v),a
bt_out: ld a,10
        out (0A0h),a
        ld a,(v_bgm_v)
        srl a
        out (0A1h),a
        ret

; play the next step of channel A (0..2).  Uses A, B, C, D, E, H, L.
ch_step:
        ld c,a
        call ch_ptr
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,d
        or e
        ret z                   ; idle
        push hl                 ; -> pointer high byte
        ex de,hl                ; HL = step
        inc hl
        inc hl
        inc hl
        ld a,(hl)               ; volume
        cp 0FFh
        jr z,cs_end
        ld b,a
        ld a,c
        add a,8
        out (0A0h),a
        ld a,b
        out (0A1h),a
        dec hl
        ld a,(hl)               ; noise period
        or a
        jr z,cs_1
        ld b,a
        ld a,6
        out (0A0h),a
        ld a,b
        out (0A1h),a
cs_1:   dec hl
        ld b,(hl)               ; period high + flags
        dec hl
        ld a,c
        add a,a
        out (0A0h),a
        ld a,(hl)
        out (0A1h),a
        ld a,c
        add a,a
        inc a
        out (0A0h),a
        ld a,b
        and 0Fh
        out (0A1h),a
        call ch_mask            ; E = tone bit, D = noise bit
        ld a,(v_mix)
        or e
        or d                    ; both off, then switch on what the step wants
        bit 6,b
        jr nz,cs_2
        xor e
cs_2:   bit 7,b
        jr z,cs_3
        xor d
cs_3:   call mix_out
        ld de,4                 ; next step
        add hl,de
        ex de,hl
        pop hl
        ld (hl),d
        dec hl
        ld (hl),e
        ret
cs_end: ld a,c                  ; finished: silence the channel
        add a,8
        out (0A0h),a
        xor a
        out (0A1h),a
        pop hl
        ld (hl),a
        dec hl
        ld (hl),a
        call ch_mask
        ld a,(v_mix)
        or e
        or d
mix_out:
        ld (v_mix),a
        ld e,a
        ld a,7
        out (0A0h),a
        ld a,e
        out (0A1h),a
        ret

; C = channel -> E = its tone-off mixer bit, D = its noise-off bit
ch_mask:
        ld a,c
        ld e,1
cm_1:   or a
        jr z,cm_2
        sla e
        dec a
        jr cm_1
cm_2:   ld a,e
        add a,a
        add a,a
        add a,a
        ld d,a
        ret

sfx_tbl:
        defb 0
        defw sfx_shot
        defb 1
        defw sfx_hurt
        defb 0
        defw sfx_pick
        defb 0
        defw sfx_key
        defb 0
        defw sfx_door
        defb 0
        defw sfx_empty
        defb 0
        defw sfx_swing

sfx_shot:
        defb 70,128,3,14
        defb 90,0,0,13
        defb 115,0,0,11
        defb 145,0,0,9
        defb 185,0,0,7
        defb 235,0,0,4
        defb 0,0,0,0FFh
sfx_hurt:
        defb 232,131,28,15
        defb 20,133,0,15
        defb 232,131,0,15
        defb 20,133,0,14
        defb 232,3,0,13
        defb 20,5,0,11
        defb 232,3,0,8
        defb 0,0,0,0FFh
sfx_pick:
        defb 140,0,0,12
        defb 140,0,0,12
        defb 140,0,0,10
        defb 93,0,0,13
        defb 93,0,0,12
        defb 93,0,0,10
        defb 93,0,0,7
        defb 0,0,0,0FFh
sfx_key:
        defb 186,0,0,13
        defb 186,0,0,11
        defb 148,0,0,13
        defb 148,0,0,11
        defb 124,0,0,13
        defb 124,0,0,11
        defb 93,0,0,13
        defb 93,0,0,12
        defb 93,0,0,10
        defb 93,0,0,7
        defb 0,0,0,0FFh
sfx_door:
        defb 8,135,31,9
        defb 108,135,0,11
        defb 208,135,0,11
        defb 108,135,0,10
        defb 208,135,0,9
        defb 108,135,0,8
        defb 208,135,0,7
        defb 108,135,0,6
        defb 208,135,0,4
        defb 0,0,0,0FFh
sfx_empty:
        defb 40,0,0,10
        defb 40,64,0,0
        defb 0,0,0,0FFh
sfx_swing:                          ; a rush of air, falling
        defb 0,0C0h,2,12
        defb 0,0C0h,4,13
        defb 0,0C0h,7,11
        defb 0,0C0h,11,8
        defb 0,0C0h,16,5
        defb 0,0C0h,22,3
        defb 0,0,0,0FFh

rand:   push hl
        ld hl,(v_rng)
        ld a,h
        rra
        ld a,l
        rra
        xor h
        ld h,a
        ld a,l
        rra
        ld a,h
        rra
        xor l
        ld l,a
        xor h
        ld h,a
        ld (v_rng),hl
        pop hl
        ret

; ----------------------------------------------------------------------------
;  navigation: minimap (north up) and heading, redrawn only when needed
; ----------------------------------------------------------------------------
MM_X    equ 30                  ; byte column
MM_Y    equ 142                 ; screen row
MM_W    equ 20                  ; window: cells across (2 pixels each, even)
MM_H    equ 19                  ; cells down (3 rows each)
MM_CX   equ 10                  ; the player's place in the window
MM_CY   equ 9
MMP0    equ 3900h               ; two cells' colours (c1*16+c2) -> plane 0 byte
MMP1    equ 3A00h               ; and plane 1 byte (mm_tables)

; the tables above, at the start
mm_tables:
        ld hl,MMP0
mt_l:   ld a,l
        rrca
        rrca
        rrca
        rrca
        call mt_nib
        ld c,a                      ; the left cell's two pixels
        ld a,l
        call mt_nib
        ld b,a                      ; the right one's
        ld a,c
        add a,a
        add a,a
        add a,a
        add a,a
        ld e,a
        ld a,b
        and 0Fh
        or e
        ld (hl),a                   ; plane 0
        inc h
        ld a,b
        rrca
        rrca
        rrca
        rrca
        and 0Fh
        ld e,a
        ld a,c
        and 0F0h
        or e
        ld (hl),a                   ; plane 1
        dec h
        inc l
        jr nz,mt_l
        ret
mt_nib: and 0Fh
        push hl
        ld hl,mm_nibs
        add a,l
        ld l,a
        jr nc,mt_n1
        inc h
mt_n1:  ld a,(hl)
        pop hl
        ret

; the map scrolls with the player: redraw when the player's cell changed
nav_update:
        ld a,(v_px+1)
        ld e,a
        ld a,(v_py+1)
        ld d,a
        ld hl,(v_pcell)             ; (x, y)
        or a
        sbc hl,de
        ret z
        ld (v_pcell),de
        ld a,e
        sub MM_CX
        ld (v_mm_ox),a              ; window origin
        ld a,d
        sub MM_CY
        ld (v_mm_oy),a
        ld a,2
        ld (v_mm_dirty),a
        ret

; map panel: MM_W x MM_H cells around the player (north up), each 2 pixels x 3
; rows.  Walls and doors appear once a ray of the lantern has reached them.
draw_minimap:
        ld a,(v_mm_dirty)
        or a
        call nz,mm_full             ; this page in full, then
        ; the cells seen this frame, on both pages (the other page may
        ; have been drawn before they were seen)
        ld a,(v_newn)
        or a
        ret z
        ld b,a
        ld hl,v_newq
mm_q:   push bc
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        push hl
        call mm_plot
        pop hl
        pop bc
        djnz mm_q
        xor a
        ld (v_newn),a
        ret
mm_full:
        dec a
        ld (v_mm_dirty),a
        jr nz,mf_full               ; the first of the two pages: draw it
        ; the second: the same window is on the other page already - copy it
        ld a,(v_back_h)
        ld d,a
        xor 40h
        ld h,a
        ld l,0
        ld e,l
        ld bc,MM_Y*40+MM_X
        add hl,bc
        ex de,hl
        add hl,bc
        ex de,hl                    ; HL = the other page, DE = this one
        ld a,MM_H*3*2               ; rows, both planes
mf_cp:
        ldi
        ldi
        ldi
        ldi
        ldi
        ldi
        ldi
        ldi
        ldi
        ldi
        ld bc,40-MM_W/2
        add hl,bc
        ex de,hl
        add hl,bc
        ex de,hl
        dec a
        jr z,mf_cpe
        cp MM_H*3                   ; half way: on to plane 1
        jr nz,mf_cp
        ld bc,2000h-MM_H*3*40
        add hl,bc
        ex de,hl
        add hl,bc
        ex de,hl
        jr mf_cp
mf_cpe: ret
mf_full:
        ld a,(v_back_h)
        ld h,a
        ld l,0
        ld de,MM_Y*40+MM_X
        add hl,de
        push hl
        pop ix                      ; plane 0
        ld de,2000h
        add hl,de
        push hl
        pop iy                      ; plane 1
        xor a
        ld (v_mm_wy),a
mf_row: ld a,(v_mm_oy)              ; map row
        ld hl,v_mm_wy
        add a,(hl)
        cp MAPN
        jr c,mf_r2
        ld c,MAPN                   ; outside the floor: all dark
        jr mf_r3
mf_r2:  ld l,a                      ; DE = seen record of the first cell
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,v_seen
        add hl,de
        ld a,(v_mm_ox)
        ld c,a                      ; C = map x
        ld e,a
        rla
        sbc a,a
        ld d,a
        add hl,de
        ex de,hl
        ld a,c                      ; inside on the left: by the tables
        or a
        jp p,mf_t
        cp -9                       ; (the cell before is the last of the row
        jr z,mf_r3                  ; before; on the first row, the map's)
        ld a,(v_mm_oy)
        ld hl,v_mm_wy
        add a,(hl)
        jr z,mf_r3
mf_t:   ld b,MM_W/2
mf_tc:  ld a,(de)                   ; (seen: 80h + colour; the 8 goes)
        add a,a
        add a,a
        add a,a
        add a,a
        ld l,a
        inc de
        ld a,(de)
        and 0Fh
        or l
        ld l,a
        inc de
        ld h,MMP0 >> 8
        ld a,(hl)
        ld (ix+0),a
        ld (ix+40),a
        ld (ix+80),a
        inc h
        ld a,(hl)
        ld (iy+0),a
        ld (iy+40),a
        ld (iy+80),a
        inc ix
        inc iy
        djnz mf_tc
        jr mf_rn
mf_r3:  ld b,MM_W/2
mf_c:   ld a,c                      ; two cells -> one byte per plane
        cp MAPN
        ld a,0
        jr nc,mf_a1
        ld a,(de)
        and 0Fh                     ; seen: its colour; not seen: 0
mf_a1:  inc de
        inc c
        ld hl,mm_nibs
        add a,l
        ld l,a
        jr nc,mf_a2
        inc h
mf_a2:  ld a,(hl)
        ld (v_t_p0),a
        ld a,c
        cp MAPN
        ld a,0
        jr nc,mf_a3
        ld a,(de)
        and 0Fh
mf_a3:  inc de
        inc c
        ld hl,mm_nibs
        add a,l
        ld l,a
        jr nc,mf_a4
        inc h
mf_a4:  ld a,(hl)
        ld h,a
        and 0Fh
        ld l,a
        ld a,(v_t_p0)
        add a,a
        add a,a
        add a,a
        add a,a
        or l
        ld (ix+0),a
        ld (ix+40),a
        ld (ix+80),a
        ld a,h
        rrca
        rrca
        rrca
        rrca
        and 0Fh
        ld l,a
        ld a,(v_t_p0)
        and 0F0h
        or l
        ld (iy+0),a
        ld (iy+40),a
        ld (iy+80),a
        inc ix
        inc iy
        djnz mf_c
mf_rn:  ld bc,120-MM_W/2
        add ix,bc
        add iy,bc
        ld a,(v_mm_wy)
        inc a
        ld (v_mm_wy),a
        cp MM_H
        jp nz,mf_row
        ; the player: white, in the middle of the window (an even column:
        ; the left of the two pixels of its byte)
        ld a,(v_back_h)
        ld h,a
        ld l,0
        ld de,(MM_Y+3*MM_CY)*40+MM_X+MM_CX/2
        add hl,de
        ld b,3
mf_me:  ld a,(hl)
        or 0F0h
        ld (hl),a
        set 5,h
        ld a,(hl)
        or 0F0h
        ld (hl),a
        res 5,h
        ld de,40
        add hl,de
        djnz mf_me
        ret

; A = colour -> C = plane 0 nibble, B = plane 1 nibble (2 pixels each)
mm_nib: ld d,a
        and 3
        ld c,a
        add a,a
        add a,a
        add a,c
        ld c,a
        ld a,d
        rrca
        rrca
        and 3
        ld b,a
        add a,a
        add a,a
        add a,b
        ld b,a
        ret

; DE = cell index: draw that cell on both pages, if it is in the window
mm_plot:
        push de
        ld a,d                      ; y = index >> 5
        add a,a
        add a,a
        add a,a
        ld b,a
        ld a,e
        rlca
        rlca
        rlca
        and 7
        or b
        ld hl,v_mm_oy
        sub (hl)
        cp MM_H
        jr nc,mpl_x
        ld d,a                      ; window y
        ld a,e
        and 31
        ld hl,v_mm_ox
        sub (hl)
        cp MM_W
        jr nc,mpl_x
        ld e,a                      ; window x
        ld a,d
        cp MM_CY
        jr nz,mpl_1
        ld a,e
        cp MM_CX
        jr nz,mpl_1
mpl_x:  pop de                      ; outside, or the player's place
        ret
mpl_1:  pop hl                      ; cell index
        push de
        ld de,v_seen
        add hl,de
        ld a,(hl)
        and 0Fh                     ; its colour (0: not seen yet)
        call mm_nib                 ; C, B = low nibbles
        pop de
        ld a,0F0h                   ; odd column: low nibble (keep the high)
        bit 0,e
        jr nz,mpl_2
        ld a,c
        add a,a
        add a,a
        add a,a
        add a,a
        ld c,a
        ld a,b
        add a,a
        add a,a
        add a,a
        add a,a
        ld b,a
        ld a,0Fh                    ; keep the other cell
mpl_2:   ld (v_t_p0),a
        ld a,d                      ; offset = (MM_Y + 3y) * 40 + MM_X + x/2
        add a,a
        add a,d
        add a,MM_Y
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl                   ; *8
        push de
        ld d,h
        ld e,l
        add hl,hl
        add hl,hl                   ; *32
        add hl,de                   ; *40
        pop de
        ld a,e
        srl a
        add a,MM_X
        add a,l
        ld l,a
        jr nc,mpl_3
        inc h
mpl_3:   ld a,80h
        call mpl_pg
        ld a,0C0h
mpl_pg:  push hl
        add a,h
        ld h,a
        ld e,3
mpl_4:   ld a,(v_t_p0)
        and (hl)
        or c
        ld (hl),a
        set 5,h
        ld a,(v_t_p0)
        and (hl)
        or b
        ld (hl),a
        res 5,h
        push de
        ld de,40
        add hl,de
        pop de
        dec e
        jr nz,mpl_4
        pop hl
        ret

; floor, walls 1-3 gray, door orange, orange door yellow, violet door magenta, exit green
mm_colour:
        defb 0,7,7,7,2,14,11,12
; colour -> its two pixels: plane 1 nibble << 4 | plane 0 nibble
mm_nibs:
        defb 000h,005h,00Ah,00Fh,050h,055h,05Ah,05Fh
        defb 0A0h,0A5h,0AAh,0AFh,0F0h,0F5h,0FAh,0FFh

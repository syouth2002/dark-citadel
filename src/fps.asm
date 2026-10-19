; ============================================================================
;  DARK CITADEL  -  original raycasting first-person prototype
;  PC-6001mkII mode 5, 160x200 16 colours, double buffered (8000h / C000h)
;  View: 32 columns x 4 px (128 px) x VH rows at the top of the screen.
;  The view uses only colours 0..3 (plane 1 = 0), so columns write plane 0.
; ============================================================================
        org 4000h

#include "fps_vars.inc"

VECTBL          equ 0100h
ROWTBL          equ 0200h
ROWLO           equ 3D00h           ; row * 40, low bytes (page aligned)
ROWHI           equ 3E00h           ; high bytes
COLANG          equ 3DC8h           ; per column: angle offset (after ROWLO)
COLCOS          equ 3EC8h           ; and cos(offset) (after ROWHI)
EDGE            equ 3700h           ; |1/cos| * 20/256 by angle: low bytes, high at 3800h
STACKTOP        equ 4000h
VY0             equ 4               ; first view row
FRAME_TICKS     equ 20              ; 40 ms -> at most 25 fps
LANTERN         equ 5               ; light reaches this many cells (in depth)
RAY_MAX         equ 6               ; = LANTERN / cos(half the field of view), rounded up
HIT_DARK        equ 8               ; "wall" type of the darkness

; STICK bits (keyboard)
K_SPACE equ 80h
K_LEFT  equ 20h
K_RIGHT equ 10h
K_DOWN  equ 08h
K_UP    equ 04h
K_SHIFT equ 01h

start:
        di
        ld sp,STACKTOP
        ld a,0DDh
        out (0F0h),a
        out (0F1h),a
        ld a,55h
        out (0F2h),a
        ld hl,0100h
        ld de,0101h
        ld bc,3EFFh
        ld (hl),0
        ldir
        ld hl,VECTBL
        ld b,129
st_vt:  ld (hl),isr_dummy & 0FFh
        inc hl
        ld (hl),isr_dummy >> 8
        inc hl
        djnz st_vt
        ld hl,isr_timer
        ld (VECTBL+06h),hl
        ld hl,isr_key
        ld (VECTBL+02h),hl
        ld (VECTBL+14h),hl
        ld hl,isr_strig
        ld (VECTBL+16h),hl
        ld a,VECTBL >> 8
        ld i,a
        im 2
        ld hl,0
        ld de,40
        ld ix,ROWTBL
        ld b,200
st_rt:  ld (ix+0),l
        ld (ix+1),h
        ld a,200
        sub b                       ; the row
        push de
        ex de,hl                    ; DE = row * 40
        ld l,a
        ld h,ROWLO >> 8
        ld (hl),e
        inc h
        ld (hl),d
        ex de,hl
        pop de
        inc ix
        inc ix
        add hl,de
        djnz st_rt
        ld hl,col_ang
        ld de,COLANG
        ld bc,NCOL
        ldir
        ld de,COLCOS                ; (col_cos follows col_ang)
        ld c,NCOL
        ldir
        xor a
        out (0C0h),a
        ld a,08h
        out (0C1h),a
        xor a
        ld (v_page),a
        out (0B0h),a
        call psg_init
        ld a,3
        out (0F6h),a
        ld a,06h
        out (0F7h),a
        xor a
        out (0F3h),a
        ld hl,0ACE1h
        ld (v_rng),hl
        call gen_sq
        call gen_tables
        ld c,0                      ; the edge table: 20/256 of a cell along
eg_l:   ld l,c                      ; a wall, as distance along the ray
        ld h,0
        add hl,hl
        ld de,ddx_tbl
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,20
        call umul8_16               ; (keeps BC)
        ex de,hl
        ld l,c
        ld h,EDGE >> 8
        ld (hl),e
        inc h
        ld (hl),d
        inc c
        jr nz,eg_l
        call mm_tables
        ; the screens (and the start-up data beyond 7FFFh: unpacked by now)
        ld hl,8000h
        ld de,8001h
        ld bc,7FFFh
        ld (hl),0
        ldir
        ld hl,v_pbot0
        ld b,NCOL
        call st_vh
        ld hl,v_pbot1
        ld b,NCOL
        call st_vh
        ei
        ; static texts on both pages
        ld a,80h
        call draw_static
        ld a,0C0h
        call draw_static
#ifdef VTEST
        jp voice_test
#endif
        ld a,1                      ; (NORMAL until another is chosen)
        ld (v_diff),a
        call title
        call new_game

main:   call read_input
        ld a,(v_lvdone)
        or a
        jr z,mn_0
        call intermission       ; floor finished
        jp main
mn_0:   ld a,(v_dead)
        or a
        jr z,mn_1
        ld a,(v_inp_new)        ; slain: continue on this floor, or the title
        ld b,a
        and 0Fh                 ; a direction: the other choice
        jr z,mn_d1
        ld a,(v_dchoice)
        xor 1
        ld (v_dchoice),a
        ld a,2
        ld (v_hud_dirty),a
mn_d1:  ld a,b
        and I_FIRE
        jr z,mn_2
        ld a,(v_dchoice)
        or a
        jr nz,mn_d2
        call restart_level
        jr mn_2
mn_d2:  call title
        call new_game
        jr mn_2
mn_1:   ld a,(v_inp_new)        ; STOP: pause
        and 40h
        call nz,pause
        call move_player
        call player_fire
        call update_enemies
mn_2:   call set_back
        call wp_check
        call render_view
        call calc_sprites
        call draw_sprites
        call draw_hurtdir
        call draw_weapon
        call draw_status
        call nav_update
        call draw_minimap
        call wait_flip
        jp main

st_vh:  ld (hl),VH
        inc hl
        djnz st_vh
        ret

; ----------------------------------------------------------------------------
draw_static:
        ld (v_tgt_h),a
        ld a,14
        call set_color
        ld hl,s_title
        ld de,(1 << 8) | L4_Y
        call draw_text
        ld a,7
        call set_color
        ld hl,s_help
        ld de,(1 << 8) | L5_Y
        jp draw_text

; ============================================================================
;  player
; ============================================================================
SPEED   equ 36
ROT     equ 4
MARGIN  equ 48

move_player:
        ld a,(v_inp)
        ld c,a
        ld a,(v_pa)
        bit 2,c                 ; left
        jr z,mp_1
        sub ROT
mp_1:   bit 3,c                 ; right
        jr z,mp_2
        add a,ROT
mp_2:   ld (v_pa),a
        bit 0,c                 ; up = forward
        jr z,mp_3
        ld b,SPEED
        call walk
mp_3:   ld a,(v_inp)
        bit 1,a                 ; down = back
        ret z
        ld b,-SPEED
        jp walk

; B = signed step (1/256 cell); move along pa with sliding collision
walk:
        ld a,b
        ld (v_t_p0),a           ; remember the step for the y part
        ld a,(v_pa)
        ld l,a
        ld h,0
        add hl,hl
        push hl
        ld de,cos_tbl
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,b
        call smul               ; HL = (DE * A) >> 8, signed
        push hl
        ; x: test cell at px + dx (+- margin)
        ld de,(v_px)
        add hl,de
        ex de,hl                ; DE = new x
        pop bc                  ; BC = dx
        push de
        ld a,b
        or a
        ld hl,MARGIN
        jp p,wk_1
        ld hl,-MARGIN
wk_1:   add hl,de
        ld e,h                  ; cell x with margin
        ld a,(v_py+1)
        ld d,a
        call map_at
        jr z,wk_1b
        call door_touch         ; blocked: maybe a door / the exit
        pop de
        jr wk_2
wk_1b:  pop de
        ld (v_px),de
wk_2:   pop hl
        ld de,sin_tbl
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ld a,(v_t_p0)
        call smul
        push hl
        ld de,(v_py)
        add hl,de
        ex de,hl
        pop bc
        push de
        ld a,b
        or a
        ld hl,MARGIN
        jp p,wk_4
        ld hl,-MARGIN
wk_4:   add hl,de
        ld d,h
        ld a,(v_px+1)
        ld e,a
        call map_at
        jr z,wk_4b
        call door_touch
        pop de
        ret
wk_4b:  pop de
        ld (v_py),de
        ret

; E = x cell, D = y cell -> A = map value, Z if empty, HL = cell
; (outside the floor counts as wall).  Map rows are MAPS bytes apart.
map_at:
        ld a,e
        cp MAPN
        jr nc,ma_out
        ld a,d
        cp MAPN
        jr nc,ma_out
        ld l,d
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,l
        or e
        ld l,a
        ld de,v_map
        add hl,de
        ld a,(hl)
        or a
        ret
ma_out: ld a,1
        or a
        ret

; HL = (DE * A) >> 8 with DE and A signed
smul:
        ld c,0                  ; sign flag
        or a
        jp p,sm_1
        neg
        inc c
sm_1:   bit 7,d
        jr z,sm_2
        push af
        xor a
        sub e
        ld e,a
        ld a,0
        sbc a,d
        ld d,a
        pop af
        inc c
sm_2:   call umul8_16           ; HL = (DE * A) >> 8 unsigned
        bit 0,c
        ret z
        xor a
        sub l
        ld l,a
        ld a,0
        sbc a,h
        ld h,a
        ret

; HL = (DE * A) >> 8, unsigned (A 8 bit, DE 16 bit).  Preserves BC.
; Both products by quarter squares, in line: a*x = q(a+x) - q(|a-x|).
umul8_16:
        push bc
        ld b,a                  ; B = a
        ld c,d                  ; C = the high byte of DE
        add a,e                 ; HL -> q(a+e), low bytes
        ld l,a
        ld a,SQP
        adc a,0
        ld h,a
        ld a,b
        sub e
        jr nc,uq_1
        neg
uq_1:   ld e,a                  ; DE -> q(|a-e|), low bytes
        ld d,SQP
        ld a,(hl)
        ex de,hl
        sub (hl)                ; (only the borrow matters)
        ex de,hl
        inc h
        inc h
        inc d
        inc d
        ld a,(hl)
        ex de,hl
        sbc a,(hl)              ; A = (a*e) >> 8
        ld e,a
        ld a,c
        or a
        jr nz,uq_2
        ld l,e                  ; DE < 256: that is all
        ld h,a
        pop bc
        ret
uq_2:   ld l,b                  ; a*d: d = 1 or 2 by adding (most often)
        ld h,0
        dec a
        jr z,uq_d1
        dec a
        jr nz,uq_5
        add hl,hl
uq_d1:  ld a,l
        add a,e                 ; + (a*e) >> 8
        ld l,a
        jr nc,uq_d2
        inc h
uq_d2:  pop bc
        ret
uq_5:   call uq_g
        pop bc
        ret
; B = a, C = d (>= 3), E = (a*e) >> 8 -> HL = a*d + E
uq_g:   ld a,c
        cp 5
        jr nc,uq_gg
        ld l,b                  ; d = 3 or 4: by adding
        ld h,0
        add hl,hl
        cp 4
        jr z,uq_g4
        ld a,l
        add a,b
        ld l,a
        jr nc,uq_g5
        inc h
        jr uq_g5
uq_g4:  add hl,hl
uq_g5:  ld a,l
        add a,e                 ; + (a*e) >> 8
        ld l,a
        ret nc
        inc h
        ret
uq_gg:  ld a,b                  ; a*d, all 16 bits
        add a,c
        ld l,a
        ld a,SQP
        adc a,0
        ld h,a
        ld a,b
        sub c
        jr nc,uq_3
        neg
uq_3:   ld c,a
        ld b,SQP
        ld a,(bc)
        ld d,a
        ld a,(hl)
        sub d
        ld d,a                  ; low byte
        inc h
        inc h
        inc b
        inc b
        ld a,(bc)
        ld c,a
        ld a,(hl)
        sbc a,c
        ld h,a
        ld a,d
        add a,e                 ; + (a*e) >> 8
        ld l,a
        ret nc
        inc h
        ret

; HL = A * E using quarter squares: a*e = q(a+e) - q(|a-e|), q(i) = i*i/4
; tables: low bytes at SQP*256 (512), high bytes at (SQP+2)*256 (512)
; destroys A, C, D, E
SQP     equ 10h
mulq:   ld c,a
        sub e
        jr nc,mq_1
        neg
mq_1:   ld d,a                  ; |a-e|
        ld a,c
        add a,e
        ld l,a
        ld a,SQP
        adc a,0
        ld h,a
        ld c,(hl)               ; q(a+e) low
        inc h
        inc h
        ld a,(hl)               ; q(a+e) high
        ld l,d
        ld h,SQP+2
        ld d,(hl)               ; q(|a-e|) high
        dec h
        dec h
        ld e,(hl)               ; q(|a-e|) low
        ld h,a
        ld a,c
        sub e
        ld l,a
        ld a,h
        sbc a,d
        ld h,a
        ret

; build the quarter-square tables: q(i+1) = q(i) + ((i+1) >> 1)
gen_sq: ld hl,0                 ; q
        ld de,SQP*256           ; table position (low byte table)
        ld bc,0                 ; i
gs_1:   ld a,l
        ld (de),a
        inc d
        inc d
        ld a,h
        ld (de),a
        dec d
        dec d
        inc bc
        push bc
        srl b
        rr c
        add hl,bc
        pop bc
        inc de
        ld a,b
        cp 2
        jr c,gs_1
        ret

; ----------------------------------------------------------------------------
;  tables built at start-up in low RAM (they are not stored in full)
; ----------------------------------------------------------------------------
gen_tables:
        ; cos and |1/cos| from a quarter wave; sin and |1/sin| are the same
        ; tables shifted by 64 (a quarter turn)
        ld hl,q_cos
        ld de,cos_tbl
        ld a,1
        call quad
        ld hl,q_ddx
        ld de,ddx_tbl
        xor a
        call quad
        ld hl,cos_tbl
        ld de,sin_tbl
        call shift64
        ld hl,ddx_tbl
        ld de,ddy_tbl
        call shift64
        ; wall heights: rows = PROJ_K / distance, at most VH
        ld ix,ht_near
        ld de,4                 ; distance of entry i = 8i + 4
        ld bc,8
        ld a,0                  ; 256 entries
        call ht_fill
        ld ix,ht_far
        ld de,32                ; 64i + 32
        ld bc,64
        ld a,128
        call ht_fill
        ; near sprites: size (3/4 of the height, at most 320) and top row
        ld ix,spr_hs
        ld iy,spr_top
        ld de,2                 ; 4i + 2
        ld b,128
gt_s:   push bc
        push de
        call proj_div           ; HL = rows
        ld bc,320
        or a
        sbc hl,bc
        add hl,bc
        jr c,gt_s1
        ld h,b
        ld l,c
gt_s1:  ld d,h                  ; DE = h
        ld e,l
        srl d
        rr e
        srl d
        rr e                    ; h/4
        push hl
        or a
        sbc hl,de               ; hs = h - h/4
        ld (ix+0),l
        pop de                  ; DE = h
        ex de,hl
        ld bc,VH
        add hl,bc
        srl h
        rr l                    ; (h + VH)/2
        ld a,l
        sub e
        ld (iy+0),a             ; top
        inc ix
        inc iy
        pop de
        ld hl,4
        add hl,de
        ex de,hl
        pop bc
        djnz gt_s
        ; sprite textures: unpack the nibbles (into the space the RAM data
        ; takes later), then nibbles -> bytes (Fh = transparent -> FFh)
        ld hl,tex_pack_lz
        ld de,RAM_DATA
        call unlz
        ld hl,RAM_DATA
        ld de,TEX_RAM
        ld bc,NTEX_PACKED*48
gt_t:   ld a,(hl)
        rrca
        rrca
        rrca
        rrca
        call gt_put
        ld a,(hl)
        call gt_put
        inc hl
        dec bc
        ld a,b
        or c
        jr nz,gt_t
        ; weapons, floors, voices, music
        ld hl,ram_blob
        ld de,RAM_DATA
; HL = LZ stream (tools/lz.py) -> DE
unlz:   ld a,(hl)
        inc hl
        cp 80h
        ret z                       ; end
        jr nc,ul_m
        ld c,a                      ; 00h-7Fh: that many + 1 literals
        ld b,0
        inc c
        ldir
        jr unlz
ul_m:   and 7Fh                     ; 81h-FFh: copy (n & 7Fh) + 2 bytes
        add a,2                     ; from (output - offset)
        push hl
        ld c,(hl)
        inc hl
        ld b,(hl)
        ld h,d
        ld l,e
        or a
        sbc hl,bc
        ld c,a
        ld b,0
        ldir
        pop hl
        inc hl
        inc hl
        jr unlz
gt_put: and 0Fh
        cp 0Fh
        jr nz,gt_p1
        ld a,0FFh
gt_p1:  ld (de),a
        inc de
        ret

; HL = 65 words (angles 0..64), DE = 256-word table, A = 1 if the second
; quarter is negated (cos) or 0 (|1/cos|)
quad:   ld b,a
        ld c,0
qd_lp:  ld a,(hl)
        ld (v_qv),a
        inc hl
        ld a,(hl)
        ld (v_qv+1),a
        inc hl
        ld a,c
        call qput               ; i
        xor a
        sub c
        call qput               ; -i
        ld a,b
        or a
        jr z,qd_1
        push hl
        ld hl,(v_qv)
        xor a
        sub l
        ld l,a
        sbc a,a
        sub h
        ld h,a
        ld (v_qv),hl
        pop hl
qd_1:   ld a,128
        sub c
        call qput               ; 128 - i
        ld a,128
        add a,c
        call qput               ; 128 + i
        inc c
        ld a,c
        cp 65
        jr nz,qd_lp
        ret
qput:   push hl
        ld l,a
        ld h,0
        add hl,hl
        add hl,de
        ld a,(v_qv)
        ld (hl),a
        inc hl
        ld a,(v_qv+1)
        ld (hl),a
        pop hl
        ret

; DE[i] = HL[i - 64] for 256-word tables
shift64:
        push hl
        ld bc,384
        add hl,bc
        ld bc,128
        ldir
        pop hl
        ld bc,384
        ldir
        ret

; IX = table, DE = first distance, BC = distance step, A = entries (0 = 256)
ht_fill:
        push af
        push bc
        push de
        call proj_div
        ld a,h
        or a
        jr nz,hq_1
        ld a,l
        cp VH+1
        jr c,hq_2
hq_1:   ld a,VH
hq_2:   ld (ix+0),a
        inc ix
        pop hl
        pop bc
        add hl,bc
        ex de,hl
        pop af
        dec a
        jr nz,ht_fill
        ret

; HL = (PROJ_K + DE/2) / DE, rounded
proj_div:
        ld h,d
        ld l,e
        srl h
        rr l
        ld bc,PROJ_K
        add hl,bc
        jp div16

; A = cells the lantern lights (5, or 7 with oil): patch the ray code; the
; rays run a little further (the edge of the view is 30 degrees off)
set_lantern:
        ld hl,v_vfull               ; (the view changes: both pages in full)
        ld (hl),2
        ld (lt_c1+1),a
        ld (lt_c2+2),a
        ld b,a
        add a,2
        srl a
        srl a
        add a,b                     ; A + (A + 2) / 4: 5 -> 6, 7 -> 9
        ld (ray_c1+1),a
        ld (ray_c2+1),a
        ld a,b                      ; objects further than A * 1.5 + 2 cells
        srl a                       ; on either axis cannot be seen: 5 -> 9
        add a,b                     ; (they are skipped before any sums)
        add a,2
        ld (cl_c1+1),a
        ld (cl_c2+1),a
        ret

; HL = HL / DE (unsigned 16 bit), result in HL
div16:
        ld a,h
        ld c,l
        ld hl,0
        ld b,16
dv_1:   sla c
        rla
        adc hl,hl
        sbc hl,de
        jr nc,dv_2
        add hl,de
        dec c
dv_2:   inc c
        djnz dv_1
        ld h,a
        ld l,c
        ret

; ============================================================================
;  raycasting
; ============================================================================
; The view is worked out again only where it may have changed: if the
; player stands as when this page was last drawn (and as last frame), and
; the scene is the same (v_vfull = 0), only the columns something was drawn
; over (cdirty: sprites, the weapon, marks) are drawn again.
render_view:
        ld a,(v_back_h)
        ld h,a
        ld l,0
        ld de,VY0*40
        add hl,de
        ld (v_vaddr),hl
        ld hl,v_pose0
        ld de,v_cdirty0
        ld a,(v_back_h)
        cp 80h
        jr z,rv_m1
        ld hl,v_pose1
        ld de,v_cdirty1
rv_m1:  ld (v_rvdp),de
        push hl
        ld hl,-2*NCOL               ; (ptop, pbot, cdirty)
        add hl,de
        ld (dc_pb+2),hl
        pop hl
        ld c,0                      ; 0: all columns
        ld a,(v_vfull)
        or a
        jr z,rv_m2
        dec a                       ; (both pages in full)
        ld (v_vfull),a
        push hl
        ld hl,(v_rvdp)              ; the walls drawn again in full, too
        ld de,NCOL                  ; (pshd follows cdirty)
        add hl,de
        ld b,e
rv_kz:  ld (hl),d
        inc hl
        djnz rv_kz
        pop hl
        jr rv_m4
rv_m2:  push hl                     ; the pose: px, py, pa (5 bytes)
        ld de,v_px
        ld b,5
rv_m3:  ld a,(de)
        cp (hl)
        jr nz,rv_m5
        inc de
        inc hl
        djnz rv_m3
        pop hl
        ld de,v_posel               ; and as the last frame (the zbuf)
        push hl
        ld hl,v_px
        ld b,5
rv_m6:  ld a,(de)
        cp (hl)
        jr nz,rv_m5
        inc de
        inc hl
        djnz rv_m6
        inc c                       ; 1: the marked columns only
rv_m5:  pop hl
rv_m4:  ld a,c
        ld (v_rvpart),a
        ex de,hl                    ; remember the pose for this page
        ld hl,v_px
        push hl
        ld bc,5
        ldir
        pop hl
        ld de,v_posel
        ld bc,5
        ldir
        ld a,(v_py+1)               ; the player's cell (every ray starts there)
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld a,(v_px+1)
        or l
        ld l,a
        ld de,v_map
        add hl,de
        ld (cr_mp+2),hl
        xor a
        ld (v_col),a
        ld a,(v_rvpart)
        or a
        jr nz,rv_col
        ld hl,(v_rvdp)              ; in full: the marks go, every column
        ld b,NCOL
rv_cl:  ld (hl),a
        inc hl
        djnz rv_cl
rv_fl:  call cast_ray
        call draw_column
        ld hl,(v_vaddr)
        inc hl
        ld (v_vaddr),hl
        ld hl,v_col
        inc (hl)
        ld a,(hl)
        cp NCOL
        jp c,rv_fl
        ret
rv_col: ld hl,(v_rvdp)              ; this column marked?
        ld a,(hl)
        ld (hl),0
        inc hl
        ld (v_rvdp),hl
        or a
        jr z,rv_nx                  ; no: as it was
        call cast_ray
        call draw_column
rv_nx:  ld hl,(v_vaddr)
        inc hl
        ld (v_vaddr),hl
        ld a,(v_col)
        inc a
        ld (v_col),a
        cp NCOL
        jp c,rv_col
        ret

cast_ray:
        ; ray angle
        ld a,(v_col)
        add a,COLANG & 0FFh
        ld l,a
        ld h,COLANG >> 8
        ld a,(v_pa)
        add a,(hl)
        ld (v_ra),a
        ; deltas and signs: the tables are 512 bytes each from a page start,
        ; cos 14h, sin 16h, |1/cos| 18h, |1/sin| 1Ah
        add a,a
        ld l,a
        ld a,ddx_tbl >> 8
        adc a,0
        ld h,a                  ; -> |1/cos|
        ld c,(hl)
        inc l
        ld b,(hl)               ; BC = ddx (kept through the multiplies)
        ld (dda_dx+1),bc
        ld a,h
        sub 4
        ld h,a                  ; -> cos, the high byte: the sign
        ld a,23h                ; inc ix
        bit 7,(hl)
        jr z,cr_s1
        ld a,2Bh                ; dec ix
cr_s1:  ld (dda_xs+1),a
        push hl
        ld d,b
        ld e,c
        ld a,(v_px)
        ld b,a                  ; (umul8_16 in line)
        ld c,d
        add a,e
        ld l,a
        ld a,SQP
        adc a,0
        ld h,a
        ld a,b
        sub e
        jr nc,cx_a
        neg
cx_a:   ld e,a
        ld d,SQP
        ld a,(hl)
        ex de,hl
        sub (hl)
        ex de,hl
        inc h
        inc h
        inc d
        inc d
        ld a,(hl)
        ex de,hl
        sbc a,(hl)
        ld e,a
        ld l,b                  ; (DE >= 256 here)
        ld h,0
        ld a,c
        dec a
        jr z,cx_c
        dec a
        jr nz,cx_g
        add hl,hl
cx_c:   ld a,l
        add a,e
        ld l,a
        jr nc,cx_e
        inc h
        jr cx_e
cx_g:   call uq_g
cx_e:
        ld a,(dda_xs+1)
        cp 23h
        jr nz,cr_x1
        ex de,hl                ; step +1: (1 - frac) * ddx = ddx - frac*ddx
        ld hl,(dda_dx+1)
        or a
        sbc hl,de
cr_x1:  ex (sp),hl              ; (sdx on the stack) -> cos
        ld a,h
        add a,6
        ld h,a                  ; -> |1/sin|
        ld d,(hl)
        dec l
        ld e,(hl)
        ld (dda_dy+1),de
        inc l
        ld a,h
        sub 4
        ld h,a                  ; -> sin, the sign
        bit 7,(hl)
        ld hl,MAPS
        jr z,cr_s2
        ld hl,-MAPS
cr_s2:  ld (dda_sy+1),hl
        ld a,(v_py)
        ld b,a                  ; (umul8_16 in line)
        ld c,d
        add a,e
        ld l,a
        ld a,SQP
        adc a,0
        ld h,a
        ld a,b
        sub e
        jr nc,cy_a
        neg
cy_a:   ld e,a
        ld d,SQP
        ld a,(hl)
        ex de,hl
        sub (hl)
        ex de,hl
        inc h
        inc h
        inc d
        inc d
        ld a,(hl)
        ex de,hl
        sbc a,(hl)
        ld e,a
        ld l,b                  ; (DE >= 256 here)
        ld h,0
        ld a,c
        dec a
        jr z,cy_c
        dec a
        jr nz,cy_g
        add hl,hl
cy_c:   ld a,l
        add a,e
        ld l,a
        jr nc,cy_e
        inc h
        jr cy_e
cy_g:   call uq_g
cy_e:
        ld a,(dda_sy+2)
        or a
        jr nz,cr_y1
        ex de,hl
        ld hl,(dda_dy+1)
        or a
        sbc hl,de
cr_y1:  ex de,hl
cr_dda: ; DDA with registers: HL = sdx, DE = sdy, BC = ddx, IX = map pointer;
        ; the x step, ddy and the row step are patched into the code
        pop hl
        ld bc,(dda_dx+1)
cr_mp:  ld ix,0                 ; (patched: the player's cell, render_view)
dda_lp: or a
        sbc hl,de
        add hl,de
        jr nc,dda_y
        ld a,h
ray_c1: cp RAY_MAX              ; (patched: set_lantern)
        jr nc,dda_dk            ; beyond the lantern's light
        add hl,bc               ; sdx += ddx
dda_xs: inc ix                  ; (patched: inc ix / dec ix)
        ld a,(ix+0)
        or a
        jr z,dda_lp
        ld (v_hit),a
        xor a
        ld (v_side),a
        sbc hl,bc               ; carry is clear: dist = sdx - ddx
        ld bc,(dda_dy+1)        ; (DE = sdy: the other lines)
        jr cr_d1
dda_dk: jp dda_dark             ; (in reach of the loop)
dda_y:  ld a,d
ray_c2: cp RAY_MAX              ; (patched)
        jr nc,dda_dk
        ex de,hl
dda_dy: ld bc,0                 ; (patched: ddy)
        add hl,bc               ; sdy += ddy
        ex de,hl
dda_sy: ld bc,0                 ; (patched: +-16, one map row)
        add ix,bc
dda_dx: ld bc,0                 ; (patched: ddx)
        ld a,(ix+0)
        or a
        jr z,dda_lp
        ld (v_hit),a
        ld a,1
        ld (v_side),a
        ex de,hl
        ld bc,(dda_dy+1)
        or a
        sbc hl,bc               ; dist = sdy - ddy
        ld bc,(dda_dx+1)        ; (DE = sdx)
cr_d1:  ; how near the hit is to the wall's cell edge, as distance along the
        ; ray: to the next crossing of the other lines (sd - dist) or from
        ; the last one (delta - that), the nearer
        push hl
        ex de,hl
        or a
        sbc hl,de
        ex de,hl                ; DE = to the next
        ld h,b
        ld l,c
        or a
        sbc hl,de               ; HL = from the last
        or a
        sbc hl,de
        add hl,de
        jr c,cr_e1
        ex de,hl
cr_e1:  ld (v_edge),hl
        pop hl
        ; perpendicular = dist * cos(col offset)
        ex de,hl
        ld a,(v_col)
        add a,COLCOS & 0FFh
        ld l,a
        ld h,COLCOS >> 8
        ld a,(hl)
        ld b,a                  ; (umul8_16 in line)
        ld c,d
        add a,e
        ld l,a
        ld a,SQP
        adc a,0
        ld h,a
        ld a,b
        sub e
        jr nc,cp_a
        neg
cp_a:   ld e,a
        ld d,SQP
        ld a,(hl)
        ex de,hl
        sub (hl)
        ex de,hl
        inc h
        inc h
        inc d
        inc d
        ld a,(hl)
        ex de,hl
        sbc a,(hl)
        ld e,a
        ld a,c
        or a
        jr nz,cp_b
        ld l,e
        ld h,a
        jr cp_e
cp_b:   ld l,b
        ld h,0
        dec a
        jr z,cp_c
        dec a
        jr nz,cp_g
        add hl,hl
cp_c:   ld a,l
        add a,e
        ld l,a
        jr nc,cp_e
        inc h
        jr cp_e
cp_g:   call uq_g
cp_e:
        ld de,40
        or a
        sbc hl,de
        add hl,de
        jr nc,cr_lt
        ld hl,40                ; not closer than ~0.16 cell
cr_lt:  ; the lantern lights everything nearer than LANTERN cells in depth
        ; (so a wall is dark or lit as a whole, whatever its angle)
        ld a,h
lt_c1:  cp LANTERN              ; (patched)
        jr c,cr_lit
dda_dark:
        ld a,HIT_DARK
        ld (v_hit),a
lt_c2:  ld hl,LANTERN*256       ; (patched: the high byte)
        jr cr_d3
cr_lit: ; auto map: this wall / door has been seen
        ld a,ixl                ; (its record: 300h on from the map cell)
        ld e,a
        ld a,ixh
        add a,(v_seen-v_map) >> 8
        ld d,a
        ld a,(de)
        or a
        jr nz,cr_d3
        push hl
        ex de,hl
        ld a,(ix+0)             ; seen: 80h + its map colour
        push hl
        ld hl,mm_colour
        add a,l
        ld l,a
        jr nc,cr_c1
        inc h
cr_c1:  ld a,(hl)
        pop hl
        or 80h
        ld (hl),a
        ld a,(v_newn)           ; queue it for the map panel
        cp 32
        jr nc,cr_sf
        inc a
        ld (v_newn),a
        add a,a
        ld e,a
        ld d,0
        ld hl,v_newq-2
        add hl,de
        push hl
        push ix
        pop hl
        ld de,-v_map
        add hl,de               ; cell index
        ex de,hl
        pop hl
        ld (hl),e
        inc hl
        ld (hl),d
        jr cr_sn
cr_sf:  ld a,2                  ; too many: redraw the whole panel
        ld (v_mm_dirty),a
cr_sn:  pop hl
cr_d3:  ld (v_dist),hl
        ex de,hl                ; keep perp per column (zbuf, later for sprites)
        ld a,(v_col)
        add a,a
        add a,v_zbuf & 0FFh     ; (in one page)
        ld l,a
        ld h,v_zbuf >> 8
        ld (hl),e
        inc l
        ld (hl),d
        ex de,hl
        ; wall height from tables (no division)
        ld a,h
        cp 8
        jr nc,cr_far
        ld a,l                  ; near: index = perp >> 3
        srl h
        rra
        srl h
        rra
        srl h
        rra
        ld l,a
        ld h,ht_near >> 8       ; (page aligned)
        jr cr_h1
cr_far: add a,a                 ; far: index = perp >> 6
        add a,a
        ld e,a
        ld a,l
        rlca
        rlca
        and 3
        or e
        cp 128
        jr c,cr_f1
        ld a,127
cr_f1:  ld l,a
        ld h,ht_far >> 8
cr_h1:  ld a,(hl)
        ld (v_wh),a
        ld b,a
        ld a,VH
        sub b
        srl a
        ld (v_wtop),a
        ret

; HL = how near the hit is to a cell edge (along the ray), DE = 20/256 of
; a cell along the wall in the same measure: HL < DE -> within 20/256
hit_edge:
        ld a,(v_side)
        or a
        ld a,(v_ra)
        jr nz,he_1
        sub 64                  ; side 0 (x wall): along y, |1/sin|
he_1:   ld l,a
        ld h,EDGE >> 8
        ld e,(hl)
        inc h
        ld d,(hl)
        ld hl,(v_edge)
        or a
        ret

; draw the current column: ceiling, wall, floor (plane 0 only)
draw_column:
        ; shade index: type, side, distance band (+1 near cell edges)
        ld a,(v_dist+1)         ; cells
        ld b,0
        cp 2
        jr c,dc_b
        inc b
        cp 3
        jr c,dc_b
        inc b
        cp 4
        jr c,dc_b
        inc b
dc_b:   ld a,(v_hit)
        cp HIT_DARK
        jr z,dc_fr              ; the dark: black
        cp 4
        jr c,dc_w
        cp 7
        jr nc,dc_w
        call hit_edge           ; doors: black frame at both edges
        ex de,hl
        add hl,hl               ; (40/256)
        ex de,hl
        or a
        sbc hl,de
        jr nc,dc_s
dc_fr:  ld hl,0
        ld (v_shade),hl
        ld a,0FEh               ; (its key)
        jr dc_draw
dc_w:   ld a,b
        cp 3
        jr nc,dc_s
        call hit_edge           ; (keeps B)
        sbc hl,de
        jr nc,dc_s
        inc b
dc_s:   ld a,(v_hit)
        dec a
        add a,a
        add a,a
        add a,a
        ld c,a
        ld a,(v_side)
        add a,a
        add a,a
        add a,c
        add a,b
        add a,a                 ; 2 bytes per entry
        ld c,a
        ld b,0
        ld hl,wall_pat
        add hl,bc
        ld b,(hl)
        inc hl
        ld c,(hl)
        ld (v_shade),bc         ; (B: even rows, C: odd)
        ld a,l                  ; its key: odd, not 0
        or 1
dc_draw:
        ; ---- draw.  The ceiling and the floor of this page are only
        ; repainted where the wall top / bottom moved since the last time;
        ; the wall too, if it has the same shade as then (pshd: its key).
        ld (dc_key+1),a
dc_pb:  ld ix,0                 ; (patched: this page's ptop, render_view)
        ld a,(v_col)
        ld e,a
        ld d,0
        add ix,de               ; (ix+0) = previous top, (ix+NCOL) = previous bottom
        ; ceiling rows previous top .. new top - 1
        ld c,(ix+0)
        ld a,(v_wtop)
        sub c
        jr c,dc_nc
        jr z,dc_nc
        push af
        ld a,c
        call row_addr
        pop af
        ld bc,0
        call fill_seg
dc_nc:  ; wall
dc_key: ld a,0                  ; (patched: the key)
        cp (ix+3*NCOL)
        jr nz,dc_wf
        ld a,(v_wtop)           ; the same shade: the rows above the old top
        ld c,a
        ld a,(ix+0)
        sub c
        jr c,dc_w2
        jr z,dc_w2
        push af
        ld a,c
        call row_addr
        pop af
        ld bc,(v_shade)
        call fill_seg
dc_w2:  ld a,(v_wtop)           ; and below the old bottom
        ld c,a
        ld a,(v_wh)
        add a,c
        ld c,(ix+NCOL)
        sub c
        jr c,dc_wx
        jr z,dc_wx
        push af
        ld a,c
        call row_addr
        pop af
        ld bc,(v_shade)
        call fill_seg
        jr dc_wx
dc_wf:  ld (ix+3*NCOL),a
        ld a,(v_wtop)
        call row_addr
        ld bc,(v_shade)
        ld a,(v_wh)
        call fill_seg
dc_wx:
        ; floor rows new bottom .. previous bottom - 1
        ld a,(v_wtop)
        ld c,a
        ld a,(v_wh)
        add a,c
        ld e,a                  ; new bottom
        ld a,(ix+NCOL)
        sub e
        jr c,dc_nf
        jr z,dc_nf
        push af
        ld a,e
        call row_addr
        pop af
        ld bc,(FLOOR_O << 8) | FLOOR_E
        call fill_seg
dc_nf:  ld a,(v_wtop)
        ld (ix+0),a
        ld c,a
        ld a,(v_wh)
        add a,c
        ld (ix+NCOL),a
        ret

; A = view row -> v_row = A, HL = column address of that row, DE = 40
row_addr:
        ld (v_row),a
        ld l,a
        ld h,ROWLO >> 8
        ld e,(hl)
        inc h
        ld d,(hl)
        ld hl,(v_vaddr)
        add hl,de
        ld de,40
        ret

; A = rows, B = even row byte, C = odd row byte, HL = vram, DE = 40.
; Rows are counted from v_row (absolute view row) so the checkerboard lines up.
fill_seg:
        or a
        ret z
        push hl
        ld l,a                  ; n
        ld a,(v_row)
        ld h,a
        add a,l
        ld (v_row),a
        ld a,VH
        sub l                   ; first block entry used
        xor h
        and 1
        jr z,fs_ns
        ld a,b
        ld b,c
        ld c,a
fs_ns:  ld a,l
        add a,a                     ; 2 bytes a row
        ld l,a
        ld a,fill_end & 0FFh
        sub l
        ld (fs_jp+1),a
        ld a,fill_end >> 8
        sbc a,0
        ld (fs_jp+2),a
        pop hl
fs_jp:  jp 0
fill_blk:
#include "fps_fill.inc"
fill_end:
        ret

#ifdef VTEST
; ============================================================================
;  speech chip test: keys 1-9, 0, A, B play the voices, P = PSG shot + voice together
; ============================================================================
voice_test:
        ld a,80h
        ld (v_tgt_h),a
        xor a
        ld (v_page),a
        out (0B0h),a            ; show page 8000h
        ld hl,8000h
        ld de,8001h
        ld bc,3FFFh
        ld (hl),0
        ldir
        ld a,15
        call set_color
        ld hl,vt_s0
        ld de,(2 << 8) | 8
        call draw_text
        ld a,7
        call set_color
        ld hl,vt_s1
        ld e,24
vt_l1:  ld a,(hl)
        or a
        jr z,vt_l2
        push de
        ld d,4
        push hl
        call draw_text
        pop hl
vt_l3:  ld a,(hl)               ; skip past this string
        inc hl
        or a
        jr nz,vt_l3
        pop de
        ld a,e
        add a,8
        ld e,a
        jr vt_l1
vt_l2:  xor a
        ld (v_lastkey),a
vt_lp0: ld a,(v_lastkey)
        or a
        jr z,vt_show
        ld b,a
        xor a
        ld (v_lastkey),a
        ld a,b
        and 0DFh
        cp 'P'
        jr z,vt_both
        ld a,b
        cp 'A'
        jr c,vt_k0
        and 0DFh
        sub 'A'-10                  ; A, B = the eleventh, twelfth voice
        jr vt_k2
vt_k0:  cp '0'
        jr nz,vt_k1
        ld a,'9'+1                  ; 0 = the tenth voice
vt_k1:  sub '1'
        jr c,vt_show
vt_k2:  cp NVOICE
        jr nc,vt_show
        call voice_play
        jr vt_show
vt_both:
        call snd_shot
        xor a
        call voice_play
vt_show:
        ld a,14
        call set_color
        ld a,(v_vt_st)          ; last status seen while feeding
        ld de,(24 << 8) | 128
        call draw_num3
        in a,(0E0h)             ; status now
        ld de,(24 << 8) | 136
        call draw_num3
        jr vt_lp0

vt_s0:  defb "DARK CITADEL  VOICE TEST",0
vt_s1:  defb "1 HUSK HIT",0
        defb "2 HUSK DIE",0
        defb "3 HUSK CLAW",0
        defb "4 ORB HIT",0
        defb "5 ORB DIE",0
        defb "6 ORB SHOT",0
        defb "7 BRUTE HIT",0
        defb "8 BRUTE DIE",0
        defb "9 STALK HIT",0
        defb "0 STALK DIE",0
        defb "A WARDEN HIT  B WARDEN DIE",0
        defb "P PSG SHOT + HUSK HIT",0
        defb " ",0
        defb "STATUS (FEEDING)",0
        defb "STATUS (NOW)",0
        defb 0
#endif

; ============================================================================
;  system: timer and key interrupts, input
; ============================================================================
isr_timer:
        push af
        push hl
        ld hl,(v_ticks)
        inc hl
        ld (v_ticks),hl
        ld a,(v_timing)         ; play time: seconds on this floor / this game
        or a
        jr z,it_t
        ld hl,v_tsub
        dec (hl)
        jr nz,it_t
        ld (hl),250             ; every 0.5 s
        ld hl,v_thalf
        ld a,(hl)
        xor 1
        ld (hl),a
        jr nz,it_t
        ld hl,(v_fsecs)
        inc hl
        ld (v_fsecs),hl
        ld hl,(v_gsecs)
        inc hl
        ld (v_gsecs),hl
it_t:   ld hl,(v_vptr)          ; speech chip waiting for a frame?
        ld a,h
        or l
        jr z,it_0
        push bc
        call voice_tick
        pop bc
it_0:   ld hl,v_sndcnt
        dec (hl)
        jr nz,it_1
        ld (hl),8
        push bc
        call sfx_tick
        pop bc
it_1:   pop hl
        pop af
        ei
        reti
isr_key:
        push af
        call subin
        ld (v_lastkey),a
        pop af
        ei
        reti
isr_strig:
        push af
        call subin
        ld (v_stick),a
        ld a,1
        ld (v_stk_ok),a
        pop af
        ei
        reti
isr_dummy:
        ei
        reti

subout:
        push af
        ld a,08h
        out (93h),a
so_1:   in a,(92h)
        and 08h
        jr z,so_1
so_2:   in a,(92h)
        and 80h
        jr z,so_2
        ld a,09h
        out (93h),a
        pop af
        out (90h),a
        ret
subin:
        ld a,0Ch
        out (93h),a
sbi_1:  in a,(92h)
        and 08h
        jr z,sbi_1
sbi_2:  in a,(92h)
        and 20h
        jr z,sbi_2
        ld a,0Dh
        out (93h),a
        in a,(90h)
        ret

; v_inp bits: 0 up, 1 down, 2 left, 3 right, 4 fire, 5 alt, 6 stop
; The keyboard is asked now and the answer awaited, so this frame acts on
; the keys as they are now (not as they were one frame ago).
read_input:
        push hl
        xor a
        ld (v_stk_ok),a
        di
        ld a,06h
        call subout
        ei
        ld hl,2000              ; give up after ~25 ms (keeps the old value)
ri_w:   ld a,(v_stk_ok)
        or a
        jr nz,ri_0
        dec hl
        ld a,h
        or l
        jr nz,ri_w
ri_0:   pop hl
        ld a,(v_stick)
        ld c,a
        ld b,0
        bit 2,c
        jr z,ri_1
        set 0,b
ri_1:   bit 3,c
        jr z,ri_2
        set 1,b
ri_2:   bit 5,c
        jr z,ri_3
        set 2,b
ri_3:   bit 4,c
        jr z,ri_4
        set 3,b
ri_4:   bit 7,c
        jr z,ri_5
        set 4,b
ri_5:   bit 0,c
        jr z,ri_5a
        set 5,b
ri_5a:  bit 1,c                 ; STOP
        jr z,ri_6
        set 6,b
ri_6:   di
        ld a,15
        out (0A0h),a
        ld a,0C0h
        out (0A1h),a
        ld a,14
        out (0A0h),a
        in a,(0A2h)
        ei
        cpl
        and 3Fh
        or b
        ld b,a
        ld a,(v_inp)
        ld (v_inp_prev),a
        cpl
        and b
        ld (v_inp_new),a
        ld a,b
        ld (v_inp),a
        ret

; ----------------------------------------------------------------------------
;  speech chip (uPD7752, external parameter mode): enemy voices
;  A voice is a list of 7-byte frames (10 ms each), ended by a frame whose
;  repeat count (top 5 bits of the first byte) is 0.
; ----------------------------------------------------------------------------
; A = voice number: start it (cutting off any voice in progress)
voice_play:
        push hl
        push de
        push bc
        ld e,a
        ld d,0
        ld hl,voice_pri
        add hl,de
        ld b,(hl)               ; rank of the new voice
        ld hl,voice_tbl
        add hl,de
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        di
        ld hl,(v_vptr)
        ld a,h
        or l
        jr z,vp_0               ; nothing playing
        ld a,(v_vprio)
        cp b
        jr z,vp_0
        jr nc,vp_x              ; a more important voice is playing
vp_0:   ld a,b
        ld (v_vprio),a
        ld hl,0
        ld (v_vptr),hl
        in a,(0E0h)
        rlca
        jr nc,vp_2              ; idle
        ld a,0FFh               ; busy: stop it first
        out (0E3h),a
        ld b,0
vp_1:   in a,(0E0h)
        rlca
        jr nc,vp_2
        djnz vp_1
vp_2:   xor a                   ; mode: 10 ms frames, normal speed
        out (0E2h),a
        ld a,0FEh               ; external parameters
        out (0E3h),a
        ld (v_vptr),de          ; the timer interrupt feeds the frames
vp_x:   ei
        pop bc
        pop de
        pop hl
        ret

; timer interrupt (HL = v_vptr, not 0): send the next frame when asked
voice_tick:
        in a,(0E0h)
        ld (v_vt_st),a
        bit 4,a
        jr nz,vt_stop           ; error: give up on this voice
        bit 6,a
        ret z                   ; no request yet
        ld a,(hl)
        and 0F8h
        ld c,a                  ; repeat count (0 = last frame)
        ld b,7
vt_lp:  push bc
        ld b,0
vt_w:   in a,(0E0h)
        bit 6,a
        jr nz,vt_ok
        djnz vt_w
        pop bc
        jr vt_stop              ; the chip stopped asking
vt_ok:  pop bc
        ld a,(hl)
        out (0E0h),a
        inc hl
        djnz vt_lp
        ld a,c
        or a
        jr z,vt_stop            ; that was the end frame
        ld (v_vptr),hl
        ret
vt_stop:
        ld hl,0
        ld (v_vptr),hl
        ret

psg_init:
        di
        ld b,14
        ld c,0
pi_1:   ld a,c
        out (0A0h),a
        xor a
        out (0A1h),a
        inc c
        djnz pi_1
        ld a,7
        out (0A0h),a
        ld a,0BBh               ; tone C on (music), the rest off;
        ld (v_mix),a            ; port B out, port A in (joystick)
        out (0A1h),a
        ld hl,0
        ld (v_sfx_p),hl
        ld (v_sfx_p+2),hl
        ld (v_sfx_p+4),hl
        ld (v_bgm_p),hl
        ei
        ret

set_back:
        ld a,(v_page)
        or a
        ld a,0C0h
        jr z,sb_1
        ld a,80h
sb_1:   ld (v_back_h),a
        ret

; flip pages; also measures frames per second
wait_flip:
wf_1:   ld hl,(v_ticks)
        ld de,(v_frame_tk)
        or a
        sbc hl,de
        ld a,h
        or a
        jr nz,wf_2
        ld a,l
        cp FRAME_TICKS
        jr c,wf_1
wf_2:   ld hl,(v_ticks)
        ld (v_frame_tk),hl
        ld a,(v_page)
        xor 2
        ld (v_page),a
        out (0B0h),a
        ret

; ---- text (3x5 font, 4 px cells) ----
set_color:
        push hl
        push de
        ld e,a
        and 3
        ld hl,pat4
        add a,l
        ld l,a
        jr nc,sc_1
        inc h
sc_1:   ld a,(hl)
        ld (v_t_p0),a
        ld a,e
        rrca
        rrca
        and 3
        ld hl,pat4
        add a,l
        ld l,a
        jr nc,sc_2
        inc h
sc_2:   ld a,(hl)
        ld (v_t_p1),a
        pop de
        pop hl
        ret
pat4:   defb 00h,55h,0AAh,0FFh

vaddr:
        ld l,e
        ld h,0
        add hl,hl
        ld bc,ROWTBL
        add hl,bc
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld c,d
        ld b,0
        add hl,bc
        ld a,(v_tgt_h)
        add a,h
        ld h,a
        ret

draw_text:
        push hl
        call vaddr
        ld (v_t_dst),hl
        pop hl
dt_lp:  ld a,(hl)
        or a
        ret z
        inc hl
        push hl
        call draw_glyph
        ld hl,(v_t_dst)
        inc hl
        ld (v_t_dst),hl
        pop hl
        jr dt_lp

draw_glyph:
        sub 32
        ld e,a
        ld d,0
        ld hl,font_map
        add hl,de
        ld a,(hl)
        ld l,a
        ld h,0
        ld e,l
        ld d,h
        add hl,hl
        add hl,hl
        add hl,de
        ld de,font_data
        add hl,de
        ex de,hl
        ld hl,(v_t_dst)
        ld b,5
dg_1:   ld a,(de)
        ld c,a
        ld a,(v_t_p0)
        and c
        ld (hl),a
        set 5,h
        ld a,(v_t_p1)
        and c
        ld (hl),a
        res 5,h
        inc de
        ld a,l
        add a,40
        ld l,a
        jr nc,dg_2
        inc h
dg_2:   djnz dg_1
        ret

draw_num2:
        ld c,0
dn_1:   cp 10
        jr c,dn_2
        sub 10
        inc c
        jr dn_1
dn_2:   push af
        push bc
        call vaddr
        ld (v_t_dst),hl
        pop bc
        ld a,c
        add a,'0'
        call dn_g
        pop af
        add a,'0'
dn_g:   call draw_glyph
        ld hl,(v_t_dst)
        inc hl
        ld (v_t_dst),hl
        ret

s_title: defb "DARK CITADEL",0
s_help:  defb "SPC:FIRE  SHIFT:WEAPON",0

#include "fps_game.asm"
#include "fps_data.inc"
; Everything from here on is used only at the start, before the screens are
; cleared: it may lie beyond 7FFFh (loaded over the BASIC loader's text).
rt_end:
#include "fps_boot.inc"
#include "fps_blob.inc"

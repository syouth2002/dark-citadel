"""Tables and test data for DARK CITADEL (original raycasting FPS prototype).

Outputs src/fps_vars.inc and src/fps_data.inc
Angles: 256 units per turn.  Positions: 8.8 fixed point, 1.0 = one map cell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font                          # the 3x5 font
import fps_levels                     # the floors (and NOBJ)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

NCOL = 32                 # view columns (4 px each -> 128 px)
VH = 112                  # view height in rows
FOV = 60.0                # degrees
# projection distance: horizontal pixels / tan(fov/2); rows are ~1.5x shorter
PROJ_ROWS = (NCOL * 4 / 2) / math.tan(math.radians(FOV / 2)) * 1.5

# ---------------------------------------------------------------- levels
# 24x24 maps (original layouts, made by fps_levels.py).  Legend:
#   '.' floor   '1' '2' '3' walls   'D' door   'O' orange-key door
#   'V' violet-key door   'X' exit panel (a wall you walk into)
#   'P' player start (facing east)   'h' husk   'e' sentinel eye
#   'b' brute (from floor 4)   's' stalker (from floor 7)   'w' the warden (the last floor)
#   'l' lantern oil (from floor 3)
#   '+' health   'a' ammo   'o' orange key   'v' violet key
MAPN = 24                 # floor size (cells); rows are 32 apart in RAM
MAPS = 32
CELL = {'.': 0, '1': 1, '2': 2, '3': 3, 'D': 4, 'O': 5, 'V': 6, 'X': 7}
OBJ = {'h': 1, 'e': 2, 'b': 3, 's': 4, 'w': 5, '+': 6, 'a': 7, 'o': 8, 'v': 9, 'l': 10,
       'g': 11, 't': 12, 'k': 13}


def parse_level(rows):
    assert len(rows) == MAPN and all(len(r) == MAPN for r in rows)
    cells, objs, start = [], [], None
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == 'P':
                start = (x, y)
                cells.append(0)
            elif ch in OBJ:
                objs.append((OBJ[ch], x, y))
                cells.append(0)
            else:
                cells.append(CELL[ch])
    assert start
    return cells, objs, start


def check_level(cells, objs, start):
    """walk the level picking up keys; the exit must become reachable"""
    keys = set()                     # door cells (5 orange, 6 violet) that can be opened
    keyat = {(x, y): {8: 5, 9: 6}[ty] for ty, x, y in objs if ty in (8, 9)}
    while True:
        seen, todo, touched_exit = {start}, [start], False
        while todo:
            x, y = todo.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                c = cells[ny * MAPN + nx]
                if c == 7:
                    touched_exit = True
                ok = c == 0 or c == 4 or (c == 5 and 5 in keys) or (c == 6 and 6 in keys)
                if ok and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    todo.append((nx, ny))
        new = {ty for (kx, ky), ty in keyat.items() if (kx, ky) in seen} - keys
        if touched_exit:
            for ty, x, y in objs:
                assert (x, y) in seen, ('unreachable object', ty, x, y)
            return
        assert new, 'exit not reachable'
        keys |= new


VARS = [
    ('ticks', 2), ('frame_tk', 2), ('sndcnt', 1), ('page', 1), ('back_h', 1), ('tgt_h', 1),
    ('stick', 1), ('inp', 1), ('inp_prev', 1), ('inp_new', 1), ('lastkey', 1), ('rng', 2),
    ('t_p0', 1), ('t_p1', 1), ('t_dst', 2), ('frame', 1),
    ('px', 2), ('py', 2), ('pa', 1),
    # ray state
    ('col', 1), ('ra', 1), ('rdx', 2), ('rdy', 2), ('ddx', 2), ('ddy', 2),
    ('sdx', 2), ('sdy', 2), ('stx', 1), ('sty', 1), ('mx', 1), ('my', 1), ('side', 1),
    ('hit', 1), ('dist', 2), ('edge', 2), ('row', 1), ('shade', 2), ('wh', 1), ('wtop', 1), ('vaddr', 2),
    ('zbuf', NCOL * 2),
    ('ptop0', NCOL), ('pbot0', NCOL), ('cdirty0', NCOL), ('pshd0', NCOL),  # (in this order)
    ('ptop1', NCOL), ('pbot1', NCOL), ('cdirty1', NCOL), ('pshd1', NCOL),
    ('pose0', 5), ('pose1', 5), ('posel', 5), ('vfull', 1), ('rvpart', 1), ('rvdp', 2),
    # game
    ('hp', 1), ('ammo', 1), ('kills', 1), ('nenemy', 1), ('fire_cd', 1), ('flash', 1),
    ('hud_dirty', 1), ('dead', 1), ('hurt', 1),
    ('enemies', fps_levels.NOBJ * 16),         # (NEN slots of 16 bytes)
    ('map', 32 * 24), ('seen', 32 * 24),  # (seen: 300h after map, cast_ray)
    ('level', 1), ('keys', 1), ('items', 1), ('nitems', 1), ('lvdone', 1),
    ('msg', 2), ('msg_t', 1), ('grp', 1), ('mm_dirty', 1), ('pcell', 2),
    # sprite drawing temporaries
    ('s_ptr', 2), ('s_cs', 1), ('s_ce', 1), ('s_top', 1), ('s_hs', 1), ('s_ws', 1),
    ('s_dep', 2), ('s_u', 2), ('s_du', 2), ('s_runs', 12), ('s_skip', 1), ('s_col', 1),
    ('e_dx', 2), ('e_dy', 2), ('e_lat', 2), ('e_sgn', 1), ('t_cnt', 1),
    ('sfx_p', 6), ('mix', 1), ('stk_ok', 1), ('vptr', 2), ('vt_st', 1), ('vprio', 1), ('qv', 2),
    ('mm_ox', 1), ('mm_oy', 1), ('mm_x', 1), ('mm_wy', 1),
    ('newn', 1), ('newq', 64),
    ('timing', 1), ('tsub', 1), ('thalf', 1), ('fsecs', 2), ('gsecs', 2), ('best', 6),
    ('deaths', 1), ('tkills', 2), ('record', 1),
    ('debug', 1), ('god', 1), ('startlv', 1), ('cheat', 1), ('dsel', 1), ('dfloor', 1),
    ('dsnd', 1), ('dchoice', 1), ('boss', 1), ('bossix', 2), ('bmus', 1), ('bmus_t', 1), ('firelock', 1), ('weapon', 1),
    ('smap', 2), ('flashix', 2), ('flasht', 1), ('oil', 2), ('paused', 1), ('hdir', 1), ('hdirt', 1),
    ('pw', 1), ('pwhp', 1), ('pwammo', 1), ('pwtext', 12), ('pwbits', 7), ('pwpos', 1), ('pwsecs', 2), ('pwkills', 2),
    ('pwdeaths', 1), ('pwdiff', 1), ('diff', 1), ('hcnt', 1), ('acnt', 1), ('xdone', 1), ('nobj', 1), ('pwn', 1), ('eskip', 1), ('wimg0', 2), ('wimg1', 2),
    ('bgm_p', 2), ('bgm_s', 2), ('bgm_t', 1), ('bgm_v', 1),
]
VARS_BASE = 0x0400


RAM_TABLES = [('cos_tbl', 0x1400), ('sin_tbl', 0x1600), ('ddx_tbl', 0x1800), ('ddy_tbl', 0x1A00),
              ('ht_near', 0x1C00), ('ht_far', 0x1D00), ('spr_hs', 0x1D80), ('spr_top', 0x1E00)]
TEX_RAM = 0x1E80                     # unpacked sprite textures (25 x 96 bytes)
RAM_DATA = None                      # the low-RAM data: just after the sprites (main)


def rle(cells):
    """runs (cell << 4 | length-1), never across the end of a row"""
    out = []
    for y in range(MAPN):
        row = cells[y * MAPN:(y + 1) * MAPN]
        i = 0
        while i < MAPN:
            j = i
            while j < MAPN and row[j] == row[i] and j - i < 16:
                j += 1
            out.append((row[i] << 4) | (j - i - 1))
            i = j
    return out


def height_tables():
    """the start-up tables as gen_tables computes them (integer arithmetic)"""
    pk = int(PROJ_ROWS * 256)
    near = [min(VH, (pk + (i * 8 + 4) // 2) // (i * 8 + 4)) for i in range(256)]
    far = [min(VH, (pk + (i * 64 + 32) // 2) // (i * 64 + 32)) for i in range(128)]
    s_hs, s_top = [], []
    for i in range(128):
        h = min(320, (pk + (i * 4 + 2) // 2) // (i * 4 + 2))
        hs = h - (h >> 2)
        s_hs.append(hs)
        s_top.append(((h + VH) // 2 - hs) & 255)
    return near, far, s_hs, s_top


def s16(v):
    return int(round(v)) & 0xFFFF


def main():
    vl = ['; generated by tools/fps_gen.py - do not edit']
    a = VARS_BASE
    va = {}
    for n, s in VARS:
        vl.append('%-12s equ 0%04Xh' % ('v_' + n, a))
        va[n] = a
        a += s
    # cast_ray relies on these: the seen record 300h after the map cell, and
    # the zbuf inside one page
    assert va['seen'] - va['map'] == 0x300
    assert (va['zbuf'] & 255) + 2 * NCOL <= 256, 'zbuf crosses a page'
    vl.append('VARS_END     equ 0%04Xh' % a)
    vl.append('NEN          equ %d' % fps_levels.NOBJ)
    assert a <= 0x1000, 'the variables run into the tables at 1000h'
    vl.append('NCOL         equ %d' % NCOL)
    vl.append('VH           equ %d' % VH)
    open(os.path.join(SRC, 'fps_vars.inc'), 'w').write('\n'.join(vl) + '\n')

    d = ['; generated by tools/fps_gen.py - do not edit']
    # cos / sin (signed 8.8)
    cs = [s16(256 * math.cos(2 * math.pi * i / 256)) for i in range(256)]
    sn = [s16(256 * math.sin(2 * math.pi * i / 256)) for i in range(256)]
    # The full tables are built at start-up in RAM (gen_tables in fps.asm):
    # only a quarter wave is stored, the rest follows by symmetry.
    for nm, addr in RAM_TABLES:
        d.append('%-12s equ 0%04Xh' % (nm, addr))
    d.append('q_cos:                         ; cos, angles 0..64')
    for i in range(0, 65, 16):
        d.append('        defw ' + ','.join(str(v) for v in cs[i:min(65, i + 16)]))
    # |1/cos| and |1/sin| in 8.8, clamped
    def inv(v):
        v = abs(v)
        return 0x7FFF if v < 1e-3 else min(0x7FFF, int(round(256 / v)))
    dx = [inv(math.cos(2 * math.pi * i / 256)) for i in range(256)]
    dy = [inv(math.sin(2 * math.pi * i / 256)) for i in range(256)]
    d.append('q_ddx:                         ; |1/cos|, angles 0..64')
    for i in range(0, 65, 16):
        d.append('        defw ' + ','.join(str(v) for v in dx[i:min(65, i + 16)]))
    # per column: angle offset (256 units) and cos(offset) as 0..256 fraction
    half = math.tan(math.radians(FOV / 2))
    offs, cosc = [], []
    for c in range(NCOL):
        camx = ((c + 0.5) / NCOL * 2 - 1) * half
        ang = math.atan(camx)
        offs.append(int(round(ang / (2 * math.pi) * 256)) & 0xFF)
        cosc.append(min(255, int(round(math.cos(ang) * 256))))
    d.append('col_ang:')
    d.append('        defb ' + ','.join(str(v) for v in offs))
    d.append('col_cos:')
    d.append('        defb ' + ','.join(str(v) for v in cosc))
    d.append('PROJ_K       equ %d     ; wall rows at distance 1.0, times 256' % int(PROJ_ROWS * 256))
    # wall patterns (plane 0 bytes, colours 0..3 of the level's plane-1 group)
    # [type 1..3][side 0/1][distance band 0..3] -> (even row byte, odd row byte)
    # two colours are mixed as a checkerboard so mixes look like an even tone
    def chk(a_, b_):
        even = (a_ << 6) | (b_ << 4) | (a_ << 2) | b_
        odd = (b_ << 6) | (a_ << 4) | (b_ << 2) | a_
        return [even, odd]
    def solid(c):
        return c * 0x55

    def stripe(a_, b_):                      # horizontal lines: even rows a, odd rows b
        return [solid(a_), solid(b_)]
    def d25(c):                              # a quarter of the pixels
        return [chk(c, 0)[0], 0]

    def d75(c):                              # three quarters
        return [solid(c), chk(c, 0)[1]]
    kinds = [(2, 1), (3, 1), (1, 0)]
    d.append('wall_pat:')
    # Light falls off with distance, but a wall inside the lantern's reach is
    # never drawn black (black is the darkness beyond it).  Side 1 is one
    # step darker than side 0.
    for a_, m in kinds:                      # plain walls 1..3
        if m:
            ladder = [chk(a_, a_), chk(a_, m), chk(m, m), chk(m, 0), d25(m)]
        else:                                # one colour: by pixel density
            ladder = [chk(a_, a_), d75(a_), chk(a_, 0), d25(a_), d25(a_)]
        s0 = sum(ladder[0:4], [])
        s1 = sum(ladder[1:5], [])
        assert all(s0[i] or s0[i + 1] for i in range(0, 8, 2)) and             all(s1[i] or s1[i + 1] for i in range(0, 8, 2)), 'a black wall band'
        d.append('        defb ' + ','.join('0%02Xh' % v for v in s0 + s1))
    # 4 door, 5 orange-key door, 6 violet-key door: striped; 7 exit: bright checker
    for a_, b_ in ((2, 0), (2, 3), (1, 3)):
        s0 = stripe(a_, b_) * 3 + stripe(1, 0)
        s1 = stripe(a_, b_) * 2 + stripe(a_, 0) + stripe(1, 0)
        d.append('        defb ' + ','.join('0%02Xh' % v for v in s0 + s1))
    s0 = chk(3, 2) + chk(3, 2) + chk(3, 1) + chk(2, 1)
    d.append('        defb ' + ','.join('0%02Xh' % v for v in s0 + s0))
    fe, fo = 0x40, 0x04          # floor: sparse purple dots (darker than any wall)
    d.append('FLOOR_E      equ 0%02Xh' % fe)
    d.append('FLOOR_O      equ 0%02Xh' % fo)
    # wall height (rows) from perpendicular distance (8.8): near table by perp>>3,
    # far table by perp>>6 (perp >= 8 cells)
    # These are computed at start-up (gen_tables); see height_tables() for
    # the same values in Python.  Sprites nearer than 2 cells use their own
    # tables, not limited to the view height (the drawing clips them).
    # ---- sprites: 8 x 12 texels, '.' transparent, 0..3 colours of the view group
    #      (0 black, 1 purple, 2 orange, 3 pink).  Original designs.
    SPR = {
        # crawling husk: hunched body, glowing eyes, long claws
        'HUSK1': ["..1111..",
                  ".111111.",
                  ".121121.",
                  ".111111.",
                  "..1001..",
                  "3.1111.3",
                  "31111113",
                  "3.1111.3",
                  "..1111..",
                  "..1..1..",
                  ".11..11.",
                  ".00..00."],
        'HUSK2': ["..1111..",
                  ".111111.",
                  ".121121.",
                  ".111111.",
                  "..1001..",
                  ".311113.",
                  ".311113.",
                  "..1111..",
                  "..1111..",
                  "...11...",
                  "..1..1..",
                  "..0..0.."],
        'HUSKA': ["3......3",
                  "31.11.13",
                  ".311113.",
                  ".122221.",
                  ".100001.",
                  "..1111..",
                  "..1111..",
                  "..1111..",
                  "..1111..",
                  "..1..1..",
                  ".11..11.",
                  ".00..00."],
        'HUSKD': ["........",
                  "........",
                  "........",
                  "........",
                  "........",
                  "........",
                  "........",
                  "........",
                  "...3....",
                  ".1111...",
                  "31111113",
                  "00000000"],
        # floating sentinel eye
        'ORB1': ["........",
                 "..3333..",
                 ".311113.",
                 "31122113",
                 "31200213",
                 "31122113",
                 ".311113.",
                 "..3333..",
                 "...11...",
                 "..1..1..",
                 "........",
                 "........"],
        'ORB2': ["........",
                 "..3333..",
                 ".311113.",
                 "31122113",
                 "31222213",
                 "31122113",
                 ".311113.",
                 "..3333..",
                 "..1..1..",
                 "...11...",
                 "........",
                 "........"],
        'ORBA': ["..2..2..",
                 "2.3333.2",
                 ".322223.",
                 "32222223",
                 "32233223",
                 "32222223",
                 ".322223.",
                 "2.3333.2",
                 "...11...",
                 "..1..1..",
                 "........",
                 "........"],
        'ORBD': ["........",
                 "........",
                 "........",
                 "........",
                 "........",
                 "........",
                 "........",
                 "........",
                 "..3..3..",
                 ".31.113.",
                 "3110113.",
                 ".000000."],
    }
    SPR.update({
        # brute: a broad armoured hulk with a small head
        'BRUTE1': ["..3333..",
                   ".311113.",
                   ".312213.",
                   "33111133",
                   "31111113",
                   "31100113",
                   "31111113",
                   "33111133",
                   ".311113.",
                   ".11..11.",
                   ".11..11.",
                   "000..000"],
        'BRUTE2': ["..3333..",
                   ".311113.",
                   ".312213.",
                   "33111133",
                   "31111113",
                   "31100113",
                   "31111113",
                   "33111133",
                   ".311113.",
                   "..11.11.",
                   "..11.11.",
                   ".000.000"],
        'BRUTEA': ["3......3",
                   "33.33.33",
                   ".311113.",
                   ".312213.",
                   "31111113",
                   "31100113",
                   "31111113",
                   ".311113.",
                   ".311113.",
                   ".11..11.",
                   ".11..11.",
                   "000..000"],
        'BRUTED': ["........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "..3333..",
                   ".311113.",
                   "33111133",
                   "00000000"],
        # stalker: thin and crouching, long limbs, glowing eyes
        'STALK1': ["........",
                   "........",
                   "...11...",
                   "..1221..",
                   "...11...",
                   "..1111..",
                   ".1.11.1.",
                   "1..11..1",
                   "...11...",
                   "..1..1..",
                   ".1....1.",
                   "1......1"],
        'STALK2': ["........",
                   "........",
                   "...11...",
                   "..1221..",
                   "...11...",
                   "..1111..",
                   ".1.11.1.",
                   ".1.11.1.",
                   "...11...",
                   "...11...",
                   "..1..1..",
                   "..1..1.."],
        'STALKA': ["........",
                   "...11...",
                   "..1221..",
                   "3..11..3",
                   ".311113.",
                   "...11...",
                   "...11...",
                   "..1111..",
                   ".1....1.",
                   "1......1",
                   "........",
                   "........"],
        'STALKD': ["........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   ".2......",
                   "1.1111.1",
                   ".111111."],
    })
    SPR.update({
        # the warden (floor 12): horned, armoured, a glowing core
        'WARDEN1': ["3......3",
                    "31....13",
                    ".311113.",
                    ".312213.",
                    "33111133",
                    "31122113",
                    "31233213",
                    "31122113",
                    "33111133",
                    ".311113.",
                    ".11..11.",
                    "000..000"],
        'WARDEN2': ["3......3",
                    "31....13",
                    ".311113.",
                    ".312213.",
                    "33111133",
                    "31122113",
                    "31233213",
                    "31122113",
                    "33111133",
                    ".311113.",
                    "..11.11.",
                    ".000.000"],
        'WARDENA': ["32....23",
                    "31.33.13",
                    ".311113.",
                    ".312213.",
                    "31111113",
                    "31233213",
                    "32333323",
                    "31233213",
                    "31111113",
                    ".311113.",
                    ".11..11.",
                    "000..000"],
        'WARDEND': ["........",
                    "........",
                    "........",
                    "........",
                    "........",
                    "........",
                    "........",
                    "........",
                    "3..33..3",
                    ".311113.",
                    "33122133",
                    "00000000"],
    })
    SPR.update({
        # bloater (from floor 5): a bulbous sac on stubby legs; swollen, it
        # glows and cracks; burst, a splash on the floor
        'BLOAT1': ["........",
                   "..1111..",
                   ".111111.",
                   "11211211",
                   "11111111",
                   "11133111",
                   "11111111",
                   ".111111.",
                   "..1111..",
                   "..1111..",
                   ".1....1.",
                   ".0....0."],
        'BLOAT2': ["........",
                   "........",
                   "..1111..",
                   ".111111.",
                   "11211211",
                   "11111111",
                   "11133111",
                   "11111111",
                   ".111111.",
                   "..1111..",
                   "..1..1..",
                   "..0..0.."],
        'BLOATA': ["..3333..",
                   ".311113.",
                   "31211213",
                   "31111113",
                   "31322313",
                   "31111113",
                   "31311313",
                   "31111113",
                   ".311113.",
                   "..3333..",
                   ".1....1.",
                   ".0....0."],
        'BLOATD': ["........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "3..3...3",
                   ".3.33.3.",
                   "23322332",
                   "00000000"],
        # lamp turret (from floor 9): a stone pillar with a glowing lens
        'TUR1':   ["..2222..",
                   ".233332.",
                   "..2332..",
                   "...22...",
                   "..1111..",
                   "..1001..",
                   "..1111..",
                   "..1001..",
                   "..1111..",
                   ".111111.",
                   ".111111.",
                   "00000000"],
        'TURA':   ["2.2222.2",
                   ".233332.",
                   "22333322",
                   ".233332.",
                   "...22...",
                   "..1111..",
                   "..1001..",
                   "..1111..",
                   "..1111..",
                   ".111111.",
                   ".111111.",
                   "00000000"],
        'TURD':   ["........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "..2.....",
                   ".1101...",
                   ".111101.",
                   "00000000"],
        # bat (from floor 3): flies high, wings up and down; fallen, on the floor
        'BAT1':   ["1......1",
                   "11.11.11",
                   ".112211.",
                   "..1111..",
                   "...11...",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........"],
        'BAT2':   ["........",
                   "...11...",
                   ".112211.",
                   "11.11.11",
                   "1......1",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........"],
        'BATD':   ["........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "........",
                   "..1221..",
                   ".11..11."],
    })
    E = "........"
    SPR.update({
        'HEALTH': [E] * 6 + [".111111.", ".113311.", ".133331.", ".113311.", ".111111.", E],
        'AMMO':   [E] * 6 + [".222222.", ".200002.", ".222222.", ".200002.", ".222222.", E],
        'KEYO':   [E] * 4 + ["..222...", ".2...2..", "..222...", "...2....", "...222..",
                             "...2....", "...22...", E],
        'KEYV':   [E] * 4 + ["..333...", ".3...3..", "..333...", "...3....", "...333..",
                             "...3....", "...33...", E],
        # lantern oil: a small flask with a stopper
        'OIL':    [E] * 4 + ["...33...", "...11...", "..2112..", ".211112.", ".211112.",
                             ".222222.", "..2222..", E],
    })
    # (items glow by a colour change while drawn: no frames of their own)
    # sprite textures: unpacked at start-up to TEX_RAM, 96 bytes each (row
    # major, FFh = transparent).  Stored as nibbles (Fh = transparent); the
    # glowing item frames are made from the plain ones (colours 1, 2 -> 3).
    # the warden's frames first: they go just below the others (TEX_RAM)
    names = [n for n in SPR if n.startswith('WARDEN')] + [n for n in SPR if not n.startswith('WARDEN')]
    global RAM_DATA
    RAM_DATA = TEX_RAM + len(names) * 96
    for k, name in enumerate(names):
        d.append('tex_%-10s equ 0%04Xh' % (name.lower(), TEX_RAM + k * 96))
    assert TEX_RAM + len(names) * 96 <= RAM_DATA, 'sprites run into the RAM data'
    d.append('NTEX_PACKED  equ %d' % len(names))
    d.append('TEX_RAM      equ 0%04Xh' % TEX_RAM)
    packed = []
    for name in names:
        rows = SPR[name]
        assert len(rows) == 12 and all(len(r) == 8 for r in rows), name
        nib = [15 if ch == '.' else int(ch) for r in rows for ch in r]
        packed += [(nib[k] << 4) | nib[k + 1] for k in range(0, 96, 2)]
    assert RAM_DATA + len(packed) <= 0x3F00
    # ... and the nibbles are LZ-compressed as well (tools/lz.py, unlz)
    import lz
    blob = lz.compress(bytes(packed))
    d.append('tex_pack_lz:                   ; %d bytes of nibbles' % len(packed))
    for k in range(0, len(blob), 24):
        d.append('        defb ' + ','.join('0%02Xh' % v for v in blob[k:k + 24]))
    # per enemy type: walk frame 1, walk frame 2, attack, dead
    d.append('tex_tbl:')
    d.append('        defw tex_husk1,tex_husk2,tex_huska,tex_huskd')
    d.append('        defw tex_orb1,tex_orb2,tex_orba,tex_orbd')
    d.append('        defw tex_brute1,tex_brute2,tex_brutea,tex_bruted')
    d.append('        defw tex_stalk1,tex_stalk2,tex_stalka,tex_stalkd')
    d.append('        defw tex_warden1,tex_warden2,tex_wardena,tex_wardend')
    for nm in ('health', 'ammo', 'keyo', 'keyv', 'oil'):     # (+8000h: glowing)
        d.append('        defw tex_%s,tex_%s+8000h,tex_%s,tex_%s+8000h' % ((nm,) * 4))
    d.append('        defw tex_bloat1,tex_bloat2,tex_bloata,tex_bloatd')  # (11)
    d.append('        defw tex_tur1,tex_tur1,tex_tura,tex_turd')          # (12)
    d.append('        defw tex_bat1,tex_bat2,tex_bat2,tex_batd')          # (13)
    # ---- weapon: 16 x 24 pixels at the bottom centre of the view (bytes 14..17).
    #      One barrel on the centre line; the muzzle flash is a single burst.
    #      '.' transparent, 0..3 colours of the view group.  Original design.
    GUN = ["................",
           "................",
           "................",
           "................",
           "................",
           "................",
           ".......33.......",
           ".......22.......",
           ".......22.......",
           "......1221......",
           "......1221......",
           "......1221......",
           ".....112211.....",
           ".....111111.....",
           "....11100111....",
           "....11100111....",
           "....11111111....",
           "...1113333111...",
           "...1111111111...",
           "...1111111111...",
           "....11111111....",
           ".....100001.....",
           ".....100001.....",
           ".....100001....."]
    FLASH = ["......2222......",
             ".....233332.....",
             "......2332......",
             ".......33......."]
    gun_f = GUN[:2] + FLASH + GUN[6:]
    # the axe: held up at the right; swung down across the view.  Original.
    AXE = ["................",
           "................",
           "................",
           "................",
           "................",
           "................",
           "........3333....",
           ".......333333...",
           "......33311333..",
           "......3331.333..",
           ".......33..33...",
           "..........2.....",
           "..........2.....",
           ".........2......",
           ".........2......",
           "........2.......",
           "........2.......",
           ".......22.......",
           ".......22.......",
           "......222.......",
           "......222.......",
           ".....2222.......",
           ".....2222.......",
           ".....2222......."]
    AXES = ["................",
            "................",
            "..1.............",
            "...1............",
            "....1...........",
            ".....1..........",
            "......1.........",
            "........333.....",
            ".......33333....",
            "......333.333...",
            ".....3331.33....",
            "......33.33.....",
            ".......2........",
            "........2.......",
            ".........2......",
            "..........2.....",
            "...........2....",
            "...........22...",
            "...........22...",
            "..........222...",
            "..........222...",
            ".........2222...",
            ".........2222...",
            ".........2222..."]
    for name, rows in (('gun', GUN), ('gunf', gun_f), ('axe', AXE), ('axes', AXES)):
        assert len(rows) == 24 and all(len(r) == 16 for r in rows), name
        d.append('tex_%s:                       ; per row 4 x (mask, plane0)' % name)
        for r in rows:
            out = []
            for bcol in range(4):
                mask = data = 0
                for k in range(4):
                    ch = r[bcol * 4 + k]
                    sh = 6 - 2 * k
                    if ch == '.':
                        mask |= 3 << sh
                    else:
                        data |= int(ch) << sh
                out += [mask, data]
            d.append('        defb ' + ','.join('0%02Xh' % v for v in out))
    # ---- levels: floors 1-3 hand made, 4-12 generated at build time (fixed seeds)
    all_levels = fps_levels.all_levels()
    d.append('MAPN         equ %d' % MAPN)
    d.append('MAPS         equ %d' % MAPS)
    d.append('NLEVEL       equ %d' % len(all_levels))
    import fps_mapcode                     # walls as runs, objects in 2 bytes
    # the extra enemies of NORMAL / HARD, by floor (kept in low RAM)
    d.append('extra_tbl:                    ; per floor: count, then objects (2 bytes)')
    d.append('        defw ' + ','.join('ext%d' % i for i in range(len(all_levels))))
    for i in range(len(all_levels)):
        ex = fps_levels.EXTRAS[i + 1]
        d.append('ext%d:   defb %d' % (i, len(ex)) + ''.join(',%d' % v for v in fps_mapcode.encode_objs(ex)))
    d.append('level_tbl:                    ; map (packed), objects, count, start x, start y, plane-1 byte')
    for i, (grp, rows) in enumerate(all_levels):
        cells, objs, (sx, sy) = parse_level(rows)
        check_level(cells, objs, (sx, sy))
        assert len(objs) <= 24, i
        d.append('        defw lv%d_map,lv%d_obj' % (i, i))
        d.append('        defb %d,%d,%d,0%02Xh' % (len(objs), sx, sy, grp * 0x55))
    import fps_mapcode                     # walls as runs, objects in 2 bytes
    for i, (grp, rows) in enumerate(all_levels):
        cells, objs, start = parse_level(rows)
        mb = fps_mapcode.encode_map(cells)
        ob = fps_mapcode.encode_objs(objs)
        d.append('lv%d_map:                      ; wall runs, FFh, special cells, FFh' % i)
        for k in range(0, len(mb), 18):
            d.append('        defb ' + ','.join('0%02Xh' % v for v in mb[k:k + 18]))
        d.append('lv%d_obj:' % i)
        for k in range(0, len(ob), 18):
            d.append('        defb ' + ','.join('0%02Xh' % v for v in ob[k:k + 18]))
    # overview picture of every floor (for checking the layouts)
    try:
        from PIL import Image
        col = {'.': (20, 20, 20), '1': (150, 150, 150), '2': (120, 120, 170), '3': (170, 120, 120),
               'D': (255, 170, 0), 'O': (255, 255, 0), 'V': (255, 0, 255), 'X': (0, 255, 0),
               'P': (255, 255, 255), 'h': (255, 60, 60), 'e': (255, 60, 200), '+': (0, 200, 255),
               'a': (0, 150, 255), 'o': (255, 255, 0), 'v': (255, 0, 255),
               'b': (255, 140, 40), 's': (160, 255, 60), 'w': (255, 255, 255),
               'l': (255, 200, 120), 'g': (120, 255, 120), 't': (255, 255, 160), 'k': (200, 160, 255)}
        S = MAPN + 1
        rows_n = (len(all_levels) + 6) // 7
        im = Image.new('RGB', (7 * S * 6, rows_n * S * 6), (60, 60, 60))
        px = im.load()
        for i, (grp, rows) in enumerate(all_levels):
            ox, oy = (i % 7) * S * 6, (i // 7) * S * 6
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    c = col[ch]
                    small = ch in 'Phebsw+aovlgtk'
                    for dy in range(6):
                        for dx in range(6):
                            inner = 1 <= dx <= 4 and 1 <= dy <= 4
                            px[ox + x * 6 + dx, oy + y * 6 + dy] = c if (inner or not small) else col['.']
        os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
        im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(os.path.join(ROOT, 'build', 'floors_preview.png'))
    except ImportError:
        pass
    # font
    d.append('font_map:')
    fm = [0] * 96
    for i, ch in enumerate(font.FONT_ORDER):
        fm[ord(ch) - 32] = i
    for i in range(0, 96, 16):
        d.append('        defb ' + ','.join(str(v) for v in fm[i:i + 16]))
    d.append('font_data:')
    for ch in font.FONT_ORDER:
        d.append('        defb ' + ','.join('0%02Xh' % font.font_mask(r) for r in font.FONT[ch]))
    # the title logo (tools/fps_logo.py): rows from VY0, one LZ stream a plane
    import fps_logo
    for name, plane in zip(('logo_p0', 'logo_p1'), fps_logo.planes(fps_logo.logo())):
        z = lz.compress(plane)
        assert lz.decompress(z) == plane
        d.append('%s:                       ; the title logo, %d bytes -> %d' % (name, len(plane), len(z)))
        for k in range(0, len(z), 24):
            d.append('        defb ' + ','.join('0%02Xh' % v for v in z[k:k + 24]))
    # The weapon pictures live in low RAM: assembled apart (src/fps_ram.asm,
    # org RAM_DATA) with the voices and the music, and stored compressed
    # (build_fps.py).  The floors stay in the program.
    cut = d.index(next(l for l in d if l.startswith('tex_gun:')))
    lvl = d.index(next(l for l in d if l.startswith('level_tbl:')))
    ram = ['        org 0%04Xh' % RAM_DATA] + [l for l in d[cut:lvl] if ' equ ' not in l]
    d = d[:cut] + [l for l in d[cut:lvl] if ' equ ' in l] + d[lvl:]
    # Used only at the start (before the screens are cleared): the table
    # seeds, the column tables and the packed sprites go after rt_end, at
    # the end of the program, where they may lie beyond 7FFFh (fps_boot.inc)
    boot = []
    for first, upto in (('q_cos:', 'PROJ_K '), ('tex_pack_lz:', 'tex_tbl:')):
        i0 = next(i for i, l in enumerate(d) if l.startswith(first))
        i1 = next(i for i, l in enumerate(d) if l.startswith(upto))
        boot += [l for l in d[i0:i1] if ' equ ' not in l]
        d = d[:i0] + [l for l in d[i0:i1] if ' equ ' in l] + d[i1:]
    open(os.path.join(SRC, 'fps_data.inc'), 'w').write('\n'.join(d) + '\n')
    open(os.path.join(SRC, 'fps_boot.inc'), 'w').write('\n'.join(
        ['; generated by tools/fps_gen.py - do not edit (used only at the start)'] + boot) + '\n')
    open(os.path.join(SRC, 'fps_ram.inc'), 'w').write('\n'.join(
        ['; generated by tools/fps_gen.py - do not edit (assembled at RAM_DATA)'] + ram) + '\n')
    import voices                     # original voices for the speech chip
    open(os.path.join(SRC, 'fps_voice.inc'), 'w').write(voices.asm())
    import music                      # original background music
    open(os.path.join(SRC, 'fps_music.inc'), 'w').write(music.asm())
    print('vars end %04X, proj rows %.1f' % (a, PROJ_ROWS))


if __name__ == '__main__':
    main()

"""Tables built at start-up (gen_tables) must equal their definitions."""
import math
import os
import re
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_gen

ROOT = H.ROOT
data = ''.join(open(os.path.join(ROOT, 'src', f)).read() for f in ('fps_data.inc', 'fps_boot.inc'))
EQ = {m.group(1): int(m.group(2), 16)
      for m in re.finditer(r'(\w+)\s+equ\s+0?([0-9A-F]+)h', data)}
EQ['NTEX_PACKED'] = int(re.search(r'NTEX_PACKED\s+equ\s+(\d+)', data).group(1))
V = {}
for l in open(os.path.join(ROOT, 'src', 'fps_vars.inc')):
    if l.startswith('v_'):
        n, _, v = l.split()
        V[n[2:]] = int(v.rstrip('h'), 16)


def defb(lbl):
    m = re.search(r'\n' + lbl + r':[^\n]*\n((?:        defb [^\n]*\n)+)', data)
    return [int(x.strip()[:-1], 16) if x.strip().endswith('h') else int(x)
            for l in m.group(1).strip().split('\n')
            for x in l.split('defb', 1)[1].split(';')[0].split(',')]


p6 = H.P6(open(os.path.join(ROOT, 'build', 'fps.bin'), 'rb').read())
m = p6.mem
H.fps_start(p6)
ok = True


def check(name, cond):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name)


def words(a, n=256):
    return [m[a + 2 * i] | m[a + 2 * i + 1] << 8 for i in range(n)]


def inv(v):
    v = abs(v)
    return 0x7FFF if v < 1e-3 else min(0x7FFF, int(round(256 / v)))


ang = [2 * math.pi * i / 256 for i in range(256)]
check('cos', words(EQ['cos_tbl']) == [fps_gen.s16(256 * math.cos(a)) for a in ang])
check('sin', words(EQ['sin_tbl']) == [fps_gen.s16(256 * math.sin(a)) for a in ang])
check('|1/cos|', words(EQ['ddx_tbl']) == [inv(math.cos(a)) for a in ang])
check('|1/sin|', words(EQ['ddy_tbl']) == [inv(math.sin(a)) for a in ang])
ref = fps_gen.height_tables()
for k, (nm, n) in enumerate((('ht_near', 256), ('ht_far', 128), ('spr_hs', 128), ('spr_top', 128))):
    check(nm, list(m[EQ[nm]:EQ[nm] + n]) == ref[k])
import lz
nib = []
for x in lz.decompress(bytes(defb('tex_pack_lz'))):
    nib += [x >> 4, x & 15]
nib = [255 if v == 15 else v for v in nib]
check('every sprite stored (%d of %d)' % (len(nib) // 96, EQ['NTEX_PACKED']), len(nib) == EQ['NTEX_PACKED'] * 96)
check('sprite textures', list(m[EQ['TEX_RAM']:EQ['TEX_RAM'] + len(nib)]) == nib)
ram = open(os.path.join(ROOT, 'build', 'fps_ram.bin'), 'rb').read()
RAM_DATA = fps_gen.RAM_DATA
check('low-RAM data (weapons, floors, voices, music) unpacked intact',
      bytes(m[RAM_DATA:RAM_DATA + len(ram)]) == ram)
import fps_levels
cells, _, _ = fps_gen.parse_level(fps_levels.all_levels()[0][1])
N, S = fps_gen.MAPN, fps_gen.MAPS
check('floor 1 map unpacked', all(m[V['map'] + y * S + x] == cells[y * N + x] for y in range(N) for x in range(N)))
print('ALL OK' if ok else 'SOME FAILED')

"""Map panel: window centred on the player; auto map of what the lantern lit."""
import math
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H

ROOT = H.ROOT
code = open(os.path.join(ROOT, 'build', 'fps.bin'), 'rb').read()
V = {}
for l in open(os.path.join(ROOT, 'src', 'fps_vars.inc')):
    if l.startswith('v_'):
        n, _, v = l.split()
        V[n[2:]] = int(v.rstrip('h'), 16)
LANTERN = 5
MM_Y, MM_X = 142, 30
MM_W, MM_H, CX, CY = 20, 19, 10, 9
COLOUR = [0, 7, 7, 7, 2, 14, 11, 12]
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def frame(p6, k=0, n=1):
    for _ in range(n):
        p6.stick = k
        c = len(p6.flips)
        s = 0
        while len(p6.flips) == c and s < 2000000:
            p6.run_cycles(4000)
            s += 4000


def panel(p6, base):
    out = []
    for wy in range(MM_H):
        rows = []
        for r in range(3):
            row = []
            for wb in range(MM_W // 2):
                a = base + (MM_Y + wy * 3 + r) * 40 + MM_X + wb
                p0, p1 = p6.mem[a], p6.mem[a + 0x2000]
                for k in range(2):
                    sh = 6 - 4 * k
                    v0, v1 = (p0 >> sh) & 3, (p1 >> sh) & 3
                    assert (p0 >> (sh - 2)) & 3 == v0 and (p1 >> (sh - 2)) & 3 == v1
                    row.append(v0 | v1 << 2)
            rows.append(row)
        assert rows[0] == rows[1] == rows[2]
        out.append(rows[0])
    return out


def expected(m):
    px, py = m[V['px'] + 1], m[V['py'] + 1]
    out = []
    for wy in range(MM_H):
        row = []
        for wx in range(MM_W):
            x, y = px - CX + wx, py - CY + wy
            if (wx, wy) == (CX, CY):
                row.append(15)
            elif 0 <= x < 24 and 0 <= y < 24 and m[V['seen'] + y * 32 + x]:
                row.append(COLOUR[m[V['map'] + y * 32 + x]])
            else:
                row.append(0)
        out.append(row)
    return out


p6 = H.P6(code)
H.fps_start(p6)
m = p6.mem
frame(p6, 0, 3)
seen = [i for i in range(32 * 24) if m[V['seen'] + i]]
px, py = (m[V['px'] + 1] * 256 + m[V['px']]) / 256, (m[V['py'] + 1] * 256 + m[V['py']]) / 256
check('lit walls are on the map', len(seen) > 0, '(%d cells)' % len(seen))
check('only walls and doors are recorded', all(m[V['map'] + i] for i in seen))
check('nothing beyond the lantern', all(math.hypot((i & 31) + .5 - px, (i >> 5) + .5 - py) < LANTERN + 1.5
                                        for i in seen))
for pg in (0x8000, 0xC000):
    check('panel on page %04X matches what was seen' % pg, panel(p6, pg) == expected(m))
# turn around: more walls get lit, drawn cell by cell on both pages
n0 = len(seen)
frame(p6, H.K_RIGHT, 32)
frame(p6, 0, 2)
n1 = sum(1 for i in range(32 * 24) if m[V['seen'] + i])
check('turning around maps more', n1 > n0, '(%d -> %d)' % (n0, n1))
for pg in (0x8000, 0xC000):
    check('panel on page %04X still matches' % pg, panel(p6, pg) == expected(m))
# walk: the map scrolls, the player stays in the centre
frame(p6, H.K_UP, 20)
frame(p6, 0, 3)
for pg in (0x8000, 0xC000):
    check('after walking, page %04X matches' % pg, panel(p6, pg) == expected(m))
# a door that was on the map becomes floor when it opens
import fps_testlib as T
g = T.Game()
gm = g.m
g.frame(0, 3)
cells, _, _ = T.level(0)
door = next((x, y) for (x, y), v in sorted(cells.items()) if v == 4)
gm[V['seen'] + door[1] * 32 + door[0]] = 0x80 | COLOUR[4]
g.approach(*door)
g.frame(0, 3)
check('opened door: floor on the map', g.cell(*door) == 0 and gm[V['seen'] + door[1] * 32 + door[0]] == 0x80)
for pg in (0x8000, 0xC000):
    check('after the door, page %04X matches' % pg, panel(g.p6, pg) == expected(gm))
p6.image().crop((440, 270, 640, 400)).resize((400, 260)).save(os.path.join(ROOT, 'build', 'map_panel.png'))
print('ALL OK' if ok else 'SOME FAILED')

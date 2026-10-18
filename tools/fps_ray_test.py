"""Every view column: the game's ray result against an exact ray cast.
A wall nearer (in depth) than the lantern's reach must be drawn at the right
distance, and only what is beyond it may be dark."""
import math
import os
import random
import re
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fps_testlib as T

V = T.V
LANTERN = 5
data = open(os.path.join(T.ROOT, 'src', 'fps_data.inc')).read()


def defb(lbl):
    m = re.search(r'\n' + lbl + r':\n        defb ([^\n]*)', data)
    return [int(x) for x in m.group(1).split(',')]


OFFS, COSC = defb('col_ang'), defb('col_cos')


def cast(cells, x, y, ang):
    """exact DDA: ray length to the first non-floor cell"""
    dx, dy = math.cos(ang), math.sin(ang)
    mx, my = int(x), int(y)
    ddx = abs(1 / dx) if dx else 1e9
    ddy = abs(1 / dy) if dy else 1e9
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    tx = ((mx + 1 - x) if dx > 0 else (x - mx)) * ddx
    ty = ((my + 1 - y) if dy > 0 else (y - my)) * ddy
    while True:
        if tx < ty:
            mx += sx
            r = tx
            tx += ddx
        else:
            my += sy
            r = ty
            ty += ddy
        if cells.get((mx, my), 1):
            return r


g = T.Game()
m = g.m
g.frame(0, 4)
for i in range(24):                      # no enemies (they would move us)
    m[V['enemies'] + i * 16] = 0
cells, _, _ = T.level(0)
floor = [c for c, v in cells.items() if v == 0]
rnd = random.Random(7)
bad_dark = bad_dist = bad_lit = cols = 0
examples = []
for n in range(80):
    cx, cy = rnd.choice(floor)
    x, y = cx + rnd.uniform(0.25, 0.75), cy + rnd.uniform(0.25, 0.75)
    pa = rnd.randrange(256)
    g.put(x, y, pa)
    g.frame(0, 2)
    x, y = g.getw('px') / 256, g.getw('py') / 256
    for c in range(32):
        ra = (pa + OFFS[c]) & 255
        r = cast(cells, x, y, 2 * math.pi * ra / 256)
        z = (m[V['zbuf'] + 2 * c] | m[V['zbuf'] + 2 * c + 1] << 8) / 256
        want = r * COSC[c] / 256                 # depth of the wall
        dark = LANTERN
        cols += 1
        if want < LANTERN - 0.05:
            if abs(z - dark) < 1e-6:
                bad_dark += 1
                examples.append(('dark but wall at depth %.2f' % want, x, y, pa, c))
            elif abs(z - max(want, 40 / 256)) > 0.08:
                bad_dist += 1
                examples.append(('wall %.2f drawn at %.2f' % (want, z), x, y, pa, c))
        elif want > LANTERN + 0.05 and abs(z - dark) > 1e-6:
            bad_lit += 1
            examples.append(('lit beyond the lantern %.2f, z %.2f' % (want, z), x, y, pa, c))
print('%d columns: %d dark although a wall is in reach, %d at a wrong distance, %d lit beyond'
      % (cols, bad_dark, bad_dist, bad_lit))
for e in examples[:8]:
    print('  %s  at (%.2f, %.2f) angle %d column %d' % e)
ok = bad_dark == 0 and bad_lit == 0 and bad_dist <= cols // 200
print('ALL OK' if ok else 'SOME FAILED')

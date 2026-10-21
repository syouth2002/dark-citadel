"""Lantern oil, the hit flash, pause, the mark of where a blow came from."""
import os
import re
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
NL = len(T.LEVELS)      # floors
LAST = NL - 1           # the last (the warden's), as an index

V = T.V
E = V['enemies']
OIL = 10
ok = True
MAP = {}
for line in open(os.path.join(T.ROOT, 'build', 'fps.map')):
    a, _, n = line.strip().partition(': ')
    MAP[n.strip().lstrip('.')] = int(a, 16)


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def lantern(m):
    return m[MAP['lt_c1'] + 1], m[MAP['ray_c1'] + 1], m[MAP['ray_c2'] + 1], m[MAP['lt_c2'] + 2]


def to_floor(g, lv):
    g.m[V['level']] = lv - 1
    g.m[V['lvdone']] = 1
    g.frame(0, 2)
    g.frame(H.K_SPACE, 2)
    g.frame(0, 3)


# ---- oil: floors 3 on have one; it makes the lantern reach 7 cells a while
for lv in range(NL):
    _, objs, _ = T.level(lv)
    n = sum(1 for ty, x, y in objs if ty == OIL)
    if n != (1 if lv >= 2 else 0):
        check('oil on floor %d' % (lv + 1), False, str(n))
g = T.Game()
m = g.m
check('the lantern: 5 cells (rays up to 6)', lantern(m) == (5, 6, 6, 5), str(lantern(m)))
to_floor(g, 2)
_, objs, _ = T.level(2)
ox, oy = next((x, y) for ty, x, y in objs if ty == OIL)
g.approach(ox, oy)
check('oil picked up: 7 cells (rays up to 9)', lantern(m) == (7, 9, 9, 7) and g.getw('oil') > 300,
      str(lantern(m)))
check('message', 'LANTERN OIL' in g.msg())
for _ in range(6):                           # (until it holds: the game may be
    g.setw('oil', 3)                         # in the middle of burning it)
    g.frame(0, 1)
    if g.getw('oil') <= 3:
        break
g.frame(0, 5)
check('burnt out: 5 cells again', lantern(m) == (5, 6, 6, 5) and g.getw('oil') == 0)
# ---- every pickup is drawn (plain and glowing)
cells1, _, _ = T.level(2)
ax, ay = T.find_open(cells1, 5, 3)
for i in range(24):
    if m[E + i * 16]:
        m[E + i * 16] = 0
g.put(ax + 0.5, ay + 1.5, 0)
g.frame(0, 2)
base = [0x8000, 0xC000][(g.p6.b0 >> 1) & 1]
empty = bytes(m[base + 4 * 40:base + 116 * 40])
for ty, name in ((6, 'health'), (7, 'ammo'), (8, 'orange key'), (9, 'violet key'), (10, 'oil')):
    drawn = []
    for k in range(4):
        g.setw('px', (ax + 0.5) * 256)
        g.setw('py', (ay + 1.5) * 256)
        m[V['pa']] = 0
        x, y = int((ax + 2.0) * 256), int((ay + 1.5) * 256)
        m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5], m[E + 6] = ty, x & 255, x >> 8, y & 255, y >> 8, 0, 0
        g.frame()
        base = [0x8000, 0xC000][(g.p6.b0 >> 1) & 1]
        view = bytes(m[base + 4 * 40:base + 116 * 40])
        drawn.append(sum(1 for a, b in zip(view, empty) if a != b))
    m[E] = 0
    check('%s drawn' % name, min(drawn) > 20, str(drawn))
g.frame(0, 2)

# ---- the hit flash and where blows come from
cells, _, _ = T.level(2)
fx, fy = T.find_open(cells, 5, 5)
cx, cy = fx + 2.5, fy + 2.5                  # the player in the middle, facing east
for i in range(24):
    if 1 <= m[E + i * 16] <= 5:
        m[E + i * 16] = 0
m[V['god']] = 1
for side, (dx, dy) in ((1, (1, 0)), (2, (0, 1)), (3, (-1, 0)), (4, (0, -1))):
    m[V['hdir']] = 0
    got = None
    for f in range(80):
        g.setw('px', cx * 256)
        g.setw('py', cy * 256)
        m[V['pa']] = 0
        x, y = int((cx + dx * 0.9) * 256), int((cy + dy * 0.9) * 256)
        m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5] = 1, x & 255, x >> 8, y & 255, y >> 8, 9
        if m[E + 6] == 0:
            m[E + 6] = 1
        g.frame()
        if m[V['hdir']]:
            got = m[V['hdir']]
            break
    check('a blow from %s is marked so' % ['', 'ahead', 'the right', 'behind', 'the left'][side],
          got == side, '(%s)' % got)
# the mark is drawn (left edge, the view's brightest colour)
m[V['hdir']] = 4
m[V['hdirt']] = 4
m[E] = 0
g.frame(0, 1)
base = [0x8000, 0xC000][(g.p6.b0 >> 1) & 1]
col0 = [m[base + (4 + 24 + r) * 40] for r in range(64)]
check('the mark at the left edge', all(v == 0xFF for v in col0))
g.frame(0, 4)
col0 = [m[base + (4 + 24 + r) * 40] for r in range(64)]
check('and gone after a while', not all(v == 0xFF for v in col0))
# a hit flashes the enemy
m[V['ammo']] = 50
for f in range(40):
    g.setw('px', cx * 256)
    g.setw('py', cy * 256)
    m[V['pa']] = 0
    x, y = int((cx + 2.0) * 256), int(cy * 256)
    m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5], m[E + 7] = 3, x & 255, x >> 8, y & 255, y >> 8, 8, 0
    g.frame(H.K_SPACE if f % 2 else 0)
    if m[E + 5] < 8:
        break
check('a hit enemy flashes', m[V['flasht']] > 0 and g.getw('flashix') == E)
# ---- far objects are skipped, but never one in sight
import math
import random
g7 = T.Game()
m7 = g7.m
to_floor(g7, 7)
m7[V['god']] = 1
cells7, _, _ = T.level(6)
floor7 = [c for c, v in cells7.items() if v == 0]
rnd = random.Random(5)
missed = seen = 0
for n in range(40):
    cx7, cy7 = rnd.choice(floor7)
    pa = rnd.randrange(256)
    g7.put(cx7 + 0.5, cy7 + 0.5, pa)
    for i in range(24):                      # hold every enemy still
        if 1 <= m7[E + i * 16] <= 5:
            m7[E + i * 16 + 6] = 4 if m7[E + i * 16 + 6] >= 3 else 0
    g7.frame(0, 1)
    px, py = g7.getw('px') / 256, g7.getw('py') / 256
    a = 2 * math.pi * m7[V['pa']] / 256
    for i in range(24):
        b = E + i * 16
        if not m7[b]:
            continue
        dx = (m7[b + 1] | m7[b + 2] << 8) / 256 - px
        dy = (m7[b + 3] | m7[b + 4] << 8) / 256 - py
        depth = dx * math.cos(a) + dy * math.sin(a)
        lat = dy * math.cos(a) - dx * math.sin(a)
        if 0.5 < depth < 4.5 and abs(lat) < 0.5 * depth:     # (the view: 30 degrees each side)
            seen += 1
            if not m7[b + 13]:
                missed += 1
check('objects in sight are never skipped', missed == 0 and seen > 10, '(%d in sight, %d missed)' % (seen, missed))

# ---- pause
g.frame(0, 2)
t0 = g.getw('gsecs')
n0 = len(g.p6.flips)
g.frame(H.K_STOP, 2)                         # (2: a frame may end before the keys
g.p6.stick = 0                               # are read; it is the press that counts)
n0 = len(g.p6.flips)
g.p6.run_cycles(3993600 * 3)
check('STOP: paused (no frames, the clock stopped, the music silent)',
      m[V['paused']] == 1 and len(g.p6.flips) <= n0 + 1 and g.getw('gsecs') <= t0 + 1 and g.p6.psg[10] == 0)
g.p6.stick = H.K_STOP
g.p6.run_cycles(400000)
g.p6.stick = 0
g.frame(0, 3)
check('STOP again: on we go', m[V['paused']] == 0 and len(g.p6.flips) > n0 + 2)
print('ALL OK' if ok else 'SOME FAILED')

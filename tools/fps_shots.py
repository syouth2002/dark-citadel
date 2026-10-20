"""Screenshots for the README (docs/images), taken from the game running in
the headless model (tools/harness.py).  python tools/fps_shots.py
(docs/images/walk.gif is not made here: it is cut from a recording of real
play in PC6001VW, so that it runs at the real speed.)"""
import math
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
from PIL import Image

V = T.V
E = V['enemies']
CPU = 3993600
OUT = os.path.join(T.ROOT, 'docs', 'images')
NL = len(T.LEVELS)
os.makedirs(OUT, exist_ok=True)


def big(p6):
    # a mode 5 dot is about twice as wide as it is tall on the screen
    return p6.image().resize((640, 400), Image.NEAREST)


def save(p6, name):
    big(p6).save(os.path.join(OUT, name))
    print('saved', name)


def to_floor(g, lv):
    """from floor 1 to floor lv (an index) through the floor-clear screen"""
    if lv:
        g.m[V['level']] = lv - 1
        g.m[V['lvdone']] = 1
        g.frame(0, 2)
        g.frame(H.K_SPACE, 2)
        g.frame(0, 3)


def game():
    """a game at NORMAL (the difficulty most will play), still on floor 1"""
    g = T.Game()
    g.m[V['diff']] = 1
    g.m[V['ammo']] = 30                    # (NORMAL's rounds at the start)
    g.m[V['hud_dirty']] = 2
    return g


def place(g, objs):
    """only these objects on the floor: (type, x, y, state)"""
    m = g.m
    for i in range(T.NEN):
        m[E + i * 16] = 0
    for i, (ty, x, y, st) in enumerate(objs):
        b = E + i * 16
        x, y = int(x * 256), int(y * 256)
        hp = {1: 3, 2: 4, 3: 8, 4: 2}.get(ty, 0)
        m[b], m[b + 1], m[b + 2], m[b + 3], m[b + 4], m[b + 5], m[b + 6] = ty, x & 255, x >> 8, y & 255, y >> 8, hp, st


# ---- the title
p6 = H.P6(T.code())
p6.run_cycles(CPU * 2)
save(p6, 'title.png')

# ---- in the corridors: a husk, a sentinel and a brute ahead, a round fired
g = game()
to_floor(g, 3)
g.god()
g.m[V['god']] = 1
cells, _, _ = T.level(3)
ox, oy = T.find_open(cells, 6, 3)
g.put(ox + 0.5, oy + 1.5, 0)
place(g, [(1, ox + 2.6, oy + 1.1, 0), (2, ox + 3.8, oy + 2.2, 0), (3, ox + 4.9, oy + 1.6, 0),
          (7, ox + 1.7, oy + 2.4, 0)])
g.frame(0, 4)
g.frame(H.K_SPACE, 1)
save(g.p6, 'combat.png')

# ---- the newer foes: a lamp turret lighting up, a bloater, a bat
g = game()
to_floor(g, 9)
g.m[V['god']] = 1
cells, _, _ = T.level(9)
ox, oy = T.find_open(cells, 6, 3)
g.put(ox + 0.5, oy + 1.5, 0)
foes = [(12, ox + 5.3, oy + 1.5, 2), (11, ox + 2.7, oy + 0.8, 0), (13, ox + 3.6, oy + 2.3, 0)]
for k in range(3):                          # (held where they are for the picture)
    place(g, foes)
    for i, hp in ((0, 10), (1, 6), (2, 1)):
        g.m[E + i * 16 + 5] = hp
    g.m[E + 7] = 30                         # (the turret's lens lit)
    g.frame(0, 1)
save(g.p6, 'foes.png')

# ---- exploring: the auto map fills in as the lantern reaches the walls
# (a walk that keeps to the corridors: turn while the way ahead is shut)
g = game()
to_floor(g, 1)
g.m[V['god']] = 1
cells, _, _ = T.level(1)


def open_ahead(d):
    x, y, a = g.getw('px') / 256, g.getw('py') / 256, g.m[V['pa']] * 2 * math.pi / 256
    return all(cells.get((int(x + math.cos(a) * s), int(y + math.sin(a) * s)), 1) == 0
               for s in (0.4, d / 2, d))


frames, depth = [], []
turn = 0
for f in range(170):
    if turn:
        k, turn = H.K_RIGHT, turn - 1
    elif not open_ahead(1.4):
        k, turn = H.K_RIGHT, 5
    else:
        k = H.K_UP if f % 40 < 34 else H.K_LEFT
    g.frame(k)
    im = big(g.p6)
    frames.append(im)
    z = [(g.m[V['zbuf'] + 2 * c] | g.m[V['zbuf'] + 2 * c + 1] << 8) / 256 for c in range(32)]
    mean = sum(z) / 32
    depth.append(sum((v - mean) ** 2 for v in z) + mean)   # varied, and deep
best = max(range(60, len(frames)), key=lambda i: depth[i])
frames[best].save(os.path.join(OUT, 'explore.png'))
print('saved explore.png (frame %d)' % best)

# ---- the warden on the last floor, its health gauge half gone
g = game()
to_floor(g, NL - 1)
m = g.m
g.m[V['god']] = 1
cells, objs, _ = T.level(NL - 1)
wx, wy = next((x, y) for ty, x, y in objs if ty == 5)
for i in range(T.NEN):                        # the warden alone
    if 1 <= m[E + i * 16] <= 4:
        m[E + i * 16] = 0
b = next(E + i * 16 for i in range(T.NEN) if m[E + i * 16] == 5)
spot = None
for k in (4, 3):
    for dx, dy, ang in ((-1, 0, 0), (1, 0, 128), (0, -1, 64), (0, 1, 192)):
        cs = [(wx + dx * i, wy + dy * i) for i in range(1, k + 1)]
        if all(cells.get(c) == 0 for c in cs):
            spot = (cs[-1], ang)
            break
    if spot:
        break
(sx, sy), ang = spot
bx, by = m[b + 1] | m[b + 2] << 8, m[b + 3] | m[b + 4] << 8
m[V['ammo']] = 99
for f in range(120):
    g.setw('px', (sx + 0.5) * 256)
    g.setw('py', (sy + 0.5) * 256)
    m[V['pa']] = ang
    m[b + 1], m[b + 2], m[b + 3], m[b + 4] = bx & 255, bx >> 8, by & 255, by >> 8
    m[V['hp']] = 100
    if m[b + 5] <= 14:
        break
    g.frame(H.K_SPACE if f % 2 == 0 else 0)
g.frame(0, 2)
save(g.p6, 'warden.png')

# ---- a floor cleared (floor 2): the tally and the password for the next floor
g = game()
to_floor(g, 1)
g.m[V['god']] = 1
cells, _, _ = T.level(1)
ex = next((x, y) for (x, y), v in cells.items() if v == 7)
g.approach(*ex)
g.p6.run_cycles(CPU)
save(g.p6, 'tally.png')

# ---- the ending: dawn over the citadel (the warden gone, out by the exit)
g = game()
to_floor(g, NL - 1)
m = g.m
m[V['god']] = 1
for i in range(T.NEN):
    if m[E + i * 16] == 5:
        m[E + i * 16] = 0
m[V['boss']] = 0
cells, _, _ = T.level(NL - 1)
ex = next((x, y) for (x, y), v in cells.items() if v == 7)
g.approach(*ex)
g.p6.run_cycles(CPU * 14)
save(g.p6, 'ending.png')

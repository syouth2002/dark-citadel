"""The axe: SHIFT switches weapons; it needs no rounds, reaches ~1.2 cells,
hits for 2; the gun hands over to it when the last round is fired."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T

V = T.V
E = V['enemies']
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def arena():
    g = T.Game()
    m = g.m
    g.frame(0, 3)
    for i in range(24):
        if 1 <= m[E + i * 16] <= 5:
            m[E + i * 16] = 0
    cells, _, _ = T.level(0)
    ox, oy = T.find_open(cells, 5, 3)
    g.put(ox + 0.5, oy + 1.5, 0)
    m[V['god']] = 1
    return g, m, ox, oy


def weapon_pixels(g):
    m = g.m
    base = [0x8000, 0xC000][(g.p6.b0 >> 1) & 1]
    return bytes(m[base + (4 + 112 - 24 + r) * 40 + 14 + c] for r in range(24) for c in range(4))


def swing_at(g, ox, oy, ty, hp, dist, swings):
    """the enemy held `dist` cells ahead; returns its health after the swings"""
    m = g.m
    m[E], m[E + 5], m[E + 6], m[E + 7] = ty, hp, 1, 0
    x, y = int((ox + 0.5 + dist) * 256), int((oy + 1.5) * 256)
    m[E + 1], m[E + 2], m[E + 3], m[E + 4] = x & 255, x >> 8, y & 255, y >> 8
    g.frame(0)                               # (on screen before the first blow)
    done = 0
    for f in range(swings * 12 + 20):
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        m[V['pa']] = 0
        x, y = int((ox + 0.5 + dist) * 256), int((oy + 1.5) * 256)
        m[E + 1], m[E + 2], m[E + 3], m[E + 4] = x & 255, x >> 8, y & 255, y >> 8
        m[E + 7] = 0                         # (it does not strike back)
        cd = m[V['fire_cd']]
        g.frame(H.K_SPACE if f % 2 == 0 and done < swings else 0)
        if m[V['fire_cd']] > cd:
            done += 1
        if m[E + 6] >= 3 or (done >= swings and m[V['fire_cd']] == 0):
            break
    g.frame(0, 2)                            # (the last blow lands)
    return m[E + 5], m[E + 6], done


# ---- switching
g, m, ox, oy = arena()
check('the game starts with the gun', m[V['weapon']] == 0)
gun_img = weapon_pixels(g)
g.frame(H.K_SHIFT, 2)
g.frame(0, 3)
check('SHIFT: the axe', m[V['weapon']] == 1)
check('the axe is drawn in hand', weapon_pixels(g) != gun_img)
g.frame(0, 4)
g.p6.image().save(os.path.join(T.ROOT, 'build', 'axe.png'))
# ---- swinging costs nothing; it reaches about a cell; hits for 2
a0 = m[V['ammo']]
hp, st, n = swing_at(g, ox, oy, 1, 3, 0.9, 2)
check('two blows fell a husk (3 health) close by', st >= 3 and n == 2, '(health %d, %d blows)' % (hp, n))
check('no rounds used', m[V['ammo']] == a0)
hp, st, n = swing_at(g, ox, oy, 3, 8, 0.9, 1)
check('one blow takes 2 from a brute', hp == 6 and n == 1, '(health %d)' % hp)
hp, st, n = swing_at(g, ox, oy, 1, 3, 2.0, 2)
check('out of reach at 2 cells', hp == 3 and n == 2, '(health %d)' % hp)
g.frame(0, 3)
# ---- back to the gun; the last round hands over to the axe
g.frame(H.K_SHIFT, 2)
g.frame(0, 3)
check('SHIFT again: the gun', m[V['weapon']] == 0)
m[V['ammo']] = 1
g.frame(H.K_SPACE, 2)
g.frame(0, 3)
check('after the last round: the axe', m[V['ammo']] == 0 and m[V['weapon']] == 1)
# ---- a floor started with no rounds: the axe
cells, _, _ = T.level(0)
ex = next((x, y) for (x, y), v in cells.items() if v == 7)
g.approach(*ex)
g.frame(0, 2)
g.frame(H.K_SPACE, 2)
g.frame(0, 3)
check('floor 2 with no rounds starts with the axe', m[V['level']] == 1 and m[V['weapon']] == 1)
print('ALL OK' if ok else 'SOME FAILED')

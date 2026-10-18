"""Slain: choose to continue on the same floor or go back to the title."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
NL = len(T.LEVELS)      # floors
LAST = NL - 1           # the last (the warden's), as an index

V = T.V
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def die(g, lv):
    """a husk claws the player, who has little health left"""
    m = g.m
    cells, _, _ = T.level(lv)
    ox, oy = T.find_open(cells, 4, 3)
    E = V['enemies']
    for i in range(24):
        m[E + i * 16] = 0
    for f in range(80):
        if m[V['dead']]:
            break
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        ex, ey = int((ox + 1.4) * 256), int((oy + 1.5) * 256)
        m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5] = 1, ex & 255, ex >> 8, ey & 255, ey >> 8, 9
        if m[E + 6] == 0:
            m[E + 6] = 1
        m[V['hp']] = min(m[V['hp']], 5)
        g.frame()
    return m[V['dead']] == 1


def press(g, k):
    """hold a key for two frames (one may end before the game reads the keys)"""
    g.frame(k, 2)
    g.frame(0, 2)


g = T.Game()
m = g.m
g.frame(0, 3)
# go to floor 3 first (continue must stay there)
for lv in range(2):
    cells, _, _ = T.level(lv)
    g.approach(*next((x, y) for (x, y), v in cells.items() if v == 7))
    g.frame(0, 2)
    g.frame(H.K_SPACE, 2)
    g.frame(0, 4)
check('on floor 3', m[V['level']] == 2)
check('slain', die(g, 2) and m[V['dchoice']] == 0)
g.frame(0, 3)
g.p6.image().save(os.path.join(T.ROOT, 'build', 'slain.png'))
m[V['ammo']] = 5
press(g, H.K_SPACE)
g.frame(0, 3)
check('CONTINUE: same floor, health back', m[V['dead']] == 0 and m[V['level']] == 2 and m[V['hp']] == 100)
check('CONTINUE on floor 3: at least 36 rounds', m[V['ammo']] == 36, str(m[V['ammo']]))
check('slain again', die(g, 2))
m[V['ammo']] = 50
press(g, H.K_SPACE)
g.frame(0, 3)
check('CONTINUE with more rounds: kept', m[V['ammo']] == 50, str(m[V['ammo']]))
# the last floor: 3 more a floor from 30
m[V['level']] = LAST - 1
m[V['lvdone']] = 1
g.frame(0, 2)
g.frame(H.K_SPACE, 2)
g.frame(0, 3)
check('slain on the last floor', m[V['level']] == LAST and die(g, LAST))
m[V['ammo']] = 0
press(g, H.K_SPACE)
g.frame(0, 3)
check('CONTINUE on the last floor: at least %d rounds' % (30 + 3 * LAST), m[V['ammo']] == 30 + 3 * LAST, str(m[V['ammo']]))
check('slain again', die(g, LAST))
press(g, H.K_RIGHT)
check('right: TITLE chosen', m[V['dchoice']] == 1)
press(g, H.K_LEFT)
check('left: CONTINUE again', m[V['dchoice']] == 0)
press(g, H.K_DOWN)
check('any direction switches', m[V['dchoice']] == 1)
g.p6.stick = H.K_SPACE
g.p6.run_cycles(800000)
g.p6.stick = 0
g.p6.run_cycles(4000000)
n = len(g.p6.flips)
g.p6.run_cycles(4000000)
check('TITLE: the title screen waits (no frames drawn)', len(g.p6.flips) == n and m[V['dead']] == 1)
H.fps_start(g.p6)
g.frame(0, 3)
check('then a new game on floor 1', m[V['level']] == 0 and m[V['dead']] == 0 and m[V['hp']] == 100)
print('ALL OK' if ok else 'SOME FAILED')

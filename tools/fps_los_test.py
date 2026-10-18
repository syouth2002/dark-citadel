"""Enemies must not hurt the player through walls or closed doors.
Positions come from floor 1's data."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fps_testlib as T

V = T.V
ok = True
cells, _, _ = T.level(0)


def scenario(name, player, enemy, etype, expect_hurt, frames=60, door=None):
    """player/enemy: (x, y) in cells (float); the enemy is pinned there, chasing"""
    global ok
    g = T.Game()
    m = g.m
    g.frame(0, 4)
    E = V['enemies']
    for i in range(24):                      # only one enemy: the test subject
        m[E + i * 16] = 0
    if door:
        g.set_cell(door[0], door[1], 4)
    hurt = False
    for f in range(frames):
        g.setw('px', player[0] * 256)
        g.setw('py', player[1] * 256)
        m[V['pa']] = 0
        ex, ey = int(enemy[0] * 256), int(enemy[1] * 256)
        m[E + 0] = etype
        m[E + 1], m[E + 2] = ex & 255, ex >> 8
        m[E + 3], m[E + 4] = ey & 255, ey >> 8
        m[E + 5] = 9
        if m[E + 6] == 0:
            m[E + 6] = 1                     # chasing
        if etype == 2 and m[E + 6] == 1 and m[E + 7] < 28:
            m[E + 7] = 28                    # sentinel about to shoot
        m[V['hp']] = 100
        g.frame()
        if m[V['hp']] < 100:
            hurt = True
            break
    res = hurt == expect_hurt
    ok &= res
    print(('OK   ' if res else 'FAIL ') + '%s (hurt=%s)' % (name, hurt), flush=True)


wx, wy = T.find_between(cells, (1, 2, 3))            # . W .
scenario('husk through a wall', (wx - 0.2, wy + 0.5), (wx + 1.05, wy + 0.5), 1, False)
dx, dy = T.find_between(cells, (4,))                 # . D .
scenario('husk through a closed door', (dx - 0.2, dy + 0.5), (dx + 1.05, dy + 0.5), 1, False,
         door=(dx, dy))
sx, sy = T.find_between(cells, (1, 2, 3), side=2)    # . . W . .
scenario('sentinel through a wall', (sx - 1.5, sy + 0.5), (sx + 2.5, sy + 0.5), 2, False, frames=90)
ox, oy = T.find_open(cells, 4, 3)
scenario('husk in the same room (control)', (ox + 0.5, oy + 1.5), (ox + 1.4, oy + 1.5), 1, True)
scenario('sentinel in the same room (control)', (ox + 0.5, oy + 2.5), (ox + 3.0, oy + 0.5), 2, True,
         frames=150)
print('ALL OK' if ok else 'SOME FAILED')

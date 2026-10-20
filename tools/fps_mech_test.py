"""Mechanics test for DARK CITADEL: doors, keys, pickups, exit, floors, ending.
Positions come from the floor data, so the test follows the layouts."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
NL = len(T.LEVELS)      # floors
LAST = NL - 1           # the last (the warden's), as an index

V = T.V
g = T.Game()
m = g.m
ok = True


def check(name, cond):
    global ok
    print(('OK   ' if cond else 'FAIL ') + name, flush=True)
    ok &= bool(cond)


g.frame(0, 4)
cells, objs, start = T.level(0)
check('floor 1 loaded', m[V['level']] == 0 and all(g.cell(x, y) == v for (x, y), v in cells.items()))
check('padding outside the floor is wall', all(g.cell(x, y) == 1 for y in range(T.N) for x in range(T.N, T.S)))
# a plain door
door = next((x, y) for (x, y), v in sorted(cells.items()) if v == 4)
g.approach(*door)
check('plain door opens', g.cell(*door) == 0)
# the orange door without the key
odoor = next((x, y) for (x, y), v in cells.items() if v == 5)
g.approach(*odoor)
check('locked without key + message', g.cell(*odoor) == 5 and 'ORANGE' in g.msg())
# the orange key
key = next((x, y) for ty, x, y in objs if ty == 8)
g.approach(*key)
check('orange key picked up', m[V['keys']] & 1 and m[V['items']] >= 1)
g.approach(*odoor)
check('orange door opens with key', g.cell(*odoor) == 0)
# ammo
am = next((x, y) for ty, x, y in objs if ty == 7)
a0 = m[V['ammo']]
g.approach(*am)
check('ammo picked up', m[V['ammo']] > a0)
# every floor by its exit
groups = [0x00, 0xAA, 0x55, 0xFF]
for lv in range(NL):
    cells, objs, start = T.level(lv)
    if lv:
        check('floor %d loaded, colour group ok' % (lv + 1),
              m[V['level']] == lv and m[V['grp']] == groups[lv % 4] and
              all(g.cell(x, y) == v for (x, y), v in cells.items()))
    ex = next((x, y) for (x, y), v in cells.items() if v == 7)
    if lv == LAST:                     # the warden (tested in fps_boss_test): gone
        for i in range(24):
            if m[V['enemies'] + i * 16] == 5:
                m[V['enemies'] + i * 16] = 0
        m[V['boss']] = 0
    g.approach(*ex)
    check('floor %d exit' % (lv + 1), m[V['lvdone']] == 1)
    if lv == 0:
        g.p6.image().save(os.path.join(T.ROOT, 'build', 'mech_tally.png'))
        t0 = g.getw('gsecs')
        g.frame(0, 30)
        check('the clock runs on a floor, stops between floors',
              g.getw('fsecs') > 0 and t0 >= g.getw('fsecs') and g.getw('gsecs') == t0)
    if lv == LAST:
        g.leave_ending()             # the dawn, then the tally
    else:
        g.frame(0, 2)
        g.frame(H.K_SPACE, 2)
        g.frame(0, 4)
check('after the ending: back to the title', m[V['level']] == LAST)
check('best time recorded', g.getw('best') == g.getw('gsecs') > 0 and m[V['record']] == 1)
H.fps_start(g.p6)
check('then a new game on floor 1', m[V['level']] == 0 and m[V['hp']] == 100)
ram_end = T.RAM_DATA + len(open(os.path.join(T.ROOT, 'build', 'fps_ram.bin'), 'rb').read())
check('the stack stays clear of the low-RAM data',
      g.p6.min_sp > ram_end + 16)
print('lowest stack %04X, RAM data ends %04X' % (g.p6.min_sp, ram_end))
print('ALL OK' if ok else 'SOME FAILED')

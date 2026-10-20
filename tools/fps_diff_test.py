"""Difficulty (EASY / NORMAL / HARD): chosen on the title with left / right;
the damage taken, the rounds at the start and on CONTINUE, the enemies, the
health and ammo items, the rounds an ammo pickup gives; a best time for each."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
NL = len(T.LEVELS)
LAST = NL - 1

V = T.V
E = V['enemies']
CPU = 3993600
HUSK, T_HEALTH, T_AMMO = 1, 6, 7
NAMES = ('EASY', 'NORMAL', 'HARD')
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def tap(p6, k):
    p6.stick = k
    p6.run_cycles(CPU // 8)
    p6.stick = 0
    p6.run_cycles(CPU // 8)


def game(diff, lv=0):
    """a game at this difficulty from the title, on floor lv"""
    p6 = H.P6(T.code())
    p6.run_cycles(CPU)
    tap(p6, H.K_LEFT)                        # (EASY, then on)
    for _ in range(diff):
        tap(p6, H.K_RIGHT)
    g = T.Game.__new__(T.Game)
    g.p6, g.m = p6, p6.mem
    p6.stick = H.K_SPACE
    p6.run_cycles(CPU // 5)
    p6.stick = 0
    g.frame(0, 2)
    if lv:
        g.m[V['level']] = lv - 1
        g.m[V['lvdone']] = 1
        g.frame(0, 2)
        g.frame(H.K_SPACE, 2)
        g.frame(0, 3)
    return g


# ---- the title: NORMAL at first; right goes on, left back, round and round
p6 = H.P6(T.code())
m = p6.mem
p6.run_cycles(CPU)
seen = [m[V['diff']]]
for k in (H.K_RIGHT, H.K_RIGHT, H.K_RIGHT, H.K_LEFT):
    tap(p6, k)
    seen.append(m[V['diff']])
check('title: NORMAL, right -> HARD -> EASY -> NORMAL, left -> EASY', seen == [1, 2, 0, 1, 0], repr(seen))
p6.image().resize((640, 400)).save(os.path.join(T.ROOT, 'build', 'diff_title.png'))

for d in range(3):
    g = game(d)
    m = g.m
    # ---- rounds at the start (EXPERT: none, the axe)
    want = (50, 30, 0)[d]
    check('%s: %d rounds at the start%s' % (NAMES[d], want, ', the axe' if d == 2 else ''),
          m[V['ammo']] == want and m[V['diff']] == d and (d < 2 or m[V['weapon']] == 1),
          '(%d, weapon %d)' % (m[V['ammo']], m[V['weapon']]))
    # ---- the damage a husk's claw does (8)
    cells, _, _ = T.level(0)
    ox, oy = T.find_open(cells, 5, 3)
    for i in range(T.NEN):
        m[E + i * 16] = 0
    got = None
    for f in range(120):
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        m[V['pa']] = 0
        b = E
        x, y = int((ox + 1.3) * 256), int((oy + 1.5) * 256)
        if f == 0:
            m[b], m[b + 5], m[b + 6], m[b + 7] = HUSK, 3, 1, 0
        m[b + 1], m[b + 2], m[b + 3], m[b + 4] = x & 255, x >> 8, y & 255, y >> 8
        m[V['hp']] = 100
        g.frame()
        if m[V['hp']] < 100:
            got = 100 - m[V['hp']]
            break
    want = (8, 12, 16)[d]
    check('%s: a husk\'s claw takes %d' % (NAMES[d], want), got == want, '(got %s)' % got)
    # ---- an ammo pickup (EXPERT: 6 rounds)
    for i in range(T.NEN):
        m[E + i * 16] = 0
    m[V['ammo']] = 10
    x, y = int((ox + 0.5) * 256), int((oy + 1.5) * 256)
    m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5], m[E + 6] = T_AMMO, x & 255, x >> 8, y & 255, y >> 8, 0, 0
    g.frame(0, 3)
    want = (22, 22, 16)[d]
    check('%s: an ammo pickup gives %d' % (NAMES[d], want - 10), m[V['ammo']] == want, '(%d)' % m[V['ammo']])

# ---- the enemies: NORMAL half as many again (rounded up), HARD twice (the
# warden is still one); health items: every second one gone on NORMAL / HARD;
# ammo items: every second one gone on NORMAL / HARD
for lv in (0, 4, 9, LAST):
    _, objs, _ = T.level(lv)
    k = sum(1 for ty, x, y in objs if 1 <= ty <= 4 or 11 <= ty <= 13)
    w = sum(1 for ty, x, y in objs if ty == 5)
    nh = sum(1 for ty, x, y in objs if ty == T_HEALTH)
    na = sum(1 for ty, x, y in objs if ty == T_AMMO)
    en, hl, am = [], [], []
    for d in range(3):
        g = game(d, lv)
        m = g.m
        slots = [m[E + i * 16] for i in range(T.NEN)]
        en.append((sum(1 for s in slots if 1 <= s <= 5 or 11 <= s <= 13), m[V['nenemy']]))
        hl.append(sum(1 for s in slots if s == T_HEALTH))
        am.append(sum(1 for s in slots if s == T_AMMO))
    want = [k + w, k + (k + 1) // 2 + w, 2 * k + w]
    check('floor %d: enemies %s' % (lv + 1, want), en == [(n, n) for n in want], repr(en))
    check('floor %d: health items %d, %d, %d' % (lv + 1, nh, (nh + 1) // 2, (nh + 1) // 2),
          hl == [nh, (nh + 1) // 2, (nh + 1) // 2], repr(hl))
    check('floor %d: ammo items %d, %d, %d' % (lv + 1, na, (na + 1) // 2, (na + 1) // 2),
          am == [na, (na + 1) // 2, (na + 1) // 2], repr(am))

# ---- CONTINUE on floor 5 with no rounds: NORMAL 42, HARD 28, EXPERT none
for d in range(3):
    g = game(d, 4)
    m = g.m
    cells, _, _ = T.level(4)
    ox, oy = T.find_open(cells, 4, 3)
    for f in range(80):
        if m[V['dead']]:
            break
        for i in range(T.NEN):
            if i:
                m[E + i * 16] = 0
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        x, y = int((ox + 1.4) * 256), int((oy + 1.5) * 256)
        m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5] = HUSK, x & 255, x >> 8, y & 255, y >> 8, 9
        if m[E + 6] == 0:
            m[E + 6] = 1
        m[V['hp']] = min(m[V['hp']], 5)
        g.frame()
    m[V['ammo']] = 0
    g.frame(H.K_SPACE, 2)
    g.frame(0, 4)
    want = (42, 28, 0)[d]
    check('%s: CONTINUE on floor 5 makes the rounds up to %d' % (NAMES[d], want),
          m[V['dead']] == 0 and m[V['level']] == 4 and m[V['ammo']] == want, '(%d)' % m[V['ammo']])

# ---- a best time for each difficulty
g = game(1, LAST)
m = g.m
for i in range(T.NEN):
    if m[E + i * 16] == 5:
        m[E + i * 16] = 0
m[V['boss']] = 0
g.setw('gsecs', 1234)
m[V['lvdone']] = 1
g.frame(0, 1)
best = [m[V['best'] + 2 * i] | m[V['best'] + 2 * i + 1] << 8 for i in range(3)]
check('NORMAL finished: its best time only', best[0] == 0 and best[1] >= 1234 and best[2] == 0, repr(best))
print('ALL OK' if ok else 'SOME FAILED')

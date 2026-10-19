"""Passwords: shown when a floor is cleared; typed on the title (P) they start
that floor with that health, those rounds and that difficulty; a wrong one is
turned away."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
NL = len(T.LEVELS)      # floors
LAST = NL - 1           # the last (the warden's), as an index

V = T.V
CPU = 3993600
ABC = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
KEY = 0x09C5A3
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def ck(f, a, h4, d):
    return (f + a + h4 + f + 3 * d + 7) & 63


def make(floor, hp, ammo, diff=0):
    """the same sums as pw_make (floor = the next floor's number - 1)"""
    hp4 = (hp + 3) // 4
    w = (ck(floor, ammo, hp4, diff) << 18) | (diff << 16) | (floor << 12) | (ammo << 5) | hp4
    w ^= KEY
    return ''.join(ABC[(w >> (5 * i)) & 31] for i in range(5))


def decode(w):
    """(floor, rounds, health/4, difficulty) or None, as pw_check"""
    v = 0
    for i, ch in enumerate(w):
        v |= ABC.index(ch) << (5 * i)
    v = (v & 0xFFFFFF) ^ KEY
    f, a, h4, d, c = (v >> 12) & 15, (v >> 5) & 127, v & 31, (v >> 16) & 3, v >> 18
    if d == 3 or c != ck(f, a, h4, d) or not (1 <= f <= LAST and a <= 99 and 1 <= h4 <= 25):
        return None
    return f, a, h4, d


def key(p6, ch):
    p6.keyq.append(ord(ch))
    p6.pending.append(0x02)
    p6.run_cycles(CPU // 10)


# ---- clear floor 3 with 23 rounds on HARD: the password for floor 4
g = T.Game()
m = g.m
m[V['diff']] = 1
m[V['level']] = 1
m[V['lvdone']] = 1
g.frame(0, 2)
g.frame(H.K_SPACE, 2)
g.frame(0, 3)
cells, _, _ = T.level(2)
ex = next((x, y) for (x, y), v in cells.items() if v == 7)
m[V['hp']] = 37
m[V['ammo']] = 23
g.approach(*ex)
m[V['hp']] = 37
m[V['ammo']] = 23
g.frame(0, 2)
m[V['hud_dirty']] = 2
shown = bytes(m[V['pwtext']:V['pwtext'] + 5]).decode()
# (made as the floor was cleared: 23 rounds; full health - approach() heals)
check('floor cleared: a 5-character password for floor 4, its health, rounds, difficulty',
      m[V['lvdone']] == 1 and decode(shown) == (3, 23, 25, 1), '%s -> %s' % (shown, decode(shown)))

# ---- on the title: P and the password (NORMAL chosen there: the password's wins)
want = make(3, 37, 23, 2)
p6 = H.P6(T.code())
m = p6.mem
p6.run_cycles(CPU)
key(p6, 'P')
for ch in want.lower():                      # (either case)
    key(p6, ch)
p6.run_cycles(CPU // 2)
check('right: floor 4, 40 health, 23 rounds, EXPERT', m[V['level']] == 3 and m[V['hp']] == 40 and
      m[V['ammo']] == 23 and m[V['pw']] == 1 and m[V['diff']] == 2,
      '(floor %d, %d, %d, difficulty %d)' % (m[V['level']] + 1, m[V['hp']], m[V['ammo']], m[V['diff']]))
# ---- a wrong one
p6 = H.P6(T.code())
m = p6.mem
p6.run_cycles(CPU)
bad = next(a + b + c + d + e for a in ABC for b in ABC for c in ABC for d in ABC for e in ABC[:16]
           if decode(a + b + c + d + e) is None)
key(p6, 'P')
for ch in bad:
    key(p6, ch)
p6.run_cycles(CPU * 2)
check('wrong (%s): still on the title' % bad, m[V['pw']] == 0 and len(p6.flips) <= 1)   # (1: set up at boot)
key(p6, 'P')
for ch in make(LAST, 100, 99):               # the last floor, full health, 99 rounds
    key(p6, ch)
p6.run_cycles(CPU // 2)
check('then a right one works: the last floor', m[V['level']] == LAST and m[V['hp']] == 100 and
      m[V['ammo']] == 99 and m[V['diff']] == 0)
# ---- every floor / health / rounds / difficulty comes back the same
bad = 0
for floor in range(1, NL):
    for hp in (1, 4, 50, 99, 100):
        for ammo in (0, 1, 50, 99):
            for diff in (0, 1, 2):
                if decode(make(floor, hp, ammo, diff)) != (floor, ammo, (hp + 3) // 4, diff):
                    bad += 1
check('the code goes both ways (Python model)', bad == 0)
# ---- a mistyped character is caught (one character changed, most of the time)
caught = tot = 0
for floor in (1, 5, LAST):
    w = make(floor, 60, 40, 1)
    for i in range(5):
        for c in ABC[:16] if i == 4 else ABC:
            if c != w[i]:
                tot += 1
                caught += decode(w[:i] + c + w[i + 1:]) is None
check('one wrong character is turned away (%d of %d)' % (caught, tot), caught >= tot * 0.9)
print('ALL OK' if ok else 'SOME FAILED')

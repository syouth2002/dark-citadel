"""Passwords: shown when a floor is cleared; typed on the title (P) they start
that floor with that health, those rounds, that difficulty and the records
so far (time, kills, deaths); a wrong one is turned away."""
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
KEY = int.from_bytes(bytes([0xA3, 0xC5, 0x09, 0x5E, 0xB2, 0x71, 0x1C]), 'little')
FIELDS = (('hp4', 5), ('ammo', 7), ('floor', 4), ('diff', 2), ('secs', 14), ('kills', 9), ('deaths', 8))
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def ck(v):
    a = 5
    for b in v.to_bytes(7, 'little'):
        a = (((a << 1) | (a >> 7)) & 255) + b & 255
    return a & 63


def make(floor, hp, ammo, diff=0, secs=0, kills=0, deaths=0):
    """as pw_make (floor = the next floor's number - 1)"""
    vals = dict(hp4=(hp + 3) // 4, ammo=ammo, floor=floor, diff=diff, secs=min(secs, 16383),
                kills=min(kills, 511), deaths=deaths)
    v, pos = 0, 0
    for name, w in FIELDS:
        v |= vals[name] << pos
        pos += w
    v |= ck(v) << pos
    v ^= KEY
    return ''.join(ABC[(v >> (5 * i)) & 31] for i in range(11))


def decode(w):
    """the fields (dict) or None, as pw_check"""
    v = 0
    for i, ch in enumerate(w):
        v |= ABC.index(ch) << (5 * i)
    v ^= KEY
    f, pos = {}, 0
    for name, wd in FIELDS:
        f[name] = (v >> pos) & ((1 << wd) - 1)
        pos += wd
    c = (v >> pos) & 63
    if c != ck(v & ((1 << pos) - 1)) or not (1 <= f['hp4'] <= 25 and f['ammo'] <= 99 and
                                             1 <= f['floor'] <= LAST and f['diff'] <= 2):
        return None
    return f


def key(p6, ch):
    p6.keyq.append(ord(ch))
    p6.pending.append(0x02)
    p6.run_cycles(CPU // 10)


# ---- clear floor 3 on NORMAL with 23 rounds, after 5:00 of play, 17 kills
# before this floor and 2 deaths: the password for floor 4 carries it all
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
m[V['ammo']] = 23
g.setw('gsecs', 300)
g.setw('tkills', 17)
m[V['deaths']] = 2
m[V['kills']] = 3
g.approach(*ex)
m[V['ammo']] = 23
g.frame(0, 2)
shown = bytes(m[V['pwtext']:V['pwtext'] + 11]).decode()
f = decode(shown)
secs = g.getw('gsecs')
check('floor cleared: an 11-character password', len(shown) == 11 and m[V['pwtext'] + 11] == 0 and f is not None,
      shown)
check('it carries floor 4, health, rounds, NORMAL',
      f and (f['floor'], f['hp4'], f['ammo'], f['diff']) == (3, 25, 23, 1), repr(f))
check('and the records: the time, kills (17 + 3 on this floor), deaths',
      f and f['secs'] == secs and 300 <= secs < 310 and f['kills'] == 20 and f['deaths'] == 2, repr(f))

# ---- on the title: P and a password -> that floor, health, rounds,
# difficulty and records (the difficulty chosen on the title gives way)
want = make(3, 37, 23, 2, 1234, 77, 5)
p6 = H.P6(T.code())
m = p6.mem
p6.run_cycles(CPU)
key(p6, 'P')
for ch in want.lower():                      # (either case)
    key(p6, ch)
p6.run_cycles(CPU // 2)
got = (m[V['level']], m[V['hp']], m[V['ammo']], m[V['diff']], m[V['pw']],
       m[V['gsecs']] | m[V['gsecs'] + 1] << 8, m[V['tkills']] | m[V['tkills'] + 1] << 8, m[V['deaths']])
check('right: floor 4, 40 health, 23 rounds, HARD', got[:5] == (3, 40, 23, 2, 1), repr(got))
check('the records go on: time 1234 s (and counting), 77 kills, 5 deaths',
      1234 <= got[5] < 1240 and got[6:] == (77, 5), repr(got[5:]))
# ---- a wrong one
p6 = H.P6(T.code())
m = p6.mem
p6.run_cycles(CPU)
bad = next(w for w in ('A' * 11, 'B' * 11, 'ABCDEFGHJKL') if decode(w) is None)
key(p6, 'P')
for ch in bad:
    key(p6, ch)
p6.run_cycles(CPU * 2)
check('wrong (%s): still on the title' % bad, m[V['pw']] == 0 and len(p6.flips) <= 1)   # (1: set up at boot)
key(p6, 'P')
for ch in make(LAST, 100, 99, 0, 3000, 300, 0):   # the last floor, full health, 99 rounds
    key(p6, ch)
p6.run_cycles(CPU // 2)
check('then a right one works: the last floor', m[V['level']] == LAST and m[V['hp']] == 100 and
      m[V['ammo']] == 99 and m[V['diff']] == 0 and (m[V['tkills']] | m[V['tkills'] + 1] << 8) == 300)
# ---- the model both ways
bad = 0
for floor in range(1, NL):
    for hp in (1, 50, 100):
        for ammo in (0, 99):
            for diff in (0, 2):
                for secs, kills, deaths in ((0, 0, 0), (16383, 511, 255), (4321, 123, 9)):
                    f = decode(make(floor, hp, ammo, diff, secs, kills, deaths))
                    if f != dict(hp4=(hp + 3) // 4, ammo=ammo, floor=floor, diff=diff, secs=secs,
                                 kills=kills, deaths=deaths):
                        bad += 1
check('the code goes both ways (Python model)', bad == 0)
# ---- one mistyped character is caught, most of the time
caught = tot = 0
for args in ((1, 60, 40, 1, 500, 20, 1), (5, 100, 99, 2, 9999, 300, 30), (LAST, 4, 0, 0, 16000, 400, 200)):
    w = make(*args)
    for i in range(11):
        for c in ABC:
            if c != w[i]:
                tot += 1
                caught += decode(w[:i] + c + w[i + 1:]) is None
check('one wrong character is turned away (%d of %d)' % (caught, tot), caught >= tot * 0.9)
print('ALL OK' if ok else 'SOME FAILED')

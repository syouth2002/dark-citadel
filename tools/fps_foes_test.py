"""The bloater, the lamp turret and the bat: where they appear, how they
move, how they hurt; the bloater's burst (shot or not) and its chain."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
import voices

V = T.V
E = V['enemies']
HUSK, STALK, BLOAT, TURRET, BAT = 1, 4, 11, 12, 13
HP = {HUSK: 3, STALK: 2, BLOAT: 6, TURRET: 10, BAT: 1}
NL = len(T.LEVELS)
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def arena(lv=8):
    """a game (EASY) on floor lv with no enemies; an open area in front"""
    g = T.Game()
    if lv:
        g.m[V['level']] = lv - 1
        g.m[V['lvdone']] = 1
        g.frame(0, 2)
        g.frame(H.K_SPACE, 2)
    g.frame(0, 3)
    for i in range(T.NEN):
        g.m[E + i * 16] = 0
    cells, _, _ = T.level(lv)
    ox, oy = T.find_open(cells, 6, 3)
    return g, ox, oy


def place(g, i, ty, x, y, st=1):
    m = g.m
    b = E + i * 16
    m[b] = ty
    m[b + 1], m[b + 2] = int(x * 256) & 255, int(x * 256) >> 8
    m[b + 3], m[b + 4] = int(y * 256) & 255, int(y * 256) >> 8
    m[b + 5] = HP[ty]
    m[b + 6] = st
    m[b + 7] = 0
    if i + 1 > m[V['nobj']]:
        m[V['nobj']] = i + 1


def pos(g, i):
    m = g.m
    b = E + i * 16
    return (m[b + 1] | m[b + 2] << 8) / 256, (m[b + 3] | m[b + 4] << 8) / 256


def hold(g, x, y, a=0):
    g.setw('px', x * 256)
    g.setw('py', y * 256)
    g.m[V['pa']] = a


def heard(g, name):
    want = dict(voices.build())[name][:-1]
    frames = [f for _, f in g.p6.voice.played]
    return any(frames[i:i + len(want)] == want for i in range(len(frames)))


# ---- where they appear: bats from floor 3, bloaters from 5, turrets from 9;
# the floors keep their number of enemies
for ty, name, first in ((BAT, 'bats', 3), (BLOAT, 'bloaters', 5), (TURRET, 'turrets', 9)):
    has = [any(t == ty for t, x, y in T.level(lv)[1]) for lv in range(NL)]
    check('%s from floor %d' % (name, first), not any(has[:first - 1]) and all(has[first - 1:]),
          ''.join('x' if h else '.' for h in has))
counts = [sum(1 for t, x, y in T.level(lv)[1] if t <= 4 or t >= 11) for lv in range(NL)]
check('enemies a floor as before (4 + floor, at most 15)', counts == [min(15, 5 + lv) for lv in range(NL)],
      repr(counts))

# ---- the bloater: within a cell it swells, then bursts: 25 (EASY)
g, ox, oy = arena()
m = g.m
px, py = ox + 0.5, oy + 1.5
place(g, 0, BLOAT, px + 0.8, py)
g.p6.voice.played.clear()
swelled = None
got = None
for f in range(80):
    hold(g, px, py)
    m[V['hp']] = 100 if got is None else m[V['hp']]
    g.frame()
    if swelled is None and m[E + 6] == 2:
        swelled = f
    if m[V['hp']] < 100 and got is None:
        got = 100 - m[V['hp']]
        burst_at = f
    if m[E + 6] >= 3 and got is not None:
        break
check('bloater swells next to the player', swelled is not None and heard(g, 'bloat_swell'))
check('then bursts: 25 damage, a moment later', got == 25 and swelled is not None and burst_at - swelled >= 6,
      '(%s, %s frames)' % (got, None if swelled is None or got is None else burst_at - swelled))
g.frame(0, 15)                               # (the pop takes a moment to say)
check('the bloater is gone, a kill, its pop', m[E + 6] >= 3 and m[V['kills']] == 1 and heard(g, 'bloat_pop'))

# ---- shot down, it bursts where it is: the player 1.2 cells off is caught
g, ox, oy = arena()
m = g.m
px, py = ox + 0.5, oy + 1.5
bx = px + 1.25
place(g, 0, BLOAT, bx, py, st=0)
m[V['ammo']] = 50
got = None
for f in range(120):
    hold(g, px, py)
    m[E + 1], m[E + 2] = int(bx * 256) & 255, int(bx * 256) >> 8
    if m[E + 6] < 2:
        m[E + 6] = 0                         # (it stays where it is until shot down)
    m[V['hp']] = 100 if got is None else m[V['hp']]
    g.frame(H.K_SPACE if f % 2 == 0 else 0)
    if m[V['hp']] < 100 and got is None:
        got = 100 - m[V['hp']]
    if m[E + 6] >= 3:
        break
check('shot down, a bloater bursts where it is (25 to the player 1.25 cells off)', got == 25 and m[E + 6] >= 3,
      '(%s)' % got)

# ---- the burst hits the others near it; another bloater bursts in turn
g, ox, oy = arena()
m = g.m
px, py = ox + 0.5, oy + 1.5
m[V['god']] = 1
place(g, 0, BLOAT, px + 3.0, py, st=2)
m[E + 7] = 2                                 # (about to burst)
place(g, 1, HUSK, px + 3.0, py + 0.9, st=0)  # within 1.5 cells: 3 damage, gone
place(g, 2, BLOAT, px + 4.2, py, st=0)       # another bloater: it bursts next
place(g, 3, HUSK, px + 5.4, py, st=0)        # only near the second one
place(g, 4, HUSK, px + 3.0, py - 1.0, st=0)  # (1.0 + the wall? no: an open cell)
for f in range(20):
    hold(g, px, py)
    g.frame()
st = [m[E + i * 16 + 6] for i in range(5)]
check('the burst: a husk near it falls, the next bloater bursts, and its burst the husk beyond',
      st[0] >= 3 and st[1] >= 3 and st[2] >= 3 and st[3] >= 3, repr(st))

# ---- the turret: does not move; fires 8 at a time while it sees the player
g, ox, oy = arena()
m = g.m
px, py = ox + 0.5, oy + 1.5
place(g, 0, TURRET, px + 4.0, py)
p0 = pos(g, 0)
g.p6.voice.played.clear()
hits = []
shots = 0
for f in range(480):
    hold(g, px, py)
    m[V['hp']] = 100
    was = m[E + 6]
    g.frame()
    if m[V['hp']] < 100:
        hits.append(100 - m[V['hp']])
    shots += was == 2 and m[E + 6] == 1
check('turret stays put', pos(g, 0) == p0)
check('turret fires every 1.5 seconds or so (%d shots in 480 frames)' % shots, 11 <= shots <= 15)
check('turret: about half its shots hit, for 8 (%d hits)' % len(hits), hits and set(hits) == {8} and
      shots // 4 <= len(hits) <= shots, repr(hits[:6]))
check('turret: its shot', heard(g, 'turret_shot'))

# ---- a turret sees the player from the dark (7 cells, beyond the lantern):
# it wakes and fires; the player has not seen it
spot = None
for lv in range(NL):
    cells, _, _ = T.level(lv)
    try:
        spot = (lv, T.find_open(cells, 9, 1))
        break
    except Exception:
        continue
lv, (ox, oy) = spot
g, _, _ = arena(lv)
m = g.m
px, py = ox + 0.5, oy + 0.5
place(g, 0, TURRET, px + 7.0, py, st=0)
first = None
for f in range(120):
    hold(g, px, py)
    m[V['hp']] = 100
    g.frame()
    if m[V['hp']] < 100:
        first = f
        break
check('a turret 7 cells off, in the dark, wakes and fires (first hit at frame %s)' % first,
      first is not None and m[E + 13] & 4 == 0)

# ---- the bloater rolls at the player: sooner than a husk
frames = {}
for ty in (HUSK, BLOAT):
    g, ox, oy = arena()
    m = g.m
    px, py = ox + 0.5, oy + 1.5
    m[V['god']] = 1
    place(g, 0, ty, px + 4.0, py)
    for f in range(150):
        hold(g, px, py)
        g.frame()
        x, y = pos(g, 0)
        if abs(x - px) + abs(y - py) < 1.6:
            break
    frames[ty] = f
check('bloater rolls at the player sooner than a husk', frames[BLOAT] < frames[HUSK] * 0.8, repr(frames))

# ---- the bat: faster than a stalker, off the line as much, bites for 4
frames = {}
offline = {}
for ty in (HUSK, STALK, BAT):
    g, ox, oy = arena()
    m = g.m
    px, py = ox + 0.5, oy + 1.5
    m[V['god']] = 1
    place(g, 0, ty, px + 4.0, py)
    far = 0
    for f in range(150):
        hold(g, px, py)
        g.frame()
        x, y = pos(g, 0)
        far = max(far, abs(y - py))
        if abs(x - px) + abs(y - py) < 1.3:
            break
    frames[ty] = f
    offline[ty] = far
check('bat reaches the player about as soon as a stalker, for all its swinging',
      frames[BAT] <= frames[STALK] + 3 and frames[BAT] < frames[HUSK] * 0.6, repr(frames))
check('bat swings off the line as far as a stalker', offline[BAT] >= 0.9 * offline[STALK],
      '(bat %.2f, stalker %.2f cells)' % (offline[BAT], offline[STALK]))
g, ox, oy = arena()
m = g.m
px, py = ox + 0.5, oy + 1.5
got = None
place(g, 0, BAT, px + 1.0, py)
g.p6.voice.played.clear()
for f in range(120):
    hold(g, px, py)
    m[E + 1], m[E + 2] = int((px + 1.0) * 256) & 255, int((px + 1.0) * 256) >> 8
    m[E + 3], m[E + 4] = int(py * 256) & 255, int(py * 256) >> 8
    m[V['hp']] = 100
    g.frame()
    if m[V['hp']] < 100:
        got = 100 - m[V['hp']]
        break
check('bat bites for 4, with a squeak', got == 4 and heard(g, 'bat_hit'), '(%s)' % got)
print('ALL OK' if ok else 'SOME FAILED')

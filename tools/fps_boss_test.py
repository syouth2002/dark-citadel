"""The warden (the last floor): where it stands, the barred exit, waking, its bolt and
blow, its health bar and music, its fall, its size on screen."""
import os
import re
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T

V = T.V
E = V['enemies']
WARDEN = 5
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


blob = open(os.path.join(T.ROOT, 'src', 'fps_blob.inc')).read()
NL = len(T.LEVELS)
LAST = NL - 1                                # (its index)
BGM_TBL = int(re.search(r'bgm_tbl\s+equ\s+0?([0-9A-F]+)h', blob).group(1), 16)

# ---- where it stands
for lv in range(NL):
    _, objs, _ = T.level(lv)
    n = sum(1 for ty, x, y in objs if ty == WARDEN)
    if lv < LAST and n:
        check('no warden on floor %d' % (lv + 1), False)
cells, objs, start = T.level(LAST)
wx, wy = next((x, y) for ty, x, y in objs if ty == WARDEN)
ex, ey = next(c for c, v in cells.items() if v == 7)
# the exit room = floor reachable from the warden without doors
room, todo = {(wx, wy)}, [(wx, wy)]
while todo:
    x, y = todo.pop()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c = (x + dx, y + dy)
        if c not in room and cells.get(c) == 0:
            room.add(c)
            todo.append(c)
check('one warden, on the last floor, in the exit room',
      sum(1 for ty, x, y in objs if ty == WARDEN) == 1 and
      any((ex + dx, ey + dy) in room for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
# a place to face it from: 3-4 cells away in a straight, open line
spot = None
for k in (4, 3):
    for dx, dy, ang in ((-1, 0, 0), (1, 0, 128), (0, -1, 64), (0, 1, 192)):
        cs = [(wx + dx * i, wy + dy * i) for i in range(1, k + 1)]
        if all(c in room for c in cs):
            spot = (cs[-1], ang, k)
            break
    if spot:
        break
(sx, sy), ang, dist = spot


def floor_last():
    g = T.Game()
    m = g.m
    m[V['level']] = LAST - 1
    m[V['lvdone']] = 1
    g.frame(0, 2)
    g.frame(H.K_SPACE, 2)
    g.frame(0, 3)
    for i in range(24):                      # only the warden (and the pickups)
        if 1 <= m[E + i * 16] <= 4:
            m[E + i * 16] = 0
    return g, m


def warden(m):
    for i in range(24):
        if m[E + i * 16] == WARDEN:
            return E + i * 16
    return None


def tune(m):
    s = m[V['bgm_s']] | m[V['bgm_s'] + 1] << 8
    return [m[BGM_TBL + 2 * i] | m[BGM_TBL + 2 * i + 1] << 8 for i in range(5)].index(s)


def bar(m, p6=None):
    """the gauge on the shown page: (red pixels inside, frame complete)"""
    base = [0x8000, 0xC000][(g.p6.b0 >> 1) & 1]
    def px(row, x):
        a = base + row * 40 + 8 + x // 4
        sh = 6 - 2 * (x % 4)
        return ((m[a] >> sh) & 3) | (((m[a + 0x2000] >> sh) & 3) << 2)
    y0 = 142                                 # the message line
    red = sum(1 for x in range(80) if px(y0 + 2, x) == 10)
    frame = all(px(y0, x) == 7 and px(y0 + 4, x) == 7 for x in range(80)) and         all(px(y, 0) == 7 and px(y, 79) == 7 for y in range(y0, y0 + 5))
    return red, frame


g, m = floor_last()
b = warden(m)
check('the last floor loaded with its warden asleep', m[V['level']] == LAST and b and m[V['boss']] == 1)
check('the last floor has its own music', tune(m) == 4)
# ---- the exit is barred
g.approach(ex, ey)
check('exit barred while the warden stands', m[V['lvdone']] == 0 and 'WARDEN' in g.msg())
# ---- it wakes when seen: music, health bar
m[V['god']] = 1
for f in range(10):
    g.put(sx + 0.5, sy + 0.5, ang)
    g.frame()
    if m[V['boss']] == 2:
        break
g.frame(0, 2)
check('it wakes when it is seen', m[V['boss']] == 2)
for f in range(40):                          # (the exit's message goes first)
    if not m[V['msg_t']]:
        break
    g.put(sx + 0.5, sy + 0.5, ang)
    g.frame()
g.frame(0, 2)
check('the warden\'s music plays (in its line of fire)', tune(m) == 3)
# ---- out of its line of fire (back where the floor started): the floor's
# music again after a while; back in sight: the warden's
m[V['god']] = 1
bx0, by0 = m[b + 1] | m[b + 2] << 8, m[b + 3] | m[b + 4] << 8


def hold(x, y, a, n):
    seen = []
    for f in range(n):
        g.setw('px', x * 256)
        g.setw('py', y * 256)
        m[V['pa']] = a
        m[b + 1], m[b + 2], m[b + 3], m[b + 4] = bx0 & 255, bx0 >> 8, by0 & 255, by0 >> 8
        g.frame()
        seen.append(tune(m))
    return seen


s = hold(start[0] + 0.5, start[1] + 0.5, 0, 50)
check('out of its line of fire: the floor\'s music after a while', s[0] == 3 and s[-1] == 4, repr(s[::5]))
s = hold(sx + 0.5, sy + 0.5, ang, 8)
check('in it again: the warden\'s music', s[-1] == 3, repr(s))
check('health gauge full', bar(m) == (78, True), repr(bar(m)))
# ---- drawn larger than a husk at the same distance
hs_w = m[b + 15]
g.frame(0, 1)
m[V['god']] = 1
# ---- its bolt from afar (it is held in place for this)
m[V['god']] = 0
got = None
bx, by = m[b + 1] | m[b + 2] << 8, m[b + 3] | m[b + 4] << 8
for f in range(200):
    g.setw('px', (sx + 0.5) * 256)
    g.setw('py', (sy + 0.5) * 256)
    m[b + 1], m[b + 2], m[b + 3], m[b + 4] = bx & 255, bx >> 8, by & 255, by >> 8
    m[V['hp']] = 100
    g.frame()
    if m[V['hp']] < 100:
        got = 100 - m[V['hp']]
        break
check('its bolt hits for 10 from %d cells' % dist, got == 10, '(got %s)' % got)
# ---- its blow when close
got = None
for f in range(200):
    # one cell from where the warden stands, on the side we came from
    g.setw('px', bx + (sx > wx) * 256 - (sx < wx) * 256)
    g.setw('py', by + (sy > wy) * 256 - (sy < wy) * 256)
    m[b + 1], m[b + 2], m[b + 3], m[b + 4] = bx & 255, bx >> 8, by & 255, by >> 8
    m[V['hp']] = 100
    g.frame()
    if m[V['hp']] < 100:
        got = 100 - m[V['hp']]
        break
check('its blow hits for 15 up close', got == 15, '(got %s)' % got)
# ---- bring it down: 30 shots; the bar follows
m[V['god']] = 1
m[V['ammo']] = 99
fired = 0
bars = {}
for f in range(400):
    g.setw('px', (sx + 0.5) * 256)
    g.setw('py', (sy + 0.5) * 256)
    m[V['pa']] = ang
    m[b + 1], m[b + 2], m[b + 3], m[b + 4] = bx & 255, bx >> 8, by & 255, by >> 8
    a0 = m[V['ammo']]
    g.frame(H.K_SPACE if f % 2 == 0 else 0)
    if m[V['ammo']] < a0:
        fired += 1
        g.frame(0, 2)
        bars[fired] = bar(m)
    if m[b + 6] >= 3:
        break
check('it falls on shot 30', fired == 30 and m[b + 6] >= 3, '(fired %d)' % fired)
check('the gauge shrinks: 15 shots -> half', bars.get(15) == (39, True), repr(bars.get(15)))
g.frame(0, 3)
base = [0x8000, 0xC000][(g.p6.b0 >> 1) & 1]
red = sum(1 for x in range(8, 30) for r in range(5) for v in [m[base + (142 + r) * 40 + x]]
          if v and v == m[base + 0x2000 + (142 + r) * 40 + x] and v & 0x80 and not v & 0x40)
check('no trace of the gauge beside the message', red == 0, '(%d red bytes)' % red)
check('fallen: message, the floor\'s music again', m[V['boss']] == 0 and 'WARDEN HAS FALLEN' in g.msg() and tune(m) == 4)
g.approach(ex, ey)
check('the exit opens', m[V['lvdone']] == 1)
# ---- size on screen: the warden against a husk at the same place
g, m = floor_last()
b = warden(m)
m[V['god']] = 1
g.put(sx + 0.5, sy + 0.5, ang)
g.frame(0, 2)
hs_w, top_w = m[b + 15], m[b + 14]
m[b] = 1                                             # the same spot, as a husk
g.frame(0, 2)
hs_h = m[b + 15]
check('the warden is drawn half as tall again', abs(hs_w - hs_h * 1.5) <= 2, '(%d vs husk %d)' % (hs_w, hs_h))
print('ALL OK' if ok else 'SOME FAILED')

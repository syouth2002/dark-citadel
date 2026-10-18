"""Enemy kinds: who appears on which floor, how tough they are, how hard
they hit, how they move."""
import math
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T
NL = len(T.LEVELS)      # floors
LAST = NL - 1           # the last (the warden's), as an index
import voices

V = T.V
E = V['enemies']
HUSK, ORB, BRUTE, STALK = 1, 2, 3, 4
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


# ---- the floors
kinds = []
for lv in range(NL):
    _, objs, _ = T.level(lv)
    kinds.append({ty for ty, x, y in objs if ty <= 4})
check('floors 1-3: husks and sentinels only', all(k <= {HUSK, ORB} for k in kinds[:3]))
check('brutes from floor 4', all(BRUTE in k for k in kinds[3:]) and all(BRUTE not in k for k in kinds[:3]))
check('stalkers from floor 7', all(STALK in k for k in kinds[6:]) and all(STALK not in k for k in kinds[:6]))
counts = []
for lv in range(NL):
    _, objs, _ = T.level(lv)
    counts.append(sum(1 for ty, x, y in objs if ty <= 4))
check('more enemies on higher floors', counts == sorted(counts), str(counts))


def arena(lv):
    """a game on floor lv with no enemies; an open area in front of the player"""
    g = T.Game()
    g.m[V['startlv']] = lv
    if lv:
        g.m[V['level']] = lv - 1
        g.m[V['lvdone']] = 1                 # pass through the tally to floor lv
        g.frame(0, 2)
        g.frame(H.K_SPACE, 2)
    g.frame(0, 3)
    for i in range(24):
        g.m[E + i * 16] = 0
    cells, _, _ = T.level(lv)
    ox, oy = T.find_open(cells, 5, 3)
    return g, ox, oy


def place(g, i, ty, x, y, st=0):
    m = g.m
    b = E + i * 16
    m[b] = ty
    m[b + 1], m[b + 2] = int(x * 256) & 255, int(x * 256) >> 8
    m[b + 3], m[b + 4] = int(y * 256) & 255, int(y * 256) >> 8
    m[b + 5] = [3, 4, 8, 2][ty - 1]
    m[b + 6] = st
    m[b + 7] = 0


# ---- toughness: shots to bring each kind down; its own voices
for ty, name, shots in ((BRUTE, 'brute', 8), (STALK, 'stalker', 2), (HUSK, 'husk', 3)):
    g, ox, oy = arena(6)
    m = g.m
    g.put(ox + 0.5, oy + 1.5, 0)
    place(g, 0, ty, ox + 3.5, oy + 1.5)
    m[V['ammo']] = 50
    m[V['god']] = 1
    g.frame(0)                               # (seen on screen before the first shot)
    g.p6.voice.played.clear()
    fired = 0
    alive_after = []
    for f in range(200):
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        m[V['pa']] = 0
        m[E + 1], m[E + 2] = int((ox + 3.5) * 256) & 255, int((ox + 3.5) * 256) >> 8
        m[E + 3], m[E + 4] = int((oy + 1.5) * 256) & 255, int((oy + 1.5) * 256) >> 8
        a0 = m[V['ammo']]
        g.frame(H.K_SPACE if f % 2 == 0 else 0)
        if m[V['ammo']] < a0:
            fired += 1
            alive_after.append(m[E + 6] < 3)
        if m[E + 6] >= 3:
            break
    check('%s falls on shot %d' % (name, shots), fired == shots and all(alive_after[:-1]),
          '(fired %d)' % fired)
    g.frame(0, 8)                            # let the death cry finish
    frames = [f for _, f in g.p6.voice.played]
    vo = dict(voices.build())
    die = vo[name[:5] + '_die' if name != 'stalker' else 'stalk_die'][:-1]
    hit = vo[name[:5] + '_hit' if name != 'stalker' else 'stalk_hit'][:-1]
    check('%s: its own hit and death voices' % name,
          any(frames[i:i + len(hit)] == hit for i in range(len(frames))) or shots == 1,
          '') if shots > 1 else None
    check('%s: death voice' % name, frames[-len(die):] == die)

# ---- how hard they hit
for ty, name, dmg in ((BRUTE, 'brute', 20), (STALK, 'stalker', 5), (HUSK, 'husk', 8)):
    g, ox, oy = arena(6)
    m = g.m
    got = None
    for f in range(120):
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        m[V['pa']] = 0
        if f == 0:
            place(g, 0, ty, ox + 1.3, oy + 1.5, st=1)
        m[E + 1], m[E + 2] = int((ox + 1.3) * 256) & 255, int((ox + 1.3) * 256) >> 8
        m[E + 3], m[E + 4] = int((oy + 1.5) * 256) & 255, int((oy + 1.5) * 256) >> 8
        m[V['hp']] = 100
        g.frame()
        if m[V['hp']] < 100:
            got = 100 - m[V['hp']]
            break
    check('%s hits for %d' % (name, dmg), got == dmg, '(got %s)' % got)

# ---- how they move: from 4 cells away, frames to reach the player
speed = {}
for ty, name in ((HUSK, 'husk'), (BRUTE, 'brute'), (STALK, 'stalker')):
    g, ox, oy = arena(6)
    m = g.m
    m[V['god']] = 1
    place(g, 0, ty, ox + 4.5, oy + 1.5, st=1)
    side = 0
    for f in range(150):
        g.setw('px', (ox + 0.5) * 256)
        g.setw('py', (oy + 1.5) * 256)
        m[V['pa']] = 128                     # facing away: it is not shot at
        g.frame()
        ex = (m[E + 1] | m[E + 2] << 8) / 256
        ey = (m[E + 3] | m[E + 4] << 8) / 256
        side = max(side, abs(ey - (oy + 1.5)))
        if math.hypot(ex - (ox + 0.5), ey - (oy + 1.5)) < 1.0:
            break
    speed[name] = f
    if name == 'stalker':
        check('stalker darts sideways', side > 0.25, '(%.2f cells off the line)' % side)
check('stalker fastest, brute slowest', speed['stalker'] < speed['husk'] < speed['brute'], str(speed))
print('ALL OK' if ok else 'SOME FAILED')

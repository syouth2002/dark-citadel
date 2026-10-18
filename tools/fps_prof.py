"""Where the frame time goes: samples the program counter while walking
through a floor with enemies, and sums it per routine.  python fps_prof.py [floor]"""
import bisect
import os
import re
import sys
floor = int(sys.argv[1]) if len(sys.argv) > 1 else 7
os.environ['PROF'] = '1'
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T

labs = []
for line in open(os.path.join(T.ROOT, 'build', 'fps.map')):
    a, _, n = line.strip().partition(': ')
    try:
        labs.append((int(a, 16), n.strip().lstrip('.')))
    except ValueError:
        pass
labs.sort()
# routines: labels that are not local (xx_1, xx_lp ...)
top = [(a, n) for a, n in labs if not re.search(r'_\d+[a-z]?$|_lp$|^[a-z]{2,3}_[a-z0-9]{1,3}$', n)]
taddr = [a for a, _ in top]

g = T.Game()
m = g.m
if floor > 1:
    m[T.V['level']] = floor - 2
    m[T.V['lvdone']] = 1
    g.frame(0, 2)
    g.frame(H.K_SPACE, 2)
m[T.V['god']] = 1
del H.PROF[:]
script = [(0, 20, 0), (20, 60, H.K_UP), (60, 100, H.K_RIGHT), (100, 160, H.K_UP),
          (160, 190, H.K_LEFT), (190, 260, H.K_UP | H.K_LEFT)]
c0 = g.p6.cycles
for f in range(200):
    k = 0
    for a, b, kk in script:
        if a <= f < b:
            k = kk
    g.frame(k)
frames = 200
from collections import Counter
c = Counter()
for pc in H.PROF:
    i = bisect.bisect_right(taddr, pc) - 1
    c[top[i][1] if i >= 0 else '?'] += 1
tot = sum(c.values())
print('floor %d: %.0f cycles per frame' % (floor, (g.p6.cycles - c0) / frames))
for n, v in c.most_common(22):
    print('%5.1f%% %s' % (100 * v / tot, n))

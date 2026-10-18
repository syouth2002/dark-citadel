"""Standing still, only the columns something was drawn over are drawn again.
The same play twice - once like that, once with every column drawn every
frame - must give the very same screens."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_testlib as T

V = T.V
E = V['enemies']
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


# what the player does, frame by frame: stand, fire, stand, turn, stand,
# switch weapons, stand while the enemies come, walk, stand
SCRIPT = ([0] * 6 + [H.K_SPACE, 0] * 3 + [0] * 6 + [H.K_RIGHT] * 3 + [0] * 8 +
          [H.K_SHIFT, 0] + [0] * 6 + [H.K_SPACE, 0] * 4 + [0] * 10 + [H.K_UP] * 4 + [0] * 10)


def run(full, enemies=False):
    g = T.Game()
    m = g.m
    g.frame(0, 3)
    m[V['god']] = 1                          # (blows land, nobody dies)
    if enemies:                              # a husk and a sentinel ahead
        cells, _, _ = T.level(0)
        ox, oy = T.find_open(cells, 5, 3)
        g.put(ox + 0.5, oy + 1.5, 0)
        for i in range(24):
            m[E + i * 16] = 0
        for i, (ty, d, hp) in enumerate(((1, 3.5, 3), (2, 4.4, 4))):
            x, y = int((ox + 0.5 + d) * 256), int((oy + 1.5 + 0.6 * i) * 256)
            b = E + i * 16
            m[b], m[b + 1], m[b + 2], m[b + 3], m[b + 4], m[b + 5], m[b + 6] = ty, x & 255, x >> 8, y & 255, y >> 8, hp, 1
    # the keys by frame number, not by time: both runs read the same keys in
    # the same frames however long a frame takes
    p6 = g.p6
    f0 = len(p6.flips)
    orig = p6.inp

    def inp(port):
        if port & 0xFF == 0x90 and not p6.keyq_active:
            i = len(p6.flips) - f0
            return SCRIPT[i] if 0 <= i < len(SCRIPT) else 0
        return orig(port)
    p6.m.set_input_callback(inp)
    shots = []
    for k in SCRIPT:
        if full:
            m[V['vfull']] = 2                # every column, every frame
        g.frame(k)
        if m[V['dead']]:
            break
        shots.append(bytes(m[0x8000:0x10000]))
    return shots, g


for enemies in (False, True):
    a, ga = run(False, enemies)
    b, gb = run(True, enemies)
    what = 'enemies ahead' if enemies else 'walking about'
    check(what + ': the same number of frames', len(a) == len(b) == len(SCRIPT), '(%d, %d)' % (len(a), len(b)))
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    check(what + ': every frame the same as when drawn in full', not diff,
          '(first different: frame %s)' % (diff[0] if diff else '-'))
    if diff:
        i = diff[0]
        n = sum(1 for p, q in zip(a[i], b[i]) if p != q)
        print('     %d bytes differ in frame %d' % (n, i))
    seen = sum(1 for i in range(24) if ga.m[E + i * 16] and ga.m[E + i * 16 + 13])
    print('     (enemies or items in view at the end: %d)' % seen)
print('ALL OK' if ok else 'SOME FAILED')

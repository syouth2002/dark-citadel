"""The ending: dawn over the citadel (sky bands, the sun), the words; SPACE
skips through; then the tally."""
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
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def row(m, page, r):
    return bytes(m[page + (4 + r) * 40:page + (4 + r) * 40 + 32])


def words(m, page):
    """rows with text in the dark ground under the horizon"""
    return sum(1 for r in range(84, 112) if any(row(m, page, r)))


for skip in (False, True):
    g = T.Game()
    m, p6 = g.m, g.p6
    g.frame(0, 3)
    m[V['level']] = LAST
    m[V['lvdone']] = 1
    g.frame(0, 1)
    if skip:
        p6.run_cycles(CPU // 2)              # (the dawn has begun)
        g.press(H.K_SPACE, 400000)           # straight through
        p6.run_cycles(CPU // 2)
    else:
        p6.run_cycles(CPU * 14)              # all of it
    for page in (0x8000, 0xC000):
        sky = [row(m, page, r) for r in (30, 45, 60, 66, 75)]
        check('%s: the dawn sky (page %04X)' % ('skipped' if skip else 'watched', page),
              sky[0] == bytes([0x44] * 32) or sky[0] == bytes([0x11] * 32))
        check('%s: the sun and the words (page %04X)' % ('skipped' if skip else 'watched', page),
              row(m, page, 75)[16] == 0xFF and words(m, page) >= 16)
    if not skip:
        line = [any(m[0x8000 + (142 + r) * 40 + c] or m[0xA000 + (142 + r) * 40 + c] for r in range(5))
                for c in range(30)]
        check('only PRESS SPACE on the message line', any(line[1:12]) and not any(line[12:30]))
    g.press(H.K_SPACE)
    check('%s: then the tally' % ('skipped' if skip else 'watched'),
          not any(row(m, 0x8000, 45)))      # (the sky gone: the view cleared for the tally)
    g.press(H.K_SPACE)
    n = len(p6.flips)
    p6.run_cycles(CPU)
    check('%s: then the title' % ('skipped' if skip else 'watched'), len(p6.flips) == n)
print('ALL OK' if ok else 'SOME FAILED')

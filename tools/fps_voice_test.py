"""Speech chip driver: every voice reaches the chip intact and on time."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import voices

ROOT = H.ROOT
CPU = 3993600
code = open(os.path.join(ROOT, 'build', 'vtest.bin'), 'rb').read()
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


p6 = H.P6(code)
p6.run_cycles(CPU)                 # start-up builds tables first
V = voices.build()
for i, (name, frames) in enumerate(V):
    p6.voice.played.clear()
    t0 = p6.cycles
    p6.keyq.append(ord('1') + i if i < 9 else ord('0') if i == 9 else ord('A') + i - 10)
    p6.pending.append(0x02)
    p6.run_cycles(CPU * (len(frames) + 20) // 100)
    got = [f for _, f in p6.voice.played]
    want = frames[:-1]
    lat = (p6.voice.played[0][0] - t0) * 1000 / CPU if got else -1
    check('%s: %d frames intact' % (name, len(want)), got == want, '(first frame after %.0f ms)' % lat)
    check('%s: chip idle at the end' % name, not p6.voice.stat & 0x80)
check('no transfer errors', p6.voice.errors == 0, str(p6.voice.errors))
# cut a long voice short with another one
p6.voice.played.clear()
p6.keyq.append(ord('2'))
p6.pending.append(0x02)
p6.run_cycles(CPU // 10)
p6.keyq.append(ord('5'))
p6.pending.append(0x02)
p6.run_cycles(CPU)
tail = [f for _, f in p6.voice.played][-(len(V[4][1]) - 1):]
check('a new voice cuts in', tail == V[4][1][:-1] and p6.voice.errors == 0)
# a death cry is not cut off by a lesser voice
p6.voice.played.clear()
p6.keyq.append(ord('2'))
p6.pending.append(0x02)
p6.run_cycles(CPU // 10)
p6.keyq.append(ord('6'))
p6.pending.append(0x02)
p6.run_cycles(CPU)
got = [f for _, f in p6.voice.played]
check('death cry not cut by a lesser voice', got == V[1][1][:-1])
print('ALL OK' if ok else 'SOME FAILED')

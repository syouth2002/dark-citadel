"""Headless test for the FPS prototype: snapshots + cycles per frame."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H

ROOT = H.ROOT
code = open(os.path.join(ROOT, 'build', 'fps.bin'), 'rb').read()
p6 = H.P6(code)
H.fps_start(p6)
# no frame wait: patch "cp FRAME_TICKS" in wait_flip
mp = dict((l.split(': ')[1].strip().lstrip('.'), int(l.split(':')[0], 16))
          for l in open(os.path.join(ROOT, 'build', 'fps.map')))
wf = mp['wf_1']
for a in range(wf, wf + 20):
    if p6.mem[a] == 0xFE and p6.mem[a + 1] == 20:
        p6.mem[a + 1] = 1
        break
K = H
script = [(0, 20, 0), (20, 60, K.K_UP), (60, 100, K.K_RIGHT), (100, 160, K.K_UP),
          (160, 190, K.K_LEFT), (190, 260, K.K_UP | K.K_LEFT)]
snaps = {30, 80, 150, 250}
for f in range(260):
    p6.stick = 0
    for a, b, k in script:
        if a <= f < b:
            p6.stick = k
    n = len(p6.flips)
    while len(p6.flips) == n:
        p6.run_cycles(4000)
    if f in snaps:
        p6.image().save(os.path.join(ROOT, 'build', 'fps_%03d.png' % f))
fl = p6.flips
d = sorted(fl[i + 1] - fl[i] for i in range(5, len(fl) - 1))
print('frames', len(fl), 'cycles/frame p50 %d p90 %d max %d -> %.1f fps' %
      (d[len(d) // 2], d[len(d) * 9 // 10], d[-1], H.CLOCK / d[len(d) // 2]))

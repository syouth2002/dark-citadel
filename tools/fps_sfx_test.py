"""Sound effects: latency from a key press, channel separation, clean endings."""
import os
import sys
sys.argv = sys.argv[:1] + ['0']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H

ROOT = H.ROOT
code = open(os.path.join(ROOT, 'build', 'fps.bin'), 'rb').read()
V = {}
for l in open(os.path.join(ROOT, 'src', 'fps_vars.inc')):
    if l.startswith('v_'):
        n, _, v = l.split()
        V[n[2:]] = int(v.rstrip('h'), 16)
CPU = 3993600                      # Z80 clock (Hz)
ok = True


def check(name, cond, info=''):
    global ok
    ok &= bool(cond)
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + info if info else ''), flush=True)


def boot():
    p6 = H.P6(code)
    H.fps_start(p6)
    log = []
    orig = p6.out

    def out(port, value):
        orig(port, value)
        if port & 0xFF == 0xA1:
            log.append((p6.cycles, p6.psg_reg, value))
    p6.m.set_output_callback(out)
    return p6, log


def frame(p6):
    c = len(p6.flips)
    spent = 0
    while len(p6.flips) == c and spent < 600000:
        p6.run_cycles(2000)
        spent += 2000


# 1. fire: the shot must sound within the frame that sees the key
p6, log = boot()
for _ in range(6):
    frame(p6)
m = p6.mem
t0 = p6.cycles
p6.stick = 0x80                    # SPACE
del log[:]
f0 = len(p6.flips)
while not any(r == 8 and v > 0 for _, r, v in log) and p6.cycles - t0 < 4 * CPU:
    p6.run_cycles(500)
hit = [c for c, r, v in log if r == 8 and v > 0]
lat = (hit[0] - t0) * 1000 / CPU if hit else 9999
fl = len(p6.flips) - f0
check('shot sounds on channel A', hit)
check('shot latency within one frame', fl <= 1, '(%.0f ms, %d flips)' % (lat, fl))
# nothing on B / C for a plain shot into the air
p6.stick = 0
for _ in range(20):                          # (frames are quick standing still)
    frame(p6)
check('no stray sound on B', not any(r == 9 and v > 0 for _, r, v in log))
check('shot ends: channel A silent', p6.psg[8] == 0)
check('mixer: effects off, music tone on C', p6.psg[7] == 0xBB, '%02X' % p6.psg[7])
# music on channel C
c_notes = [v for _, r, v in log if r == 4]
c_vol = [v for _, r, v in log if r == 10]
check('music plays on channel C', len(set(c_notes)) >= 3 and max(c_vol) >= 9,
      '(%d notes, vol max %d)' % (len(c_notes), max(c_vol or [0])))
# 2. empty gun: click only on a new press
m[V['ammo']] = 0
del log[:]
p6.stick = 0x80
frame(p6)
frame(p6)
clicks = [v for _, r, v in log if r == 8 and v > 0]
check('empty click once', len(clicks) == 1, str(clicks))
p6.stick = 0

# 3. hurt -> channel B, enemy sounds -> channel C
import fps_testlib as T
E = V['enemies']
for i in range(24):
    m[E + i * 16] = 0
ox, oy = T.find_open(T.level(0)[0], 4, 3)
del log[:]
p6.voice.played.clear()
for f in range(150):
    for nm, v in (('px', int((ox + 0.5) * 256)), ('py', int((oy + 2.5) * 256))):
        m[V[nm]] = v & 255
        m[V[nm] + 1] = v >> 8
    ex, ey = int((ox + 3.0) * 256), int((oy + 0.5) * 256)
    m[E + 0] = 2
    m[E + 1], m[E + 2] = ex & 255, ex >> 8
    m[E + 3], m[E + 4] = ey & 255, ey >> 8
    m[E + 5] = 9
    if m[E + 6] == 0:
        m[E + 6] = 1
    if m[E + 6] == 1 and m[E + 7] < 28:
        m[E + 7] = 28
    m[V['hp']] = 100
    frame(p6)
    if any(r == 9 and v > 0 for _, r, v in log):
        break
import voices
VO = dict(voices.build())
played = [f for _, f in p6.voice.played]
check('sentinel shot is a voice', played[:len(VO['orb_shot']) - 1] == VO['orb_shot'][:-1],
      '(%d frames)' % len(played))
check('speech chip without errors', p6.voice.errors == 0)
check('hurt on channel B', any(r == 9 and v == 15 for _, r, v in log))
check('health shown red', m[V['hurt']] > 0)
print('ALL OK' if ok else 'SOME FAILED')

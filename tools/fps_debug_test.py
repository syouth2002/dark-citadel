"""Debug mode: hidden command on the title, floor select, sound test, invincible."""
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


UP, DOWN, LEFT, RIGHT = H.K_UP, H.K_DOWN, H.K_LEFT, H.K_RIGHT


def press(p6, k):
    p6.stick = k
    p6.run_cycles(CPU // 10)
    p6.stick = 0
    p6.run_cycles(CPU // 10)


g = T.Game(start=False)
p6, m = g.p6, g.m
p6.run_cycles(CPU)
for k in (UP, UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT):    # one "up" too many
    press(p6, k)
check('not yet in debug mode', m[V['debug']] == 0)
press(p6, RIGHT)
check('hidden command opens the debug menu', m[V['debug']] == 1)
press(p6, UP)                                              # wraps to EXIT
check('up from the top selects EXIT', m[V['dsel']] == 4)
p6.image().save(os.path.join(T.ROOT, 'build', 'debug_menu.png'))
press(p6, H.K_SPACE)
p6.run_cycles(CPU // 2)
check('EXIT: back to the title, normal mode', m[V['debug']] == 0 and m[V['god']] == 0 and m[V['dsel']] == 4)
for k in (UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT):
    press(p6, k)
check('the command works again', m[V['debug']] == 1 and m[V['dsel']] == 0)
press(p6, DOWN)
press(p6, DOWN)
press(p6, DOWN)
press(p6, DOWN)
press(p6, DOWN)
check('down from EXIT wraps to FLOOR', m[V['dsel']] == 0)
# floor 5
for _ in range(4):
    press(p6, RIGHT)
check('floor select', m[V['dfloor']] == 4)
press(p6, LEFT)
press(p6, RIGHT)
# sound test: effect, voice, tune
press(p6, DOWN)
log = []
orig = p6.out


def out(port, value):
    orig(port, value)
    if port & 0xFF == 0xA1:
        log.append((p6.psg_reg, value))
p6.m.set_output_callback(out)
press(p6, H.K_SPACE)
check('sound 1 (shot) plays on PSG A', any(r == 8 and v > 0 for r, v in log))
for _ in range(8):
    press(p6, RIGHT)                                       # 9: husk die
p6.voice.played.clear()
press(p6, H.K_SPACE)
p6.run_cycles(CPU // 2)
check('sound 9 is a voice', m[V['dsnd']] == 8 and len(p6.voice.played) > 20)
for _ in range(12):
    press(p6, RIGHT)                                       # 21: music 2
s0 = m[V['bgm_s']] | m[V['bgm_s'] + 1] << 8
press(p6, H.K_SPACE)
s1 = m[V['bgm_s']] | m[V['bgm_s'] + 1] << 8
check('sound 21 changes the music', m[V['dsnd']] == 20 and s1 != s0)
for _ in range(21):
    press(p6, LEFT)
check('sound number wraps', m[V['dsnd']] == 23)     # (24 sounds: 21 left from 20)
# invincible on, start
press(p6, DOWN)
press(p6, RIGHT)
check('invincible on', m[V['god']] == 1)
press(p6, DOWN)
press(p6, H.K_SPACE)
g.frame(0, 4)
check('game starts on floor 5 with 99 rounds', m[V['level']] == 4 and m[V['hp']] == 100 and m[V['ammo']] == 99)
p6.image().save(os.path.join(T.ROOT, 'build', 'debug_game.png'))
# a husk claws: hurt (sound, red) but no damage
cells, _, _ = T.level(4)
ox, oy = T.find_open(cells, 4, 3)
E = V['enemies']
for i in range(24):
    m[E + i * 16] = 0
hurt = False
for f in range(60):
    g.setw('px', (ox + 0.5) * 256)
    g.setw('py', (oy + 1.5) * 256)
    ex, ey = int((ox + 1.4) * 256), int((oy + 1.5) * 256)
    m[E], m[E + 1], m[E + 2], m[E + 3], m[E + 4], m[E + 5] = 1, ex & 255, ex >> 8, ey & 255, ey >> 8, 9
    if m[E + 6] == 0:
        m[E + 6] = 1
    g.frame()
    if m[V['hurt']]:
        hurt = True
        break
check('invincible: hit, but health stays 100', hurt and m[V['hp']] == 100)
# to the end: no best time from a debug game
for lv in range(4, NL):
    cells, _, _ = T.level(lv)
    ex = next((x, y) for (x, y), v in cells.items() if v == 7)
    if lv == LAST:                     # the warden (tested in fps_boss_test): gone
        for i in range(24):
            if m[E + i * 16] == 5:
                m[E + i * 16] = 0
        m[V['boss']] = 0
    g.approach(*ex)
    if lv == LAST:
        g.leave_ending()             # the dawn, then the tally
    else:
        g.frame(0, 2)
        g.frame(H.K_SPACE, 2)
        g.frame(0, 4)
check('debug game ends without a best time', m[V['level']] == LAST and g.getw('best') == 0)
p6.run_cycles(CPU)
check('back on the title: debug mode off', m[V['debug']] == 0 and m[V['god']] == 0)
print('ALL OK' if ok else 'SOME FAILED')

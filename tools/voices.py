"""Original enemy voices for DARK CITADEL, for the PC-6001mkII speech chip
(uPD7752, external parameter mode, 10 ms frames).

Each voice is a list of frame targets; compile() turns them into the chip's
7-byte frames (deltas from the previous frame, as the chip expects), starting
from the chip's state after a mode set.  Run this file to preview the voices
as WAV files in build/voices/.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d7752sim as S

MODE = 0                      # 10 ms frames, normal speed

# formant stages (index into the chip's coefficient table, see d7752sim.resonance)
#   stage 0: top (~4 kHz)  1: F1  2: F3  3: F2  4: a low extra resonance
VOW = {
    'a':  [124, 94, 116, 104, 90],     # F1 ~750 Hz, F2 ~1280
    'o':  [124, 84, 116, 97, 88],      # F1 ~520,  F2 ~900
    'u':  [124, 78, 114, 95, 84],      # F1 ~440,  F2 ~780
    'e':  [124, 66, 120, 114, 100],    # F1 ~360,  F2 ~2200 (eerie "ee")
    'h':  [126, 92, 118, 106, 98],     # breath
    's':  [126, 116, 124, 120, 112],   # hiss (high resonances)
}
B_V = [9, 5, 7, 6, 9]                  # voiced: fairly sharp
B_N = [11, 9, 9, 9, 11]                # noise: wide


def mix(a, b, t):
    return [round(x + (y - x) * t) for x, y in zip(VOW[a], VOW[b])]


def fr(f, amp, pitch, voiced=True, b=None, rough=False):
    return dict(f=f, b=b or (B_V if voiced else B_N), amp=amp, pitch=pitch, voiced=voiced,
                rough=rough)


def husk_hit():
    """short pained grunt: breath into 'ah', falling"""
    v = [fr(VOW['h'], 10, 30, False)]
    for i, a in enumerate([13, 13, 12, 11, 9, 6, 3]):
        v.append(fr(mix('a', 'u', i / 6), a, 33 + i * 3, True))
    return v


def husk_die():
    """long falling groan 'aah-ooh-uuh', roughened by breath frames"""
    v = [fr(VOW['h'], 11, 30, False)]
    n = 34
    for i in range(n):
        t = i / (n - 1)
        a = 13 if i < 10 else max(2, round(13 - (i - 10) * 0.5))
        f = mix('a', 'o', t * 2) if t < 0.5 else mix('o', 'u', (t - 0.5) * 2)
        v.append(fr(f, a, 30 + 3 * (i + 1), voiced=(i % 4 != 3)))
    return v


def husk_claw():
    """attack snarl: rough 'khh' then a short 'ha'"""
    v = [fr(VOW['h'], 14, 30, False), fr(VOW['h'], 15, 30, False), fr(VOW['a'], 14, 30, False)]
    for i, a in enumerate([13, 12, 9, 5]):
        v.append(fr(VOW['a'], a, 33 + 3 * i, True))
    return v


# The sentinel's voice is electric: its pitch rises (the period shrinks),
# which on this chip also mixes noise in - a buzzing, crackling tone.
def orb_hit():
    """sentinel hit: a short rising squeak"""
    return [fr(VOW['o'], a, 30 - 4 * (i + 1), True, rough=True) for i, a in enumerate([8, 9, 7, 5, 2])]


def orb_die():
    """sentinel destroyed: a squeal rising until it breaks into a low crackle"""
    v = []
    for i, a in enumerate([7, 8, 9, 9, 9, 9, 9, 9]):
        v.append(fr(mix('u', 'o', i / 7), a, 30 - 4 * (i + 1), True, rough=True))
    for i in range(14):
        v.append(fr(mix('o', 'u', i / 13), max(2, 10 - (i * 2) // 3), -40, True, rough=True))
    return v


def orb_shot():
    """sentinel fires: a quick rising zap"""
    return [fr(mix('u', 'a', i / 5), a, 30 - 4 * (i + 1), True, rough=True)
            for i, a in enumerate([7, 8, 8, 6, 4, 2])]


def brute_hit():
    """brute hit: a deep, short grunt"""
    v = [fr(VOW['h'], 11, 30, False)]
    for i, a in enumerate([11, 11, 10, 8, 6, 3]):
        v.append(fr(mix('o', 'u', i / 5), a, 33 + 3 * i, True))
    return v


def brute_die():
    """brute falls: a long low roar breaking into breath"""
    v = [fr(VOW['h'], 12, 30, False)]
    for i in range(18):
        a = 11 if i < 6 else max(3, 11 - (i - 6) // 2)
        v.append(fr(mix('o', 'u', i / 17), a, 33 + 3 * i, voiced=(i % 3 != 2)))
    for a in [9, 7, 5, 3]:
        v.append(fr(VOW['h'], a, 0, False))
    return v


def stalk_hit():
    """stalker hit: a sharp rising shriek"""
    return [fr(mix('a', 'e', 0.3), a, 30 - 4 * (i + 1), True, rough=True)
            for i, a in enumerate([11, 12, 12, 10, 6])]


def stalk_die():
    """stalker destroyed: a shriek that tears into a hiss"""
    v = [fr(mix('a', 'e', 0.3 + i / 20), a, 30 - 4 * (i + 1), True, rough=True)
         for i, a in enumerate([11, 12, 12, 12, 11, 10, 9])]
    for a in [12, 11, 9, 7, 5, 3]:
        v.append(fr(VOW['h'], a, 0, False))
    return v


def warden_hit():
    """the warden hit: a short metallic roar"""
    v = [fr(VOW['h'], 12, 30, False)]
    for i, a in enumerate([10, 11, 10, 8, 5]):
        v.append(fr(mix('a', 'o', i / 4), a, 30 - 4 * (i + 1), True, rough=True))
    return v


def warden_die():
    """the warden falls: a roar that sinks and breaks into a long hiss"""
    v = []
    for i in range(10):
        v.append(fr(mix('a', 'o', i / 9), 11, 30 - 4 * (i + 1), True, rough=True))
    for i in range(10):
        v.append(fr(mix('o', 'u', i / 9), max(4, 11 - i // 2), -40, True, rough=True))
    for a in [12, 11, 10, 9, 8, 6, 5, 4, 3, 2]:
        v.append(fr(VOW['h'], a, 0, False))
    return v


# The bloater: wet and low; it swells with a strained rising hum and bursts.
def bloat_hit():
    """bloater hit: a short wet gurgle"""
    return [fr(mix('o', 'u', i / 5), a, 36 + 2 * i, voiced=(i % 2 == 0)) for i, a in enumerate([10, 11, 10, 8, 5, 3])]


def bloat_swell():
    """bloater swells: a strained hum rising"""
    return [fr(mix('u', 'o', i / 8), min(12, 5 + i), 30 - 4 * (i + 1), True, rough=True) for i in range(9)]


def bloat_pop():
    """bloater bursts: a loud wet pop, then a spray of hiss"""
    v = [fr(VOW['a'], 15, 30, False), fr(VOW['o'], 15, 30, False)]
    for a in [14, 12, 10, 8, 6, 4, 2]:
        v.append(fr(VOW['h'] if a >= 10 else VOW['s'], a, 0, False))
    return v


# The lamp turret: hollow and mechanical.
def turret_hit():
    """turret struck: a dull clank"""
    return [fr(VOW['o'], a, 50, True) for a in [12, 9, 6, 3]]


def turret_shot():
    """turret fires: a low hum swelling into a crack"""
    v = [fr(VOW['u'], a, 40, True) for a in [5, 8, 10]]
    v += [fr(VOW['s'], a, 0, False) for a in [13, 9, 5]]
    return v


def turret_die():
    """turret collapses: a grinding crackle sinking into rubble"""
    v = [fr(mix('o', 'u', i / 7), max(3, 12 - i), -40, True, rough=True) for i in range(8)]
    v += [fr(VOW['h'], a, 0, False) for a in [10, 8, 6, 4, 2]]
    return v


# The bat: high squeaks.
def bat_hit():
    """bat: a high squeak (hit, and its bite)"""
    return [fr(VOW['e'], a, 30 - 4 * (i + 1), True, rough=True) for i, a in enumerate([10, 12, 9, 5])]


def bat_die():
    """bat falls: a squeal rising, cut off"""
    return [fr(VOW['e'], a, 30 - 4 * (i + 1), True, rough=True) for i, a in enumerate([10, 12, 12, 11, 9, 6, 3])]


PRIORITY = {'husk_die': 2, 'orb_die': 2, 'brute_die': 2, 'stalk_die': 2, 'warden_hit': 2,
            'warden_die': 3, 'bloat_pop': 2, 'turret_die': 2, 'bat_die': 2}

VOICES = [
    ('husk_hit', husk_hit),
    ('husk_die', husk_die),
    ('husk_claw', husk_claw),
    ('orb_hit', orb_hit),
    ('orb_die', orb_die),
    ('orb_shot', orb_shot),
    ('brute_hit', brute_hit),
    ('brute_die', brute_die),
    ('stalk_hit', stalk_hit),
    ('stalk_die', stalk_die),
    ('warden_hit', warden_hit),
    ('warden_die', warden_die),
    ('bloat_hit', bloat_hit),
    ('bloat_pop', bloat_pop),
    ('bloat_swell', bloat_swell),
    ('turret_hit', turret_hit),
    ('turret_shot', turret_shot),
    ('turret_die', turret_die),
    ('bat_hit', bat_hit),
    ('bat_die', bat_die),
]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def compile_voice(spec):
    f = list(S.F_DEF)
    b = list(S.B_DEF)
    pitch = 30
    out = []
    for s in spec:
        df = [t - c for t, c in zip(s['f'], f)]
        db = [t - c for t, c in zip(s['b'], b)]
        q = any(not -16 <= d <= 15 for d in df) or any(not -4 <= d <= 3 for d in db)
        if q:
            df = [clamp(round(d / 2), -16, 15) for d in df]
            db = [clamp(round(d / 2), -4, 3) for d in db]
        p = [0] * 7
        p[0] = (1 << 3) | (4 if q else 0) | (1 if s['voiced'] else 0)
        for i in range(5):
            p[i + 1] = ((df[i] & 31) << 3) | (db[i] & 7)
            f[i] += df[i] << (1 if q else 0)
            b[i] += db[i] << (1 if q else 0)
        if s['voiced']:
            # a falling period (rising pitch) also mixes noise in: only when wanted
            dp = clamp(s['pitch'] - pitch, -4 if s['rough'] else 0, 3)
        else:
            dp = 0
        pitch += dp
        p[6] = (s['amp'] << 4) | (dp & 7)
        out.append(p)
    out.append([0] * 7)                              # end
    return out


def build():
    res = []
    for name, fn in VOICES:
        res.append((name, compile_voice(fn())))
    return res


def asm():
    d = ['; generated by tools/voices.py - original voices for the speech chip']
    d.append('voice_tbl:')
    for name, _ in build():
        d.append('        defw vc_%s' % name)
    d.append('voice_pri:                 ; a voice only cuts in on one of lower or equal rank')
    d.append('        defb ' + ','.join(str(PRIORITY.get(n, 1)) for n, _ in VOICES))
    for name, frames in build():
        d.append('vc_%s:' % name)
        for p in frames:
            d.append('        defb ' + ','.join('%d' % x for x in p))
    return '\n'.join(d) + '\n'


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    od = os.path.join(root, 'build', 'voices')
    os.makedirs(od, exist_ok=True)
    total = 0
    for name, frames in build():
        smp = S.render(frames, MODE)
        S.save_wav(os.path.join(od, name + '.wav'), smp)
        peak = max(abs(x) for x in smp)
        total += len(frames) * 7
        print('%-10s %2d frames %4d ms  peak %5d' % (name, len(frames) - 1, len(smp) // 10, peak))
    print('data %d bytes' % total)

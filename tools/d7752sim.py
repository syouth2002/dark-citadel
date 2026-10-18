"""uPD7752-style speech synthesis model (after the PC6001V emulator's engine,
cisc 2004) used to design and preview DARK CITADEL's voices offline."""
import random
import struct
import wave

AMP = [0, 1, 1, 2, 3, 4, 5, 7, 9, 13, 17, 23, 31, 42, 56, 75]
IIR1 = [11424, 11400, 11377, 11331, 11285, 11265, 11195, 11149, 11082, 11014, 10922, 10830, 10741, 10629, 10491, 10332,
        10172, 9992, 9788, 9560, 9311, 9037, 8721, 8377, 8016, 7631, 7199, 6720, 6245, 5721, 5197, 4654,
        -11245, -11200, -11131, -11064, -10995, -10905, -10813, -10700, -10585, -10447, -10291, -10108, -9924, -9722, -9470, -9223,
        -8928, -8609, -8247, -7881, -7472, -7019, -6566, -6068, -5545, -4999, -4452, -3902, -3363, -2844, -2316, -1864,
        11585, 11561, 11561, 11561, 11561, 11540, 11540, 11540, 11515, 11515, 11494, 11470, 11470, 11448, 11424, 11400,
        11377, 11356, 11307, 11285, 11241, 11195, 11149, 11082, 11014, 10943, 10874, 10784, 10695, 10583, 10468, 10332,
        10193, 10013, 9833, 9628, 9399, 9155, 8876, 8584, 8218, 7857, 7445, 6970, 6472, 5925, 5314, 4654,
        3948, 3178, 2312, 1429, 450, -543, -1614, -2729, -3883, -5066, -6250, -7404, -8500, -9497, -10359, -11038]
IIR2 = [8192, 8105, 7989, 7844, 7670, 7424, 7158, 6803, 6370, 5860, 5252, 4579, 3824, 3057, 2307, 1623,
        8193, 8100, 7990, 7844, 7672, 7423, 7158, 6802, 6371, 5857, 5253, 4576, 3825, 3057, 2309, 1617,
        -6739, -6476, -6141, -5738, -5225, -4604, -3872, -2975, -1930, -706, 686, 2224, 3871, 5518, 6992, 8085,
        -6746, -6481, -6140, -5738, -5228, -4602, -3873, -2972, -1931, -705, 685, 2228, 3870, 5516, 6993, 8084]
F_DEF = [126, 64, 121, 111, 96]
B_DEF = [9, 4, 9, 9, 11]
FS = 10000


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


class D7752:
    def __init__(self, mode=4, seed=1):
        self.n = [100, 120, 80, 100, 200, 240, 160, 200][mode & 7]
        self.f = [x << 16 for x in F_DEF]
        self.b = [x << 16 for x in B_DEF]
        self.amp = 0
        self.pitch = 30 << 16
        self.pc = 0
        self.y = [[0, 0] for _ in range(5)]
        self.rnd = random.Random(seed)

    def frame(self, p):
        q = 1 if p[0] & 4 else 0
        nf, nb = [], []
        for i in range(5):
            f = (p[i + 1] >> 3) & 31
            f = f - 32 if f & 16 else f
            nf.append(self.f[i] + ((f << q) << 16))
            b = p[i + 1] & 7
            b = b - 8 if b & 4 else b
            nb.append(self.b[i] + ((b << q) << 16))
        namp = ((p[6] >> 4) & 15) << 16
        pp = p[6] & 7
        pp = pp - 8 if pp & 4 else pp
        npitch = self.pitch + (pp << 16)
        n = self.n
        ia = tdiv(namp - self.amp, n)
        ip = tdiv(npitch - self.pitch, n)
        ib = [tdiv(nb[i] - self.b[i], n) for i in range(5)]
        iff = [tdiv(nf[i] - self.f[i], n) for i in range(5)]
        vu = 1 if p[0] & 1 else 2
        vu |= 3 if p[6] & 4 else 0
        out = []
        for _ in range(n):
            y = 0
            c = self.pitch >> 16
            if self.pc > (c if c > 0 else 128):
                if vu & 1:
                    y = AMP[self.amp >> 16] * 16 - 1
                self.pc = 0
            self.pc += 1
            if vu & 2 and self.rnd.random() < 0.5:
                y += AMP[self.amp >> 16] * 4 - 1
            for j in range(5):
                Y = self.y[j]
                t = tdiv(Y[0] * IIR1[(self.f[j] >> 16) & 127], 8192)
                y += tdiv(t * IIR1[((self.b[j] >> 16) * 2 + 1) & 127], 8192)
                y -= tdiv(Y[1] * IIR2[(self.b[j] >> 16) & 63], 8192)
                y = max(-8192, min(8191, y))
                Y[1] = Y[0]
                Y[0] = y
            out.append(y)
            self.amp += ia
            self.pitch += ip
            for j in range(5):
                self.b[j] += ib[j]
                self.f[j] += iff[j]
        self.f, self.b, self.amp, self.pitch = nf, nb, namp, npitch
        return out


def render(frames, mode=4):
    d = D7752(mode)
    s = []
    for p in frames:
        if not p[0] >> 3:
            break
        s += d.frame(p)
    return s


def save_wav(path, samples, rate=FS):
    w = wave.open(path, 'wb')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(b''.join(struct.pack('<h', max(-32768, min(32767, v * 4))) for v in samples))
    w.close()


def resonance(f, b):
    """(Hz, pole radius) of one formant stage"""
    import cmath
    a1 = IIR1[f & 127] * IIR1[(b * 2 + 1) & 127] / 8192 / 8192
    a2 = IIR2[b & 63] / 8192
    z = (a1 + cmath.sqrt(a1 * a1 - 4 * a2)) / 2
    return abs(cmath.phase(z)) * FS / (2 * 3.14159265), abs(z)

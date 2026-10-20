"""Shared helpers for the DARK CITADEL headless tests (24x24 floors)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import fps_gen
import fps_levels

ROOT = H.ROOT
N = fps_gen.MAPN                 # floor size
S = fps_gen.MAPS                 # row stride in RAM
V = {}
for _l in open(os.path.join(ROOT, 'src', 'fps_vars.inc')):
    if _l.startswith('v_'):
        _n, _, _v = _l.split()
        V[_n[2:]] = int(_v.rstrip('h'), 16)
    elif _l.startswith('NEN '):
        NEN = int(_l.split()[2])        # object slots
for _l in open(os.path.join(ROOT, 'src', 'fps_blob.inc')):
    if _l.startswith('RAM_DATA '):
        RAM_DATA = int(_l.split()[2].rstrip('h'), 16)   # where the low-RAM data unpacks
LEVELS = fps_levels.all_levels()


def level(i):
    """(cells as {(x, y): value}, objects [(type, x, y)], start (x, y)) of floor i"""
    cells, objs, start = fps_gen.parse_level(LEVELS[i][1])
    return {(k % N, k // N): v for k, v in enumerate(cells)}, objs, start


def code(name='fps'):
    return open(os.path.join(ROOT, 'build', name + '.bin'), 'rb').read()


class Game:
    def __init__(self, name='fps', start=True):
        self.p6 = H.P6(code(name))
        self.m = self.p6.mem
        if start:
            H.fps_start(self.p6)

    def frame(self, k=0, n=1):
        p6 = self.p6
        for _ in range(n):
            p6.stick = k
            c = len(p6.flips)
            spent = 0
            while len(p6.flips) == c and spent < 2000000:
                p6.run_cycles(4000)
                spent += 4000

    def cell(self, x, y):
        return self.m[V['map'] + y * S + x]

    def set_cell(self, x, y, v):
        self.m[V['map'] + y * S + x] = v

    def setw(self, name, v):
        v = int(v) & 0xFFFF
        self.m[V[name]] = v & 255
        self.m[V[name] + 1] = v >> 8

    def getw(self, name):
        return self.m[V[name]] | self.m[V[name] + 1] << 8

    def put(self, x, y, a, again=True):
        """teleport the player to (x, y) in cells (float), angle a (0 east, 64 south)"""
        want = (int(x * 256) & 0xFFFF, int(y * 256) & 0xFFFF, a)
        for _ in range(6):
            self.setw('px', want[0])
            self.setw('py', want[1])
            self.m[V['pa']] = a
            if not again:
                return
            # the CPU may have been inside move_player (it reads the position
            # and writes it back): run a frame and set again until it holds
            self.frame(0)
            if (self.getw('px'), self.getw('py'), self.m[V['pa']]) == want:
                return
        raise RuntimeError('could not place the player')

    def god(self):
        self.m[V['hp']] = 100

    def msg(self):
        a = self.getw('msg')
        s = bytes(self.m[a:a + 40]).split(b'\0')[0].decode().strip()
        return s if self.m[V['msg_t']] else ''

    def press(self, k, cycles=800000):
        """hold a key a while, then let go (for screens without frames)"""
        self.p6.stick = k
        self.p6.run_cycles(cycles)
        self.p6.stick = 0
        self.p6.run_cycles(cycles)

    def leave_ending(self):
        """after the last floor's exit: skip the dawn, leave it, leave the tally"""
        for _ in range(3):
            self.press(H.K_SPACE)

    def approach(self, tx, ty, steps=8):
        """step into cell (tx, ty) from a free neighbour, facing it"""
        for dx, dy, ang in ((-1, 0, 0), (1, 0, 128), (0, -1, 64), (0, 1, 192)):
            sx, sy = tx + dx, ty + dy
            if 0 <= sx < N and 0 <= sy < N and self.cell(sx, sy) == 0:
                self.put(sx + 0.5, sy + 0.5, ang)
                self.god()
                self.frame(H.K_UP, steps)
                return True
        return False


def find_between(cells, kind, gap=1, side=1):
    """a cell of the given kinds with `side` floor cells on the left and right
    (and `gap` = its width) -> (x, y) of the cell"""
    for (x, y), v in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if v not in kind:
            continue
        if all(cells.get((x - k, y)) == 0 for k in range(1, side + 1)) and \
           all(cells.get((x + k, y)) == 0 for k in range(1, side + 1)):
            return x, y
    return None


def find_open(cells, w, h):
    """top-left (x, y) of a w x h block of floor"""
    for y in range(N - h):
        for x in range(N - w):
            if all(cells.get((x + i, y + j)) == 0 for i in range(w) for j in range(h)):
                return x, y
    return None

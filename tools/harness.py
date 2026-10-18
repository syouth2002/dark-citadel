"""Headless test harness: a minimal PC-6001mkII model (Z80, memory, mode 5
screen, timer and key interrupts, PSG, the speech chip) for running the game
in tests (tools/fps_testlib.py)."""
import os
import random
import sys

import z80
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOCK = 3993600
TIMER = 7987
PROF = [] if os.environ.get('PROF') else None                      # 2 ms

RGB = [0x141414, 0x8000FF, 0xFFAC00, 0xFF00AC, 0x00FFAC, 0x00ACFF, 0xACFF00, 0xACACAC,
       0x141414, 0x0000FF, 0xFF0000, 0xFF00FF, 0x00FF00, 0x00FFFF, 0xFFFF00, 0xFFFFFF]

# STICK bits (keyboard)
K_SPACE, K_LEFT, K_RIGHT, K_DOWN, K_UP, K_STOP, K_SHIFT = 0x80, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01


class P6:
    def __init__(self, code, seed=1):
        self.m = z80.Z80Machine()
        self.m.set_memory_block(0x4000, code)
        self.m.pc = 0x4000
        self.mem = self.m.memory
        self.b0 = 0
        self.psg_reg = 0
        self.psg = [0] * 16
        self.pending = []
        self.stick = 0
        self.cycles = 0
        self.next_timer = TIMER
        self.flips = []
        self.timer_vec = 0x06
        self.m.set_output_callback(self.out)
        self.m.set_input_callback(self.inp)
        self.m.set_get_int_vector_callback(self.vec)
        self.cur_vec = 0
        self.rnd = random.Random(seed)
        self.psg_writes = 0
        self.keyq = []
        self.keyq_active = False
        self.voice = Voice(self)
        self.min_sp = 0x10000            # lowest stack pointer seen (sampled)

    def out(self, port, value):
        p = port & 0xFF
        if p == 0xB0:
            self.b0 = value
            self.flips.append(self.cycles)
        elif p == 0x90:
            if value == 0x06:
                self.pending.append(0x16)
        elif p == 0xA0:
            self.psg_reg = value & 0x0F
        elif p == 0xA1:
            self.psg[self.psg_reg] = value
            self.psg_writes += 1
        elif p == 0xF7:
            self.timer_vec = value
        elif p in (0xE0, 0xE2, 0xE3):
            self.voice.out(p, value)

    def inp(self, port):
        p = port & 0xFF
        if p == 0x92:
            return 0xFF
        if p == 0x90:
            if self.keyq_active:
                self.keyq_active = False
                return self.keyq.pop(0)
            return self.stick
        if p == 0xE0:
            return self.voice.stat
        if p == 0xA2:
            if self.psg_reg == 14:
                return 0xFF
            return self.psg[self.psg_reg]
        return 0xFF

    def vec(self):
        return self.cur_vec

    def run_cycles(self, n):
        end = self.cycles + n
        while self.cycles < end:
            self.m.ticks_to_stop = 400
            self.m.run()
            self.cycles += 400
            if self.m.sp < self.min_sp:
                self.min_sp = self.m.sp
            if PROF is not None:
                PROF.append(self.m.pc)
            if self.voice.next and self.cycles >= self.voice.next:
                self.voice.event()
            if self.cycles >= self.next_timer:
                self.next_timer += TIMER
                if self.timer_vec not in self.pending:
                    self.pending.append(self.timer_vec)
            if self.pending and self.m.iff1 and not self.m.int_disabled:
                self.cur_vec = self.pending[0]
                self.m.on_handle_active_int()
                if not self.m.iff1:
                    v = self.pending.pop(0)
                    if v == 0x02:
                        self.keyq_active = True

    def run_until_flip(self, maxc=4000000):
        n = len(self.flips)
        start = self.cycles
        while len(self.flips) == n and self.cycles - start < maxc:
            self.run_cycles(2000)

    def image(self):
        base = [0x8000, 0xC000, 0x0000, 0x4000][(self.b0 >> 1) & 3]
        img = Image.new('RGB', (160, 200))
        px = img.load()
        mem = self.mem
        for y in range(200):
            for xb in range(40):
                a = mem[base + y * 40 + xb]
                b = mem[base + 0x2000 + y * 40 + xb]
                for k in range(4):
                    sh = 6 - 2 * k
                    v = ((a >> sh) & 3) | (((b >> sh) & 3) << 2)
                    c = RGB[v]
                    px[xb * 4 + k, y] = (c >> 16, (c >> 8) & 255, c & 255)
        return img.resize((640, 400), Image.NEAREST)


class Voice:
    """speech chip (uPD7752, external mode) as the PC6001V emulator models it"""
    BSY, REQ, EXT, ERR = 0x80, 0x40, 0x20, 0x10

    def __init__(self, p6):
        self.p6 = p6
        self.stat = 0
        self.next = 0
        self.frame_c = 39936          # 10 ms
        self.buf = [0] * 7
        self.pnum = self.fnum = 0
        self.ready = False
        self.played = []              # (cycle, 7 parameter bytes) per frame synthesised
        self.errors = 0

    def abort(self):
        self.next = 0
        self.pnum = self.fnum = 0
        self.ready = False
        self.stat &= ~self.BSY

    def out(self, p, v):
        if p == 0xE2:                 # mode
            self.frame_c = 79872 if v & 4 else 39936
            self.stat = 0
        elif p == 0xE3:               # command
            self.abort()
            if v == 0xFE:
                self.next = self.p6.cycles + self.frame_c
                self.stat = self.BSY | self.EXT | self.REQ
        elif p == 0xE0 and self.stat & self.BSY and self.stat & self.REQ:
            if self.fnum == 0 or self.pnum:
                if self.pnum == 0:
                    self.fnum = v >> 3
                self.buf[self.pnum] = v
                self.pnum += 1
                if self.pnum == 7:
                    self.stat &= ~self.REQ
                    self.pnum = 0
                    if self.fnum:
                        self.fnum -= 1
                    self.ready = True
            else:
                self.buf[1:6] = [0] * 5
                self.buf[6] = v
                self.stat &= ~self.REQ
                self.fnum -= 1
                self.ready = True

    def event(self):
        self.next += self.frame_c
        if not self.ready:
            self.abort()
            self.stat = self.ERR
            self.errors += 1
            return
        if not self.buf[0] >> 3:
            self.abort()
            return
        self.played.append((self.p6.cycles, list(self.buf)))
        self.ready = False
        self.stat |= self.REQ


def fps_start(p6, auto_map=False):
    """DARK CITADEL: get past the title screen (map mode, then SPACE)"""
    cpu = 3993600
    p6.stick = 0
    p6.run_cycles(cpu)
    if auto_map:
        p6.stick = 0x08                 # down: auto map
        p6.run_cycles(cpu // 5)
        p6.stick = 0
        p6.run_cycles(cpu // 5)
    p6.stick = 0x80
    p6.run_cycles(cpu // 5)
    p6.stick = 0
    n = len(p6.flips)
    while len(p6.flips) < n + 2:
        p6.run_cycles(4000)

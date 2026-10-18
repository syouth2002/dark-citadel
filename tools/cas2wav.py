"""Convert a .cas image to a WAV for a real PC-6001mkII.

PC-6001 cassette format (1200 baud FSK):
  bit 0 = one cycle of 1200 Hz, bit 1 = two cycles of 2400 Hz
  byte  = start bit (0) + 8 data bits (LSB first) + 3 stop bits (1)
Idle line / leader = continuous 2400 Hz (mark).

Layout written:
  leader 4.0s | header (D3 x10 + name) | leader 1.0s | BASIC loader + trailer
  | leader 2.0s | game block (FF.. C9 addr len data) | leader 0.5s
usage: python cas2wav.py fps.cas fps.wav
"""
import math
import struct
import sys

RATE = 48000
AMP = 100


def cyc(freq):
    n = RATE // freq
    return bytes(128 + int(AMP * math.sin(2 * math.pi * i / n)) for i in range(n))


C1200 = cyc(1200)
C2400 = cyc(2400)
BIT0 = C1200
BIT1 = C2400 * 2


def leader(sec):
    return BIT1 * int(1200 * sec)


def byte(b):
    out = bytearray(BIT0)
    for i in range(8):
        out += BIT1 if (b >> i) & 1 else BIT0
    out += BIT1 * 3
    return bytes(out)


def main():
    cas = open(sys.argv[1], 'rb').read()
    # split: header 16 bytes, BASIC (until first FF run of the game block)
    head = cas[:16]
    i = cas.index(b'\xFF' * 16, 16)
    basic = cas[16:i]
    game = cas[i:]
    pcm = bytearray()
    pcm += leader(4.0)
    for b in head:
        pcm += byte(b)
    pcm += leader(1.0)
    for b in basic:
        pcm += byte(b)
    pcm += leader(2.0)
    for b in game:
        pcm += byte(b)
    pcm += leader(0.5)
    with open(sys.argv[2], 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(pcm)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 1, RATE, RATE, 1, 8))
        f.write(b'data' + struct.pack('<I', len(pcm)))
        f.write(pcm)
    print('%s: %.1f s' % (sys.argv[2], len(pcm) / RATE))


if __name__ == '__main__':
    main()

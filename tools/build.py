"""Build a PC-6001mkII (mode 5) cassette image.

Tape layout:
  [D3 x10][name 6]  BASIC loader (N60m-BASIC tokenized)  [00 x 11]
  [FF x 64] C9 <load addr L,H> <length L,H> <binary...> [00 x 16]

The BASIC loader pokes a small machine-language stub at &HF000 and EXECs it.
The stub reads the binary block with the BASIC ROM cassette routines
(1A61h open / 1A70h read byte / 1AAAh close), maps RAM over the ROM area
(port F0h = DDh) and jumps to the program entry.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# N60m-BASIC tokens used by the loader
T_FOR, T_NEXT, T_DATA, T_READ, T_POKE = 0x81, 0x82, 0x83, 0x86, 0x94
T_PRINT, T_CLEAR, T_EXEC, T_TO, T_EQ = 0x95, 0x99, 0xA5, 0xC3, 0xD2

STUB_ADDR = 0xF000
LOAD_ADDR = 0x4000
LOAD_TOP = 0xC000             # (8000h-BFFFh: the loader's BASIC text, free once it runs)
BASIC_START = 0x8001          # mode 5, any page count is relinked below


def stub(entry):
    s = []
    def emit(*b):
        s.extend(b)
    emit(0xCD, 0x61, 0x1A)                  # call 1A61h  cassette open
    l1 = len(s)
    emit(0xCD, 0x70, 0x1A, 0xFE, 0xFF)      # call 1A70h / cp 0FFh
    emit(0x20, (l1 - (len(s) + 2)) & 0xFF)  # jr nz,l1
    l2 = len(s)
    emit(0xCD, 0x70, 0x1A, 0xFE, 0xC9)      # call 1A70h / cp 0C9h
    emit(0x20, (l2 - (len(s) + 2)) & 0xFF)  # jr nz,l2
    emit(0xCD, 0x70, 0x1A, 0x6F)            # l
    emit(0xCD, 0x70, 0x1A, 0x67)            # h
    emit(0xCD, 0x70, 0x1A, 0x5F)            # e
    emit(0xCD, 0x70, 0x1A, 0x57)            # d
    l3 = len(s)
    emit(0xCD, 0x70, 0x1A, 0x77, 0x23, 0x1B, 0x7A, 0xB3)  # (hl)=a, hl++, de--
    emit(0x20, (l3 - (len(s) + 2)) & 0xFF)  # jr nz,l3
    emit(0xCD, 0xAA, 0x1A)                  # call 1AAAh  cassette close
    emit(0xF3)                              # di
    emit(0x3E, 0xDD, 0xD3, 0xF0)            # out (0F0h),0DDh : RAM at 0000-7FFF
    emit(0xC3, entry & 0xFF, entry >> 8)    # jp entry
    return bytes(s)


def basic_line(num, body):
    return num, bytes(body)


def txt(s):
    return list(s.encode('ascii'))


def make_basic(stub_bytes, title):
    end = STUB_ADDR + len(stub_bytes) - 1
    lines = []
    lines.append((10, [T_CLEAR] + txt('50,&HF000')))
    lines.append((20, [T_PRINT] + txt('"' + title + '"')))
    lines.append((30, [T_FOR] + txt('I') + [T_EQ] + txt('&HF000') + [T_TO] +
                  txt('&H%04X:' % end) + [T_READ] + txt('A:') + [T_POKE] +
                  txt('I,A:') + [T_NEXT]))
    lines.append((40, [T_PRINT] + txt('"LOADING..."') + txt(':') + [T_EXEC] +
                  txt('&HF000')))
    data = list(stub_bytes)
    num = 100
    while data:
        chunk, data = data[:16], data[16:]
        lines.append((num, [T_DATA] + txt(','.join(str(b) for b in chunk))))
        num += 10
    out = bytearray()
    addr = BASIC_START
    for n, body in lines:
        size = 2 + 2 + len(body) + 1
        nxt = addr + size
        out += bytes([nxt & 0xFF, nxt >> 8, n & 0xFF, n >> 8]) + bytes(body) + b'\x00'
        addr = nxt
    out += b'\x00\x00'
    return bytes(out)


def build(asm, cas, name, title, entry=LOAD_ADDR):
    bdir = os.path.join(ROOT, 'build')
    os.makedirs(bdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(asm))[0]
    binf = os.path.join(bdir, base + '.bin')
    mapf = os.path.join(bdir, base + '.map')
    r = subprocess.run(['zxbasm', asm, '-o', binf, '-M', mapf], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(binf):
        print(r.stdout, r.stderr)
        sys.exit(1)
    if r.stderr.strip():
        print(r.stderr)
    code = open(binf, 'rb').read()
    if LOAD_ADDR + len(code) > LOAD_TOP:
        sys.exit('binary too large: %d bytes' % len(code))
    st = stub(entry)
    tape = bytearray()
    tape += b'\xD3' * 10 + name.encode('ascii').ljust(6, b'\x00')[:6]
    tape += make_basic(st, title)
    tape += b'\x00' * 9
    tape += b'\xFF' * 64 + b'\xC9'
    tape += bytes([LOAD_ADDR & 0xFF, LOAD_ADDR >> 8, len(code) & 0xFF, len(code) >> 8])
    tape += code
    tape += b'\x00' * 16
    open(cas, 'wb').write(tape)
    print('%s: code %d bytes (%04X-%04X), tape %d bytes' %
          (cas, len(code), LOAD_ADDR, LOAD_ADDR + len(code) - 1, len(tape)))
    return code


if __name__ == '__main__':
    asm = sys.argv[1]
    cas = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else 'GAME'
    title = sys.argv[4] if len(sys.argv) > 4 else name
    build(asm, cas, name, title)

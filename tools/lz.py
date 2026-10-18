"""Small LZ77 for DARK CITADEL's data (decoded at start-up by unlz in fps.asm).

Stream of commands:
  00h-7Fh  n      : n+1 literal bytes follow
  81h-FFh  n lo hi: copy (n & 7Fh) + 2 bytes from (output - offset)
  80h             : end
"""


def compress(data):
    out = bytearray()
    lit = bytearray()
    heads = {}
    i = 0
    n = len(data)

    def flush():
        nonlocal lit
        while lit:
            chunk = lit[:128]
            out.append(len(chunk) - 1)
            out.extend(chunk)
            lit = lit[128:]

    while i < n:
        best_len, best_off = 0, 0
        if i + 3 <= n:
            key = bytes(data[i:i + 3])
            for j in reversed(heads.get(key, [])[-64:]):
                ln = 0
                while ln < 129 and i + ln < n and data[j + ln] == data[i + ln]:
                    ln += 1
                if ln > best_len:
                    best_len, best_off = ln, i - j
                    if ln == 129:
                        break
        if best_len >= 3:
            flush()
            out.append(0x80 | (best_len - 2))
            out.append(best_off & 255)
            out.append(best_off >> 8)
            for k in range(i, i + best_len):
                if k + 3 <= n:
                    heads.setdefault(bytes(data[k:k + 3]), []).append(k)
            i += best_len
        else:
            if i + 3 <= n:
                heads.setdefault(bytes(data[i:i + 3]), []).append(i)
            lit.append(data[i])
            i += 1
    flush()
    out.append(0x80)
    return bytes(out)


def decompress(blob):
    out = bytearray()
    i = 0
    while True:
        c = blob[i]
        i += 1
        if c == 0x80:
            return bytes(out)
        if c < 0x80:
            out.extend(blob[i:i + c + 1])
            i += c + 1
        else:
            ln = (c & 0x7F) + 2
            off = blob[i] | blob[i + 1] << 8
            i += 2
            for _ in range(ln):
                out.append(out[-off])

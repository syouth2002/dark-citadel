"""Compact floor encoding for DARK CITADEL (decoded by start_level).

A floor is drawn as: walls all round, floor inside, then
  runs     3 bytes each: b0 = x | dir << 5 | type << 6   (dir 1 = down)
                         b1 = y | (len-1) << 5 (low 3 bits)
                         b2 = (len-1) >> 3 | door << 2  (door: 1-based cell of
                              the run that is a plain door, 0 = none)
           FFh ends them
  specials 2 bytes each: b0 = x | (cell - 4) << 5, b1 = y   (doors 4-6, exit 7)
           FFh ends them
  objects  2 bytes each: b0 = x | (type & 7) << 5, b1 = y | (type >> 3) << 5
"""
N = 24


def encode_map(cells):
    """cells: N*N values -> bytes; checked by decoding again"""
    g = {(k % N, k // N): v for k, v in enumerate(cells)}
    inner = lambda x, y: 1 <= x < N - 1 and 1 <= y < N - 1
    todo = {c for c, v in g.items() if inner(*c) and v}
    walls = {c for c in todo if g[c] in (1, 2, 3)}
    runs, covered = [], set()
    for dir_, (dx, dy) in ((0, (1, 0)), (1, (0, 1))):
        for c in sorted(walls, key=lambda c: (c[1], c[0]) if dir_ == 0 else (c[0], c[1])):
            if c in covered:
                continue
            t = g[c]
            cells_ = [c]
            door = 0
            x, y = c
            while True:
                n = (x + dx, y + dy)
                if not inner(*n):
                    break
                if g.get(n) == t and n not in covered:
                    cells_.append(n)
                elif g.get(n) == 4 and not door and g.get((n[0] + dx, n[1] + dy)) == t:
                    cells_.append(n)
                    door = len(cells_)
                else:
                    break
                x, y = n
            if len(cells_) < 2 and dir_ == 0:
                continue                      # leave single cells to the down pass
            covered.update(cells_)
            runs.append((c[0], c[1], dir_, t, len(cells_), door))
    assert walls <= covered, 'walls left over'
    out = bytearray()
    for x, y, d, t, ln, door in runs:
        out += bytes([x | d << 5 | t << 6, y | ((ln - 1) & 7) << 5, (ln - 1) >> 3 | door << 2])
    out.append(0xFF)
    door_cells = {c for r in runs if r[5] for c in [((r[0] + (r[5] - 1) * (1 - r[2])), r[1] + (r[5] - 1) * r[2])]}
    for c in sorted(c for c in g if g[c] in (4, 5, 6, 7) and c not in door_cells):
        out += bytes([c[0] | (g[c] - 4) << 5, c[1]])
    out.append(0xFF)
    assert decode_map(bytes(out)) == list(cells), 'map does not decode back'
    return bytes(out)


def decode_map(data):
    m = [1 if x in (0, N - 1) or y in (0, N - 1) else 0 for y in range(N) for x in range(N)]
    i = 0
    while data[i] != 0xFF:
        b0, b1, b2 = data[i:i + 3]
        i += 3
        x, d, t = b0 & 31, (b0 >> 5) & 1, b0 >> 6
        y, ln, door = b1 & 31, ((b1 >> 5) | (b2 & 3) << 3) + 1, b2 >> 2
        for k in range(ln):
            cx, cy = (x + k, y) if d == 0 else (x, y + k)
            m[cy * N + cx] = 4 if k + 1 == door else t
    i += 1
    while data[i] != 0xFF:
        b0, b1 = data[i:i + 2]
        i += 2
        m[b1 * N + (b0 & 31)] = (b0 >> 5) + 4
    return m


def encode_objs(objs):
    out = bytearray()
    for ty, x, y in objs:
        out += bytes([x | (ty & 7) << 5, y | (ty >> 3) << 5])
    return bytes(out)

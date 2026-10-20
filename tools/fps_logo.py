"""The title logo of DARK CITADEL (an original design): the citadel's towers
in silhouette against the night, lit windows, a crescent moon, and the name
in cold blue in front.  Drawn in the mode 5 colours (dots twice as wide as
tall); fps_gen.py stores it in the program, compressed, one stream a plane.
    python fps_logo.py   (writes build/logo.png to look at)"""

BLACK, PURPLE, ORANGE, SKY, GREY = 0, 1, 2, 5, 7
BLUE, CYAN, YELLOW, WHITE = 9, 13, 14, 15

W, H = 160, 42          # dots across (a whole screen row), rows (from VY0)
BASE = 30               # the ground line under the towers

# letters 8 dots x 16 rows, built from blocks (x0, y0, x1, y1)
LETTERS = {
    'D': [(0, 0, 6, 3), (0, 13, 6, 16), (0, 0, 2, 16), (6, 2, 8, 14)],
    'A': [(0, 2, 2, 16), (6, 2, 8, 16), (1, 0, 7, 3), (0, 7, 8, 10)],
    'R': [(0, 0, 2, 16), (0, 0, 7, 3), (6, 1, 8, 8), (0, 7, 7, 10), (5, 10, 7, 13), (6, 13, 8, 16)],
    'K': [(0, 0, 2, 16), (6, 0, 8, 3), (5, 3, 7, 6), (2, 6, 6, 10), (5, 10, 7, 13), (6, 13, 8, 16)],
    'C': [(0, 2, 2, 14), (1, 0, 8, 3), (1, 13, 8, 16)],
    'I': [(3, 0, 5, 16), (1, 0, 7, 3), (1, 13, 7, 16)],
    'T': [(0, 0, 8, 3), (3, 0, 5, 16)],
    'E': [(0, 0, 2, 16), (0, 0, 8, 3), (0, 7, 6, 10), (0, 13, 8, 16)],
    'L': [(0, 0, 2, 16), (0, 13, 8, 16)],
}
# towers: (x, width, height above the ground)
TOWERS = [(4, 14, 16), (18, 10, 24), (30, 20, 12), (52, 24, 28), (78, 16, 18), (96, 12, 22)]


def word(text, gap=1, space=5):
    w = sum(space if c == ' ' else 8 + gap for c in text) - gap
    m = [[0] * w for _ in range(16)]
    x = 0
    for c in text:
        if c == ' ':
            x += space
            continue
        for x0, y0, x1, y1 in LETTERS[c]:
            for y in range(y0, y1):
                for xx in range(x0, x1):
                    m[y][x + xx] = 1
        x += 8 + gap
    return m


def logo():
    """-> H rows of W colours"""
    scr = [[BLACK] * W for _ in range(H)]
    # the towers, battlements, a lit window in each
    for x, tw, th in TOWERS:
        for y in range(BASE - th, BASE):
            for xx in range(x, min(128, x + tw)):
                scr[y][xx] = PURPLE if (xx + y) % 2 else BLUE
        for xx in range(x, min(128, x + tw), 4):
            for y in range(BASE - th - 2, BASE - th):
                for k in range(2):
                    if xx + k < min(128, x + tw):
                        scr[y][xx + k] = PURPLE
        wx, wy = x + tw // 2 - 1, BASE - th + 4
        scr[wy][wx] = scr[wy + 1][wx] = ORANGE
    for y in range(BASE, BASE + 2):            # the ground
        for x in range(128):
            scr[y][x] = BLUE
    # the crescent moon
    mx, my = 120, 6
    for dy in range(-4, 5):
        for dx in range(-3, 4):
            if (dx * 1.3) ** 2 + dy ** 2 <= 16 and not ((dx - 1) * 1.3) ** 2 + (dy - 1) ** 2 <= 9:
                scr[my + dy][mx + dx] = YELLOW
    # the name: a dark rim, lit from the top left
    m = word('DARK CITADEL')
    mh, mw = len(m), len(m[0])
    x0, y0 = (128 - mw) // 2, BASE - 6

    def on(x, y):
        return 0 <= y < mh and 0 <= x < mw and m[y][x]
    for y in range(-1, mh + 1):
        for x in range(-1, mw + 1):
            if not on(x, y) and any(on(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)):
                scr[y0 + y][x0 + x] = BLACK
    for y in range(mh):
        for x in range(mw):
            if on(x, y):
                if not on(x, y - 1) or not on(x - 1, y):
                    c = WHITE
                elif not on(x, y + 1):
                    c = BLUE
                else:
                    c = CYAN if y < 9 else SKY
                scr[y0 + y][x0 + x] = c
    return scr


def planes(scr):
    """-> (plane 0, plane 1) bytes, 40 a row (4 dots a byte, 2 bits each)"""
    p0, p1 = bytearray(), bytearray()
    for row in scr:
        for b in range(W // 4):
            a = c = 0
            for k in range(4):
                v = row[b * 4 + k]
                a |= (v & 3) << (6 - 2 * k)
                c |= (v >> 2) << (6 - 2 * k)
            p0.append(a)
            p1.append(c)
    return bytes(p0), bytes(p1)


if __name__ == '__main__':
    import os
    from PIL import Image
    RGB = [0x141414, 0x8000FF, 0xFFAC00, 0xFF00AC, 0x00FFAC, 0x00ACFF, 0xACFF00, 0xACACAC,
           0x141414, 0x0000FF, 0xFF0000, 0xFF00FF, 0x00FF00, 0x00FFFF, 0xFFFF00, 0xFFFFFF]
    scr = logo()
    im = Image.new('RGB', (W, H))
    for y in range(H):
        for x in range(W):
            c = RGB[scr[y][x]]
            im.putpixel((x, y), (c >> 16, (c >> 8) & 255, c & 255))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'logo.png')
    im.resize((W * 4, H * 2), Image.NEAREST).save(out)
    print('saved', out)

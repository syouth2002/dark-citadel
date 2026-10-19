"""Build-time floor generator for DARK CITADEL (original layouts).

Splits the 24x24 floor into rooms (BSP), joins every split with one door
(so the rooms form a tree), puts the exit in the room farthest from the
start, locks one or two doors on the way with the keys placed before them,
then spreads enemies and pickups.  The result is written as map rows in the
same symbols as the hand-made floors and validated by fps_gen.check_level.
"""
import random

WALLS = '123'
N = 24                       # floor size (cells)
ROOM_MIN = 3                 # smallest room side (cells)
ROOMS = (7, 18)              # rooms per floor (fewest, most)
FLOORS = 13                  # the warden waits on the last
NOBJ = 40                    # objects a floor may hold with its extra enemies
KIND_T = {'h': 1, 'e': 2, 'b': 3, 's': 4}
EXTRAS = {}                  # floor -> extra enemies [(type, x, y)] (make)
_last_extras = []


def _flood(g, x, y, seen):
    stack, cells = [(x, y)], []
    seen.add((x, y))
    while stack:
        cx, cy = stack.pop()
        cells.append((cx, cy))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if (nx, ny) not in seen and g[ny][nx] == '.':
                seen.add((nx, ny))
                stack.append((nx, ny))
    return cells


def generate(seed, floor):
    rnd = random.Random(seed)
    g = [['1'] * N for _ in range(N)]
    for y in range(1, N - 1):
        for x in range(1, N - 1):
            g[y][x] = '.'
    doors = []
    keep = rnd.uniform(0.15, 0.6)           # chance to leave an area whole

    def split(x0, y0, x1, y1, depth):
        w, h = x1 - x0 + 1, y1 - y0 + 1
        # rooms at least ROOM_MIN cells wide; mid-sized areas are left whole
        # now and then (how often differs per floor), so small rooms and
        # large halls mix
        can_v, can_h = w >= ROOM_MIN * 2 + 1, h >= ROOM_MIN * 2 + 1
        if depth >= 5 or not (can_v or can_h) or (w * h <= 80 and rnd.random() < keep):
            return
        vertical = can_v and (not can_h or w > h or (w == h and rnd.random() < 0.5))
        ch = rnd.choice(WALLS)
        if vertical:
            x = rnd.randint(x0 + ROOM_MIN, x1 - ROOM_MIN)
            for y in range(y0, y1 + 1):
                g[y][x] = ch
            split(x0, y0, x - 1, y1, depth + 1)
            split(x + 1, y0, x1, y1, depth + 1)
            cand = [(x, y) for y in range(y0, y1 + 1) if g[y][x - 1] == '.' and g[y][x + 1] == '.']
        else:
            y = rnd.randint(y0 + ROOM_MIN, y1 - ROOM_MIN)
            for x in range(x0, x1 + 1):
                g[y][x] = ch
            split(x0, y0, x1, y - 1, depth + 1)
            split(x0, y + 1, x1, y1, depth + 1)
            cand = [(x, y) for x in range(x0, x1 + 1) if g[y - 1][x] == '.' and g[y + 1][x] == '.']
        if not cand:
            raise ValueError('no door place')
        dx, dy = rnd.choice(cand)
        g[dy][dx] = 'D'
        doors.append((dx, dy))

    split(1, 1, N - 2, N - 2, 0)
    # rooms = floor regions separated by walls and doors
    seen, rooms, room_of = set(), [], {}
    for y in range(1, N - 1):
        for x in range(1, N - 1):
            if g[y][x] == '.' and (x, y) not in seen:
                cells = _flood(g, x, y, seen)
                for c in cells:
                    room_of[c] = len(rooms)
                rooms.append(cells)
    if not ROOMS[0] <= len(rooms) <= ROOMS[1]:
        raise ValueError('room count')
    # door graph (a tree)
    adj = {i: [] for i in range(len(rooms))}
    door_rooms = {}
    for d in doors:
        x, y = d
        ns = [room_of[(x + dx, y + dy)] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if (x + dx, y + dy) in room_of]
        a, b = ns[0], ns[1]
        door_rooms[d] = (a, b)
        adj[a].append((b, d))
        adj[b].append((a, d))

    def bfs(src):
        dist, prev = {src: 0}, {src: None}
        todo = [src]
        while todo:
            r = todo.pop(0)
            for n, d in adj[r]:
                if n not in dist:
                    dist[n] = dist[r] + 1
                    prev[n] = (r, d)
                    todo.append(n)
        return dist, prev

    start = rnd.randrange(len(rooms))
    dist, prev = bfs(start)
    exit_room = max(dist, key=lambda r: (dist[r], len(rooms[r])))
    path = []                               # doors on the way, start -> exit
    r = exit_room
    while prev[r]:
        r, d = prev[r]
        path.append(d)
    path.reverse()
    if len(path) < 3:
        raise ValueError('path too short')
    # exit panel: a wall cell next to the exit room (prefer the outer wall)
    cand = []
    for (x, y) in rooms[exit_room]:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if g[ny][nx] in WALLS:
                outer = nx in (0, N - 1) or ny in (0, N - 1)
                cand.append((0 if outer else 1, nx, ny))
    cand.sort()
    best = [c for c in cand if c[0] == cand[0][0]]
    _, ex, ey = rnd.choice(best)
    g[ey][ex] = 'X'
    # locks: one on floors 1-6, two from floor 7
    nlocks = 1 if floor < 7 else 2
    lock_idx = sorted(rnd.sample(range(1, len(path)), min(nlocks, len(path) - 1)))
    used = set()

    def side_rooms(blocked):
        """rooms reachable from start without crossing the blocked doors"""
        seen_r, todo = {start}, [start]
        while todo:
            rr = todo.pop()
            for n, d in adj[rr]:
                if d not in blocked and n not in seen_r:
                    seen_r.add(n)
                    todo.append(n)
        return seen_r

    objs = []
    free = lambda rr: [c for c in rooms[rr] if c not in used and
                       all(g[c[1] + dy][c[0] + dx] != 'D' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for k, li in enumerate(lock_idx):
        d = path[li]
        g[d[1]][d[0]] = 'O' if k == 0 else 'V'
        blocked = {path[j] for j in lock_idx[k:]}
        reach = side_rooms(blocked)
        if k > 0:                            # prefer rooms opened by the previous key
            newer = reach - side_rooms({path[j] for j in lock_idx[k - 1:]})
            reach = newer or reach
        # the room farthest from the start among the reachable ones
        pick = sorted(reach, key=lambda rr: -dist[rr])
        for rr in pick:
            cells = free(rr)
            if cells:
                c = rnd.choice(cells)
                used.add(c)
                objs.append(('o' if k == 0 else 'v', c))
                break
        else:
            raise ValueError('no key place')
    # the warden: the last floor, in the exit room, as near its middle as possible
    if floor == FLOORS:
        cells = free(exit_room)
        mx = sum(c[0] for c in rooms[exit_room]) / len(rooms[exit_room])
        my = sum(c[1] for c in rooms[exit_room]) / len(rooms[exit_room])
        c = min(cells, key=lambda c: (c[0] - mx) ** 2 + (c[1] - my) ** 2)
        used.add(c)
        objs.append(('w', c))
    # player
    px, py = rnd.choice(rooms[start])
    used.add((px, py))
    # enemies and pickups (not in the start room)
    others = [c for rr in range(len(rooms)) if rr != start for c in free(rr)]
    rnd.shuffle(others)
    n_en = min(15, 4 + floor)
    n_eye = int(round(n_en * min(0.4, 0.2 + 0.02 * floor)))
    n_brute = 0 if floor < 4 else min(4, 1 + (floor - 4) // 2)     # from floor 4
    n_stalk = 0 if floor < 7 else min(4, 1 + (floor - 7) // 2)     # from floor 7
    n_hp = 3 if floor < 8 else 2
    n_am = 3
    n_husk = n_en - n_eye - n_brute - n_stalk
    assert n_husk >= 1
    want = (['e'] * n_eye + ['b'] * n_brute + ['s'] * n_stalk + ['h'] * n_husk +
            ['+'] * n_hp + ['a'] * n_am + ['l'] * (floor >= 3))     # lantern oil
    for kind in want:
        while others:
            c = others.pop()
            if c not in used and abs(c[0] - px) + abs(c[1] - py) >= 3:
                used.add(c)
                objs.append((kind, c))
                break
    # the extra enemies of the harder difficulties: as many again, of the same
    # kinds, on free cells out of the start room (NORMAL takes the first half,
    # HARD all of them)
    kinds = [k for k, c in objs if k in KIND_T]
    rnd.shuffle(kinds)
    extras = []
    for kind in kinds:
        while others:
            c = others.pop()
            if c not in used and abs(c[0] - px) + abs(c[1] - py) >= 3:
                used.add(c)
                extras.append((KIND_T[kind], c[0], c[1]))
                break
    if len(extras) < len(kinds):
        raise ValueError('no room for the extra enemies')
    assert len(objs) + len(extras) <= NOBJ
    global _last_extras
    _last_extras = extras
    for kind, (x, y) in objs:
        g[y][x] = kind
    g[py][px] = 'P'
    return [''.join(r) for r in g]


def all_levels():
    """the floors: (colour group, rows); fixed seeds, so every build is the same"""
    groups = [0, 2, 1, 3]                    # colour group cycle
    return [(groups[f % 4], make(f + 1, 1000 + f * 37)) for f in range(FLOORS)]


def make(floor, base_seed):
    """first valid layout for this floor"""
    import fps_gen
    for s in range(base_seed, base_seed + 500):
        try:
            rows = generate(s, floor)
        except ValueError:
            continue
        cells, objs, start = fps_gen.parse_level(rows)
        try:
            fps_gen.check_level(cells, objs, start)
        except AssertionError:
            continue
        EXTRAS[floor] = _last_extras
        return rows
    raise RuntimeError('no valid floor for %d' % floor)

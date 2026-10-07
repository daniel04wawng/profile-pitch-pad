"""The landing page: Daniel's café seen from outside, on a street corner.

The same isometric grid, palette and wood as the room inside: a corner café with two shop
fronts (big lamp-lit windows under a striped awning, a glass-panelled door), its name on the
fascia, a navy brick floor above, a stone sidewalk and a wet street wrapping the corner, a
street lamp and a chalkboard out front.

Writes public/cafe/landing/storefront.png, and storefront.glow.png: just the lit glass and the
lamp (the page brightens these at night and keeps them warm when the street goes dark).

    python3 art/landing/draw_storefront.py [--preview]
"""
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
sys.path.insert(0, ART)
from draw_cozy import P as COZY, Canvas, P2, face_left, face_right, face_top  # noqa: E402
from draw_room import WOOD  # noqa: E402

OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "landing")

P = COZY
for k, v in {
    "brick0": "#232842", "brick1": "#2f3656", "brick2": "#3c446a", "mortar": "#1b1f33", "trim0": "#c9b48e", "trim1": "#e6d3ab",
    "stone0": "#6f675e", "stone1": "#8f877c", "stone2": "#a39a8f", "stone3": "#b9b0a5", "curb": "#cfc7b9",
    "road0": "#24262f", "road1": "#2d2f3a", "road2": "#363946", "wet0": "#4a5270", "wet1": "#6c7698", "dash": "#cdbf8f",
    "rust1": "#7a2c1c", "rust2": "#a3412a", "rust3": "#c25a38", "awn0": "#e9d9b8", "awn1": "#f7ecd3",
    "iron": "#1d140f", "iron1": "#3a2c24", "lamp0": "#ffd98a", "lamp1": "#fff3cf",
    "slate0": "#1c1f1e", "slate1": "#2c302e", "chalk": "#e8e2d0",
    "pane0": "#141a2c", "pane1": "#1f2840",
    "lit0": "#c27a2c", "lit1": "#e09a3e", "lit2": "#f2bb5c", "lit3": "#ffd98a", "lit4": "#fff0c4",
    "leaf0": "#26361f", "navy0": "#0a192f", "navy1": "#22253e", "silver0": "#7d8080", "silver1": "#b4b6b0", "silver2": "#dcdcd4",
}.items():
    P[k] = tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,)
for i, v in enumerate(WOOD):
    P[f"wood{i}"] = tuple(int(v[j : j + 2], 16) for j in (1, 3, 5)) + (255,)

# the building's footprint (units; 8 to a tile), and the ground around its two front sides
A, B = 64, 48
S, R = 14, 26  # sidewalk and street widths
GF, CORN, UF = 62, 6, 54  # ground floor, cornice and upper floor heights (px)
TOP = GF + CORN + UF
SLAB = 9  # the diorama's base, like the room's

W, H = 420, 352
X0, Y0 = 2 * (B + S + R) + 14, TOP + 16  # where the building's back corner meets the ground

random.seed(7)
glow = Canvas(W, H)  # the lit glass and lamp, for the night


def lit(c, x, y, col):
    c.px(x, y, col)
    glow.px(x, y, col)


# ---------------------------------------------------------------- lettering

FONT = {
    "D": ["110", "101", "101", "101", "110"], "A": ["010", "101", "111", "101", "101"],
    "N": ["101", "111", "111", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "E": ["111", "100", "110", "100", "111"], "L": ["100", "100", "100", "100", "111"],
    "'": ["1", "1", "0", "0", "0"], "S": ["011", "100", "010", "001", "110"],
    "C": ["011", "100", "100", "100", "011"], "F": ["111", "100", "110", "100", "100"], " ": ["00", "00", "00", "00", "00"],
}


def text_cells(s, accent=None):
    """The set of (t, row) cells a word fills: t in units along the wall, row 0 = top."""
    cells, t = set(), 0
    for i, ch in enumerate(s):
        g = FONT[ch]
        for r, line in enumerate(g):
            for k, bit in enumerate(line):
                if bit == "1":
                    cells.add((t + k, r))
        if accent == i:  # an acute accent over this letter (the É)
            cells.add((t + len(g[0]) - 1, -2))
        t += len(g[0]) + 1
    return cells, t - 1


SIGN, SIGN_W = text_cells("DANIEL'S CAFE", accent=12)


# ---------------------------------------------------------------- the ground


def ground(c):
    def col(a, b):
        A2, B2 = a, b  # absolute (the face starts at 0, 0)
        on_walk = A2 < A + S and B2 < B + S
        if on_walk:
            curb = A2 >= A + S - 1.5 or B2 >= B + S - 1.5
            if curb:
                return "curb" if (A2 + B2) % 6 > 0.8 else "stone2"
            # square slabs, a tile each, with darker seams and a little wear
            if A2 % 8 < 0.75 or B2 % 8 < 0.75:
                return "stone0"
            n = (int(A2 // 8) * 7 + int(B2 // 8) * 13) % 5
            if random.random() < 0.06:
                return "stone1"
            return ("stone2", "stone3", "stone2", "stone1", "stone2")[n]
        # the street: dark asphalt, a dashed line down each side street, wet patches
        mid_b = B + S + R / 2
        mid_a = A + S + R / 2
        if A2 < A + S and abs(B2 - mid_b) < 0.8 and int(A2 // 6) % 2 == 0:
            return "dash"
        if B2 < B + S and abs(A2 - mid_a) < 0.8 and int(B2 // 6) % 2 == 0:
            return "dash"
        wet = ((A2 * 0.7 + B2 * 1.3) % 23 < 2.2) and random.random() < 0.7
        if wet:
            return "wet0"
        return ("road1", "road0", "road1", "road2")[random.randrange(4)] if random.random() < 0.35 else "road1"

    face_top(c, X0, Y0, 0, A + S + R, 0, B + S + R, 0, col)
    # the slab the scene stands on (its two front edges)
    face_left(c, X0, Y0, 0, A + S + R, B + S + R, -SLAB, 0, lambda t, z: "navy1" if z > -SLAB + 2 else "navy0")
    face_right(c, X0, Y0, A + S + R, 0, B + S + R, -SLAB, 0, lambda s, z: "navy0" if z > -SLAB + 2 else "line")


# ---------------------------------------------------------------- the building


def window_glass(t, z, w, h, c_x=None):
    """A lamp-lit shop window seen from outside, (t, z) inside a w x h pane: warm light,
    brightest up top where the pendant lamps hang, a soft reflection streak."""
    u, v = t / w, z / h
    if 0.48 < u < 0.52 or 0.66 < v < 0.7:  # mullion and transom bar
        return "wood1"
    # one soft diagonal reflection across the pane
    if abs(u * w - (1 - v) * h * 0.8 - w * 0.25) < 1.2:
        return "lit4"
    # brightest under the lamps up top, a little warmer and darker toward the sill
    level = 0.25 + 0.7 * v + (0.06 if (int(t) + int(z)) % 3 == 0 else 0)
    for lim, k in ((0.86, "lit4"), (0.66, "lit3"), (0.46, "lit2"), (0.3, "lit1")):
        if level > lim:
            return k
    return "lit0"


def brick(t, z, lightness):
    """Navy brick, 4px courses, bricks 6 units long, every other course offset."""
    row = int(z // 4)
    off = 3 if row % 2 else 0
    if z % 4 < 1 or (t + off) % 6 < 0.7:
        return "mortar"
    n = (int((t + off) // 6) * 5 + row * 3) % 4
    return ("brick1", "brick2", "brick1", "brick0")[(n + lightness) % 4]


def facade_left(c):
    """The face looking down-left (b = B): two big windows under an awning, the name above."""
    windows = [(3, 30), (34, 61)]

    def col(t, z):
        if z < 5:
            return "wood1" if z < 4 else "wood3"  # plinth and its lip
        if z >= GF - 13:  # fascia, with the name in brass
            if z >= GF - 2:
                return "wood3"
            row = int(GF - 3 - z) - 2  # rows counted down from the fascia's top
            x0 = (A - SIGN_W) / 2
            if (int(t - x0), row) in SIGN and t >= x0:
                return "gold2" if row < 3 else "gold1"
            return "wood1"
        for w0, w1 in windows:
            if w0 <= t < w1 and 8 <= z < GF - 15:
                return None  # glass, drawn below
            if w0 <= t < w1 and (z < 8 or z >= GF - 15):
                return "wood2" if z >= 6 else "wood3"  # sill and head
        # pilasters
        if (t % 34) < 1:
            return "wood4"
        return "wood2" if (t % 34) < 3 else "wood3"

    face_left(c, X0, Y0, 0, A, B, 0, GF, col)
    for w0, w1 in windows:
        def g(t, z, w0=w0, w1=w1):
            return window_glass(t, z, w1 - w0, GF - 23)
        face_left(glow, X0, Y0, w0, w1, B, 8, GF - 15, g)
        face_left(c, X0, Y0, w0, w1, B, 8, GF - 15, g)
    # cornice, then brick with two windows (one lit), then the top trim
    face_left(c, X0, Y0, 0, A, B, GF, GF + CORN, lambda t, z: "trim1" if z > 3 else ("trim0" if z > 1 else "wood1"))
    up = [(8, 20), (30, 42), (50, 60)]

    def upper(t, z):
        for i, (w0, w1) in enumerate(up):
            if w0 <= t < w1 and 12 <= z < UF - 10:
                if z < 14:
                    return "trim0"  # sill
                if i == 1:
                    return "lit2" if (t - w0) % 6 > 0.8 and z < UF - 12 else "wood1"
                return "pane1" if (t - w0 + z) % 9 < 2 else "pane0"
        return brick(t, z, 1)

    face_left(c, X0, Y0, 0, A, B, GF + CORN, TOP, upper)
    face_left(c, X0, Y0, 0, A, B, TOP - 3, TOP, lambda t, z: "trim1" if z > 1 else "trim0")


def facade_right(c):
    """The face looking down-right (a = A), in the shade: a window, the door, a window."""
    win = [(4, 15), (35, 45)]
    door = DOOR

    def col(s, z):
        if z < 5:
            return "wood0" if z < 4 else "wood2"
        if z >= GF - 13:
            return "wood2" if z >= GF - 2 else "wood0"
        if door[0] <= s < door[1] and z < GF - 15:
            return None
        for w0, w1 in win:
            if w0 <= s < w1 and 8 <= z < GF - 15:
                return None
            if w0 <= s < w1:
                return "wood1"
        if (s % 17) < 1:
            return "wood3"
        return "wood1" if (s % 17) < 3 else "wood2"

    face_right(c, X0, Y0, A, 0, B, 0, GF, col)
    for w0, w1 in win:
        def g(s, z, w0=w0, w1=w1):
            k = window_glass(s, z, w1 - w0, GF - 23)
            # the shaded side: a step dimmer
            return {"lit4": "lit3", "lit3": "lit2", "lit2": "lit1", "lit1": "lit0"}.get(k, k)
        face_right(glow, X0, Y0, A, w0, w1, 8, GF - 15, g)
        face_right(c, X0, Y0, A, w0, w1, 8, GF - 15, g)

    # the door: a wood frame, a glass upper half (lit), panels below, a brass handle
    d0, d1 = door

    def dcol(s, z):
        if s < 1 or s >= (d1 - d0) - 1 or z >= GF - 16:
            return "wood0"
        if z > 22 and z < GF - 19 and 2 <= s < (d1 - d0) - 2:
            return "lit2" if (s + z) % 11 > 1 else "lit3"
        if s < 2 or s >= (d1 - d0) - 2 or 20 <= z <= 22 or z < 3:
            return "wood1"
        return "wood2" if (z // 6) % 2 else "wood1"

    face_right(c, X0, Y0, A, d0, d1, 0, GF - 15, dcol)
    face_right(glow, X0, Y0, A, d0, d1, 0, GF - 15, lambda s, z: "lit2" if 22 < z < GF - 19 and 2 <= s < (d1 - d0) - 2 else None)
    hx, hy = P2(X0, Y0, A, d1 - 2.5, 24)
    c.px(hx, hy, "brass2")
    c.px(hx, hy + 1, "brass1")
    # step
    face_top(c, X0, Y0, A, A + 3, d0 - 1, d1 + 1, 2, lambda a, b: "stone3" if a < 2.4 else "stone1")
    face_right(c, X0, Y0, A + 3, d0 - 1, d1 + 1, 0, 2, lambda s, z: "stone0")
    face_left(c, X0, Y0, A, A + 3, d1 + 1, 0, 2, lambda t, z: "stone1")

    face_right(c, X0, Y0, A, 0, B, GF, GF + CORN, lambda s, z: "trim0" if z > 3 else ("cream0" if z > 1 else "wood0"))
    up = [(6, 17), (28, 39)]

    def upper(s, z):
        for w0, w1 in up:
            if w0 <= s < w1 and 12 <= z < UF - 10:
                return "trim0" if z < 14 else ("pane1" if (s - w0 + z) % 9 < 2 else "pane0")
        return brick(s, z, 0)

    face_right(c, X0, Y0, A, 0, B, GF + CORN, TOP, upper)
    face_right(c, X0, Y0, A, 0, B, TOP - 3, TOP, lambda s, z: "trim0" if z > 1 else "cream0")
    roof(c)


def roof(c):
    """A flat gravel roof behind a low parapet, with a skylight and a vent."""
    def gravel(a, b):
        if a < 2 or b < 2 or a > A - 2 or b > B - 2:
            return "trim1" if (a < 1 or b < 1 or a > A - 1 or b > B - 1) else "trim0"  # parapet cap
        r = random.random()
        return "stone0" if r < 0.25 else ("stone1" if r < 0.85 else "stone2")

    face_top(c, X0, Y0, 0, A, 0, B, TOP, gravel)
    # the parapet's inner faces, along the two far edges
    face_left(c, X0, Y0, 2, A - 2, 2, TOP - 3, TOP, lambda t, z: "brick1")
    face_right(c, X0, Y0, 2, 2, B - 2, TOP - 3, TOP, lambda s, z: "brick0")
    # a skylight glowing from the café below, and a little vent
    sa, sb = 14, 12
    face_left(c, X0, Y0, sa, sa + 14, sb + 10, TOP, TOP + 4, lambda t, z: "wood2")
    face_right(c, X0, Y0, sa + 14, sb, sb + 10, TOP, TOP + 4, lambda s, z: "wood1")
    face_top(glow, X0, Y0, sa + 1, sa + 13, sb + 1, sb + 9, TOP + 4, lambda a, b: "lit3" if (a + b) % 5 > 0.7 else "wood1")
    face_top(c, X0, Y0, sa, sa + 14, sb, sb + 10, TOP + 4, lambda a, b: ("wood3" if a < 1 or b < 1 or a > 13 or b > 9 else ("lit3" if (a + b) % 5 > 0.7 else "wood1")))
    va, vb = 44, 30
    face_left(c, X0, Y0, va, va + 5, vb + 5, TOP, TOP + 9, lambda t, z: "silver1" if z < 8 else "silver2")
    face_right(c, X0, Y0, va + 5, vb, vb + 5, TOP, TOP + 9, lambda s, z: "silver0")
    face_top(c, X0, Y0, va, va + 5, vb, vb + 5, TOP + 9, lambda a, b: "silver2")


def awning(c):
    """Striped canvas over the left windows: from the wall at GF-11 out 10 units, dropping
    as it goes, with a scalloped valance."""
    DEP, Z0, DROP = 9, GF - 14, 8
    steps = 6
    for ai in range(0, A * steps):
        a = ai / steps
        if a < 2 or a > A - 2:
            continue
        stripe = int((a - 2) // 4) % 2
        for di in range(0, DEP * steps):
            d = di / steps
            z = Z0 - DROP * d / DEP
            x, y = P2(X0, Y0, a, B + d, z)
            shade = "rust2" if stripe else "awn0"
            if d < 1.2:
                shade = "rust1" if stripe else "trim0"  # where it meets the wall
            elif d > DEP - 2:
                shade = "rust3" if stripe else "awn1"  # the lit front edge
            c.px(x, y, shade)
        # the valance: a short hanging strip with a scalloped hem
        hem = 3 + (1 if int(a * 1.0) % 4 in (1, 2) else 0)
        for zz in range(hem):
            x, y = P2(X0, Y0, a, B + DEP, Z0 - DROP - zz)
            c.px(x, y, ("rust2" if stripe else "awn0") if zz < hem - 1 else ("rust1" if stripe else "trim0"))


# ---------------------------------------------------------------- out front


def planter(c, a, b):
    """A wooden planter box with a bushy green plant."""
    face_left(c, X0, Y0, a, a + 5, b + 5, 0, 7, lambda t, z: "wood3" if z > 5 else "wood2")
    face_right(c, X0, Y0, a + 5, b, b + 5, 0, 7, lambda s, z: "wood2" if z > 5 else "wood1")
    face_top(c, X0, Y0, a, a + 5, b, b + 5, 7, lambda u, v: "choc0")
    cx, cy = P2(X0, Y0, a + 2.5, b + 2.5, 7)
    for _ in range(140):
        dx, dy = random.gauss(0, 4.2), random.gauss(-6, 4)
        if dy > 1:
            continue
        k = "sage2" if dy < -8 and dx < 1 else ("sage1" if dy < -3 else "sage0")
        c.px(cx + dx, cy + dy, k)


def chalkboard(c, a, b):
    """An A-frame sign on the sidewalk, facing down-left."""
    for side, z0 in ((0, 0),):
        face_left(c, X0, Y0, a, a + 7, b, 0, 20, lambda t, z: "wood2" if t < 0.8 or t > 6.2 or z > 18.5 or z < 1.5 else ("slate1" if (t + z) % 7 > 0.6 else "slate0"))
    # a few chalk scribbles: a cup and a line of "writing"
    for t, z in ((2, 14), (3, 14), (4, 14), (2, 13), (4, 13), (2.5, 12), (3.5, 12), (5, 13.5)):
        x, y = P2(X0, Y0, a + t, b, z)
        c.px(x, y, "chalk")
    for t in range(2, 6):
        x, y = P2(X0, Y0, a + t, b, 8)
        if t % 2:
            c.px(x, y, "chalk")
        x, y = P2(X0, Y0, a + t, b, 5)
        c.px(x, y, "chalk")
    lx, ly = P2(X0, Y0, a + 3.5, b + 3, 0)
    for z in range(0, 18):  # back leg
        c.px(lx + 4, ly - z * 0.9, "wood1")


def street_lamp(c, a, b):
    """An iron street lamp with a lit lantern."""
    bx, by = P2(X0, Y0, a, b, 0)
    for dx in range(-2, 3):
        c.px(bx + dx, by, "iron")
        c.px(bx + dx, by - 1, "iron1" if dx < 1 else "iron")
    for z in range(2, 70):
        c.px(bx - 1, by - z, "iron1")
        c.px(bx, by - z, "iron1" if z % 9 else "iron")
        c.px(bx + 1, by - z, "iron")
    # the lantern
    top = by - 70
    for y in range(top - 13, top):
        for x in range(bx - 4, bx + 6):
            edge = x in (bx - 4, bx + 5) or y in (top - 13, top - 1) or (x == bx + 0.5)
            if edge:
                c.px(x, y, "iron")
            else:
                lit(c, x, y, "lamp1" if (x - bx + y - top) % 5 else "lamp0")
    for x in range(bx - 3, bx + 5):
        c.px(x, top - 14, "iron")
    for x in range(bx - 1, bx + 3):
        c.px(x, top - 15, "iron")


DOOR = (19, 30)  # along the shaded front (b), hinges at the first end, handle at the second


def door_frames():
    """The door swinging in, three steps: each a full-size overlay (the doorway lit from inside,
    the leaf turned on its hinges into the café), stacked over the picture by the page."""
    import math

    d0, d1 = DOOR
    L = d1 - d0  # the leaf's width
    top = GF - 15
    frames = []
    for angle in (35, 70, 100):
        c = Canvas(W, H)
        # the doorway: warm light from inside, brightest up high, a sliver of floor
        def room(s, z):
            if s < 1 or s >= L - 1 or z >= top - 1:
                return "wood0"  # the frame stays put
            if z < 3:
                return "wood3" if (s + z) % 4 else "wood4"  # the café floor just inside
            v = z / top
            return "lit4" if v > 0.75 else ("lit3" if v > 0.45 else "lit2")

        face_right(c, X0, Y0, A, d0, d1, 0, top, room)
        # the opening itself (inside the frame): an inward-swinging leaf is only seen through it
        hole = Canvas(W, H)
        face_right(hole, X0, Y0, A, d0, d1, 0, top, lambda s, z: None if (s < 1 or s >= L - 1 or z >= top - 1) else "line")
        ha = hole.im.getchannel("A").load()
        leaf = Canvas(W, H)
        # the leaf, from the hinges (b = d0 + 1) swung in by `angle`
        t = math.radians(angle)
        hb = d0 + 1
        ea, eb = A - (L - 2) * math.sin(t), hb + (L - 2) * math.cos(t)
        for z in range(1, top - 1):
            p0 = P2(X0, Y0, A, hb, z)
            p1 = P2(X0, Y0, ea, eb, z)
            n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1])) * 2) + 1
            for i in range(n + 1):
                f = i / n
                x, y = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
                glass = 22 < z < top - 4 and 0.18 < f < 0.85
                edge = f > 0.93 or z < 3 or z > top - 3
                leaf.px(x, y, "wood1" if edge else ("lit3" if glass and angle < 90 else ("wood3" if f < 0.5 else "wood2")))
        la = leaf.im.load()
        for y in range(H):
            for x in range(W):
                if la[x, y][3] and ha[x, y]:
                    c.im.putpixel((x, y), la[x, y])
        frames.append(c.im)
    return frames


def main():
    os.makedirs(OUT, exist_ok=True)
    c = Canvas(W, H)
    ground(c)
    facade_right(c)
    facade_left(c)
    awning(c)
    planter(c, A + 1, 13)
    planter(c, A + 1, 32)
    chalkboard(c, 40, B + 6)
    street_lamp(c, A + S - 4, B + S - 4)
    c.outline()
    # keep only the glow that's still visible in the finished picture (the awning, the lamp
    # post and the planters cover some of the glass)
    gp, cp = glow.im.load(), c.im.load()
    for y in range(H):
        for x in range(W):
            if gp[x, y][3] and gp[x, y] != cp[x, y]:
                gp[x, y] = (0, 0, 0, 0)
    c.im.save(os.path.join(OUT, "storefront.png"))
    glow.im.save(os.path.join(OUT, "storefront.glow.png"))
    for i, im in enumerate(door_frames(), 1):
        im.save(os.path.join(OUT, f"door-{i}.png"))
    # where the door is (its middle), so "step inside" can zoom right into it
    import json
    dx, dy = P2(X0, Y0, A, 24.5, 22)
    # the way in, for your avatar: in along the sidewalk from the far end of the side street,
    # past the planter, then a turn up the step and through the door
    walk = [P2(X0, Y0, A + 9, 1, 0), P2(X0, Y0, A + 9, 24.5, 0), P2(X0, Y0, A + 1.5, 24.5, 2)]
    json.dump(
        {"w": W, "h": H, "door": {"x": round(dx), "y": round(dy)}, "doorFrames": 3, "walk": [{"x": round(x, 1), "y": round(y, 1)} for x, y in walk]},
        open(os.path.join(OUT, "storefront.json"), "w"),
    )
    print("storefront", c.im.size)
    if "--preview" in sys.argv:
        bg = Image.new("RGBA", c.im.size, (40, 46, 78, 255))
        bg.alpha_composite(c.im)
        bg.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(HERE, "preview-storefront.png"))


if __name__ == "__main__":
    main()

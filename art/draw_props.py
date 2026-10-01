"""Café props drawn clean in the original café's palette, at the room's scale.

Pieces that don't cut well from the original (they overlap other things there, or turn to
mush at native size) are drawn here instead: simple café tables and chairs, the piano and
its stool, woven tablecloths and a globe pendant lamp.

    python3 art/draw_props.py [--preview]   # writes public/cafe/sprites/<name>.png
"""
import os
import sys

from PIL import Image

from draw_cozy import P as COZY, Canvas, face_left, face_right, face_top
from draw_room import WOOD

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")

# extra tones from the original: the red rug, navy trim, warm whites
P = COZY
for k, v in {
    "red0": "#4a1012", "red1": "#7a1f1f", "red2": "#a8352a", "red3": "#c95a3a",
    "navy0": "#1b2040", "navy1": "#2c3463", "navy2": "#46508a",
    "iron": "#24170f",
    "olive0": "#2a3319", "olive1": "#45522a", "olive2": "#647538", "olive3": "#8a9a4e",
    "lea0": "#5e2e12", "lea1": "#8a4a20", "lea2": "#b8682e", "lea3": "#d88a45", "lea4": "#efae6a",
    "slate0": "#1c1f1e", "slate1": "#2c302e", "chalk": "#e8e2d0", "silver0": "#7d8080", "silver1": "#b4b6b0", "silver2": "#dcdcd4",
    "leaf0": "#26361f", "leaf3": "#b5c46a", "terra0": "#6e2f1c", "terra1": "#9c4a2a", "terra2": "#c4643a", "terra3": "#e08a5a",
    # the original piano's mahogany, sampled from it: near-black body, lamp-lit glossy lid
    "mah0": "#1b0801", "mah1": "#33140a", "mah2": "#4a2212", "mah3": "#6e3414", "mah4": "#903f02", "mah5": "#c7875d", "key0": "#c9b28c", "key1": "#f3e6c8", "key2": "#fff8e6",
}.items():
    P[k] = tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,)
# one wood for everything (the piano too), from the room's ramp
for i, v in enumerate(WOOD):
    P[f"wood{i}"] = P[f"mah{i}"] = tuple(int(v[j : j + 2], 16) for j in (1, 3, 5)) + (255,)


EXTRA = {}  # name -> companion info (sky mask, sun patch) for _companions.json


def save(c, name, anchor=None, sky=None, light=None, foot=None):
    """Outline, crop and write a sprite. `anchor` (x, y) is where a wall item meets the floor:
    an almost invisible pixel goes there so the editor sets it on the wall line. `sky` is a
    Canvas masking window glass; `light` a Canvas with the sun patch it throws on the floor."""
    c.outline()
    if anchor:
        c.im.putpixel((int(anchor[0]), int(anchor[1])), (0, 0, 0, 1))
    bbox = c.im.getbbox()
    im = c.im.crop(bbox)
    im.save(os.path.join(OUT, f"{name}.png"))
    info = {}
    if foot is not None:  # the point that stands on the grid, for the editor's snapping
        info["foot"] = {"x": round(foot[0]) - bbox[0], "y": round(foot[1]) - bbox[1]}
    elif anchor is not None:
        info["foot"] = {"x": round(anchor[0]) - bbox[0], "y": round(anchor[1]) - bbox[1]}
    if sky is not None:
        sky.im.crop(bbox).save(os.path.join(OUT, f"{name}.sky.png"))
        info["sky"] = f"sprites/{name}.sky.png"
    if light is not None:
        lb = light.im.getbbox()
        light.im.crop(lb).save(os.path.join(OUT, f"{name}.light.png"))
        info["light"] = {"file": f"sprites/{name}.light.png", "dx": lb[0] - bbox[0], "dy": lb[1] - bbox[1], "w": lb[2] - lb[0], "h": lb[3] - lb[1]}
    EXTRA[name] = info
    return im


def disc(c, cx, cy, rx, ry, color_fn):
    """Filled ellipse; color_fn(dx, dy) gets the offset from the centre, normalised to -1..1."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1:
                col = color_fn(dx, dy)
                if col:
                    c.px(x, y, col)


def darker(c, remap):
    src = {P[k]: P[v] for k, v in remap.items()}
    px = c.im.load()
    for y in range(c.h):
        for x in range(c.w):
            if px[x, y] in src:
                px[x, y] = src[px[x, y]]


def vline(c, x, y0, y1, col):
    for y in range(int(y0), int(y1) + 1):
        c.px(x, y, col)


# ---------------------------------------------------------------- tables and chairs


def cafe_table():
    """Small round café table: wood top, dark pedestal, iron foot."""
    c = Canvas(60, 60)
    cx, floor_y, top = 30, 50, 20
    disc(c, cx, floor_y - 1, 7, 3, lambda dx, dy: "iron")  # foot
    for x in (cx - 1, cx):
        vline(c, x, floor_y - top, floor_y - 1, "wood1" if x == cx - 1 else "wood0")  # pedestal
    ty = floor_y - top
    disc(c, cx, ty + 1.5, 13, 6.5, lambda dx, dy: "wood1")  # thickness of the top
    disc(c, cx, ty, 13, 6.5, lambda dx, dy: "wood5" if (dx + dy < -1.0) else ("wood4" if dx + dy < 0.6 else "wood3"))
    c.px(cx - 6, ty - 2, "gold3")  # a glint of lamplight
    c.px(cx - 5, ty - 2, "gold2")
    return save(c, "cafe-table", foot=(cx, floor_y))


def cafe_chair():
    """Bentwood café chair, facing down-right (flip it in the editor for the other way)."""
    c = Canvas(50, 60)
    cx, floor_y, seat = 25, 50, 12
    sy = floor_y - seat
    # legs, splayed a little; back legs first
    for (x0, x1, col) in ((cx - 3, cx - 4, "wood0"), (cx + 4, cx + 5, "wood0"), (cx - 5, cx - 6, "wood1"), (cx + 2, cx + 3, "wood1")):
        for y in range(sy + 1, floor_y + 1):
            t = (y - sy) / seat
            c.px(round(x0 + (x1 - x0) * t), y + (2 if col == "wood1" else 0) - (0 if col == "wood1" else 2), col)
    # leg ring
    for x in range(cx - 5, cx + 5):
        c.px(x, floor_y - 4 + (1 if x > cx else 0), "wood1")
    # back: two posts from the back of the seat, a hooped top rail, one cross rail
    bx0, bx1 = cx - 6, cx + 1
    for x, col in ((bx0, "wood2"), (bx1, "wood1")):
        vline(c, x, sy - 14 + (x - bx0) // 3, sy - 1, col)
    for x in range(bx0, bx1 + 1):
        y = sy - 15 + (x - bx0) // 3 - (1 if bx0 < x < bx1 else 0)
        c.px(x, y, "wood3")
        c.px(x, y + 1, "wood2")
        c.px(x, sy - 7 + (x - bx0) // 3, "wood2")
    # round seat
    disc(c, cx, sy + 1, 7, 3.5, lambda dx, dy: "wood1")
    disc(c, cx, sy, 7, 3.5, lambda dx, dy: "wood4" if dx + dy < -0.3 else "wood3")
    return save(c, "cafe-chair", foot=(cx, floor_y))


# ---------------------------------------------------------------- the piano corner


def piano():
    """Upright piano after the original's: near-black mahogany, glossy lamp-lit lid, framed
    panels, gold strip over the keys, turned front legs, brass pedals, a brass desk lamp and
    a black phone on top. Keyboard faces down-left."""
    c = Canvas(140, 160)
    X0, Y0 = 24, 76
    L, D = 20, 4  # length along the keyboard, depth (units: 2px across, 1px down)
    KB, TOP = 22, 64  # keyboard height and body height (px): tall, like the original
    KD = 4  # how far the keyboard sticks out
    m0, m1, m2, m3, m4, m5 = "mah0", "mah1", "mah2", "mah3", "mah4", "mah5"

    def framed(t, z, z0, z1, panels):
        """Recessed panels with a lit moulding on their top and left edges."""
        w = L / panels
        k = t % w
        if z <= z0 or z >= z1 - 1 or k < 0.35 or k > w - 0.35:
            return m3  # stiles and rails
        if k < 0.75 or z >= z1 - 2:
            return m4  # moulding catching the light
        if k > w - 0.75 or z <= z0 + 1:
            return m0  # shadowed moulding
        return m2  # panel face

    # right end of the case (in shadow), lower front, legs, keyboard, upper front, lid
    face_right(c, X0, Y0, L, 0, D + KD, 0, KB + 3, lambda s, z: m0 if s < D else m1)
    face_right(c, X0, Y0, L, 0, D, KB + 3, TOP, lambda s, z: m3 if z >= TOP - 1 else (m1 if s > D - 1 else m0))
    face_left(c, X0, Y0, 0, L, D, 1, KB, lambda t, z: m0 if z < 2 else framed(t, z, 2, KB, 1))
    for a0 in (0.2, L - 1.4):  # turned front legs under the keyboard cheeks
        face_left(c, X0, Y0, a0, a0 + 1.2, D + KD, 0, KB, lambda t, z: (m3 if t < 0.4 else m2) if (z % 5) not in (0, 1) else m1)
        face_right(c, X0, Y0, a0 + 1.2, D, D + KD, 0, KB, lambda s, z: m0)
    for a in (L / 2 - 1.2, L / 2, L / 2 + 1.2):  # brass pedals
        x, y = X0 + 2 * a - 2 * (D + 0.5), Y0 + a + D + 0.5 - 1
        c.px(x, y, "brass2"); c.px(x + 1, y, "brass1")
    face_left(c, X0, Y0, 0, L, D + KD, KB, KB + 3, lambda t, z: m2 if z < 2 else m3)  # key slip

    def keys(a, b):
        if b < 0.6:
            return m0  # shadow under the fallboard
        black = b < 1.9 and (int(a * 3.5) % 7) in (1, 2, 4, 5, 6) and (a * 3.5) % 1 < 0.6
        if black:
            return "iron"
        return "key2" if b > 2.6 else ("key1" if (a * 3.5) % 1 > 0.15 else "key0")
    face_top(c, X0, Y0, 0.2, L - 0.2, D, D + KD, KB + 3, keys)
    # keyboard cheeks: the blocks at each end of the keys
    for a0 in (0, L - 0.8):
        face_top(c, X0, Y0, a0, a0 + 0.8, D, D + KD, KB + 4, lambda a, b: m3)
        face_left(c, X0, Y0, a0, a0 + 0.8, D + KD, KB + 2, KB + 4, lambda t, z: m2)

    def upper(t, z):
        if z < 2:
            return m0  # fallboard shadow
        if z < 4:
            return ("gold2" if z == 3 else "gold0") if 1 < t < L - 1 else m3  # gold strip over the fallboard
        if L / 2 - 1.6 < t < L / 2 + 1.6 and 6 < z < 13:  # sheet music on the stand
            return "key1" if not (int(z) in (8, 10) and t % 1 < 0.5) else "key0"
        if L / 2 - 2.2 < t < L / 2 + 2.2 and int(z) == 5:
            return m4  # music-stand ledge
        return framed(t, z, 4, TOP - KB - KD, 2)
    face_left(c, X0, Y0, 0, L, D, KB + 3, TOP, upper)
    # glossy lid, lit by the lamp toward its middle
    def lid(a, b):
        d = abs(a - L * 0.6)  # the lamp lights the lid around it
        if b > D - 0.5:
            return m5 if d < 5 else m4  # front edge
        if b < 0.4 or a < 0 or a > L:
            return m3
        return m5 if (d < 2.5 and 1.5 < b < 3.5) else (m4 if d < 6 else m3)
    face_top(c, X0, Y0, -0.3, L + 0.3, -0.3, D + 0.3, TOP, lid)

    # brass banker's lamp: round foot, curved stem, long shade with warm light under it
    lx, ly = X0 + 2 * (L * 0.62) - 2 * (D * 0.5), Y0 + L * 0.62 + D * 0.5 - TOP
    for dx in range(-3, 4):
        c.px(lx + dx, ly, "brass1" if abs(dx) < 3 else "brass0")
        if abs(dx) < 2:
            c.px(lx + dx, ly - 1, "brass2")
    vline(c, lx, ly - 9, ly - 2, "brass1")
    c.px(lx - 1, ly - 6, "brass2")
    for dx in range(-7, 6):  # the shade runs along the piano, a little downhill
        y = ly - 12 + (dx + 7) // 3
        c.px(lx + dx, y - 1, "brass2" if dx < 3 else "brass1")
        c.px(lx + dx, y, "brass1")
        c.px(lx + dx, y + 1, "gold3" if -6 <= dx <= 4 else "brass0")
    c.px(lx - 7, ly - 13, "brass2")
    # black rotary phone toward the left end
    px_, py_ = X0 + 2 * 2.5 - 2 * (D * 0.4), Y0 + 2.5 + D * 0.4 - TOP
    for dx in range(-3, 4):
        c.px(px_ + dx, py_, "iron")
        c.px(px_ + dx, py_ - 1, "iron" if abs(dx) < 3 else None) if abs(dx) < 3 else None
    for dx in range(-3, 4):
        c.px(px_ + dx, py_ - 3 + (1 if abs(dx) == 3 else 0), "navy0")  # handset
    c.px(px_ - 1, py_ - 1, "key0")
    c.px(px_, py_ - 1, "navy1")
    return save(c, "piano", foot=(X0 + 2 * L - 2 * (D + KD), Y0 + L + D + KD))


def piano_stool():
    c = Canvas(40, 40)
    cx, floor_y, h = 20, 32, 10
    sy = floor_y - h
    for x0, x1, col in ((cx - 3, cx - 4, "wood1"), (cx + 3, cx + 4, "wood0"), (cx, cx, "wood0")):
        for y in range(sy + 2, floor_y + 1):
            t = (y - sy) / h
            c.px(round(x0 + (x1 - x0) * t), y, col)
    disc(c, cx, sy + 1.5, 6, 3, lambda dx, dy: "wood1")
    disc(c, cx, sy, 6, 3, lambda dx, dy: "mah5" if dx + dy < -0.8 else ("mah4" if dx + dy < 0.4 else "mah3"))  # brown leather top, like the original
    return save(c, "piano-stool", foot=(cx, floor_y))


# ---------------------------------------------------------------- walls and ceiling


def table_cloth(name, field, alt, trim, hem):
    """Round café table under a woven cloth that drapes over the edge, with a fringed hem."""
    def draw():
        c = Canvas(60, 60)
        cx, floor_y, top = 30, 50, 20
        rx, ry, drop = 14, 7, 7  # cloth a little wider than the table; how far it hangs
        disc(c, cx, floor_y - 1, 7, 3, lambda dx, dy: "iron")
        for x in (cx - 1, cx):
            vline(c, x, floor_y - top, floor_y - 1, "wood1" if x == cx - 1 else "wood0")
        ty = floor_y - top
        # the hanging skirt: below the front half of the top's rim
        for x in range(cx - rx, cx + rx + 1):
            dx = (x + 0.5 - cx) / rx
            if abs(dx) > 1:
                continue
            rim = ty + ry * (1 - dx * dx) ** 0.5
            for k in range(drop + 1):
                y = int(rim) + k
                if k >= drop - 1:
                    col = hem if (x % 2 == 0 or k == drop - 1) else None  # fringe
                elif k == drop - 2:
                    col = trim
                else:
                    shade = abs(dx) > 0.75 or (x % 4 == 0)  # folds
                    col = alt if shade else field
                if col:
                    c.px(x, y, col)
        # the top of the cloth, with a woven border and a diamond in the middle
        def top_col(dx, dy):
            r = dx * dx + dy * dy
            if r > 0.8:
                return trim
            if abs(dx) * 0.9 + abs(dy) < 0.32:
                return hem
            return alt if (r > 0.55 or (abs(dx) * 0.9 + abs(dy) < 0.5 and r > 0.12)) else field
        disc(c, cx, ty, rx, ry, top_col)
        return save(c, name, foot=(cx, floor_y))
    draw.__name__ = name.replace("-", "_")
    return draw


def globe_lamp():
    """Glass globe pendant on a long cord, from the original's ceiling lamps."""
    c = Canvas(30, 60)
    cx = 15
    vline(c, cx, 2, 30, "wood0")
    for x in range(cx - 2, cx + 3):
        c.px(x, 31, "brass1"); c.px(x, 32, "brass2" if x < cx else "brass1")
    disc(c, cx + 0.5, 39, 6, 6.5, lambda dx, dy: "shine" if (dx + 0.35) ** 2 + (dy + 0.35) ** 2 < 0.12 else ("gold3" if dx * dx + dy * dy < 0.45 else ("gold2" if dy < 0.6 else "gold1")))
    return save(c, "globe-lamp")


def wall_lamp():
    """Brass wall sconce: a plate on the wall, a curved arm, a glowing tulip glass shade.
    Hand-placed pixels (too small to draw any other way)."""
    art = [
        "......oggggo..",
        "......gGGwGg..",
        "......gGwwGg..",
        "......gGGGGg..",
        ".......gGGg...",
        "........hh....",
        "........hb....",
        ".......hb.....",
        ".hb...hb......",
        "Bhb..hb.......",
        "Bhbhhb........",
        "Bhbbb.........",
        "Bhb...........",
        ".b............",
    ]
    key = {"B": "brass0", "b": "brass1", "h": "brass2", "o": "gold1", "g": "gold2", "G": "gold3", "w": "shine"}
    c = Canvas(20, 20)
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            if ch in key:
                c.px(x + 2, y + 2, key[ch])
    return save(c, "wall-lamp")



# ---------------------------------------------------------------- batch: books, window, plants


def bookshelf():
    """Tall wooden bookshelf full of books, for a back wall (front faces down-left)."""
    import random
    rng = random.Random(7)
    c = Canvas(90, 140)
    X0, Y0 = 20, 90
    L, D, H = 12, 4, 66
    SH = [3, 15, 27, 39, 51, 63]  # shelf boards (z of each board's top)
    spines = ["red1", "red2", "navy1", "navy2", "sage1", "sage0", "key1", "gold1", "choc1", "pink0", "terra1", "mah3"]
    books = {}  # (shelf) -> list of (t0, t1, colour, height, band)
    for i, z0 in enumerate(SH[:-1]):
        t, row = 0.6, []
        while t < L - 0.8:
            w = rng.choice([0.5, 0.5, 0.5, 1.0])
            if rng.random() < 0.08:
                t += 1.0  # a gap
                continue
            row.append((t, t + w, rng.choice(spines), rng.randint(7, 11), rng.random() < 0.35))
            t += w
        books[i] = row

    def front(t, z):
        if t < 0.6 or t > L - 0.6 or z >= H - 3:
            return "wood3" if t < 0.3 or z >= H - 1 else "wood2"  # sides and crown
        for i, z0 in enumerate(SH):
            if z0 - 2 <= z < z0:
                return "wood3" if z == z0 - 1 else "wood2"  # shelf board front
        for i, z0 in enumerate(SH[:-1]):
            if z0 <= z < SH[i + 1] - 2:
                for (t0, t1, col, h, band) in books[i]:
                    if t0 <= t < t1 and z < z0 + h:
                        if band and z in (z0 + h - 3, z0 + 2):
                            return "gold2"
                        return "shine" if (t - t0 < 0.25 and z > z0 + 1 and col in ("navy1", "red1", "sage0", "choc1", "mah3")) else col
                return "wood0" if z > SH[i + 1] - 5 else "mah2"  # shadow at the back of the shelf
        return "wood1"
    face_left(c, X0, Y0, 0, L, D, 0, H, front)
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s, z: "wood1" if z < H - 1 else "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood4" if b > D - 0.6 else "wood3")
    # a small plant on top
    px_, py_ = X0 + 2 * 8 - 2 * 1.5, Y0 + 8 + 1.5 - H
    for dx in range(-2, 3):
        c.px(px_ + dx, py_, "terra1"); c.px(px_ + dx, py_ - 1, "terra2")
    for (dx, dy, col) in ((-3, -3, "sage1"), (-2, -4, "sage2"), (-1, -5, "leaf3"), (0, -4, "sage1"), (1, -6, "sage2"), (2, -4, "sage0"), (3, -3, "sage1"), (0, -2, "sage0"), (-1, -3, "sage0"), (1, -3, "sage2"), (2, -5, "sage1")):
        c.px(px_ + dx, py_ + dy, col)
    return save(c, "bookshelf", foot=(X0 + 2 * L - 2 * D, Y0 + L + D))


def window():
    """Tall café window with dark navy frames and small panes, like the original's.
    For the back-right wall (flip for the other one). The glass is left empty: the engine
    paints the current sky into it and casts a sun patch on the floor."""
    c, sky, light = Canvas(110, 170), Canvas(110, 170), Canvas(110, 170)
    L, z0, z1 = 16, 44, 116
    x0, y0 = 20, 140
    pt = lambda t, z: (x0 + 2 * t, y0 + t - z)
    COLS, ROWS = 3, 4
    for t2 in range(L * 2):
        t = t2 / 2
        for z in range(z0, z1):
            x, y = pt(t, z)
            x, y = int(x), int(y)
            border = t < 1 or t >= L - 1 or z < z0 + 3 or z >= z1 - 3
            inner_t = (t - 1) / (L - 2) * COLS
            inner_z = (z - z0 - 3) / (z1 - z0 - 6) * ROWS
            mullion = abs(inner_t - round(inner_t)) * (L - 2) / COLS < 0.3 or abs(inner_z - round(inner_z)) * (z1 - z0 - 6) / ROWS < 0.8
            if border:
                c.px(x, y, "navy2" if (t < 0.5 or z >= z1 - 1) else ("navy1" if z >= z0 + 1 else "navy0"))
            elif mullion:
                c.px(x, y, "navy1")
            else:
                sky.px(x, y, "shine")
    # deep wooden sill with a lip
    for t2 in range(-2, L * 2 + 2):
        t = t2 / 2
        for k, col in ((0, "wood4"), (1, "wood3"), (2, "wood2"), (3, "wood1")):
            x, y = pt(t, z0 - k)
            c.px(int(x), int(y), col)
        x, y = pt(t, z0 + 1)
        c.px(int(x) - 2, int(y) + 1, "wood5"); c.px(int(x) - 1, int(y) + 1, "wood4")
    # sun patch on the floor: the panes thrown down and out from the wall
    for ti in range(0, 2 * L):
        for si in range(4, 30):
            t, depth = ti / 2, si / 2
            tt = t - depth * 0.45
            if not (1 <= tt <= L - 1.5):
                continue
            if any(abs(tt - (1 + k * (L - 2) / COLS)) < 0.3 for k in range(1, COLS)) or any(abs(depth - d) < 0.3 for d in (6, 9.5, 13)):
                continue
            x, y = x0 + 2 * t - 2 * depth, y0 + t + depth
            light.px(x, y, "shine"); light.px(x + 1, y, "shine")
    ax, ay = pt(0, 0)
    return save(c, "window", anchor=(ax, ay), sky=sky, light=light)


def leaf_cluster(c, x, y, rng, big=False):
    """A few pixels of leaf, lit from the top-left like the original's foliage."""
    shape = [(0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1)] + ([(2, 0), (1, -1), (2, 1), (-1, 1)] if big else [])
    for dx, dy in shape:
        k = dx + dy
        col = "leaf3" if k <= -1 and rng.random() < 0.7 else ("sage2" if k <= 0 else ("sage1" if k <= 1 else "sage0"))
        c.px(x + dx, y + dy, col)
    if rng.random() < 0.4:
        c.px(x + 1, y + 2, "leaf0")


def hanging_plant():
    """Pothos in a terracotta pot on three cords, vines trailing down, like the original's."""
    import random
    rng = random.Random(4)
    c = Canvas(60, 90)
    cx, pot_y = 30, 30
    vline(c, cx, 4, pot_y - 3, "wood0")  # one cord up to a hook
    c.px(cx, 3, "brass2")
    # pot: a short terracotta cylinder
    for y in range(pot_y - 2, pot_y + 5):
        half = 6 if y < pot_y + 3 else 5
        for x in range(cx - half, cx + half + 1):
            col = "terra3" if x < cx - half + 2 else ("terra2" if x < cx + 2 else "terra1")
            if y == pot_y - 2:
                col = "terra3"
            c.px(x, y, col)
    # foliage spilling over the rim, then vines trailing down
    for _ in range(14):
        leaf_cluster(c, cx + rng.randint(-8, 7), pot_y - 3 + rng.randint(-3, 3), rng, big=True)
    for v in range(6):
        x = cx + rng.choice([-8, -6, -4, 3, 5, 7])
        length = rng.randint(14, 38)
        for y in range(pot_y + 2, pot_y + length, 3):
            x += rng.choice([-1, 0, 0, 1])
            c.px(x, y + 1, "leaf0")
            leaf_cluster(c, x + rng.choice([-1, 1]), y, rng)
    return save(c, "hanging-plant")


def potted_plant():
    """Big leafy floor plant in a terracotta pot."""
    import random
    rng = random.Random(9)
    c = Canvas(50, 70)
    cx, floor_y = 25, 60
    disc(c, cx, floor_y - 1, 6, 3, lambda dx, dy: "terra0")
    for y in range(floor_y - 12, floor_y):
        half = 6 - (floor_y - y) // 8
        for x in range(cx - half, cx + half + 1):
            c.px(x, y, "terra3" if x < cx - half + 2 else ("terra2" if x < cx + 2 else "terra1"))
    disc(c, cx, floor_y - 12, 6, 2.5, lambda dx, dy: "terra3" if dy < -0.3 else "choc0")
    # stems and a bushy crown of leaves
    for sx in (-3, 0, 3):
        for y in range(floor_y - 26, floor_y - 12):
            c.px(cx + sx + (floor_y - 12 - y) // 6 * (1 if sx > 0 else -1 if sx < 0 else 0), y, "leaf0")
    for _ in range(44):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(0, 1) ** 0.6
        import math
        leaf_cluster(c, round(cx + math.cos(a) * r * 11), round(floor_y - 32 + math.sin(a) * r * 9), rng, big=True)
    return save(c, "potted-plant", foot=(cx, floor_y))


def flower_vase():
    """Small glass vase of pink and yellow flowers for a table or counter."""
    import random
    rng = random.Random(2)
    c = Canvas(30, 30)
    cx, base = 15, 24
    for y in range(base - 6, base + 1):
        half = 2 if y > base - 5 else 1
        for x in range(cx - half, cx + half + 1):
            c.px(x, y, "glass2" if x == cx - half else ("glass1" if y > base - 3 else "glass0"))
    for _ in range(5):  # stems
        c.px(cx + rng.choice([-1, 0, 1]), base - 7, "sage0")
    for (dx, dy) in ((-4, -10), (-2, -12), (0, -10), (2, -13), (4, -10), (-3, -8), (3, -8), (1, -11), (-1, -9)):
        col = rng.choice(["pink1", "pink2", "gold2", "pink1", "key1"])
        c.px(cx + dx, base + dy, col); c.px(cx + dx + 1, base + dy, col)
        c.px(cx + dx, base + dy + 1, "pink0" if col.startswith("pink") else "gold1")
    for (dx, dy) in ((-5, -8), (5, -8), (-1, -7), (1, -7)):
        c.px(cx + dx, base + dy, "sage1")
    return save(c, "flower-vase")



# ---------------------------------------------------------------- batch: rug, seating, lamp, table things


def rug():
    """The original's red patterned rug: lies flat on the floor, 4 x 3 tiles."""
    c = Canvas(160, 90)
    X0, Y0 = 50, 4
    A, B = 32, 24  # 8 units per tile edge

    def col(a, b):
        e = min(a, A - a, b, B - b)
        if e < 0.6:
            return "red0"
        if e < 1.6:
            return "gold1" if (int(a) + int(b)) % 2 else "gold0"
        if e < 2.6:
            return "navy1"
        if e < 3.4:
            return "red3"
        d = abs(a - A / 2) / (A / 2) + abs(b - B / 2) / (B / 2)  # diamond medallion
        if d < 0.18:
            return "key1"
        if d < 0.3:
            return "navy1"
        if d < 0.38:
            return "gold1"
        if d < 0.55:
            return "red2" if (int(a * 2) + int(b * 2)) % 3 else "red3"
        if (int(a) % 4 == 0) and (int(b) % 4 == 0):
            return "navy0"
        return "red1" if (int(a / 2) + int(b / 2)) % 2 else "red2"
    face_top(c, X0, Y0, 0, A, 0, B, 0, col)
    for b2 in range(0, B * 2, 2):  # fringe on the two short ends
        for a in (-0.6, A + 0.1):
            x, y = X0 + 2 * a - b2, Y0 + a + b2 / 2
            c.px(x, y, "key1"); c.px(x + 1, y, "key0")
    return save(c, "rug", foot=(X0 + 2 * A - 2 * B, Y0 + A + B))


def booth():
    """Tufted leather booth bench like the original's, for a back wall (seat faces down-left)."""
    c = Canvas(120, 100)
    X0, Y0 = 20, 50
    L, D = 16, 8
    SEAT, BACK = 11, 30
    face_left(c, X0, Y0, 0, L, D, 0, SEAT - 3, lambda t, z: "wood0" if z < 2 else ("wood2" if t % 4 > 0.4 else "wood1"))  # wood plinth
    face_right(c, X0, Y0, L, 2.5, D, 0, SEAT, lambda s, z: "lea0" if z < SEAT - 3 else "lea1")
    # tall back with channel tufting
    face_left(c, X0, Y0, 0, L, 2.5, SEAT, BACK, lambda t, z: "lea1" if t % 2 < 0.35 else ("lea4" if z > BACK - SEAT - 3 and t % 2 < 1.0 else ("lea3" if t % 2 < 1.1 else "lea2")))
    face_right(c, X0, Y0, L, 0, 2.5, 0, BACK, lambda s, z: "lea1" if z < BACK - 1 else "lea2")
    face_top(c, X0, Y0, 0, L, 0, 2.5, BACK, lambda a, b: "lea3" if b > 1.5 else "lea2")
    # seat cushion: rounded front edge
    face_left(c, X0, Y0, 0, L, D, SEAT - 3, SEAT, lambda t, z: "lea1" if t % 4 < 0.3 else ("lea3" if z >= 2 else "lea2"))
    face_top(c, X0, Y0, 0, L, 2.5, D, SEAT, lambda a, b: "lea1" if a % 4 < 0.3 else ("lea4" if b > D - 1 else "lea3"))
    return save(c, "booth", foot=(X0 + 2 * L - 2 * D, Y0 + L + D))


def armchair():
    """Green velvet armchair like the original's reading chair (seat faces down-left)."""
    c = Canvas(80, 80)
    X0, Y0 = 20, 40
    L, D = 8, 8
    SEAT, ARM, BACK = 10, 16, 27
    for a0 in (0.3, L - 1.3):  # little wood feet
        face_left(c, X0, Y0, a0, a0 + 0.8, D, 0, 3, lambda t, z: "wood1")
    face_left(c, X0, Y0, 0, L, D, 3, SEAT - 2, lambda t, z: "olive1")
    face_right(c, X0, Y0, L, 0, D, 3, ARM, lambda s, z: "olive0" if z < ARM - 2 else "olive1")
    # back
    face_left(c, X0, Y0, 0, L, 2.5, SEAT, BACK, lambda t, z: "olive3" if z > BACK - SEAT - 3 else ("olive2" if t % 3 > 0.3 else "olive1"))
    face_top(c, X0, Y0, 0, L, 0, 2.5, BACK, lambda a, b: "olive3")
    # cushion
    face_left(c, X0, Y0, 1.5, L - 1.5, D, SEAT - 2, SEAT, lambda t, z: "olive2")
    face_top(c, X0, Y0, 1.5, L - 1.5, 2.5, D, SEAT, lambda a, b: "olive3" if b > D - 1 else "olive2")
    # arms: the left one shows its top and front, the right one its outside
    for a0 in (0, L - 1.5):
        face_left(c, X0, Y0, a0, a0 + 1.5, D, 3, ARM, lambda t, z: "olive2" if t < 0.6 else "olive1")
        face_top(c, X0, Y0, a0, a0 + 1.5, 2.5, D, ARM, lambda a, b: "olive3")
    return save(c, "armchair", foot=(X0 + 2 * L - 2 * D, Y0 + L + D))


def floor_lamp():
    """Brass floor lamp with a cream pleated shade, warm light inside."""
    c = Canvas(40, 90)
    cx, floor_y = 20, 80
    disc(c, cx, floor_y - 1, 5, 2.5, lambda dx, dy: "brass2" if dx + dy < -0.5 else "brass1")
    vline(c, cx, floor_y - 52, floor_y - 2, "brass1")
    vline(c, cx - 1, floor_y - 52, floor_y - 3, "brass2")
    top = floor_y - 66
    for y in range(top, top + 14):  # bell shade, wider at the bottom
        half = 4 + (y - top) // 3
        for x in range(cx - half, cx + half + 1):
            pleat = (x - cx) % 3 == 0
            col = "key2" if x < cx - half + 2 else ("key1" if not pleat else "key0")
            if y == top + 13:
                col = "gold2"  # the lit rim
            c.px(x, y, col)
    for x in range(cx - 7, cx + 8):  # light spilling from under the shade
        c.px(x, top + 14, "gold3" if abs(x - cx) < 6 else "gold2")
    return save(c, "floor-lamp", foot=(cx, floor_y))


def special_board():
    """Little A-frame chalkboard for the special of the day."""
    c = Canvas(40, 50)
    x0, floor_y, w, h = 12, 44, 16, 26
    for y in range(floor_y - h, floor_y + 1):
        lean = (floor_y - y) // 6  # leans back a little
        for x in range(x0 + lean, x0 + w + lean):
            edge = x in (x0 + lean, x0 + w + lean - 1) or y in (floor_y - h, floor_y - 6)
            if y > floor_y - 6:
                if x in (x0 + lean, x0 + lean + 1, x0 + w + lean - 2, x0 + w + lean - 1):
                    c.px(x, y, "wood2")  # legs
                continue
            c.px(x, y, "wood3" if edge else "slate1")
    # chalk: a heading line, a little pastry, two lines of text
    for x in range(x0 + 5, x0 + w - 1):
        c.px(x, floor_y - h + 4, "chalk" if x % 3 else "slate1")
    for (dx, dy, col) in ((6, 9, "gold2"), (7, 9, "gold2"), (8, 9, "gold2"), (9, 9, "gold2"), (5, 10, "gold1"), (6, 10, "gold2"), (7, 10, "gold3"), (8, 10, "gold2"), (9, 10, "gold2"), (10, 10, "gold1")):
        c.px(x0 + dx + 2, floor_y - h + dy, col)  # a croissant
    for row, n in ((13, 9), (15, 7), (17, 8)):
        for k in range(n):
            if k % 4 != 3:
                c.px(x0 + 4 + k + (floor_y - (floor_y - h + row)) // 6, floor_y - h + row, "chalk" if row == 13 else "silver1")
    return save(c, "special-board")


def coffee_cup():
    c = Canvas(20, 20)
    cx, y = 10, 12
    disc(c, cx, y + 1, 4.5, 2, lambda dx, dy: "key1" if dy < 0.3 else "key0")  # saucer
    for yy in range(y - 4, y + 1):
        for x in range(cx - 2, cx + 3):
            c.px(x, yy, "key2" if x < cx else "key1")
    disc(c, cx, y - 4, 2.5, 1, lambda dx, dy: "choc1" if dx < 0.4 else "lea3")  # latte
    c.px(cx + 3, y - 3, "key1"); c.px(cx + 4, y - 2, "key1"); c.px(cx + 3, y - 1, "key1")
    return save(c, "coffee-cup")


def laptop():
    c = Canvas(30, 30)
    x0, y0 = 6, 20
    for t in range(12):  # base, angled along the table
        for k in range(5):
            c.px(x0 + t - k, y0 + t // 2 + k // 2, "silver2" if k == 0 else "silver1")
    for t in range(12):  # screen
        for z in range(9):
            col = "silver0" if t in (0, 11) or z in (0, 8) else ("navy2" if z > 5 else "glass2")
            c.px(x0 + t, y0 + t // 2 - z - 1, col)
    return save(c, "laptop")


def cake_stand():
    c = Canvas(30, 34)
    cx, base = 15, 26
    disc(c, cx, base, 3, 1.2, lambda dx, dy: "key0")
    vline(c, cx, base - 3, base - 1, "key0")
    disc(c, cx, base - 4, 6, 2, lambda dx, dy: "key1")  # plate
    for y in range(base - 9, base - 4):  # cake
        for x in range(cx - 4, cx + 5):
            c.px(x, y, "pink1" if y < base - 7 else ("cream1" if y == base - 7 else "choc1"))
    disc(c, cx, base - 9, 4, 1.5, lambda dx, dy: "pink2")
    c.px(cx - 1, base - 11, "red2"); c.px(cx + 1, base - 11, "red2")  # berries
    for y in range(base - 16, base - 4):  # glass dome
        half = round((1 - ((base - 4 - y) / 12) ** 2) ** 0.5 * 6.5)
        for x in (cx - half, cx + half):
            c.px(x, y, "glass2")
        if y == base - 13:
            c.px(cx - half + 1, y, "shine")
    c.px(cx, base - 17, "glass1")
    return save(c, "cake-stand")


ALL = [cafe_table, table_cloth("cafe-table-cloth", "red1", "red2", "gold1", "key1"),
       table_cloth("cafe-table-linen", "key1", "key0", "red2", "key2"), cafe_chair, piano, piano_stool, globe_lamp, wall_lamp,
       bookshelf, window, hanging_plant, potted_plant, flower_vase,
       rug, booth, armchair, floor_lamp, special_board, coffee_cup, laptop, cake_stand]

GLOWS = {"floor-lamp": {"x": 10, "y": 15, "r": 90}, "wall-lamp": {"x": 10, "y": 4, "r": 60}, "globe-lamp": {"x": 7, "y": 38, "r": 80}}


def write_glows():
    import json
    path = os.path.join(OUT, "_companions.json")
    comp = json.load(open(path)) if os.path.exists(path) else {}
    for name, g in GLOWS.items():
        comp[name] = {**comp.get(name, {}), "glow": g}
    for name, info in EXTRA.items():
        comp[name] = {**comp.get(name, {}), **info}
    json.dump(comp, open(path, "w"), indent=1)


if __name__ == "__main__":
    imgs = [(f.__name__, f()) for f in ALL]
    write_glows()
    for n, im in imgs:
        print(f"{n:14s} {im.size}")
    if "--preview" in sys.argv:
        pad = 6
        W = sum(i.width + pad for _, i in imgs) + pad
        H = max(i.height for _, i in imgs) + pad * 2
        sheet = Image.new("RGBA", (W, H), (110, 150, 120, 255))
        x = pad
        for _, i in imgs:
            sheet.alpha_composite(i, (x, H - pad - i.height))
            x += i.width + pad
        sheet.resize((W * 6, H * 6), Image.NEAREST).save(sys.argv[-1] if sys.argv[-1].endswith(".png") else os.path.join(ART, "preview", "props.png"))

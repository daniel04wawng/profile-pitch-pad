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
    "rust0": "#4a1d12", "rust1": "#6e2c1a", "rust2": "#94402a", "rust3": "#b85a3a", "rust4": "#d47a55",
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


def save(c, name, anchor=None, sky=None, light=None, foot=None, size=None, centre=False):
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
    if size is not None:  # floor the piece covers, in grid units (8 per tile), from its foot
        info["size"] = {"a": size[0], "b": size[1], "from": "centre" if centre else "front"}
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
    return save(c, "cafe-table", foot=(cx, floor_y), size=(8, 8), centre=True)


def cafe_chair():
    """Bentwood café chair facing down-left (flip it in the editor to face down-right):
    four thin legs, a round-edged seat, a hooped back with two slats."""
    c = Canvas(50, 70)
    X0, Y0 = 14, 30
    N, SEAT, BACK = 5, 11, 29  # seat size (units), seat height, top of the back (px)

    def leg(a, b, col):
        x, y = X0 + 2 * a - 2 * b, Y0 + a + b
        vline(c, x, y - SEAT, y, col)

    leg(0.5, 0.5, "wood0"); leg(N - 0.5, 0.5, "wood1")  # back legs
    # the back: two posts rising from the back legs, a hoop on top, a rail, two slats
    def back(t, z):
        post = t < 0.7 or t > N - 1.2
        rail = z >= BACK - SEAT - 3 or SEAT + 5 <= z + SEAT <= SEAT + 6
        slat = abs(t - N * 0.38) < 0.3 or abs(t - N * 0.62) < 0.3
        if post or rail or slat:
            return "wood4" if (z >= BACK - SEAT - 1 or t < 0.35) else ("wood3" if post or rail else "wood2")
        return None
    face_left(c, X0, Y0, 0.2, N - 0.5, 0.5, SEAT, BACK, back)
    # seat: thin top with a lit edge
    face_left(c, X0, Y0, 0, N, N, SEAT - 2, SEAT, lambda t, z: "wood2" if z < 1 else "wood3")
    face_right(c, X0, Y0, N, 0, N, SEAT - 2, SEAT, lambda s_, z: "wood1")
    face_top(c, X0, Y0, 0, N, 0, N, SEAT, lambda a_, b_: "wood5" if (b_ > N - 0.7 or a_ < 0.5) else "wood4")
    leg(0.5, N - 0.5, "wood2"); leg(N - 0.5, N - 0.5, "wood1")  # front legs
    # a stretcher ring between the legs
    for t2 in range(0, int(N * 2) + 1):
        t = t2 / 2
        for (a_, b_) in ((t, N - 0.5), (N - 0.5, t)):
            x, y = X0 + 2 * a_ - 2 * b_, Y0 + a_ + b_ - 4
            c.px(x, y, "wood1")
    cx, cy = X0 + N - N, Y0 + N  # the seat's centre on the floor
    return save(c, "cafe-chair", foot=(X0, Y0 + N), size=(N, N), centre=True)

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
    return save(c, "piano", foot=(X0 + 2 * L - 2 * (D + KD), Y0 + L + D + KD), size=(L, D + KD))


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
    return save(c, "piano-stool", foot=(cx, floor_y), size=(4, 4), centre=True)


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
        return save(c, name, foot=(cx, floor_y), size=(8, 8), centre=True)
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
    return save(c, "bookshelf", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def window():
    """Tall café window in the room's wood, small panes with a glint of light on the glass.
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
            border = t < 1.5 or t >= L - 1.5 or z < z0 + 4 or z >= z1 - 4
            inner_t = (t - 1.5) / (L - 3) * COLS
            inner_z = (z - z0 - 4) / (z1 - z0 - 8) * ROWS
            mullion = abs(inner_t - round(inner_t)) * (L - 3) / COLS < 0.35 or abs(inner_z - round(inner_z)) * (z1 - z0 - 8) / ROWS < 1.0
            if border:
                # chunky wood frame in the room's wood: lit on its left side and top, a groove inside
                inner = (1 <= t < 1.5) or (L - 1.5 <= t < L - 1) or (z0 + 3 <= z < z0 + 4) or (z1 - 4 <= z < z1 - 3)
                col = "wood1" if inner else ("wood4" if (t < 0.5 or z >= z1 - 1) else "wood3")
                c.px(x, y, col)
            elif mullion:
                c.px(x, y, "wood3" if (z % 2 or t2 % 2) else "wood2")
            else:
                sky.px(x, y, "shine")
                # glass catching the light: two thin diagonal glints per pane
                pane_t = inner_t % 1
                pane_z = inner_z % 1
                g = pane_t - (1 - pane_z)
                if abs(g) < 0.05 and (int(inner_t) + int(inner_z)) % 2 == 0:
                    c.im.putpixel((x, y), (255, 246, 224, 80))
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
    return save(c, "potted-plant", foot=(cx, floor_y), size=(4, 4), centre=True)


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
    return save(c, "rug", foot=(X0 + 2 * A - 2 * B, Y0 + A + B), size=(A, B))


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
    return save(c, "booth", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def armchair():
    """Green velvet armchair like the original's reading chair, facing down-left: a plinth,
    a tall rounded back, two padded arms and a seat cushion, on little wooden feet."""
    c = Canvas(80, 80)
    X0, Y0 = 22, 38
    L, D = 8, 8
    BASE, SEAT, ARM, BACK = 3, 10, 17, 28
    BK, AW = 2.5, 1.6  # back thickness, arm width (units)
    for (a_, b_) in ((0.6, D - 0.4), (L - 0.4, D - 0.4), (L - 0.4, 0.6)):  # feet
        x, y = X0 + 2 * a_ - 2 * b_, Y0 + a_ + b_
        vline(c, x, y - BASE, y, "wood1"); vline(c, x + 1, y - BASE, y, "wood0")
    # plinth under everything
    face_left(c, X0, Y0, 0, L, D, BASE, SEAT, lambda t, z: "olive1" if z < SEAT - BASE - 1 else "olive2")
    face_right(c, X0, Y0, L, 0, D, BASE, SEAT, lambda s_, z: "olive0")
    # back
    face_left(c, X0, Y0, 0, L, BK, SEAT, BACK, lambda t, z: "olive3" if z >= BACK - SEAT - 2 else ("olive1" if t % (L / 3) < 0.3 else "olive2"))
    face_right(c, X0, Y0, L, 0, BK, SEAT, BACK, lambda s_, z: "olive1" if z >= BACK - SEAT - 1 else "olive0")
    face_top(c, X0, Y0, 0, L, 0, BK, BACK, lambda a_, b_: "olive3")
    # left arm (its inner side faces the seat), then the cushion, then the right arm in front
    def arm(a0):
        face_left(c, X0, Y0, a0, a0 + AW, D, SEAT, ARM, lambda t, z: "olive3" if z >= ARM - SEAT - 1 else "olive2")
        face_right(c, X0, Y0, a0 + AW, BK, D, SEAT, ARM, lambda s_, z: "olive1" if z >= ARM - SEAT - 1 else "olive0")
        face_top(c, X0, Y0, a0, a0 + AW, BK, D, ARM, lambda a_, b_: "olive3" if b_ > D - 0.8 else "olive2")
    arm(0)
    face_left(c, X0, Y0, AW, L - AW, D, SEAT, SEAT + 3, lambda t, z: "olive2" if z < 2 else "olive3")
    face_top(c, X0, Y0, AW, L - AW, BK, D, SEAT + 3, lambda a_, b_: "olive3" if b_ > D - 1 else "olive2")
    arm(L - AW)
    return save(c, "armchair", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))

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
    return save(c, "floor-lamp", foot=(cx, floor_y), size=(4, 4), centre=True)


def special_board():
    """A-frame chalkboard for the special of the day, facing down-left like the furniture:
    an upright framed slate on short legs."""
    c = Canvas(50, 60)
    X0, Y0 = 18, 40
    W, B, LEG, H = 7, 2, 4, 26  # width (units), depth of the front board, leg height, top (px)
    for t0 in (0, W - 0.8):  # front legs
        face_left(c, X0, Y0, t0, t0 + 0.8, B, 0, LEG, lambda t, z: "wood2")

    def slate(t, z):
        if t < 0.6 or t > W - 0.6 or z < 1.5 or z > H - LEG - 1.5:
            return "wood4" if (z > H - LEG - 1 or t < 0.3) else "wood3"  # frame
        u = (t - 0.6) / (W - 1.2)
        top = H - LEG - 1.5
        if top - 4 <= z < top - 3 and 0.15 < u < 0.85:
            return "chalk"  # heading
        if top - 9 <= z < top - 6 and abs(u - 0.5) < 0.28 - abs(z - (top - 7.5)) * 0.08:
            return "gold3" if z >= top - 7 else "gold1"  # a croissant
        for zr, end in ((7, 0.8), (5, 0.65), (3, 0.75)):
            if int(z) == zr and 0.15 < u < end:
                return "silver1"
        return "slate1"
    face_left(c, X0, Y0, 0, W, B, LEG, H, slate)
    return save(c, "special-board", foot=(X0 + 2 * (W / 2) - 2 * B, Y0 + W / 2 + B))

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


def record_cabinet():
    """Low wood cabinet of records with a turntable on top, after the original's (which is
    too tangled with plants to cut). Faces down-left, 3 x 1 half-tiles."""
    import random
    rng = random.Random(5)
    c = Canvas(90, 90)
    X0, Y0 = 20, 50
    L, D, H = 12, 4, 30
    CUB = [(2, 14), (16, 27)]  # two rows of cubbies (z ranges)
    sleeves = ["navy1", "red1", "key0", "sage0", "gold0", "red2", "navy2", "choc1", "key1", "terra1"]
    cols = {}
    for row in range(2):
        t, run = 0.8, []
        while t < L - 0.8:
            w = rng.choice([0.25, 0.25, 0.5])
            run.append((t, t + w, rng.choice(sleeves)))
            t += w
        cols[row] = run

    def front(t, z):
        if t < 0.6 or t > L - 0.6 or z >= H - 2 or abs(t - L / 2) < 0.3:
            return "wood3" if (t < 0.3 or z >= H - 1) else "wood2"  # frame, top rail, middle divider
        for row, (z0, z1) in enumerate(CUB):
            if z0 <= z < z1:
                for t0, t1, col in cols[row]:
                    if t0 <= t < t1 and z < z1 - (1 if (t0 * 4) % 3 else 2):
                        return "shine" if (t - t0 < 0.12 and col in ("navy1", "red1", "sage0", "choc1")) else col
                return "wood0"
        return "wood2" if z < 2 else "wood1"  # shelf boards
    face_left(c, X0, Y0, 0, L, D, 0, H, front)
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "wood1" if z < H - 1 else "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood5" if b > D - 0.6 else "wood4")
    # turntable: a dark plinth with a black record and a brass tonearm
    face_top(c, X0, Y0, 1.5, 7.5, 0.6, D - 0.4, H + 2, lambda a, b: "wood1")
    face_left(c, X0, Y0, 1.5, 7.5, D - 0.4, H, H + 2, lambda t, z: "wood0")
    rx, ry = X0 + 2 * 4.2 - 2 * 2.1, Y0 + 4.2 + 2.1 - H - 2
    disc(c, rx, ry, 4.5, 2.3, lambda dx, dy: "red2" if dx * dx + dy * dy < 0.08 else ("slate1" if (dx * dx + dy * dy) % 0.3 < 0.15 else "iron"))
    for k in range(5):
        c.px(rx + 4 - k, ry - 2 + k // 2, "brass2" if k < 2 else "brass1")
    # a little vase of flowers on the right
    vx, vy = X0 + 2 * 10 - 2 * 2, Y0 + 10 + 2 - H
    for y in range(vy - 4, vy + 1):
        c.px(vx, y, "glass1"); c.px(vx + 1, y, "glass0")
    for dx, dy, col in ((-2, -6, "gold2"), (0, -7, "pink1"), (2, -6, "gold2"), (-1, -8, "gold3"), (1, -8, "pink2"), (-2, -5, "sage1"), (2, -5, "sage1"), (0, -5, "sage0")):
        c.px(vx + dx, vy + dy, col)
    return save(c, "record-cabinet", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def back_bar_shelves():
    """Wall shelf unit for behind the counter, like the original's back bar (back panel, sides,
    crown, three shelves):
    jars of coffee, matcha, sugar and beans, mugs, stacked cups and a little plant.
    For the back-right wall (flip for the other one)."""
    import random
    rng = random.Random(12)
    c = Canvas(110, 140)
    X0, Y0 = 16, 96
    L, D = 16, 3
    SHELVES = [0, 18, 36]  # heights of the shelf tops above the lowest one (px)

    def at(t, b, z):
        return X0 + 2 * t - 2 * b, Y0 + t + b - z

    def jar(t, z, fill, lid):
        x, y = at(t, D * 0.5, z)
        x, y = round(x), round(y)
        for yy in range(y - 7, y + 1):
            for xx in range(x - 2, x + 2):
                inside = yy > y - 6 and x - 2 < xx < x + 1
                col = (fill if yy > y - 5 else "glass2") if inside else "glass1"
                if xx == x - 2 and yy > y - 6:
                    col = "shine" if yy == y - 4 else "glass2"
                c.px(xx, yy, col)
        for xx in range(x - 2, x + 2):
            c.px(xx, y - 8, lid)

    def mug(t, z, col):
        x, y = at(t, D * 0.5, z)
        x, y = round(x), round(y)
        for yy in range(y - 3, y + 1):
            for xx in range(x - 1, x + 2):
                c.px(xx, yy, "key2" if xx == x - 1 else col)
        c.px(x + 2, y - 2, col); c.px(x + 2, y - 1, col)

    def cups(t, z):
        x, y = at(t, D * 0.5, z)
        x, y = round(x), round(y)
        for k in range(3):
            for xx in range(x - 2 + (k % 2 == 0) * 0, x + 2):
                c.px(xx, y - k * 2, "key1" if k % 2 else "key2")
                c.px(xx, y - k * 2 - 1, "key0")

    def plant(t, z):
        x, y = at(t, D * 0.5, z)
        x, y = round(x), round(y)
        for yy in range(y - 3, y + 1):
            for xx in range(x - 2, x + 2):
                c.px(xx, yy, "terra2" if xx < x else "terra1")
        for dx, dy, col in ((-3, -5, "sage1"), (-2, -6, "sage2"), (-1, -7, "leaf3"), (0, -6, "sage1"), (1, -7, "sage2"),
                            (2, -5, "sage0"), (3, -4, "sage1"), (-1, -4, "sage0"), (1, -4, "sage1"), (4, -2, "sage1"), (-4, -3, "sage2")):
            c.px(x + dx, y + dy, col)

    fills = [("choc1", "brass1"), ("sage1", "wood3"), ("key1", "brass2"), ("choc0", "wood3"), ("gold1", "brass1"), ("sage2", "wood4")]
    TOP = SHELVES[-1] + 16  # crown of the unit
    # the unit's back panel against the wall, then its two side uprights and crown
    face_left(c, X0, Y0, 0, L, 0.2, SHELVES[0] - 3, TOP, lambda t, zz: "wood1" if t % 2 < 0.25 else "wood2")
    # inside of the near end panel (you look into the unit past it), then a bottom apron
    face_right(c, X0, Y0, 0.8, 0.2, D, SHELVES[0] - 4, TOP, lambda s_, zz: "wood1" if s_ < D - 1 else "wood2")
    face_left(c, X0, Y0, 0, L, D, SHELVES[0] - 4, SHELVES[0] - 2, lambda t, zz: "wood2")
    for i, z in enumerate(SHELVES):
        face_top(c, X0, Y0, 0, L, 0, D, z, lambda a, b: "wood4" if b > D - 0.7 else "wood3")
        face_left(c, X0, Y0, 0, L, D, z - 2, z, lambda t, zz: "wood2" if zz < 1 else "wood3")
        # what's on the shelf, back to front along it
        t = 1.0
        while t < L - 1.5:
            kind = rng.choice(["jar", "jar", "jar", "mug", "cups", "plant"] if i else ["jar", "mug", "mug", "cups"])
            if kind == "jar":
                jar(t, z, *fills[rng.randrange(len(fills))])
                t += 2.2
            elif kind == "mug":
                mug(t, z, rng.choice(["key1", "sage1", "terra2", "navy2"]))
                t += 1.8
            elif kind == "cups":
                cups(t, z)
                t += 2.4
            else:
                plant(t, z)
                t += 3.0
    # side uprights and the crown, drawn last so they frame the shelves
    face_left(c, X0, Y0, 0, 0.8, D, SHELVES[0] - 4, TOP, lambda t, zz: "wood4" if t < 0.35 else "wood3")
    face_left(c, X0, Y0, L - 0.8, L, D, SHELVES[0] - 4, TOP, lambda t, zz: "wood3")
    face_right(c, X0, Y0, L, 0, D, SHELVES[0] - 4, TOP, lambda s_, zz: "wood1")
    face_left(c, X0, Y0, -0.3, L + 0.3, D + 0.3, TOP - 3, TOP, lambda t, zz: "wood4" if zz >= 2 else "wood3")
    face_top(c, X0, Y0, -0.3, L + 0.3, 0, D + 0.3, TOP, lambda a, b: "wood5" if b > D - 0.4 else "wood4")
    return save(c, "back-bar-shelves", foot=at(0, 0, SHELVES[0] - 4))


def bar_counter():
    """Plain wooden bar counter, 3 tiles long, the pastry counter's height: framed panels on
    the front, a thick lit top that overhangs a little. Line up copies for a longer bar."""
    c = Canvas(130, 100)
    X0, Y0 = 22, 40
    L, D, H = 24, 8, 24

    def panels(t, z):
        if z < 2:
            return "wood0"  # kick plate shadow
        k = t % 4
        if k < 0.35:
            return "wood1"  # stile
        if k < 0.7 or z >= H - 6:
            return "wood3"  # moulding catching the light
        if k > 3.6 or z < 4:
            return "wood1"
        return "wood2"
    face_left(c, X0, Y0, 0.3, L - 0.3, D - 0.3, 0, H - 3, panels)
    face_right(c, X0, Y0, L - 0.3, 0.3, D - 0.3, 0, H - 3, lambda s_, z: "wood1" if z > 1 else "wood0")
    # top: thick slab with an overhang and a lit front edge
    face_left(c, X0, Y0, 0, L, D, H - 3, H, lambda t, z: "wood4" if z >= 2 else "wood3")
    face_right(c, X0, Y0, L, 0, D, H - 3, H, lambda s_, z: "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood5" if (b > D - 0.6 or a > L - 0.6) else ("wood5" if abs(a - b * 1.4 - 3) < 0.6 else "wood4"))
    return save(c, "bar-counter", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def espresso_station():
    """Espresso machine with a grinder beside it, to sit on a counter: steel body with brass
    trim, two group heads with wooden handles, drip tray, cups warming on top, steam wand,
    and a pressure gauge. Faces down-left."""
    c = Canvas(70, 60)
    X0, Y0 = 14, 30
    L, D, H = 8, 4, 14

    def front(t, z):
        if z < 1.5:
            return "iron" if int(t * 4) % 2 else "slate1"  # drip tray grille
        if z >= H - 2:
            return "brass2" if z >= H - 1 else "brass1"  # brass trim on top
        if 3 <= z < 6 and any(abs(t - g) < 0.6 for g in (2.2, 5.2)):
            return "iron"  # group heads
        if 9 <= z < 11 and abs(t - L / 2 - 0.2) < 0.7:
            return "key1" if z == 10 else "iron"  # pressure gauge
        return "silver2" if t < 0.6 else ("silver1" if z > 6 else "silver0")
    face_left(c, X0, Y0, 0, L, D, 0, H, front)
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "brass1" if z >= H - 2 else "silver0")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "silver2" if b > D - 0.6 else "silver1")
    for g in (2.2, 5.2):  # portafilter handles poking out toward the viewer
        x, y = X0 + 2 * g - 2 * (D + 0.5), Y0 + g + D + 0.5 - 4
        c.px(x - 1, y, "iron"); c.px(x - 2, y + 1, "wood2"); c.px(x - 3, y + 1, "wood3"); c.px(x - 4, y + 2, "wood2")
        c.px(x + 1, y + 2, "key2")  # a shot cup waiting under it
    for k, cx in enumerate((1.5, 3.5, 5.5)):  # cups warming on top
        x, y = round(X0 + 2 * cx - 2 * 2), round(Y0 + cx + 2 - H)
        for yy in range(y - 2, y + 1):
            c.px(x, yy, "key2"); c.px(x + 1, yy, "key1")
    sx, sy = round(X0 + 2 * L - 2 * (D - 0.5)), round(Y0 + L + D - 0.5 - 9)  # steam wand
    for k in range(6):
        c.px(sx + 1, sy + k, "silver2" if k < 5 else "silver1")
    # grinder: a dark base, a glass hopper of beans
    gx, gy = round(X0 + 2 * (L + 2.5) - 2 * 2), round(Y0 + L + 2.5 + 2)
    for yy in range(gy - 8, gy + 1):
        for xx in range(gx - 2, gx + 2):
            c.px(xx, yy, "wood1" if xx < gx else "wood0")
    for yy in range(gy - 15, gy - 8):
        half = 3 - (gy - 8 - yy) // 4
        for xx in range(gx - half - 1, gx + half + 1):
            inside = yy > gy - 13
            c.px(xx, yy, ("choc1" if (xx + yy) % 2 else "choc0") if inside else "glass1")
        c.px(gx - half - 1, yy, "glass2")
    for xx in range(gx - 3, gx + 3):
        c.px(xx, gy - 16, "iron")
    return save(c, "espresso-station", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def cafe_chair_back():
    """The bentwood café chair turned away from you (facing up-right; flip for up-left), for
    the near side of a table: its hooped back is in front, the seat behind it."""
    c = Canvas(50, 70)
    X0, Y0 = 14, 30
    N, SEAT, BACK = 5, 11, 29

    def leg(a, b, col):
        x, y = X0 + 2 * a - 2 * b, Y0 + a + b
        vline(c, x, y - SEAT, y, col)

    leg(0.5, 0.5, "wood1"); leg(N - 0.5, 0.5, "wood1")  # far legs
    face_left(c, X0, Y0, 0, N, N, SEAT - 2, SEAT, lambda t, z: "wood2" if z < 1 else "wood3")
    face_right(c, X0, Y0, N, 0, N, SEAT - 2, SEAT, lambda s_, z: "wood1")
    face_top(c, X0, Y0, 0, N, 0, N, SEAT, lambda a_, b_: "wood5" if (b_ > N - 0.7 or a_ < 0.5) else "wood4")
    for t2 in range(0, int(N * 2) + 1):  # stretcher ring
        t = t2 / 2
        for (a_, b_) in ((t, N - 0.5), (N - 0.5, t)):
            x, y = X0 + 2 * a_ - 2 * b_, Y0 + a_ + b_ - 4
            c.px(x, y, "wood1")
    leg(0.5, N - 0.5, "wood2"); leg(N - 0.5, N - 0.5, "wood1")  # near legs, which carry the back

    def back(t, z):
        post = t < 0.7 or t > N - 1.2
        rail = z >= BACK - SEAT - 3 or 5 <= z <= 6
        slat = abs(t - N * 0.38) < 0.3 or abs(t - N * 0.62) < 0.3
        if post or rail or slat:
            return "wood3" if (z >= BACK - SEAT - 1 or t < 0.35) else ("wood2" if post or rail else "wood1")
        return None  # you see the seat through the gaps
    face_left(c, X0, Y0, 0.2, N - 0.5, N - 0.5, SEAT, BACK, back)
    return save(c, "cafe-chair-back", foot=(X0, Y0 + N), size=(N, N), centre=True)


# ---------------------------------------------------------------- back views (for Rotate)
# Each piece seen from behind: the same footprint turned 180 degrees, so what was its back
# now faces you. Same canvas origin and foot as the front view, so rotating keeps its spot.


def wood_back(t, z, step=4):
    """Plain back panelling: vertical boards with a lit edge every `step` units."""
    k = t % step
    return "wood1" if k < 0.3 else ("wood3" if k < 0.6 else "wood2")


def piano_back():
    c = Canvas(140, 160)
    X0, Y0 = 24, 76
    L, D, KD = 20, 4, 4
    KB, TOP = 22, 64
    m = ["mah0", "mah1", "mah2", "mah3", "mah4", "mah5"]
    # keybed sticks out behind (mostly hidden): its far end, then the tall body in front of it
    face_right(c, X0, Y0, L, 0, KD, 0, KB + 3, lambda s_, z: m[1])
    face_right(c, X0, Y0, L, KD, KD + D, 0, TOP, lambda s_, z: m[3] if z >= TOP - 1 else m[1])
    def back(t, z):
        if z < 2:
            return m[0]
        if z >= TOP - 3:
            return m[3]
        k = t % (L / 4)
        if k < 0.4 or z in (2, 3, TOP - 4):
            return m[1]  # frame of the back's braces
        if abs(t - L / 2) < 0.5:
            return m[2]  # the soundboard brace
        return m[2] if (z // 6) % 2 else m[1]
    face_left(c, X0, Y0, 0, L, KD + D, 0, TOP, back)
    def lid(a, b):
        d = abs(a - L * 0.4)
        return m[5] if (d < 2.5 and b < KD + D - 1.5) else (m[4] if d < 6 or b > KD + D - 0.5 else m[3])
    face_top(c, X0, Y0, -0.3, L + 0.3, KD - 0.3, KD + D + 0.3, TOP, lid)
    # the brass lamp from behind (mirrored along the piano)
    lx, ly = X0 + 2 * (L * 0.38) - 2 * (KD + D * 0.5), Y0 + L * 0.38 + KD + D * 0.5 - TOP
    for dx in range(-3, 4):
        c.px(lx + dx, ly, "brass1")
    vline(c, lx, ly - 9, ly - 1, "brass1")
    for dx in range(-6, 7):
        y = ly - 12 + (dx + 6) // 3
        c.px(lx + dx, y - 1, "brass2"); c.px(lx + dx, y, "brass1")
    return save(c, "piano-back", foot=(X0 + 2 * L - 2 * (D + KD), Y0 + L + D + KD), size=(L, D + KD))


def bookshelf_back():
    c = Canvas(90, 140)
    X0, Y0 = 20, 90
    L, D, H = 12, 4, 66
    face_left(c, X0, Y0, 0, L, D, 0, H, lambda t, z: "wood3" if z >= H - 3 else ("wood1" if z < 2 else wood_back(t, z, 3)))
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "wood1" if z < H - 1 else "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood4" if b > D - 0.6 else "wood3")
    px_, py_ = round(X0 + 2 * 4 - 2 * 2.5), round(Y0 + 4 + 2.5 - H)  # the plant, now at the other end
    for dx in range(-2, 3):
        c.px(px_ + dx, py_, "terra1"); c.px(px_ + dx, py_ - 1, "terra2")
    for (dx, dy, col) in ((-3, -3, "sage1"), (-2, -4, "sage2"), (-1, -5, "leaf3"), (0, -4, "sage1"), (1, -6, "sage2"), (2, -4, "sage0"), (3, -3, "sage1"), (0, -2, "sage0")):
        c.px(px_ + dx, py_ + dy, col)
    return save(c, "bookshelf-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def armchair_back():
    c = Canvas(80, 80)
    X0, Y0 = 22, 38
    L, D = 8, 8
    BASE, SEAT, ARM, BACK = 3, 10, 17, 28
    BK, AW = 2.5, 1.6
    for (a_, b_) in ((0.6, D - 0.4), (L - 0.4, D - 0.4), (L - 0.4, 0.6)):
        x, y = X0 + 2 * a_ - 2 * b_, Y0 + a_ + b_
        vline(c, x, y - BASE, y, "wood1"); vline(c, x + 1, y - BASE, y, "wood0")
    # the far arms' tops peek over; the tall back is nearest you
    for a0 in (0, L - AW):
        face_top(c, X0, Y0, a0, a0 + AW, 0, D - BK, ARM, lambda a_, b_: "olive3")
        face_right(c, X0, Y0, a0 + AW, 0, D - BK, SEAT, ARM, lambda s_, z: "olive1")
    face_right(c, X0, Y0, L, 0, D, BASE, ARM, lambda s_, z: "olive0" if z < ARM - BASE - 1 else "olive1")
    face_left(c, X0, Y0, 0, L, D, BASE, BACK, lambda t, z: "olive3" if z >= BACK - BASE - 2 else ("olive1" if (t < 0.4 or t > L - 0.4 or z < 2) else "olive2"))
    face_right(c, X0, Y0, L, D - BK, D, BASE, BACK, lambda s_, z: "olive1" if z >= BACK - BASE - 1 else "olive0")
    face_top(c, X0, Y0, 0, L, D - BK, D, BACK, lambda a_, b_: "olive3")
    return save(c, "armchair-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def booth_back():
    c = Canvas(120, 100)
    X0, Y0 = 20, 50
    L, D = 16, 8
    SEAT, BACK = 11, 30
    face_right(c, X0, Y0, L, 0, D - 2.5, 0, SEAT, lambda s_, z: "lea0" if z < SEAT - 3 else "lea1")
    face_left(c, X0, Y0, 0, L, D, 0, BACK, lambda t, z: "wood0" if z < 2 else ("wood3" if z >= BACK - 2 else wood_back(t, z, 4)))
    face_right(c, X0, Y0, L, D - 2.5, D, 0, BACK, lambda s_, z: "wood1" if z < BACK - 1 else "wood2")
    face_top(c, X0, Y0, 0, L, D - 2.5, D, BACK, lambda a, b: "lea3" if b < D - 1.5 else "wood4")
    return save(c, "booth-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def bar_counter_back():
    """The bartender's side: open shelves under the top with cups and glasses."""
    import random
    rng = random.Random(3)
    c = Canvas(130, 100)
    X0, Y0 = 22, 40
    L, D, H = 24, 8, 24
    items = {}
    for row, z0 in ((0, 3), (1, 12)):
        t, run = 1.0, []
        while t < L - 1.5:
            kind = rng.choice(["cup", "cup", "glass", "jar", None])
            run.append((t, kind))
            t += 1.4
        items[row] = run

    def shelf(t, z):
        if z < 2 or t < 0.5 or t > L - 0.5 or abs(t % 8) < 0.4:
            return "wood2"  # frame and dividers
        for row, (z0, z1) in enumerate(((3, 10), (12, 19))):
            if z0 - 1 <= z < z0:
                return "wood3"  # shelf board
            if z0 <= z < z1:
                for t0, kind in items[row]:
                    if kind and t0 <= t < t0 + 0.9:
                        h = {"cup": 3, "glass": 5, "jar": 6}[kind]
                        if z < z0 + h:
                            return {"cup": "key1" if t - t0 < 0.4 else "key0", "glass": "glass2" if t - t0 < 0.3 else "glass1", "jar": "choc1" if z < z0 + 4 else "brass1"}[kind]
                return "wood0"  # the dark inside of the shelf
        return "wood1"
    face_left(c, X0, Y0, 0.3, L - 0.3, D - 0.3, 0, H - 3, shelf)
    face_right(c, X0, Y0, L - 0.3, 0.3, D - 0.3, 0, H - 3, lambda s_, z: "wood1" if z > 1 else "wood0")
    face_left(c, X0, Y0, 0, L, D, H - 3, H, lambda t, z: "wood4" if z >= 2 else "wood3")
    face_right(c, X0, Y0, L, 0, D, H - 3, H, lambda s_, z: "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood5" if (b > D - 0.6 or a > L - 0.6) else ("wood5" if abs(a - b * 1.4 - 3) < 0.6 else "wood4"))
    return save(c, "bar-counter-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def record_cabinet_back():
    c = Canvas(90, 90)
    X0, Y0 = 20, 50
    L, D, H = 12, 4, 30
    face_left(c, X0, Y0, 0, L, D, 0, H, lambda t, z: "wood3" if z >= H - 2 else ("wood1" if z < 2 else wood_back(t, z, 3)))
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "wood1" if z < H - 1 else "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood5" if b > D - 0.6 else "wood4")
    face_top(c, X0, Y0, 4.5, 10.5, 0.4, D - 0.6, H + 2, lambda a, b: "wood1")  # turntable, now at the other end
    face_left(c, X0, Y0, 4.5, 10.5, D - 0.6, H, H + 2, lambda t, z: "wood0")
    rx, ry = X0 + 2 * 7.8 - 2 * 1.9, Y0 + 7.8 + 1.9 - H - 2
    disc(c, rx, ry, 4.5, 2.3, lambda dx, dy: "red2" if dx * dx + dy * dy < 0.08 else ("slate1" if (dx * dx + dy * dy) % 0.3 < 0.15 else "iron"))
    vx, vy = round(X0 + 2 * 2 - 2 * 2), round(Y0 + 2 + 2 - H)
    for y in range(vy - 4, vy + 1):
        c.px(vx, y, "glass1"); c.px(vx + 1, y, "glass0")
    for dx, dy, col in ((-2, -6, "gold2"), (0, -7, "pink1"), (2, -6, "gold2"), (-1, -8, "gold3"), (1, -8, "pink2"), (-2, -5, "sage1"), (2, -5, "sage1")):
        c.px(vx + dx, vy + dy, col)
    return save(c, "record-cabinet-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def espresso_station_back():
    c = Canvas(70, 60)
    X0, Y0 = 14, 30
    L, D, H = 8, 4, 14
    # the grinder is now on the far left, behind the machine
    gx, gy = round(X0 + 2 * (-2.0) - 2 * 2), round(Y0 - 2.0 + 2)
    for yy in range(gy - 8, gy + 1):
        for xx in range(gx - 2, gx + 2):
            c.px(xx, yy, "wood1" if xx < gx else "wood0")
    for yy in range(gy - 15, gy - 8):
        half = 3 - (gy - 8 - yy) // 4
        for xx in range(gx - half - 1, gx + half + 1):
            c.px(xx, yy, ("choc1" if (xx + yy) % 2 else "choc0") if yy > gy - 13 else "glass1")
    face_left(c, X0, Y0, 0, L, D, 0, H, lambda t, z: "brass2" if z >= H - 1 else ("brass1" if z >= H - 2 else ("silver0" if (t * 2) % 2 < 0.25 else "silver1")))
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "brass1" if z >= H - 2 else "silver0")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "silver2" if b > D - 0.6 else "silver1")
    for cx in (2.5, 4.5, 6.5):
        x, y = round(X0 + 2 * cx - 2 * 2), round(Y0 + cx + 2 - H)
        for yy in range(y - 2, y + 1):
            c.px(x, yy, "key2"); c.px(x + 1, yy, "key1")
    return save(c, "espresso-station-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def laptop_back():
    c = Canvas(30, 30)
    x0, y0 = 6, 20
    for t in range(12):  # lid seen from behind, base hidden behind it
        for z in range(9):
            col = "silver0" if t in (0, 11) or z in (0, 8) else "silver1"
            if 4 <= t <= 6 and 3 <= z <= 5:
                col = "silver2"  # a little logo
            c.px(x0 + t, y0 + t // 2 - z - 1, col)
    for t in range(12):
        c.px(x0 + t + 1, y0 + t // 2, "silver0")
    return save(c, "laptop-back")


# ---------------------------------------------------------------- more plants


def pot(c, cx, floor_y, half, h, rim=True, colours=("terra3", "terra2", "terra1", "terra0")):
    """A tapered pot standing on the floor, lit from the left, with a dark soil top."""
    hi, mid, lo, dark = colours
    for y in range(floor_y - h, floor_y + 1):
        w = half - (y - (floor_y - h)) * 2 // max(h, 1) // 2
        for x in range(cx - w, cx + w + 1):
            c.px(x, y, hi if x < cx - w + 2 else (mid if x < cx + 1 else lo))
    if rim:
        for x in range(cx - half - 1, cx + half + 2):
            c.px(x, floor_y - h, hi)
    disc(c, cx, floor_y - h, half - 0.5, 1.2, lambda dx, dy: "choc0")


def fiddle_leaf_fig():
    """Tall fiddle-leaf fig in a big pot: a thin trunk and big glossy leaves."""
    import math, random
    rng = random.Random(21)
    c = Canvas(50, 100)
    cx, floor_y = 25, 92
    pot(c, cx, floor_y, 7, 12)
    for y in range(floor_y - 52, floor_y - 12):
        c.px(cx + (1 if y < floor_y - 34 else 0), y, "wood1")
    for _ in range(16):  # big leaves, each a small lit oval
        y = rng.randint(floor_y - 76, floor_y - 30)
        side = rng.choice([-1, 1])
        x = cx + side * rng.randint(2, 8)
        disc(c, x, y, 3.2, 2.4, lambda dx, dy: "leaf3" if dx + dy < -0.9 else ("sage2" if dx + dy < 0 else ("sage1" if dx + dy < 0.9 else "sage0")))
        c.px(x, y, "leaf0")
    return save(c, "fiddle-leaf-fig", foot=(cx, floor_y), size=(4, 4), centre=True)


def snake_plant():
    """Snake plant: stiff upright striped leaves in a cream pot."""
    import random
    rng = random.Random(8)
    c = Canvas(40, 60)
    cx, floor_y = 20, 52
    pot(c, cx, floor_y, 5, 9, colours=("key2", "key1", "key0", "silver0"))
    for k, (dx, h) in enumerate(((-4, 16), (-2, 24), (0, 20), (2, 27), (4, 17), (-1, 13), (3, 12))):
        lean = rng.choice([-1, 0, 1])
        for y in range(h):
            x = cx + dx + (lean * y) // 10
            yy = floor_y - 10 - y
            col = "sage0" if (y // 3) % 2 else "sage1"
            if y > h - 3:
                col = "leaf3"
            c.px(x, yy, col)
            c.px(x + 1, yy, "olive2" if y < h - 2 else col)
    return save(c, "snake-plant", foot=(cx, floor_y), size=(4, 4), centre=True)


def fern_stand():
    """Boston fern spilling over a tall wooden plant stand."""
    import math, random
    rng = random.Random(14)
    c = Canvas(50, 70)
    cx, floor_y = 25, 62
    for dx in (-4, 4):  # stand legs
        vline(c, cx + dx, floor_y - 20, floor_y, "wood2")
    for x in range(cx - 5, cx + 6):
        c.px(x, floor_y - 20, "wood4"); c.px(x, floor_y - 19, "wood3")
        c.px(x, floor_y - 6, "wood2")
    pot(c, cx, floor_y - 21, 4, 6)
    for _ in range(110):  # arching fronds
        a = rng.uniform(math.pi * 0.95, math.pi * 2.05)
        r = rng.uniform(4, 13)
        x = round(cx + math.cos(a) * r)
        y = round(floor_y - 30 - math.sin(a) * r * 0.6 + (r * 0.45 if abs(math.cos(a)) > 0.6 else 0))
        c.px(x, y, rng.choice(["sage2", "sage1", "leaf3", "sage1"]))
        c.px(x + 1, y, rng.choice(["sage1", "sage0"]))
    return save(c, "fern-stand", foot=(cx, floor_y), size=(4, 4), centre=True)


def succulent():
    """Little succulent in a terracotta pot, for tables, shelves and the counter."""
    c = Canvas(20, 20)
    cx, base = 10, 15
    for y in range(base - 4, base + 1):
        for x in range(cx - 3, cx + 4):
            c.px(x, y, "terra3" if x < cx - 1 else ("terra2" if x < cx + 2 else "terra1"))
    for dx, dy, col in ((0, -6, "leaf3"), (-2, -5, "sage2"), (2, -5, "sage1"), (-3, -5, "sage1"), (3, -5, "sage0"), (-1, -7, "sage2"), (1, -7, "sage1"), (0, -8, "leaf3"), (-1, -5, "sage2"), (1, -5, "sage1")):
        c.px(cx + dx, base + dy, col)
    return save(c, "succulent")


def tulip_pot():
    """A pot of tulips, pink and yellow, like the original's flowers."""
    c = Canvas(30, 40)
    cx, floor_y = 15, 34
    pot(c, cx, floor_y, 5, 8)
    for k, (dx, h, col) in enumerate(((-4, 13, "pink1"), (-1, 17, "gold2"), (2, 15, "pink2"), (4, 12, "gold2"), (0, 11, "pink1"))):
        x = cx + dx
        vline(c, x, floor_y - 8 - h, floor_y - 9, "sage1")
        top = floor_y - 9 - h
        for yy, ww in ((top - 3, 1), (top - 2, 1), (top - 1, 1)):
            c.px(x - 1, yy, col); c.px(x, yy, col); c.px(x + 1, yy, "pink0" if col.startswith("pink") else "gold1")
        c.px(x - 2, top + 4, "sage2"); c.px(x + 2, top + 6, "sage1")
    return save(c, "tulip-pot", foot=(cx, floor_y), size=(4, 4), centre=True)


def window_box():
    """Herb planter for a window sill or a wall: a wood box of basil and rosemary.
    For the back-right wall (flip for the other one)."""
    import random
    rng = random.Random(6)
    c = Canvas(60, 40)
    X0, Y0 = 8, 28
    L, D, H = 12, 3, 6
    face_left(c, X0, Y0, 0, L, D, 0, H, lambda t, z: "wood3" if z >= H - 1 else ("wood2" if t % 3 > 0.3 else "wood1"))
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "wood1")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "choc0")
    for k in range(34):
        t, b = rng.uniform(0.6, L - 0.6), rng.uniform(0.4, D - 0.4)
        x, y = round(X0 + 2 * t - 2 * b), round(Y0 + t + b - H - rng.randint(1, 6))
        leaf_cluster(c, x, y, rng)
    return save(c, "window-box", foot=(X0, Y0))


# ---------------------------------------------------------------- couch and menu board


def couch(back=False, name="couch", L=16, seats=3, R=("rust0", "rust1", "rust2", "rust3", "rust4")):
    """Velvet couch on little wooden feet, facing down-left: `seats` cushions over `L` units, in
    the colours R (dark to light). back=True draws it from behind (for Rotate)."""
    c = Canvas(150, 100)
    X0, Y0 = 26, 40
    D = 8
    BASE, SEAT, ARM, BACK = 3, 10, 16, 26
    BK, AW = 2.5, 1.6
    for (a_, b_) in ((0.6, D - 0.4), (L - 0.4, D - 0.4), (L - 0.4, 0.6), (L / 2, D - 0.4)):
        x, y = X0 + 2 * a_ - 2 * b_, Y0 + a_ + b_
        vline(c, x, y - BASE, y, "wood1"); vline(c, x + 1, y - BASE, y, "wood0")
    if not back:
        face_left(c, X0, Y0, 0, L, D, BASE, SEAT, lambda t, z: R[1] if z < SEAT - BASE - 1 else R[2])
        face_right(c, X0, Y0, L, 0, D, BASE, SEAT, lambda s_, z: R[0])
        face_left(c, X0, Y0, 0, L, BK, SEAT, BACK, lambda t, z: R[4] if z >= BACK - SEAT - 2 else (R[1] if (t - AW) % ((L - 2 * AW) / seats) < 0.3 else R[2]))
        face_right(c, X0, Y0, L, 0, BK, SEAT, BACK, lambda s_, z: R[1] if z >= BACK - SEAT - 1 else R[0])
        face_top(c, X0, Y0, 0, L, 0, BK, BACK, lambda a_, b_: R[3])

        def arm(a0):
            face_left(c, X0, Y0, a0, a0 + AW, D, SEAT, ARM, lambda t, z: R[4] if z >= ARM - SEAT - 1 else R[3])
            face_right(c, X0, Y0, a0 + AW, BK, D, SEAT, ARM, lambda s_, z: R[1] if z >= ARM - SEAT - 1 else R[0])
            face_top(c, X0, Y0, a0, a0 + AW, BK, D, ARM, lambda a_, b_: R[4] if b_ > D - 0.8 else R[3])
        arm(0)
        cw = (L - 2 * AW) / seats
        for k in range(seats):  # seat cushions
            a0 = AW + k * cw
            face_left(c, X0, Y0, a0, a0 + cw, D, SEAT, SEAT + 3, lambda t, z: R[1] if (t < 0.25 or t > cw - 0.25) else (R[2] if z < 2 else R[3]))
            face_top(c, X0, Y0, a0, a0 + cw, BK, D, SEAT + 3, lambda a_, b_: R[1] if (a_ < 0.25) else (R[4] if b_ > D - 1 else R[3]))
        arm(L - AW)
    else:
        for a0 in (0, L - AW):
            face_top(c, X0, Y0, a0, a0 + AW, 0, D - BK, ARM, lambda a_, b_: R[3])
            face_right(c, X0, Y0, a0 + AW, 0, D - BK, SEAT, ARM, lambda s_, z: R[1])
        face_right(c, X0, Y0, L, 0, D, BASE, ARM, lambda s_, z: R[0] if z < ARM - BASE - 1 else R[1])
        face_left(c, X0, Y0, 0, L, D, BASE, BACK, lambda t, z: R[3] if z >= BACK - BASE - 2 else (R[1] if (t < 0.4 or t > L - 0.4 or z < 2) else R[2]))
        face_right(c, X0, Y0, L, D - BK, D, BASE, BACK, lambda s_, z: R[1] if z >= BACK - BASE - 1 else R[0])
        face_top(c, X0, Y0, 0, L, D - BK, D, BACK, lambda a_, b_: R[3])
    return save(c, name + "-back" if back else name, foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def coffee_table():
    """Low wooden coffee table with a lower shelf of books, 2 x 1 tiles."""
    c = Canvas(90, 60)
    X0, Y0 = 22, 24
    L, D, H = 16, 8, 9
    for (a_, b_) in ((0.5, D - 0.5), (L - 0.5, D - 0.5), (L - 0.5, 0.5)):  # legs
        x, y = X0 + 2 * a_ - 2 * b_, Y0 + a_ + b_
        vline(c, x, y - H, y, "wood2"); vline(c, x + 1, y - H, y, "wood1")
    # lower shelf with a couple of books
    face_top(c, X0, Y0, 0.5, L - 0.5, 0.5, D - 0.5, 2, lambda a, b: "wood2")
    for t0, t1, col in ((3, 6, "navy1"), (3.3, 5.6, "red2"), (10, 13, "sage1")):
        face_top(c, X0, Y0, t0, t1, 2.5, 5.5, 3 if col != "red2" else 4, lambda a, b, col=col: col)
    # the top: a thick slab with a lit edge
    face_left(c, X0, Y0, 0, L, D, H - 2, H, lambda t, z: "wood4" if z >= 1 else "wood3")
    face_right(c, X0, Y0, L, 0, D, H - 2, H, lambda s_, z: "wood2")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood5" if (b > D - 0.6 or a > L - 0.6) else ("wood5" if abs(a - b * 1.4 - 3) < 0.5 else "wood4"))
    return save(c, "coffee-table", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def booth_table():
    """Table to set in front of a booth: as long as the booth (2 tiles), half a tile deep,
    a thick wood top on a centre pedestal and a cross foot, café-table height."""
    c = Canvas(90, 70)
    X0, Y0 = 22, 34
    L, D, H = 16, 4, 20
    mid = lambda a, b, z: (round(X0 + 2 * a - 2 * b), round(Y0 + a + b - z))
    # cross foot and the pedestal
    for k in range(-5, 6):
        x, y = mid(L / 2 + k * 0.5, D / 2, 0)
        c.px(x, y, "iron"); c.px(x + 1, y, "iron")
    for k in range(-3, 4):
        x, y = mid(L / 2, D / 2 + k * 0.5, 0)
        c.px(x, y, "iron")
    x, y = mid(L / 2, D / 2, 0)
    vline(c, x, y - H + 2, y - 1, "wood1"); vline(c, x + 1, y - H + 2, y - 1, "wood0")
    # top: thick slab with a lit front edge and a sheen
    face_left(c, X0, Y0, 0, L, D, H - 3, H, lambda t, z: "wood4" if z >= 2 else "wood2")
    face_right(c, X0, Y0, L, 0, D, H - 3, H, lambda s_, z: "wood2" if z >= 2 else "wood1")
    face_top(c, X0, Y0, 0, L, 0, D, H, lambda a, b: "wood5" if (b > D - 0.6 or a > L - 0.6) else ("wood5" if abs(a - b * 2.5 - 4) < 0.5 else "wood4"))
    return save(c, "booth-table", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


def menu_board():
    """Large chalkboard menu for the wall, in a wood frame: a heading, three sections of items
    with prices, a coffee cup and a croissant drawn in chalk. For the back-right wall."""
    c = Canvas(90, 110)
    X0, Y0 = 10, 96
    L, Z0, Z1, F = 22, 30, 78, 1.2  # width (units), bottom/top height (px), frame (units)
    FZ = 3  # frame thickness (px)

    def board(t, zr):
        z = zr + Z0  # face_left hands over the height above the face's bottom
        if t < F or t > L - F or z < Z0 + FZ or z >= Z1 - FZ:
            return "wood4" if (t < 0.4 or z >= Z1 - 1) else ("wood2" if z < Z0 + 1 else "wood3")
        u = (t - F) / (L - 2 * F)  # 0..1 across
        v = (Z1 - FZ - z) / (Z1 - Z0 - 2 * FZ)  # 0..1 down
        if v < 0.13:  # heading: four chunky chalk letters
            return "chalk" if (0.25 < u < 0.75 and int(u * 24) % 3 != 2 and v > 0.04) else "slate1"
        if 0.16 < v < 0.18 and 0.1 < u < 0.9:
            return "silver0"  # rule under the heading
        for top, n in ((0.24, 3), (0.5, 3), (0.76, 2)):
            if abs(v - top) < 0.022 and 0.08 < u < 0.42:
                return "gold2"  # section title
            for k in range(n):
                row = top + 0.06 + k * 0.055
                if abs(v - row) < 0.015:
                    if 0.08 < u < 0.08 + 0.28 + (k % 2) * 0.08 and int(u * 40) % 5 != 4:
                        return "chalk"  # item
                    if 0.6 < u < 0.66 or 0.68 < u < 0.72:
                        return "chalk"  # price
                    if 0.45 < u < 0.58 and int(u * 60) % 2 == 0:
                        return "silver0"  # dots
        # chalk doodles on the right: a coffee cup and a croissant
        if 0.78 < u < 0.92 and 0.26 < v < 0.36:
            return "chalk" if (u < 0.8 or u > 0.9 or v > 0.34) else "slate1"
        if 0.76 < u < 0.94 and 0.58 < v < 0.66 and abs(u - 0.85) < 0.09 - abs(v - 0.62) * 1.2:
            return "gold2"
        return "slate1" if (u * 3 + v * 2) % 1 > 0.06 else "slate0"
    face_left(c, X0, Y0, 0, L, 0, Z0, Z1, board)
    face_right(c, X0, Y0, L, 0, 0.8, Z0, Z1, lambda s_, z: "wood2")  # frame edge standing off the wall
    face_top(c, X0, Y0, 0, L, 0, 0.8, Z1, lambda a, b: "wood4")
    # a chalk ledge along the bottom with a stub of chalk
    face_top(c, X0, Y0, 0, L, 0, 1.4, Z0, lambda a, b: "wood4" if not (4 < a < 5) else "chalk")
    face_left(c, X0, Y0, 0, L, 1.4, Z0 - 1, Z0, lambda t, z: "wood2")
    return save(c, "menu-board", foot=(X0, Y0 - Z0 + 1))


def wardrobe(back=False):
    """A tall wooden armoire where visitors change their look: crown on top, two drawers at the
    bottom; the left door shut with an oval mirror, the right door swung open toward you
    showing a rail of jackets in the café people's colours. Faces down-left.
    back=True draws it from behind (for Rotate)."""
    c = Canvas(90, 130)
    X0, Y0 = 22, 92
    L, D, H = 12, 6, 64
    DR = 14  # drawer section height
    jackets = [(110, 104, 66), (150, 66, 40), (40, 96, 96), (84, 110, 150), (176, 136, 56), (90, 44, 66), (112, 40, 40)]
    if back:
        face_left(c, X0, Y0, 0, L, D, 0, H, lambda t, z: "wood3" if z >= H - 3 else ("wood1" if z < 2 else wood_back(t, z, 3)))
        face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "wood1" if z < H - 1 else "wood2")
        face_top(c, X0, Y0, -0.4, L + 0.4, -0.4, D + 0.4, H, lambda a, b: "wood5" if b > D - 0.2 else "wood4")
        return save(c, "wardrobe-back", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))

    half = L / 2

    def front(t, z):
        if z < 2:
            return "wood0"  # plinth shadow
        if z >= H - 4:
            return "wood4" if z >= H - 2 else "wood3"  # crown
        if z < DR:  # two drawers with brass pulls
            if z in (2, DR - 1) or t < 0.5 or t > L - 0.5 or abs(t - half) < 0.25:
                return "wood1"
            if z == DR // 2 + 1 and (abs(t - half / 2) < 0.6 or abs(t - half * 1.5) < 0.6):
                return "brass2"
            return "wood3" if z == DR - 2 else "wood2"
        if t >= half:  # the open side: inside of the cabinet with a rail of jackets
            if t > L - 0.5 or z >= H - 5:
                return "wood1"
            if z == H - 8:
                return "brass1"  # the rail
            k = int((t - half - 0.3) / 0.85)
            if 0 <= k < len(jackets) and DR + 6 <= z < H - 8:
                if z == H - 9 and (t - half - 0.3) % 0.85 < 0.3:
                    return "brass0"  # hanger hook
                base = jackets[k]
                lit = (t - half - 0.3) % 0.85 < 0.28
                return tuple(min(255, int(v * (1.25 if lit else 1.0))) for v in base) + (255,)
            return "wood0"
        # the shut left door: framed, with an oval mirror
        if t < 0.5 or abs(t - half) < 0.4 or z in (DR, DR + 1):
            return "wood3" if t < 0.3 else "wood2"
        u = (t - half / 2) / (half / 2 - 0.9)
        v = (z - (DR + H - 4) / 2) / ((H - 4 - DR) / 2 - 3)
        if u * u + v * v <= 1:
            if u * u + v * v > 0.8:
                return "brass1"  # mirror frame
            g = (u + v * 0.6)
            return "shine" if abs(g + 0.4) < 0.12 else ("glass2" if g < 0 else "glass1")
        if abs(t - (half - 0.8)) < 0.25 and abs(z - (DR + 22)) < 2:
            return "brass2"  # handle
        return "wood2"

    face_left(c, X0, Y0, 0, L, D, 0, H, front)
    face_right(c, X0, Y0, L, 0, D, 0, H, lambda s_, z: "wood1" if z < H - 2 else "wood2")
    face_top(c, X0, Y0, -0.4, L + 0.4, -0.4, D + 0.4, H, lambda a, b: "wood5" if b > D - 0.2 else "wood4")
    # the open right door, folded right back against the cabinet's side so the jackets show
    face_right(c, X0, Y0, L + 0.4, D - half + 0.6, D, DR + 1, H - 4,
               lambda s_, z: "wood1" if (s_ < 0.4 or s_ > half - 1.1 or z < 1 or z > H - DR - 7) else ("wood3" if s_ > half - 1.8 else "wood2"))
    return save(c, "wardrobe", foot=(X0 + 2 * L - 2 * D, Y0 + L + D), size=(L, D))


ALL = [cafe_table, table_cloth("cafe-table-cloth", "red1", "red2", "gold1", "key1"),
       table_cloth("cafe-table-linen", "key1", "key0", "red2", "key2"), cafe_chair, piano, piano_stool, globe_lamp, wall_lamp,
       bookshelf, window, hanging_plant, potted_plant, flower_vase,
       rug, booth, armchair, floor_lamp, special_board, coffee_cup, laptop, cake_stand, record_cabinet, back_bar_shelves, bar_counter, espresso_station, cafe_chair_back,
       piano_back, bookshelf_back, armchair_back, booth_back, bar_counter_back, record_cabinet_back,
       espresso_station_back, laptop_back,
       fiddle_leaf_fig, snake_plant, fern_stand, succulent, tulip_pot, window_box,
       couch, lambda: couch(back=True), menu_board, wardrobe, lambda: wardrobe(back=True), coffee_table, booth_table,
       lambda: couch(name="sofa-large", L=24, seats=4, R=("olive0", "olive1", "olive2", "olive3", "leaf3")),
       lambda: couch(back=True, name="sofa-large", L=24, seats=4, R=("olive0", "olive1", "olive2", "olive3", "leaf3"))]

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

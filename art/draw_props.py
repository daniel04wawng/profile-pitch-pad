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

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")

# extra tones from the original: the red rug, navy trim, warm whites
P = COZY
for k, v in {
    "red0": "#4a1012", "red1": "#7a1f1f", "red2": "#a8352a", "red3": "#c95a3a",
    "navy0": "#1b2040", "navy1": "#2c3463", "navy2": "#46508a",
    "iron": "#24170f", "key0": "#c9b28c", "key1": "#f3e6c8", "key2": "#fff8e6",
}.items():
    P[k] = tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,)


def save(c, name):
    c.outline()
    im = c.im.crop(c.im.getbbox())
    im.save(os.path.join(OUT, f"{name}.png"))
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
    return save(c, "cafe-table")


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
    return save(c, "cafe-chair")


# ---------------------------------------------------------------- the piano corner


def piano():
    """Upright piano in dark warm wood, keyboard facing down-left, a brass lamp on top."""
    c = Canvas(120, 110)
    X0, Y0 = 20, 40
    L, D = 16, 5  # length along the keyboard, depth (units: 2px across, 1px down)
    KB, TOP = 16, 36  # keyboard height and body height (px)

    def panel(t, z, lo, hi):
        if z <= lo or z >= hi - 1:
            return "wood1"
        k = t % (L / 3)
        return "wood1" if k < 0.4 else ("wood3" if k < 0.8 else "wood2")

    # body: right end, then the recessed lower front, legs, keyboard, upper front, lid
    face_right(c, X0, Y0, L, 0, D + 3, 0, KB + 3, lambda s, z: "wood1" if s < D else "wood2")
    face_right(c, X0, Y0, L, 0, D, KB + 3, TOP, lambda s, z: "wood1" if z < TOP - 2 else "wood2")
    face_left(c, X0, Y0, 0, L, D, 1, KB, lambda t, z: "wood0" if z < 2 else panel(t, z, 2, KB))
    for a0 in (0.3, L - 1.3):  # front legs under the keyboard
        face_left(c, X0, Y0, a0, a0 + 1, D + 3, 0, KB, lambda t, z: "wood2" if t < 0.5 else "wood1")
        face_right(c, X0, Y0, a0 + 1, D, D + 3, 0, KB, lambda s, z: "wood0")
    # pedals
    for a in (L / 2 - 1, L / 2, L / 2 + 1):
        x, y = c and (X0 + 2 * a - 2 * (D + 1), Y0 + a + D + 1 - 1)
        c.px(x, y, "brass2"); c.px(x + 1, y, "brass1")
    face_left(c, X0, Y0, 0, L, D + 3, KB, KB + 3, lambda t, z: "wood2" if z < 2 else "wood3")  # key slip
    # keys: whites with groups of blacks toward the back
    def keys(a, b):
        if b < 0.5:
            return "wood0"  # shadow under the fallboard
        black = b < 1.9 and (int(a * 3.5) % 7) in (1, 2, 4, 5, 6) and (a * 3.5) % 1 < 0.6
        if black:
            return "iron"
        return "key2" if b > 2.4 else ("key1" if (a * 3.5) % 1 > 0.15 else "key0")
    face_top(c, X0, Y0, 0.3, L - 0.3, D, D + 3, KB + 3, keys)
    face_left(c, X0, Y0, 0, L, D, KB + 3, TOP, lambda t, z: (
        "key1" if (L / 2 - 1.6 < t < L / 2 + 1.6 and 6 < z < 12 and not (int(z) == 9 and t % 1 < 0.5)) else
        ("wood1" if z in (KB + 3, TOP - 1) else panel(t, z, 0, TOP - KB - 3))))
    face_top(c, X0, Y0, 0, L, 0, D, TOP, lambda a, b: "wood5" if b > D - 0.6 else ("wood4" if a < L - 0.6 else "wood3"))
    # brass lamp on the lid
    lx, ly = X0 + 2 * (L * 0.62) - 2 * (D / 2), Y0 + L * 0.62 + D / 2 - TOP
    vline(c, lx, ly - 5, ly, "brass1")
    for dx in range(-4, 4):
        c.px(lx + dx, ly - 6 - dx // 3, "brass2")
        c.px(lx + dx, ly - 5 - dx // 3, "gold3" if -2 <= dx <= 1 else "brass1")
    c.px(lx - 1, ly, "brass0"); c.px(lx + 1, ly, "brass0")
    darker(c, {"wood1": "wood0", "wood2": "wood1", "wood3": "wood2", "wood4": "wood3", "wood5": "wood4"})  # polished dark wood
    return save(c, "piano")


def piano_stool():
    c = Canvas(40, 40)
    cx, floor_y, h = 20, 32, 10
    sy = floor_y - h
    for x0, x1, col in ((cx - 3, cx - 4, "wood1"), (cx + 3, cx + 4, "wood0"), (cx, cx, "wood0")):
        for y in range(sy + 2, floor_y + 1):
            t = (y - sy) / h
            c.px(round(x0 + (x1 - x0) * t), y, col)
    disc(c, cx, sy + 1.5, 6, 3, lambda dx, dy: "wood1")
    disc(c, cx, sy, 6, 3, lambda dx, dy: "red3" if dx + dy < -0.6 else "red2")  # padded top
    return save(c, "piano-stool")


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
        return save(c, name)
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


ALL = [cafe_table, table_cloth("cafe-table-cloth", "red1", "red2", "gold1", "key1"),
       table_cloth("cafe-table-linen", "key1", "key0", "red2", "key2"), cafe_chair, piano, piano_stool, globe_lamp, wall_lamp]

GLOWS = {"wall-lamp": {"x": 10, "y": 4, "r": 60}, "globe-lamp": {"x": 7, "y": 38, "r": 80}}


def write_glows():
    import json
    path = os.path.join(OUT, "_companions.json")
    comp = json.load(open(path)) if os.path.exists(path) else {}
    for name, g in GLOWS.items():
        comp[name] = {**comp.get(name, {}), "glow": g}
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

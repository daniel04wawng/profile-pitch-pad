"""Cozy café assets: the original café's pieces, redrawn clean as standalone objects.

Each piece follows its original (art/archive/old-cafe/) for shape, colors and details, but is
drawn fresh: one object, complete silhouette, no floor, no stray pixels. Warm, dark wood and
golden light like the original; 2:1 isometric on the editor's grid.

    python3 art/draw_cozy.py --preview   # writes public/cafe/sprites/cozy-*.png
"""
import os
import random
import sys

from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")

# Palette sampled from the original café: deep warm woods, golden light, cream, brass.
PALETTE = {
    "line": "#24140d",
    "wood0": "#3b2418", "wood1": "#523020", "wood2": "#6e4128", "wood3": "#8f5733", "wood4": "#b0743f", "wood5": "#cf9554",
    "gold0": "#b9782f", "gold1": "#e3a24a", "gold2": "#f4c873", "gold3": "#ffe6a8",
    "cream0": "#d9b98a", "cream1": "#efd7ad", "cream2": "#fbeed2",
    "pink0": "#a5485a", "pink1": "#e0899a", "pink2": "#f5bfc6",
    "berry": "#6a2b45", "choc0": "#3d2117", "choc1": "#5e3324",
    "glass0": "#6f8f8c", "glass1": "#9fbcb5", "glass2": "#cfe3d9", "shine": "#fff6e0",
    "brass0": "#8a5f22", "brass1": "#c9963f", "brass2": "#f0c66c",
    "sage0": "#3e5434", "sage1": "#5d7a48", "sage2": "#86a463",
}
P = {k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in PALETTE.items()}


class Canvas:
    def __init__(self, w=220, h=200):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.w, self.h = w, h

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((x, y), P[c] if isinstance(c, str) else c)

    def poly(self, pts, c):
        self.d.polygon([(round(x), round(y)) for x, y in pts], fill=P[c])

    def outline(self, c="line"):
        src = self.im.copy()
        a = src.getchannel("A").load()
        for y in range(self.h):
            for x in range(self.w):
                if not a[x, y] and any(0 <= x + dx < self.w and 0 <= y + dy < self.h and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.im.putpixel((x, y), P[c])

    def save(self, name):
        bb = self.im.getbbox()
        out = self.im.crop(bb)
        out.save(os.path.join(OUT, f"cozy-{name}.png"))
        return out


# Isometric helpers. Floor coords (a, b) in units (1 unit = 2px across, 1px down);
# a runs down-right, b runs down-left, z is height in px.
def P2(X0, Y0, a, b, z=0):
    return (X0 + 2 * a - 2 * b, Y0 + a + b - z)


def _scan(c, color_fn, solve):
    """Fill every canvas pixel whose face coordinates `solve(x, y)` land inside the face."""
    for y in range(c.h):
        for x in range(c.w):
            r = solve(x + 0.5, y + 0.5)
            if r is None:
                continue
            col = color_fn(*r)
            if col:
                c.px(x, y, col)


def face_left(c, X0, Y0, a0, a1, b, z0, z1, color_fn):
    """The face looking down-left (constant b). color_fn(t, z): t along it, z up from its bottom."""
    def solve(x, y):
        a = (x - X0 + 2 * b) / 2
        z = Y0 + a + b - y
        if a0 <= a < a1 and z0 <= z < z1:
            return (a - a0, z - z0)
    _scan(c, color_fn, solve)


def face_right(c, X0, Y0, a, b0, b1, z0, z1, color_fn):
    """The face looking down-right (constant a). color_fn(s, z)."""
    def solve(x, y):
        s = (X0 + 2 * a - x) / 2
        z = Y0 + a + s - y
        if b0 <= s < b1 and z0 <= z < z1:
            return (s - b0, z - z0)
    _scan(c, color_fn, solve)


def face_top(c, X0, Y0, a0, a1, b0, b1, z, color_fn):
    """A horizontal face at height z. color_fn(a, b) relative to its corner."""
    def solve(x, y):
        u = (x - X0) / 2
        v = y - Y0 + z
        a = (u + v) / 2
        b = (v - u) / 2
        if a0 <= a < a1 and b0 <= b < b1:
            return (a - a0, b - b0)
    _scan(c, color_fn, solve)


# ---------------------------------------------------------------- the pastry counter


def pastry_counter():
    """Long wooden counter with a lit glass display of pastries, like the original's."""
    c = Canvas()
    X0, Y0 = 40, 70
    L, D = 36, 9  # length along the counter (units), depth
    BASE, CASE = 22, 20  # wood base height, glass case height (px)
    GL = L - 4  # the glass case covers this much; the rest is plain counter top
    rng = random.Random(11)
    kinds = [
        ("gold1", "gold2", "gold0"), ("pink1", "pink2", "pink0"), ("choc1", "wood4", "choc0"),
        ("cream1", "cream2", "cream0"), ("gold2", "gold3", "gold1"), ("berry", "pink1", "choc0"),
    ]

    # ---- wood base: framed panels, lit top edge, darker toward the floor
    def base_front(t, z):
        if z < 2:
            return "wood0"
        if z >= BASE - 2:
            return "wood5" if z >= BASE - 1 else "wood4"
        k = t % 6
        if k < 0.5 or z in (3, BASE - 4):
            return "wood1"  # panel frame grooves
        if k < 1.0:
            return "wood3"  # lit edge
        return "wood2" if z > BASE / 2 else "wood1"

    face_left(c, X0, Y0, 0, L, D, 0, BASE, base_front)
    face_right(c, X0, Y0, L, 0, D, 0, BASE, lambda s, z: "wood2" if z >= BASE - 2 else ("wood1" if z > 2 else "wood0"))

    # ---- inside the case: fill it with warm light first so no gaps show through the glass
    face_left(c, X0, Y0, 0, GL, D, BASE, BASE + CASE, lambda t, z: "gold1" if z < CASE - 6 else "gold0")
    face_top(c, X0, Y0, 0, GL, 0, D, BASE + CASE, lambda a, b: "gold0")
    face_left(c, X0, Y0, 0, GL, 0.5, BASE, BASE + CASE, lambda t, z: "gold0" if z < CASE - 3 else "wood2")  # back wall
    face_right(c, X0, Y0, GL, 1, D, BASE, BASE + CASE, lambda s, z: "gold0")  # inside of the far end
    rows = []
    for shelf_z, depth in ((BASE + 1, D - 1.2), (BASE + 10, D - 3.2)):
        face_top(c, X0, Y0, 0, GL, depth - 3, depth, shelf_z, lambda a, b: "gold2" if b > 2.2 else "gold1")  # lit shelf
        for row_off in (2.0, 0.6):  # a back row and a front row on every shelf
            t = 0.5 + rng.random()
            while t < GL - 2:
                body, top, shade = kinds[rng.randrange(len(kinds))]
                w = rng.choice([2, 2, 2.5, 3])
                h = rng.choice([4, 4, 5, 6])
                rows.append((t, depth - row_off, shelf_z, w, h, body, top, shade))
                t += w + rng.choice([0.2, 0.3, 0.5])
    for (t, depth, shelf_z, w, h, body, top, shade) in rows:
        face_left(c, X0, Y0, t, t + w, depth, shelf_z, shelf_z + h,
                  lambda tt, z, body=body, top=top, shade=shade, w=w, h=h: top if z >= h - 1 else (shade if (tt < 0.5 or tt > w - 0.6 or z < 1) else body))
        face_top(c, X0, Y0, t, t + w, depth - 1, depth, shelf_z + h, lambda a, b, top=top: top)
        gx, gy = P2(X0, Y0, t + 0.6, depth, shelf_z + h - 1)
        c.px(gx, gy, "shine")

    # ---- glass: front pane mostly clear with warm diagonal glints; slim top pane
    face_left(c, X0, Y0, 0, GL, D, BASE, BASE + CASE,
              lambda t, z: "shine" if (z - t * 1.1) % 26 < 1 else ("glass2" if (z - t * 1.1) % 26 < 2 else None))
    face_top(c, X0, Y0, 0, GL, 0, D, BASE + CASE,
             lambda a, b: "glass2" if (a + b * 0.5) % 16 < 1 else None)
    # brass frame: top edges, bottom rail, corner posts
    for t2 in range(int(GL * 2) + 1):
        tt = t2 / 2
        for z, col in ((BASE + CASE, "brass2"), (BASE, "brass1")):
            x, y = P2(X0, Y0, tt, D, z)
            c.px(x, y, col); c.px(x + 1, y, col)
        x, y = P2(X0, Y0, tt, 0, BASE + CASE)
        c.px(x, y, "brass1"); c.px(x + 1, y, "brass1")
    for s2 in range(int(D * 2) + 1):
        x, y = P2(X0, Y0, GL, s2 / 2, BASE + CASE)
        c.px(x, y, "brass2"); c.px(x + 1, y, "brass2")
        x, y = P2(X0, Y0, 0, s2 / 2, BASE + CASE)
        c.px(x, y, "brass1")
    for (a, b) in ((0, D), (GL, D)):
        x, y = P2(X0, Y0, a, b, BASE)
        for z in range(CASE):
            c.px(x, y - z, "brass1")
    # far-end glass pane (curved in the original): a lighter column with a highlight
    face_right(c, X0, Y0, GL, 0, D, BASE, BASE + CASE, lambda s, z: "shine" if abs(s - z * 0.35) < 0.4 else None)

    # ---- plain counter top past the case, with a little cake dome
    face_top(c, X0, Y0, GL, L, 0, D, BASE, lambda a, b: "wood5" if (a < 0.5 or b > D - 0.6) else "wood4")
    dx, dy = P2(X0, Y0, GL + 2, D / 2, BASE)
    c.d.ellipse([dx - 4, dy - 3, dx + 4, dy + 1], fill=P["cream1"])  # plate
    c.d.ellipse([dx - 3, dy - 6, dx + 3, dy - 1], fill=P["pink1"])  # cake
    c.d.rectangle([dx - 3, dy - 4, dx + 3, dy - 2], fill=P["pink0"])
    c.d.ellipse([dx - 3, dy - 8, dx + 3, dy - 4], fill=P["pink2"])
    c.px(dx - 1, dy - 7, "shine")
    c.outline()
    return c.save("pastry-counter")


ALL = [pastry_counter]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    imgs = [f() for f in ALL]
    print(f"{len(imgs)} cozy assets -> {OUT}")
    if "--preview" in sys.argv:
        os.makedirs(os.path.join(ART, "preview"), exist_ok=True)
        pad = 10
        W = sum(i.width + pad for i in imgs) + pad
        H = max(i.height for i in imgs) + pad * 2
        sheet = Image.new("RGBA", (W, H), (58, 42, 34, 255))
        x = pad
        for i in imgs:
            sheet.alpha_composite(i, (x, H - pad - i.height))
            x += i.width + pad
        sheet.resize((W * 5, H * 5), Image.NEAREST).save(os.path.join(ART, "preview", "cozy-sheet.png"))

"""Isometric pixel-art café assets (2:1 iso, dollhouse room view), drawn in code.

Conventions
- 2:1 isometric: every diagonal edge steps 2px across for 1px down. Floor tile = 32x16px.
- Light from the top-left: top faces lightest, left faces mid, right faces darkest.
- 1px dark outline around each sprite; shared PALETTE so everything matches.
- Objects are drawn facing down-left (their front is the left face, like furniture standing
  against the room's back-right wall). Flip (F) in the editor to face the other wall.

    python3 art/draw_iso.py            # writes public/cafe/sprites/iso-<name>.png
    python3 art/draw_iso.py --preview  # also writes art/preview/iso-sheet.png
"""
import os
import random
import sys

from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")

PALETTE = {
    "ink": "#2b1d1a",
    "wood0": "#4a2f25", "wood1": "#6b4232", "wood2": "#8f5b3e", "wood3": "#b47a4f", "wood4": "#d29f6b",
    "cream0": "#c9b18a", "cream1": "#e2cfa8", "cream2": "#f3e6c9", "white": "#fdf8ef",
    "sage0": "#3f5a3a", "sage1": "#5f8251", "sage2": "#86a86b", "sage3": "#b5cf8f",
    "terra0": "#a3523a", "terra1": "#cf7a56", "terra2": "#eaa37f",
    "gold0": "#c98f3c", "gold1": "#e8b45c", "gold2": "#f6d58a",
    "pink0": "#9b3b52", "pink1": "#e89aa8", "pink2": "#f4c6cc",
    "blue0": "#3c5878", "blue1": "#6488aa", "blue2": "#9dbad3",
    "steel0": "#3b3f4a", "steel1": "#6d7380", "steel2": "#a9afba", "steel3": "#d9dde3",
    "glass0": "#9fcbd3", "glass1": "#d6eef1",
    "keyblack": "#1c1717",
}
P = {k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in PALETTE.items()}


class Iso:
    """A sprite canvas with isometric drawing helpers.

    Coordinates for boxes use the top face's back corner (ox, oy). `a` runs down-right
    (2px across, 1 down per unit), `b` runs down-left, `h` is height in px.
    """

    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.w, self.h = w, h

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((int(x), int(y)), P[c])

    def poly(self, pts, c):
        self.d.polygon([(int(x), int(y)) for x, y in pts], fill=P[c])

    def iso_line(self, x, y, n, c, dx=2):
        """n steps along the down-right (dx=2) or down-left (dx=-2) iso direction."""
        for k in range(n):
            self.px(x + dx * k, y + k, c)
            self.px(x + dx * k + (1 if dx > 0 else -1), y + k, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.px(x, y, c)

    def corners(self, ox, oy, a, b):
        A = (ox, oy)
        B = (ox + 2 * a, oy + a)
        C = (ox + 2 * a - 2 * b, oy + a + b)
        D = (ox - 2 * b, oy + b)
        return A, B, C, D

    def box(self, ox, oy, a, b, h, top, left, right, edge=None):
        A, B, C, D = self.corners(ox, oy, a, b)
        dn = lambda p: (p[0], p[1] + h)
        self.poly([D, C, dn(C), dn(D)], left)
        self.poly([C, B, dn(B), dn(C)], right)
        self.poly([A, B, C, D], top)
        if edge:  # light rim along the top's front edges
            for k in range(a + 1):
                self.px(D[0] + 2 * k, D[1] + k, edge)
            for k in range(b + 1):
                self.px(C[0] + 2 * k, C[1] - k, edge)
        return A, B, C, D

    def on_left_face(self, D, t, z):
        """Screen point on a left face: t units along it (down-right), z px up from its bottom-left D."""
        return (D[0] + 2 * t, D[1] + t - z)

    def outline(self, c="ink"):
        src = self.im.copy()
        a = src.getchannel("A").load()
        for y in range(self.h):
            for x in range(self.w):
                if not a[x, y] and any(
                    0 <= x + dx < self.w and 0 <= y + dy < self.h and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ):
                    self.im.putpixel((x, y), P[c])

    def save(self, name):
        bbox = self.im.getbbox()
        im = self.im.crop(bbox) if bbox else self.im
        im.save(os.path.join(OUT, f"iso-{name}.png"))
        return im


# ---------------------------------------------------------------- assets


def bookshelf():
    """Tall open bookshelf, front on the left face, four shelves of favourite books."""
    s = Iso(48, 70)
    a, b, h = 16, 5, 50  # 32px wide front, shallow, 50px tall
    ox, oy = 12, 2
    A, B, C, D = s.box(ox, oy, a, b, h, "wood3", "wood2", "wood1", edge="wood4")
    # hollow out the front: back panel visible inside, framed by the sides
    Dh = (D[0], D[1] + h)  # bottom-left of the front face
    inner = [s.on_left_face(Dh, 1, h - 2), s.on_left_face(Dh, a - 1, h - 2), s.on_left_face(Dh, a - 1, 3), s.on_left_face(Dh, 1, 3)]
    s.poly(inner, "wood0")
    rng = random.Random(4)
    spines = ["terra1", "sage2", "blue1", "gold1", "pink1", "cream2", "terra0", "sage1", "blue0", "wood4"]
    shelf_z = [3, 15, 27, 39]  # heights of each shelf board from the bottom
    for z in shelf_z:
        # the board, catching light on its top edge
        for t in range(1, a):
            x, y = s.on_left_face(Dh, t, z)
            s.px(x, y, "wood3"); s.px(x + 1, y, "wood3")
            s.px(x, y + 1, "wood1"); s.px(x + 1, y + 1, "wood1")
        # books standing on it; each spine is 2px wide (one iso step)
        t = 1.5
        while t < a - 1:
            hb = rng.choice([7, 8, 9, 9, 10])
            col = rng.choice(spines)
            if rng.random() < 0.12:  # the odd gap or leaning book
                t += 1
                continue
            x, y = s.on_left_face(Dh, int(t), z + 1)
            for yy in range(y - hb + 1, y + 1):
                s.px(x, yy, col)
                s.px(x + 1, yy + 1, col)
            s.px(x, y - hb + 1, "white" if col not in ("cream2",) else "cream0")  # spine highlight
            t += 1
    # a little plant on top
    tx, ty = A[0] - 2, A[1] + 3
    for (dx, dy, c) in [(0, -3, "sage2"), (-2, -1, "sage1"), (2, -1, "sage2"), (0, 0, "sage1"), (-1, -5, "sage3")]:
        s.d.ellipse([tx + dx - 2, ty + dy - 2, tx + dx + 2, ty + dy + 1], fill=P[c])
    s.d.rectangle([tx - 2, ty + 1, tx + 2, ty + 4], fill=P["terra1"])
    s.outline()
    return s.save("bookshelf")


def counter():
    """Café counter: wood top, sage panelled front (left face)."""
    s = Iso(84, 52)
    a, b, h = 30, 9, 22
    ox, oy = 20, 2
    A, B, C, D = s.box(ox, oy, a, b, h, "wood3", "sage1", "sage0", edge="wood4")
    Dh = (D[0], D[1] + h)
    # panels on the front
    for p0 in range(2, a - 2, 7):
        pts = [s.on_left_face(Dh, p0, h - 5), s.on_left_face(Dh, p0 + 5, h - 5), s.on_left_face(Dh, p0 + 5, 4), s.on_left_face(Dh, p0, 4)]
        s.poly(pts, "sage2")
        for t in range(p0, p0 + 6):  # light top rim of each panel
            x, y = s.on_left_face(Dh, t, h - 5)
            s.px(x, y, "sage3"); s.px(x + 1, y, "sage3")
    # dark kick plate along the bottom
    for t in range(a):
        x, y = s.on_left_face(Dh, t, 1)
        s.px(x, y, "wood0"); s.px(x + 1, y, "wood0"); s.px(x, y - 1, "wood1"); s.px(x + 1, y - 1, "wood1")
    # shadow line under the worktop
    for t in range(a):
        x, y = s.on_left_face(Dh, t, h - 1)
        s.px(x, y, "sage0"); s.px(x + 1, y, "sage0")
    s.outline()
    return s.save("counter")


def table_round():
    s = Iso(40, 34)
    cx, cy = 20, 9
    # pedestal + foot
    s.d.ellipse([cx - 8, 27, cx + 8, 31], fill=P["wood0"])
    s.d.rectangle([cx - 2, 12, cx + 1, 29], fill=P["wood1"])
    # top: 2:1 ellipse with a visible rim
    s.d.ellipse([cx - 17, cy - 6, cx + 17, cy + 10], fill=P["wood1"])
    s.d.ellipse([cx - 17, cy - 8, cx + 17, cy + 8], fill=P["wood3"])
    s.d.ellipse([cx - 13, cy - 6, cx + 11, cy + 4], fill=P["wood4"])
    s.outline()
    return s.save("table-round")


def chair():
    """Bentwood-style chair, seat toward the viewer's left (flip to face right)."""
    s = Iso(32, 38)
    # legs
    for (x, y0, y1) in [(5, 22, 34), (11, 25, 36), (19, 21, 31), (13, 18, 28)]:
        s.vline(x, y0, y1, "wood1")
    # seat (a small iso box)
    s.box(13, 14, 6, 6, 3, "terra1", "wood2", "wood1", edge="terra2")
    # backrest rising from the back edge (the right side of the seat)
    for k in range(7):
        x, y = 13 + 2 * k, 14 + k
        s.vline(x, y - 14, y, "wood2"); s.vline(x + 1, y - 14, y, "wood2")
    for k in range(7):
        x, y = 13 + 2 * k, 14 + k
        s.px(x, y - 14, "wood3"); s.px(x + 1, y - 14, "wood3")
        if k in (2, 4):
            s.vline(x, y - 11, y - 2, "wood0")
    s.outline()
    return s.save("chair")


ALL = [bookshelf, counter, table_round, chair]


def sheet(images, path, scale=5):
    pad = 8
    W = sum(i.width for i in images) + pad * (len(images) + 1)
    H = max(i.height for i in images) + pad * 2
    out = Image.new("RGBA", (W, H), (234, 222, 199, 255))
    x = pad
    for im in images:
        out.alpha_composite(im, (x, H - pad - im.height))
        x += im.width + pad
    out.resize((W * scale, H * scale), Image.NEAREST).save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    imgs = [f() for f in ALL]
    print(f"{len(imgs)} iso assets -> {OUT}")
    if "--preview" in sys.argv:
        os.makedirs(os.path.join(ART, "preview"), exist_ok=True)
        sheet(imgs, os.path.join(ART, "preview", "iso-sheet.png"))

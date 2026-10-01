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
# Outside pieces are for the landing page (the café from the street), so they're kept out of
# the room's asset library until that page exists.
LANDING = {"knee-wall", "storefront-glass", "door", "awning", "street-lamp", "sidewalk-tree", "bench"}
LANDING_OUT = os.path.join(ART, "landing", "sprites")


def out_dir(name):
    return LANDING_OUT if name in LANDING else OUT

PALETTE = {
    "ink": "#3d2418",
    "wood0": "#4a2f25", "wood1": "#6b4232", "wood2": "#8f5b3e", "wood3": "#b47a4f", "wood4": "#d29f6b",
    "cream0": "#c9b18a", "cream1": "#e2cfa8", "cream2": "#f3e6c9", "white": "#fdf8ef",
    "sage0": "#3f5a3a", "sage1": "#5f8251", "sage2": "#86a86b", "sage3": "#b5cf8f",
    "terra0": "#a3523a", "terra1": "#cf7a56", "terra2": "#eaa37f",
    "gold0": "#c98f3c", "gold1": "#e8b45c", "gold2": "#f6d58a",
    "pink0": "#9b3b52", "pink1": "#e89aa8", "pink2": "#f4c6cc",
    "blue0": "#3c5878", "blue1": "#6488aa", "blue2": "#9dbad3",
    "steel0": "#3b3f4a", "steel1": "#6d7380", "steel2": "#a9afba", "steel3": "#d9dde3",
    "glass0": "#9fcbd3", "glass1": "#d6eef1",
    "chalk0": "#24342c", "chalk1": "#2f4538",
    "keyblack": "#1c1717",
}
P = {k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in PALETTE.items()}


class Iso:
    """A sprite canvas with isometric drawing helpers.

    Coordinates for boxes use the top face's back corner (ox, oy). `a` runs down-right
    (2px across, 1 down per unit), `b` runs down-left, `h` is height in px.
    """

    def __init__(self, w, h):
        # Generous canvas so nothing is ever clipped; save() crops to the drawing.
        w, h = max(w, 200), max(h, 200)
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
        for y in range(int(y0), int(y1) + 1):
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

    def block(self, X0, Y0, a, b, z, da, db, h, top, left, right, edge=None):
        """Box whose footprint starts at floor coords (a, b), lifted z px, size da x db x h.
        (X0, Y0) is the screen point of floor coords (0, 0) at height 0."""
        return self.box(X0 + 2 * a - 2 * b, Y0 + a + b - (z + h), da, db, h, top, left, right, edge)

    def pt(self, X0, Y0, a, b, z=0):
        return (X0 + 2 * a - 2 * b, Y0 + a + b - z)

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
        os.makedirs(out_dir(name), exist_ok=True)
        im.save(os.path.join(out_dir(name), f"iso-{name}.png"))
        return im


# Extra layers some assets carry, written to sprites/_companions.json for the engine:
#   sky   = mask of window glass (the engine fills it with the current sky)
#   light = sun patch the window casts on the floor (shown in daytime), with its offset
#   glow  = where a lamp's light comes from (shown at night), and how far it reaches
COMPANIONS = {}


def save_set(name, frame, sky=None, light=None, glow=None):
    bbox = frame.im.getbbox()
    out = frame.im.crop(bbox)
    os.makedirs(out_dir(name), exist_ok=True)
    out.save(os.path.join(out_dir(name), f"iso-{name}.png"))
    info = {}
    if sky is not None:
        sky.im.crop(bbox).save(os.path.join(OUT, f"iso-{name}.sky.png"))
        info["sky"] = f"sprites/iso-{name}.sky.png"
    if light is not None:
        lb = light.im.getbbox()
        light.im.crop(lb).save(os.path.join(OUT, f"iso-{name}.light.png"))
        info["light"] = {"file": f"sprites/iso-{name}.light.png", "dx": lb[0] - bbox[0], "dy": lb[1] - bbox[1], "w": lb[2] - lb[0], "h": lb[3] - lb[1]}
    if glow is not None:
        gx, gy, r = glow
        info["glow"] = {"x": gx - bbox[0], "y": gy - bbox[1], "r": r}
    if info and name not in LANDING:
        COMPANIONS[f"iso-{name}"] = info
    return out


def wall_pt(x0, y0, t, z):
    """A point on the back-right wall plane: t units along the wall, z px up from the floor."""
    return (x0 + 2 * t, y0 + t - z)


def anchor(s, x, y):
    """Invisible pixel at floor level so a wall item's base sits on the wall line."""
    s.im.putpixel((int(x), int(y)), (0, 0, 0, 1))


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


# ---------------------------------------------------------------- batch 2


def pastry_case():
    """Counter base with a glass display case of pastries on top. Opens your projects."""
    s = Iso(120, 110)
    X0, Y0 = 40, 30
    # wood base
    s.block(X0, Y0, 0, 0, 0, 22, 9, 16, "wood3", "wood2", "wood1", edge="wood4")
    A, B, C, D = s.corners(*s.pt(X0, Y0, 0, 0, 16), 22, 9)
    Dh = (D[0], D[1] + 16)
    for p0 in range(2, 20, 6):  # panels on the front
        pts = [s.on_left_face(Dh, p0, 12), s.on_left_face(Dh, p0 + 4, 12), s.on_left_face(Dh, p0 + 4, 3), s.on_left_face(Dh, p0, 3)]
        s.poly(pts, "wood3")
    # glass case on top, inset a little
    gA, gB, gC, gD = s.block(X0, Y0, 1, 1, 16, 20, 7, 14, "glass1", "glass1", "glass0")
    gDh = (gD[0], gD[1] + 14)
    # two glass shelves of pastries seen through the front
    goods = ["gold1", "pink1", "terra1", "gold2", "sage2", "pink2", "gold1", "terra2", "pink1"]
    for row, z in enumerate((2, 8)):
        for t in range(1, 20):
            x, y = s.on_left_face(gDh, t, z)
            s.px(x, y, "glass0"); s.px(x + 1, y, "glass0")
        for k, t in enumerate(range(2, 19, 4)):
            c = goods[(k + row * 3) % len(goods)]
            x, y = s.on_left_face(gDh, t, z + 1)
            for dx in range(4):
                for dy in range(3):
                    s.px(x + dx, y - dy + dx // 2, c)
            s.px(x + 1, y - 2, "white")
    # glare + brass trim along the top edges
    for k in range(5):
        x, y = s.on_left_face(gDh, 15 + k // 2, 12 - k)
        s.px(x, y, "white")
    for k in range(21):
        s.px(gD[0] + 2 * k, gD[1] + k, "gold0"); s.px(gD[0] + 2 * k + 1, gD[1] + k, "gold0")
    s.outline()
    return s.save("pastry-case")


def espresso_machine():
    s = Iso(60, 60)
    X0, Y0 = 20, 20
    A, B, C, D = s.block(X0, Y0, 0, 0, 0, 7, 6, 12, "steel3", "steel2", "steel1", edge="white")
    for k, (a, b) in enumerate([(1, 1), (3, 1), (5, 1)]):  # cups warming on top
        x, y = s.pt(X0, Y0, a, b, 13)
        s.px(x, y, "white"); s.px(x + 1, y, "white"); s.px(x, y + 1, "cream0"); s.px(x + 1, y + 1, "cream0")
    Dh = (D[0], D[1] + 12)
    for t in range(7):  # red name stripe
        x, y = s.on_left_face(Dh, t, 9)
        s.px(x, y, "terra1"); s.px(x + 1, y, "terra1")
    gx, gy = s.on_left_face(Dh, 3, 6)  # group head, portafilter, cup
    s.px(gx, gy, "steel0"); s.px(gx + 1, gy, "steel0"); s.px(gx, gy + 1, "steel0")
    for k in range(3):
        s.px(gx - 2 - k, gy + 1 + k, "keyblack")
    cx, cy = s.on_left_face(Dh, 3, 2)
    s.px(cx, cy, "white"); s.px(cx + 1, cy, "white"); s.px(cx, cy - 1, "wood1"); s.px(cx + 1, cy - 1, "wood1")
    s.outline()
    return s.save("espresso-machine")


def register():
    s = Iso(50, 50)
    X0, Y0 = 18, 16
    s.block(X0, Y0, 0, 0, 0, 5, 5, 5, "cream2", "terra1", "terra0", edge="white")
    s.block(X0, Y0, 1, 0, 5, 3, 1, 5, "steel0", "steel1", "steel0")  # screen
    x, y = s.pt(X0, Y0, 2, 1, 9)
    s.px(x, y, "sage3"); s.px(x + 1, y, "sage3")
    s.outline()
    return s.save("register")


def menu_board():
    """Hangs on the back-right wall (flip for the other wall). A faint anchor pixel at floor
    level keeps its base on the wall line, so it snaps to the floor right under itself."""
    s = Iso(70, 90)
    x0, y0 = 4, 30  # bottom-left corner of the board, on the wall plane
    L, Hh = 14, 24  # length along the wall (units), height (px)
    for t in range(L):
        for z in range(Hh):
            edge = t == 0 or t == L - 1 or z < 2 or z >= Hh - 2
            c = "wood2" if edge else "chalk1"
            if edge and (z >= Hh - 2 or t == 0):
                c = "wood3"
            for dx in (0, 1):
                s.px(x0 + 2 * t + dx, y0 + t - z, c)
    # chalk heading and menu lines (they follow the wall's slope)
    for t in range(4, 10):
        x, y = x0 + 2 * t, y0 + t - 19
        s.px(x, y, "cream2"); s.px(x + 1, y, "cream2")
    for z in (14, 10, 6):
        for t in range(2, 9):
            s.px(x0 + 2 * t, y0 + t - z, "cream1")
        for t in range(10, 12):
            s.px(x0 + 2 * t, y0 + t - z, "gold2")
    s.outline()
    # invisible anchor at floor level under the board's middle
    s.im.putpixel((x0 + L, y0 + L // 2 + 40), (0, 0, 0, 1))
    return s.save("menu-board")


def piano():
    s = Iso(110, 110)
    X0, Y0 = 40, 50
    s.block(X0, Y0, 0, 0, 0, 14, 5, 30, "wood2", "wood1", "wood0", edge="wood3")
    # music sheet on the front, above the keys
    A, B, C, D = s.corners(*s.pt(X0, Y0, 0, 0, 30), 14, 5)
    Dh = (D[0], D[1] + 30)
    s.poly([s.on_left_face(Dh, 5, 24), s.on_left_face(Dh, 9, 24), s.on_left_face(Dh, 9, 19), s.on_left_face(Dh, 5, 19)], "cream2")
    # keyboard sticking out of the front
    kA, kB, kC, kD = s.block(X0, Y0, 0, 5, 14, 14, 3, 3, "white", "wood1", "wood0")
    for t in range(14):
        if t % 7 not in (2, 6):
            x, y = kA[0] + 2 * t - 2, kA[1] + t + 1
            s.px(x, y, "keyblack"); s.px(x + 1, y, "keyblack")
    for a in (0, 13):  # legs
        x, y = s.pt(X0, Y0, a, 8, 14)
        s.vline(x, y, y + 14, "wood1")
    # bench in front
    s.block(X0, Y0, 4, 11, 0, 6, 3, 8, "terra1", "wood1", "wood0", edge="terra2")
    s.outline()
    return s.save("piano")


def record_player():
    s = Iso(80, 80)
    X0, Y0 = 30, 30
    A, B, C, D = s.block(X0, Y0, 0, 0, 0, 10, 6, 14, "wood3", "wood2", "wood1", edge="wood4")
    Dh = (D[0], D[1] + 14)
    for p0 in (1, 5):  # two cabinet doors
        s.poly([s.on_left_face(Dh, p0, 11), s.on_left_face(Dh, p0 + 3, 11), s.on_left_face(Dh, p0 + 3, 3), s.on_left_face(Dh, p0, 3)], "wood1")
        x, y = s.on_left_face(Dh, p0 + 3 if p0 == 1 else p0, 7)
        s.px(x, y, "gold1")
    # turntable + record on top
    s.block(X0, Y0, 1, 1, 14, 8, 4, 2, "cream2", "cream1", "cream0")
    cx, cy = s.pt(X0, Y0, 4.5, 3, 16)
    s.d.ellipse([cx - 6, cy - 3, cx + 5, cy + 2], fill=P["keyblack"])
    s.d.ellipse([cx - 2, cy - 1, cx + 1, cy], fill=P["terra1"])
    tx, ty = s.pt(X0, Y0, 8, 2, 16)
    s.px(tx, ty - 1, "steel2"); s.px(tx - 1, ty, "steel2"); s.px(tx - 2, ty + 1, "steel2")
    s.outline()
    return s.save("record-player")


def armchair():
    s = Iso(80, 80)
    X0, Y0 = 30, 30
    s.block(X0, Y0, 0, 0, 0, 9, 2, 16, "sage2", "sage1", "sage0", edge="sage3")  # backrest
    s.block(X0, Y0, 0, 2, 0, 2, 7, 9, "sage2", "sage1", "sage0", edge="sage3")  # arm (far)
    s.block(X0, Y0, 2, 2, 0, 5, 7, 6, "sage3", "sage1", "sage0", edge="sage3")  # seat
    s.block(X0, Y0, 7, 2, 0, 2, 7, 9, "sage2", "sage1", "sage0", edge="sage3")  # arm (near)
    for (a, b) in ((0.5, 8.5), (8.5, 8.5)):
        x, y = s.pt(X0, Y0, a, b, 0)
        s.px(x, y + 1, "wood1")
    s.outline()
    return s.save("armchair")


def stool():
    s = Iso(40, 50)
    cx, cy = 18, 14
    for x in (cx - 4, cx + 3):
        s.vline(x, cy + 2, cy + 18, "steel1")
    s.vline(cx, cy + 3, cy + 20, "steel0")
    for x in range(cx - 4, cx + 4):
        s.px(x, cy + 12, "gold0")
    s.d.ellipse([cx - 7, cy - 2, cx + 7, cy + 5], fill=P["wood2"])
    s.d.ellipse([cx - 7, cy - 4, cx + 7, cy + 3], fill=P["wood3"])
    s.d.ellipse([cx - 4, cy - 3, cx + 3, cy], fill=P["wood4"])
    s.outline()
    return s.save("stool")


def plant_pot():
    s = Iso(50, 60)
    X0, Y0 = 20, 30
    s.block(X0, Y0, 0, 0, 0, 5, 5, 8, "wood1", "terra1", "terra0", edge="terra2")
    cx, cy = s.pt(X0, Y0, 2.5, 2.5, 8)
    for (dx, dy, r, c) in [(0, -6, 6, "sage1"), (-5, -3, 5, "sage2"), (5, -3, 5, "sage1"), (0, -12, 5, "sage2"), (-3, -9, 4, "sage3"), (4, -10, 4, "sage2")]:
        s.d.ellipse([cx + dx - r, cy + dy - r // 1.5, cx + dx + r, cy + dy + r // 1.5], fill=P[c])
    s.outline()
    return s.save("plant-pot")


def floor_lamp():
    s = Iso(40, 80)
    cx = 18
    s.d.ellipse([cx - 5, 60, cx + 5, 64], fill=P["steel0"])
    s.vline(cx, 20, 62, "steel0"); s.vline(cx + 1, 20, 62, "steel1")
    # shade: a little cone
    for y in range(8, 20):
        w = 4 + (y - 8) // 2
        for x in range(cx - w, cx + w + 2):
            s.px(x, y, "cream2" if x < cx + 1 else "cream1")
    for x in range(cx - 9, cx + 11):
        s.px(x, 20, "gold1")
    s.outline()
    return save_set("floor-lamp", s, glow=(cx, 22, 90))


def rug():
    s = Iso(140, 80)
    X0, Y0 = 60, 4
    a, b = 24, 16
    s.box(X0, Y0, a, b, 0, "terra1", "terra1", "terra1")
    s.box(X0, Y0 + 2, a - 2, b - 2, 0, "cream1", "cream1", "cream1")
    s.box(X0, Y0 + 4, a - 4, b - 4, 0, "terra0", "terra0", "terra0")
    # little diamonds down the middle
    for k in range(3):
        cx, cy = X0 + 2 * (6 + k * 5) - 2 * (b // 2), Y0 + (6 + k * 5) + b // 2
        s.poly([(cx, cy - 2), (cx + 4, cy), (cx, cy + 2), (cx - 4, cy)], "gold1")
    s.outline()
    return s.save("rug")


# ---------------------------------------------------------------- wall pieces (batch 3)


def window():
    """Tall window for the back-right wall (flip for the other wall). The glass is left
    transparent; the engine paints the current sky into it and casts a sun patch."""
    L, z0, z1 = 12, 50, 98
    x0, y0 = 40, 120
    frame, sky, light = Iso(200, 200), Iso(200, 200), Iso(200, 200)
    for t in range(L):
        for z in range(z0, z1):
            x, y = wall_pt(x0, y0, t, z)
            border = t == 0 or t == L - 1 or z < z0 + 2 or z >= z1 - 2
            mullion = t == L // 2 or z in ((z0 + z1) // 2, (z0 + z1) // 2 + 1)
            for dx in (0, 1):
                if border:
                    frame.px(x + dx, y, "wood3" if (z >= z1 - 2 or t == 0) else "wood2")
                elif mullion:
                    frame.px(x + dx, y, "wood2")
                else:
                    sky.px(x + dx, y, "white")
    # sill: a little ledge under the window
    for t in range(-1, L + 1):
        for k, c in ((0, "cream2"), (1, "cream1"), (2, "cream0")):
            x, y = wall_pt(x0, y0, t, z0 - k)
            frame.px(x, y, c); frame.px(x + 1, y, c)
        x, y = wall_pt(x0, y0, t, z0 + 1)
        frame.px(x - 2, y + 1, "cream2"); frame.px(x - 1, y + 1, "cream2")
    frame.outline()
    anchor(frame, *wall_pt(x0, y0, L // 2, 0))
    # sun patch on the floor in front: the window's shape, thrown down and out from the wall
    for ti in range(0, 2 * L):
        for si in range(6, 24):
            t, sdepth = ti / 2, si / 2
            tt = t - sdepth * 0.45  # the sun comes in at an angle
            if not (0.5 <= tt <= L - 1.5):
                continue
            if abs(tt - L / 2) < 0.4 or abs(sdepth - 7.5) < 0.3:  # mullion shadows
                continue
            x = x0 + 2 * t - 2 * sdepth
            y = y0 + t + sdepth
            light.px(x, y, "white"); light.px(x + 1, y, "white")
    return save_set("window", frame, sky=sky, light=light)


def wall_sconce():
    s = Iso(60, 120)
    x0, y0 = 10, 100
    bx, by = wall_pt(x0, y0, 3, 78)
    for k in range(4):  # brass arm out from the wall
        s.px(bx - k, by + k // 2, "gold0")
    # little shade, bulb glowing under it
    for dy, w in ((0, 3), (1, 4), (2, 5), (3, 5)):
        for dx in range(-w, w + 1):
            s.px(bx - 4 + dx, by + 2 + dy, "sage1" if dy < 3 else "sage0")
    s.px(bx - 4, by + 6, "gold2"); s.px(bx - 3, by + 6, "gold2")
    s.outline()
    anchor(s, *wall_pt(x0, y0, 3, 0))
    return save_set("wall-sconce", s, glow=(bx - 4, by + 8, 70))


def framed_picture():
    s = Iso(70, 130)
    x0, y0 = 6, 110
    L, z0, z1 = 9, 62, 84
    for t in range(L):
        for z in range(z0, z1):
            x, y = wall_pt(x0, y0, t, z)
            border = t == 0 or t == L - 1 or z < z0 + 2 or z >= z1 - 2
            if border:
                c = "gold1" if z >= z1 - 2 else "gold0"
            elif z > z0 + 12:
                c = "blue2" if z > z0 + 16 else "glass1"  # sky
            elif z > z0 + 7:
                c = "sage2" if (t + z) % 5 else "sage1"  # hills
            else:
                c = "sage1"
            s.px(x, y, c); s.px(x + 1, y, c)
    sx, sy = wall_pt(x0, y0, 6, z0 + 17)
    s.px(sx, sy, "gold2"); s.px(sx + 1, sy, "gold2")  # a little sun
    s.outline()
    anchor(s, *wall_pt(x0, y0, L // 2, 0))
    return save_set("framed-picture", s)


def wall_shelf():
    s = Iso(80, 130)
    x0, y0 = 10, 110
    L, z = 12, 70
    for t in range(L):  # the plank, sticking out of the wall
        for k, c in ((0, "wood3"), (1, "wood2"), (2, "wood1")):
            x, y = wall_pt(x0, y0, t, z - k)
            s.px(x - 2, y + 1, c); s.px(x - 1, y + 1, c)
    jars = [("glass1", "gold1"), ("glass1", "terra1"), ("cream2", "wood1"), ("glass1", "sage2"), ("cream2", "pink1")]
    for k, (glass, inner) in enumerate(jars):
        t = 1 + k * 2.2
        bx, by = wall_pt(x0, y0, t, z + 1)
        h = 7 if k % 2 == 0 else 5
        for dy in range(h):
            for dx in range(3):
                s.px(bx - 1 + dx, by - dy, inner if dy < h - 2 else glass)
        s.px(bx - 1, by - h, "wood1"); s.px(bx, by - h, "wood1"); s.px(bx + 1, by - h, "wood1")
    s.outline()
    anchor(s, *wall_pt(x0, y0, L // 2, 0))
    return save_set("wall-shelf", s)


def hanging_plant():
    s = Iso(60, 130)
    x0, y0 = 14, 110
    bx, by = wall_pt(x0, y0, 3, 92)
    for k in range(6):  # bracket arm
        s.px(bx - k, by + k // 2, "keyblack")
    px, py = bx - 7, by + 3
    s.vline(px, py, py + 4, "steel1")
    for dy in range(5):  # pot
        for dx in range(-3, 4):
            s.px(px + dx, py + 5 + dy, "cream1" if dx < 2 else "cream0")
    for (dx, dy, r, c) in [(-3, 3, 3, "sage1"), (2, 3, 3, "sage2"), (0, 2, 3, "sage2")]:
        s.d.ellipse([px + dx - r, py + dy - r // 1.5, px + dx + r, py + dy + r // 1.5], fill=P[c])
    for vx, length in [(-4, 14), (-1, 19), (2, 16), (4, 10)]:  # trailing vines
        for k in range(length):
            x, y = px + vx + (k // 5) % 2, py + 10 + k
            s.px(x, y, "sage0")
            if k % 3 == 0:
                s.px(x - 1, y, "sage2"); s.px(x + 1, y + 1, "sage1")
    s.outline()
    anchor(s, *wall_pt(x0, y0, 3, 0))
    return save_set("hanging-plant", s)


# ---------------------------------------------------------------- storefront + street (batch 4)
# Front-wall pieces run along the café's front edges. Drawn facing down-left (front-left
# edge); flip for the front-right edge. 8 units = one tile along the wall.

NAVY = ("blue0", "steel0")


def knee_wall():
    """Low wall segment, two tiles long: the base of the storefront."""
    s = Iso(120, 80)
    X0, Y0 = 50, 30
    s.block(X0, Y0, 0, 0, 0, 16, 2, 20, "cream1", "blue0", "steel0", edge="cream2")
    A, B, C, D = s.corners(*s.pt(X0, Y0, 0, 0, 20), 16, 2)
    Dh = (D[0], D[1] + 20)
    for p0 in (1, 9):  # recessed panels
        s.poly([s.on_left_face(Dh, p0, 15), s.on_left_face(Dh, p0 + 6, 15), s.on_left_face(Dh, p0 + 6, 4), s.on_left_face(Dh, p0, 4)], "blue1")
    s.outline()
    return s.save("knee-wall")


def storefront_glass():
    """Two tiles of shop window: navy frame, big panes, a knee wall underneath."""
    s = Iso(120, 140)
    X0, Y0 = 50, 100
    s.block(X0, Y0, 0, 0, 0, 16, 2, 20, "cream1", "blue0", "steel0", edge="cream2")
    # frame + glass above the knee wall
    s.block(X0, Y0, 0, 0, 20, 16, 1, 62, "blue0", "glass0", "steel0")
    A, B, C, D = s.corners(*s.pt(X0, Y0, 0, 0, 82), 16, 1)
    Dh = (D[0], D[1] + 62)
    for t in range(16):
        for z in range(62):
            x, y = s.on_left_face(Dh, t, z)
            frame = t in (0, 8, 15) or z < 2 or z >= 60
            if frame:
                c = "blue0"
            else:
                glare = 0 <= (z - 2 * t + 8) % 30 < 3  # diagonal reflections
                c = "glass1" if glare else ("glass0" if z > 30 else "blue2")
            s.px(x, y, c); s.px(x + 1, y, c)
    s.outline()
    return s.save("storefront-glass")


def door():
    """Café door with a glass upper half; one tile wide."""
    s = Iso(80, 140)
    X0, Y0 = 30, 100
    A, B, C, D = s.block(X0, Y0, 0, 0, 0, 8, 1, 82, "blue0", "wood2", "wood0")
    Dh = (D[0], D[1] + 82)
    for t in range(8):
        for z in range(82):
            x, y = s.on_left_face(Dh, t, z)
            if t in (0, 7) or z >= 79 or z < 2:
                c = "blue0"
            elif 44 < z < 74 and 1 < t < 6:
                c = "glass1" if (z - t) % 9 == 0 else "glass0"
            elif t in (1, 6) or z in (40, 44):
                c = "wood3"
            else:
                c = "wood2"
            s.px(x, y, c); s.px(x + 1, y, c)
    hx, hy = s.on_left_face(Dh, 6, 38)
    s.px(hx, hy, "gold1"); s.px(hx, hy + 1, "gold0")
    s.outline()
    return s.save("door")


def awning():
    """Striped awning sloping out and down from the front wall, two tiles wide."""
    s = Iso(120, 140)
    x0, y0 = 40, 110
    top_z = 92
    for ti in range(0, 33):  # along the wall, half-unit steps
        t = ti / 2
        for ki in range(0, 25):  # out from the wall (and down), fine steps so there are no gaps
            o = ki / 8  # units out from the wall
            drop = ki * 0.6  # px down as it slopes out
            x = x0 + 2 * t - 2 * o
            y = y0 + t - top_z + o + drop
            stripe = int(t) % 2 == 0
            c = "cream2" if stripe else "sage1"
            if ki > 21:
                c = "cream1" if stripe else "sage0"  # front lip
            s.px(x, y, c); s.px(x + 1, y, c)
        # scalloped edge under the lip
        if ti % 2 == 0:
            x = x0 + 2 * t - 2 * 3
            y = y0 + t - top_z + 3 + 24 * 0.6 + 1
            s.px(x, y, "sage0" if int(t) % 2 else "cream0")
    s.outline()
    anchor(s, x0 + 16, y0 + 8)
    return s.save("awning")


def street_lamp():
    s = Iso(60, 160)
    cx = 26
    for y in range(130, 136):  # base
        for x in range(cx - 4, cx + 5):
            s.px(x, y, "steel0")
    s.vline(cx, 30, 132, "steel0"); s.vline(cx + 1, 30, 132, "steel1")
    for x in range(cx - 3, cx + 5):
        s.px(x, 100, "steel1")  # little collar
    # lantern
    for y in range(14, 30):
        w = 4 if y < 18 or y > 26 else 5
        for x in range(cx - w, cx + w + 2):
            edge = x in (cx - w, cx + w + 1) or y in (14, 29)
            s.px(x, y, "steel0" if edge else ("gold2" if x < cx + 1 else "gold1"))
    for x in range(cx - 3, cx + 5):
        s.px(x, 12, "steel0"); s.px(x, 13, "steel1")
    s.px(cx, 10, "steel0"); s.px(cx + 1, 10, "steel0")
    s.outline()
    return save_set("street-lamp", s, glow=(cx, 22, 110))


def sidewalk_tree():
    s = Iso(110, 160)
    X0, Y0 = 50, 120
    s.block(X0, Y0, 0, 0, 0, 6, 6, 2, "steel1", "steel0", "steel0")  # iron grate
    tx, ty = s.pt(X0, Y0, 3, 3, 2)
    s.vline(tx, ty - 62, ty, "wood1"); s.vline(tx + 1, ty - 62, ty, "wood0")
    s.px(tx - 1, ty - 30, "wood1"); s.px(tx - 2, ty - 31, "wood1")
    rng = random.Random(5)
    for k in range(26):  # leafy canopy of overlapping clusters, lit from the top-left
        dx = rng.randint(-22, 22)
        dy = rng.randint(-34, 6)
        r = rng.randint(6, 10)
        c = "sage3" if dx + dy < -22 else ("sage2" if dx + dy < 0 else ("sage1" if dx + dy < 18 else "sage0"))
        s.d.ellipse([tx + dx - r, ty - 66 + dy * 0.7 - r * 0.8, tx + dx + r, ty - 66 + dy * 0.7 + r * 0.8], fill=P[c])
    s.outline()
    return s.save("sidewalk-tree")


def bench():
    s = Iso(90, 70)
    X0, Y0 = 34, 30
    for a in (0.5, 11):  # iron legs
        for b in (0.5, 3.5):
            x, y = s.pt(X0, Y0, a, b, 0)
            s.vline(x, y - 9, y, "steel0")
    s.block(X0, Y0, 0, 0, 9, 12, 4, 2, "wood3", "wood2", "wood1", edge="wood4")  # seat
    s.block(X0, Y0, 0, 0, 11, 12, 1, 9, "wood3", "wood2", "wood1", edge="wood4")  # backrest
    s.outline()
    return s.save("bench")


def laptop():
    s = Iso(40, 40)
    X0, Y0 = 16, 14
    s.block(X0, Y0, 0, 0, 0, 6, 4, 1, "steel3", "steel2", "steel1")  # base
    s.block(X0, Y0, 0, 0, 1, 6, 1, 7, "steel1", "blue2", "steel0")  # screen, lit
    x, y = s.pt(X0, Y0, 2, 1, 5)
    s.px(x, y, "white"); s.px(x + 1, y, "glass1")
    s.outline()
    return s.save("laptop")


def flower_vase():
    s = Iso(30, 40)
    cx = 12
    for y in range(18, 28):
        for x in range(cx - 2, cx + 3):
            s.px(x, y, "glass1" if x < cx else "glass0")
    for (dx, dy, c) in [(-4, 6, "pink1"), (3, 5, "gold1"), (0, 2, "white"), (-2, 9, "terra2"), (4, 10, "pink2"), (1, 7, "sage2"), (-5, 12, "sage1")]:
        s.d.ellipse([cx + dx - 2, dy + 4, cx + dx + 2, dy + 7], fill=P[c])
    s.vline(cx, 12, 18, "sage1")
    s.outline()
    return s.save("flower-vase")


def coffee_cup():
    s = Iso(20, 20)
    s.d.ellipse([3, 10, 13, 14], fill=P["cream1"])  # saucer
    for y in range(5, 11):
        for x in range(5, 11):
            s.px(x, y, "white" if x < 9 else "cream2")
    for x in range(5, 11):
        s.px(x, 5, "wood1")
    s.px(11, 7, "white"); s.px(12, 8, "white"); s.px(11, 9, "white")
    s.outline()
    return s.save("coffee-cup")


ALL = [bookshelf, counter, table_round, chair, pastry_case, espresso_machine, register, menu_board,
       piano, record_player, armchair, stool, plant_pot, floor_lamp, rug,
       window, wall_sconce, framed_picture, wall_shelf, hanging_plant,
       knee_wall, storefront_glass, door, awning, street_lamp, sidewalk_tree, bench, laptop, flower_vase, coffee_cup]


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
    import json

    # glow points for pieces brought over from the original café (not drawn here)
    with open(os.path.join(OUT, "_companions.json"), "w") as f:
        json.dump(COMPANIONS, f, indent=2)
    print(f"{len(imgs)} iso assets -> {OUT}")
    if "--preview" in sys.argv:
        os.makedirs(os.path.join(ART, "preview"), exist_ok=True)
        sheet(imgs, os.path.join(ART, "preview", "iso-sheet.png"))

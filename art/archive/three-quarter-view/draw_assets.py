"""Hand-drawn (in code) café assets: chunky, cozy, 3/4 top-down view.

Every sprite uses the small shared PALETTE below, a 1px dark outline, and light from the
top-left. Drawn at 1x on a 16px grid; the site scales them up with hard pixels.

    python3 art/draw_assets.py            # writes public/cafe/sprites/<name>.png
    python3 art/draw_assets.py --preview  # also writes art/preview/assets-sheet.png

Edit any result in the café's pixel editor afterwards; re-running overwrites these files.
"""
import os
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
    "steel0": "#3b3f4a", "steel1": "#6d7380", "steel2": "#a9afba", "steel3": "#d9dde3",
    "glass0": "#9fcbd3", "glass1": "#d6eef1",
    "chalk0": "#24342c", "chalk1": "#2f4538",
    "keyblack": "#1c1717",
}
P = {k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in PALETTE.items()}


class Sprite:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.w, self.h = w, h

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((x, y), P[c])

    def rect(self, x0, y0, x1, y1, c):  # inclusive; empty if the box has no size
        if x1 >= x0 and y1 >= y0:
            self.d.rectangle([x0, y0, x1, y1], fill=P[c])

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def ellipse(self, x0, y0, x1, y1, c):
        self.d.ellipse([x0, y0, x1, y1], fill=P[c])

    def outline(self, c="ink"):
        """1px outline around everything drawn so far (outside the shape)."""
        src = self.im.copy()
        a = src.getchannel("A").load()
        for y in range(self.h):
            for x in range(self.w):
                if a[x, y]:
                    continue
                if any(0 <= x + dx < self.w and 0 <= y + dy < self.h and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.im.putpixel((x, y), P[c])

    def save(self, name):
        self.im.save(os.path.join(OUT, f"{name}.png"))
        return self.im


def box(s, x, y, w, top, front, top_c, front_c, light=None, dark=None):
    """A 3/4-view block: lit top face over a front face, with a highlight and a shadow edge."""
    s.rect(x, y, x + w - 1, y + top - 1, top_c)
    s.rect(x, y + top, x + w - 1, y + top + front - 1, front_c)
    if light:
        s.hline(x, x + w - 1, y, light)
    if dark:
        s.hline(x, x + w - 1, y + top, dark)  # where top meets front
        s.hline(x, x + w - 1, y + top + front - 1, dark)


# ---------------------------------------------------------------- furniture


def counter():
    s = Sprite(66, 34)
    # top: wood slab, slight overhang
    box(s, 1, 1, 64, 7, 0, "wood3", "wood3", light="wood4")
    s.hline(1, 64, 7, "wood1")
    for x in (12, 30, 47):  # plank joints on top
        s.vline(x, 2, 6, "wood2")
    # front: sage panels with cream frames
    s.rect(2, 8, 63, 30, "sage1")
    for x0 in (4, 19, 34, 49):
        s.rect(x0, 10, x0 + 12, 27, "sage2")
        s.hline(x0, x0 + 12, 10, "sage3")
        s.vline(x0, 10, 27, "sage3")
        s.hline(x0, x0 + 12, 27, "sage0")
        s.vline(x0 + 12, 10, 27, "sage0")
    s.hline(2, 63, 8, "sage0")  # shadow under the top
    s.rect(2, 29, 63, 31, "wood1")  # kick plate
    s.outline()
    return s.save("counter")


def pastry_case():
    s = Sprite(40, 27)
    # wood base
    box(s, 1, 19, 38, 2, 5, "wood3", "wood1", light="wood4", dark="wood0")
    # glass box
    s.rect(2, 2, 37, 19, "glass0")
    s.rect(3, 3, 36, 18, "glass1")
    # shelf
    s.hline(3, 36, 11, "cream0")
    # top row: croissants
    for x in (5, 13, 21, 29):
        s.rect(x, 7, x + 5, 9, "gold1")
        s.hline(x + 1, x + 4, 6, "gold2")
        s.px(x, 9, "gold0"); s.px(x + 5, 9, "gold0")
        s.vline(x + 2, 7, 9, "gold0")
    # bottom row: pink cakes and macarons
    for x in (5, 17, 29):
        s.rect(x, 14, x + 5, 17, "pink1")
        s.hline(x, x + 5, 14, "pink2")
        s.hline(x, x + 5, 16, "white")
        s.px(x + 2, 13, "pink0")
    for x in (12, 24):
        s.rect(x, 15, x + 3, 17, "sage2"); s.hline(x, x + 3, 16, "cream2")
    # glare + brass frame corners
    for i in range(5):
        s.px(30 + i, 3 + i, "white")
    s.hline(2, 37, 2, "gold0")
    s.vline(2, 2, 19, "gold0"); s.vline(37, 2, 19, "gold0")
    s.outline()
    return s.save("pastry-case")


def piano_upright():
    s = Sprite(38, 36)
    # body
    s.rect(2, 4, 35, 22, "wood1")
    s.hline(2, 35, 4, "wood2")
    box(s, 1, 1, 36, 3, 0, "wood2", "wood2", light="wood3")  # lid
    # front panel insets
    s.rect(5, 7, 32, 15, "wood0")
    s.rect(6, 8, 31, 14, "wood1")
    # sheet music on the stand
    s.rect(14, 8, 23, 14, "cream2")
    for y in (10, 12):
        s.hline(15, 22, y, "cream0")
    # keybed
    s.rect(1, 17, 36, 21, "wood2")
    s.rect(3, 18, 34, 20, "white")
    for x in range(4, 34, 4):  # black keys in 2s and 3s
        if x % 28 not in (12, 24):
            s.rect(x, 18, x + 1, 19, "keyblack")
    s.hline(1, 36, 21, "wood0")
    # lower body + legs
    s.rect(3, 22, 34, 30, "wood1")
    s.rect(6, 24, 31, 29, "wood0")
    s.rect(1, 22, 3, 33, "wood2"); s.rect(34, 22, 36, 33, "wood2")
    s.hline(1, 3, 33, "wood0"); s.hline(34, 36, 33, "wood0")
    s.px(17, 31, "gold1"); s.px(20, 31, "gold1")  # pedals
    s.outline()
    return s.save("piano-upright")


def record_player():
    s = Sprite(26, 26)
    # cabinet
    box(s, 1, 8, 24, 3, 14, "wood3", "wood2", light="wood4", dark="wood1")
    s.rect(3, 13, 11, 21, "wood1"); s.rect(14, 13, 22, 21, "wood1")
    s.px(10, 17, "gold1"); s.px(15, 17, "gold1")
    s.rect(2, 24, 3, 25, "wood0"); s.rect(22, 24, 23, 25, "wood0")
    # turntable on top
    s.rect(3, 3, 20, 9, "cream1")
    s.hline(3, 20, 3, "cream2")
    s.ellipse(5, 3, 15, 9, "keyblack")
    s.ellipse(8, 5, 12, 7, "terra1")
    s.px(10, 6, "cream2")
    s.vline(18, 2, 6, "steel2"); s.hline(15, 18, 7, "steel2")  # tonearm
    s.outline()
    return s.save("record-player")


def chair(facing="front"):
    s = Sprite(16, 24)
    if facing == "front":
        # backrest behind the seat
        s.rect(3, 1, 12, 2, "wood2"); s.vline(3, 1, 11, "wood1"); s.vline(12, 1, 11, "wood1")
        s.vline(6, 3, 10, "wood1"); s.vline(9, 3, 10, "wood1")
        # seat with cushion
        box(s, 2, 11, 12, 3, 2, "terra1", "wood1", light="terra2", dark="wood0")
        # legs
        s.vline(2, 16, 22, "wood1"); s.vline(13, 16, 22, "wood1")
        s.vline(4, 16, 21, "wood0"); s.vline(11, 16, 21, "wood0")
    else:
        # seen from behind: the backrest covers the seat
        box(s, 2, 11, 12, 3, 2, "terra1", "wood1", light="terra2", dark="wood0")
        s.vline(2, 16, 22, "wood1"); s.vline(13, 16, 22, "wood1")
        s.rect(3, 1, 12, 13, "wood2")
        s.rect(5, 4, 10, 11, "wood1")
        s.hline(3, 12, 1, "wood3")
    s.outline()
    return s.save(f"chair-{facing}")


def stool():
    s = Sprite(14, 20)
    s.ellipse(1, 1, 12, 6, "wood3")
    s.ellipse(2, 1, 11, 4, "wood4")
    s.vline(3, 6, 18, "steel1"); s.vline(10, 6, 18, "steel1")
    s.hline(3, 10, 13, "gold0")
    s.outline()
    return s.save("stool")


def table_round():
    s = Sprite(28, 24)
    s.ellipse(1, 1, 26, 10, "wood2")
    s.ellipse(1, 0, 26, 8, "wood3")
    s.ellipse(4, 1, 23, 6, "wood4")
    s.rect(12, 10, 15, 19, "wood1")
    s.ellipse(6, 18, 21, 22, "wood0")
    s.outline()
    return s.save("table-round")


def table_square():
    s = Sprite(34, 22)
    box(s, 1, 1, 32, 9, 2, "wood3", "wood1", light="wood4", dark="wood0")
    for x in (11, 22):
        s.vline(x, 2, 9, "wood2")
    s.rect(2, 12, 4, 20, "wood1"); s.rect(29, 12, 31, 20, "wood1")
    s.outline()
    return s.save("table-square")


def menu_board():
    s = Sprite(36, 26)
    s.rect(0, 0, 35, 25, "wood2")
    s.hline(0, 35, 0, "wood3"); s.vline(0, 0, 25, "wood3")
    s.hline(0, 35, 25, "wood0"); s.vline(35, 0, 25, "wood0")
    s.rect(2, 2, 33, 23, "chalk1")
    s.rect(2, 2, 33, 3, "chalk0")
    # heading + menu lines in chalk
    s.hline(10, 25, 5, "cream2")
    s.px(9, 5, "pink1"); s.px(26, 5, "pink1")
    for y in (9, 12, 15, 18):
        s.hline(5, 19, y, "cream1")
        s.hline(25, 30, y, "gold2")
    s.px(5, 21, "sage3"); s.hline(7, 14, 21, "cream0")
    s.outline()
    return s.save("menu-chalkboard")


# ---------------------------------------------------------------- small things


def espresso_machine():
    s = Sprite(26, 24)
    # cups warming on top
    for x in (4, 9, 14):
        s.rect(x, 0, x + 3, 2, "white"); s.hline(x, x + 3, 2, "cream0")
    box(s, 1, 3, 22, 3, 15, "steel3", "steel2", light="white", dark="steel1")
    s.hline(2, 21, 7, "terra1"); s.hline(2, 21, 8, "terra0")  # thin name stripe
    s.ellipse(17, 10, 20, 13, "cream2"); s.px(19, 11, "terra0")  # gauge, off to one side
    # single group head + portafilter angled down to the left
    s.rect(7, 11, 12, 12, "steel0")
    s.rect(8, 13, 11, 13, "steel1")
    for k in range(4):
        s.px(6 - k, 13 + k, "keyblack")
    # cup under the spout
    s.rect(8, 16, 11, 18, "white"); s.hline(8, 11, 16, "wood1"); s.px(12, 17, "white")
    # steam wand on the right side
    s.vline(23, 8, 17, "steel1"); s.px(24, 17, "steel1")
    s.rect(2, 19, 21, 20, "steel1"); s.hline(2, 21, 19, "steel2")  # drip tray
    s.outline()
    return s.save("espresso-machine")


def cup():
    s = Sprite(9, 8)
    s.rect(1, 2, 5, 6, "white")
    s.hline(1, 5, 2, "wood1")  # coffee
    s.vline(6, 3, 4, "white"); s.px(7, 3, "white"); s.px(7, 4, "white")
    s.hline(0, 6, 7, "cream0")  # saucer
    s.outline()
    return s.save("cup")


def cake_stand():
    s = Sprite(16, 16)
    s.rect(2, 4, 13, 8, "pink1")
    s.hline(2, 13, 4, "pink2")
    s.hline(2, 13, 6, "white")
    for x in (4, 8, 11):
        s.px(x, 3, "pink0")
    s.hline(1, 14, 9, "cream2")
    s.vline(7, 10, 13, "cream1"); s.vline(8, 10, 13, "cream1")
    s.hline(4, 11, 14, "cream1")
    s.outline()
    return s.save("cake-stand")


def plant_pot():
    s = Sprite(16, 22)
    for (x, y, c) in [(3, 2, "sage1"), (8, 1, "sage2"), (5, 6, "sage2"), (10, 5, "sage1"), (2, 8, "sage2"), (11, 9, "sage2"), (7, 9, "sage1")]:
        s.ellipse(x, y, x + 4, y + 4, c)
    for (x, y) in [(9, 2), (6, 7), (3, 9), (12, 10)]:
        s.px(x, y, "sage3")
    s.rect(4, 13, 11, 20, "terra1")
    s.rect(3, 13, 12, 15, "terra2")
    s.hline(3, 12, 15, "terra0")
    s.vline(11, 16, 20, "terra0")
    s.outline()
    return s.save("plant-pot")


def hanging_plant():
    s = Sprite(18, 28)
    s.vline(8, 0, 4, "steel1"); s.vline(9, 0, 4, "steel1")
    # leafy crown spilling over the pot
    for (x, y, c) in [(1, 4, "sage1"), (5, 3, "sage2"), (10, 3, "sage1"), (13, 5, "sage2"), (3, 7, "sage2"), (11, 7, "sage2")]:
        s.ellipse(x, y, x + 4, y + 4, c)
    s.rect(5, 7, 12, 11, "cream1"); s.hline(5, 12, 7, "cream2"); s.hline(5, 12, 11, "cream0")
    # trailing vines: chunky leaf pairs hanging down
    for vx, top, length in [(3, 11, 13), (7, 12, 15), (11, 12, 11), (14, 10, 9)]:
        s.vline(vx, top, top + length, "sage0")
        for k in range(0, length, 3):
            c = "sage2" if (k // 3) % 2 else "sage1"
            s.px(vx - 1, top + k + 1, c); s.px(vx + 1, top + k + 2, c)
            s.px(vx, top + k + 1, "sage3" if k % 6 == 0 else c)
    s.outline()
    return s.save("hanging-plant")


def pendant_lamp():
    s = Sprite(12, 20)
    s.vline(5, 0, 9, "steel0"); s.vline(6, 0, 9, "steel0")
    s.rect(1, 10, 10, 14, "sage1")
    s.hline(2, 9, 10, "sage2")
    s.rect(4, 15, 7, 16, "gold2")
    s.outline()
    return s.save("pendant-lamp")


ALL = [counter, pastry_case, espresso_machine, menu_board, piano_upright, record_player,
       lambda: chair("front"), lambda: chair("back"), stool, table_round, table_square,
       cup, cake_stand, plant_pot, hanging_plant, pendant_lamp]


def contact_sheet(images, path, scale=6, cols=6):
    pad = 4
    cw = max(i.width for i in images) + pad * 2
    ch = max(i.height for i in images) + pad * 2
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows), (234, 222, 199, 255))
    for n, im in enumerate(images):
        cx = (n % cols) * cw + (cw - im.width) // 2
        cy = (n // cols) * ch + ch - pad - im.height  # sit on a shared "floor" line per row
        sheet.alpha_composite(im, (cx, cy))
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST).save(path)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    images = [f() for f in ALL]
    print(f"{len(images)} assets -> {OUT}")
    if "--preview" in sys.argv:
        os.makedirs(os.path.join(ART, "preview"), exist_ok=True)
        contact_sheet(images, os.path.join(ART, "preview", "assets-sheet.png"))

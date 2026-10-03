"""Avatar sprite sheets: a small chibi café visitor, in layers the site recolours per person.

Frames (16 x 28 px each, left to right):
  0 front idle   1 front step A   2 front step B   (facing you, to the left)
  3 back idle    4 back step A    5 back step B    (facing away, to the right)
  6 front sit    7 back sit
Mirroring gives the other two directions, like the furniture.

Layers, each a sheet of the 8 frames:
  body.png         skin, shirt, trousers, shoes, eyes
  hair-<style>.png one per hairstyle (rows: front frames, back frames, sit frames)
  apron.png        the barista's apron
Colours in the sheets are KEYS (see KEYS) that the site swaps for each visitor's palette; the
dark outline is added after compositing, so it hugs hair and apron too.

    python3 art/draw_avatar.py [--preview out.png]
"""
import json
import math
import os
import random
import sys

from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "avatar")
FW, FH = 16, 28
FRAMES = ["front", "front-a", "front-b", "back", "back-a", "back-b", "front-sit", "back-sit"]
FOOT = (8, 26)  # where the avatar stands on the floor, in a frame

KEYS = {
    "skin0": (250, 0, 1), "skin1": (250, 0, 2), "skin2": (250, 0, 3),
    "hair0": (250, 1, 0), "hair1": (250, 2, 0), "hair2": (250, 3, 0),
    "shirt0": (0, 250, 1), "shirt1": (0, 250, 2), "shirt2": (0, 250, 3),
    "pants0": (1, 0, 250), "pants1": (2, 0, 250),
    "shoe": (3, 0, 250),
    "apron0": (250, 250, 1), "apron1": (250, 250, 2), "apron2": (250, 250, 3),
}
EYE = (36, 20, 13)
BLUSH = (232, 140, 130)
STYLES = ["short", "long", "bun", "curly", "buzz"]


class Frame:
    def __init__(self):
        self.im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))

    def px(self, x, y, key):
        x, y = int(x), int(y)
        if 0 <= x < FW and 0 <= y < FH:
            col = KEYS[key] if isinstance(key, str) else key
            self.im.putpixel((x, y), col + (255,))


def head_cells(dy=0):
    """Pixels of the head: a soft circle centred on (7.5, 6.5)."""
    cells = []
    for y in range(1, 12):
        for x in range(2, 14):
            if ((x + 0.5 - 7.5) / 5.0) ** 2 + ((y + 0.5 - 6.5) / 5.2) ** 2 <= 1:
                cells.append((x, y + dy))
    return cells


def body(f, kind, step, dy):
    front = kind == "front"
    sit = step == "sit"
    # legs and shoes first (behind the torso when sitting)
    if sit:
        if front:  # thighs come toward you and to the left, shins hang down
            for x in range(3, 10):
                f.px(x, 17 + dy, "pants1"); f.px(x, 18 + dy, "pants0")
            for y in range(19, 22):
                f.px(3, y + dy, "pants1"); f.px(4, y + dy, "pants0")
                f.px(6, y + dy, "pants1"); f.px(7, y + dy, "pants0")
            for x in (2, 3, 4, 5, 6, 7):
                f.px(x, 22 + dy, "shoe")
        else:  # from behind, just the seat of the trousers shows
            for x in range(5, 12):
                f.px(x, 17 + dy, "pants0")
    else:
        lift = {"": (0, 0), "a": (0, 1), "b": (1, 0)}[step]
        for leg, (x0, up) in enumerate(((5, lift[0]), (9, lift[1]))):
            for y in range(17, 22 - up):
                f.px(x0, y + dy, "pants1" if leg == 0 else "pants0")
                f.px(x0 + 1, y + dy, "pants0")
            sy = 22 - up + dy
            toe = -1 if front else 1
            f.px(x0, sy, "shoe"); f.px(x0 + 1, sy, "shoe")
            f.px(x0 + (2 if toe > 0 else -1), sy, "shoe")
    # torso: lit from the top-left
    for y in range(11, 17):
        for x in range(4, 12):
            key = "shirt2" if x < 6 and y < 14 else ("shirt0" if x > 9 else "shirt1")
            f.px(x, y + dy, key)
    # arms swing a little when walking
    swing = {"": 0, "a": 1, "b": -1, "sit": 0}[step]
    for side, x in ((-1, 3), (1, 12)):
        off = swing * side
        for y in range(12, 15):
            f.px(x, y + dy + (off if y > 12 else 0), "shirt1" if side < 0 else "shirt0")
        f.px(x, 15 + dy + off, "skin1")  # hand
    # neck and head
    f.px(7, 10 + dy, "skin0"); f.px(8, 10 + dy, "skin0")
    for (x, y) in head_cells(dy):
        shade = (x + 0.5 - 7.5) + (y - dy + 0.5 - 6.5) * 0.6
        f.px(x, y, "skin2" if shade < -3 else ("skin0" if shade > 3 else "skin1"))
    if front:  # face looks a little to the left
        f.px(5, 7 + dy, EYE); f.px(8, 7 + dy, EYE)
        f.px(4, 9 + dy, BLUSH); f.px(9, 9 + dy, BLUSH)


def hair(f, style, kind, dy):
    front = kind == "front"
    head = set(head_cells(dy))
    for (x, y) in head:
        yy = y - dy
        if front:
            # fringe across the forehead, the back and sides of the head covered
            cover = yy <= 4 or (yy <= 6 and (x <= 3 or x >= 11)) or x >= 12 or (yy <= 8 and x >= 11)
            if style == "buzz":
                cover = yy <= 3 or (x >= 12 and yy <= 7)
        else:
            cover = yy <= 10 if style != "buzz" else yy <= 9
        if cover:
            lit = (x + 0.5 - 7.5) + (yy + 0.5 - 6.5) * 0.8
            f.px(x, y, "hair2" if lit < -3.5 else ("hair0" if lit > 2.5 else "hair1"))
    if style == "long":  # falls past the shoulders
        cols = (2, 3, 11, 12) if front else range(3, 13)
        for x in cols:
            for y in range(8, 15 if front else 13):
                f.px(x, y + dy, "hair0" if x in (2, 12) or y > 13 else "hair1")
    if style == "bun":
        cx, cy = (10, 0) if front else (7.5, 0)
        for y in range(-2, 3):
            for x in range(-2, 3):
                if x * x + y * y <= 5:
                    f.px(cx + x, cy + y + 1 + dy, "hair2" if x + y < -1 else "hair1")
    if style == "curly":  # bumpy outline a pixel bigger than the head
        for a in range(0, 360, 20):
            r = 5.6 + (0.6 if (a // 20) % 2 else 0)
            x = 7.5 + math.cos(math.radians(a)) * r
            y = 6.0 + math.sin(math.radians(a)) * r * 0.95
            if (front and (y < 6.5 + dy - dy or x > 10.5)) or (not front and y < 11):
                f.px(x, y + dy, "hair1" if a < 180 else "hair0")


def apron(f, kind, step, dy):
    if kind == "front":
        for y in range(12, 21 if step != "sit" else 17):
            for x in range(5, 11):
                if y == 12 and x not in (6, 9):
                    continue  # bib straps
                f.px(x, y + dy, "apron2" if x == 5 else ("apron0" if x == 10 else "apron1"))
        f.px(7, 15 + dy, "apron0"); f.px(8, 15 + dy, "apron0")  # pocket
    else:  # ties at the back of the waist
        for x in range(4, 12):
            f.px(x, 16 + dy, "apron1")
        f.px(7, 17 + dy, "apron0"); f.px(8, 17 + dy, "apron0"); f.px(6, 18 + dy, "apron1"); f.px(9, 18 + dy, "apron1")


def sheet(draw):
    out = Image.new("RGBA", (FW * len(FRAMES), FH), (0, 0, 0, 0))
    for i, name in enumerate(FRAMES):
        kind = "front" if name.startswith("front") else "back"
        step = "sit" if name.endswith("sit") else (name[-1] if name[-2:] in ("-a", "-b") else "")
        dy = 3 if step == "sit" else (-1 if step in ("a", "b") else 0)  # bob up mid-stride, sink when seated
        f = Frame()
        draw(f, kind, step, dy)
        out.alpha_composite(f.im, (i * FW, 1))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet(body).save(os.path.join(OUT, "body.png"))
    for st in STYLES:
        sheet(lambda f, k, s, dy, st=st: hair(f, st, k, dy)).save(os.path.join(OUT, f"hair-{st}.png"))
    sheet(apron).save(os.path.join(OUT, "apron.png"))
    json.dump({"frame": [FW, FH], "frames": FRAMES, "foot": [FOOT[0], FOOT[1] + 1], "styles": STYLES,
               "keys": {k: "#%02x%02x%02x" % v for k, v in KEYS.items()}},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    print("avatar sheets ->", OUT)


# ---- preview: recolour like the site does and outline, for a few random visitors
def recolour(im, pal):
    px = im.load()
    rev = {v: k for k, v in KEYS.items()}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            k = rev.get((r, g, b))
            if a and k:
                px[x, y] = pal[k] + (255,)
    return im


def preview(path):
    rng = random.Random(3)
    skins = [((141, 85, 54), (176, 112, 74), (204, 140, 98)), ((222, 168, 128), (240, 196, 158), (252, 220, 186)), ((96, 58, 38), (128, 80, 52), (156, 104, 70))]
    hairs = [((40, 26, 20), (66, 44, 30), (98, 66, 44)), ((150, 80, 40), (190, 110, 55), (225, 150, 80)), ((20, 20, 26), (36, 36, 46), (60, 60, 74)), ((214, 170, 90), (240, 206, 130), (252, 232, 170))]
    shirts = [((70, 90, 60), (100, 128, 82), (134, 164, 104)), ((140, 60, 50), (176, 82, 66), (210, 112, 90)), ((50, 62, 110), (72, 88, 150), (104, 122, 186)), ((200, 170, 120), (226, 200, 150), (244, 226, 190))]
    rows = []
    for k in range(5):
        s, h, c = rng.choice(skins), rng.choice(hairs), rng.choice(shirts)
        pal = {"skin0": s[0], "skin1": s[1], "skin2": s[2], "hair0": h[0], "hair1": h[1], "hair2": h[2],
               "shirt0": c[0], "shirt1": c[1], "shirt2": c[2], "pants0": (46, 40, 52), "pants1": (66, 58, 74), "shoe": (40, 26, 20),
               "apron0": (40, 70, 52), "apron1": (56, 96, 70), "apron2": (80, 124, 92)}
        layers = [Image.open(os.path.join(OUT, "body.png")).convert("RGBA"), Image.open(os.path.join(OUT, f"hair-{STYLES[k % len(STYLES)]}.png")).convert("RGBA")]
        if k == 0:
            layers.append(Image.open(os.path.join(OUT, "apron.png")).convert("RGBA"))
        comp = Image.new("RGBA", layers[0].size, (0, 0, 0, 0))
        for L in layers:
            comp.alpha_composite(L)
        comp = recolour(comp, pal)
        a = comp.getchannel("A").load()
        o = comp.copy()
        for y in range(comp.height):
            for x in range(comp.width):
                if not a[x, y] and any(0 <= x + dx < comp.width and 0 <= y + dy < comp.height and a[x + dx, y + dy] and (x + dx) // FW == x // FW for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    o.putpixel((x, y), (36, 20, 13, 255))
        rows.append(o)
    sheetp = Image.new("RGBA", (rows[0].width, FH * len(rows)), (205, 140, 85, 255))
    for i, r in enumerate(rows):
        sheetp.alpha_composite(r, (0, i * FH))
    sheetp.resize((sheetp.width * 5, sheetp.height * 5), Image.NEAREST).save(path)


if __name__ == "__main__":
    main()
    if "--preview" in sys.argv:
        preview(sys.argv[-1])

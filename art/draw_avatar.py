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
FW, FH = 20, 32
FRAMES = ["front", "front-a", "front-b", "back", "back-a", "back-b", "front-sit", "back-sit"]
FOOT = (10, 30)  # where the avatar stands on the floor, in a frame (shoes end on row 30)

KEYS = {
    "skin0": (250, 0, 1), "skin1": (250, 0, 2), "skin2": (250, 0, 3),
    "hair0": (250, 1, 0), "hair1": (250, 2, 0), "hair2": (250, 3, 0),
    "shirt0": (0, 250, 1), "shirt1": (0, 250, 2), "shirt2": (0, 250, 3),
    "pants0": (1, 0, 250), "pants1": (2, 0, 250),
    "shoe": (3, 0, 250),
    "apron0": (250, 250, 1), "apron1": (250, 250, 2), "apron2": (250, 250, 3),
}
EYE = (36, 20, 13)
WHITE = (255, 250, 240)
MOUTH = (120, 50, 40)
BLUSH = (240, 150, 140)
STYLES = ["short", "long", "bun", "curly", "buzz"]


class Frame:
    def __init__(self):
        self.im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))

    def px(self, x, y, key):
        x, y = int(x), int(y)
        if 0 <= x < FW and 0 <= y < FH:
            col = KEYS[key] if isinstance(key, str) else key
            self.im.putpixel((x, y), col + (255,))


HEAD_C = (10.0, 8.6)  # a big round head (chibi: about half the height)
HEAD_R = (7.3, 6.9)
SIT_DY = 4  # how far the whole figure sinks when sitting
SIT_LIFT = 5  # px from the seat of the sitting frame to its foot point


def head_cells(dy=0):
    cells = []
    for y in range(0, 17):
        for x in range(1, 19):
            if ((x + 0.5 - HEAD_C[0]) / HEAD_R[0]) ** 2 + ((y + 0.5 - HEAD_C[1]) / HEAD_R[1]) ** 2 <= 1:
                cells.append((x, y + dy))
    return cells


def body(f, kind, step, dy):
    """A tiny body under a big round head, turned three-quarters toward the viewer's left
    (front) or away to the right (back). Lit from the top-left like the room."""
    front = kind == "front"
    sit = step == "sit"
    # ---- legs and shoes (short and stubby)
    if sit:
        if front:  # little legs stick forward off the seat
            for x in range(6, 12):
                f.px(x, 23 + dy, "pants1"); f.px(x, 24 + dy, "pants0")
            for x0 in (6, 9):
                f.px(x0, 25 + dy, "pants1"); f.px(x0 + 1, 25 + dy, "pants0")
                for k in (-1, 0, 1):
                    f.px(x0 + k, 26 + dy, "shoe")
        else:
            for x in range(8, 13):
                f.px(x, 23 + dy, "pants0")
    else:
        fwd = {"": (0, 0), "a": (1, 0), "b": (0, 1)}[step]
        toe = -1 if front else 1
        for leg, x0 in enumerate((8, 11)):
            reach, lift = fwd[leg], fwd[1 - leg]
            shift = toe * reach
            for y in range(23, 28 - lift):
                f.px(x0 + shift, y + dy, "pants1" if leg == 0 else "pants0")
                f.px(x0 + 1 + shift, y + dy, "pants0")
            for row in (28 - lift, 29 - lift):  # round little shoes, toe the way you face
                for k in (0, 1):
                    f.px(x0 + k + shift, row + dy, "shoe")
                f.px(x0 + shift + (2 if toe > 0 else -1), 29 - lift + dy, "shoe")
    # ---- torso: small and round-bottomed
    for y in range(16, 23):
        x0, x1 = (7, 12) if 17 <= y <= 21 else (8, 11)
        for x in range(x0, x1 + 1):
            key = "shirt2" if (x <= x0 + 1 and y < 19) else ("shirt0" if x == x1 or y == 22 else "shirt1")
            f.px(x, y + dy, key)
    # ---- arms: little nubs with round hands, swinging when walking
    swing = {"": 0, "a": 1, "b": -1, "sit": 0}[step]
    for side, x in ((-1, 6), (1, 13)):
        off = swing * side
        for y in (17, 18, 19):
            f.px(x, y + dy + (off if y > 17 else 0), "shirt1" if side < 0 else "shirt0")
        f.px(x, 20 + dy + off, "skin1" if side < 0 else "skin0")
    # ---- head
    for (x, y) in head_cells(dy):
        u = (x + 0.5 - HEAD_C[0]) / HEAD_R[0]
        v = (y - dy + 0.5 - HEAD_C[1]) / HEAD_R[1]
        light = -u * 0.8 - v * 0.6
        f.px(x, y, "skin2" if light > 0.5 else ("skin0" if (u > 0.78 or v > 0.86) else "skin1"))
    if front:
        # big eyes with a highlight, looking a little to the viewer's left
        for ex in (6, 11):
            for yy in (9, 10, 11):
                f.px(ex, yy + dy, EYE); f.px(ex + 1, yy + dy, EYE)
            f.px(ex, 9 + dy, WHITE)  # sparkle
        for bx in (4, 5, 13, 14):
            f.px(bx, 12 + dy, BLUSH)
        f.px(9, 13 + dy, MOUTH); f.px(10, 13 + dy, MOUTH)


def hair(f, style, kind, dy):
    """Hair with volume: it puffs a pixel out past the head. Front: a soft fringe with a
    ragged edge and the far side covered; back: the whole head."""
    front = kind == "front"
    cx, cy = HEAD_C
    rx, ry = HEAD_R[0] + 1.0, HEAD_R[1] + 0.8  # a little bigger than the head
    tone = lambda x, y: ("hair2" if (x + 0.5 - cx) * 0.8 + (y + 0.5 - cy) * 0.6 < -3.2 else
                         ("hair0" if (x + 0.5 - cx) * 0.8 + (y + 0.5 - cy) * 0.6 > 3.0 else "hair1"))
    for y in range(-1, 17):
        for x in range(0, 20):
            u = (x + 0.5 - cx) / rx
            v = (y + 0.5 - cy) / ry
            if u * u + v * v > 1:
                continue
            if front:
                fringe = 6 + (1 if x % 3 == 1 else 0) - (1 if x in (9, 10) else 0)  # soft, a little parted
                cover = y <= fringe or (x >= 15 and y <= 11) or (x <= 3 and y <= 9)
                if style == "buzz":
                    cover = y <= 4 or (x >= 16 and y <= 9)
                if style == "long":
                    cover = cover or x <= 3 or x >= 16
            else:
                cover = y <= (14 if style != "buzz" else 11)
            if cover:
                f.px(x, y + dy, tone(x, y))
    if style == "long":  # falls to the shoulders, behind the arms
        for x in ((2, 3, 16, 17) if front else range(4, 16)):
            for y in range(12, 21 if front else 18):
                f.px(x, y + dy, "hair0" if x in (2, 17) or y > 19 else "hair1")
    if style == "bun":
        bx, by = (14, 0) if front else (10, -1)
        for y in range(-3, 3):
            for x in range(-3, 3):
                if x * x + y * y <= 7:
                    f.px(bx + x, by + y + dy, "hair2" if x + y < -2 else ("hair0" if x + y > 1 else "hair1"))
    if style == "curly":  # a halo of round curls
        import math
        for a in range(0, 360, 24):
            ang = math.radians(a)
            px_, py_ = cx + math.cos(ang) * rx - 0.5, cy + math.sin(ang) * ry - 0.5
            if front and not (py_ < cy - 1.5 or px_ > cx + 3):
                continue
            if not front and py_ > cy + 5:
                continue
            for ox, oy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
                f.px(round(px_) + ox, round(py_) + oy + dy, "hair2" if (ox, oy) in ((-1, 0), (0, -1)) else ("hair0" if oy > 0 else "hair1"))


def apron(f, kind, step, dy):
    if kind == "front":
        for y in range(17, 25 if step != "sit" else 23):
            for x in range(8, 12):
                f.px(x, y + dy, "apron2" if x == 8 else ("apron0" if x == 11 else "apron1"))
        for x in (8, 11):
            f.px(x, 16 + dy, "apron1")
    else:
        for x in range(7, 13):
            f.px(x, 22 + dy, "apron1")


def sheet(draw):
    out = Image.new("RGBA", (FW * len(FRAMES), FH), (0, 0, 0, 0))
    for i, name in enumerate(FRAMES):
        kind = "front" if name.startswith("front") else "back"
        step = "sit" if name.endswith("sit") else (name[-1] if name[-2:] in ("-a", "-b") else "")
        dy = SIT_DY if step == "sit" else (-1 if step in ("a", "b") else 0)  # bob up mid-stride, sink when seated
        f = Frame()
        draw(f, kind, step, dy)
        out.alpha_composite(f.im, (i * FW, 1))  # one row of headroom for hair
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet(body).save(os.path.join(OUT, "body.png"))
    for st in STYLES:
        sheet(lambda f, k, s, dy, st=st: hair(f, st, k, dy)).save(os.path.join(OUT, f"hair-{st}.png"))
    sheet(apron).save(os.path.join(OUT, "apron.png"))
    json.dump({"frame": [FW, FH], "frames": FRAMES, "foot": [FOOT[0], FOOT[1] + 1], "styles": STYLES, "sitLift": SIT_LIFT,
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

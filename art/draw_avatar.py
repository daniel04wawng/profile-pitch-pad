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
FOOT = (8, 26)  # where the avatar stands on the floor, in a frame (shoes on row 25)

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


HEAD_C = (8.0, 6.6)  # centre of the (big, chibi) head
HEAD_R = (5.4, 5.6)


def head_cells(dy=0):
    """Pixels of the head: a big soft circle, wider than the body."""
    cells = []
    for y in range(0, 13):
        for x in range(1, 15):
            if ((x + 0.5 - HEAD_C[0]) / HEAD_R[0]) ** 2 + ((y + 0.5 - HEAD_C[1]) / HEAD_R[1]) ** 2 <= 1:
                cells.append((x, y + dy))
    return cells


def body(f, kind, step, dy):
    """Narrow body under a big head, turned three-quarters toward the viewer's left (front) or
    away to the right (back). Lit from the top-left like the room."""
    front = kind == "front"
    sit = step == "sit"
    # ---- legs and shoes
    if sit:
        if front:  # thighs forward (toward the viewer's left), shins hanging down
            for x in range(4, 10):
                f.px(x, 19 + dy, "pants1"); f.px(x, 20 + dy, "pants0")
            for x0 in (4, 7):
                for y in range(21, 23):
                    f.px(x0, y + dy, "pants1"); f.px(x0 + 1, y + dy, "pants0")
                f.px(x0 - 1, 23 + dy, "shoe"); f.px(x0, 23 + dy, "shoe"); f.px(x0 + 1, 23 + dy, "shoe")
        else:
            for x in range(6, 11):
                f.px(x, 19 + dy, "pants0")
    else:
        # step "a": near leg forward, far leg lifted; "b": the other way round
        fwd = {"": (0, 0), "a": (1, 0), "b": (0, 1)}[step]
        toe = -1 if front else 1
        for leg, x0 in enumerate((5, 9)):
            reach = fwd[leg]
            lift = fwd[1 - leg]
            shift = toe * reach  # a forward leg reaches toward where you're facing
            for y in range(19, 25 - lift):
                f.px(x0 + shift, y + dy, "pants1" if leg == 0 else "pants0")
                f.px(x0 + 1 + shift, y + dy, "pants0")
            sy = 25 - lift + dy
            for k in (0, 1):
                f.px(x0 + k + shift, sy, "shoe")
            f.px(x0 + shift + (2 if toe > 0 else -1), sy, "shoe")  # toe points the way you face
    # ---- torso: narrow, a little wider at the shoulders, lit on the left
    for y in range(13, 19):
        x0, x1 = (5, 10) if y > 13 else (6, 9)
        for x in range(x0, x1 + 1):
            key = "shirt2" if (x <= x0 + 1 and y < 16) else ("shirt0" if x == x1 else "shirt1")
            f.px(x, y + dy, key)
    # ---- arms: thin, separate from the body, swinging when walking
    swing = {"": 0, "a": 1, "b": -1, "sit": 0}[step]
    for side, x in ((-1, 4), (1, 11)):
        off = swing * side
        for y in range(14, 17):
            f.px(x, y + dy + (off if y > 14 else 0), "shirt1" if side < 0 else "shirt0")
        f.px(x, 17 + dy + off, "skin1" if side < 0 else "skin0")  # hand
    # ---- neck and head
    f.px(7, 12 + dy, "skin0"); f.px(8, 12 + dy, "skin0")
    for (x, y) in head_cells(dy):
        u = (x + 0.5 - HEAD_C[0]) / HEAD_R[0]
        v = (y - dy + 0.5 - HEAD_C[1]) / HEAD_R[1]
        light = -u * 0.8 - v * 0.6
        f.px(x, y, "skin2" if light > 0.55 else ("skin0" if (u > 0.72 or v > 0.82) else "skin1"))
    if front:
        # three-quarter face, looking to the viewer's left: features shifted left, an ear right
        for ex in (5, 8):
            f.px(ex, 7 + dy, EYE); f.px(ex, 8 + dy, EYE)
        f.px(4, 9 + dy, BLUSH); f.px(9, 9 + dy, BLUSH)
        f.px(6, 10 + dy, "skin0")  # mouth
        f.px(12, 8 + dy, "skin0"); f.px(12, 7 + dy, "skin1")  # ear
    else:
        f.px(3, 8 + dy, "skin0")  # ear on the other side, seen from behind


def hair(f, style, kind, dy):
    """Hairstyles drawn over the head. Front: a fringe with a ragged edge, the back and the far
    side of the head covered. Back: the whole head."""
    front = kind == "front"
    cx, cy = HEAD_C
    lit = lambda x, y: (x + 0.5 - cx) * 0.8 + (y + 0.5 - cy) * 0.6  # lower = more lit
    tone = lambda x, y: "hair2" if lit(x, y) < -2.6 else ("hair0" if lit(x, y) > 2.4 else "hair1")
    head = set(head_cells(dy))
    for (x, y) in head:
        yy = y - dy
        if front:
            fringe = 4 + ((x * 7) % 3 == 0)  # ragged lower edge of the fringe
            cover = yy <= fringe or x >= 12 or (x <= 3 and yy <= 8) or (x >= 11 and yy <= 9)
            if style == "buzz":
                cover = yy <= 3 or (x >= 12 and yy <= 6)
            if style == "long":
                cover = cover or x <= 3
        else:
            cover = yy <= (10 if style != "buzz" else 8) or (style == "long")
        if cover:
            f.px(x, y, tone(x, yy))
    if style == "short" and front:  # a couple of loose strands over the forehead
        f.px(6, 6 + dy, "hair1"); f.px(9, 5 + dy, "hair0")
    if style == "long":  # falls past the shoulders, behind the arms
        cols = (2, 3, 12, 13) if front else range(4, 13)
        for x in cols:
            for y in range(9, 16 if front else 13):
                f.px(x, y + dy, "hair0" if x in (2, 13) or y > 14 else "hair1")
    if style == "bun":
        bx, by = (11, 0) if front else (8, 0)
        for y in range(-2, 3):
            for x in range(-2, 3):
                if x * x + y * y <= 5:
                    f.px(bx + x, by + y + dy, "hair2" if x + y < -1 else ("hair0" if x + y > 1 else "hair1"))
    if style == "curly":  # a full mop: round bumps all over the top and sides
        import math
        for a in range(0, 360, 30):
            ang = math.radians(a)
            bx = cx + math.cos(ang) * HEAD_R[0] * 0.95 - 0.5
            by = cy + math.sin(ang) * HEAD_R[1] * 0.95 - 0.5
            if front and not (by < cy - 1 or bx > cx + 2.5):
                continue  # keep the face clear
            if not front and by > cy + 4:
                continue
            for ox, oy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
                x, y = round(bx) + ox, round(by) + oy
                f.px(x, y + dy, "hair2" if (ox, oy) == (-1, 0) or (ox, oy) == (0, -1) else ("hair0" if oy > 0 else "hair1"))


def apron(f, kind, step, dy):
    if kind == "front":
        for y in range(14, 22 if step != "sit" else 19):
            for x in range(5, 11):
                f.px(x, y + dy, "apron2" if x == 5 else ("apron0" if x == 10 else "apron1"))
        for x in (6, 9):
            f.px(x, 13 + dy, "apron1")  # straps
        f.px(7, 17 + dy, "apron0"); f.px(8, 17 + dy, "apron0")  # pocket
    else:  # ties at the back of the waist
        for x in range(5, 11):
            f.px(x, 18 + dy, "apron1")
        f.px(7, 19 + dy, "apron0"); f.px(8, 19 + dy, "apron0"); f.px(6, 20 + dy, "apron1"); f.px(9, 20 + dy, "apron1")


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

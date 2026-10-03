"""Doorways in the room's palette, in the same wood frame:
  kitchen-doorway  warm light inside, one kitchen shelf
  changing-room    a velvet curtain on a brass rod (where visitors change their look)
  front-door       the café's way in: glass panes (showing the live sky, like the windows),
                   a wood panel, brass handle and kick plate, an OPEN sign
  front-door-open  the same door swung open, the street outside showing through

Drawn for the back-left wall (their top and bottom edges rise to the right, 1px per 2px);
the editor turns them to face whichever wall they're on.

    python3 art/draw_door.py   # writes public/cafe/sprites/<name>.png
"""
import math
import os

from PIL import Image

from draw_room import P, BAYER

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")

W, H = 26, 50  # outer width and height of the frame (px)
F = 3  # frame thickness


GLOW = ["glow", "wall4", "shine1"]  # inside the kitchen doorway: warm, brightest near the floor
CURTAIN = [(74, 29, 18, 255), (110, 44, 26, 255), (148, 64, 42, 255), (184, 90, 58, 255)]  # rust velvet
BRASS = [(138, 95, 34, 255), (201, 150, 63, 255), (240, 198, 108, 255)]


def kitchen(x, z, y):
    level = 2.2 * (1 - z / (H - F)) ** 0.7
    i = int(level)
    if i < 2 and (level - i) * 16 > BAYER[y % 4][x % 4]:
        i += 1
    c = GLOW[min(i, 2)]
    if x == F or z == H - F - 1:
        c = "deep1"  # shadow just inside the frame
    elif z in (30, 31) and F + 2 <= x < W - F - 4:
        c = "panel1" if z == 30 else "deep1"  # one kitchen shelf, nothing more
    return P[c]


def curtain(x, z, y):
    top = H - F - 1
    if z >= top - 1:
        return BRASS[2] if z == top else BRASS[1]  # the rod
    if z == top - 2 and x % 2:
        return BRASS[0]  # rings
    # folds: soft vertical waves, lit from the left, a little gathered toward the top
    t = (x - F) / (W - 2 * F)
    fold = math.sin(t * math.pi * 5 + 0.6) + 0.15 * (1 - z / top)
    k = 3 if fold > 0.6 else (2 if fold > -0.1 else (1 if fold > -0.7 else 0))
    if x == F:
        k = 0  # shadow inside the frame
    if z < 2 and (x % 3 == 0):
        return None  # the hem sways a little off the floor
    return CURTAIN[k]


SKY = "sky"  # an inside_fn may answer this: left clear, and marked in the sky mask
CREAM = (240, 226, 196, 255)
SIGN_RED = (168, 52, 42, 255)
STREET = [(46, 50, 70, 255), (66, 72, 96, 255), (98, 104, 128, 255)]  # pavement under the night sky


def front_door(x, z, y):
    top = H - F - 1
    if z < 2:
        return BRASS[1] if z == 1 else BRASS[0]  # kick plate
    if x == F:
        return P["panel2"]  # lit edge of the door leaf
    if x == W - F - 1:
        return P["panel0"]
    if 18 <= z <= 20 and x in (W - F - 3, W - F - 4):
        return BRASS[2] if z == 20 else BRASS[1]  # handle
    if 22 <= z < top - 2 and F + 2 <= x < W - F - 2:
        mid = (F + W - F) // 2
        if x == mid or z == 33:
            return P["panel1"]  # glazing bars
        if 36 <= z <= 39 and mid - 4 <= x <= mid + 3:  # the OPEN sign hanging in the glass
            if z in (36, 39) or x in (mid - 4, mid + 3):
                return CREAM
            return SIGN_RED if (x + z) % 2 == 0 else CREAM
        if z == 40 and x in (mid - 3, mid + 2):
            return P["deep0"]  # its string
        return SKY
    if 4 <= z < 18 and F + 2 <= x < W - F - 2:  # a framed wood panel
        edge = z in (4, 17) or x in (F + 2, W - F - 3)
        return P["panel0"] if edge else P["panel1"]
    return P["panel2"] if z >= top - 1 else P["panel1"]


def front_door_open(x, z, y):
    top = H - F - 1
    if x < F + 4:  # the door leaf, swung in against the frame, seen edge-on
        if x == F:
            return P["panel2"]
        if 22 <= z < top - 2 and x == F + 2:
            return SKY
        return BRASS[1] if (18 <= z <= 20 and x == F + 3) else (P["panel1"] if x < F + 3 else P["panel0"])
    if z < 8:  # the pavement outside
        k = 2 if z > 5 else (1 if z > 2 else 0)
        return STREET[k]
    return SKY


def draw(name, inside_fn):
    im = Image.new("RGBA", (W + 2, H + W // 2 + 2), (0, 0, 0, 0))
    sky = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for x in range(W):
        bottom = H + W // 2 - x // 2  # floor line on the wall at this column
        for z in range(H):
            y = bottom - z
            inside = F <= x < W - F and z < H - F
            if not inside:
                # frame: lit left edge, darker right, a lintel on top
                if z >= H - F:
                    c = "panel2" if z == H - 1 else "panel1"
                elif x < F:
                    c = "rail" if x == 0 else "panel2"
                else:
                    c = "panel1" if x == W - 1 else "panel0"
            else:
                col = inside_fn(x, z, y)
                if col == SKY:
                    sky.putpixel((x + 1, y + 1), (255, 255, 255, 255))
                    continue
                if col is None:
                    col = P["deep0"]  # the dark room behind the curtain
                im.putpixel((x + 1, y + 1), col)
                continue
            im.putpixel((x + 1, y + 1), P[c])
    # 1px dark edge
    src = im.copy()
    a = src.getchannel("A").load()
    glass = sky.getchannel("A").load()
    for y in range(im.height):
        for x in range(im.width):
            if not a[x, y] and not glass[x, y] and any(0 <= x + dx < im.width and 0 <= y + dy < im.height and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), (36, 20, 13, 255))
    bbox = im.getbbox()
    im = im.crop(bbox)
    im.save(os.path.join(OUT, f"{name}.png"))
    if sky.getbbox():
        # glass: the engine paints the live sky here (see Stage), like the windows
        sky.crop(bbox).save(os.path.join(OUT, f"{name}.sky.png"))
        import json
        path = os.path.join(OUT, "_companions.json")
        comp = json.load(open(path))
        comp[name] = {**comp.get(name, {}), "sky": f"sprites/{name}.sky.png"}
        json.dump(comp, open(path, "w"), indent=1)
    print(name, im.size)


if __name__ == "__main__":
    draw("kitchen-doorway", kitchen)
    draw("changing-room", curtain)
    draw("front-door", front_door)
    draw("front-door-open", front_door_open)

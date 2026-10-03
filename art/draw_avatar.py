"""Avatar sprite sheets, hand-placed pixel by pixel after Daniel's reference: a front-facing
little person with messy hair, big eyes with whites, short-sleeved tee, baggy trousers and
chunky sneakers. Drawn in layers the site recolours per visitor.

Frames (20 x 40 px each, left to right):
  0 front idle   1 front step A   2 front step B   (facing you)
  3 back idle    4 back step A    5 back step B    (facing away)
  6 front sit    7 back sit
Facing left or right is the same art mirrored.

Layers, each a sheet of the 8 frames:
  body.png         skin, face, tee, trousers, sneakers
  hair-<style>.png one per hairstyle
  apron.png        (unused for now: the barista is Daniel's own look)
Colours in the sheets are KEYS the site swaps for each visitor's palette; the dark outline
is added after compositing so it hugs the hair too.

    python3 art/draw_avatar.py [--preview out.png]
"""
import json
import os
import random
import sys

from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "avatar")
FW, FH = 20, 40
FRAMES = ["front", "front-a", "front-b", "back", "back-a", "back-b", "front-sit", "back-sit"]
FOOT = (10, 35)  # where the avatar stands on the floor, in a frame
TOP = 3  # rows of headroom above the art for tall hair
SIT_DY = 6  # how far the figure sinks when sitting
STYLES = ["messy", "long", "bun", "curly", "buzz"]

KEYS = {
    "skin0": (250, 0, 1), "skin1": (250, 0, 2), "skin2": (250, 0, 3),
    "hair0": (250, 1, 0), "hair1": (250, 2, 0), "hair2": (250, 3, 0),
    "shirt0": (0, 250, 1), "shirt1": (0, 250, 2), "shirt2": (0, 250, 3),
    "pants0": (1, 0, 250), "pants1": (2, 0, 250),
    "shoe": (3, 0, 250),
    "apron0": (250, 250, 1), "apron1": (250, 250, 2), "apron2": (250, 250, 3),
}
FIXED = {
    "P": (238, 140, 130),  # blush
    "E": (40, 24, 20),  # eye: lashes and iris
    "W": (255, 252, 244),  # sparkle
    "M": (150, 70, 60),  # mouth
    "O": (236, 232, 224),  # sneaker soles
    "o": (150, 146, 150),  # sneaker shade
}
CHARS = {
    "1": "skin0", "2": "skin1", "3": "skin2",
    "B": "hair0", "h": "hair0", "H": "hair1", "L": "hair2",
    "4": "shirt0", "5": "shirt1", "6": "shirt2",
    "7": "pants0", "8": "pants1",
    "9": "shoe",
}

# ---------------------------------------------------------------- the body, facing you
HEAD_FRONT = [
    "....................",  # 0
    "....................",
    "....................",
    "....................",
    "....................",
    "......22222222......",  # 5 forehead (under the hair)
    ".....2333222222.....",
    "....233322222222....",
    "...22BB222222BB22...",  # 8 little eyebrows
    "...122WE2222WE221...",  # 9 big eyes, a sparkle in each
    "...122EE2222EE221...",
    "...122EE2222EE221...",
    "...1PP22222222PP1...",  # 12 blush
    "....22222MM22221....",  # 13 small mouth
    ".....2222222221.....",
    "......22222211......",
    "........1111........",  # 16 neck
]
TORSO_FRONT = [
    ".....4555555554.....",  # 17 shoulders
    "....455565555554....",  # short sleeves
    "....455565555554....",
    "....255555555551....",  # 20 forearms
    "....255555555551....",
    "....1.44444444.1....",  # 22 hands, hem
]
HEAD_BACK = [
    "....................",
    "....................",
    "....................",
    "....................",
    "....................",
    "......22222222......",
    ".....2222222222.....",
    "....222222222222....",
    "...22222222222222...",
    "...12222222222221...",
    "...12222222222221...",
    "...12222222222221...",
    "...12222222222221...",
    "....122222222221....",
    ".....1222222221.....",
    "......11222211......",
    "........1111........",
]
TORSO_BACK = [
    ".....4555555554.....",
    "....456555555554....",
    "....456555555554....",
    "....255555555551....",
    "....255555555551....",
    "....1.44444444.1....",
]
# trousers and sneakers, from row 23; the step frames lift one foot
LEGS = {
    "": [
        "......88888888......",
        "......888..888......",
        "......887..887......",
        "......887..887......",
        "......887..887......",
        "......887..887......",
        ".....9999..9999.....",
        ".....99o9..99o9.....",
        ".....OOOO..OOOO.....",
    ],
    "a": [  # left foot forward, right lifted
        "......88888888......",
        "......888..888......",
        "......887..887......",
        "......887..887......",
        "......887..999......",
        "......887..99o9.....",
        ".....9999..OOOO.....",
        ".....99o9...........",
        ".....OOOO...........",
    ],
    "b": [
        "......88888888......",
        "......888..888......",
        "......887..887......",
        "......887..887......",
        "......999..887......",
        ".....99o9..887......",
        ".....OOOO..9999.....",
        "...........99o9.....",
        "...........OOOO.....",
    ],
    "sit": [  # knees forward, feet hanging just below
        "......88888888......",
        ".....8888888888.....",
        ".....887....887.....",
        ".....9999..9999.....",
        ".....OOOO..OOOO.....",
    ],
}

# ---------------------------------------------------------------- hairstyles
HAIR = {
    "messy": {
        "front": [
            ".........H....H.....",
            "......H.HH...HH.H...",
            ".....HHLHHH.HHLHH...",
            "...hHHLLHHHHHLLHHh..",
            "..hHHLLLHHHHHLLLHHh.",
            ".hHHHHLHHHHHHHLHHHHh",
            ".hHHHHHHHHHHHHHHHHHh",
            "hHHhHHHhHHHHhHHHhHHh",
            "hHh.hH..hHh..hH.hHh.",
            "hh..h.........h..hh.",
            "h..................h",
        ],
        "back": [
            ".........H....H.....",
            "......H.HH...HH.H...",
            ".....HHLHHH.HHLHH...",
            "...hHHLLHHHHHLLHHh..",
            "..hHHLLLHHHHHLLLHHh.",
            ".hHHHHLHHHHHHHLHHHHh",
            ".hHHHHHHHHHHHHHHHHHh",
            "hHHHHHHHHHHHHHHHHHHh",
            "hHHHHHHHHHHHHHHHHHHh",
            "hhHHHHHHHHHHHHHHHHhh",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hhHHHHHHHHHHHHHHhh.",
            "..hhHHHhHHHhHHHHhh..",
            "...hh.hh.hh.hh.hh...",
        ],
    },
    "long": {
        "front": [
            "....................",
            "......HHHHHHHH......",
            "....HHLLLHHHHHHH....",
            "...HHLLHHHHHHHHHH...",
            "..hHLLHHHHHHHHHHHh..",
            "..hHLHHHHHHHHHHHHh..",
            ".hHHHHHHHhhHHHHHHHh.",
            ".hHHHHHHh..hHHHHHHh.",
            ".hHHh..........hHHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hHh............hHh.",
            ".hh..............hh.",
        ],
        "back": [
            "....................",
            "......HHHHHHHH......",
            "....HHLLLHHHHHHH....",
            "...HHLLHHHHHHHHHH...",
            "..hHLLHHHHHHHHHHHh..",
            "..hHLHHHHHHHHHHHHh..",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHHHHHHHHHHHHHHHHh.",
            "..hHHHHHHHHHHHHHHh..",
            "...hhhhhhhhhhhhhh...",
        ],
    },
    "bun": {
        "front": [
            "........HHHH........",
            ".......HLLHHH.......",
            ".......HLHHHh.......",
            "......hHHHHHh.......",
            ".....HHHHHHHHHH.....",
            "...hHHLLHHHHHHHHh...",
            "..hHLLHHHHHHHHHHHh..",
            "..hHLHHHHHHHHHHHHh..",
            "..hHHh.hHHHHh.hHHh..",
            "..hh............hh..",
        ],
        "back": [
            "........HHHH........",
            ".......HLLHHH.......",
            ".......HLHHHh.......",
            "......hHHHHHh.......",
            ".....HHHHHHHHHH.....",
            "...hHHLLHHHHHHHHh...",
            "..hHLLHHHHHHHHHHHh..",
            "..hHLHHHHHHHHHHHHh..",
            "..hHHHHHHHHHHHHHHh..",
            "..hHHHHHHHHHHHHHHh..",
            "..hHHHHHHHHHHHHHHh..",
            "...hHHHHHHHHHHHHh...",
            "....hhHHHHHHHHhh....",
        ],
    },
    "curly": {
        "front": [
            "......HH.HH.HH......",
            "....HHLLHHLLHHHH....",
            "...HLLHHLLHHHHHHH...",
            "..HHLHHLHHHHHHHHHH..",
            ".hHLHHHHHHHHHHHHHHh.",
            "hHHHHHHHHHHHHHHHHHHh",
            "hHHhHHhHHhHHhHHhHHHh",
            "hHh.hh.hh.hh.hh.hHHh",
            "hHh..............hHh",
            "hHh..............hHh",
            ".hh..............hh.",
        ],
        "back": [
            "......HH.HH.HH......",
            "....HHLLHHLLHHHH....",
            "...HLLHHLLHHHHHHH...",
            "..HHLHHLHHHHHHHHHH..",
            ".hHLHHHHHHHHHHHHHHh.",
            "hHHHHHHHHHHHHHHHHHHh",
            "hHHHHHHHHHHHHHHHHHHh",
            "hHHHHHHHHHHHHHHHHHHh",
            "hHHHHHHHHHHHHHHHHHHh",
            "hHHHHHHHHHHHHHHHHHHh",
            ".hHHHHHHHHHHHHHHHHh.",
            ".hHhHHhHHhHHhHHhHHh.",
            "..hh.hh.hh.hh.hh.h..",
        ],
    },
    "buzz": {
        "front": [
            "....................",
            "....................",
            "....................",
            "......hHHHHHHh......",
            ".....hHLLHHHHHh.....",
            "....hHLHHHHHHHHh....",
            "....hHHHHHHHHHHh....",
            "....h..........h....",
        ],
        "back": [
            "....................",
            "....................",
            "....................",
            "......hHHHHHHh......",
            ".....hHLLHHHHHh.....",
            "....hHLHHHHHHHHh....",
            "....hHHHHHHHHHHh....",
            "....hHHHHHHHHHHh....",
            "....hHHHHHHHHHHh....",
            "....hHHHHHHHHHHh....",
            ".....hHHHHHHHHh.....",
            "......hhHHHHhh......",
        ],
    },
}


def paint(im, rows, x0, y0, skip_skin=False):
    for y, row in enumerate(rows):
        assert len(row) == FW, (len(row), row)
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            col = FIXED.get(ch) or KEYS[CHARS[ch]]
            yy = y0 + y
            if 0 <= yy < FH:
                im.putpixel((x0 + x, yy), col + (255,))


def frame_parts(name):
    kind = "front" if name.startswith("front") else "back"
    step = "sit" if name.endswith("sit") else (name[-1] if name[-2:] in ("-a", "-b") else "")
    dy = SIT_DY if step == "sit" else (-1 if step in ("a", "b") else 0)  # bob mid-stride, sink when seated
    return kind, step, dy


def body_sheet():
    out = Image.new("RGBA", (FW * len(FRAMES), FH), (0, 0, 0, 0))
    for i, name in enumerate(FRAMES):
        kind, step, dy = frame_parts(name)
        f = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        legs = LEGS[step]
        paint(f, legs, 0, TOP + 23 + (dy if step == "sit" else 0))
        torso = TORSO_FRONT if kind == "front" else TORSO_BACK
        paint(f, torso, 0, TOP + 17 + dy)
        paint(f, HEAD_FRONT if kind == "front" else HEAD_BACK, 0, TOP + dy)
        out.alpha_composite(f, (i * FW, 0))
    return out


def hair_sheet(style):
    out = Image.new("RGBA", (FW * len(FRAMES), FH), (0, 0, 0, 0))
    for i, name in enumerate(FRAMES):
        kind, step, dy = frame_parts(name)
        f = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        paint(f, HAIR[style][kind], 0, TOP + dy - 1)
        out.alpha_composite(f, (i * FW, 0))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    body_sheet().save(os.path.join(OUT, "body.png"))
    for st in STYLES:
        hair_sheet(st).save(os.path.join(OUT, f"hair-{st}.png"))
    for old in os.listdir(OUT):  # drop hairstyles that no longer exist
        if old.startswith("hair-") and old[5:-4] not in STYLES:
            os.remove(os.path.join(OUT, old))
    Image.new("RGBA", (FW * len(FRAMES), FH), (0, 0, 0, 0)).save(os.path.join(OUT, "apron.png"))
    json.dump({"frame": [FW, FH], "frames": FRAMES, "foot": list(FOOT), "styles": STYLES,
               "keys": {k: "#%02x%02x%02x" % v for k, v in KEYS.items()}},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    print("avatar sheets ->", OUT)


# ---- preview: recolour like the site does and outline
def recolour(im, pal):
    px = im.load()
    rev = {v: k for k, v in KEYS.items()}
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            k = rev.get((r, g, b))
            if a and k and k in pal:
                px[x, y] = pal[k] + (255,)
    return im


DANIEL = {"skin0": (150, 92, 62), "skin1": (190, 126, 88), "skin2": (214, 152, 110),
          "hair0": (46, 30, 22), "hair1": (84, 58, 42), "hair2": (122, 90, 66),
          "shirt0": (40, 40, 44), "shirt1": (58, 58, 64), "shirt2": (78, 78, 86),
          "pants0": (30, 22, 24), "pants1": (46, 34, 36), "shoe": (176, 172, 178)}


def compose(style, pal):
    comp = Image.new("RGBA", (FW * len(FRAMES), FH), (0, 0, 0, 0))
    comp.alpha_composite(Image.open(os.path.join(OUT, "body.png")).convert("RGBA"))
    comp.alpha_composite(Image.open(os.path.join(OUT, f"hair-{style}.png")).convert("RGBA"))
    comp = recolour(comp, pal)
    a = comp.getchannel("A").load()
    o = comp.copy()
    for y in range(comp.height):
        for x in range(comp.width):
            if not a[x, y] and any(0 <= x + dx < comp.width and 0 <= y + dy < comp.height and a[x + dx, y + dy] and (x + dx) // FW == x // FW for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o.putpixel((x, y), (36, 20, 13, 255))
    return o


def preview(path):
    rng = random.Random(5)
    rows = [compose("messy", DANIEL)]
    shirts = [((70, 90, 60), (100, 128, 82), (134, 164, 104)), ((140, 60, 50), (176, 82, 66), (210, 112, 90)), ((200, 170, 120), (226, 200, 150), (244, 226, 190)), ((50, 62, 110), (72, 88, 150), (104, 122, 186))]
    hairs = [((150, 80, 40), (190, 110, 55), (225, 150, 80)), ((20, 20, 26), (36, 36, 46), (60, 60, 74)), ((214, 170, 90), (240, 206, 130), (252, 232, 170)), ((122, 48, 72), (168, 74, 102), (208, 108, 136))]
    skins = [((222, 168, 128), (240, 196, 158), (252, 220, 186)), ((96, 58, 38), (128, 80, 52), (156, 104, 70)), ((176, 112, 74), (204, 140, 98), (228, 170, 128))]
    for st in STYLES[1:]:
        s, h, c = rng.choice(skins), rng.choice(hairs), rng.choice(shirts)
        pal = dict(DANIEL)
        pal.update({"skin0": s[0], "skin1": s[1], "skin2": s[2], "hair0": h[0], "hair1": h[1], "hair2": h[2], "shirt0": c[0], "shirt1": c[1], "shirt2": c[2]})
        rows.append(compose(st, pal))
    sheetp = Image.new("RGBA", (rows[0].width, FH * len(rows)), (205, 140, 85, 255))
    for i, r in enumerate(rows):
        sheetp.alpha_composite(r, (0, i * FH))
    sheetp.resize((sheetp.width * 5, sheetp.height * 5), Image.NEAREST).save(path)


if __name__ == "__main__":
    main()
    if "--preview" in sys.argv:
        preview(sys.argv[-1])

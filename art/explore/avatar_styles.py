"""Avatar style exploration: a few distinct directions, front-facing idle only, each shown as
Daniel + two sample visitors. Not used by the site; pick one, then it gets full frames.

    python3 art/explore/avatar_styles.py out.png
"""
import sys
from PIL import Image, ImageDraw

OUTLINE = (36, 20, 13)
FIX = {".": None, "E": (36, 24, 20), "W": (255, 252, 244), "P": (238, 140, 130), "M": (150, 70, 60), "O": (236, 232, 224)}
ROLE = {"1": ("skin", 0), "2": ("skin", 1), "3": ("skin", 2), "h": ("hair", 0), "H": ("hair", 1), "L": ("hair", 2),
        "4": ("top", 0), "5": ("top", 1), "6": ("top", 2), "7": ("pants", 0), "8": ("pants", 1), "9": ("shoe", 0), "o": ("shoe", 1)}

STYLES = {
# ---- A: round chibi, Animal Crossing-ish: huge round head, dot eyes, tiny body
"A  round chibi": [
    ".....hHHHHHh.....",
    "...hHHLLHHHHHh...",
    "..hHLLHHHHHHHHh..",
    ".hHLHHHHHHHHHHHh.",
    ".hHHHHhHHHhHHHHh.",
    "hHHHh2222222hHHHh",
    "hHh2233222222hHHh",
    "hh223322222222hHh",
    ".h22E222222E222h.",
    ".122E222222E2221.",
    ".12PP222222PP221.",
    "..122222MM22221..",
    "...1122222221....",
    ".....1111111.....",
    "......45554......",
    ".....4566554.....",
    "....2455555542...",
    ".....4555554.....",
    "......78.87......",
    "......99.99......",
],
# ---- B: bean: one soft egg-shaped body, face up top, no arms, little feet
"B  bean": [
    "......hHHHh......",
    "....hHHLLHHHh....",
    "...hHLLHHHHHHh...",
    "..hHLHHHHHHHHHh..",
    "..hHHhHHHHhHHHh..",
    "..h22222222222h..",
    ".1233322222222h..",
    ".12332E222E2221..",
    ".12222E222E2221..",
    ".12PP2222222PP21.",
    ".1222222MM222221.",
    ".1222222222222221",
    ".455555555555554.",
    ".456555555555554.",
    ".456555555555554.",
    "..4555555555554..",
    "...44555555544...",
    ".....99...99.....",
],
# ---- C: slim cozy-RPG (Stardew-ish): normal head, longer body, detailed clothes
"C  cozy RPG": [
    "....hHHHHHh.....",
    "...hHLLHHHHh....",
    "..hHLHHHHHHHh...",
    "..hHHhHHHhHHh...",
    "..h233222222h...",
    "..1232E22E221...",
    "..1222E22E221...",
    "..12222222221...",
    "...122MM2221....",
    "....1122211.....",
    ".....4555554....",
    "....456655554...",
    "...2456555554...",
    "...2455555552...",
    "...1455555551...",
    "....4444444......",
    "....788887.......",
    "....78..87.......",
    "....78..87.......",
    "....78..87.......",
    "....78..87.......",
    "...999..999......",
],
# ---- D: big-eyed cute (the current reference style, cuter): sparkle eyes, short tee
"D  big-eyed": [
    "....hHHHHHHHh....",
    "..hHHLLHHHHHHHh..",
    ".hHLLHHHHHHHHHHh.",
    "hHHHHhHHHhHHHhHHh",
    "hHh2222222222hHHh",
    "hh223322222222hHh",
    ".h22WE2222WE222h.",
    ".122EE2222EE2221.",
    ".122EE2222EE2221.",
    ".12PP22222222PP1.",
    "..1222222MM22221.",
    "...122222222211..",
    ".....11111111....",
    "....4555555554...",
    "...455565555554..",
    "...255555555551..",
    "...1.44444444.1..",
    ".....88888888....",
    ".....888..888....",
    ".....887..887....",
    "....9999..9999...",
    "....OOOO..OOOO...",
],
}

PALETTES = [
    {"skin": [(150, 92, 62), (190, 126, 88), (214, 152, 110)], "hair": [(46, 30, 22), (84, 58, 42), (122, 90, 66)],
     "top": [(40, 40, 44), (58, 58, 64), (78, 78, 86)], "pants": [(30, 22, 24), (46, 34, 36)], "shoe": [(176, 172, 178), (130, 126, 132)]},
    {"skin": [(222, 168, 128), (240, 196, 158), (252, 220, 186)], "hair": [(150, 80, 40), (190, 110, 55), (225, 150, 80)],
     "top": [(70, 90, 60), (100, 128, 82), (134, 164, 104)], "pants": [(44, 58, 82), (64, 82, 116)], "shoe": [(90, 56, 40), (70, 44, 30)]},
    {"skin": [(96, 58, 38), (128, 80, 52), (156, 104, 70)], "hair": [(20, 20, 26), (36, 36, 46), (60, 60, 74)],
     "top": [(168, 74, 96), (200, 100, 124), (228, 136, 156)], "pants": [(60, 52, 44), (86, 76, 64)], "shoe": [(236, 232, 224), (190, 186, 180)]},
]


def draw(rows, pal):
    w = max(len(r) for r in rows)
    im = Image.new("RGBA", (w + 2, len(rows) + 2), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in FIX:
                if FIX[ch]:
                    im.putpixel((x + 1, y + 1), FIX[ch] + (255,))
            else:
                role, k = ROLE[ch]
                im.putpixel((x + 1, y + 1), pal[role][k] + (255,))
    a = im.getchannel("A").load()
    o = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if not a[x, y] and any(0 <= x + dx < im.width and 0 <= y + dy < im.height and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                o.putpixel((x, y), OUTLINE + (255,))
    return o


if __name__ == "__main__":
    S = 6
    cell = 30
    sheet = Image.new("RGBA", ((cell * 3 + 6) * len(STYLES) * S, 44 * S), (205, 140, 85, 255))
    d = ImageDraw.Draw(sheet)
    for si, (name, rows) in enumerate(STYLES.items()):
        x0 = si * (cell * 3 + 6)
        for pi, pal in enumerate(PALETTES):
            im = draw(rows, pal)
            big = im.resize((im.width * S, im.height * S), Image.NEAREST)
            sheet.alpha_composite(big, ((x0 + pi * cell + (cell - im.width) // 2) * S, (40 - im.height) * S))
        d.text(((x0 + 2) * S, 2 * S), name, fill=(40, 20, 10, 255))
    sheet.save(sys.argv[1])

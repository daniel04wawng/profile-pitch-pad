"""Small pixel sprites used inside the café's screens (pastries, a record, a coffee cup).

Same palette and outline style as the room's furniture. Shown scaled up with hard pixels.

    python3 art/draw_ui.py   # writes public/cafe/ui/<name>.png
"""
import os

from draw_iso import P, Iso

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "ui")


def save(s, name):
    s.im.save(os.path.join(OUT, f"{name}.png"))


def croissant():
    s = Iso(18, 12)
    for x, y0, y1, c in [(3, 5, 8, "gold0"), (4, 3, 9, "gold1"), (5, 2, 9, "gold1"), (6, 2, 10, "gold1"),
                         (7, 1, 10, "gold2"), (8, 1, 10, "gold1"), (9, 1, 10, "gold2"), (10, 1, 10, "gold1"),
                         (11, 2, 10, "gold1"), (12, 2, 9, "gold1"), (13, 3, 9, "gold1"), (14, 5, 8, "gold0")]:
        s.vline(x, y0, y1, c)
    for x in (6, 9, 12):  # the rolled ridges
        s.vline(x, 3, 9, "gold0")
    s.px(8, 2, "white"); s.px(10, 2, "white")
    s.outline()
    save(s, "pastry-croissant")


def macaron():
    s = Iso(16, 14)
    for y, (x0, x1, c) in enumerate([(5, 10, "pink1"), (3, 12, "pink1"), (2, 13, "pink2"), (2, 13, "pink1"),
                                     (2, 13, "white"), (2, 13, "cream1"), (2, 13, "pink1"), (3, 12, "pink0"), (5, 10, "pink0")]):
        for x in range(x0, x1 + 1):
            s.px(x, y + 2, c)
    s.px(5, 4, "white")
    s.outline()
    save(s, "pastry-macaron")


def cinnamon():
    s = Iso(16, 14)
    s.d.ellipse([1, 2, 14, 12], fill=P["terra0"])
    s.d.ellipse([3, 3, 12, 10], fill=P["terra1"])
    s.d.ellipse([5, 4, 10, 8], fill=P["terra0"])
    s.d.ellipse([6, 5, 9, 7], fill=P["terra2"])
    for x, y in [(4, 2), (8, 3), (11, 4), (3, 6), (12, 7), (6, 10), (9, 9)]:
        s.px(x, y, "cream2")  # icing drizzle
    s.outline()
    save(s, "pastry-cinnamon")


def muffin():
    s = Iso(16, 16)
    s.d.ellipse([2, 1, 13, 9], fill=P["wood3"])
    s.d.ellipse([3, 1, 11, 6], fill=P["wood4"])
    for x, y in [(5, 3), (9, 2), (7, 5), (11, 5), (4, 6)]:
        s.px(x, y, "blue0")  # blueberries
    for y in range(8, 15):
        inset = (y - 8) // 3
        for x in range(3 + inset, 13 - inset):
            s.px(x, y, "cream1" if (x % 2) else "cream0")  # pleated paper cup
    s.outline()
    save(s, "pastry-muffin")


def donut():
    s = Iso(16, 14)
    s.d.ellipse([1, 2, 14, 12], fill=P["wood3"])
    s.d.ellipse([2, 2, 13, 9], fill=P["pink1"])
    s.d.ellipse([6, 5, 9, 7], fill=(0, 0, 0, 0))
    for x, y in [(4, 4), (10, 3), (11, 7), (3, 7), (7, 3)]:
        s.px(x, y, "sage3" if (x + y) % 2 else "gold2")  # sprinkles
    s.outline()
    save(s, "pastry-donut")


def cake_slice():
    s = Iso(16, 14)
    s.poly([(2, 5), (13, 2), (13, 11), (2, 11)], "cream2")
    s.poly([(2, 5), (13, 2), (13, 4), (2, 7)], "pink1")
    for y in (8,):
        for x in range(2, 14):
            s.px(x, y, "pink2")
    s.px(11, 1, "pink0")
    s.outline()
    save(s, "pastry-cake")


def record():
    s = Iso(26, 26)
    s.d.ellipse([1, 1, 24, 24], fill=P["keyblack"])
    for r in (9, 7):
        s.d.ellipse([12.5 - r, 12.5 - r, 12.5 + r, 12.5 + r], outline=P["steel0"])
    s.d.ellipse([9, 9, 16, 16], fill=P["terra1"])
    s.px(12, 12, "cream2"); s.px(13, 12, "cream2")
    s.px(6, 6, "steel2"); s.px(7, 5, "steel2")  # shine
    s.outline()
    save(s, "record")


def cup():
    s = Iso(16, 14)
    for y in range(3, 11):
        for x in range(2, 11):
            s.px(x, y, "white")
    for x in range(3, 10):
        s.px(x, 3, "wood1"); s.px(x, 4, "wood2")
    s.vline(11, 5, 8, "white"); s.vline(12, 5, 8, "white")
    for x in range(0, 14):
        s.px(x, 12, "cream0")
    s.outline()
    save(s, "cup")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (croissant, macaron, cinnamon, muffin, donut, cake_slice, record, cup):
        f()
    print("ui sprites ->", OUT)

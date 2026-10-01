"""A simple kitchen doorway in the room's palette: wood frame, warm light inside.

Drawn for the back-left wall (its top and bottom edges rise to the right, 1px per 2px);
flip it in the editor for the back-right wall.

    python3 art/draw_door.py   # writes public/cafe/sprites/kitchen-doorway.png
"""
import os

from PIL import Image

from draw_room import P, BAYER

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")

W, H = 26, 50  # outer width and height of the frame (px)
F = 3  # frame thickness


def main():
    im = Image.new("RGBA", (W + 2, H + W // 2 + 2), (0, 0, 0, 0))
    glow = ["glow", "wall4", "shine1"]  # inside the doorway: warm, brightest near the floor
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
                level = 2.2 * (1 - z / (H - F)) ** 0.7
                c = glow[0]
                i = int(level)
                if i < 2 and (level - i) * 16 > BAYER[y % 4][x % 4]:
                    i += 1
                c = glow[min(i, 2)]
                if x == F or z == H - F - 1:
                    c = "deep1"  # shadow just inside the frame
                elif z in (30, 31) and F + 2 <= x < W - F - 4:
                    c = "panel1" if z == 30 else "deep1"  # one kitchen shelf, nothing more
            im.putpixel((x + 1, y + 1), P[c])
    # 1px dark edge
    src = im.copy()
    a = src.getchannel("A").load()
    for y in range(im.height):
        for x in range(im.width):
            if not a[x, y] and any(0 <= x + dx < im.width and 0 <= y + dy < im.height and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), (36, 20, 13, 255))
    im = im.crop(im.getbbox())
    im.save(os.path.join(OUT, "kitchen-doorway.png"))
    print("kitchen-doorway", im.size)


if __name__ == "__main__":
    main()

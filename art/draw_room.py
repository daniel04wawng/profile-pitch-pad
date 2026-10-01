"""The empty café room: an isometric dollhouse cutaway drawn on the editor's grid.

Just the shell (floor, two walls, base). Windows, lamps and everything else are assets
placed in the editor, and lighting comes from the time of day, not from this image.

Floor of N x N tiles (32x16px, 2:1 iso), two back walls, and a floating base, in the same
simple palette as the iso assets. Nothing is baked in: furniture is placed in the editor.

    python3 art/draw_room.py   # writes public/cafe/room.png and prints the grid origin

The floor's back corner is the grid origin (ox, oy), so editor tiles line up with the planks.
"""
import math
import os
import random

from PIL import Image

from draw_iso import P as BASE_P

# The room gets a few warmer tones on top of the shared palette: golden walls, deep wood.
# Colors sampled from the original café: orange-brown planks with dark seams and bright
# reflections, warm cream walls over dark wood paneling.
P = {**BASE_P, **{k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in {
    "wall0": "#d9b585", "wall1": "#e6c697", "wall2": "#f0d6aa",
    "glow": "#e0a865", "deep0": "#2e1508", "deep1": "#4a2410",
    "plank0": "#884517", "plank1": "#9e5a26", "plank2": "#a65927", "plank3": "#b1652b",
    "seam": "#5a311c", "shine0": "#d0732a", "shine1": "#e78e31",
    "panel0": "#4f2a16", "panel1": "#6b3d22", "panel2": "#7c4a29", "rail": "#9e5a26",
}.items()}}

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe")

N = 20  # floor is N x N tiles (roomy, so it doesn't feel cluttered)
TILE = 32
HW = TILE // 2  # half tile width
HH = TILE // 4  # half tile height
WALL = 140  # wall height in px
CAP = 4  # thickness of the cut wall top
SLAB = 10  # floating base under the floor
W, H = 672, 492
OX, OY = W // 2, 4 + CAP + WALL  # floor back corner = grid origin


def floor_uv(x, y):
    """Screen pixel -> floor coords in tiles (u runs down-right, v runs down-left)."""
    a = (x - OX) / HW
    b = (y - OY) / HH
    return (a + b) / 2, (b - a) / 2


def wall_color(z, along, lit):
    if z >= WALL:
        return "seam" if z >= WALL + CAP - 1 else "deep1"  # the cut top of the wall
    if z >= WALL - 7:  # crown molding
        return ("panel2" if lit else "panel1") if z in (WALL - 7, WALL - 3) else ("panel1" if lit else "panel0")
    if z < 4:
        return "deep0"  # baseboard
    if z < 48:  # dark wood paneling, framed panels every half tile
        k = (along * 2) % 1
        if k < 0.08 or z in (6, 44):
            return "panel0"
        if k < 0.14:
            return "panel2" if lit else "panel1"  # lit panel edge
        return "panel1" if lit else "panel0"
    if z < 52:
        return "rail" if lit else "panel2"  # chair rail
    # warm cream wall with soft stripes
    if (along * 2) % 1 < 0.16:
        return "wall1" if lit else "wall0"
    return "wall2" if lit else "wall1"


def main():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    put = lambda x, y, c: 0 <= x < W and 0 <= y < H and im.putpixel((int(x), int(y)), P[c])
    rng = random.Random(3)

    # ---- walls: back-left (lit) runs down-left from the back corner, back-right (shaded) down-right
    for x in range(OX - N * HW, OX + N * HW + 1):
        lit = x <= OX
        along = (OX - x) / HW if lit else (x - OX) / HW
        floor_y = round(OY + along * HH)
        for z in range(WALL + CAP):
            put(x, floor_y - z, wall_color(z, along, lit))

    # ---- floor: narrow orange-brown planks like the original, dark seams, glossy light streaks
    PLANKS = 5
    tones = ["plank1", "plank2", "plank1", "plank3", "plank0"]
    plank_tone, plank_offset = {}, {}
    for y in range(H):
        for x in range(W):
            u, v = floor_uv(x, y)
            if not (0 <= u < N and 0 <= v < N):
                continue
            p = math.floor(v * PLANKS)
            seg_len = 3.0
            off = plank_offset.setdefault(p, rng.random() * seg_len)
            seg = math.floor((u + off) / seg_len)
            c = plank_tone.setdefault((p, seg), rng.choice(tones))
            if (v * PLANKS) % 1 < 0.16:
                c = "seam"
            elif ((u + off) / seg_len) % 1 < 0.025:
                c = "seam"
            else:
                # glossy floor: soft bands of reflected light running across the planks
                g = math.sin(u * 0.55 - v * 0.25) + 0.6 * math.sin(v * 0.9 + u * 0.15)
                if g > 1.35:
                    c = "shine1" if (x + y) % 2 == 0 else "shine0"
                elif g > 1.15 and (x + y) % 2 == 0:
                    c = "shine0"
            if u < 0.15 or v < 0.15:
                c = "deep0"
            elif (u < 0.45 or v < 0.45) and c not in ("seam",):
                c = "plank0"  # darker where the floor meets the walls
            put(x, y, c)

    # ---- floating base under the two front edges of the floor
    for x in range(OX - N * HW, OX + N * HW + 1):
        if x <= OX:
            edge = OY + N * HH + (x - (OX - N * HW)) / 2
            c = "steel1"
        else:
            edge = OY + 2 * N * HH - (x - OX) / 2
            c = "steel0"
        for k in range(1, SLAB + 1):
            put(x, math.floor(edge) + k, c)

    # ---- 1px outline so the room pops off the page
    src = im.copy()
    a = src.getchannel("A").load()
    for y in range(H):
        for x in range(W):
            if not a[x, y] and any(0 <= x + dx < W and 0 <= y + dy < H and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), P["ink"])

    im.save(os.path.join(OUT, "room.png"))
    print(f"room.png {W}x{H}, grid origin ox={OX} oy={OY}, {N}x{N} tiles")


if __name__ == "__main__":
    main()

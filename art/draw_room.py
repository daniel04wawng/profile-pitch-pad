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
P = {**BASE_P, **{k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in {
    "wall0": "#d9b27c", "wall1": "#e8c793", "wall2": "#f2d9aa",
    "glow": "#e0a865", "deep0": "#3a2219", "deep1": "#56331f",
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
        return "wood1" if z >= WALL + CAP - 1 else "deep1"  # the cut top of the wall
    if z >= WALL - 7:  # crown molding: a stepped wooden trim along the top
        return ("wood3" if lit else "wood2") if z in (WALL - 7, WALL - 3) else ("wood2" if lit else "wood1")
    if z < 4:
        return "deep0"  # baseboard
    if z < 44:  # tall wood wainscot, a seam every quarter tile
        seam = (along * 4) % 1 < 0.12
        return ("wood1" if lit else "deep1") if seam else ("wood2" if lit else "wood1")
    if z < 47:
        return "wood3" if lit else "wood2"  # chair rail
    # cozy striped wallpaper: soft stripes every half tile
    stripe = (along * 2) % 1 < 0.18
    if stripe:
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

    # ---- floor: planks along u, staggered joints, darker seams, soft shadow at the walls
    PLANKS = 4
    tones = ["wood2", "wood3", "wood3", "wood4", "wood2"]
    plank_tone, plank_offset = {}, {}
    for y in range(H):
        for x in range(W):
            u, v = floor_uv(x, y)
            if not (0 <= u < N and 0 <= v < N):
                continue
            p = math.floor(v * PLANKS)
            seg_len = 2.5
            off = plank_offset.setdefault(p, rng.random() * seg_len)
            seg = math.floor((u + off) / seg_len)
            c = plank_tone.setdefault((p, seg), rng.choice(tones))
            if (v * PLANKS) % 1 < 0.13:
                c = "wood2" if c != "wood2" else "wood1"
            elif ((u + off) / seg_len) % 1 < 0.03:
                c = "wood1"
            if u < 0.12 or v < 0.12:
                c = "deep0"
            elif (u < 0.3 or v < 0.3) and c in ("wood3", "wood4"):
                c = "wood1"
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

"""LANDING PAGE (not used yet): the café seen from outside, on a street corner.

Kept for the landing page, where visitors arrive outside before stepping in.

The café base: an isometric corner café on a street, in the style of the original café.

Just the shell, drawn on the editor's grid (32x16px tiles, 2:1 iso):
- the café floor (INSIDE x INSIDE tiles) and its two back walls, warm and wood-panelled,
- dark brick city buildings rising behind it (the café is their ground floor),
- a stone sidewalk and a wet street wrapping around the two front sides.

Everything else (storefront walls, windows, door, lamps, trees, furniture) is an asset placed
in the editor, and the light comes from the time of day.

    python3 art/draw_room.py   # writes public/cafe/room.png and room-night.png (lit windows)
"""
import math
import os
import random

from PIL import Image

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from draw_iso import P as BASE_P  # noqa: E402

P = {**BASE_P, **{k: tuple(int(v[i : i + 2], 16) for i in (1, 3, 5)) + (255,) for k, v in {
    "wall0": "#d9b27c", "wall1": "#e8c793", "wall2": "#f2d9aa",
    "deep0": "#3a2219", "deep1": "#56331f",
    "brick0": "#2b3150", "brick1": "#363e62", "brick2": "#424c74", "mortar": "#252a44",
    "sill": "#5a6386", "pane": "#1d2238", "pane1": "#283050",
    "stone0": "#8f877c", "stone1": "#a39a8f", "stone2": "#b9b0a5", "curb": "#d6cfc3",
    "road0": "#2f313b", "road1": "#383a46", "road2": "#454857", "wet": "#5d6683", "dash": "#cfc6a2",
    "lit0": "#f2b45c", "lit1": "#ffd98a",
}.items()}}

ART = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ART, "landing")  # not served until the landing page exists

INSIDE = 14  # café floor is INSIDE x INSIDE tiles
WALK = 3  # sidewalk depth in tiles
ROAD = 3  # street depth in tiles
N = INSIDE + WALK + ROAD  # whole ground, in tiles
TILE = 32
HW, HH = TILE // 2, TILE // 4
WALL = 112  # café interior wall height
TOWER = 190  # buildings rising behind
SLAB = 10
W = 2 * N * HW + 32
OX = W // 2
OY = TOWER + 8  # back corner of the café floor = grid origin
H = OY + 2 * N * HH + SLAB + 8


def uv(x, y):
    a = (x - OX) / HW
    b = (y - OY) / HH
    return (a + b) / 2, (b - a) / 2


def main():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    night = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def put(img, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            img.putpixel((int(x), int(y)), P[c])

    rng = random.Random(7)

    # ---- back planes: café walls on the ground floor, brick buildings above and beyond
    for x in range(OX - N * HW, OX + N * HW + 1):
        left = x <= OX
        along = (OX - x) / HW if left else (x - OX) / HW  # tiles along this back plane
        floor_y = round(OY + along * HH)
        cafe = along < INSIDE
        for z in range(TOWER):
            y = floor_y - z
            if cafe and z < WALL:
                # inside the café: wainscot, chair rail, striped wallpaper, crown molding
                if z < 4:
                    c = "deep0"
                elif z < 44:
                    seam = (along * 4) % 1 < 0.12
                    c = ("wood1" if left else "deep1") if seam else ("wood2" if left else "wood1")
                elif z < 47:
                    c = "wood3" if left else "wood2"
                elif z >= WALL - 7:
                    c = ("wood3" if left else "wood2") if z in (WALL - 7, WALL - 3) else ("wood2" if left else "wood1")
                else:
                    c = ("wall1" if left else "wall0") if (along * 2) % 1 < 0.18 else ("wall2" if left else "wall1")
                put(im, x, y, c)
                continue
            if cafe and z < WALL + 4:
                put(im, x, y, "deep1")  # cut top of the café wall
                continue
            # brick: courses every 4px with staggered joints
            course = z // 4
            joint = ((along * 4) + (course % 2) * 0.5) % 1 < 0.1
            c = "mortar" if (z % 4 == 0 or joint) else ("brick1" if left else "brick0")
            if (course * 7 + int(along * 4)) % 11 == 0 and c != "mortar":
                c = "brick2" if left else "brick1"
            # upper-floor windows: one per 2-tile bay per storey
            wx = (along % 2) / 2
            floor_z = z - (WALL + 14 if cafe else 30)
            fz = floor_z % 56 if floor_z >= 0 else -1
            if 0 <= fz < 30 and 0.3 < wx < 0.7:
                c = "sill" if fz < 3 else ("pane1" if wx < 0.5 else "pane")
                mullion = abs(wx - 0.5) < 0.03
                if fz >= 3 and mullion:
                    c = "brick0"
                # about half the windows glow at night (deterministic per window)
                bay = (int(along // 2), floor_z // 56, left)
                if fz >= 3 and not mullion and (bay[0] * 7 + bay[1] * 3 + (1 if bay[2] else 0)) % 5 in (0, 2, 3):
                    put(night, x, y, "lit1" if fz > 16 else "lit0")
            if z == TOWER - 1:
                c = "brick0"
            put(im, x, y, c)

    # ---- ground: wood floor inside, stone sidewalk, curb, wet street
    PLANKS = 4
    tones = ["wood2", "wood3", "wood3", "wood4", "wood2"]
    plank_tone, plank_offset = {}, {}
    for y in range(H):
        for x in range(W):
            u, v = uv(x, y)
            if not (0 <= u < N and 0 <= v < N):
                continue
            if u < INSIDE and v < INSIDE:
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
            else:
                d = max(u, v)  # how far out from the café
                if d < INSIDE + WALK - 0.15:
                    # sidewalk: stone slabs one tile each, with grout lines
                    grout = u % 1 < 0.06 or v % 1 < 0.06
                    c = "stone0" if grout else ["stone1", "stone2", "stone1"][(int(u) * 3 + int(v)) % 3]
                elif d < INSIDE + WALK:
                    c = "curb"
                else:
                    # wet asphalt with puddles that catch the light, and lane dashes
                    n = (math.sin(u * 2.3) + math.sin(v * 1.7 + u * 0.6) + math.sin((u + v) * 3.1)) / 3
                    c = "road1" if (x + y) % 2 else "road0"
                    if n > 0.55:
                        c = "wet"
                    elif n > 0.35 and (x + y) % 2 == 0:
                        c = "road2"
                    mid = INSIDE + WALK + ROAD / 2
                    if (abs(u - mid) < 0.08 and v < INSIDE + WALK and (v % 2) < 1) or (abs(v - mid) < 0.08 and u < INSIDE + WALK and (u % 2) < 1):
                        c = "dash"
            put(im, x, y, c)

    # ---- floating base under the ground's two front edges
    for x in range(OX - N * HW, OX + N * HW + 1):
        if x <= OX:
            edge, c = OY + N * HH + (x - (OX - N * HW)) / 2, "steel1"
        else:
            edge, c = OY + 2 * N * HH - (x - OX) / 2, "steel0"
        for k in range(1, SLAB + 1):
            put(im, x, math.floor(edge) + k, c)

    # ---- 1px outline
    src = im.copy()
    a = src.getchannel("A").load()
    for y in range(H):
        for x in range(W):
            if not a[x, y] and any(0 <= x + dx < W and 0 <= y + dy < H and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), P["ink"])

    im.save(os.path.join(OUT, "room.png"))
    night.save(os.path.join(OUT, "room-night.png"))
    print(f"room.png {W}x{H}, grid origin ox={OX} oy={OY}, ground {N}x{N} tiles, café {INSIDE}x{INSIDE}")


if __name__ == "__main__":
    main()

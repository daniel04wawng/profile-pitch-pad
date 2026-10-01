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
    # walls: the original's lamp-lit orange-tan plaster (sampled from the high-res original)
    "wall0": "#a4693f", "wall1": "#b97644", "wall2": "#c4814d", "wall3": "#d38c54", "wall4": "#e09a5c",
    "glow": "#eba868", "deep0": "#2e1508", "deep1": "#4a2410",
    # floor: golden honey planks with bright glossy reflections
    "plank0": "#934b1c", "plank1": "#ac5f27", "plank2": "#c76b28", "plank3": "#cd7536",
    "seam": "#6a3415", "shine0": "#e08738", "shine1": "#ffa640",
    "panel0": "#4f2a16", "panel1": "#6b3d22", "panel2": "#8a5530", "rail": "#b0703a",
    # navy trim and base, like the original's outer walls
    "navy0": "#0a192f", "navy1": "#22253e", "navy2": "#363763",
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


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(level, x, y, ramp):
    """Pick from a dark->light ramp at a fractional level, with ordered dithering between steps."""
    level = max(0.0, min(len(ramp) - 1.0, level))
    i = int(level)
    if i < len(ramp) - 1 and (level - i) * 16 > BAYER[y % 4][x % 4]:
        i += 1
    return ramp[i]


def wall_color(z, along, lit, x, y):
    if z >= WALL:
        return "navy0" if z >= WALL + CAP - 1 else "navy1"  # the cut top of the wall
    if z >= WALL - 6:  # crown molding
        return "panel2" if z in (WALL - 6, WALL - 2) else ("panel1" if lit else "panel0")
    if z < 4:
        return "deep0"  # baseboard
    if z < 34:  # low wood wainscot, framed panels every half tile
        k = (along * 2) % 1
        if k < 0.08 or z in (6, 31):
            return "panel0"
        if k < 0.14:
            return "panel2" if lit else "panel1"
        return "panel1" if lit else "panel0"
    if z < 37:
        return "rail"  # chair rail
    # warm plaster: brightest at mid-height, falling off toward the ceiling, corner and far ends
    mid = 1 - abs((z - 80) / 70)
    ends = 1 - (along / N) ** 2 * 0.6
    corner = min(1.0, along / 2.5)
    level = (0.6 + 3.2 * mid * ends * (0.55 + 0.45 * corner)) - (0 if lit else 0.7)
    return dither(level, x, y, ["wall0", "wall1", "wall2", "wall3", "wall4"])


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
            put(x, floor_y - z, wall_color(z, along, lit, x, floor_y - z))

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
                # glossy floor: long streaks of reflected lamplight along the planks
                g = math.sin(u * 0.35 - v * 0.9) + 0.5 * math.sin(v * 1.7 + 1.3)
                lit_plank = plank_tone.setdefault(("lit", p, seg), rng.random())
                if g > 1.15 and lit_plank < 0.7:
                    c = "shine1" if g > 1.38 else "shine0"
            # lamp-lit middle, dimmer toward the walls and the front edges
            d = ((u - N * 0.5) ** 2 + (v - N * 0.5) ** 2) ** 0.5 / (N * 0.7)
            if c in ("plank1", "plank2", "plank3") and d > 0.55 and BAYER[y % 4][x % 4] < (d - 0.55) * 40:
                c = "plank0"
            if u < 0.15 or v < 0.15:
                c = "deep0"
            elif (u < 0.45 or v < 0.45) and c not in ("seam",):
                c = "plank0"  # darker where the floor meets the walls
            put(x, y, c)

    # ---- floating base under the two front edges of the floor
    for x in range(OX - N * HW, OX + N * HW + 1):
        if x <= OX:
            edge = OY + N * HH + (x - (OX - N * HW)) / 2
            c = "navy2"
        else:
            edge = OY + 2 * N * HH - (x - OX) / 2
            c = "navy1"
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

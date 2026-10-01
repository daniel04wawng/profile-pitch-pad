"""Cut the original café's features into standalone assets, from the high-res original.

For each piece: cut a generous outline from art/reference/cafe-reference-night.webp, drop the
surroundings (cream wall behind wall pieces, floor under floor pieces) by colour, shrink 4:1
into true pixels at the room's scale (the same scale as the cleaned pastry counter), snap to
the original's palette, remove specks, and add a dark edge.

    python3 art/cut_reference.py [name ...]   # writes public/cafe/sprites/<name>.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(ART, "reference", "cafe-reference-night.webp")
PALETTE_GPL = os.path.join(ART, "source", "cafe-night-palette.gpl")
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")
EDGE = (36, 20, 13, 255)
SCALE = 4  # high-res original pixels per room pixel


def wall(px):
    """The original's walls: warm orange-cream under its lamplight (sampled next to each piece)."""
    r, g, b = px[..., 0].astype(int), px[..., 1].astype(int), px[..., 2].astype(int)
    orange_wall = (r > 160) & (g > 95) & (b > 35) & (b < 110) & (r > g) & (g > b) & ((r - g) > 40) & ((r - g) < 100)
    night_sky = (b > r + 8) & (r < 120)  # the dark blue outside, above the original's walls
    return orange_wall | night_sky


def floor(px):
    """Warm orange floorboards."""
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    return (r > 140) & ((r - b) > 70) & (g > 70) & (g < r) & ((r + g + b) > 300)


def rug(px):
    """The deep red patterned rug under the piano corner."""
    r, g, b = px[..., 0].astype(int), px[..., 1].astype(int), px[..., 2].astype(int)
    red = (r > 90) & (g < 75) & (b < 75) & ((r - g) > 45)
    dark_threads = (b >= r - 6) & (r < 120)  # navy and grey pattern; the wood is always warmer
    pink = (r > 150) & (b > 90) & ((r - g) > 50)
    return red | dark_threads | pink


def leaves(px):
    r, g, b = px[..., 0].astype(int), px[..., 1].astype(int), px[..., 2].astype(int)
    return (g > r) & (g > b)


def below_piece(px):
    """For pieces whose top edge is traced by hand: only floor, rug and leaves go."""
    return floor(px) | rug(px) | leaves(px)


def around_floor_piece(px):
    return floor(px) | wall(px) | rug(px) | leaves(px)


# name: (outline in high-res pixels, what to remove inside it)
PIECES = {
    "chalkboard-menu": ([(956, 120), (1016, 120), (1016, 238), (956, 238)], wall),
    "sax-poster": ([(1302, 214), (1418, 214), (1418, 350), (1302, 350)], wall),
    "record-art": ([(1428, 345), (1490, 345), (1490, 430), (1428, 430)], wall),
    "framed-picture-tall": ([(712, 78), (768, 78), (768, 164), (712, 164)], wall),
    "back-bar-shelves": ([(766, 34), (962, 112), (962, 196), (766, 150)], wall),
    "espresso-station": ([(776, 178), (902, 214), (902, 268), (776, 236)], wall),
    "record-cabinet": ([(1352, 436), (1490, 436), (1490, 566), (1352, 566)], around_floor_piece),
}


def palette():
    cols = []
    for line in open(PALETTE_GPL).read().splitlines()[4:]:
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit():
            cols.append(tuple(int(v) for v in parts[:3]))
    return np.array(cols, dtype=int)


def cut(name, poly, remove, pal):
    ref = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    H, W, _ = ref.shape
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    inside = np.asarray(m) > 0
    bg = remove(ref) & inside
    # Only background that's connected to the edge of the cut goes; matching colours enclosed
    # by the object (gold inside a frame) stay.
    x0, y0 = min(p[0] for p in poly), min(p[1] for p in poly)
    x1, y1 = max(p[0] for p in poly), max(p[1] for p in poly)
    reach = np.zeros_like(bg)
    stack = [(x, y) for x in range(x0, x1 + 1) for y in (y0, y1)] + [(x, y) for y in range(y0, y1 + 1) for x in (x0, x1)]
    while stack:
        x, y = stack.pop()
        if not (x0 <= x <= x1 and y0 <= y <= y1) or reach[y, x] or not bg[y, x]:
            continue
        reach[y, x] = True
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    keep = inside & ~reach
    x0, y0 = min(p[0] for p in poly), min(p[1] for p in poly)
    x1, y1 = max(p[0] for p in poly), max(p[1] for p in poly)
    x0, y0 = x0 - x0 % SCALE, y0 - y0 % SCALE
    w, h = (x1 - x0) // SCALE + 1, (y1 - y0) // SCALE + 1
    rgb = ref[y0 : y0 + h * SCALE, x0 : x0 + w * SCALE]
    k = keep[y0 : y0 + h * SCALE, x0 : x0 + w * SCALE]
    hh, ww = rgb.shape[0] // SCALE, rgb.shape[1] // SCALE
    rgb = rgb[: hh * SCALE, : ww * SCALE].reshape(hh, SCALE, ww, SCALE, 3).transpose(0, 2, 1, 3, 4).reshape(hh, ww, SCALE * SCALE, 3)
    k = k[: hh * SCALE, : ww * SCALE].reshape(hh, SCALE, ww, SCALE).transpose(0, 2, 1, 3).reshape(hh, ww, SCALE * SCALE)
    out = np.zeros((hh, ww, 4), dtype=np.uint8)
    for yy in range(hh):
        for xx in range(ww):
            sel = k[yy, xx]
            if sel.sum() < (SCALE * SCALE) // 2:
                continue  # mostly background: leave transparent
            c = np.median(rgb[yy, xx][sel], axis=0)
            c = pal[np.argmin(((pal - c) ** 2).sum(axis=1))]  # snap to the original's palette
            out[yy, xx] = (*c, 255)
    im = Image.fromarray(out)
    # drop loose fragments: keep the object, and any detached part at least 8% of its size
    a = out[..., 3] > 0
    seen = np.zeros_like(a)
    comps = []
    for yy in range(hh):
        for xx in range(ww):
            if a[yy, xx] and not seen[yy, xx]:
                stack, comp = [(xx, yy)], []
                seen[yy, xx] = True
                while stack:
                    cx, cy = stack.pop()
                    comp.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < ww and 0 <= ny < hh and a[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((nx, ny))
                comps.append(comp)
    biggest = max((len(c) for c in comps), default=0)
    for comp in comps:
        if len(comp) < max(4, 0.08 * biggest):
            for cx, cy in comp:
                im.putpixel((cx, cy), (0, 0, 0, 0))
    im = im.crop(im.getbbox())
    # 1px dark edge
    edged = Image.new("RGBA", (im.width + 2, im.height + 2), (0, 0, 0, 0))
    edged.alpha_composite(im, (1, 1))
    al = edged.getchannel("A").load()
    for y in range(edged.height):
        for x in range(edged.width):
            if not al[x, y] and any(0 <= x + dx < edged.width and 0 <= y + dy < edged.height and al[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edged.putpixel((x, y), EDGE)
    edged.save(os.path.join(OUT, f"{name}.png"))
    return edged


if __name__ == "__main__":
    from unify_wood import unify
    pal = palette()
    for name in sys.argv[1:] or PIECES:
        poly, remove = PIECES[name]
        im = cut(name, poly, remove, pal)
        unify(name)  # same wood as everything else
        print(f"{name:22s} {im.size}")

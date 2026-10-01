"""Turn the original café pieces into clean standalone assets, keeping the original art.

For each piece: cut along the object's real outline (drops floor and background bits),
remove stray specks, fill pinholes, and add a 1px dark edge. Output is 2x so it matches
the room's scale. Outlines are traced by hand on a zoomed grid; adjust KEEP to refine.

    python3 art/clean_originals.py   # writes public/cafe/sprites/<name>.png
"""
import os

from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ART, "archive", "old-cafe", "sprites")
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")
EDGE = (36, 20, 13, 255)

# Outline of each object to keep, in the original sprite's pixels (after cropping to content).
KEEP = {
    "pastry-counter": [(0, 0), (24, 0), (72, 24), (86, 29), (91, 34), (91, 66), (69, 77), (64, 75), (0, 43)],
}


def clean(name, poly, min_speck=6):
    im = Image.open(os.path.join(SRC, f"{name}.png")).convert("RGBA")
    im = im.crop(im.getbbox())
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(poly, fill=255)
    px = im.load()
    m = mask.load()
    for y in range(h):
        for x in range(w):
            if not m[x, y]:
                px[x, y] = (0, 0, 0, 0)

    # drop specks: tiny islands of pixels not connected to the main body
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and not seen[y][x]:
                stack, comp = [(x, y)], []
                seen[y][x] = True
                while stack:
                    cx, cy = stack.pop()
                    comp.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and px[nx, ny][3]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
                if len(comp) < min_speck:
                    for cx, cy in comp:
                        px[cx, cy] = (0, 0, 0, 0)

    # fill pinholes: transparent pixels boxed in on 3+ sides take a neighbour's colour
    for _ in range(2):
        holes = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if px[x, y][3]:
                    continue
                nb = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if px[x + dx, y + dy][3]]
                if len(nb) >= 3:
                    holes.append((x, y, nb[0]))
        for x, y, c in holes:
            px[x, y] = c

    # 1px dark edge around the silhouette, then 2x to match the room
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    out.alpha_composite(im, (1, 1))
    a = out.getchannel("A").load()
    o = out.load()
    edge = [(x, y) for y in range(h + 2) for x in range(w + 2)
            if not a[x, y] and any(0 <= x + dx < w + 2 and 0 <= y + dy < h + 2 and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        o[x, y] = EDGE
    out = out.resize(((w + 2) * 2, (h + 2) * 2), Image.NEAREST)
    out.save(os.path.join(OUT, f"{name}.png"))
    return out


if __name__ == "__main__":
    for name, poly in KEEP.items():
        im = clean(name, poly)
        print(f"{name:16s} {im.size}")

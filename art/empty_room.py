"""Paint movable objects out of the café background so sprites can be moved without ghosts.

1. Every movable sprite's area is filled in from its surroundings (edges inward, using
   colors already next to it), giving an "empty room" background.png.
2. Each movable sprite is trimmed to just the object: pixels that match the new empty
   background are made transparent, so a moved sprite doesn't drag a patch of floor along.
3. Built-in sprites (walls, counter, booth...) lose any pixels that belong to a movable
   object, so moving the object leaves nothing behind in them either.

Automatic fill is a first pass. Touch it up with "Paint background" in /cafe?edit.

    python3 art/empty_room.py

Overwrites public/cafe/background.png and every sprite PNG (not layout.json).
"""
import os
import random

import numpy as np
from PIL import Image, ImageDraw

from cut_assets import ASSETS, OUT, SCENE

# Part of the building; these stay baked into the room.
FIXED = {"pastry-counter", "till", "espresso-bar", "kitchen", "booth", "window-wall", "front-wall-right", "trees-front"}
# How different (sum of RGB) a pixel must be from the empty room to count as part of an object.
OBJECT_THRESHOLD = 60

NEIGHBORS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def polygon_mask(size, poly):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return np.asarray(m) > 0


def fill_from_edges(img, hole, seed=7):
    """Onion-peel fill for leftovers: each ring takes the most common color among its known neighbors."""
    rng = random.Random(seed)
    out = img.copy()
    known = ~hole
    h, w = hole.shape
    while not known.all():
        frontier = []
        for y, x in zip(*np.nonzero(~known)):
            cols = [tuple(out[y + dy, x + dx]) for dx, dy in NEIGHBORS if 0 <= x + dx < w and 0 <= y + dy < h and known[y + dy, x + dx]]
            if cols:
                frontier.append((y, x, cols))
        if not frontier:
            break
        for y, x, cols in frontier:
            counts = {}
            for c in cols:
                counts[c] = counts.get(c, 0) + 1
            best = max(counts.values())
            out[y, x] = rng.choice([c for c, n in counts.items() if n == best])
        for y, x, _ in frontier:
            known[y, x] = True
    return out


def grow(mask, r):
    out = mask.copy()
    for _ in range(r):
        step = out.copy()
        for dx, dy in NEIGHBORS:
            step |= np.roll(np.roll(out, dy, 0), dx, 1)
        out = step
    return out


def synthesize(img, hole, blocked, half=2, radius=40, samples=1600, seed=11):
    """Pixel-by-pixel texture synthesis (Efros-Leung).

    Each hole pixel, filled from the edges inward, takes the color at the center of the nearby
    source window that best matches its already-known surroundings. Rebuilds plank and wall
    texture instead of smearing or pasting whole objects.
    """
    rng = np.random.default_rng(seed)
    h, w = hole.shape
    out = img.astype(np.int32)
    known = ~hole
    k = 2 * half + 1

    # Candidate source windows: near the hole, fully inside the image, touching no hole at all.
    y0, x0 = np.min(np.nonzero(hole), axis=1)
    y1, x1 = np.max(np.nonzero(hole), axis=1)
    area = np.zeros_like(hole)
    area[max(half, y0 - radius) : min(h - half, y1 + radius + 1), max(half, x0 - radius) : min(w - half, x1 + radius + 1)] = True
    clean = area & ~grow(blocked, half)
    cy, cx = np.nonzero(clean)
    if len(cy) == 0:
        return img, False
    pick = rng.choice(len(cy), size=min(samples, len(cy)), replace=False)
    cy, cx = cy[pick], cx[pick]
    dy, dx = np.mgrid[-half : half + 1, -half : half + 1]
    dy, dx = dy.ravel(), dx.ravel()
    cand = out[cy[:, None] + dy, cx[:, None] + dx]  # (n, k*k, 3)

    padded_known = np.pad(known, half)
    padded = np.pad(out, ((half, half), (half, half), (0, 0)))
    while True:
        todo = np.nonzero(hole & ~known)
        if len(todo[0]) == 0:
            break
        counts = sum(np.roll(np.roll(known, oy, 0), ox, 1).astype(int) for ox, oy in NEIGHBORS)
        ring = [(counts[y, x], y, x) for y, x in zip(*todo) if counts[y, x] > 0]
        if not ring:
            break
        ring.sort(reverse=True)
        for _, y, x in ring:
            win = padded[y : y + k, x : x + k].reshape(-1, 3)
            m = padded_known[y : y + k, x : x + k].ravel()
            d = (((cand[:, m] - win[m]) ** 2).sum(axis=(1, 2))) / max(1, m.sum())
            ok = np.nonzero(d <= d.min() * 1.15 + 1)[0]
            c = cand[rng.choice(ok), (k * k) // 2]
            out[y, x] = c
            padded[y + half, x + half] = c
            padded_known[y + half, x + half] = True
            known[y, x] = True
    return out.astype(np.uint8), True


def main():
    scene = np.asarray(Image.open(SCENE).convert("RGB")).copy()
    h, w, _ = scene.shape
    size = (w, h)

    movable = {n: polygon_mask(size, a[0]) for n, a in ASSETS.items() if n not in FIXED}
    holes = {n: grow(m, 1) for n, m in movable.items()}  # a pixel of margin takes outlines/shadows too
    all_holes = np.zeros((h, w), bool)
    for m in holes.values():
        all_holes |= m

    # Smallest first; each filled area becomes usable source for the next.
    empty = scene.copy()
    pending = all_holes.copy()
    for n in sorted(holes, key=lambda k: holes[k].sum()):
        empty, ok = synthesize(empty, holes[n], pending)
        if ok:
            pending &= ~holes[n]
        print(f"  filled {n}" + ("" if ok else " (no clean source, using edge fill)"))
    if pending.any():
        empty = fill_from_edges(empty, pending)
    Image.fromarray(empty).save(f"{OUT}/background.png")

    diff = np.abs(scene.astype(int) - empty.astype(int)).sum(axis=2)
    object_px = {}
    for n, m in movable.items():
        px = m & (diff > OBJECT_THRESHOLD)
        # drop lone specks: keep pixels with at least two object neighbours
        nb = sum(np.roll(np.roll(px, dy, 0), dx, 1).astype(int) for dx, dy in NEIGHBORS)
        object_px[n] = px & (nb >= 2)
    any_object = np.zeros((h, w), bool)
    for m in object_px.values():
        any_object |= m

    rgba = np.dstack([scene, np.full((h, w), 255, np.uint8)])
    for n, (poly, *_rest) in ASSETS.items():
        region = polygon_mask(size, poly)
        alpha = region & (object_px[n] if n in movable else ~any_object)
        sprite = rgba.copy()
        sprite[..., 3] = np.where(alpha, 255, 0)
        box = Image.fromarray(region.astype(np.uint8) * 255).getbbox()
        Image.fromarray(sprite).crop(box).save(f"{OUT}/sprites/{n}.png")
        print(f"{n:18s} {'fixed  ' if n in FIXED else 'movable'} {int(alpha.sum()):5d} px")
    print("empty room ->", f"{OUT}/background.png")


if __name__ == "__main__":
    main()

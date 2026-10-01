"""Snap the wood in the sprites cut from the original onto the café's one wood (WOOD in
draw_room.py), so cut pieces match the drawn ones and the room.

A pixel counts as wood when it's a warm brown (red > green > blue, clearly warm) and not
bright: bright golds, glows and pastries are left alone. Each wood pixel takes the ramp
colour nearest its brightness.

    python3 art/unify_wood.py [name ...]
"""
import os
import sys

import numpy as np
from PIL import Image

from draw_room import WOOD

ART = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")
CUT = ["pastry-counter", "espresso-station", "chalkboard-menu",
       "framed-picture-tall"]  # not the posters: their gold and browns are the art
RAMP = np.array([[int(v[i : i + 2], 16) for i in (1, 3, 5)] for v in WOOD])
RAMP_LUM = RAMP @ np.array([0.299, 0.587, 0.114])
EDGE = (36, 20, 13)  # the dark outline: keep it


def unify(name):
    path = os.path.join(SPRITES, f"{name}.png")
    a = np.asarray(Image.open(path).convert("RGBA")).copy()
    r, g, b = (a[..., i].astype(int) for i in range(3))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    wood = (a[..., 3] > 0) & (r >= g) & (g >= b) & ((r - b) > 18) & (lum < 125) & ~((r == EDGE[0]) & (g == EDGE[1]) & (b == EDGE[2]))
    # map the piece's own wood brightness range onto the ramp, so its shading survives
    lo, hi = np.percentile(lum[wood], [3, 97]) if wood.any() else (0, 1)
    t = np.clip((lum - lo) / max(hi - lo, 1), 0, 1)
    idx = np.clip(np.round(t * (len(WOOD) - 1)).astype(int), 0, len(WOOD) - 1)
    a[..., :3][wood] = RAMP[idx[wood]]
    Image.fromarray(a).save(path)
    return int(wood.sum())


if __name__ == "__main__":
    for n in sys.argv[1:] or CUT:
        print(f"{n:22s} {unify(n)} wood px")

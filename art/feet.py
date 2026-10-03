"""Give the pieces cut from the original a foot for the editor's grid snapping.

An iso piece's outline tells its footprint: the lowest pixel is the front floor corner, the
leftmost and rightmost columns give how far it runs each way. The foot is the BACK floor
corner, the one that has to touch a wall, so the piece sits flush when pushed against one.

    python3 art/feet.py   # updates public/cafe/sprites/_companions.json
"""
import json
import os

import numpy as np
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(os.path.dirname(ART), "public", "cafe", "sprites")
PIECES = ["pastry-counter"]


def back_corner(name):
    a = np.asarray(Image.open(os.path.join(SPRITES, f"{name}.png")).convert("RGBA"))[..., 3] > 8
    cols = [x for x in range(a.shape[1]) if a[:, x].any()]
    low = {x: int(np.nonzero(a[:, x])[0].max()) for x in cols}
    fy = max(low.values())
    front = [x for x in cols if low[x] == fy]
    fx = sum(front) / len(front)
    lx, rx = cols[0], cols[-1]
    A, B = (fx - lx) / 2, (rx - fx) / 2  # units along the two floor axes
    return {"x": round(lx + rx - fx), "y": round(fy - A - B)}, {"a": round(A), "b": round(B), "from": "back"}


WALL_FEET = ["kitchen-doorway"]  # things on a wall that stand on the floor


def wall_foot(name):
    """The lowest point of a piece drawn flat on a wall: where it meets the floor line."""
    a = np.asarray(Image.open(os.path.join(SPRITES, f"{name}.png")).convert("RGBA"))[..., 3] > 8
    ys, xs = np.nonzero(a)
    y = int(ys.max())
    return {"x": int(round(xs[ys == y].mean())), "y": y}


if __name__ == "__main__":
    path = os.path.join(SPRITES, "_companions.json")
    comp = json.load(open(path))
    for n in PIECES:
        foot, size = back_corner(n)
        comp[n] = {**comp.get(n, {}), "foot": foot, "size": size}
        print(n, foot, size)
    for n in WALL_FEET:
        comp[n] = {**comp.get(n, {}), "foot": wall_foot(n)}
        print(n, comp[n]["foot"])
    json.dump(comp, open(path, "w"), indent=1)

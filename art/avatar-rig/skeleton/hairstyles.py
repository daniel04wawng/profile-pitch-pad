"""Hairstyles made from the character's own hair pixels: the hair is trimmed to a new shape
along a clean edge, the way a pixel artist would cut a sprite's hair shorter. Nothing is drawn
from scratch: every hair pixel is the original art's, so it keeps its texture, and the face,
eyes, brows and fringe are never touched (styles that would show the forehead need new art).

Each style is a layer: characters/green/layers/hair-<style>/<view>/head.hide.png (the hair cut
away) and head.fill.png (the new outline along the cut, and for the bun, the bun: a round patch
of the real crown hair set on top, darker where it meets the head, with its own outline).

    python3 art/avatar-rig/skeleton/hairstyles.py
"""
import json
import pathlib

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation

from materials import HEM, material_map

HERE = pathlib.Path(__file__).parent
CH = HERE / "characters" / "green"
INK = np.array([36, 20, 13, 255], np.uint8)

# the head's centre per view, and each style's shape (how far the hair may reach, px)
CENTRE = {"front": (127, 52), "back": (139, 50)}
STYLES = {"tidy": (23, 22, 0), "short": (20.5, 20, 0), "cropped": (18.5, 18.5, 1)}  # rx, ry, drop
# the bun: the short trim, plus a patch of crown hair (centre, radius) moved up to sit on top
BUN = {"front": ((122, 42), (117, 31), 7), "back": ((139, 42), (140, 30), 7)}


def trim(view: str, rx: float, ry: float, drop: float):
    """The hair cut to an oval `rx` x `ry` around the head's centre (lowered by `drop`):
    returns what to take away and the outline to draw along the new edge."""
    head = np.array(Image.open(CH / view / "head.png").convert("RGBA"))
    m = material_map("head", head, HEM[view])
    hair, skin = m == 2, m == 1
    solid = head[:, :, 3] > 0
    yy, xx = np.mgrid[: solid.shape[0], : solid.shape[1]]
    cx, cy = CENTRE[view]
    face = binary_dilation(skin, iterations=3)  # the face, its outline, brows and eyes: kept
    region = binary_dilation(hair, iterations=3) & solid & ~skin & ~face  # the hair and its old outline
    keep = (((xx - cx) / rx) ** 2 + ((yy - cy - drop) / ry) ** 2 <= 1) | face
    cut = region & ~keep
    left = solid & ~cut
    edge = binary_dilation(left) & ~left & binary_dilation(cut) & ~face
    hide = np.zeros_like(head)
    hide[cut, 3] = 255
    fill = np.zeros_like(head)
    fill[edge] = INK
    return hide, fill


def with_bun(view: str, hide: np.ndarray, fill: np.ndarray):
    """Add a bun to a trimmed style: a round patch of the real hair from the crown, moved up to
    sit on top of the head (only where the trimmed head leaves room), shaded darker at its base,
    outlined."""
    head = np.array(Image.open(CH / view / "head.png").convert("RGBA"))
    hair = material_map("head", head, HEM[view]) == 2
    yy, xx = np.mgrid[: hair.shape[0], : hair.shape[1]]
    (sx, sy), (dx, dy), r = BUN[view]
    src = (((xx - sx) / r) ** 2 + ((yy - sy) / (r * 0.85)) ** 2 <= 1) & hair
    bun = np.zeros_like(head)
    ys, xs = np.nonzero(src)
    bun[ys + (dy - sy), xs + (dx - sx)] = head[ys, xs]
    low = (bun[:, :, 3] > 0) & (yy > dy + r * 0.35)
    bun[low, :3] = (bun[low, :3] * 0.8).astype(np.uint8)
    on = bun[:, :, 3] > 0
    bun[binary_dilation(on) & ~on] = INK
    trimmed = (head[:, :, 3] > 0) & ~(hide[:, :, 3] > 0) | (fill[:, :, 3] > 0)
    room = (bun[:, :, 3] > 0) & ~trimmed  # the bun sits behind the head's own top edge
    fill = fill.copy()
    fill[room] = bun[room]
    return fill


def main():
    for name, (rx, ry, drop) in STYLES.items():
        layer = CH / "layers" / f"hair-{name}"
        for view in ("front", "back"):
            d = layer / view
            d.mkdir(parents=True, exist_ok=True)
            hide, fill = trim(view, rx, ry, drop)
            Image.fromarray(hide).save(d / "head.hide.png")
            Image.fromarray(fill).save(d / "head.fill.png")
        json.dump({"slot": "hair", "about": "trimmed from the original hair"}, open(layer / "layer.json", "w"), indent=1)
        print("hair-" + name)
    layer = CH / "layers" / "hair-bun"
    for view in ("front", "back"):
        d = layer / view
        d.mkdir(parents=True, exist_ok=True)
        hide, fill = trim(view, *STYLES["short"])
        Image.fromarray(hide).save(d / "head.hide.png")
        Image.fromarray(with_bun(view, hide, fill)).save(d / "head.fill.png")
    json.dump({"slot": "hair", "about": "the short trim with a top knot of the original hair"}, open(layer / "layer.json", "w"), indent=1)
    print("hair-bun")


if __name__ == "__main__":
    main()

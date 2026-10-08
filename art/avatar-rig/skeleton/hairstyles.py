"""Hairstyles made from the character's own hair pixels: the hair is trimmed to a new shape
along a clean edge, the way a pixel artist would cut a sprite's hair shorter. Nothing is drawn
from scratch: every hair pixel is the original art's, so it keeps its texture, and the face,
eyes, brows and fringe are never touched (styles that would show the forehead need new art).

Each style is a layer: characters/green/layers/hair-<style>/<view>/head.hide.png (the hair cut
away) and head.fill.png (the new outline along the cut, and for the bun, the bun: a round patch
of the real crown hair set over the crown, shaded round, with a shadow on the hair under it).

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
BUN = {"front": ((124, 44), (119, 32), 8.5), "back": ((139, 44), (140, 32), 10)}


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
    sit over the top of the head, shaded round (darker away from the upper left), with a shadow on the
    hair below it. Its outline is black against the background and the hair's own darkest tone
    where it meets the hair."""
    head = np.array(Image.open(CH / view / "head.png").convert("RGBA"))
    hair = material_map("head", head, HEM[view]) == 2
    yy, xx = np.mgrid[: hair.shape[0], : hair.shape[1]]
    (sx, sy), (dx, dy), r = BUN[view]
    src = (((xx - sx) / r) ** 2 + ((yy - sy) / (r * 0.85)) ** 2 <= 1) & hair
    bun = np.zeros_like(head)
    ys, xs = np.nonzero(src)
    bun[ys + (dy - sy), xs + (dx - sx)] = head[ys, xs]
    on = bun[:, :, 3] > 0
    gaps = (((xx - dx) / r) ** 2 + ((yy - dy) / (r * 0.85)) ** 2 <= 1) & ~on  # non-hair specks in the patch
    bun[gaps] = np.median(head[hair], axis=0).astype(np.uint8)
    on = bun[:, :, 3] > 0
    d = np.hypot(xx - (dx - r * 0.35), yy - (dy - r * 0.4)) / r
    # rounded by darkening only: a brighter brown reads as skin to the colour changer
    k = np.where(d < 0.95, 1.0, np.where(d < 1.35, 0.82, 0.68))
    bun[on, :3] = (bun[on, :3] * k[on, None]).astype(np.uint8)
    ring = binary_dilation(on) & ~on
    trimmed = (head[:, :, 3] > 0) & ~(hide[:, :, 3] > 0) | (fill[:, :, 3] > 0)
    out = fill.copy()
    shadow = binary_dilation(ring, iterations=2) & ~ring & ~on & trimmed & (yy > dy)
    out[shadow] = head[shadow]
    out[shadow, :3] = (head[shadow, :3] * 0.65).astype(np.uint8)
    out[shadow, 3] = 255
    out[on] = bun[on]
    tones = head[hair][:, :3].astype(int)
    lum = tones.sum(1)
    out[ring & ~trimmed] = INK
    out[ring & trimmed, :3] = tones[lum <= np.percentile(lum, 8)].mean(0).astype(np.uint8)
    out[ring & trimmed, 3] = 255
    return out


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

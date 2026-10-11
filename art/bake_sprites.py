"""The pastry case's sprites from Daniel's own pixel art of his bakes.

    python3 art/bake_sprites.py   # sources/<name>.webp -> public/cafe/ui/pastry-<name>.png

Each piece of art loses its white background, is shrunk to the size it shows at on the shelf
(about 1:1) and gets the café's outline. Add a bake: put its art in sources/, add it to BAKES,
run this, then add "pastry-<name>" to UI_SPRITES (src/components/cafe/engine/screenData.ts).

The Notion cupcake needs one more step: at that size the cookie's crumb texture drowns its
stamp, so the cookie is flattened and the stamp (the Notion cube's face and its N) drawn back
on crisp, at the cookie's tilt.
"""
import math
import os

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes, label

ART = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(os.path.dirname(ART), "public", "cafe", "ui")
TILT = 15  # degrees the cookie leans in the art
LIGHT, MID, DARK = (246, 184, 88), (228, 152, 60), (170, 92, 28)
INK = (61, 36, 24, 255)


def sprite(name: str, width: int, stamp=None):
    a = np.array(Image.open(os.path.join(ART, "sources", f"{name}.webp")).convert("RGBA")).astype(int)
    lab, _ = label(a[:, :, :3].min(2) > 225)  # the white background, joined to the edge
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    a[np.isin(lab, list(edge)), 3] = 0
    im = Image.fromarray(a.astype(np.uint8))
    im = im.crop(im.getbbox())
    w, h = width, round(im.height * width / im.width)
    arr = np.array(im).astype(float)
    al = arr[:, :, 3:] / 255
    pm = Image.fromarray(np.concatenate([arr[:, :, :3] * al, arr[:, :, 3:]], 2).clip(0, 255).astype(np.uint8))
    sm = np.array(pm.resize((w, h), Image.BOX)).astype(float)
    alpha = sm[:, :, 3]
    rgb = ((sm[:, :, :3] / np.maximum(alpha[..., None] / 255, 1e-6) - 128) * 1.12 + 128).clip(0, 255)
    solid = alpha > 110

    if stamp:
        stamp(rgb, solid, h, w)
    out = np.zeros((h + 2, w + 2, 4), np.uint8)
    out[1:-1, 1:-1, :3] = rgb
    s = np.zeros((h + 2, w + 2), bool)
    s[1:-1, 1:-1] = solid
    out[..., 3] = s * 255
    out[binary_dilation(s) & ~s] = INK
    path = os.path.join(UI, f"pastry-{name}.png")
    Image.fromarray(out).save(path)
    print("->", path)


def notion_stamp(rgb, solid, h, w):
    # the cookie: its biggest orange patch
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lab, _ = label(solid & (r > 165) & (r - b > 80) & (g > 85))
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    cookie = binary_fill_holes(lab == sizes.argmax())
    ys, xs = np.nonzero(cookie)
    cy, cx, half = ys.mean(), xs.mean(), np.sqrt(cookie.sum()) / 2
    th = math.radians(TILT)
    yy, xx = np.mgrid[:h, :w]
    u = ((xx - cx) * math.cos(th) + (yy - cy) * math.sin(th)) / half
    v = (-(xx - cx) * math.sin(th) + (yy - cy) * math.cos(th)) / half
    rgb[cookie] = LIGHT
    rgb[cookie & ~binary_erosion(cookie)] = MID
    ring = np.maximum(abs(u), abs(v))
    stamp = (ring > 0.58) & (ring < 0.74)  # the cube's face
    stamp |= (abs(v) < 0.42) & (((u > -0.38) & (u < -0.18)) | ((u > 0.2) & (u < 0.4)))  # the N's stems
    stamp |= (abs(v) < 0.42) & (abs(v - u * 1.05) < 0.15) & (u > -0.3) & (u < 0.32)  # its diagonal
    rgb[cookie & stamp] = DARK



BAKES = {"notion-cupcake": (52, notion_stamp), "vercel-pavlova": (54, None), "gemma-cookies": (52, None), "composio-cookies": (56, None), "gemma-1b-cake": (72, None), "waymo-cake": (58, None), "coming-soon": (50, None)}  # (coming-soon's art: draw_coming_soon.py)

if __name__ == "__main__":
    for name, (width, stamp) in BAKES.items():
        sprite(name, width, stamp)

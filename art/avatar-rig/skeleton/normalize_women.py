"""Bring the generated women (art/people-src/women/<id>/<pose>.png, 256x352, feet at y=336)
into the rig's frame: 256x280, the first character's scale (he stands 227px tall, they ~296px
at source, so one shared factor keeps their heights relative), feet on y=254, centred on x=128.
Nearest-neighbour only, and alpha hardened (the generator leaves soft edges; pixel art has none).

    python3 art/avatar-rig/skeleton/normalize_women.py
"""
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
SRC = HERE.parent.parent / "people-src" / "women"
OUT = HERE / "characters" / "women-src"
SCALE = 227 / 297
FEET_Y, MID_X = 254, 128


def normalize(path: pathlib.Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    w, h = round(im.width * SCALE), round(im.height * SCALE)
    im = im.resize((w, h), Image.NEAREST)
    a = np.array(im)
    a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
    a[a[:, :, 3] == 0] = 0
    im = Image.fromarray(a)
    out = Image.new("RGBA", (256, 280))
    out.alpha_composite(im, (MID_X - round(128 * SCALE), FEET_Y - round(336 * SCALE)))
    return out


if __name__ == "__main__":
    for d in sorted(p for p in SRC.iterdir() if p.is_dir()):
        (OUT / d.name).mkdir(parents=True, exist_ok=True)
        for f in sorted(d.glob("*.png")):
            im = normalize(f)
            im.save(OUT / d.name / f.name)
            print(d.name, f.name, im.getbbox())

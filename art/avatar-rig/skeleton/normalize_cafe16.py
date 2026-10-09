"""Bring the 16 generated views (art/people-src/cafe16: the man and the woman, jacket on and
off, three-quarter front and back in the tee, and facing you / away / side for all four) into
the rig's frame: 256x280, nearest-neighbour only, alpha hardened, feet on y=254 at x=128.

They're drawn about 4.6x the rig's scale. One factor per person, so every view of them is the
same size: the man to the first character's height (227 px), the woman to Sage's (229 px), each
measured on their tee three-quarter front.

    python3 art/avatar-rig/skeleton/normalize_cafe16.py
"""
import json
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
SRC = HERE.parent.parent / "people-src" / "cafe16"
OUT = HERE / "characters" / "cafe16-src"
FEET_Y, MID_X = 254, 128


def main():
    images = {m["file"]: m for m in json.load(open(SRC / "manifest.json"))["images"]}
    height = lambda f: images[f]["visible_bounds_alpha_gt_32"][3] - images[f]["visible_bounds_alpha_gt_32"][1]  # noqa: E731
    scale = {"man": 227 / height("01-man-tee-front.png"), "woman": 229 / height("03-woman-tee-front.png")}
    OUT.mkdir(parents=True, exist_ok=True)
    for f, m in sorted(images.items()):
        s = scale["woman" if "woman" in f else "man"]
        im = Image.open(SRC / f).convert("RGBA")
        sm = im.resize((round(im.width * s), round(im.height * s)), Image.NEAREST)
        a = np.array(sm)
        a[:, :, 3] = np.where(a[:, :, 3] >= 128, 255, 0)
        a[a[:, :, 3] == 0] = 0
        gx, gy = m["suggested_ground_anchor"]
        out = Image.new("RGBA", (256, 280))
        out.alpha_composite(Image.fromarray(a), (round(MID_X - gx * s), round(FEET_Y - gy * s)))
        out.save(OUT / f)
        print(f, out.getbbox())


if __name__ == "__main__":
    main()

"""The pastry case's "coming soon" bake: a polished silver cloche, a question mark pressed into
it. Painted large with real shading, like the
bake art in sources/, so that shrunk to the shelf (bake_sprites.py) it sits among them.

    python3 art/draw_coming_soon.py   # -> sources/coming-soon.webp, then the sprite
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ART = os.path.dirname(os.path.abspath(__file__))
W, H = 640, 600
INK = (61, 36, 24)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main():
    yy, xx = np.mgrid[:H, :W].astype(float)
    img = np.zeros((H, W, 4), float)

    def paint(mask, rgb):
        img[mask, :3] = rgb[mask] if rgb.ndim == 3 else rgb
        img[mask, 3] = 255

    # the plate: a wide oval, its rim lit along the front
    pcx, pcy, prx, pry = 320, 470, 290, 70
    plate = ((xx - pcx) / prx) ** 2 + ((yy - pcy) / pry) ** 2 <= 1
    t = np.clip((yy - (pcy - pry)) / (2 * pry), 0, 1)[..., None]
    paint(plate, np.array((150, 156, 168)) * (1 - t) + np.array((226, 230, 236)) * t)
    top = ((xx - pcx) / (prx - 22)) ** 2 + ((yy - pcy + 10) / (pry - 22)) ** 2 <= 1
    paint(top, np.full((H, W, 3), (196, 202, 212), float))

    # the dome: half an ellipse sitting on the plate, lit from the upper left
    dcx, dcy, drx, dry = 320, 452, 240, 330
    dome = (((xx - dcx) / drx) ** 2 + ((yy - dcy) / dry) ** 2 <= 1) & (yy <= dcy)
    nx = (xx - dcx) / drx
    ny = (yy - dcy) / dry
    nz = np.sqrt(np.clip(1 - nx**2 - ny**2, 0, 1))
    L = np.array([-0.55, -0.6, 0.58])
    L = L / np.linalg.norm(L)
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    base = np.array((120, 128, 142), float)
    lit = np.array((236, 240, 246), float)
    col = base + (lit - base) * diff[..., None] ** 1.4
    # a warm glow along its foot (the case's light bouncing off the plate)
    warm = np.clip(1 - (dcy - yy) / 90, 0, 1)[..., None] * 0.35
    col = col * (1 - warm) + np.array((232, 170, 110)) * warm
    paint(dome, col)
    # the specular streak and a soft hotspot
    streak = dome & ((((xx - 215) / 34) ** 2 + ((yy - 250) / 120) ** 2) <= 1)
    paint(streak, np.full((H, W, 3), (252, 253, 255), float))
    hot = dome & ((((xx - 250) / 22) ** 2 + ((yy - 170) / 30) ** 2) <= 1)
    paint(hot, np.full((H, W, 3), (255, 255, 255), float))

    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # the rim where the dome meets the plate
    d.ellipse([dcx - drx - 8, dcy - 22, dcx + drx + 8, dcy + 22], outline=(110, 116, 130), width=14)
    d.arc([dcx - drx - 8, dcy - 22, dcx + drx + 8, dcy + 22], 200, 340, fill=(236, 240, 246), width=6)
    # the knob: a little sphere on a stem
    d.rectangle([306, 106, 334, 132], fill=(130, 136, 150))
    d.ellipse([280, 52, 360, 120], fill=(150, 156, 170))
    d.ellipse([294, 62, 326, 88], fill=(236, 240, 246))
    # the question mark, pressed in: a shadow below and right, a lit edge above and left
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 230)
    for (ox, oy), c in (((8, 8), (88, 94, 108)), ((-5, -5), (250, 252, 255)), ((0, 0), (150, 156, 172))):
        d.text((320 + ox, 300 + oy), "?", font=font, fill=c, anchor="mm")
    # a dark outline round it all (the white page outside stays separable)
    a = np.array(im)
    solid = Image.fromarray((a[:, :, 3] > 0).astype(np.uint8) * 255)
    ring = np.array(solid.filter(ImageFilter.MaxFilter(13))) > 0
    out = np.full((H, W, 3), 255, np.uint8)
    out[ring] = INK
    out[a[:, :, 3] > 0] = a[a[:, :, 3] > 0][:, :3]
    Image.fromarray(out).save(os.path.join(ART, "sources", "coming-soon.webp"), lossless=True)


if __name__ == "__main__":
    main()
    import bake_sprites

    bake_sprites.sprite("coming-soon", 50)

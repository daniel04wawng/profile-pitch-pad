"""Accessories for the first character, drawn in code: layers the rig puts over a part.

Each is a full 256x280 frame, transparent except the accessory, lined up on the character's
rest pose, saved where the rig looks for layers:
    characters/green/layers/<layer>/<view>/<part>.png

    beanie   a rust knit beanie with a folded, ribbed cuff (front and back), on the head
    glasses  round dark-rimmed glasses (front only: from behind the head hides them)

    python3 art/avatar-rig/skeleton/accessories.py
"""
import math
import pathlib

from PIL import Image

HERE = pathlib.Path(__file__).parent
LAYERS = HERE / "characters" / "green" / "layers"
SIZE = (256, 280)
INK = (36, 20, 13, 255)
KNIT = [(92, 32, 20, 255), (122, 44, 28, 255), (163, 65, 42, 255), (194, 90, 56, 255), (212, 122, 85, 255)]
RIM = (43, 29, 26, 255)
GLINT = (255, 246, 224, 255)


def canvas():
    return Image.new("RGBA", SIZE, (0, 0, 0, 0))


def outline(im, color=INK):
    """A 1px outline round everything drawn, like every sprite in the café."""
    src = im.copy()
    a = src.getchannel("A").load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            if not a[x, y] and any(0 <= x + dx < w and 0 <= y + dy < h and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                im.putpixel((x, y), color)


def beanie(cx, top, bottom, rx, cuff_h, tilt, light_left=True):
    """A knit beanie: a dome from `top` down to the cuff, and a ribbed cuff above `bottom`.
    `tilt` px drops the cuff toward the right (the head's tilt in the art)."""
    im = canvas()
    px = im.load()
    cy = bottom - cuff_h  # where the dome meets the cuff
    ry = cy - top
    for y in range(top, bottom + 1):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            u = (x - cx) / rx  # -1..1 across
            drop = tilt * (u + 1) / 2  # the cuff (and dome edge) sit lower to the right
            if y <= cy + drop:  # the dome: an ellipse above the cuff line
                dy = (cy + drop - y) / ry
                if u * u + dy * dy > 1:
                    continue
                # shade: light from the upper left, knit rows every 2px
                shade = 2 + (1 if (u < -0.2 if light_left else u > 0.2) and dy > 0.35 else 0) - (1 if u > 0.55 or dy < 0.12 else 0)
                if (y + int(x * 0.5)) % 3 == 0:
                    shade -= 1  # the knit's little ridges
                px[x, y] = KNIT[max(0, min(4, shade))]
            elif y <= cy + drop + cuff_h and abs(u) <= 1.03:  # the folded cuff, ribbed
                rib = (x % 2 == 0)
                edge = y >= cy + drop + cuff_h - 1
                px[x, y] = KNIT[0] if edge else (KNIT[2] if rib else KNIT[1])
    outline(im)
    # a glint on the crown
    for gx, gy in ((cx - rx * 0.45, top + ry * 0.35), (cx - rx * 0.4, top + ry * 0.35 + 1)):
        im.putpixel((round(gx), round(gy)), KNIT[4])
    return im


def ring(im, cx, cy, rx, ry):
    """A lens rim: an ellipse outline, with a glint inside."""
    px = im.load()
    for k in range(64):
        t = 2 * math.pi * k / 64
        px[round(cx + rx * math.cos(t)), round(cy + ry * math.sin(t))] = RIM
    px[round(cx - rx * 0.4), round(cy - ry * 0.4)] = GLINT


def glasses_front():
    im = canvas()
    ring(im, 129.5, 60, 4, 3.5)  # the near eye
    ring(im, 143, 58.5, 3, 3.2)  # the far eye, a little foreshortened by the turn of the head
    px = im.load()
    for x in range(134, 140):  # the bridge
        px[x, 59] = RIM
    for x, y in ((147, 57), (148, 57), (149, 56), (150, 56)):  # the arm back to the ear
        px[x, y] = RIM
    return im


def save(im, layer, view, part="head"):
    d = LAYERS / layer / view
    d.mkdir(parents=True, exist_ok=True)
    im.save(d / f"{part}.png")
    print(layer, view, part, im.getbbox())


if __name__ == "__main__":
    save(beanie(cx=127, top=21, bottom=47, rx=24, cuff_h=6, tilt=-3), "beanie", "front")
    save(beanie(cx=138, top=21, bottom=48, rx=25, cuff_h=6, tilt=2, light_left=True), "beanie", "back")
    save(glasses_front(), "glasses", "front")

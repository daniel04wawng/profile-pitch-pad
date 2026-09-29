"""Cut the 1x café scene into individual sprites + a manifest the site reads.

The full scene stays as the background; each sprite is drawn back on top of its own
pixels, so cut edges never show. Sprites exist for clicking, hover highlight and
depth (an avatar walking behind the big table is hidden by the table sprite).

Re-run after editing the scene or the shapes below:  python3 art/cut_assets.py
It writes cut-manifest.json every time, but never overwrites files you may have edited
in the in-site editor: layout.json, background.png and existing sprite PNGs are only
created if missing. Pass --force to re-cut sprites that already exist.
"""
import json
import os
import sys
from PIL import Image, ImageDraw

ART = os.path.dirname(os.path.abspath(__file__))
SCENE = f"{ART}/source/cafe-night-384x256.png"
OUT = os.path.join(os.path.dirname(ART), "public", "cafe")

# id: (outline polygon in scene pixels, base_y = where it touches the floor for depth sorting,
#      hotspot id or None, label)
ASSETS = {
    "pastry-counter": ([(176, 58), (200, 56), (264, 88), (273, 98), (273, 131), (246, 133), (176, 99)], 131, "projects", "pastry case: my projects"),
    "espresso-bar": ([(184, 36), (226, 36), (226, 70), (184, 66)], 70, "about", "espresso: about me"),
    "menu-board": ([(238, 32), (254, 32), (254, 59), (238, 59)], 60, "menu", "menu: the blog"),
    "kitchen": ([(253, 28), (288, 28), (288, 86), (253, 86)], 86, "now", "the kitchen: in the oven"),
    "till": ([(248, 72), (272, 72), (272, 106), (248, 106)], 106, "contact", "the till: say hi"),
    "piano": ([(290, 80), (342, 80), (342, 132), (290, 132)], 132, "piano", "piano: my music"),
    "record-shelf": ([(336, 108), (375, 108), (375, 150), (336, 150)], 150, "books", "shelf: books + records"),
    "armchair": ([(283, 140), (318, 140), (318, 172), (283, 172)], 172, "chill", "sit and listen"),
    "sax-poster": ([(326, 52), (354, 52), (354, 86), (326, 86)], 86, None, None),
    "big-table": ([(156, 114), (206, 114), (245, 146), (245, 184), (214, 184), (156, 150)], 182, None, None),
    "booth": ([(100, 68), (178, 68), (178, 126), (100, 126)], 124, None, None),
    "window-wall": ([(30, 46), (72, 46), (150, 136), (150, 214), (120, 214), (30, 160)], 214, None, None),
    "front-wall-right": ([(262, 171), (288, 171), (376, 139), (384, 139), (384, 162), (284, 203), (262, 203)], 203, None, None),
    "planter-center": ([(146, 160), (177, 160), (177, 216), (146, 216)], 215, None, None),
    "planter-left": ([(112, 184), (139, 184), (139, 216), (112, 216)], 215, None, None),
    "flowers-right": ([(262, 148), (290, 148), (290, 178), (262, 178)], 177, None, None),
    "aframe-sign": ([(82, 170), (110, 170), (110, 211), (82, 211)], 210, "now", "special of the day"),
    "bistro-set": ([(42, 146), (94, 146), (94, 191), (42, 191)], 190, None, None),
    "lamp-post": ([(15, 66), (29, 66), (29, 156), (15, 156)], 155, None, None),
    "bike": ([(0, 115), (32, 115), (32, 149), (0, 149)], 148, None, None),
    "trees-front": ([(296, 204), (334, 188), (350, 162), (384, 152), (384, 256), (296, 256)], 256, None, None),
}


def main():
    scene = Image.open(SCENE).convert("RGBA")
    os.makedirs(f"{OUT}/sprites", exist_ok=True)
    force = "--force" in sys.argv
    manifest = {"scene": "background.png", "width": scene.width, "height": scene.height, "assets": []}
    for name, (poly, base_y, hotspot, label) in ASSETS.items():
        mask = Image.new("L", scene.size, 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        box = mask.getbbox()
        sprite = Image.new("RGBA", scene.size, (0, 0, 0, 0))
        sprite.paste(scene, (0, 0), mask)
        sprite = sprite.crop(box)
        if force or not os.path.exists(f"{OUT}/sprites/{name}.png"):
            sprite.save(f"{OUT}/sprites/{name}.png")
        manifest["assets"].append(
            {"id": name, "file": f"sprites/{name}.png", "x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1],
             "baseY": base_y, "hotspot": hotspot, "label": label}
        )
    if not os.path.exists(f"{OUT}/background.png"):
        scene.save(f"{OUT}/background.png")
    with open(f"{OUT}/cut-manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    layout = f"{OUT}/layout.json"
    if not os.path.exists(layout):
        with open(layout, "w") as f:
            json.dump(manifest, f, indent=2)
        print("created layout.json")
    print(f"{len(ASSETS)} sprites -> {OUT}")


if __name__ == "__main__":
    main()

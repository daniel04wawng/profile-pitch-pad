"""Build the rig viewer: one HTML page that plays the skeleton walk, front and back, with the
skeleton drawn on, layers to wear, and live appearance: skin tone, hair and outfit colours,
recoloured in the page from each frame's material map (materials.py) so the shading stays.

    python3 art/avatar-rig/skeleton/viewer.py   # writes public/rig-viewer.html (dev only, gitignored)
"""
import base64
import io
import json
import pathlib

import numpy as np
from PIL import Image

from animations import walk
from materials import MATERIALS, material_map, profile, reference_values
from rig import Character, pose, render

HERE = pathlib.Path(__file__).parent
OUT = HERE.parents[2] / "public" / "rig-viewer.html"
BONES = [("pelvis", "neck"), ("neck", "shoulder.free"), ("shoulder.free", "elbow.free"),
         ("pelvis", "hip.near"), ("hip.near", "knee.near"), ("knee.near", "ankle.near"),
         ("pelvis", "hip.far"), ("hip.far", "knee.far"), ("knee.far", "ankle.far")]
CROP = (40, 10, 232, 270)
HAIRS = {"natural": (), "tidy": ("hair-tidy",), "short": ("hair-short",), "cropped": ("hair-cropped",), "bun": ("hair-bun",)}
WEARS = {"none": (), "beanie": ("beanie",), "glasses": ("glasses",), "both": ("beanie", "glasses")}
LOOKS = {f"{h}+{w}": hl + wl for h, hl in HAIRS.items() for w, wl in WEARS.items()}
# who to show: the first character with his layers, and every cut woman as drawn (the hair and
# wear layers are cut from his art, so they're his alone for now)
WHO = {"green": "Green overshirt", "sage-bob": "Sage bob", "blue-pixie": "Blue pixie", "terracotta-curls": "Terracotta curls", "plum-braid": "Plum braid"}


def prof(who: str, view: str) -> dict:
    return profile(HERE / "characters" / who / view)


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _thumb(im):
    x0, y0, x1, y1 = im.getbbox()
    return im.crop((x0 - 3, y0 - 3, x1 + 3, y1 + 3))


def id_character(ch: Character, view: str, mats: dict) -> Character:
    """The same character with every part replaced by its material ids (R = id), so rendering
    it gives each frame's material map; layers (hats, glasses) are id 0: never recoloured."""
    ids = Character.__new__(Character)
    ids.__dict__.update(ch.__dict__)
    ids.images, ids.overlays = {}, {}
    for n, a in ch.images.items():
        m = np.zeros_like(a)
        m[:, :, 0] = material_map(n, a, **mats)
        m[:, :, 3] = np.where(a[:, :, 3] > 0, 255, 0)
        ids.images[n] = m
    for n, lst in ch.overlays.items():
        ids.overlays[n] = [np.dstack([np.zeros(o.shape[:2] + (3,), np.uint8), np.where(o[:, :, 3] > 0, 255, 0).astype(np.uint8)]) for o in lst]
    return ids


def build():
    data = {"frames": {}, "maps": {}, "parts": {}, "joints": {}, "bones": BONES, "materials": MATERIALS, "who": {}, "refs": {}}
    for who, name in WHO.items():
        if not (HERE / "characters" / who / "back" / "parts.json").exists():
            continue
        data["who"][who] = name
        base = Character(HERE / "characters" / who / "front")
        data["refs"][who] = reference_values([(a, material_map(n, a, **prof(who, "front"))) for n, a in base.images.items()])
        looks = LOOKS if who == "green" else {"natural+none": ()}
        for look, layers in looks.items():
            for view in ("front", "back"):
                frames(data, who, look, layers, view)
    OUT.write_text((HERE / "viewer.template.html").read_text().replace("__DATA__", json.dumps(data)))
    print(OUT)


def frames(data, who, look, layers, view):
    ch = Character(HERE / "characters" / who / view, layers=layers)
    ids = id_character(ch, view, prof(who, view))
    key = f"{who}:{look}-{view}"
    data["frames"][key], data["maps"][key], data["joints"][key] = [], [], []
    for f in walk(view):
        data["frames"][key].append(b64(render(ch, view, f).crop(CROP)))
        data["maps"][key].append(b64(render(ids, view, f).crop(CROP)))
        data["joints"][key].append({k: [float(v[0]) - CROP[0], float(v[1]) - CROP[1]] for k, v in pose(ch, view, f).items()})
    if look == "natural+none":
        data["parts"][f"{who}-{view}"] = [{"name": p["part"], "kind": p["kind"], "src": b64(_thumb(Image.fromarray(ch.images[p["part"]])))} for p in ch.parts]
        data["count"] = len(ch.parts)


if __name__ == "__main__":
    build()

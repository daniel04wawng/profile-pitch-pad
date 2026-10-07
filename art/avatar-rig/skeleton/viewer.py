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
from materials import MATERIALS, material_map, reference_values
from rig import Character, pose, render

HERE = pathlib.Path(__file__).parent
OUT = HERE.parents[2] / "public" / "rig-viewer.html"
BONES = [("pelvis", "neck"), ("neck", "shoulder.free"), ("shoulder.free", "elbow.free"),
         ("pelvis", "hip.near"), ("hip.near", "knee.near"), ("knee.near", "ankle.near"),
         ("pelvis", "hip.far"), ("hip.far", "knee.far"), ("knee.far", "ankle.far")]
CROP = (40, 10, 232, 270)
LOOKS = {"none": (), "beanie": ("beanie",), "glasses": ("glasses",), "both": ("beanie", "glasses")}


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _thumb(im):
    x0, y0, x1, y1 = im.getbbox()
    return im.crop((x0 - 3, y0 - 3, x1 + 3, y1 + 3))


def id_character(ch: Character) -> Character:
    """The same character with every part replaced by its material ids (R = id), so rendering
    it gives each frame's material map; layers (hats, glasses) are id 0: never recoloured."""
    ids = Character.__new__(Character)
    ids.__dict__.update(ch.__dict__)
    ids.images, ids.overlays = {}, {}
    for n, a in ch.images.items():
        m = np.zeros_like(a)
        m[:, :, 0] = material_map(n, a)
        m[:, :, 3] = np.where(a[:, :, 3] > 0, 255, 0)
        ids.images[n] = m
    for n, lst in ch.overlays.items():
        ids.overlays[n] = [np.dstack([np.zeros(o.shape[:2] + (3,), np.uint8), np.where(o[:, :, 3] > 0, 255, 0).astype(np.uint8)]) for o in lst]
    return ids


def build():
    data = {"frames": {}, "maps": {}, "parts": {}, "joints": {}, "bones": BONES, "looks": list(LOOKS), "materials": MATERIALS}
    base = Character(HERE / "characters" / "green" / "front")
    data["refs"] = reference_values([(a, material_map(n, a)) for n, a in base.images.items()])
    for look, layers in LOOKS.items():
        for view in ("front", "back"):
            ch = Character(HERE / "characters" / "green" / view, layers=layers)
            ids = id_character(ch)
            key = f"{look}-{view}"
            data["frames"][key], data["maps"][key], data["joints"][key] = [], [], []
            for f in walk(view):
                data["frames"][key].append(b64(render(ch, view, f).crop(CROP)))
                data["maps"][key].append(b64(render(ids, view, f).crop(CROP)))
                data["joints"][key].append({k: [float(v[0]) - CROP[0], float(v[1]) - CROP[1]] for k, v in pose(ch, view, f).items()})
            if look == "none":
                data["parts"][view] = [{"name": p["part"], "kind": p["kind"], "src": b64(_thumb(Image.fromarray(ch.images[p["part"]])))} for p in ch.parts]
                data["count"] = len(ch.parts)
    OUT.write_text((HERE / "viewer.template.html").read_text().replace("__DATA__", json.dumps(data)))
    print(OUT)


if __name__ == "__main__":
    build()

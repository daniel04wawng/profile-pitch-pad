"""Build the rig viewer: a single HTML page that plays the skeleton walk with the skeleton drawn
on, for both views and both shirts, and lays out the parts.

    python3 art/avatar-rig/skeleton/viewer.py   # writes public/rig-viewer.html (dev only, not shipped)
"""
import base64
import io
import json
import pathlib

from PIL import Image

from animations import walk
from bake import recolor
from rig import Character, pose, render

HERE = pathlib.Path(__file__).parent
OUT = HERE.parents[2] / "public" / "rig-viewer.html"
BONES = [("pelvis", "neck"), ("neck", "shoulder.free"), ("shoulder.free", "elbow.free"),
         ("pelvis", "hip.near"), ("hip.near", "knee.near"), ("knee.near", "ankle.near"),
         ("pelvis", "hip.far"), ("hip.far", "knee.far"), ("knee.far", "ankle.far")]
CROP = (40, 10, 232, 270)


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def build():
    data = {"frames": {}, "parts": {}, "joints": {}, "bones": BONES}
    for shirt, hexc in (("green", None), ("navy", "#3c5878")):
        for view in ("front", "back"):
            ch = Character(HERE / "characters" / "green" / view)
            if hexc:
                for p in ch.images:
                    ch.images[p] = recolor(ch.images[p], hexc)
            key = f"{shirt}-{view}"
            data["frames"][key], data["joints"][key] = [], []
            for f in walk(view):
                data["frames"][key].append(b64(render(ch, view, f).crop(CROP)))
                data["joints"][key].append({k: [float(v[0]) - CROP[0], float(v[1]) - CROP[1]] for k, v in pose(ch, view, f).items()})
            if shirt == "green":
                data["parts"][view] = [{"name": p["part"], "kind": p["kind"], "src": b64(Image.fromarray(ch.images[p["part"]]).crop(CROP))} for p in ch.parts]
    OUT.write_text((HERE / "viewer.template.html").read_text().replace("__DATA__", json.dumps(data)))
    print(OUT)


if __name__ == "__main__":
    build()

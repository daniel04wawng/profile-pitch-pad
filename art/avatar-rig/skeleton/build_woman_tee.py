"""The woman with her jacket off: Sage (the woman base model) in just her tee.

There's no art of Sage without her overshirt, but Terracotta wears just a tee with bare arms,
drawn in the same style, pose and scale. So this character is Terracotta's body (torso, arms,
legs, feet, recoloured to Sage's skin, a cream tee and Sage's trousers and shoes) with Sage's own
head on it, set on Terracotta's neck. At café size it reads as the same woman. Her mug arm,
joints and seat are Terracotta's; her mouth (where the mug goes) is Sage's, moved with her head.

    python3 art/avatar-rig/skeleton/build_woman_tee.py   (after cut_women.py)
"""
import json
import pathlib
import shutil

import numpy as np
from PIL import Image

from materials import IDS, MATERIALS, material_map, profile, recolour, reference_values

HERE = pathlib.Path(__file__).parent
CH = HERE / "characters"
HEAD_FROM, BODY_FROM, OUT = "sage-bob", "terracotta-curls", "woman-tee"


def median_hex(arr, m, k):
    px = arr[m == k][:, :3]
    return "#%02x%02x%02x" % tuple(int(c) for c in np.median(px, axis=0)) if len(px) else None


def sage_colours():
    """Sage's own colours, from her front (her tee doesn't show from behind)."""
    spec = json.load(open(CH / HEAD_FROM / "front" / "parts.json"))
    prof = profile(CH / HEAD_FROM / "front")
    px, ms = [], []
    for p in spec["parts"]:
        a = np.array(Image.open(CH / HEAD_FROM / "front" / f"{p['part']}.png"))
        px.append(a.reshape(-1, 4))
        ms.append(material_map(p["part"], a, **prof).reshape(-1))
    px, ms = np.concatenate(px)[None], np.concatenate(ms)[None]
    look = {n: median_hex(px, ms, IDS[n]) for n in ("skin", "trousers", "shoes")}
    look["shirt"] = median_hex(px, ms, IDS["tee"])  # her tee is the cream one
    return look


def skin_or_tee(arr, m):
    """Her terracotta tee and her skin are close in colour; between those two, the skin is the
    more orange and saturated (hue ~23 vs ~12 degrees, saturation ~0.7 vs ~0.5)."""
    rgb = arr[:, :, :3].astype(float) / 255
    mx, mn = rgb.max(2), rgb.min(2)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    either = (m == IDS["skin"]) | (m == IDS["shirt"])
    out = m.copy()
    out[either] = np.where((hue[either] >= 17) & (sat[either] >= 0.6), IDS["skin"], IDS["shirt"])
    return out


def build(view, look):
    hs, bs = json.load(open(CH / HEAD_FROM / view / "parts.json")), json.load(open(CH / BODY_FROM / view / "parts.json"))
    ph, pb = profile(CH / HEAD_FROM / view), profile(CH / BODY_FROM / view)
    sage = {p["part"]: np.array(Image.open(CH / HEAD_FROM / view / f"{p['part']}.png")) for p in hs["parts"]}
    body = {p["part"]: np.array(Image.open(CH / BODY_FROM / view / f"{p['part']}.png")) for p in bs["parts"]}
    refs = reference_values([(a, material_map(n, a, **pb)) for n, a in body.items()])

    d = CH / OUT / view
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for n, a in body.items():
        if n == "head":
            continue
        # (the mug's guard box is left off here: it also covers tee beside the mug, and the mug's
        # own colours match no material anyway)
        Image.fromarray(recolour(a, skin_or_tee(a, material_map(n, a, **{**pb, "fixed": []})), look, refs)).save(d / f"{n}.png")
    # her head on Terracotta's neck
    dx, dy = np.round(np.array(bs["joints"]["neck"]) - np.array(hs["joints"]["neck"])).astype(int)
    head = sage["head"].copy()
    yy = np.mgrid[: head.shape[0], : head.shape[1]][0]
    collar = (material_map("head", head, **ph) == IDS["shirt"]) & (yy >= hs["joints"]["neck"][1] - 6)
    head[collar] = 0  # a bit of her overshirt's collar (not her hair's highlights, higher up)
    moved = np.zeros_like(head)
    ys, xs = np.nonzero(head[:, :, 3] > 0)
    ok = (ys + dy >= 0) & (ys + dy < head.shape[0]) & (xs + dx >= 0) & (xs + dx < head.shape[1])
    moved[ys[ok] + dy, xs[ok] + dx] = head[ys[ok], xs[ok]]
    Image.fromarray(moved).save(d / "head.png")

    spec = json.loads(json.dumps(bs))
    if "mouth" in hs["joints"]:
        spec["joints"]["mouth"] = [hs["joints"]["mouth"][0] + int(dx), hs["joints"]["mouth"][1] + int(dy)]
    # palettes: her skin and hair as Sage's, the body's colours as recoloured
    pal = {}
    for name in MATERIALS.values():
        cols = []
        if name in ("skin", "hair"):
            cols += ph["palette"].get(name, [])
        if name in look and name in pb["palette"]:
            src = np.clip(np.array(pb["palette"][name]), 0, 255).astype(np.uint8).reshape(1, -1, 3)
            arr = np.dstack([src, np.full(src.shape[:2], 255, np.uint8)])
            cols += recolour(arr, np.full(src.shape[:2], IDS[name], np.uint8), {name: look[name]}, refs)[0, :, :3].tolist()
        if cols:
            pal[name] = cols
    spec["palette"] = pal
    spec["zones"] = {"skin": bs.get("zones", {}).get("skin", []) + [[x0 + int(dx), y0 + int(dy), x1 + int(dx), y1 + int(dy)] for x0, y0, x1, y1 in hs.get("zones", {}).get("skin", [])]}
    json.dump(spec, open(d / "parts.json", "w"), indent=1)
    print(view, "head moved", int(dx), int(dy), "colours", look)


if __name__ == "__main__":
    look = sage_colours()
    for v in ("front", "back"):
        build(v, look)

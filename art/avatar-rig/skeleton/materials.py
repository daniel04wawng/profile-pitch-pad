"""Materials: which pixels of a character are skin, hair, which clothes. Appearance changes
(skin tone, hair colour, outfit colours) recolour one material at a time and keep the art's
own shading: a pixel keeps how light or dark it is relative to its material, and takes the new
colour's hue and saturation.

A pixel's material comes from its colour and from which part it's in (the white tee and the
white sneakers are both near-white; one is in the torso, the other in the feet). Outlines
(very dark pixels) are left alone, so the line work stays.

    from materials import MATERIALS, material_map, recolour
"""
import colorsys

import numpy as np

# id -> name. 0 is "not recoloured" (outlines, the mug, anything unrecognised).
MATERIALS = {1: "skin", 2: "hair", 3: "shirt", 4: "tee", 5: "trousers", 6: "shoes"}
IDS = {v: k for k, v in MATERIALS.items()}

# the parts each material can be in (by part name prefix)
WHERE = {
    "skin": ("head", "torso", "forearm"),
    "hair": ("head",),
    "shirt": ("torso", "head", "upper-arm", "forearm"),
    "tee": ("torso",),
    "trousers": ("thigh", "shin", "torso"),
    "shoes": ("foot",),
}


def _hsv(arr):
    rgb = arr[:, :, :3].astype(float) / 255
    mx, mn = rgb.max(2), rgb.min(2)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    return hue, sat, mx, rgb


# where the shirt's hem is, per character and view (rows below it in the torso are the trouser
# tops kept under the hem); above it, grey in the torso is the tee's shading
HEM = {"front": 148, "back": 150}


def profile(folder) -> dict:
    """What a character's parts.json says about its materials, as material_map's keywords:
    its hem line, and for a character with its own palettes (the generated women: their
    shading runs as dark as the outlines, and skin shadow and hair overlap in hue, so the first
    character's colour rules can't sort them) those palettes and the boxes never recoloured."""
    import json
    import pathlib

    spec = json.load(open(pathlib.Path(folder) / "parts.json"))
    view = pathlib.Path(folder).name
    out = {"hem": spec.get("hem", HEM.get(view, 149))}
    if "palette" in spec:
        out["palette"] = spec["palette"]
        out["fixed"] = spec.get("fixed", [])
    return out


def palette_map(part: str, arr: np.ndarray, palette: dict, fixed=(), tol: int = 30) -> np.ndarray:
    """Per pixel, the material whose sampled colours it's nearest (sum of channel differences,
    within `tol`), among the materials that can be in this part; 0 for outlines, the mug,
    anything not close to a material."""
    rgb = arr[:, :, :3].astype(int).reshape(-1, 3)
    best = np.full(len(rgb), tol + 1)
    out = np.zeros(len(rgb), np.uint8)
    for name, cols in palette.items():
        if not any(part.startswith(p) for p in WHERE[name]):
            continue
        for c in cols:
            d = np.abs(rgb - np.array(c)).sum(1)
            hit = d < best
            best[hit] = d[hit]
            out[hit] = IDS[name]
    out = out.reshape(arr.shape[:2])
    out[arr[:, :, 3] == 0] = 0
    for x0, y0, x1, y1 in fixed:
        out[y0:y1, x0:x1] = 0
    return out


def material_map(part: str, arr: np.ndarray, hem: int = 149, palette: dict = None, fixed=()) -> np.ndarray:
    """Per pixel, the material id (0 = leave it)."""
    if palette:
        return palette_map(part, arr, palette, fixed)
    hue, sat, v, rgb = _hsv(arr)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    solid = arr[:, :, 3] > 0
    ink = v < 0.22
    # the hair's darkest shading is about as dark as the outlines: in hair, only true black-brown
    # line work (darker still, and greyer) counts as outline
    hair_ink = (v < 0.16) | ((v < 0.22) & (sat < 0.25))
    out = np.zeros(arr.shape[:2], np.uint8)

    def ok(name):
        return any(part.startswith(p) for p in WHERE[name])

    # skin is warm and fairly saturated; the cream mug is the same hue but much paler
    skin = solid & ~ink & (hue < 40) & (r > 0.62) & (sat > 0.28) & (sat < 0.65)
    shirt = solid & ~ink & (hue >= 45) & (hue <= 100) & (sat > 0.18)
    light = solid & ~ink & (sat < 0.14) & (v > 0.74)
    grey = solid & ~ink & (sat < 0.22) & (v <= 0.72) & ~light  # the trousers, highlights included
    hair = solid & ~hair_ink & ~skin & ((hue < 45) | (sat < 0.12)) & (v < 0.72) & ~light
    if ok("hair"):
        out[hair] = IDS["hair"]
    if ok("skin"):
        out[skin] = IDS["skin"]
    if ok("shirt"):
        out[shirt] = IDS["shirt"]
    yy = np.mgrid[: arr.shape[0], : arr.shape[1]][0]
    if ok("tee"):  # the tee: white, and its grey shading above the hem
        out[light | (grey & (yy < hem))] = IDS["tee"]
    if ok("trousers"):
        below = (yy >= hem) if part.startswith("torso") else np.ones_like(solid)
        out[grey & below & ~(out > 0)] = IDS["trousers"]
    if ok("shoes"):  # the sneakers: every shade of them, so a new colour has no grey left in it
        out[(light | grey) & ~(out > 0)] = IDS["shoes"]
    return out


def reference_values(arrs_and_maps) -> dict:
    """Each material's typical brightness in the art (its median), the anchor for recolouring."""
    vals = {k: [] for k in MATERIALS}
    for arr, m in arrs_and_maps:
        _, _, v, _ = _hsv(arr)
        for k in MATERIALS:
            vals[k].append(v[m == k])
    return {MATERIALS[k]: float(np.median(np.concatenate(v))) if sum(len(x) for x in v) else 0.5 for k, v in vals.items()}


def recolour(arr: np.ndarray, mmap: np.ndarray, appearance: dict, refs: dict) -> np.ndarray:
    """Recolour each material named in `appearance` ({material: "#RRGGBB"}): the new colour's
    hue and saturation, brightness scaled so the material's typical pixel lands on the new
    colour's brightness (the shading stays)."""
    out = arr.copy()
    _, sat, v, _ = _hsv(arr)
    for name, hexc in appearance.items():
        k = IDS[name]
        m = mmap == k
        if not m.any():
            continue
        th, ts, tv = colorsys.rgb_to_hsv(*[int(hexc[i : i + 2], 16) / 255 for i in (1, 3, 5)])
        ref = refs[name]
        # near-white art (the tee, the sneakers) has almost no colour or shading of its own:
        # give it the new colour fully, and keep its shading as gentle steps, not a ratio
        pale = ref > 0.8
        scale = tv / max(1e-6, ref)
        ys, xs = np.nonzero(m)
        for y, x in zip(ys, xs):
            if pale:
                nv = min(1.0, max(0.0, tv + (v[y, x] - ref) * 0.45))
                ns = ts
            else:
                nv = min(1.0, v[y, x] * scale)
                ns = min(1.0, ts * (0.6 + 0.4 * min(1.5, sat[y, x] / max(1e-6, 0.4))))  # keep a little of the art's own variation
            rr, gg, bb = colorsys.hsv_to_rgb(th, ns, nv)
            out[y, x, :3] = [round(rr * 255), round(gg * 255), round(bb * 255)]
    return out

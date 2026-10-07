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


def material_map(part: str, arr: np.ndarray) -> np.ndarray:
    """Per pixel, the material id (0 = leave it)."""
    hue, sat, v, rgb = _hsv(arr)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    solid = arr[:, :, 3] > 0
    ink = v < 0.22
    out = np.zeros(arr.shape[:2], np.uint8)

    def ok(name):
        return any(part.startswith(p) for p in WHERE[name])

    skin = solid & ~ink & (hue < 40) & (r > 0.62) & (sat > 0.15) & (sat < 0.65)
    shirt = solid & ~ink & (hue >= 45) & (hue <= 100) & (sat > 0.18)
    light = solid & ~ink & (sat < 0.14) & (v > 0.74)
    grey = solid & ~ink & (sat < 0.22) & (v <= 0.62)
    hair = solid & ~ink & ~skin & ((hue < 45) | (sat < 0.12)) & (v < 0.72) & ~light
    if ok("hair"):
        out[hair] = IDS["hair"]
    if ok("skin"):
        out[skin] = IDS["skin"]
    if ok("shirt"):
        out[shirt] = IDS["shirt"]
    if ok("tee"):
        out[light] = IDS["tee"]
    if ok("trousers"):
        out[grey & ~(out > 0)] = IDS["trousers"]
    if ok("shoes"):
        out[light] = IDS["shoes"]
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
        scale = tv / max(1e-6, refs[name])
        ys, xs = np.nonzero(m)
        for y, x in zip(ys, xs):
            nv = min(1.0, v[y, x] * scale)
            # keep a little of each pixel's own saturation variation
            ns = min(1.0, ts * (0.6 + 0.4 * min(1.5, sat[y, x] / max(1e-6, 0.4))))
            rr, gg, bb = colorsys.hsv_to_rgb(th, ns, nv)
            out[y, x, :3] = [round(rr * 255), round(gg * 255), round(bb * 255)]
    return out

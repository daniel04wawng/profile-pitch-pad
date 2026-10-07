"""Bake a character on the skeleton rig into the sprite sheets the café plays.

    python3 art/avatar-rig/skeleton/bake.py --character green --id green
    python3 art/avatar-rig/skeleton/bake.py --character green --id green-navy --label "Navy overshirt" --shirt "#3c5878"

The walk comes from the skeleton (rig.py + animations.py) for both views. The other actions
(idle with its sip, sit-down, seated-idle, coffee-sip, stand-up) are still the character's
own baked sheets for now (`--seated-from`), recoloured the same way when asked. The output is the
format the café already plays: public/cafe/avatars/<id>/ (12 sheets + manifest.json), and the
avatar is added to the café's catalog.

Recolouring picks the overshirt by its colour (a hue window), in every part, keeping the
shading; hair, skin, the tee and trousers are other colours and stay as they are.
"""
import argparse
import colorsys
import json
import pathlib
import shutil

import numpy as np
from PIL import Image

from animations import ANIMATIONS
from rig import Character, render

HERE = pathlib.Path(__file__).parent
SITE = HERE.parents[2] / "public" / "cafe" / "avatars"
GAME = (64, 70)  # a game frame: the 256x280 art at a quarter, nearest neighbour
SHIRT_PARTS = None  # every part: the hue window only matches the overshirt, wherever a cut put it (the collar sits in the head part)
SHIRT_HUES = (45, 100)  # degrees: the olive overshirt
SKELETON_SHEETS = {("walk", "front"): "walk-front", ("walk", "back"): "walk-back", ("idle", "front"): "idle-front", ("idle", "back"): "idle-back"}


def recolor(arr: np.ndarray, target_hex: str, hues=SHIRT_HUES) -> np.ndarray:
    """Every pixel whose hue is in `hues` (and has some colour) takes the target's hue and
    saturation, keeping its own brightness, so the shading stays."""
    th, ts, tv = colorsys.rgb_to_hsv(*[int(target_hex[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    out = arr.copy()
    rgb = arr[:, :, :3].reshape(-1, 3) / 255.0
    flat = out.reshape(-1, 4)
    for k, (r, g, b) in enumerate(rgb):
        if flat[k, 3] == 0:
            continue
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s < 0.18 or not (hues[0] <= h * 360 <= hues[1]):
            continue
        # keep the light-to-dark ramp, centred on the target's own brightness
        nv = min(1.0, v * (tv / 0.45))
        nr, ng, nb = colorsys.hsv_to_rgb(th, min(1.0, ts * (s / 0.45)), nv)
        flat[k, :3] = [round(nr * 255), round(ng * 255), round(nb * 255)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", default="green")
    ap.add_argument("--id", required=True)
    ap.add_argument("--label")
    ap.add_argument("--shirt", help="a #RRGGBB for the overshirt")
    ap.add_argument("--layers", default="", help="layers to wear, comma separated (e.g. beanie,glasses); walk only for now")
    ap.add_argument("--seated-from", default="green", help="avatar whose seated sheets to reuse")
    args = ap.parse_args()

    out = SITE / args.id
    out.mkdir(parents=True, exist_ok=True)
    base = SITE / args.seated_from
    manifest = json.load(open(base / "manifest.json"))
    manifest["character"] = args.id

    for view in ("front", "back"):
        ch = Character(HERE / "characters" / args.character / view, layers=tuple(x for x in args.layers.split(",") if x))
        if args.shirt:
            for p in (SHIRT_PARTS or set(ch.images)) & set(ch.images):
                ch.images[p] = recolor(ch.images[p], args.shirt)
        for anim, make in ANIMATIONS.items():
            frames = [render(ch, view, f).resize(GAME, Image.Resampling.NEAREST) for f in make(view)]
            sheet = Image.new("RGBA", (GAME[0] * len(frames), GAME[1]))
            for i, fr in enumerate(frames):
                sheet.alpha_composite(fr, (GAME[0] * i, 0))
            name = SKELETON_SHEETS[(anim, view)]
            sheet.save(out / f"{name}.png")
            n = len(manifest["animations"][name]["durationMs"])
            assert n == len(frames), f"{name}: the manifest times {n} frames, the skeleton made {len(frames)}"

    # the seated actions: reused for now (recoloured to match)
    for name, clip in manifest["animations"].items():
        if (out / clip["sheet"]).exists() and name in SKELETON_SHEETS.values():
            continue
        src = base / clip["sheet"]
        if args.shirt:
            Image.fromarray(recolor(np.array(Image.open(src).convert("RGBA")), args.shirt)).save(out / clip["sheet"])
        elif src.resolve() != (out / clip["sheet"]).resolve():
            shutil.copy(src, out / clip["sheet"])
    json.dump(manifest, open(out / "manifest.json", "w"), indent=2)

    cat_path = SITE / "catalog.json"
    cat = json.load(open(cat_path))
    entry = {"id": args.id, "label": args.label or args.id.replace("-", " ").title(), "manifest": f"{args.id}/manifest.json"}
    cat["avatars"] = [a for a in cat["avatars"] if a["id"] != args.id] + [entry]
    json.dump(cat, open(cat_path, "w"), indent=2)
    print("baked", args.id, "->", out)


if __name__ == "__main__":
    main()

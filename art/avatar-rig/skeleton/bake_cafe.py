"""Bake every café avatar from the skeleton rig: the first character (his own hair and the
styles cut from it) and the four women (each in her own hair and in each
of the others', hair_swap.py), so a hairstyle holds in every pose.

    python3 art/avatar-rig/skeleton/bake_cafe.py

Each avatar is public/cafe/avatars/<id>/ (12 sheets + manifest.json, the format the café plays,
and beside each sheet its material map, <sheet>.mat.png: red = which material each pixel is, so
the café recolours skin, hair and clothes in the browser, keeping the shading),
listed in the catalog with the person it is and whose hair they're wearing, so the changing room
can group them.

The actions:
  walk          the walk (animations.walk)
  idle          standing, a sip of coffee
  sit-down      the thighs swing forward to the seat, the body lowering so the feet stay put
  seated-idle   seated, breathing
  coffee-sip    seated, a sip: the elbow lifts and the forearm turns the mug up to the mouth
                (from behind, the hand goes up out of sight behind the head)
  stand-up      sit-down backwards
"""
import json
import shutil
import math
import pathlib

import numpy as np
from PIL import Image

from animations import walk
from materials import MATERIALS, material_map, profile, reference_values
from rig import Character, pose, render
from viewer import id_character

HERE = pathlib.Path(__file__).parent
SITE = HERE.parents[2] / "public" / "cafe" / "avatars"
GAME = (64, 70)
SEAT_ANGLE = 1.35  # radians the thighs swing forward to sit
# the base models (the changing room groups them by body), and the hairstyle each one's own hair
# is: anyone wears anyone's (hair_swap.py)
MODELS = {"green": "man", "sage-bob": "woman", "blue-pixie": "woman", "terracotta-curls": "woman", "plum-braid": "woman"}
HAIR = {"green": "wavy", "sage-bob": "bob", "blue-pixie": "pixie", "terracotta-curls": "curls", "plum-braid": "braid"}


def seat(ch, view, a, breath=0.0):
    """A frame with the thighs swung forward by `a` and the shins back to hanging, the body
    lowered so the near foot stays on the ground."""
    f = {"angles": {"hip.near": a, "hip.far": a, "knee.near": a, "knee.far": a}, "offset": [0, 0], "breath": breath}
    drop = ch.joints["ankle.near"][1] - pose(ch, view, f)["ankle.near"][1]
    f["offset"] = [0, float(drop)]
    return f


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def sip_turn(ch):
    """How far the forearm turns at the top of a sip: from the mug at rest to the mouth, seen
    from the lifted elbow; from behind, a fixed turn up and in."""
    J = ch.joints
    if "mouth" not in J:
        return -0.5
    ang = lambda v: math.atan2(v[1], v[0])  # noqa: E731
    return ang(J["mouth"] - J["elbow.mug.sip"]) - ang(J["hand.mug"] - J["elbow.mug"])


def sipping(frame, t, turn):
    f = dict(frame)
    f["sip"] = t
    f["turns"] = {**frame.get("turns", {}), "forearm.mug": t * turn}
    return f


def actions(ch, view):
    sit = [seat(ch, view, SEAT_ANGLE * ease(i / 7)) for i in range(8)]
    turn = sip_turn(ch)
    return {
        "walk": walk(view),
        "idle": [sipping({}, t, turn) for t in (0, 0.3, 0.6, 0.9, 1, 0.7, 0.3, 0)],
        "sit-down": sit,
        "stand-up": sit[::-1],
        "seated-idle": [seat(ch, view, SEAT_ANGLE, b) for b in (0, 0, 1, 1, 1, 1, 0, 0)],
        "coffee-sip": [sipping(seat(ch, view, SEAT_ANGLE), t, turn) for t in (0, 0.4, 0.8, 1, 1, 0.8, 0.4, 0)],
    }


SHEET = {  # action, view -> the café's sheet name (the first character's manifest names them)
    **{(a, "front"): a for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip")},
    **{(a, "back"): f"{a}-back" for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip")},
    ("walk", "front"): "walk-front", ("walk", "back"): "walk-back",
    ("idle", "front"): "idle-front", ("idle", "back"): "idle-back",
}


TEMPLATE = json.load(open(SITE / "green" / "manifest.json"))  # read once: green itself is rebaked below


def entry(model, aid, hair):
    return {"id": aid, "label": f"{MODELS[model]}, {hair}", "manifest": f"{aid}/manifest.json", "person": model, "hair": hair, "body": MODELS[model]}


def bake(w, d):
    aid = w if d == w else f"{w}-{d}"
    bake_avatar(w, aid, () if d == w else (f"hair-{d}",))
    return entry(w, aid, HAIR[d])


def bake_avatar(character, aid, layers=(), recolor=None):
    """One avatar: every sheet from the rig, for `character` wearing `layers`, each part passed
    through `recolor` if given."""
    out = SITE / aid
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(json.dumps(TEMPLATE))
    manifest["character"] = aid
    refs = None
    for view in ("front", "back"):
        ch = Character(HERE / "characters" / character / view, layers=layers)
        mats = profile(HERE / "characters" / character / view)
        ids = id_character(ch, view, mats)  # (the material maps, from the art before any recolour)
        if refs is None:
            pairs = [(a, material_map(n, a, **mats)) for n, a in ch.images.items()]
            refs = reference_values(pairs)
            base = {}  # each material's own colour in the art (the changing room's "as drawn" swatch)
            for k, name in MATERIALS.items():
                px = np.concatenate([a[m == k][:, :3] for a, m in pairs])
                if len(px) > 20:
                    base[name] = "#%02x%02x%02x" % tuple(int(c) for c in np.median(px, axis=0))
        if recolor:
            ch.images = {n: recolor(a) for n, a in ch.images.items()}
        for action, frames in actions(ch, view).items():
            name = SHEET[(action, view)]
            sheet = Image.new("RGBA", (GAME[0] * len(frames), GAME[1]))
            mat = Image.new("RGBA", (GAME[0] * len(frames), GAME[1]))
            for i, f in enumerate(frames):
                sheet.alpha_composite(render(ch, view, f).resize(GAME, Image.Resampling.NEAREST), (GAME[0] * i, 0))
                mat.alpha_composite(render(ids, view, f).resize(GAME, Image.Resampling.NEAREST), (GAME[0] * i, 0))
            sheet.save(out / f"{name}.png")
            mat.save(out / f"{name}.mat.png")
            manifest["animations"][name]["materialMap"] = f"{name}.mat.png"
            assert len(manifest["animations"][name]["durationMs"]) == len(frames), name
        # where the chair's seat goes: just under and behind her hips, seated
        p = pose(ch, view, seat(ch, view, SEAT_ANGLE))["pelvis"]
        back = (-3, 6) if view == "front" else (-3, 7)
        at = [round((p[0] + back[0]) / 4, 2), round((p[1] + back[1]) / 4, 2)]
        for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip"):
            manifest["attachments"][SHEET[(a, view)]] = {"chairSeat": at}
    # what each material is, and its typical brightness in the art (the recolour's anchor)
    manifest["materials"] = {"ids": {v: k for k, v in MATERIALS.items()}, "refs": {k: round(v, 4) for k, v in refs.items() if k in base}, "base": base}
    json.dump(manifest, open(out / "manifest.json", "w"), indent=2)


# the first character's own hair, cut to other lengths
GREEN_HAIR = {"tidy": ("hair-tidy",), "short": ("hair-short",), "cropped": ("hair-cropped",), "bun": ("hair-bun",)}


def bake_green_cuts():
    """His own hair cut shorter (hairstyles.py): his alone, they're made from his art."""
    entries = []
    for hair, layers in GREEN_HAIR.items():
        bake_avatar("green", f"green-{hair}", layers)
        entries.append(entry("green", f"green-{hair}", hair))
    return entries


def main():
    entries = []
    for w in MODELS:  # each model in her (his) own hair first: the changing room's tile
        entries += [bake(w, d) for d in [w] + [x for x in MODELS if x != w]]
        if w == "green":
            entries += bake_green_cuts()
    cat_path = SITE / "catalog.json"
    cat = json.load(open(cat_path))
    ids = {e["id"] for e in entries}
    # the café's avatars are exactly these (anything else, like the old navy recolour, goes:
    # colours are picked in the changing room now)
    for a in cat["avatars"]:
        if a["id"] not in ids and (SITE / a["id"]).is_dir():
            shutil.rmtree(SITE / a["id"])
    cat["avatars"] = entries
    json.dump(cat, open(cat_path, "w"), indent=2)
    print("baked", len(entries), "avatars")


if __name__ == "__main__":
    main()

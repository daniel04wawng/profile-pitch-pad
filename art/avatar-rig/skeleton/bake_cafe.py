"""Bake the café's avatars from the skeleton rig, in layers: each base model (the man; the woman,
jacket on and off) once with no hair, then each hairstyle and each thing to wear on its own, so
the café stacks whichever someone picks and recolours them (rig.ts). One new hairstyle is one
more layer per model, not one more avatar per combination.

    python3 art/avatar-rig/skeleton/bake_cafe.py [model ...]

Each model is public/cafe/avatars/<model>/ (see bake_model), listed in the catalog with its body
(man, woman) and jacket (on, off).

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
def seat(ch, view, a, breath=0.0):
    """A frame with the thighs swung forward by `a` and the shins back to hanging, the body
    lowered so the near foot stays on the ground."""
    f = {"angles": {"hip.near": a, "hip.far": a, "knee.near": a, "knee.far": a}, "offset": [0, 0], "breath": breath}
    drop = ch.joints["ankle.near"][1] - pose(ch, view, f)["ankle.near"][1]
    f["offset"] = [0, float(drop)]
    if view in ("back", "north") and a > 0.7:  # from behind, the body and the chair hide the legs once they're up
        f["hide"] = [p["part"] for p in ch.parts if p["part"].split(".")[0] in ("thigh", "shin", "foot")]
    return f


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def sip_turn(ch):
    """How far the forearm turns at the top of a sip: from the mug at rest to the mouth, seen
    from the lifted elbow; from behind, a fixed turn up and in."""
    J = ch.joints
    if "mouth" not in J:  # from behind: up and in behind the head (facing straight away: just in)
        return 0.35 if "shoulder.free" in J and J["elbow.mug"][0] > J["neck"][0] + 10 and J["elbow.mug"][1] < J["neck"][1] + 20 else -0.5
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


# the views for eight directions (facing you, away, side on), when a model has them: S, N, E
# (W is E mirrored). They come from one drawing each, in the model's own hair only.
CARDINAL = {"south": "S", "north": "N", "east": "E"}
SHEET = {  # action, view -> the café's sheet name (the first character's manifest names them)
    **{(a, "front"): a for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip")},
    **{(a, "back"): f"{a}-back" for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip")},
    ("walk", "front"): "walk-front", ("walk", "back"): "walk-back",
    ("idle", "front"): "idle-front", ("idle", "back"): "idle-back",
    **{(a, v): f"{a}-{v}" for v in CARDINAL for a in ("walk", "idle", "sit-down", "stand-up", "seated-idle", "coffee-sip")},
}
ACTION_OF = {"walk": "walk", "idle": "idle", "sit-down": "sit-down", "stand-up": "stand-up", "seated-idle": "seated-idle", "coffee-sip": "coffee-sip"}


def add_cardinal(manifest, view):
    """The manifest entries for a cardinal view: its clips (timed like the front ones) and the
    direction(s) that play them."""
    front = {a: SHEET[(a, "front")] for a in ACTION_OF}
    for a, name in front.items():
        clip = json.loads(json.dumps(manifest["animations"][name]))
        clip["sheet"] = f"{SHEET[(a, view)]}.png"
        clip.pop("rootMotion", None)
        manifest["animations"][SHEET[(a, view)]] = clip
    acts = {a: SHEET[(a, view)] for a in ACTION_OF}
    manifest["directions"][CARDINAL[view]] = {"flipX": False, "actions": acts}
    if view == "east":
        manifest["directions"]["W"] = {"flipX": True, "actions": acts}


TEMPLATE = json.load(open(HERE / "manifest.template.json"))  # the café's clip names, timings, directions

# The base models, and the hairstyles and things to wear each one can have. A hairstyle is
# layers on the model (someone's hair, hair_swap.py; his own cut shorter, hairstyles.py); ()
# is the model's own hair.
HAIRS = ("wavy", "bob", "pixie", "curls", "braid", "tidy", "short", "cropped", "bun")  # the same for everyone, in this order
DONOR = {"wavy": "green", "bob": "sage-bob", "pixie": "blue-pixie", "curls": "terracotta-curls", "braid": "plum-braid",
         "tidy": "green-tidy", "short": "green-short", "cropped": "green-cropped", "bun": "green-bun"}


def hair_layers(character, own):
    """Each hairstyle as layers on `character`: its own hair is (); his cuts on him are his own
    hair's layers (hairstyles.py); everything else is someone's hair (hair_swap.py)."""
    out = {}
    for h in HAIRS:
        if h == own:
            out[h] = ()
        elif character == "green" and DONOR[h].startswith("green-"):
            out[h] = (f"hair-{h}",)
        else:
            out[h] = (f"hair-{DONOR[h]}",)
    return out


# The base models: the man, and the woman with her jacket on or off (her head either way).
MODELS = {
    "man": {"character": "green", "body": "man", "jacket": "on", "own": "wavy"},
    "man-tee": {"character": "man-tee", "body": "man", "jacket": "off", "own": "wavy"},
    "woman": {"character": "sage-bob", "body": "woman", "jacket": "on", "own": "bob"},
    "woman-tee": {"character": "woman-tee", "body": "woman", "jacket": "off", "own": "bob"},
}
for _m in MODELS.values():
    _m["hair"] = hair_layers(_m["character"], _m["own"])


WEAR = {"beanie": ("beanie",), "glasses": ("glasses",)}
BALD = ("hair-none",)


def game(im):
    return im.resize(GAME, Image.Resampling.NEAREST)


def strip(frames):
    sheet = Image.new("RGBA", (GAME[0] * len(frames), GAME[1]))
    for i, fr in enumerate(frames):
        sheet.alpha_composite(fr, (GAME[0] * i, 0))
    return sheet


def only_new(img, base):
    """The pixels of `img` that aren't the same in `base` (a hair layer: the model in that hair,
    less the model with no hair)."""
    a, b = np.array(img), np.array(base)
    keep = (a[:, :, 3] > 0) & ((a != b).any(2))
    a[~keep] = 0
    return Image.fromarray(a)


def mask_character(ch, layer_dir, view):
    """A character whose head is just a layer's hide mask, so rendering it gives that mask where
    the head is in each frame (what a hat hides of the hair under it)."""
    m = Character.__new__(Character)
    m.__dict__.update(ch.__dict__)
    m.overlays = {}
    m.images = {n: np.zeros_like(a) for n, a in ch.images.items()}
    hide = layer_dir / view / "head.hide.png"
    if hide.exists():
        h = np.array(Image.open(hide).convert("RGBA"))
        img = np.zeros_like(h)
        img[h[:, :, 3] > 0] = (255, 255, 255, 255)
        m.images["head"] = img
    return m


def bake_model(mid, spec):
    """One base model in layers: public/cafe/avatars/<mid>/
         <sheet>.png, .mat.png            the body under the hair (no hair), and its materials
         <sheet>.over.png, .over.mat.png  the parts drawn in front of the hair (arms, legs)
         hair/<name>/<sheet>.png, .mat.png  each hairstyle, alone
         wear/<name>/<sheet>.png, .hide.png each thing to wear, and what of the hair it hides
    The café stacks body, hair (less what a hat hides), wear, over; then recolours."""
    out = SITE / mid
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    manifest = json.loads(json.dumps(TEMPLATE))
    manifest["character"] = mid
    cdir = HERE / "characters" / spec["character"]
    refs = base = None
    views = ["front", "back"] + [v for v in CARDINAL if (cdir / v / "parts.json").exists()]
    for view in views:
        cardinal = view in CARDINAL
        if cardinal:
            add_cardinal(manifest, view)
        mats = profile(cdir / view)
        own = Character(cdir / view)
        if refs is None:  # her colours, from her as drawn
            pairs = [(a, material_map(n, a, **mats)) for n, a in own.images.items()]
            refs = reference_values(pairs)
            base = {}
            for k, name in MATERIALS.items():
                px = np.concatenate([a[m == k][:, :3] for a, m in pairs])
                if len(px) > 20:
                    base[name] = "#%02x%02x%02x" % tuple(int(c) for c in np.median(px, axis=0))
        # (a cardinal view has only its own hair: its body is drawn with it, its hair layer empty)
        bald = own if cardinal else Character(cdir / view, layers=BALD)
        bald_ids = id_character(bald, view, mats)
        names = [p["part"] for p in bald.parts]
        under = set(names[: names.index("head") + 1])
        over = set(names) - under
        hairs = {h: Character(cdir / view, layers=layers) for h, layers in spec["hair"].items() if not cardinal or h == spec["own"]}
        hair_ids = {h: id_character(c, view, mats) for h, c in hairs.items()}
        wears = {} if cardinal else {w: Character(cdir / view, layers=BALD + layers) for w, layers in WEAR.items() if (cdir / "layers" / layers[0]).is_dir()}
        masks = {w: mask_character(bald, cdir / "layers" / WEAR[w][0], view) for w in wears}
        for action, frames in actions(own, view).items():
            name = SHEET[(action, view)]
            body, body_m, front, front_m = [], [], [], []
            hair = {h: ([], []) for h in hairs}
            wear = {w: ([], []) for w in wears}
            for f in frames:
                b = render(bald, view, f, only=under)
                body.append(game(b))
                body_m.append(game(render(bald_ids, view, f, only=under)))
                front.append(game(render(bald, view, f, only=over)))
                front_m.append(game(render(bald_ids, view, f, only=over)))
                for h, c in hairs.items():
                    img = render(c, view, f, only=under)
                    keep = only_new(img, b)
                    hm = np.array(render(hair_ids[h], view, f, only=under))
                    hm[np.array(keep)[:, :, 3] == 0] = 0
                    hair[h][0].append(game(keep))
                    hair[h][1].append(game(Image.fromarray(hm)))
                for w, c in wears.items():
                    wear[w][0].append(game(only_new(render(c, view, f, only=under), b)))
                    wear[w][1].append(game(render(masks[w], view, f, only=under)))
            strip(body).save(out / f"{name}.png")
            strip(body_m).save(out / f"{name}.mat.png")
            strip(front).save(out / f"{name}.over.png")
            strip(front_m).save(out / f"{name}.over.mat.png")
            for h, (imgs, ms) in hair.items():
                (out / "hair" / h).mkdir(parents=True, exist_ok=True)
                strip(imgs).save(out / "hair" / h / f"{name}.png")
                strip(ms).save(out / "hair" / h / f"{name}.mat.png")
            for w, (imgs, ms) in wear.items():
                (out / "wear" / w).mkdir(parents=True, exist_ok=True)
                strip(imgs).save(out / "wear" / w / f"{name}.png")
                strip(ms).save(out / "wear" / w / f"{name}.hide.png")
            clip = manifest["animations"][name]
            assert len(clip["durationMs"]) == len(frames), name
            clip.update({"materialMap": f"{name}.mat.png", "over": f"{name}.over.png", "overMap": f"{name}.over.mat.png"})
        # where the chair's seat goes: just under and behind the hips, seated
        p = pose(own, view, seat(own, view, SEAT_ANGLE))["pelvis"]
        back = (-3, 6) if view == "front" else (-3, 7)
        at = [round((p[0] + back[0]) / 4, 2), round((p[1] + back[1]) / 4, 2)]
        for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip"):
            manifest["attachments"][SHEET[(a, view)]] = {"chairSeat": at}
    manifest["materials"] = {"ids": {v: k for k, v in MATERIALS.items()}, "refs": {k: round(v, 4) for k, v in refs.items() if k in base}, "base": base}
    worn = [w for w, layers in WEAR.items() if (cdir / "layers" / layers[0]).is_dir()]
    manifest["layers"] = {"hair": list(spec["hair"]), "defaultHair": spec["own"], "wear": worn, "wearHides": {w: ["hair"] for w in worn},
                          # the cardinal directions are drawn in the model's own hair with nothing worn
                          "cardinalOnly": {"hair": [spec["own"]], "wear": []} if len(views) > 2 else None}
    json.dump(manifest, open(out / "manifest.json", "w"), indent=2)
    print("baked", mid, "hair:", ", ".join(spec["hair"]), "| wear:", ", ".join(wears))
    return {"id": mid, "label": spec["body"] + ("" if spec["jacket"] == "on" else ", jacket off"), "manifest": f"{mid}/manifest.json",
            "body": spec["body"], "jacket": spec["jacket"]}


def main():
    import sys

    only = sys.argv[1:]
    entries = [bake_model(m, s) if not only or m in only else None for m, s in MODELS.items()]
    cat_path = SITE / "catalog.json"
    old = {a["id"]: a for a in json.load(open(cat_path))["avatars"]}
    entries = [e or old[m] for e, m in zip(entries, MODELS)]
    ids = {e["id"] for e in entries}
    for d in SITE.iterdir():  # the café's avatars are exactly these
        if d.is_dir() and d.name not in ids:
            shutil.rmtree(d)
    json.dump({"version": 2, "avatars": entries}, open(cat_path, "w"), indent=2)


if __name__ == "__main__":
    main()

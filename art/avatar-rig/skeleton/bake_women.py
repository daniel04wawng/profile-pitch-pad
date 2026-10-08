"""Bake the women into the café: every action from the skeleton rig, for each woman in her own
hair and in each of the others' (hair_swap.py), so a hairstyle holds in every pose.

    python3 art/avatar-rig/skeleton/bake_women.py

Each avatar is public/cafe/avatars/<id>/ (12 sheets + manifest.json, the format the café
plays, timed like the first character's), listed in the catalog with the woman it is and whose
hair she's wearing, so the changing room can group them.

The actions:
  walk          the walk (animations.walk)
  idle          standing, breathing
  sit-down      the thighs swing forward to the seat, the body lowering so the feet stay put
  seated-idle   seated, breathing
  coffee-sip    seated, a deeper breath (her mug arm is part of the torso, so it can't lift yet)
  stand-up      sit-down backwards
"""
import json
import math
import pathlib

from PIL import Image

from animations import walk
from rig import Character, pose, render

HERE = pathlib.Path(__file__).parent
SITE = HERE.parents[2] / "public" / "cafe" / "avatars"
GAME = (64, 70)
SEAT_ANGLE = 1.35  # radians the thighs swing forward to sit
WOMEN = {"sage-bob": "Sage", "blue-pixie": "Blue", "terracotta-curls": "Terracotta", "plum-braid": "Plum"}
HAIR = {"sage-bob": "bob", "blue-pixie": "pixie", "terracotta-curls": "curls", "plum-braid": "braid"}


def seat(ch, view, a, breath=0.0):
    """A frame with the thighs swung forward by `a` and the shins back to hanging, the body
    lowered so the near foot stays on the ground."""
    f = {"angles": {"hip.near": a, "hip.far": a, "knee.near": a, "knee.far": a}, "offset": [0, 0], "breath": breath}
    drop = ch.joints["ankle.near"][1] - pose(ch, view, f)["ankle.near"][1]
    f["offset"] = [0, float(drop)]
    return f


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def actions(ch, view):
    sit = [seat(ch, view, SEAT_ANGLE * ease(i / 7)) for i in range(8)]
    return {
        "walk": walk(view),
        "idle": [{"breath": b} for b in (0, 0, 1, 2, 2, 2, 1, 0)],
        "sit-down": sit,
        "stand-up": sit[::-1],
        "seated-idle": [seat(ch, view, SEAT_ANGLE, b) for b in (0, 0, 1, 1, 1, 1, 0, 0)],
        "coffee-sip": [seat(ch, view, SEAT_ANGLE, b) for b in (0, 1, 2, 3, 3, 2, 1, 0)],
    }


SHEET = {  # action, view -> the café's sheet name (the first character's manifest names them)
    **{(a, "front"): a for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip")},
    **{(a, "back"): f"{a}-back" for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip")},
    ("walk", "front"): "walk-front", ("walk", "back"): "walk-back",
    ("idle", "front"): "idle-front", ("idle", "back"): "idle-back",
}


def bake(w, d):
    aid = w if d == w else f"{w}-{d}"
    out = SITE / aid
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.load(open(SITE / "green" / "manifest.json"))
    manifest["character"] = aid
    layers = () if d == w else (f"hair-{d}",)
    for view in ("front", "back"):
        ch = Character(HERE / "characters" / w / view, layers=layers)
        for action, frames in actions(ch, view).items():
            name = SHEET[(action, view)]
            sheet = Image.new("RGBA", (GAME[0] * len(frames), GAME[1]))
            for i, f in enumerate(frames):
                sheet.alpha_composite(render(ch, view, f).resize(GAME, Image.Resampling.NEAREST), (GAME[0] * i, 0))
            sheet.save(out / f"{name}.png")
            assert len(manifest["animations"][name]["durationMs"]) == len(frames), name
        # where the chair's seat goes: just under and behind her hips, seated
        p = pose(ch, view, seat(ch, view, SEAT_ANGLE))["pelvis"]
        back = (-3, 6) if view == "front" else (-3, 7)
        at = [round((p[0] + back[0]) / 4, 2), round((p[1] + back[1]) / 4, 2)]
        for a in ("sit-down", "stand-up", "seated-idle", "coffee-sip"):
            manifest["attachments"][SHEET[(a, view)]] = {"chairSeat": at}
    json.dump(manifest, open(out / "manifest.json", "w"), indent=2)
    return {"id": aid, "label": f"{WOMEN[w]}" if d == w else f"{WOMEN[w]}, {HAIR[d]}", "manifest": f"{aid}/manifest.json", "person": w, "hair": HAIR[d]}


def main():
    entries = [bake(w, d) for w in WOMEN for d in [w] + [x for x in WOMEN if x != w]]
    cat_path = SITE / "catalog.json"
    cat = json.load(open(cat_path))
    ids = {e["id"] for e in entries}
    cat["avatars"] = [a for a in cat["avatars"] if a["id"] not in ids] + entries
    json.dump(cat, open(cat_path, "w"), indent=2)
    print("baked", len(entries), "avatars")


if __name__ == "__main__":
    main()

"""The café avatar's animations, as bone motion. Character-independent: these say how the
skeleton moves (rig.py); any character's parts follow along.

Each animation is a list of frames. A frame:
  offset  [dx, dy] px for the whole body (sway, bob)
  breath  px the chest rises (idle)
  angles  per joint, radians: hip.* swings that thigh forward, knee.* bends that shin back
  turns   per rigid part, radians (a foot rolling, an arm swinging)
"""
import json
import math
import pathlib

# which leg is "near" in each view, by body side (skeleton.json): the legs are timed by side,
# so the stride stays in step when someone turns between views
SIDES = json.load(open(pathlib.Path(__file__).with_name("skeleton.json")))["views"]

# the walk, as the first rig tuned it for this café
WALK = {"hipSwing": 0.30, "kneeFlex": 0.45, "bodyHeight": 78, "bodySway": 1.5}
ARM_SWING = {"front": 0.15, "back": 0.12}
FOOT_ROLL = {"front": -0.10, "back": -0.08}


def walk(view: str, frames: int = 8):
    out = []
    for i in range(frames):
        phase = i / frames
        bob = WALK["bodyHeight"] * (1 - math.cos(WALK["hipSwing"] * math.cos(2 * math.pi * phase)))
        sway = WALK["bodySway"] * math.sin(2 * math.pi * phase)
        f = {"offset": [sway, bob], "angles": {}, "turns": {"forearm.free": ARM_SWING[view] * math.cos(2 * math.pi * phase)}}
        for side in ("near", "far"):
            body = SIDES[view]["sides"][side]
            g = (phase + (0.0 if body == "right" else 0.5)) % 1  # right leg leads, left half a stride behind
            f["angles"][f"hip.{side}"] = WALK["hipSwing"] * math.cos(2 * math.pi * g)
            # the knee bends only while that foot is off the ground
            f["angles"][f"knee.{side}"] = WALK["kneeFlex"] * math.sin(math.pi * (g - 0.5) * 2) if g > 0.5 else 0.0
            f["turns"][f"foot.{side}"] = FOOT_ROLL[view] * math.sin(math.pi * max(0, (g - 0.5) * 2)) if g >= 0.5 else 0.0
        out.append(f)
    return out


def breathe(view: str):
    """Standing, breathing: the chest rises and falls a few pixels. (Not the café's idle yet:
    that one lifts the mug for a sip, which needs the mug arm as its own bones.)"""
    return [{"breath": b} for b in (0, 0, 1, 2, 3, 2, 1, 0)]


# what the skeleton bakes today; the other actions are still the character's own sheets
ANIMATIONS = {"walk": walk}

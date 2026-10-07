"""The skeleton rig: pose the bones, then pin each sprite part of a character to its bone.

The rig knows nothing about any one character. A character is a folder per view with part
images and a parts.json saying where its joints are at rest (see cut_green.py); an animation
(animations.py) says, per frame, how the bones move.

The model is 2D projected pseudo-3D, not true 3D bones. Each bone is its drawn (screen) vector
at rest. Swinging it forward by an angle shortens the drawn vector by cos(angle) and adds the
view's projected "forward" direction, scaled by the bone's true length, times sin(angle). For a
bone drawn hanging straight down, that true length is its drawn length over the camera's
vertical scale (cos 35 degrees); swing() checks that a bone is close enough to vertical for
that to hold, or a character can give the length outright (parts.json "lengths"). So one
animation drives several views, as long as each view defines a consistent projected forward
direction and the same near/far meaning (skeleton.json).

Part kinds:
  segment  stretched between two joints (a thigh, a shin, the torso): its length follows the
           bone, its width stays, so a leg swinging toward you foreshortens as it should
  rigid    turned about one joint (a foot, a swinging arm). With "inherit": a segment part,
           it also turns as that bone turns on screen (a hand with its forearm), and the
           animation's own turn is added on top
  follow   carried along with one joint (the head)

Layers: a character can wear layers (hair, glasses, a hat, a jacket): extra images for a part,
drawn right over it and moved exactly as it moves. They live in
characters/<name>/layers/<layer>/<view>/<part>.png, and a bake picks which layers to wear. A
layer can also hide what it covers: <part>.hide.png marks pixels of the part to take away
(a beanie takes away the hair above its cuff, so the hair doesn't stick out around it).

Draw order is the order in parts.json, back to front; an animation frame can move a part in
front of or behind others for that frame ("depth": part -> position in the order).
"""
import json
import math
import pathlib
from typing import Optional

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
SKELETON = json.load(open(HERE / "skeleton.json"))
VERTICAL = math.cos(math.radians(SKELETON["cameraDegrees"]))  # how much a vertical length shrinks
MAX_TILT = math.radians(25)  # how far from vertical a bone may be drawn and still swing() by its drawn length


class Character:
    """One character, one view: its rest joints and its parts (as arrays, full-frame), and the
    layers it's wearing, each drawn over its part (in the order given)."""

    def __init__(self, folder: pathlib.Path, layers: tuple = ()):
        spec = json.load(open(folder / "parts.json"))
        self.size = tuple(spec["frameSize"])
        self.joints = {k: np.array(v, float) for k, v in spec["joints"].items()}
        self.parts = spec["parts"]
        # true lengths for bones not drawn hanging down (bone "a>b" -> px), when a character needs them
        self.lengths = {k: float(v) for k, v in spec.get("lengths", {}).items()}
        self.images = {p["part"]: np.array(Image.open(folder / f"{p['part']}.png").convert("RGBA")) for p in self.parts}
        # part -> the layer images over it
        self.overlays: dict = {}
        view = folder.name
        for layer in layers:
            d = folder.parent / "layers" / layer / view
            if not (folder.parent / "layers" / layer).is_dir():
                raise FileNotFoundError(f"no layer {layer!r} for this character")
            for p in self.parts:  # a layer may skip a view (glasses don't show from behind)
                f = d / f"{p['part']}.png"
                if f.exists():
                    self.overlays.setdefault(p["part"], []).append(np.array(Image.open(f).convert("RGBA")))
                h = d / f"{p['part']}.hide.png"
                if h.exists():  # what the layer covers, taken away from the part underneath
                    hide = np.array(Image.open(h).convert("RGBA"))[:, :, 3] > 0
                    img = self.images[p["part"]].copy()
                    img[hide] = 0
                    self.images[p["part"]] = img


def swing(rest: np.ndarray, angle: float, forward: np.ndarray, name: str = "bone", length: Optional[float] = None) -> np.ndarray:
    """A bone drawn along `rest` (screen px) swung forward by `angle` radians: the drawn vector
    shortens by cos, and the view's projected forward direction takes up the rest, scaled by
    the bone's true length. That length is the drawn length over the camera's vertical scale,
    which only holds for a bone drawn close to vertical; others must give `length`."""
    if length is None:
        tilt = abs(math.atan2(rest[0], rest[1]))
        if tilt > MAX_TILT:
            raise ValueError(f"{name} is drawn {math.degrees(tilt):.0f} degrees off vertical: give its true length in parts.json \"lengths\"")
        length = float(np.linalg.norm(rest)) / VERTICAL
    return rest * math.cos(angle) + forward * length * math.sin(angle)


def pose(ch: Character, view: str, f: dict) -> dict:
    """Where every joint is in this frame. `f` is one animation frame:
    offset [dx, dy] for the whole body, breath (px the chest rises), angles per joint
    (hip.* swing the thigh, knee.* bend the shin back), turns per part (rigid parts)."""
    fwd = np.array(SKELETON["views"][view]["forward"])
    J = ch.joints
    off = np.array(f.get("offset", [0, 0]), float)
    a = f.get("angles", {})
    breath = f.get("breath", 0.0)
    P = {"pelvis": J["pelvis"] + off, "neck": J["neck"] + off + [0, -breath]}
    # the arm rides on the torso: each joint rises with the chest in proportion to its height
    for k in ("shoulder.free", "elbow.free"):
        t = (J["pelvis"][1] - J[k][1]) / max(1e-6, J["pelvis"][1] - J["neck"][1])
        P[k] = J[k] + off + [0, -breath * t]
    for side in ("near", "far"):
        H, K, A = J[f"hip.{side}"], J[f"knee.{side}"], J[f"ankle.{side}"]
        hip = a.get(f"hip.{side}", 0.0)
        knee = a.get(f"knee.{side}", 0.0)
        P[f"hip.{side}"] = H + off
        thigh, shin = f"hip.{side}>knee.{side}", f"knee.{side}>ankle.{side}"
        P[f"knee.{side}"] = P[f"hip.{side}"] + swing(K - H, hip, fwd, thigh, ch.lengths.get(thigh))
        P[f"ankle.{side}"] = P[f"knee.{side}"] + swing(A - K, hip - knee, fwd, shin, ch.lengths.get(shin))
    return P


def _affine(arr, size, coeffs):
    return np.array(Image.fromarray(arr).transform(size, Image.Transform.AFFINE, coeffs, Image.Resampling.NEAREST))


def _rigid(arr, size, origin, target, angle):
    c, s = math.cos(angle), math.sin(angle)
    return _affine(arr, size, (c, s, origin[0] - c * target[0] - s * target[1], -s, c, origin[1] + s * target[0] - c * target[1]))


def _segment(arr, size, origin, rest, target, posed):
    """Map the part drawn along `rest` (from `origin`) onto `posed` (from `target`): along the
    bone it stretches to the new length, across it keeps its width."""
    length = np.linalg.norm(rest)
    u = rest / length
    n = np.array([-u[1], u[0]])
    U = posed / max(1e-6, np.linalg.norm(posed))
    N = np.array([-U[1], U[0]])
    inv = np.linalg.inv(np.outer(posed / length, u) + np.outer(N, n))
    off = origin - inv @ target
    return _affine(arr, size, (inv[0, 0], inv[0, 1], off[0], inv[1, 0], inv[1, 1], off[1]))


def _screen_angle(v: np.ndarray) -> float:
    return math.atan2(v[1], v[0])


def render(ch: Character, view: str, f: dict) -> Image.Image:
    """One frame: every part on its bone, back to front (as parts.json orders them, unless the
    frame moves a part with "depth")."""
    P = pose(ch, view, f)
    J = ch.joints
    turns = f.get("turns", {})
    depth = f.get("depth", {})
    by_name = {p["part"]: p for p in ch.parts}
    order = sorted(range(len(ch.parts)), key=lambda i: (depth.get(ch.parts[i]["part"], i), i))
    frame = Image.new("RGBA", ch.size)
    for p in (ch.parts[i] for i in order):
        for arr in [ch.images[p["part"]], *ch.overlays.get(p["part"], [])]:  # the part, then its layers
            frame.alpha_composite(Image.fromarray(_place(arr, p, ch, J, P, turns, by_name)))
    return frame


def _place(arr, p, ch, J, P, turns, by_name):
    """One part's image (or a layer over it) moved to where the part goes this frame."""
    if p["kind"] == "segment":
        a, b = p["from"], p["to"]
        out = _segment(arr, ch.size, J[a], J[b] - J[a], P[a], P[b] - P[a])
    elif p["kind"] == "rigid":
        j = p["at"]
        angle = turns.get(p["part"], 0.0)
        parent = by_name.get(p.get("inherit", ""))
        if parent:  # turn with the parent bone as it turns on screen, then the part's own turn
            a, b = parent["from"], parent["to"]
            # image y runs down, so a screen turn of +d is a turn of -d for the affine below
            angle -= _screen_angle(P[b] - P[a]) - _screen_angle(J[b] - J[a])
        out = _rigid(arr, ch.size, J[j], P[j], angle)
    else:  # follow
        j = p["at"]
        d = P[j] - J[j]
        out = _affine(arr, ch.size, (1, 0, -d[0], 0, 1, -d[1]))
    return out

"""The skeleton rig: pose the bones, then pin each sprite part of a character to its bone.

The rig knows nothing about any one character. A character is a folder per view with part
images and a parts.json saying where its joints are at rest (see cut_green.py); an animation
(animations.py) says, per frame, how the bones move. Bones swing in 3D, toward and away from
you as well as sideways, and the fixed isometric camera projects that onto the screen, so one
animation drives the front and the back views alike.

Part kinds:
  segment  stretched between two joints (a thigh, a shin, the torso): its length follows the
           bone, its width stays, so a leg swinging toward you foreshortens as it should
  rigid    turned about one joint (a foot, a swinging arm)
  follow   carried along with one joint (the head)
"""
import json
import math
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
SKELETON = json.load(open(HERE / "skeleton.json"))
VERTICAL = math.cos(math.radians(SKELETON["cameraDegrees"]))  # how much a vertical length shrinks


class Character:
    """One character, one view: its rest joints and its parts (as arrays, full-frame)."""

    def __init__(self, folder: pathlib.Path):
        spec = json.load(open(folder / "parts.json"))
        self.size = tuple(spec["frameSize"])
        self.joints = {k: np.array(v, float) for k, v in spec["joints"].items()}
        self.parts = spec["parts"]
        self.images = {p["part"]: np.array(Image.open(folder / f"{p['part']}.png").convert("RGBA")) for p in self.parts}


def swing(rest: np.ndarray, angle: float, forward: np.ndarray) -> np.ndarray:
    """A bone hanging along `rest` (2D, as drawn) swung forward by `angle` radians: the drawn
    vector shortens by cos, and the forward direction (projected) takes up the rest."""
    return rest * math.cos(angle) + forward * (np.linalg.norm(rest) / VERTICAL) * math.sin(angle)


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
    # the shoulder rides on the torso: it rises with the chest in proportion to its height
    t = (J["pelvis"][1] - J["shoulder.free"][1]) / max(1e-6, J["pelvis"][1] - J["neck"][1])
    P["shoulder.free"] = J["shoulder.free"] + off + [0, -breath * t]
    for side in ("near", "far"):
        H, K, A = J[f"hip.{side}"], J[f"knee.{side}"], J[f"ankle.{side}"]
        hip = a.get(f"hip.{side}", 0.0)
        knee = a.get(f"knee.{side}", 0.0)
        P[f"hip.{side}"] = H + off
        P[f"knee.{side}"] = P[f"hip.{side}"] + swing(K - H, hip, fwd)
        P[f"ankle.{side}"] = P[f"knee.{side}"] + swing(A - K, hip - knee, fwd)
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


def render(ch: Character, view: str, f: dict) -> Image.Image:
    """One frame: every part on its bone, back to front."""
    P = pose(ch, view, f)
    J = ch.joints
    turns = f.get("turns", {})
    frame = Image.new("RGBA", ch.size)
    for p in ch.parts:
        arr = ch.images[p["part"]]
        if p["kind"] == "segment":
            a, b = p["from"], p["to"]
            out = _segment(arr, ch.size, J[a], J[b] - J[a], P[a], P[b] - P[a])
        elif p["kind"] == "rigid":
            j = p["at"]
            out = _rigid(arr, ch.size, J[j], P[j], turns.get(p["part"], 0.0))
        else:  # follow
            j = p["at"]
            d = P[j] - J[j]
            out = _affine(arr, ch.size, (1, 0, -d[0], 0, 1, -d[1]))
        frame.alpha_composite(Image.fromarray(out))
    return frame

"""Cut the current character ("green") into parts for the skeleton rig.

A character for the rig is a folder per view (front, back) holding:
  - one PNG per part, the full 256x280 frame with only that part's pixels, so every part
    keeps the position it has in the character's rest pose;
  - parts.json: where its joints are in that rest pose (pixels), and what each part is.

This script makes that folder for the café's first character from its standing images,
reusing the cut lines the earlier rig measured (authoring/green.rig.json, back/back.rig.json).
A new character can come from its own cut script like this one, or straight from parts drawn
to the same template.

    python3 art/avatar-rig/skeleton/cut_green.py
"""
import json
import pathlib

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt, label

HERE = pathlib.Path(__file__).parent
RIG = HERE.parent / "authoring"
OUT = HERE / "characters" / "green"


def poly(size, points):
    m = Image.new("L", size)
    ImageDraw.Draw(m).polygon([tuple(p) for p in points], fill=255)
    return np.array(m) > 0


def save(view, parts, joints, spec):
    d = OUT / view
    d.mkdir(parents=True, exist_ok=True)
    for name, arr in parts.items():
        Image.fromarray(arr).save(d / f"{name}.png")
    json.dump({"frameSize": [256, 280], "joints": joints, "parts": spec}, open(d / "parts.json", "w"), indent=1)
    print(view, sorted(parts))


def split_head(body: np.ndarray, neck_y: float):
    """The head (hair, face, neck) and the torso, cut along the art itself rather than a
    straight line: every pixel is sorted by colour (hair, skin, the rest); hair and skin regions
    (joined across 1px outline gaps) that start above the neck are the head, so the hand
    holding the mug, lower on the chest, stays with the torso; each outline pixel goes with
    whatever it borders."""
    rgb = body[:, :, :3].astype(float) / 255
    mx, mn = rgb.max(2), rgb.min(2)
    v = mx
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    hue = np.zeros_like(v)
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    solid = body[:, :, 3] > 0
    ink = solid & (v < 0.22)  # the outlines
    skin = solid & ~ink & (hue < 40) & (r > 0.62) & (sat > 0.15) & (sat < 0.65)
    hair = solid & ~ink & ~skin & ((hue < 45) | (sat < 0.12)) & (v < 0.72) & ~((sat < 0.12) & (v > 0.6))
    yy = np.mgrid[: body.shape[0], : body.shape[1]][0]
    lab, n = label(binary_dilation(hair | skin, iterations=1))
    head = np.zeros_like(solid)
    for k in range(1, n + 1):
        m = lab == k
        if yy[m].min() < neck_y - 8:  # starts above the neck: hair, face, ears, neck
            head |= m
    head &= hair | skin
    # outlines (and anything left unsorted) go with the nearest sorted pixel
    sorted_ = solid & ~ink
    _, (iy, ix) = distance_transform_edt(~sorted_, return_indices=True)
    head = head | (solid & ~sorted_ & head[iy, ix])
    # small leftovers up at head height (eye whites, highlights) belong to the face
    rest, n = label(solid & ~head)
    for k in range(1, n + 1):
        m = rest == k
        if m.sum() < 40 and yy[m].max() < neck_y:
            head |= m
    return head, solid & ~head


def legs_split(a, leg, knee_y, overlap, shin_bottom=None):
    """A whole trouser leg into thigh and shin, overlapping a little at the knee."""
    yy = np.mgrid[: a.shape[0], : a.shape[1]][0]
    thigh = leg.copy()
    thigh[yy > knee_y + overlap] = 0
    shin = leg.copy()
    shin[yy < knee_y - overlap] = 0
    if shin_bottom is not None:
        shin[yy > shin_bottom] = 0
    return thigh, shin


def front():
    cfg = json.load(open(RIG / "green.rig.json"))
    L = cfg["layers"]
    im = Image.open(RIG / cfg["source"]).convert("RGBA")
    a = np.array(im)
    yy, xx = np.mgrid[: im.height, : im.width]
    boundary = np.where(yy >= L["calfBoundaryY"], L["calfBoundaryX"], L["legBoundaryX"])
    regions = [(yy >= L["nearLegTop"]) & (xx < boundary), (yy >= L["farLegTop"]) & (xx >= boundary)]
    gray = (np.max(a[:, :, :3], axis=2) - np.min(a[:, :, :3], axis=2) < L["graySaturation"]) & (np.max(a[:, :, :3], axis=2) < L["grayMax"])
    body = a.copy()
    legs, feet = [], []
    for idx, region in enumerate(regions):
        leg = a.copy()
        leg[~(region & gray)] = 0
        legs.append(leg)
        body[region & (yy >= L["torsoOverlapY"])] = 0
        fm = poly(im.size, L["footPolygons"][idx])
        fm &= (xx < 134 if idx == 0 else xx >= 134) | (yy > 237 if idx == 0 else yy > 219)
        fm &= yy >= (L["nearShoeTop"] if idx == 0 else L["farShoeTop"])
        foot = a.copy()
        foot[~fm] = 0
        feet.append(foot)
        body[fm & (yy > 218 if idx == 0 else yy > 207)] = 0
    # the free arm (the one without the mug): found by skin, plus its sleeve
    skin = (a[:, :, 0] > 160) & (a[:, :, 0] > a[:, :, 1] * 1.12) & (a[:, :, 1] > 70) & (a[:, :, 2] < 190) & (xx >= 150) & (yy >= 126) & (yy <= 177) & (a[:, :, 3] > 0)
    am = binary_dilation(skin, iterations=2) | poly(im.size, L["sleevePolygon"])
    for leg in legs:
        leg[am] = 0
    arm = a.copy()
    arm[~am] = 0
    body[am & (yy > 126)] = 0
    # the head, cut along the art (hair, face, neck), so the torso can breathe under it
    NECK_Y = 82  # the neck joint: where the head turns and rides
    hm, tm = split_head(body, NECK_Y)
    head = body.copy()
    head[~hm] = 0
    torso = body.copy()
    torso[~tm] = 0
    near, far = cfg["near"], cfg["far"]
    j = {
        "hip.near": near["hip"], "knee.near": near["knee"], "ankle.near": near["ankle"],
        "hip.far": far["hip"], "knee.far": far["knee"], "ankle.far": far["ankle"],
        "shoulder.free": [150, 82],  # where the free arm's sleeve meets the shoulder
        "elbow.free": cfg["freeArm"]["pivot"],  # the forearm swings from here, out of the rolled cuff
        "pelvis": [(near["hip"][0] + far["hip"][0]) / 2, (near["hip"][1] + far["hip"][1]) / 2],
        "neck": [128, NECK_Y],
    }
    tn, sn = legs_split(a, legs[0], near["knee"][1], L["kneeOverlap"], L["nearShinBottom"])
    tf, sf = legs_split(a, legs[1], far["knee"][1], L["kneeOverlap"], L["farShinBottom"])
    parts = {"head": head, "torso": torso, "arm.free": arm, "thigh.near": tn, "shin.near": sn, "foot.near": feet[0], "thigh.far": tf, "shin.far": sf, "foot.far": feet[1]}
    spec = [  # back to front: the body and its free arm, then the far leg, then the near leg
        # (the legs are drawn over the shirt's hem, as the approved frames have them)
        {"part": "torso", "kind": "segment", "from": "pelvis", "to": "neck"},
        {"part": "head", "kind": "follow", "at": "neck"},
        {"part": "arm.free", "kind": "rigid", "at": "elbow.free"},
        {"part": "thigh.far", "kind": "segment", "from": "hip.far", "to": "knee.far"},
        {"part": "shin.far", "kind": "segment", "from": "knee.far", "to": "ankle.far"},
        {"part": "foot.far", "kind": "rigid", "at": "ankle.far"},
        {"part": "thigh.near", "kind": "segment", "from": "hip.near", "to": "knee.near"},
        {"part": "shin.near", "kind": "segment", "from": "knee.near", "to": "ankle.near"},
        {"part": "foot.near", "kind": "rigid", "at": "ankle.near"},
    ]
    save("front", parts, j, spec)


def back():
    cfg = json.load(open(RIG / "back" / "back.rig.json"))
    L = cfg["layers"]
    im = Image.open(RIG / "back" / cfg["source"]).convert("RGBA")
    a = np.array(im)
    yy, xx = np.mgrid[:280, :256]
    armmask = poly(im.size, L["armPolygon"]) & (a[:, :, 3] > 0)
    regions = [(yy >= L["legTop"]) & (xx >= L["boundaryX"]), (yy >= L["legTop"]) & (xx < L["boundaryX"])]
    body = a.copy()
    legs, feet = [], []
    gray = (np.max(a[:, :, :3], axis=2) - np.min(a[:, :, :3], axis=2) < 40) & (np.max(a[:, :, :3], axis=2) < 160)
    white = (np.min(a[:, :, :3], axis=2) > 165) & (a[:, :, 3] > 0)
    footmasks = [
        binary_dilation(white & (yy >= 230) & (xx >= 140), iterations=1) | ((yy >= 237) & (xx >= 140) & (xx <= 157)),
        binary_dilation(white & (yy >= 208) & (yy <= 235) & (xx < 142), iterations=1) | ((yy >= 217) & (yy <= 224) & (xx >= 116) & (xx <= 130)),
    ]
    allfeet = footmasks[0] | footmasks[1]
    for idx, reg in enumerate(regions):
        shoe_y = L["nearShoeTop"] if idx == 0 else L["farShoeTop"]
        legmask = reg & gray & ~armmask & ~allfeet
        footmask = footmasks[idx] & ~armmask
        leg = a.copy()
        leg[~legmask | (yy >= shoe_y)] = 0
        foot = a.copy()
        foot[~footmask] = 0
        legs.append(leg)
        feet.append(foot)
        body[legmask | footmask] = 0
    body[yy >= 155] = 0
    arm = a.copy()
    arm[~armmask] = 0
    body[armmask & (yy >= 116)] = 0
    NECK_Y = 80
    hm, tm = split_head(body, NECK_Y)
    head = body.copy()
    head[~hm] = 0
    torso = body.copy()
    torso[~tm] = 0
    near, far = cfg["near"], cfg["far"]
    j = {
        "hip.near": near["hip"], "knee.near": near["knee"], "ankle.near": near["ankle"],
        "hip.far": far["hip"], "knee.far": far["knee"], "ankle.far": far["ankle"],
        "shoulder.free": [113, 78],
        "elbow.free": cfg["freeArm"]["pivot"],
        "pelvis": [(near["hip"][0] + far["hip"][0]) / 2, (near["hip"][1] + far["hip"][1]) / 2],
        "neck": [138, NECK_Y],
    }
    tn, sn = legs_split(a, legs[0], near["knee"][1], 5)
    tf, sf = legs_split(a, legs[1], far["knee"][1], 5)
    parts = {"head": head, "torso": torso, "arm.free": arm, "thigh.near": tn, "shin.near": sn, "foot.near": feet[0], "thigh.far": tf, "shin.far": sf, "foot.far": feet[1]}
    spec = [  # seen from behind: the legs first, then the body over them, the arm on top
        {"part": "thigh.far", "kind": "segment", "from": "hip.far", "to": "knee.far"},
        {"part": "shin.far", "kind": "segment", "from": "knee.far", "to": "ankle.far"},
        {"part": "foot.far", "kind": "rigid", "at": "ankle.far"},
        {"part": "thigh.near", "kind": "segment", "from": "hip.near", "to": "knee.near"},
        {"part": "shin.near", "kind": "segment", "from": "knee.near", "to": "ankle.near"},
        {"part": "foot.near", "kind": "rigid", "at": "ankle.near"},
        {"part": "torso", "kind": "segment", "from": "pelvis", "to": "neck"},
        {"part": "head", "kind": "follow", "at": "neck"},
        {"part": "arm.free", "kind": "rigid", "at": "elbow.free"},
    ]
    save("back", parts, j, spec)


if __name__ == "__main__":
    front()
    back()

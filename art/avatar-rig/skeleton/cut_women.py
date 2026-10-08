"""Cut the generated women (characters/women-src/<id>/, from normalize_women.py) into parts for
the skeleton rig, the same parts and joints as the first character (cut_green.py).

Each woman has a spec per view: her joints at rest, read off her art, and the few lines a
colour can't find, traced by hand along the art: the free arm's sleeve and forearm, and the two
shoes. Everything else is sorted by colour:
  - a leg is the trouser-coloured pixels on its side of the split below the hips (so the
    shirt's hem, hanging over them, stays on the torso), plus the outlines that border them;
  - the head is everything above the shoulders that isn't the shirt or tee's colours (their
    hair can be as dark as the outlines, so the first character's hair-and-skin cut can't
    find it);
  - what's left is the torso, with the shirt painted in behind the arm and the trouser tops
    kept under the hem, so nothing opens a gap when the limbs swing.

    python3 art/avatar-rig/skeleton/cut_women.py [id ...]
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, distance_transform_edt, label

from cut_green import fill_under, keep_under, legs_split, poly

HERE = pathlib.Path(__file__).parent
SRC = HERE / "characters" / "women-src"
CH = HERE / "characters"

SPECS = {
    "sage-bob": {
        "front": {
            "neck": [130, 80], "headMaxY": 84,
            "hip.near": [119, 150], "knee.near": [118, 190], "ankle.near": [117, 226],
            "hip.far": [142, 148], "knee.far": [141, 186], "ankle.far": [142, 217],
            "shoulder.free": [152, 78], "elbow.free": [161, 123],
            "legTop": 140, "split": 131, "nearSide": "left", "torsoOverlapY": 152,
            "trouserSample": [[110, 175, 128, 215], [134, 175, 150, 210]],
            "sleeve": [(149, 74), (154, 74), (158, 84), (162, 98), (166, 112), (167, 124), (157, 125), (155, 112), (152, 98), (149, 86)],
            "forearm": [(156, 120), (166, 119), (169, 140), (169, 166), (158, 167), (157, 152), (154, 140)],
            "foot.near": [(99, 222), (131, 222), (131, 256), (99, 256)],
            "foot.far": [(132, 214), (171, 214), (171, 247), (132, 247)],
            "hem": 137, "chinY": 72, "legsOnlyY": 162,
            "shirtSample": [[95, 95, 115, 120], [131, 120, 146, 134], [152, 100, 158, 140]],
            "materials": {"skin": [[126, 57, 138, 66], [126, 70, 138, 80], [112, 110, 125, 118], [158, 128, 164, 150]],
                          "hair": [[112, 32, 140, 48], [100, 55, 112, 70]], "shirt": [[92, 86, 108, 104], [96, 122, 112, 140], [152, 100, 157, 140]],
                          "tee": [[130, 84, 140, 96], [131, 120, 146, 134]], "trousers": [[110, 175, 128, 215], [134, 175, 150, 210]],
                          "shoes": [[104, 232, 125, 250], [136, 222, 160, 238]]},
            "fixed": [[137, 97, 152, 119]],
        },
        "back": {
            "neck": [127, 82], "headMaxY": 86,
            "hip.near": [137, 155], "knee.near": [135, 193], "ankle.near": [136, 233],
            "hip.far": [112, 157], "knee.far": [110, 193], "ankle.far": [107, 219],
            "shoulder.free": [101, 82], "elbow.free": [99, 124],
            "legTop": 148, "split": 123, "nearSide": "right", "torsoOverlapY": 160,
            "trouserSample": [[100, 175, 118, 205], [128, 175, 146, 215]],
            "sleeve": [(97, 79), (104, 79), (104, 95), (103, 110), (104, 127), (96, 128), (89, 124), (89, 105), (93, 90)],
            "forearm": [(93, 121), (105, 121), (106, 140), (104, 158), (93, 158), (92, 140)],
            "foot.near": [(125, 226), (167, 222), (167, 256), (125, 256)],
            "foot.far": [(89, 208), (126, 208), (124, 226), (112, 237), (89, 245)],
            "hem": 158, "chinY": 76, "legsOnlyY": 165,
            "shirtSample": [[110, 100, 140, 140], [92, 90, 100, 110]],
            "materials": {"skin": [[150, 108, 160, 118], [95, 128, 102, 150], [135, 56, 142, 68]],
                          "hair": [[100, 40, 140, 70]], "shirt": [[110, 100, 140, 140], [92, 90, 100, 110]],
                          "trousers": [[100, 175, 118, 205], [128, 175, 146, 215]], "shoes": [[128, 238, 158, 250], [96, 224, 115, 236]]},
            "fixed": [[148, 98, 162, 109]],
        },
    },
}

def spec(neck, head_max, chin, near, far, shoulder, elbow, leg_top, split, near_side, overlap, legs_only, hem,
         sleeve, forearm, foot_near, foot_far, skin, hair, shirt, tee, trousers, shoes, fixed):
    """One view's spec, from the measurements read off the art (see SPECS)."""
    out = {"neck": neck, "headMaxY": head_max, "chinY": chin, "shoulder.free": shoulder, "elbow.free": elbow,
           "legTop": leg_top, "split": split, "nearSide": near_side, "torsoOverlapY": overlap, "legsOnlyY": legs_only,
           "hem": hem, "sleeve": sleeve, "forearm": forearm, "foot.near": foot_near, "foot.far": foot_far,
           "trouserSample": trousers, "shirtSample": shirt + tee, "fixed": fixed,
           "materials": {k: v for k, v in {"skin": skin, "hair": hair, "shirt": shirt, "tee": tee, "trousers": trousers, "shoes": shoes}.items() if v}}
    for j, (h, k, a) in (("near", near), ("far", far)):
        out[f"hip.{j}"], out[f"knee.{j}"], out[f"ankle.{j}"] = h, k, a
    return out


def box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# in the torso, skin and hair are only looked for in these boxes (materials.py ZONED)
NECK_AND_MUG_HAND = {"front": [[105, 68, 145, 95], [96, 96, 140, 135]], "back": [[115, 60, 150, 90], [138, 96, 166, 145]]}
for v in ("front", "back"):
    SPECS["sage-bob"][v]["zones"] = {"skin": NECK_AND_MUG_HAND[v]}

SPECS["blue-pixie"] = {
    "front": spec([128, 80], 82, 70, ([114, 152], [112, 190], [110, 221]), ([138, 150], [137, 186], [138, 212]), [149, 76], [157, 123],
                  138, 129, "left", 150, 158, 133,
                  [(145, 72), (150, 72), (155, 85), (159, 100), (162, 112), (163, 124), (153, 125), (152, 112), (150, 100), (147, 88)],
                  [(153, 120), (163, 119), (166, 140), (167, 166), (155, 166), (155, 145), (154, 132)],
                  box(96, 218, 128, 254), box(130, 209, 166, 242),
                  [[132, 58, 142, 68], [108, 108, 122, 120], [156, 130, 163, 150]], [[108, 35, 140, 50]],
                  [[92, 95, 110, 120], [95, 130, 112, 145]], [[120, 85, 135, 98]],
                  [[105, 170, 125, 210], [132, 170, 145, 205]], [[102, 232, 118, 246], [135, 218, 155, 232]], [[130, 100, 152, 128]]),
    "back": spec([125, 80], 80, 72, ([138, 158], [137, 195], [138, 231]), ([112, 160], [110, 195], [106, 217]), [99, 80], [98, 124],
                 150, 124, "right", 160, 162, 155,
                 [(95, 77), (101, 76), (101, 95), (101, 110), (102, 125), (93, 125), (89, 118), (90, 100), (92, 88)],
                 [(93, 121), (103, 121), (102, 140), (101, 156), (94, 156), (93, 140)],
                 box(125, 224, 167, 256), box(89, 212, 123, 242),
                 [[95, 128, 100, 150], [150, 108, 160, 118]], [[105, 40, 140, 65]],
                 [[110, 95, 140, 140], [92, 95, 99, 115]], [],
                 [[100, 175, 120, 205], [128, 175, 145, 215]], [[128, 238, 158, 250], [96, 222, 115, 234]], [[148, 99, 163, 108]]),
}
SPECS["terracotta-curls"] = {  # no overshirt: the terracotta tee is her "shirt", arms bare below its short sleeves
    "front": spec([125, 84], 86, 76, ([116, 152], [115, 190], [113, 222]), ([140, 150], [140, 187], [142, 214]), [146, 80], [155, 128],
                  142, 130, "left", 146, 150, 142,
                  [(143, 76), (149, 76), (153, 90), (156, 100), (158, 115), (160, 130), (152, 131), (150, 118), (148, 105), (145, 92)],
                  [(151, 125), (160, 124), (163, 140), (167, 152), (167, 167), (155, 167), (154, 148), (151, 138)],
                  box(98, 219, 129, 254), box(131, 211, 167, 244),
                  [[125, 62, 138, 75], [110, 110, 125, 120], [96, 110, 104, 130], [153, 130, 160, 155]], [[100, 35, 140, 55]],
                  [[105, 85, 125, 100], [130, 120, 145, 135]], [],
                  [[105, 170, 125, 210], [133, 170, 148, 205]], [[103, 232, 120, 246], [138, 222, 158, 234]], [[130, 100, 150, 123]]),
    "back": spec([125, 84], 86, 76, ([138, 150], [137, 190], [140, 233]), ([112, 152], [110, 190], [108, 219]), [99, 82], [103, 126],
                 140, 125, "right", 146, 147, 141,
                 [(97, 78), (101, 78), (102, 100), (108, 106), (110, 118), (108, 130), (98, 131), (95, 118), (92, 104), (94, 90)],
                 [(99, 125), (109, 125), (108, 132), (99, 132)],
                 box(126, 227, 168, 256), box(92, 212, 124, 242),
                 [[97, 105, 107, 125], [143, 110, 152, 135]], [[100, 40, 140, 70]],
                 [[110, 90, 140, 130]], [],
                 [[100, 170, 120, 205], [128, 170, 145, 215]], [[130, 238, 158, 250], [98, 220, 118, 233]], [[148, 100, 162, 110]]),
}
SPECS["plum-braid"] = {  # the braid hangs over the shoulder: below the head's line it rides with the torso
    "front": spec([130, 80], 82, 70, ([115, 155], [114, 192], [113, 226]), ([140, 153], [140, 189], [142, 216]), [148, 76], [160, 126],
                  142, 130, "left", 152, 156, 140,
                  [(144, 72), (150, 72), (155, 84), (160, 100), (163, 114), (165, 128), (155, 129), (153, 114), (150, 100), (147, 86)],
                  [(155, 124), (165, 123), (167, 140), (170, 152), (170, 168), (157, 168), (157, 150), (156, 135)],
                  box(98, 224, 129, 256), box(131, 214, 164, 247),
                  [[132, 58, 142, 70], [112, 108, 125, 120], [158, 130, 165, 150]], [[115, 35, 140, 50], [105, 80, 115, 110]],
                  [[92, 100, 105, 125], [150, 95, 157, 115]], [[122, 85, 135, 98], [122, 130, 138, 140]],
                  [[105, 170, 125, 210], [133, 170, 148, 205]], [[103, 234, 120, 248], [136, 222, 156, 236]], [[130, 100, 152, 125]]),
    "back": spec([130, 78], 80, 70, ([136, 160], [135, 195], [136, 231]), ([110, 160], [108, 195], [105, 219]), [98, 85], [97, 128],
                 152, 122, "right", 162, 165, 158,
                 [(96, 82), (100, 82), (100, 100), (100, 128), (92, 129), (90, 115), (91, 98), (93, 88)],
                 [(93, 125), (102, 125), (102, 145), (101, 163), (94, 163), (93, 145)],
                 box(123, 223, 166, 256), box(89, 211, 121, 242),
                 [[94, 132, 100, 155], [150, 110, 160, 125]], [[100, 45, 140, 62], [103, 90, 113, 130]],
                 [[120, 100, 145, 145], [91, 95, 99, 120]], [],
                 [[100, 175, 118, 205], [127, 175, 145, 215]], [[130, 238, 158, 250], [96, 222, 115, 234]], [[148, 102, 163, 110]]),
}

for cid in ("blue-pixie", "terracotta-curls", "plum-braid"):
    for v in ("front", "back"):
        SPECS[cid][v]["zones"] = {"skin": NECK_AND_MUG_HAND[v]}
SPECS["plum-braid"]["front"]["zones"]["hair"] = [[103, 62, 122, 132]]
SPECS["plum-braid"]["back"]["zones"]["hair"] = [[96, 50, 124, 148]]

FRONT_ORDER = ["torso", "head", "upper-arm.free", "forearm.free", "thigh.far", "shin.far", "foot.far", "thigh.near", "shin.near", "foot.near"]
BACK_ORDER = ["thigh.far", "shin.far", "foot.far", "thigh.near", "shin.near", "foot.near", "torso", "head", "upper-arm.free", "forearm.free"]
KINDS = {
    "torso": {"kind": "segment", "from": "pelvis", "to": "neck"},
    "head": {"kind": "follow", "at": "neck"},
    "upper-arm.free": {"kind": "segment", "from": "shoulder.free", "to": "elbow.free"},
    "forearm.free": {"kind": "rigid", "at": "elbow.free"},
    **{f"thigh.{s}": {"kind": "segment", "from": f"hip.{s}", "to": f"knee.{s}"} for s in ("near", "far")},
    **{f"shin.{s}": {"kind": "segment", "from": f"knee.{s}", "to": f"ankle.{s}"} for s in ("near", "far")},
    **{f"foot.{s}": {"kind": "rigid", "at": f"ankle.{s}"} for s in ("near", "far")},
}


def near_palette(a: np.ndarray, boxes, tol: float = 34) -> np.ndarray:
    """Pixels close in colour to any colour sampled in `boxes` (the trousers' own shades)."""
    rgb = a[:, :, :3].astype(int)
    samples = np.concatenate([rgb[y0:y1, x0:x1][a[y0:y1, x0:x1, 3] > 0] for x0, y0, x1, y1 in boxes])
    samples = np.unique(samples // 4, axis=0) * 4 + 2
    flat = rgb.reshape(-1, 3)
    best = np.full(len(flat), 1e9)
    for c in samples:
        best = np.minimum(best, np.abs(flat - c).sum(1))
    return (best <= tol).reshape(a.shape[:2]) & (a[:, :, 3] > 0)


def with_outlines(a: np.ndarray, mask: np.ndarray, others: np.ndarray) -> np.ndarray:
    """`mask` plus the dark outline pixels whose nearest non-outline pixel is in it (not in
    `others`, the colours sorted elsewhere)."""
    solid = a[:, :, 3] > 0
    ink = solid & (a[:, :, :3].max(2) < 60)
    sorted_ = (mask | others) & ~ink
    _, (iy, ix) = distance_transform_edt(~sorted_, return_indices=True)
    return (mask & ~ink) | (ink & mask[iy, ix] & ~others[iy, ix]) | (ink & mask & ~others & sorted_)


def _hsv(px: np.ndarray):
    rgb = px / 255
    mx, mn = rgb.max(1), rgb.min(1)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return hue, (mx - mn) / np.maximum(mx, 1e-6), mx


# what each material can look like at all, so a box's edge that catches a lapel or a sleeve
# can't put blue in the tee or olive in the skin
LOOKS_LIKE = {
    "tee": lambda h, s, v: (s < 0.25) & (v > 0.5),  # the cream tees
    "skin": lambda h, s, v: ((h < 45) | (h > 340)) & (s > 0.15) & (v > 0.2),
    "shoes": lambda h, s, v: s < 0.25,  # the white sneakers, and their grey shading
}


def palette(a: np.ndarray, boxes: dict) -> dict:
    """Each material's colours, from boxes of mostly that material in the art. A box's edge
    can catch a neighbour (a sleeve's edge in a box of forearm), so a colour seen in several
    materials' boxes goes to the one it's most common in (as a share of that material's
    samples); a colour seen once doesn't count, and outlines are left out."""
    share, seen = {}, {}
    for name, bs in boxes.items():
        px = np.concatenate([a[y0:y1, x0:x1][a[y0:y1, x0:x1, 3] > 0][:, :3] for x0, y0, x1, y1 in bs]).astype(int)
        px = px[px.max(1) >= 30]
        px = px[LOOKS_LIKE.get(name, lambda h, sat, v: np.ones_like(v, bool))(*_hsv(px))]
        cols, n = np.unique(px // 3 * 3 + 1, axis=0, return_counts=True)
        for c, k in zip(map(tuple, cols.tolist()), n.tolist()):
            share.setdefault(c, {})[name] = k / len(px)
            seen[c] = seen.get(c, 0) + k
    out = {name: [] for name in boxes}
    for c, by in share.items():
        if seen[c] >= 2:
            out[max(by, key=by.get)].append(list(c))
    return out


def cut(cid: str, view: str):
    s = SPECS[cid][view]
    im = Image.open(SRC / cid / "stand-front.png" if view == "front" else SRC / cid / "stand-back.png").convert("RGBA")
    a = np.array(im)
    solid = a[:, :, 3] > 0
    yy, xx = np.mgrid[: a.shape[0], : a.shape[1]]
    size = im.size

    # a shoe is everything in its (generous) outline that isn't trouser-coloured: the hem the
    # outline overlaps stays with the leg, the shoe's own outline and sock go with the shoe
    trouser_colour = near_palette(a, s["trouserSample"])
    feet = {side: poly(size, s[f"foot.{side}"]) & solid & ~trouser_colour for side in ("near", "far")}
    allfeet = feet["near"] | feet["far"]
    forearm_m = poly(size, s["forearm"]) & solid
    sleeve_m = poly(size, s["sleeve"]) & solid
    arm_all = forearm_m | sleeve_m

    trousers = trouser_colour & (yy >= s["legTop"]) & ~allfeet & ~arm_all
    # only what's joined to the legs (a dark patch of shirt or hair the same colour isn't)
    lab, n = label(trousers)
    keep = np.zeros_like(trousers)
    for k in range(1, n + 1):
        m = lab == k
        if m.sum() > 30:
            keep |= m
    trousers = keep
    leftside = xx < s["split"]
    sides = {"near": leftside if s["nearSide"] == "left" else ~leftside}
    sides["far"] = ~sides["near"]
    rest = solid & ~trousers & ~allfeet & ~arm_all & ~(a[:, :, :3].max(2) < 60)
    legs = {}
    for side in ("near", "far"):
        lm = with_outlines(a, trousers & sides[side], rest | (trousers & ~sides[side]) | allfeet) & sides[side] & (yy >= s["legTop"]) & ~allfeet & ~arm_all
        legs[side] = lm

    def leg_img(side):
        """The leg, with what the hand hid painted in (the hand swings away from it)."""
        out = a.copy()
        out[~legs[side]] = 0
        fill_under(out, forearm_m & (yy >= s["legTop"]), reach=2)
        return out

    def img(mask):
        out = a.copy()
        out[~mask] = 0
        return out

    body = a.copy()
    for side in ("near", "far"):
        body[legs[side] & (yy >= s["torsoOverlapY"])] = 0
        body[feet[side]] = 0
    hole = arm_all
    body[hole] = 0
    fill_under(body, hole)
    keep_under(body, a, (legs["near"] | legs["far"]) & (yy < s["torsoOverlapY"] + 6))
    # below the hem nothing is the torso's: strays (a shoe's top edge, an outline in the crotch)
    # go to the nearest leg or shoe, or they'd stay behind as the legs move
    lower = (body[:, :, 3] > 0) & (yy >= s["legsOnlyY"])
    if lower.any():
        owners = [legs["near"], legs["far"], feet["near"], feet["far"]]
        lab_ = np.zeros(a.shape[:2], int)
        for k, m in enumerate(owners, 1):
            lab_[m] = k
        _, (iy, ix) = distance_transform_edt(lab_ == 0, return_indices=True)
        nearest = lab_[iy, ix]
        for k, m in enumerate(owners, 1):
            m |= lower & (nearest == k)
        body[lower] = 0

    bsolid = body[:, :, 3] > 0
    shirtish = near_palette(body, s["shirtSample"], 30) & (yy > s["chinY"])
    up = bsolid & (yy <= s["headMaxY"])
    hm = with_outlines(body, up & ~shirtish, shirtish | (bsolid & (yy > s["headMaxY"]))) & up
    # bits of the torso left up among the hair (highlights, specks) join the head
    lab, n = label(bsolid & ~hm)
    for k in range(1, n + 1):
        m = lab == k
        if m.sum() < 40 and yy[m].max() <= s["headMaxY"]:
            hm |= m
    tm = bsolid & ~hm

    parts = {"head": img(hm), "torso": body.copy(), "upper-arm.free": img(sleeve_m), "forearm.free": img(forearm_m),
             "foot.near": img(feet["near"]), "foot.far": img(feet["far"])}
    parts["torso"][~tm] = 0
    for side in ("near", "far"):
        t, sh = legs_split(a, leg_img(side), s[f"knee.{side}"][1], 5)
        parts[f"thigh.{side}"], parts[f"shin.{side}"] = t, sh

    joints = {k: s[k] for k in ("hip.near", "knee.near", "ankle.near", "hip.far", "knee.far", "ankle.far", "shoulder.free", "elbow.free", "neck")}
    joints["pelvis"] = [(s["hip.near"][0] + s["hip.far"][0]) / 2, (s["hip.near"][1] + s["hip.far"][1]) / 2]
    order = FRONT_ORDER if view == "front" else BACK_ORDER
    d = CH / cid / view
    d.mkdir(parents=True, exist_ok=True)
    for name, arr in parts.items():
        Image.fromarray(arr).save(d / f"{name}.png")
    json.dump({"frameSize": [256, 280], "joints": joints, "hem": s["hem"], "palette": palette(a, s["materials"]), "fixed": s["fixed"], "zones": s.get("zones", {}), "parts": [{"part": p, **KINDS[p]} for p in order]}, open(d / "parts.json", "w"), indent=1)
    # coverage: every pixel of the art is in some part
    covered = np.zeros_like(solid)
    for arr in parts.values():
        covered |= arr[:, :, 3] > 0
    print(cid, view, "uncovered px:", int((solid & ~covered).sum()))


if __name__ == "__main__":
    for cid in sys.argv[1:] or SPECS:
        for view in ("front", "back"):
            cut(cid, view)

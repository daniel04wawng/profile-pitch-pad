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
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes, distance_transform_edt, label

from cut_green import fill_under, keep_under, legs_split, poly, smooth_fill
from hair_swap import paint_across
from materials import IDS, palette_map

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
SPECS["plum-braid"]["front"]["zones"]["hair"] = [[100, 62, 124, 136]]
SPECS["sage-bob"]["front"]["zones"]["hair"] = [[94, 66, 124, 92]]  # the bob's ends on her shoulder
SPECS["sage-bob"]["back"]["zones"]["hair"] = [[86, 72, 146, 96]]
SPECS["plum-braid"]["back"]["zones"]["hair"] = [[96, 50, 124, 148]]

# The mug arm, traced along the art: from the front, the upper arm (shoulder to the cuff) and the
# forearm with its hand and the mug; from behind only the hand and mug show. Joints: the
# shoulder and elbow, the mug's centre, where the elbow lifts to for a sip, and the mouth the mug
# goes to. (From behind, the sip turns the hand up out of sight behind her head.)
MUG = {
    "sage-bob": {
        "front": {"upper": [(97, 75), (108, 77), (114, 88), (114, 116), (110, 126), (100, 126), (92, 118), (88, 100), (90, 84)],
                  "fore": [(100, 121), (110, 112), (116, 101), (124, 97), (134, 92), (153, 92), (154, 121), (138, 122), (124, 121), (112, 128), (102, 130)],
                  "shoulder": [104, 80], "elbow": [104, 122], "mug": [144, 107], "mouth": [138, 66]},
        "back": {"fore": [(147, 95), (164, 95), (164, 122), (147, 122)], "elbow": [149, 124]},
    },
    "blue-pixie": {
        "front": {"upper": [(96, 77), (108, 78), (113, 90), (113, 116), (110, 125), (100, 125), (92, 117), (88, 100), (90, 84)],
                  "fore": [(100, 120), (110, 113), (114, 104), (122, 101), (129, 96), (149, 96), (150, 125), (134, 126), (122, 124), (112, 128), (102, 129)],
                  "shoulder": [103, 80], "elbow": [103, 122], "mug": [139, 111], "mouth": [139, 70]},
        "back": {"fore": [(146, 97), (163, 97), (163, 122), (146, 122)], "elbow": [148, 124]},
    },
    "terracotta-curls": {
        "front": {"upper": [(96, 82), (106, 83), (111, 95), (111, 118), (107, 124), (98, 124), (92, 116), (90, 100), (92, 88)],
                  "fore": [(98, 118), (110, 112), (116, 106), (125, 104), (131, 98), (151, 98), (152, 127), (134, 128), (122, 126), (110, 128), (100, 128)],
                  "shoulder": [102, 84], "elbow": [100, 120], "mug": [141, 113], "mouth": [136, 74]},
        "back": {"fore": [(146, 98), (164, 98), (164, 124), (146, 124)], "elbow": [148, 128]},
    },
    "plum-braid": {
        "front": {"upper": [(97, 76), (108, 78), (114, 90), (114, 118), (110, 127), (100, 127), (93, 119), (89, 100), (91, 84)],
                  "fore": [(100, 121), (110, 113), (116, 104), (124, 101), (133, 97), (153, 97), (154, 128), (136, 129), (124, 126), (112, 130), (102, 131)],
                  "shoulder": [104, 80], "elbow": [104, 124], "mug": [145, 113], "mouth": [140, 70]},
        "back": {"fore": [(147, 99), (165, 99), (165, 126), (147, 126)], "elbow": [148, 128]},
    },
}
SIP_LIFT = (10, -18)
SIP_LIFT_BACK = (-8, -28)  # behind: the hand goes up and in, out of sight behind her shoulder and head  # how far the elbow comes up and in for a sip (front)

# --- the jacket-off base models, from their own art (cafe16, normalize_cafe16.py) ---
C16 = HERE / "characters" / "cafe16-src"
SOURCE = {
    "man-tee": {"front": C16 / "01-man-tee-front.png", "back": C16 / "02-man-tee-back.png"},
    "woman-tee": {"front": C16 / "03-woman-tee-front.png", "back": C16 / "04-woman-tee-back.png"},
}
SPECS["man-tee"] = {  # in just his white tee: the tee is his top ("shirt"), arms bare below short sleeves
    "front": spec([122, 72], 74, 66, ([117, 148], [116, 185], [115, 224]), ([139, 145], [139, 180], [140, 214]), [142, 76], [147, 120],
                  133, 129, "left", 140, 142, 136,
                  [(138, 74), (146, 74), (152, 84), (155, 100), (157, 112), (158, 124), (148, 125), (146, 110), (143, 95), (140, 84)],
                  [(144, 120), (158, 119), (161, 135), (163, 157), (146, 158), (144, 140)],
                  box(102, 222, 129, 254), box(131, 210, 170, 242),
                  [[112, 55, 122, 62], [93, 108, 100, 118], [146, 110, 152, 130]], [[100, 30, 130, 45]],
                  [[122, 118, 140, 130], [97, 80, 108, 98]], [],
                  [[106, 160, 122, 200], [132, 160, 146, 200]], [[108, 232, 124, 246], [140, 220, 160, 232]], [[127, 88, 149, 113]]),
    "back": spec([126, 68], 70, 64, ([140, 148], [140, 190], [141, 230]), ([114, 150], [112, 188], [110, 213]), [98, 75], [97, 120],
                 138, 127, "right", 146, 148, 140,
                 [(92, 72), (101, 70), (104, 88), (104, 118), (100, 124), (92, 124), (89, 108), (89, 90)],
                 [(90, 118), (104, 118), (105, 135), (105, 152), (91, 152), (90, 135)],
                 box(128, 225, 165, 256), box(97, 205, 126, 236),
                 [[93, 108, 100, 128], [148, 85, 160, 100]], [[110, 30, 145, 55]],
                 [[110, 90, 140, 125], [92, 80, 99, 98]], [],
                 [[106, 170, 122, 200], [132, 170, 146, 210]], [[104, 214, 120, 228], [136, 238, 158, 250]], [[147, 79, 160, 92]]),
}
SPECS["woman-tee"] = {  # Sage in just her cream tee: the tee is her top, arms bare below short sleeves
    "front": spec([128, 78], 80, 70, ([113, 150], [112, 188], [112, 228]), ([138, 148], [138, 185], [140, 219]), [143, 80], [152, 122],
                  136, 127, "left", 142, 145, 137,
                  [(138, 78), (147, 77), (153, 88), (157, 104), (159, 118), (160, 126), (150, 127), (148, 112), (145, 98), (141, 88)],
                  [(147, 120), (160, 119), (163, 135), (165, 166), (149, 166), (147, 140)],
                  box(97, 224, 127, 256), box(129, 214, 166, 244),
                  [[128, 58, 138, 66], [93, 110, 102, 122], [150, 110, 156, 135]], [[105, 30, 135, 45], [97, 55, 110, 75]],
                  [[105, 85, 120, 100], [135, 122, 148, 134]], [],
                  [[104, 165, 122, 205], [130, 165, 146, 205]], [[103, 234, 120, 248], [136, 224, 156, 236]], [[131, 92, 151, 119]]),
    "back": spec([127, 86], 88, 80, ([140, 158], [140, 195], [141, 231]), ([113, 158], [112, 192], [112, 215]), [100, 82], [98, 122],
                 150, 122, "right", 158, 160, 152,
                 [(93, 82), (101, 80), (104, 95), (104, 120), (100, 125), (92, 125), (89, 110), (90, 92)],
                 [(90, 118), (104, 118), (105, 140), (103, 158), (91, 158), (90, 138)],
                 box(128, 225, 166, 256), box(91, 210, 126, 240),
                 [[93, 110, 101, 130], [152, 112, 162, 125]], [[110, 40, 145, 70]],
                 [[112, 100, 140, 140], [91, 86, 99, 100]], [],
                 [[104, 175, 120, 205], [130, 175, 146, 215]], [[98, 222, 116, 232], [134, 238, 158, 250]], [[150, 99, 164, 113]]),
}
for cid in ("man-tee", "woman-tee"):
    for v in ("front", "back"):
        SPECS[cid][v]["zones"] = {"skin": NECK_AND_MUG_HAND[v] + ([[140, 75, 170, 125]] if v == "back" else [])}
MUG["man-tee"] = {
    "front": {"upper": [(92, 74), (104, 72), (110, 82), (110, 100), (106, 124), (96, 126), (90, 118), (89, 98), (90, 84)],
              "fore": [(96, 118), (106, 110), (114, 100), (122, 97), (128, 90), (148, 90), (148, 112), (132, 113), (120, 120), (108, 126), (98, 127)],
              "shoulder": [100, 78], "elbow": [100, 121], "mug": [140, 101], "mouth": [121, 63]},
    "back": {"fore": [(148, 78), (168, 78), (169, 100), (162, 118), (152, 120), (150, 100)], "elbow": [154, 118]},
}
MUG["woman-tee"] = {
    "front": {"upper": [(93, 78), (104, 77), (110, 88), (110, 104), (106, 126), (96, 127), (90, 118), (89, 100), (91, 86)],
              "fore": [(95, 118), (106, 110), (114, 102), (122, 98), (130, 92), (150, 92), (150, 118), (134, 119), (122, 122), (108, 128), (97, 128)],
              "shoulder": [100, 82], "elbow": [99, 122], "mug": [140, 106], "mouth": [133, 69]},
    "back": {"fore": [(147, 98), (166, 98), (167, 125), (158, 138), (150, 138), (148, 118)], "elbow": [153, 132]},
}

# --- the views for eight directions: facing you (south), facing away (north), side (east;
# west is it mirrored), for the four base models, from their own art (cafe16) ---
KIND = {"front": "front", "south": "front", "back": "back", "north": "back", "east": "east"}
SPECS.setdefault("green", {})
SOURCE["green"] = {"south": C16 / "05-man-jacket-south.png", "north": C16 / "06-man-jacket-north.png", "east": C16 / "07-man-jacket-east.png"}
SOURCE["man-tee"].update({"south": C16 / "08-man-tee-south.png", "north": C16 / "09-man-tee-north.png", "east": C16 / "10-man-tee-east.png"})
SOURCE["sage-bob"] = {"south": C16 / "11-woman-jacket-south.png", "north": C16 / "12-woman-jacket-north.png", "east": C16 / "13-woman-jacket-east.png"}
SOURCE["woman-tee"].update({"south": C16 / "14-woman-tee-south.png", "north": C16 / "15-woman-tee-north.png", "east": C16 / "16-woman-tee-east.png"})
SOUTH_ZONES = {"skin": [[104, 66, 150, 98], [88, 96, 140, 135]]}

SPECS["green"]["south"] = spec([124, 74], 76, 70, ([114, 152], [113, 190], [110, 222]), ([140, 152], [141, 190], [146, 222]), [155, 74], [160, 124],
    145, 128, "left", 152, 155, 148,
    [(149, 70), (160, 72), (167, 84), (170, 104), (170, 126), (152, 128), (149, 110)],
    [(150, 120), (167, 120), (170, 140), (170, 166), (154, 166), (151, 145)],
    box(94, 222, 127, 254), box(130, 222, 166, 254),
    [[118, 55, 132, 66], [100, 105, 112, 118], [156, 145, 166, 160]], [[106, 30, 140, 45]],
    [[90, 85, 100, 105], [155, 85, 168, 105]], [[118, 75, 135, 90], [118, 122, 135, 140]],
    [[105, 170, 122, 205], [133, 170, 150, 205]], [[100, 232, 115, 248], [145, 232, 160, 248]], [[119, 94, 139, 118]])
SPECS["man-tee"]["south"] = spec([125, 74], 76, 70, ([115, 145], [114, 185], [112, 224]), ([140, 145], [141, 185], [146, 224]), [152, 76], [157, 122],
    138, 128, "left", 144, 146, 140,
    [(148, 74), (158, 74), (163, 86), (165, 104), (165, 124), (150, 126), (148, 108)],
    [(149, 120), (165, 120), (168, 140), (168, 168), (152, 168), (150, 145)],
    box(96, 222, 127, 254), box(130, 222, 166, 254),
    [[118, 55, 132, 66], [93, 105, 101, 118], [152, 110, 160, 140]], [[105, 30, 140, 45]],
    [[110, 80, 125, 95], [130, 120, 150, 135]], [],
    [[106, 165, 122, 205], [133, 165, 148, 205]], [[102, 232, 118, 248], [144, 232, 160, 248]], [[120, 96, 141, 119]])
SPECS["sage-bob"]["south"] = spec([127, 80], 82, 74, ([115, 155], [115, 192], [112, 230]), ([141, 155], [142, 192], [147, 230]), [154, 82], [159, 124],
    147, 130, "left", 155, 158, 145,
    [(150, 80), (160, 81), (166, 94), (168, 112), (168, 128), (152, 130), (150, 112)],
    [(151, 122), (167, 122), (170, 142), (170, 172), (154, 172), (152, 148)],
    box(96, 226, 129, 254), box(131, 226, 166, 254),
    [[122, 60, 135, 70], [103, 105, 115, 118], [156, 150, 165, 165]], [[105, 35, 140, 48], [100, 60, 112, 80]],
    [[93, 90, 104, 108], [152, 90, 163, 110]], [[122, 86, 132, 96], [122, 124, 134, 140]],
    [[106, 170, 124, 210], [133, 170, 150, 210]], [[103, 236, 117, 248], [143, 236, 158, 248]], [[119, 98, 139, 121]])
SPECS["woman-tee"]["south"] = spec([127, 80], 82, 74, ([113, 148], [112, 188], [110, 228]), ([138, 148], [139, 188], [143, 228]), [150, 82], [155, 124],
    136, 126, "left", 144, 146, 138,
    [(145, 80), (154, 80), (159, 92), (162, 108), (163, 126), (148, 128), (146, 108)],
    [(147, 120), (162, 120), (166, 140), (167, 172), (151, 172), (148, 148)],
    box(96, 224, 125, 254), box(127, 224, 164, 254),
    [[122, 60, 135, 70], [92, 108, 100, 120], [150, 112, 158, 140]], [[105, 35, 140, 48], [98, 60, 108, 80]],
    [[110, 86, 122, 98], [132, 120, 148, 132]], [],
    [[104, 165, 122, 205], [130, 165, 146, 205]], [[101, 236, 115, 248], [145, 236, 157, 248]], [[117, 97, 136, 121]])
for cid in ("green", "man-tee", "sage-bob", "woman-tee"):
    SPECS[cid]["south"]["zones"] = SOUTH_ZONES
MUG.setdefault("green", {})
MUG["green"]["south"] = {"upper": [(86, 72), (100, 70), (104, 82), (104, 120), (98, 124), (86, 124), (84, 100)],
                         "fore": [(90, 116), (98, 104), (108, 98), (118, 92), (140, 92), (140, 118), (124, 120), (110, 124), (96, 126)],
                         "shoulder": [97, 74], "elbow": [96, 120], "mug": [128, 105], "mouth": [126, 64]}
MUG["man-tee"]["south"] = {"upper": [(89, 74), (101, 72), (106, 86), (106, 122), (100, 128), (90, 128), (88, 104)],
                           "fore": [(94, 118), (102, 106), (112, 100), (120, 95), (142, 95), (142, 120), (124, 122), (110, 126), (98, 129)],
                           "shoulder": [97, 76], "elbow": [97, 124], "mug": [130, 107], "mouth": [126, 64]}
MUG["sage-bob"]["south"] = {"upper": [(89, 80), (102, 79), (106, 90), (106, 122), (100, 126), (89, 126), (87, 104)],
                            "fore": [(93, 118), (100, 106), (110, 100), (119, 96), (140, 96), (140, 121), (124, 123), (110, 126), (96, 128)],
                            "shoulder": [97, 82], "elbow": [96, 122], "mug": [129, 109], "mouth": [128, 71]}
MUG["woman-tee"]["south"] = {"upper": [(89, 82), (101, 81), (105, 92), (105, 122), (99, 127), (89, 127), (87, 104)],
                             "fore": [(92, 118), (100, 106), (108, 101), (117, 96), (138, 96), (138, 121), (122, 123), (108, 127), (95, 129)],
                             "shoulder": [96, 84], "elbow": [96, 123], "mug": [127, 109], "mouth": [128, 71]}

# facing away: the mug arm is the near arm, bent forward out of sight; it lifts at the shoulder
NO_FIX = [[0, 0, 1, 1]]
SPECS["green"]["north"] = spec([126, 76], 78, 72, ([138, 152], [138, 190], [140, 225]), ([110, 152], [108, 190], [104, 225]), [100, 86], [96, 128],
    148, 124, "right", 158, 162, 150,
    [(88, 84), (108, 82), (112, 100), (110, 130), (90, 132), (86, 110)],
    [(88, 126), (104, 126), (104, 145), (102, 162), (88, 162), (87, 140)],
    box(126, 224, 168, 256), box(86, 226, 122, 256),
    [[118, 72, 130, 78], [90, 142, 100, 156]], [[100, 40, 140, 65]],
    [[110, 95, 140, 140]], [],
    [[100, 170, 120, 210], [130, 170, 148, 210]], [[95, 236, 115, 248], [135, 236, 155, 248]], NO_FIX)
SPECS["man-tee"]["north"] = spec([126, 80], 82, 76, ([138, 150], [138, 190], [142, 226]), ([112, 150], [110, 190], [104, 226]), [98, 84], [96, 118],
    142, 124, "right", 150, 155, 145,
    [(86, 80), (106, 78), (110, 92), (108, 112), (88, 114), (85, 96)],
    [(86, 108), (106, 108), (106, 130), (104, 162), (86, 162), (85, 130)],
    box(128, 222, 170, 256), box(86, 224, 124, 256),
    [[118, 76, 132, 82], [90, 125, 100, 150]], [[100, 35, 145, 65]],
    [[110, 95, 140, 135]], [],
    [[100, 165, 120, 205], [130, 165, 148, 205]], [[92, 234, 112, 248], [138, 236, 158, 248]], NO_FIX)
SPECS["sage-bob"]["north"] = spec([128, 90], 96, 90, ([140, 165], [140, 198], [142, 228]), ([114, 165], [112, 198], [110, 228]), [96, 98], [94, 136],
    160, 127, "right", 170, 175, 162,
    [(84, 94), (104, 92), (108, 110), (106, 140), (86, 142), (82, 118)],
    [(84, 134), (104, 134), (104, 152), (102, 172), (84, 172), (83, 150)],
    box(128, 226, 168, 256), box(86, 226, 126, 256),
    [[88, 145, 98, 165]], [[105, 45, 145, 85]],
    [[110, 110, 140, 150]], [],
    [[100, 180, 120, 215], [132, 180, 148, 215]], [[92, 236, 110, 248], [140, 236, 158, 248]], NO_FIX)
SPECS["woman-tee"]["north"] = spec([128, 88], 96, 90, ([140, 152], [140, 192], [143, 228]), ([114, 152], [112, 192], [108, 228]), [96, 92], [94, 118],
    145, 127, "right", 155, 160, 150,
    [(84, 88), (104, 86), (108, 100), (106, 116), (86, 118), (82, 102)],
    [(82, 110), (104, 110), (104, 135), (102, 164), (82, 164), (81, 135)],
    box(130, 226, 170, 256), box(86, 226, 124, 256),
    [[86, 125, 98, 150]], [[105, 40, 145, 85]],
    [[110, 100, 140, 140]], [],
    [[100, 170, 120, 210], [132, 170, 148, 210]], [[92, 236, 110, 248], [140, 236, 158, 248]], NO_FIX)
NORTH_ARM = {
    "green": [(138, 82), (158, 84), (164, 104), (162, 128), (150, 130), (140, 110)],
    "man-tee": [(138, 80), (158, 82), (164, 100), (164, 130), (152, 132), (142, 112)],
    "sage-bob": [(144, 92), (164, 94), (170, 112), (168, 140), (154, 142), (146, 120)],
    "woman-tee": [(144, 88), (164, 90), (172, 108), (172, 136), (156, 138), (148, 116)],
}
for cid, arm in NORTH_ARM.items():
    SPECS[cid]["north"]["zones"] = {"skin": [[108, 60, 150, 100]]}
    x0, y0 = arm[0]
    MUG[cid]["north"] = {"fore": arm, "elbow": [x0 + 6, y0 + 4], "lift": (0, -3)}

# side on (east): the mug arm is the near arm, all of it showing; the free arm hangs behind the
# body with only its hand showing. The legs overlap, so they're split at the knee-to-foot line
# (the near leg's shoe is the lower one).
SPECS["green"]["east"] = spec([112, 78], 80, 72, ([108, 152], [106, 190], [108, 226]), ([116, 150], [120, 188], [126, 212]), [112, 92], [118, 132],
    148, 115, "left", 156, 160, 150,
    [(110, 124), (124, 124), (125, 138), (111, 138)],
    [(111, 136), (127, 136), (127, 162), (111, 162)],
    box(96, 228, 150, 254), box(118, 210, 162, 234),
    [[124, 58, 134, 70], [116, 142, 122, 156]], [[85, 38, 120, 55]],
    [[88, 95, 100, 130]], [[112, 82, 116, 98]],
    [[102, 165, 118, 200]], [[102, 238, 128, 246], [130, 218, 148, 228]], [[126, 94, 142, 122]])
SPECS["man-tee"]["east"] = spec([116, 78], 80, 72, ([112, 150], [110, 190], [110, 228]), ([122, 148], [126, 188], [134, 214]), [120, 95], [124, 135],
    145, 120, "left", 152, 156, 146,
    [(119, 126), (131, 126), (132, 140), (120, 140)],
    [(120, 138), (134, 138), (134, 166), (120, 166)],
    box(100, 228, 150, 254), box(124, 210, 172, 236),
    [[130, 58, 138, 68], [124, 145, 130, 160]], [[90, 35, 125, 55]],
    [[108, 85, 125, 140]], [],
    [[108, 165, 122, 200]], [[105, 238, 130, 248], [135, 218, 160, 228]], [[132, 94, 150, 122]])
SPECS["sage-bob"]["east"] = spec([122, 84], 86, 78, ([116, 160], [114, 195], [112, 230]), ([126, 158], [130, 192], [138, 214]), [112, 100], [112, 136],
    155, 124, "left", 165, 170, 158,
    [(105, 126), (119, 126), (119, 140), (105, 140)],
    [(104, 138), (121, 138), (121, 164), (104, 164)],
    box(100, 230, 146, 254), box(128, 210, 172, 238),
    [[132, 60, 142, 72], [108, 145, 116, 158]], [[95, 35, 130, 60]],
    [[108, 100, 122, 140]], [[136, 92, 142, 110]],
    [[110, 170, 124, 205]], [[105, 240, 128, 248], [138, 220, 160, 230]], [[140, 96, 158, 124]])
SPECS["woman-tee"]["east"] = spec([122, 82], 84, 76, ([116, 152], [114, 190], [112, 230]), ([128, 150], [132, 190], [140, 214]), [110, 98], [110, 128],
    146, 124, "left", 155, 160, 148,
    [(103, 118), (117, 118), (117, 132), (103, 132)],
    [(102, 130), (119, 130), (119, 164), (102, 164)],
    box(100, 230, 146, 254), box(128, 208, 172, 238),
    [[132, 58, 142, 70], [106, 140, 114, 156], [118, 110, 126, 122]], [[95, 30, 130, 60]],
    [[115, 95, 135, 140]], [],
    [[110, 165, 124, 200]], [[105, 240, 128, 248], [138, 220, 160, 230]], [[140, 96, 158, 124]])
MUG["green"]["east"] = {"upper": [(102, 84), (118, 84), (122, 100), (120, 122), (108, 124), (100, 110)],
                        "fore": [(110, 112), (118, 100), (126, 94), (142, 92), (143, 124), (126, 125), (114, 125)],
                        "shoulder": [110, 88], "elbow": [112, 118], "mug": [134, 108], "mouth": [133, 64]}
MUG["man-tee"]["east"] = {"upper": [(108, 82), (122, 82), (126, 96), (126, 118), (114, 122), (106, 108)],
                          "fore": [(116, 110), (124, 100), (134, 94), (150, 92), (150, 124), (132, 125), (120, 125)],
                          "shoulder": [116, 86], "elbow": [118, 118], "mug": [140, 108], "mouth": [138, 64]}
MUG["sage-bob"]["east"] = {"upper": [(118, 90), (132, 92), (136, 106), (134, 128), (120, 130), (114, 112)],
                           "fore": [(124, 116), (132, 104), (142, 96), (159, 94), (159, 126), (140, 127), (128, 129)],
                           "shoulder": [124, 94], "elbow": [126, 124], "mug": [150, 110], "mouth": [146, 72]}
MUG["woman-tee"]["east"] = {"upper": [(114, 86), (130, 88), (134, 100), (130, 124), (118, 126), (110, 108)],
                            "fore": [(122, 112), (130, 104), (140, 96), (159, 94), (159, 126), (140, 127), (126, 129)],
                            "shoulder": [120, 90], "elbow": [122, 120], "mug": [150, 110], "mouth": [146, 70]}
for cid in ("green", "man-tee", "sage-bob", "woman-tee"):
    SPECS[cid]["east"]["zones"] = {"skin": [[100, 60, 160, 135]]}

FRONT_ORDER = ["torso", "head", "upper-arm.free", "forearm.free", "upper-arm.mug", "forearm.mug", "thigh.far", "shin.far", "foot.far", "thigh.near", "shin.near", "foot.near"]
EAST_ORDER = ["upper-arm.free", "forearm.free", "thigh.far", "shin.far", "foot.far", "torso", "head", "thigh.near", "shin.near", "foot.near", "upper-arm.mug", "forearm.mug"]  # side on: his far arm behind him
BACK_ORDER = ["forearm.mug", "thigh.far", "shin.far", "foot.far", "thigh.near", "shin.near", "foot.near", "torso", "head", "upper-arm.free", "forearm.free"]
KINDS = {
    "torso": {"kind": "segment", "from": "pelvis", "to": "neck"},
    "head": {"kind": "follow", "at": "neck"},
    "upper-arm.free": {"kind": "segment", "from": "shoulder.free", "to": "elbow.free"},
    "forearm.free": {"kind": "rigid", "at": "elbow.free"},
    "upper-arm.mug": {"kind": "segment", "from": "shoulder.mug", "to": "elbow.mug"},
    "forearm.mug": {"kind": "rigid", "at": "elbow.mug"},
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
    im = Image.open(SOURCE.get(cid, {}).get(view) or SRC / cid / f"stand-{view}.png").convert("RGBA")
    a = np.array(im)
    solid = a[:, :, 3] > 0
    yy, xx = np.mgrid[: a.shape[0], : a.shape[1]]
    size = im.size

    # a shoe is everything in its (generous) outline that isn't trouser-coloured: the hem the
    # outline overlaps stays with the leg, the shoe's own outline and sock go with the shoe
    trouser_colour = near_palette(a, s["trouserSample"])
    # (below the ankle, everything in a shoe's outline is the shoe: its dark outline can look
    # like the trousers, and left on the shin it drifts off as the leg swings)
    feet = {side: poly(size, s[f"foot.{side}"]) & solid & ~(trouser_colour & (yy < s[f"ankle.{side}"][1] + 3)) for side in ("near", "far")}
    if KIND[view] == "east":
        # side on, the shoes overlap, so their outlines can't be boxes: each shoe is one of the
        # two white shapes (the lower one is the near shoe), and its outline the dark pixels
        # round it (each to the nearer shoe), the trousers left out
        both = (feet["near"] | feet["far"])
        white = both & (a[:, :, :3].min(2) > 150)
        lab, n = label(white, structure=np.ones((3, 3)))
        sizes = np.bincount(lab.ravel())[1:]
        big = [k + 1 for k in np.argsort(sizes)[::-1][:2]]
        if len(big) == 2:
            ys = [np.nonzero(lab == k)[0].mean() for k in big]
            near_k, far_k = (big[0], big[1]) if ys[0] > ys[1] else (big[1], big[0])
            owner = np.zeros(lab.shape, int)
            owner[binary_dilation(lab == far_k, iterations=1)] = 2
            owner[lab == near_k] = 1
            _, (iy, ix) = distance_transform_edt(owner == 0, return_indices=True)
            nearest = owner[iy, ix]
            shoe = binary_dilation(white, iterations=2) & solid & ~trouser_colour
            feet = {"near": shoe & (nearest == 1), "far": shoe & (nearest == 2)}
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
    if KIND[view] == "east":
        # side on, the joints' x is read off the trousers themselves (rows across the hips and
        # knees: the near leg is the front-left third, the far one the back-right third)
        for j in ("hip", "knee"):
            y = int(s[f"{j}.near"][1])
            xs = np.nonzero(trousers[y])[0]
            if len(xs):
                w = xs.max() - xs.min()
                s[f"{j}.near"] = [float(xs.min() + 0.3 * w), s[f"{j}.near"][1]]
                s[f"{j}.far"] = [float(xs.min() + 0.7 * w), s[f"{j}.far"][1]]
        # side on, the legs overlap: each pixel goes to the nearer leg bone (hip-knee-ankle);
        # where they're about as near, the near leg (it's in front)
        def dist(side):
            d = np.full(xx.shape, 1e9)
            pts = [np.array(s[f"{j}.{side}"], float) for j in ("hip", "knee", "ankle")]
            for p0, p1 in zip(pts, pts[1:]):
                v = p1 - p0
                t = np.clip(((xx - p0[0]) * v[0] + (yy - p0[1]) * v[1]) / (v @ v), 0, 1)
                d = np.minimum(d, np.hypot(xx - (p0[0] + t * v[0]), yy - (p0[1] + t * v[1])))
            return d
        dn, df = dist("near"), dist("far")
        # a leg's own width round its bone goes to it even where the other leg hides it, so a
        # leg swinging out from behind the other isn't a sliver (the near leg is drawn over it)
        sides["near"] = (dn <= df + 2) | (dn <= 6)
        sides["far"] = (df < dn + 2) | (df <= 7)
    else:
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
    # the mug arm: out of the torso; what it covered inside her (the tee and shirt behind the
    # forearm) is filled with the cloth beside it, row by row
    mg = MUG[cid][view]
    pal = palette(a, s["materials"])
    hair_here = palette_map("torso", a, pal, s["fixed"], s.get("zones", {})) == IDS["hair"]  # a braid stays put
    taken = solid & ~arm_all & ~legs["near"] & ~legs["far"] & ~hair_here
    mug_fore = poly(size, mg["fore"]) & taken
    mug_upper = (poly(size, mg["upper"]) & taken & ~mug_fore) if "upper" in mg else np.zeros_like(solid)
    mug_all = mug_fore | mug_upper
    was = body[:, :, 3] > 0
    body[mug_all] = 0
    # behind the forearm is all her; behind the upper arm, all but its outer edge (with the arm
    # up, her side is a little slimmer than the arm made it)
    behind = (mug_fore | (mug_upper & binary_erosion(was, iterations=5))) if "upper" in mg else np.zeros_like(was)  # behind: the hand was beside her, nothing under it
    smooth_fill(body, behind)
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
             "forearm.mug": img(mug_fore), **({"upper-arm.mug": img(mug_upper)} if "upper" in mg else {}),
             "foot.near": img(feet["near"]), "foot.far": img(feet["far"])}
    parts["torso"][~tm] = 0
    for side in ("near", "far"):
        t, sh = legs_split(a, leg_img(side), s[f"knee.{side}"][1], 5)
        parts[f"thigh.{side}"], parts[f"shin.{side}"] = t, sh

    joints = {k: s[k] for k in ("hip.near", "knee.near", "ankle.near", "hip.far", "knee.far", "ankle.far", "shoulder.free", "elbow.free", "neck")}
    lift = mg.get("lift") or (SIP_LIFT if "upper" in mg else SIP_LIFT_BACK)
    joints["elbow.mug.sip"] = [mg["elbow"][0] + lift[0], mg["elbow"][1] + lift[1]]
    if "upper" in mg:
        joints["shoulder.mug"] = mg["shoulder"]
        joints["hand.mug"], joints["mouth"] = mg["mug"], mg["mouth"]
    joints["elbow.mug"] = mg["elbow"]
    joints["pelvis"] = [(s["hip.near"][0] + s["hip.far"][0]) / 2, (s["hip.near"][1] + s["hip.far"][1]) / 2]
    order = [p for p in {"front": FRONT_ORDER, "back": BACK_ORDER, "east": EAST_ORDER}[KIND[view]] if p in parts]
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
    # cut_women.py [id | id:view ...]: every view of each, or just that one
    for arg in sys.argv[1:] or SPECS:
        cid, _, only = arg.partition(":")
        for view in [only] if only else SPECS[cid]:
            cut(cid, view)

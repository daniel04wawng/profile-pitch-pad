"""Give each woman the others' hair: a layer per (wearer, donor) pair, made from the donor's own
hair pixels, so nothing is drawn from scratch.

For a wearer W and a donor D, per view:
  - D's hair (and its outline) is cut out of D's head, plus any of it lying on D's torso (a
    braid), and moved so D's face sits on W's face (the centre of the face's skin);
  - W's own hair is hidden (in the head, and on the torso for a braid);
  - what W's hair covered and D's doesn't is painted back: skin where it was over W's face
    (a fringe over the forehead), the shirt where a braid lay over it.
Saved as characters/<W>/layers/hair-<D>/<view>/{head,torso}{,.hide,.fill}.png, with
layer.json {"slot": "hair", "material": "hair"} so the hair colour picker recolours it.

    python3 art/avatar-rig/skeleton/hair_swap.py
"""
import json
import pathlib

import numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, binary_dilation, binary_fill_holes, distance_transform_edt, label

from materials import IDS, material_map, profile

HERE = pathlib.Path(__file__).parent
CH = HERE / "characters"
WOMEN = ("sage-bob", "blue-pixie", "terracotta-curls", "plum-braid")
HAIR, SKIN = IDS["hair"], IDS["skin"]


def load(cid, view, part):
    return np.array(Image.open(CH / cid / view / f"{part}.png").convert("RGBA"))


def face_of(m):
    """The face as one solid shape: its skin with the eyes, brows and lips inside it filled in,
    and its outline. Never hair, whatever colour a shadow on it is."""
    skin = m == SKIN
    lab, n = label(skin)
    for k in range(1, n + 1):  # a hair highlight can be skin-coloured: only real patches of skin count
        if (lab == k).sum() < 30:
            skin[lab == k] = False
    return binary_dilation(binary_fill_holes(binary_closing(skin, iterations=3)) | skin, iterations=1)


def hair_of(arr, m):
    """The hair, and the dark outline around it: outside the face, small stray bits dropped,
    highlights inside it kept."""
    solid = arr[:, :, 3] > 0
    face = face_of(m)
    # a fringe lies over the face: big stretches of hair there are hair (brows, small, aren't)
    lab, n = label((m == HAIR) & face)
    for k in range(1, n + 1):
        if (lab == k).sum() >= 25:
            face &= lab != k
    hair = (m == HAIR) & ~face
    lab, n = label(hair)
    for k in range(1, n + 1):
        if (lab == k).sum() < 12:
            hair[lab == k] = False
    dark = solid & (arr[:, :, :3].max(2) < 70) & (m == 0) & ~face
    hair |= binary_dilation(hair, iterations=2) & dark
    hair |= binary_closing(hair, iterations=2) & solid  # highlights along its edge
    return binary_fill_holes(hair) & solid & ~face


def face_centre(arr, m, neck_y):
    yy = np.mgrid[: arr.shape[0], : arr.shape[1]][0]
    face = (m == SKIN) & (yy < neck_y - 6)
    ys, xs = np.nonzero(face)
    return np.array([xs.mean(), ys.mean()])


def shift(arr, dx, dy):
    out = np.zeros_like(arr)
    h, w = arr.shape[:2]
    ys, xs = np.nonzero(arr[:, :, 3] > 0)
    ny, nx = ys + dy, xs + dx
    ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
    out[ny[ok], nx[ok]] = arr[ys[ok], xs[ok]]
    return out


def paint_across(arr, src_mask, hole):
    """Fill `hole` with real cloth: each row's run of hole is copied from the cloth just beside
    it (to its right if there's room, else its left), so the folds and weave carry on."""
    out = np.zeros_like(arr)
    w = arr.shape[1]
    for y in np.unique(np.nonzero(hole)[0]):
        xs = np.nonzero(hole[y])[0]
        runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        for run in runs:
            x0, x1 = run[0], run[-1]
            width = x1 - x0 + 1
            for shift in [d * k for k in range(width + 2, width + 24) for d in (1, -1)]:
                src = run + shift
                if src.min() >= 0 and src.max() < w and src_mask[y, src].all():
                    out[y, run] = arr[y, src]
                    break
            else:  # no clean cloth beside it (up by the shoulder): the cloth below each pixel
                for x in run:
                    below = np.nonzero(src_mask[y:, x])[0]
                    if len(below):
                        out[y, x] = arr[y + below[0] + 2 if src_mask[min(y + below[0] + 2, arr.shape[0] - 1), x] else y + below[0], x]
            out[y, run, 3] = np.where(out[y, run, 3] > 0, 255, 0)
    return out


def paint_from(arr, src_mask, hole):
    """Fill `hole` with the colour of the nearest pixel in `src_mask`."""
    _, (iy, ix) = distance_transform_edt(~src_mask, return_indices=True)
    out = np.zeros_like(arr)
    out[hole] = arr[iy[hole], ix[hole]]
    return out


def swap(w, d, view):
    pw, pd = profile(CH / w / view), profile(CH / d / view)
    neck_w = json.load(open(CH / w / view / "parts.json"))["joints"]["neck"][1]
    neck_d = json.load(open(CH / d / view / "parts.json"))["joints"]["neck"][1]
    hw, hd = load(w, view, "head"), load(d, view, "head")
    tw, td = load(w, view, "torso"), load(d, view, "torso")
    mhw, mhd = material_map("head", hw, **pw), material_map("head", hd, **pd)
    mtw, mtd = material_map("torso", tw, **pw), material_map("torso", td, **pd)
    dx, dy = np.round(face_centre(hw, mhw, neck_w) - face_centre(hd, mhd, neck_d)).astype(int)

    out = CH / w / "layers" / f"hair-{d}" / view
    out.mkdir(parents=True, exist_ok=True)
    # the donor's hair, on the wearer's face
    dh = hd.copy()
    dh[~hair_of(hd, mhd)] = 0
    dh = shift(dh, dx, dy)
    # the wearer's own hair, hidden; what it covered and the new hair doesn't, painted back
    own = hair_of(hw, mhw)
    hide = np.zeros_like(hw)
    hide[own, 3] = 255
    face = mhw == SKIN
    yy = np.mgrid[: hw.shape[0], : hw.shape[1]][0]
    fys = np.nonzero(face & (yy < neck_w - 6))[0]
    # (a little way out from the face too: long hair hides the neck and ears, which come back)
    over_face = own & binary_dilation(face_of(mhw), iterations=7) & (yy >= fys.min() - 2) & ~(dh[:, :, 3] > 0)
    fill = paint_from(hw, face, over_face)
    Image.fromarray(dh).save(out / "head.png")
    Image.fromarray(hide).save(out / "head.hide.png")
    if fill[:, :, 3].any():
        Image.fromarray(fill).save(out / "head.fill.png")
    # the torso: a braid lying on it goes (painted over with the shirt around it), and the
    # donor's braid comes along
    own_t = hair_of(tw, mtw)
    if own_t.any():
        hide_t = np.zeros_like(tw)
        hide_t[own_t, 3] = 255
        rest = (mtw == IDS["shirt"]) & ~own_t  # cloth only: copying an outline makes stripes
        Image.fromarray(hide_t).save(out / "torso.hide.png")
        Image.fromarray(paint_across(tw, rest, own_t)).save(out / "torso.fill.png")
    dt = td.copy()
    dt[~hair_of(td, mtd)] = 0
    if dt[:, :, 3].any():
        Image.fromarray(shift(dt, dx, dy)).save(out / "torso.png")
    json.dump({"slot": "hair", "material": "hair", "about": f"{d}'s hair, cut from her art"}, open(out.parent / "layer.json", "w"), indent=1)
    return dx, dy


if __name__ == "__main__":
    for w in WOMEN:
        for d in WOMEN:
            if w != d:
                print(w, "wears", d, [swap(w, d, v) for v in ("front", "back")])

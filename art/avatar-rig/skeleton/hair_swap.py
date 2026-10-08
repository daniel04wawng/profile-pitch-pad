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

from cut_green import poly
from materials import IDS, MATERIALS, material_map, profile, recolour, reference_values

HERE = pathlib.Path(__file__).parent
CH = HERE / "characters"
WOMEN = ("sage-bob", "blue-pixie", "terracotta-curls", "plum-braid")
PEOPLE = ("green",) + WOMEN  # whose hair there is: his wavy crop, their bob, pixie, curls, braid
# who wears it: the base models (the man, the woman, the woman with her jacket off, whose head is
# the woman's own), each with no hair at all ("hair-none", what the café stacks a hair layer on)
MODELS = {"green": "green", "sage-bob": "sage-bob", "woman-tee": "sage-bob"}  # model -> whose hair is hers
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
        if (lab == k).sum() >= 14:  # brows are smaller than this; strands of fringe aren't
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


# whose neck, collar and shoulders show under a wearer's hair once it's gone: a woman with
# short hair, so they're drawn (the wearer's own hair hid hers)
# (in order: where the first has hair too, the next one's is used)
UNDER = {"green": ("blue-pixie", "terracotta-curls"), "woman-tee": ("blue-pixie", "terracotta-curls"), "sage-bob": ("blue-pixie", "terracotta-curls"), "plum-braid": ("blue-pixie", "terracotta-curls"),
         "terracotta-curls": ("blue-pixie",), "blue-pixie": ("terracotta-curls", "sage-bob")}


def composite(cid, view):
    """A woman at rest, all parts drawn in order, and its material map."""
    spec = json.load(open(CH / cid / view / "parts.json"))
    prof = profile(CH / cid / view)
    img = np.zeros((280, 256, 4), np.uint8)
    mat = np.zeros((280, 256), np.uint8)
    for p in spec["parts"]:
        a = load(cid, view, p["part"])
        on = a[:, :, 3] > 0
        img[on] = a[on]
        mat[on] = material_map(p["part"], a, **prof)[on]
    return img, mat


def hex_of(rgb):
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def drop_specks(arr, smallest=6):
    """In place: take away isolated bits (an outline dot with nothing beside it)."""
    lab, n = label(arr[:, :, 3] > 0)
    for k in range(1, n + 1):
        if (lab == k).sum() < smallest:
            arr[lab == k] = 0
    return arr


def under(w, view, neck_w):
    """What's under the wearer's hair, from each UNDER woman in turn (see under_from)."""
    out = np.zeros((280, 256, 4), np.uint8)
    for b in UNDER[w]:
        layer = under_from(b, w, view, neck_w)
        gap = (out[:, :, 3] == 0) & (layer[:, :, 3] > 0)
        out[gap] = layer[gap]
    return out


def under_from(b, w, view, neck_w):
    """What's under the wearer's hair: the UNDER woman's neck, collar and shoulders, moved onto
    the wearer (faces matched) and recoloured to the wearer's own skin, shirt and tee, shading
    and outlines kept. Her hair isn't anything's underneath, so it's left out."""
    bi, bm = composite(b, view)
    wi, wm = composite(w, view)
    neck_b = json.load(open(CH / b / view / "parts.json"))["joints"]["neck"][1]
    dx, dy = np.round(face_centre(wi, wm, neck_w) - face_centre(bi, bm, neck_b)).astype(int)
    looks = {}
    for name in ("skin", "shirt", "tee"):
        px = wi[wm == IDS[name]][:, :3]
        if len(px):
            looks[name] = hex_of(np.median(px, axis=0))
    refs = reference_values([(bi, bm)])
    bm2 = bm.copy()
    if "tee" not in looks:  # no tee of her own (a tee is her only top): the tee becomes her shirt
        bm2[bm == IDS["tee"]] = IDS["shirt"]
        refs["shirt"] = reference_values([(bi, bm2)])["shirt"]
    out = recolour(bi, bm2, looks, refs)
    out[hair_of(bi, bm) | (bm == IDS["hair"])] = 0  # her hair and its outline: nobody's underneath
    # her face is hers: only its plain skin is borrowed, never her eyes, brows or lines
    out[binary_dilation(face_of(bm), iterations=1) & (bm != IDS["skin"])] = 0
    return drop_specks(shift(out, dx, dy))


# Hair the colour rules can't see, traced by hand: hair drawn as near-black line work over the
# face's edge (a lock of fringe on the temple, strands beside the cheek), which reads as
# outline. Everything of her head inside these is hidden with her hair.
HIDE_TOO = {
    ("plum-braid", "front"): [
        [(112, 50), (141, 44), (143, 49), (139, 55), (135, 58), (128, 58), (123, 60), (120, 66), (112, 66)],  # the fringe's lock
        [(147, 46), (153, 46), (154, 75), (147, 75)],  # strands beside her cheek
    ],
}


def offset(w, d, view):
    """How far to move d's head things so d's face sits on w's."""
    def centre(c):
        a = load(c, view, "head")
        return face_centre(a, material_map("head", a, **profile(CH / c / view)), json.load(open(CH / c / view / "parts.json"))["joints"]["neck"][1])
    return np.round(centre(w) - centre(d)).astype(int)


def swap(w, d, view):
    """w wearing d's hair (d None: no hair at all, her head as a hair layer goes on)."""
    pw = profile(CH / w / view)
    neck_w = json.load(open(CH / w / view / "parts.json"))["joints"]["neck"][1]
    hw, tw = load(w, view, "head"), load(w, view, "torso")
    mhw, mtw = material_map("head", hw, **pw), material_map("torso", tw, **pw)
    out = CH / w / "layers" / f"hair-{d or 'none'}" / view
    out.mkdir(parents=True, exist_ok=True)
    if d:
        pd = profile(CH / d / view)
        hd, td = load(d, view, "head"), load(d, view, "torso")
        mhd, mtd = material_map("head", hd, **pd), material_map("torso", td, **pd)
        dx, dy = offset(w, d, view)
        # the donor's hair, on the wearer's face
        dh = hd.copy()
        dh[~hair_of(hd, mhd)] = 0
        dh = shift(dh, dx, dy)
        drop_specks(dh)  # stray dots of the donor's outline, away from her hair
    else:
        dx = dy = 0
        dh = np.zeros_like(hw)
        td = np.zeros_like(tw)
        mtd = np.zeros(tw.shape[:2], np.uint8)
    # the wearer's own hair, hidden; what it covered and the new hair doesn't, painted back
    own = hair_of(hw, mhw)
    for pts in HIDE_TOO.get((w, view), []):
        own |= poly((256, 280), pts) & (hw[:, :, 3] > 0)
    hide = np.zeros_like(hw)
    hide[own, 3] = 255
    face = mhw == SKIN
    yy = np.mgrid[: hw.shape[0], : hw.shape[1]][0]
    fys = np.nonzero(face & (yy < neck_w - 6))[0]
    # (a little way out from the face too: long hair hides the neck and ears, which come back)
    bare = own & ~(dh[:, :, 3] > 0)  # where her hair was and the new hair isn't
    ub = under(w, view, neck_w)
    fill = np.zeros_like(hw)
    fill[bare] = ub[bare]
    # over the face itself (a fringe on the forehead): her own skin, carried in
    over_face = bare & binary_dilation(face_of(mhw), iterations=4) & (yy >= fys.min() - 2) & ~(fill[:, :, 3] > 0)
    painted = paint_from(hw, face, over_face)
    fill[over_face] = painted[over_face]
    # anything still open inside the new head (where the borrowed neck had hair too, and the
    # new hair doesn't reach) takes its nearest neighbour's colour
    res = hw.copy()
    res[own] = 0
    for layer in (fill, dh):
        on = layer[:, :, 3] > 0
        res[on] = layer[on]
    solid = res[:, :, 3] > 0
    holes = binary_fill_holes(solid) & ~solid
    if holes.any():  # from skin or cloth beside it: copying a dark outline or hair draws squiggles
        near = paint_from(res, solid & (res[:, :, :3].max(2) >= 110), holes)
        fill[holes] = near[holes]
    Image.fromarray(dh).save(out / "head.png")
    Image.fromarray(hide).save(out / "head.hide.png")
    drop_specks(fill)
    if fill[:, :, 3].any():
        Image.fromarray(fill).save(out / "head.fill.png")
    # the torso: a braid lying on it goes (painted over with the shirt around it), and the
    # donor's braid comes along
    own_t = hair_of(tw, mtw)
    if own_t.any():
        hide_t = np.zeros_like(tw)
        hide_t[own_t, 3] = 255
        Image.fromarray(hide_t).save(out / "torso.hide.png")
        fill_t = np.zeros_like(tw)
        fill_t[own_t] = ub[own_t]
        drop_specks(fill_t)
        Image.fromarray(fill_t).save(out / "torso.fill.png")
    if d:
        dt = td.copy()
        dt[~hair_of(td, mtd)] = 0
        if dt[:, :, 3].any():
            Image.fromarray(shift(dt, dx, dy)).save(out / "torso.png")
    about = f"{d}'s hair, cut from her art" if d else "no hair: her own taken away, what it hid rebuilt"
    json.dump({"slot": "hair", "material": "hair", "about": about}, open(out.parent / "layer.json", "w"), indent=1)
    return int(dx), int(dy)


def fit_wear(w, view):
    """The man's beanie and glasses (accessories.py), moved so his face sits on w's."""
    dx, dy = offset(w, "green", view)
    for name in ("beanie", "glasses"):
        src = CH / "green" / "layers" / name / view
        if not src.is_dir():
            continue
        out = CH / w / "layers" / name / view
        out.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.png"):
            Image.fromarray(shift(np.array(Image.open(f).convert("RGBA")), dx, dy)).save(out / f.name)
        meta = CH / "green" / "layers" / name / "layer.json"
        if meta.exists():
            (CH / w / "layers" / name / "layer.json").write_text(meta.read_text())


if __name__ == "__main__":
    for w, own in MODELS.items():
        print(w, "with no hair", [swap(w, None, v) for v in ("front", "back")])
        for d in PEOPLE:
            if d != own:
                print(w, "wears", d, [swap(w, d, v) for v in ("front", "back")])
        if w != "green":
            for v in ("front", "back"):
                fit_wear(w, v)

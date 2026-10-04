"""Import generated character pose sheets into game sprites.

Each art/people/<person>/<outfit>/pose-sheet.png is a 4x4 grid of poses (see PACK-README): walk-front 1-4, walk-back 1-4, stand-front, stand-back, sit-front, sit-sip, sit-back.
The grid isn't pixel-perfect, so poses are found from their actual alpha outlines, then:
  - mirrored where needed so 'front' poses face the viewer's left and 'back' poses face away
    to the right (the game's convention; it mirrors for the other two directions),
  - scaled with one factor per character (standing ~58px tall), box-filtered on alpha-weighted
    colour, alpha thresholded, colours snapped to one palette per character, 1px dark outline,
  - aligned: standing/walking frames at the feet (torso centre over the floor point), seated
    frames at the seat contact point.
Writes public/cafe/people/<person>--<outfit>.png (frames side by side) and people.json, which
lists every person and their outfits (a person's skin and hair are theirs; outfits vary).

    python3 art/import_people.py [--preview out.png]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ART = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(ART), "public", "cafe", "people")
ORDER = ["walk-front-1", "walk-front-2", "walk-front-3", "walk-front-4",
         "walk-back-1", "walk-back-2", "walk-back-3", "walk-back-4",
         "stand-front", "stand-back", "sit-front", "sit-sip", "sit-back"]
# the generated sheets face screen-right for front views and seated-from-behind faces left
MIRROR = {"walk-front-1", "walk-front-2", "walk-front-3", "walk-front-4", "stand-front", "sit-front", "sit-sip", "sit-back"}
STAND_H = 58  # px, standing height in game
OUTLINE = (30, 18, 14, 255)
COLOURS = 40


def components(alpha, min_px):
    """Connected blobs of solid alpha (4-neighbour), as (y0, x0, y1, x1, count)."""
    H, W = alpha.shape
    seen = np.zeros_like(alpha, dtype=bool)
    out = []
    ys, xs = np.nonzero(alpha)
    for y, x in zip(ys, xs):
        if seen[y, x]:
            continue
        stack = [(y, x)]
        seen[y, x] = True
        y0 = y1 = y
        x0 = x1 = x
        n = 0
        while stack:
            cy, cx = stack.pop()
            n += 1
            y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < H and 0 <= nx < W and alpha[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if n >= min_px:
            out.append([y0, x0, y1, x1, n])
    return out


def find_poses(sheet):
    """Boxes of the 13 poses in reading order. Poses can touch their neighbours, so the sheet is
    cut along its emptiest lines near the expected 4x4 grid: rows first, then columns per row."""
    a = np.asarray(sheet)[..., 3].astype(np.float64) / 255.0
    ys, xs = np.nonzero(a > 0.6)
    top, bot, lft, rgt = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

    def cut(profile, lo, hi, n):
        """n-1 cut positions between lo and hi, each at the emptiest line near its grid spot."""
        cuts = []
        step = (hi - lo) / n
        for k in range(1, n):
            c = lo + step * k
            w0, w1 = int(c - step * 0.3), int(c + step * 0.3)
            seg = profile[w0:w1]
            cuts.append(w0 + int(np.argmin(seg)))
        return [lo] + cuts + [hi]

    rows = cut(a.sum(axis=1), top, bot, 4)
    boxes = []
    for r in range(4):
        y0, y1 = rows[r], rows[r + 1]
        band = a[y0:y1]
        cols = cut(band.sum(axis=0), lft, rgt, 4)
        for c in range(4):
            x0, x1 = cols[c], cols[c + 1]
            cell = band[:, x0:x1] > 0.6
            if cell.sum() < 0.02 * cell.size:
                continue  # an empty slot in the last row
            cy, cx = np.nonzero(cell)
            boxes.append((x0 + cx.min(), y0 + cy.min(), x0 + cx.max() + 1, y0 + cy.max() + 1))
    return boxes


def clean_crop(sheet, box):
    """The pose, with only its own figure kept (neighbouring poses' edges and glow removed)."""
    x0, y0, x1, y1 = box
    pad = 6
    crop = sheet.crop((max(0, x0 - pad), max(0, y0 - pad), min(sheet.width, x1 + pad), min(sheet.height, y1 + pad)))
    arr = np.asarray(crop).copy()
    solid = arr[..., 3] > 160
    blobs = components(solid, 1)
    if blobs:
        biggest = max(b[4] for b in blobs)
        keep = np.zeros_like(solid)
        # keep the figure and any detached bits big enough to be part of it (a cup, a shoe)
        H, W = solid.shape
        seen = np.zeros_like(solid)
        for b in blobs:
            if b[4] >= 0.01 * biggest:
                keep[b[0] : b[2] + 1, b[1] : b[3] + 1] |= solid[b[0] : b[2] + 1, b[1] : b[3] + 1]
        arr[..., 3] = np.where(keep, arr[..., 3], 0)
    im = Image.fromarray(arr)
    return im.crop(im.getbbox())


def shrink(im, k):
    """Scale by k with an alpha-weighted box filter, then make alpha binary."""
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    arr = np.asarray(im).astype(np.float64)
    a = arr[..., 3:4] / 255.0
    pre = np.concatenate([arr[..., :3] * a, a * 255], axis=2).astype(np.float32)
    chans = [np.asarray(Image.fromarray(pre[..., c]).resize((w, h), Image.BOX)) for c in range(4)]
    A = chans[3]
    rgb = np.stack(chans[:3], axis=2) / np.maximum(A[..., None] / 255.0, 1e-6)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = np.where(A > 120, 255, 0)
    return Image.fromarray(out)


def anchor(im, seated):
    """(x, y) inside the frame that sits on the floor point (feet) or the seat (seated)."""
    a = np.asarray(im)[..., 3] > 0
    H, W = a.shape
    rows = np.nonzero(a.any(axis=1))[0]
    top, bot = rows[0], rows[-1]
    band = a[top + int((bot - top) * 0.3) : top + int((bot - top) * 0.55)]  # the torso
    xs = np.nonzero(band)[1]
    cx = int(round(np.median(xs))) if len(xs) else W // 2
    if seated:
        return cx, top + int((bot - top) * 0.6)
    return cx, bot + 1


def outline(im):
    a = im.getchannel("A").load()
    out = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            if not a[x, y] and any(0 <= x + dx < im.width and 0 <= y + dy < im.height and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), OUTLINE)
    return out


def make_gait(frames, fw, anchor):
    """The generated walk frames are all one frozen stride, and cutting/mirroring their legs
    looked wrong (toes pointing backwards, legs jumping about). So each walk frame keeps the
    generated upper body and gets legs redrawn in the person's own trouser and shoe colours
    (sampled from their standing pose), in a real alternating cycle: one leg forward, passing
    (the swinging foot lifted, the body bobbing up), the other leg forward, passing. The far
    leg is in shade, the trailing knee bends, toes always point the way you walk."""
    import math
    arr = np.asarray(frames).copy()
    ax, ay = anchor
    fh = arr.shape[0]
    get = lambda n: arr[:, ORDER.index(n) * fw : (ORDER.index(n) + 1) * fw].copy()
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    def ramp(px, fallback):
        if not px:
            return fallback
        px = sorted(px, key=lum)
        return [tuple(int(v) for v in px[int(len(px) * q)][:3]) + (255,) for q in (0.15, 0.5, 0.85)]

    def spread(f):
        low = (f[..., 3] > 0)[ay - 4 : ay]
        xs = np.nonzero(low.any(0))[0]
        return xs.max() - xs.min() if len(xs) else 0

    for d in ("front", "back"):
        S = get(f"stand-{d}")
        a = S[..., 3] > 0
        top = np.nonzero(a.any(1))[0][0]
        H = ay - top
        hip = top + int(H * 0.6)
        pants = ramp([tuple(S[y, x]) for y in range(hip + 3, ay - 6) for x in range(fw) if a[y, x] and lum(S[y, x]) > 40], [(40, 36, 44, 255), (58, 52, 62, 255), (80, 74, 86, 255)])
        shoes = ramp([tuple(S[y, x]) for y in range(ay - 4, ay) for x in range(fw) if a[y, x] and lum(S[y, x]) > 120], [(200, 196, 188, 255), (230, 226, 218, 255), (250, 248, 244, 255)])
        A = max((get(f"walk-{d}-{i}") for i in range(1, 5)), key=spread)
        sa = A[..., 3] > 0
        cx = int(np.median(np.nonzero(sa[top + int(H * 0.3) : top + int(H * 0.55)])[1]))
        fwd = (-1.0, 0.35) if d == "front" else (1.0, -0.3)  # the walking direction, in the sprite
        for k in range(4):
            s = math.cos(2 * math.pi * k / 4)  # +1 one leg forward, -1 the other
            bob = -1 if abs(s) < 0.5 else 0
            img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            px = img.load()

            def put(x, y, c):
                x, y = int(round(x)), int(round(y))
                if 0 <= x < fw and 0 <= y < fh:
                    px[x, y] = c

            def leg(hx, swing, near):
                fx, fy = hx + fwd[0] * swing * 6.0, ay - 3 + fwd[1] * swing * 6.0
                fy -= 2 if (abs(swing) < 0.3 and near) else 0  # the swinging foot clears the floor
                hy = hip + bob
                L = max(1, int(fy - hy))
                knee = 1.4 if swing < -0.3 else 0.5  # the trailing leg bends at the knee
                for i in range(L + 1):
                    u = i / L
                    x = hx + (fx - hx) * u + fwd[0] * knee * math.sin(u * math.pi)
                    y = hy + (fy - hy) * u
                    w = 3.1 - 0.7 * u  # baggy at the hip, narrower at the hem
                    for dx in np.arange(-w, w + 0.01, 0.5):
                        lit, shade = dx < -w + 1.1, dx > w - 1.3
                        c = pants[2] if lit else (pants[0] if shade else pants[1])
                        if not near:
                            c = pants[1] if lit else pants[0]  # the far leg is in shade
                        put(x + dx, y, c)
                tx = 1 if fwd[0] > 0 else -1
                for i in range(-2, 6):  # a chunky sneaker, toe forward, white sole
                    for j in range(4):
                        if j == 0 and i > 3:
                            continue
                        c = shoes[2] if j == 3 else (shoes[1] if (i < 4 or j > 0) else shoes[0])
                        if not near and j < 3:
                            c = shoes[0]
                        put(fx + tx * i * 0.75 - tx * 0.5, fy - 1 + j + fwd[1] * i * 0.4, c)

            far, near = (cx + 3.5, cx - 3.0) if d == "front" else (cx - 3.5, cx + 3.0)
            leg(far, -s if d == "front" else s, False)
            leg(near, s if d == "front" else -s, True)
            F = np.asarray(img).copy()
            U = A.copy()
            U[hip + 1 :] = 0
            U = np.roll(U, bob, axis=0)
            m = U[..., 3] > 0
            F[m] = U[m]
            out = Image.fromarray(F)
            al = out.getchannel("A").load()
            o = out.copy()
            for y in range(fh):
                for x in range(fw):
                    if not al[x, y] and any(0 <= x + dx < fw and 0 <= y + dy < fh and al[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        o.putpixel((x, y), OUTLINE)
            j = ORDER.index(f"walk-{d}-{k + 1}")
            arr[:, j * fw : (j + 1) * fw] = np.asarray(o)
    return Image.fromarray(arr)


def import_character(path, name):
    sheet = Image.open(path).convert("RGBA")
    boxes = find_poses(sheet)
    if len(boxes) < len(ORDER):
        raise SystemExit(f"{name}: found {len(boxes)} poses, expected {len(ORDER)}")
    boxes = boxes[: len(ORDER)]
    crops = {}
    for pose, box in zip(ORDER, boxes):
        c = clean_crop(sheet, box)
        if pose in MIRROR:
            c = c.transpose(Image.FLIP_LEFT_RIGHT)
        crops[pose] = c
    k = STAND_H / crops["stand-front"].height
    small = {p: shrink(c, k) for p, c in crops.items()}
    # one palette for the character, from all its frames together
    strip = Image.new("RGBA", (sum(s.width for s in small.values()), max(s.height for s in small.values())), (0, 0, 0, 0))
    x = 0
    spots = {}
    for p, s in small.items():
        strip.alpha_composite(s, (x, 0))
        spots[p] = x
        x += s.width
    al = np.asarray(strip)[..., 3]
    pal_img = Image.fromarray(np.asarray(strip)[..., :3]).quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    snapped = Image.fromarray(np.dstack([np.asarray(pal_img), al]))
    small = {p: outline(snapped.crop((spots[p], 0, spots[p] + s.width, s.height))) for p, s in small.items()}
    # frames share one size; standing/walking frames meet the floor at FOOT, seated at SEAT
    anchors = {p: anchor(s, p.startswith("sit")) for p, s in small.items()}
    left = max(anchors[p][0] for p in small) + 1
    right = max(s.width - anchors[p][0] for p, s in small.items()) + 1
    up = max(anchors[p][1] for p in small) + 1
    down = max(s.height - anchors[p][1] for p, s in small.items()) + 1
    fw, fh = left + right, up + down
    frames = Image.new("RGBA", (fw * len(ORDER), fh), (0, 0, 0, 0))
    for i, p in enumerate(ORDER):
        s = small[p]
        ax, ay = anchors[p]
        frames.alpha_composite(s, (i * fw + left - ax, up - ay))
    frames = make_gait(frames, fw, (left, up))
    os.makedirs(OUT, exist_ok=True)
    frames.save(os.path.join(OUT, f"{name}.png"))
    return {"frame": [int(fw), int(fh)], "anchor": [int(left), int(up)], "frames": ORDER}


if __name__ == "__main__":
    src = os.path.join(ART, "people")
    manifest = {}
    for person in sorted(os.listdir(src)):
        pdir = os.path.join(src, person)
        if not os.path.isdir(pdir):
            continue
        for outfit in sorted(os.listdir(pdir)):
            p = os.path.join(pdir, outfit, "pose-sheet.png")
            if os.path.exists(p):
                key = f"{person}/{outfit}"
                manifest[key] = import_character(p, f"{person}--{outfit}")
                print(f"{key:24s} frame {manifest[key]['frame']}")
    for old in os.listdir(OUT):  # sheets for people/outfits that are gone
        if old.endswith(".png") and old[:-4].replace("--", "/") not in manifest:
            os.remove(os.path.join(OUT, old))
    people = {}
    for key in manifest:
        person, outfit = key.split("/")
        people.setdefault(person, []).append(outfit)
    json.dump({"standHeight": STAND_H, "people": people, "characters": manifest}, open(os.path.join(OUT, "people.json"), "w"), indent=1)
    if "--preview" in sys.argv:
        S = 4
        rows = [Image.open(os.path.join(OUT, f"{k.replace('/', '--')}.png")).convert("RGBA") for k in manifest]
        W = max(r.width for r in rows)
        H = sum(r.height for r in rows)
        sheet = Image.new("RGBA", (W, H), (205, 140, 85, 255))
        y = 0
        for r in rows:
            sheet.alpha_composite(r, (0, y))
            y += r.height
        sheet.resize((W * S, H * S), Image.NEAREST).save(sys.argv[-1])

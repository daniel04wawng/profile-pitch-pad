"""Café visitors, drawn like the room's mock-ups: small realistic people turned three-quarters
to the room's isometric angle, rendered from a tiny 3D figure (capsule limbs, a box-ish
torso, a round head) lit from the top-left, then outlined. Poses (standing, a walking
stride, sitting) come from the same figure, so every frame matches.

Coordinates: floor axes a (down-right on screen) and b (down-left), z up, in px.
Screen: x = a - b, y = (a + b) / 2 - z  (the room's 2:1 isometric projection).

    python3 art/draw_people.py --preview out.png
"""
import math
import sys

from PIL import Image

FW, FH = 28, 66
FOOT = (14, 63)  # screen point (in a frame) under the figure's feet
OUTLINE = (30, 18, 14)


def proj(p):
    a, b, z = p
    return (FOOT[0] + (a - b), FOOT[1] + (a + b) / 2 - z)


def depth(p):
    a, b, z = p
    return a + b + z * 0.01  # nearer the viewer = bigger


class Canvas:
    def __init__(self):
        self.col = {}  # (x, y) -> (rgb, depth)

    def put(self, x, y, rgb, d):
        x, y = int(math.floor(x)), int(math.floor(y))
        if not (0 <= x < FW and 0 <= y < FH):
            return
        old = self.col.get((x, y))
        if old is None or d >= old[1]:
            self.col[(x, y)] = (rgb, d)

    def image(self):
        im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
        for (x, y), (rgb, _) in self.col.items():
            im.putpixel((x, y), rgb + (255,))
        a = im.getchannel("A").load()
        out = im.copy()
        for y in range(FH):
            for x in range(FW):
                if not a[x, y] and any(0 <= x + dx < FW and 0 <= y + dy < FH and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    out.putpixel((x, y), OUTLINE + (255,))
        return out


def shade(ramp, lit):
    """ramp = (dark, mid, light); lit in -1..1 (1 = facing the top-left light)."""
    return ramp[2] if lit > 0.45 else (ramp[0] if lit < -0.35 else ramp[1])


def capsule(cv, p0, p1, r, ramp, bias=0.0):
    """A limb: a rounded tube from p0 to p1 (3D points) of radius r, shaded across its width."""
    x0, y0 = proj(p0)
    x1, y1 = proj(p1)
    d0, d1 = depth(p0), depth(p1)
    minx, maxx = int(min(x0, x1) - r - 1), int(max(x0, x1) + r + 1)
    miny, maxy = int(min(y0, y1) - r - 1), int(max(y0, y1) + r + 1)
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy or 1e-6
    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - x0) * vx + (py - y0) * vy) / L2))
            cx, cy = x0 + vx * t, y0 + vy * t
            dx, dy = px - cx, py - cy
            if dx * dx + dy * dy <= r * r:
                lit = (-dx * 0.8 - dy * 0.6) / max(r, 0.5) + bias
                cv.put(x, y, shade(ramp, lit), d0 + (d1 - d0) * t + 0.3 * (1 - (dx * dx + dy * dy) / (r * r + 1e-6)))


def blob(cv, c, rx, ry, ramp, d_bias=0.0, cut=None, bias=0.0):
    """An ellipse on screen centred on 3D point c (a head, a hand, a bun), shaded like a ball."""
    x0, y0 = proj(c)
    d = depth(c) + d_bias
    for y in range(int(y0 - ry - 1), int(y0 + ry + 2)):
        for x in range(int(x0 - rx - 1), int(x0 + rx + 2)):
            u = (x + 0.5 - x0) / rx
            v = (y + 0.5 - y0) / ry
            if u * u + v * v <= 1 and (cut is None or cut(u, v)):
                cv.put(x, y, shade(ramp, -u * 0.8 - v * 0.6 + bias), d + 0.5 * (1 - u * u - v * v))


def quad(cv, pts, ramp, lit, d):
    """A flat polygon (4 projected 3D points), one shade: torso faces, jacket panels."""
    P = [proj(p) for p in pts]
    minx, maxx = int(min(p[0] for p in P)) - 1, int(max(p[0] for p in P)) + 1
    miny, maxy = int(min(p[1] for p in P)) - 1, int(max(p[1] for p in P)) + 1

    def inside(x, y):
        s = 0
        for i in range(len(P)):
            (ax, ay), (bx, by) = P[i], P[(i + 1) % len(P)]
            s2 = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
            if s2 != 0:
                if s == 0:
                    s = 1 if s2 > 0 else -1
                elif (s2 > 0) != (s > 0):
                    return False
        return True

    col = shade(ramp, lit) if isinstance(ramp, tuple) and len(ramp) == 3 and isinstance(ramp[0], tuple) else ramp
    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            if inside(x + 0.5, y + 0.5):
                cv.put(x, y, col, d)


# ---------------------------------------------------------------- the figure

def person(look, facing="front", pose="stand", phase=0.0):
    """facing 'front' = turned toward the viewer's left (forward = +b), 'back' = away to the
    right (forward = -b). phase 0..1 drives the walking stride."""
    cv = Canvas()
    fwd = (0.0, 1.0) if facing == "front" else (0.0, -1.0)  # forward on the floor (a, b)
    side = (1.0, 0.0) if facing == "front" else (-1.0, 0.0)  # the figure's left hand side
    F = lambda f, s, z: (f * fwd[0] + s * side[0], f * fwd[1] + s * side[1], z)

    walk = pose == "walk"
    sit = pose == "sit"
    swing = math.sin(phase * 2 * math.pi) if walk else 0.0
    bob = abs(math.cos(phase * 2 * math.pi)) * 1.0 if walk else 0.0

    hip_z = 27 + bob
    if sit:
        hip_z = 16
    shoulder_z = hip_z + 18
    head_z = shoulder_z + 8.5

    skin, hair, top, jacket, pants, shoe = look["skin"], look["hair"], look["top"], look["jacket"], look["pants"], look["shoe"]

    # ---- legs (far leg first so the near one draws over it)
    for s_off, sgn in ((-2.6, -1), (2.6, 1)):
        hip = F(0, s_off, hip_z)
        if sit:
            knee = F(9, s_off, hip_z + 1)
            foot = F(10, s_off, 2)
        else:
            step = 7 * swing * sgn
            knee = F(step * 0.55, s_off, hip_z * 0.52 + (1.2 if step > 0 else 0))
            foot = F(step, s_off, 2.0 + (1.6 if (walk and step < -2) else 0))
        capsule(cv, hip, knee, 2.7, pants, bias=0.1)
        capsule(cv, knee, foot, 2.4, pants, bias=0.1)
        # sneaker: a little box pointing forward, white sole
        toe = (foot[0] + fwd[0] * 3.2, foot[1] + fwd[1] * 3.2, foot[2] - 0.6)
        heel = (foot[0] - fwd[0] * 1.2, foot[1] - fwd[1] * 1.2, foot[2] - 0.6)
        capsule(cv, heel, toe, 1.7, shoe)
        capsule(cv, (heel[0], heel[1], heel[2] - 1.4), (toe[0], toe[1], toe[2] - 1.4), 0.9, ((214, 210, 202), (236, 232, 224), (250, 248, 242)))

    # ---- torso: a slightly tapered box. Its two faces toward the viewer (+a, +b) are drawn:
    # for 'front' that's the chest (+b) and the left side (+a); for 'back', the back and the
    # right side. The chest shows the tee through the open jacket.
    w, dpt = 5.0, 2.8  # half-width across the shoulders, half-depth
    outer = jacket or top
    z0, z1 = hip_z - 0.5, shoulder_z
    taper = 0.8  # narrower at the waist
    def box_pt(f, s_, z):
        k = 1 - taper * (z1 - z) / (z1 - z0) * 0.25
        return F(f * k, s_ * k, z)
    chest = [box_pt(dpt, -w, z0), box_pt(dpt, w, z0), box_pt(dpt, w, z1), box_pt(dpt, -w, z1)]
    side_s = w if facing == "front" else -w  # the side face toward +a
    side_face = [box_pt(dpt, side_s, z0), box_pt(-dpt, side_s, z0), box_pt(-dpt, side_s, z1), box_pt(dpt, side_s, z1)]
    front_face = chest if facing == "front" else [box_pt(-dpt, -w, z0), box_pt(-dpt, w, z0), box_pt(-dpt, w, z1), box_pt(-dpt, -w, z1)]
    dz = depth(F(0, 0, hip_z))
    quad(cv, side_face, outer[0], 0, dz + 1)
    quad(cv, front_face, outer[1], 0, dz + 1.5)
    quad(cv, [box_pt(dpt, -w, z1), box_pt(dpt, w, z1), box_pt(-dpt, w, z1), box_pt(-dpt, -w, z1)], outer[2], 0, dz + 2)  # shoulders
    if facing == "front":
        # tee showing between the open jacket fronts, a lit edge on each lapel
        for zz in range(int(z0) + 1, int(z1)):
            for ss in (-1.2, -0.4, 0.4):
                x, y = proj(box_pt(dpt + 0.2, ss, zz))
                cv.put(x, y, top[1] if jacket else top[2], dz + 3)
            if jacket:
                x, y = proj(box_pt(dpt + 0.2, 1.3, zz))
                cv.put(x, y, outer[2], dz + 3)
        # hem
        for ss in [i / 2 for i in range(-10, 11)]:
            x, y = proj(box_pt(dpt + 0.1, ss, z0 + 0.5))
            cv.put(x, y, outer[0], dz + 3)
    elif look.get("hood"):
        blob(cv, F(-dpt - 0.4, 0, shoulder_z + 0.5), 3.6, 2.0, outer, d_bias=4)

    # ---- arms (far arm, then near arm after the head so it overlaps the body correctly)
    def arm(sgn):
        sh = F(0, sgn * (w + 0.4), shoulder_z - 1.0)
        a_sw = -6 * swing * sgn if walk else 0
        if sit:
            el = F(4.5, sgn * (w + 0.6), shoulder_z - 8)
            hand = F(8.5, sgn * 2.5, shoulder_z - 8.5)
        else:
            el = F(a_sw * 0.5, sgn * (w + 1.0), shoulder_z - 8.5)
            hand = F(a_sw, sgn * (w + 0.8), shoulder_z - 16)
        capsule(cv, sh, el, 2.2, outer)
        capsule(cv, el, hand, 1.9, outer if not look.get("rolled") else skin)
        blob(cv, hand, 1.5, 1.6, skin)
        return hand

    arm(-1)

    # ---- neck and head
    capsule(cv, F(0, 0, shoulder_z - 0.5), F(0.3, 0, shoulder_z + 2.5), 1.6, skin)
    hc = F(0.6, 0, head_z)
    blob(cv, hc, 5.2, 6.0, skin)
    hx, hy = proj(hc)
    d_face = depth(hc) + 2
    if facing == "front":
        # three-quarter face toward the viewer's left: features sit left of centre
        for ex in (-2.6, 0.6):
            cv.put(hx + ex, hy - 0.3, (34, 22, 18), d_face)
            cv.put(hx + ex, hy + 0.7, (34, 22, 18), d_face)
        for bx in (-2.6, 0.6):
            cv.put(hx + bx, hy - 2.0, hair[0], d_face)  # brows
        cv.put(hx - 1.0, hy + 2.6, (150, 72, 60), d_face)  # mouth
        cv.put(hx + 3.4, hy + 0.6, skin[0], d_face)  # ear
    # ---- hair
    style = look["style"]
    if facing == "front":
        cover = {
            "messy": lambda u, v: v < -0.18 + 0.12 * math.sin(u * 9) or u > 0.55,
            "short": lambda u, v: v < -0.3 or u > 0.6,
            "long": lambda u, v: v < -0.3 or u > 0.45 or u < -0.75,
            "bob": lambda u, v: v < -0.25 or u > 0.5 or (u < -0.7 and v < 0.6),
            "buzz": lambda u, v: v < -0.55 or (u > 0.7 and v < 0.2),
        }[style]
    else:
        cover = {
            "messy": lambda u, v: v < 0.55,
            "short": lambda u, v: v < 0.5,
            "long": lambda u, v: True,
            "bob": lambda u, v: v < 0.7,
            "buzz": lambda u, v: v < 0.35,
        }[style]
    grow = {"messy": 1.0, "short": 0.6, "long": 0.9, "bob": 1.0, "buzz": 0.2}[style]
    blob(cv, hc, 5.2 + grow, 6.0 + grow * 0.8, hair, d_bias=1.0 if facing == "front" else 3.0, cut=cover)
    if style == "messy":  # a few tufts sticking up
        for (u, h) in ((-2.5, 1.5), (0.0, 2.2), (2.5, 1.4)):
            cv.put(hx + u, hy - 6.2 - h * 0.6, hair[1], d_face + 1)
            cv.put(hx + u + 0.8, hy - 6.6 - h * 0.6, hair[2], d_face + 1)
    if style == "long":  # falls past the shoulders
        side_x = 3.6 if facing == "front" else 0
        for k in range(12):
            for xx in ((-4.8, -4.0, 3.8, 4.6) if facing == "front" else tuple(x / 2 for x in range(-9, 10))):
                cv.put(hx + xx, hy + 2 + k, hair[1] if abs(xx) < 4.4 else hair[0], d_face - (3 if facing == "front" else -3))

    arm(1)
    return cv.image()


# ---------------------------------------------------------------- preview

def R(*hexes):
    return tuple(tuple(int(h[i : i + 2], 16) for i in (1, 3, 5)) for h in hexes)


LOOKS = {
    "daniel": dict(style="messy", skin=R("#9a5e3e", "#be7e58", "#d89a72"), hair=R("#1e1612", "#33261e", "#4e3c30"),
                   top=R("#2a2a2e", "#3a3a40", "#4e4e56"), jacket=None, pants=R("#1c1618", "#2a2224", "#3a3034"), shoe=R("#8c8890", "#b0acb2", "#cfccd2")),
    "green jacket": dict(style="short", skin=R("#b07a52", "#cf9a70", "#e6b88e"), hair=R("#141418", "#24242c", "#383844"),
                         top=R("#cfc6b0", "#ece4d0", "#fbf6ea"), jacket=R("#3a4428", "#566238", "#72804a"), pants=R("#22242a", "#33363e", "#474b54"), shoe=R("#c8c4bc", "#ece8e0", "#fbf9f4")),
    "red jacket": dict(style="long", skin=R("#c08860", "#dca880", "#f0c49c"), hair=R("#2a1a12", "#4a2e1c", "#6a4428"),
                       top=R("#d8ccb4", "#f0e6d2", "#fdf8ec"), jacket=R("#6e2a1c", "#94402a", "#b85a3a"), pants=R("#5a7898", "#7898b8", "#9ab6d0"), shoe=R("#c8c4bc", "#ece8e0", "#fbf9f4")),
    "navy hoodie": dict(style="short", skin=R("#b07a52", "#cf9a70", "#e6b88e"), hair=R("#141418", "#24242c", "#383844"), hood=True,
                        top=R("#1e2440", "#2e3866", "#46528a"), jacket=R("#1e2440", "#2e3866", "#46528a"), pants=R("#9a8460", "#bca47c", "#d6c09a"), shoe=R("#c8c4bc", "#ece8e0", "#fbf9f4")),
}

if __name__ == "__main__":
    poses = [("front", "stand", 0), ("front", "walk", 0.25), ("front", "walk", 0.75), ("back", "stand", 0), ("back", "walk", 0.25), ("front", "sit", 0)]
    S = 6
    sheet = Image.new("RGBA", ((FW + 2) * len(poses) * S, (FH + 2) * len(LOOKS) * S), (205, 140, 85, 255))
    for r, look in enumerate(LOOKS.values()):
        for c, (f, p, ph) in enumerate(poses):
            im = person(look, f, p, ph).resize((FW * S, FH * S), Image.NEAREST)
            sheet.alpha_composite(im, (c * (FW + 2) * S, r * (FH + 2) * S))
    sheet.save(sys.argv[-1])

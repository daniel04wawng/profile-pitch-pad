"""Build every café avatar from the art, in order, then check that every outfit walks all 8 ways.

    python3 art/avatar-rig/skeleton/build_all.py

Runs: the cuts (cut_green.py, cut_women.py), the woman's jacket-off build, the man's haircuts
(hairstyles.py), the hats and glasses (accessories.py), the hair swaps for the diagonal and the
straight-on views (hair_swap.py), then the bake (bake_cafe.py). Then the coverage check: every
base model, in every hairstyle and with everything it can wear, must have all 8 directions:
the 4 diagonals (front, back, mirrored) and the 4 straight-on ones (facing you, facing away,
side on, mirrored). Anything short of that is listed with the art it needs, and the build
fails, so a new hairstyle or accessory can't ship turning diagonal in half the directions.

Add something new (a hairstyle, a hat, a person): give it art for every view in
characters/GENERATE.md's list, add it to the step that makes it, run this.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
SITE = HERE.parents[2] / "public" / "cafe" / "avatars"
STEPS = [
    ["cut_green.py"],
    ["cut_women.py"],
    ["hairstyles.py"],
    ["accessories.py"],
    ["hair_swap.py"],
    ["hair_swap.py", "--cardinal"],
    ["bake_cafe.py"],
]
# which source art each hairstyle comes from, for the "what's missing" list
HAIR_ART = {"pixie": "blue-pixie", "curls": "terracotta-curls", "braid": "plum-braid"}


def coverage() -> list[str]:
    """What isn't drawn all 8 ways, per base model."""
    problems = []
    for entry in json.load(open(SITE / "catalog.json"))["avatars"]:
        m = json.load(open(SITE / entry["manifest"]))
        layers = m.get("layers") or {}
        dirs = set(m["directions"])
        if dirs != {"SE", "SW", "NE", "NW", "S", "N", "E", "W"}:
            problems.append(f"{entry['id']}: directions {sorted(dirs)} (needs all 8)")
            continue
        straight = layers.get("cardinalOnly") or {"hair": [], "wear": []}
        for h in layers.get("hair", []):
            if h not in straight["hair"]:
                art = HAIR_ART.get(h, h)
                problems.append(f"{entry['id']}: hair '{h}' has no straight-on drawings (needs {art} facing you, facing away and side on)")
        for w in layers.get("wear", []):
            if w not in straight["wear"]:
                problems.append(f"{entry['id']}: '{w}' has no straight-on drawings (accessories.py, south/north/east)")
    return problems


def main():
    if "--check" not in sys.argv:
        for step in STEPS:
            print("==", " ".join(step), flush=True)
            subprocess.run([sys.executable, str(HERE / step[0]), *step[1:]], cwd=HERE, check=True)
    problems = coverage()
    if problems:
        print("\nNot all 8 ways yet:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("\nEvery outfit walks all 8 ways.")


if __name__ == "__main__":
    main()

# Women sprite source models

Four characters, four transparent RGBA PNG poses each. Every PNG uses a 256×352 canvas, bottom-center anchor (128,336). Original artwork preserved without resizing or palette changes. Use nearest-neighbor scaling when reducing for the game.

Poses: stand-front, stand-back, sit-front, sit-sip. Front/back are isometric three-quarter views. These are flattened source models, not animation frames or separately extracted body/clothes/hair layers. The seated pose has no chair or table. Standing poses hold a mug, so they are coffee poses rather than neutral arm-down walking rest poses.

Import into your existing rig and calibrate joints for each body. Foot anchor is a packaging alignment aid; seated hips must be aligned to your chair anchor separately. Preserve the same scale between poses, and review limb connections and outfit edges in motion. Do not treat stand-to-sip images as a walk cycle.

## Source generation prompt
Detailed adult non-chibi women café avatars, matching existing warm pixel art and isometric three-quarter camera. Four characters: sage overshirt/dark bob; terracotta tee/natural curls; plum cardigan/dark braid; blue overshirt/auburn pixie. For each character: front standing, back standing, front seated holding cream mug, front seated sipping. Consistent identity, outfit, proportions and palette. Full body, connected limbs, attached cuffs and shoes, transparent background, no chair, floor, shadow or text. Generated using built-in image generation, then separated into source-pose PNGs without resampling.

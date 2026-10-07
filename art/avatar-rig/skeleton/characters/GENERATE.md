# Making a new character for the skeleton rig

A character is generated as a few full-body images that match the first character ("green")
exactly in style, camera and scale. The rig then cuts each image into parts along its own lines,
pins the parts to the shared skeleton, and bakes every animation. Colours (skin, hair, clothes)
are changed afterwards by the materials system, so generate in simple, solid colours.

## What to generate (per character)

| File | Pose | Needed for |
|---|---|---|
| `standing-front.png` | standing, three-quarter front, facing the lower right (south-east) | walk, idle (front) |
| `standing-back.png` | standing, three-quarter back, facing away to the upper right (north-east) | walk, idle (back) |
| `seated-front.png` | seated on an invisible chair, same facing as standing-front | sitting (front) |
| `seated-back.png` | seated on an invisible chair, same facing as standing-back | sitting (back) |
| `seated-back-plate.png` | `seated-back.png` with the mug arm removed and the shirt and trousers behind it filled in | the sip (back) |

Put them in `art/people-src/<name>/` and tell Claude; it writes `cut_<name>.py` (like
`cut_green.py`) and bakes the character into the café.

## Rules every image must follow (so it fits the rig)

- Attach `art/avatar-rig/assets/green/source-standing.png` (front) or
  `art/avatar-rig/authoring/back/standing.png` (back) as the style and camera reference.
- Same camera: elevated orthographic isometric view, 35 degrees, no perspective.
- Same scale and framing: one adult figure, full body, about the same height as the reference.
- Transparent background. No floor, no shadow, no props except the mug.
- Same pose as the reference: right hand holding a cream mug at the chest, left arm relaxed
  at the side with the forearm and hand clearly separate from the body (the free arm swings).
- Legs: trousers or jeans with the two legs clearly separate, sneakers. (A long skirt or dress
  hides the legs, and the walk can't bend them; it needs a different rig, so not for now.)
- Clothes in solid, distinct colours, so the colour changer can find each one: one colour for
  the top layer (overshirt, cardigan or jacket), white or light for the tee, a mid-to-dark
  neutral for the trousers, white for the sneakers.
- Pixel art: crisp pixels, a dark outline, no anti-aliased blur, no text, no watermark.

## Prompts: a woman, as the second character

Standing, front:

> Pixel-art game character, same art style, palette, line weight and shading as the attached
> reference, same elevated orthographic isometric camera (35 degrees), same scale and framing.
> An adult woman in her twenties, three-quarter front view, body turned toward the lower
> right, head turned slightly toward the viewer's right like the reference. Shoulder-length
> wavy dark-brown hair. Olive-green relaxed overshirt worn open, sleeves rolled to the
> elbows, plain white tee, charcoal straight-leg trousers rolled once at the ankle, white
> sneakers. Right hand holds a cream coffee mug at the chest; left arm relaxed at her side,
> hand and forearm clearly separate from the body. Full body, transparent background, no
> floor, no shadow, crisp pixels, dark outline.

Standing, back:

> Same character as the first image, same art style, camera and scale, back three-quarter
> view, facing away toward the upper right (north-east). Same outfit and hair (the back of
> the shoulder-length wavy hair visible). Cream mug in the right hand, held in front of her
> (only the edge of the mug visible); left arm relaxed at her side, clearly separate from the
> body. Full body, transparent background, no floor, no shadow.

Seated, front / back:

> Same character, same camera and scale, seated on an invisible chair (no furniture drawn),
> facing [the lower right / away toward the upper right]. Right hand holding the mug, left
> hand resting on the thigh. Same outfit and hair. Transparent background, no shadow.

Seated back, clean plate:

> The same seated-back image with the right arm and mug removed, and the overshirt and
> trousers behind them filled in naturally. Nothing else changed: same framing, pixels and
> colours.

## Variants: hairstyles and outfits for the same character

Hair and clothes are swapped by part: generate the same character again with only one thing
changed, and the rig takes just that part from it (the new head for a hairstyle, the new torso
and arms for a top). Everything else stays the first image's, so the variant drops onto the
same skeleton. For each variant, generate standing front and standing back (and the two
seated images when sitting is on the rig).

Rules for a variant: attach the character's own standing image as the reference and say
"identical pose, body, face, camera, scale and colours; change only the hair" (or "only the
top"). The less else changes, the cleaner the swap.

Hairstyles (one prompt each, front and back):

> Same character, identical pose, body, face, outfit, camera and scale as the attached image.
> Change only the hair to: [a short buzz cut / a short textured crop with a fringe / hair
> pulled back into a bun on top / shoulder-length wavy hair / long straight hair tied in a low
> ponytail / curly afro]. Same pixel-art style. Transparent background, no shadow.

Just the tee (no overshirt):

> Same character, identical pose, body, face, hair, trousers, shoes, camera and scale as the
> attached image. Remove the olive overshirt: he wears only the plain white tee, short
> sleeves, arms bare from the sleeve down. Right hand still holds the mug at the chest; left
> arm relaxed at the side. Same pixel-art style. Transparent background, no shadow.

## After generating

The images will need a little cleanup (stray pixels, a background halo). Claude handles that
when it cuts them; it checks every part covers the art and that the walk has no gaps.

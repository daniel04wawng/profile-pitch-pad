# Daniel's café: art

**Current pipeline (isometric pixel art, drawn in code):**
- `draw_room.py`: the empty room (floor + two walls) -> `public/cafe/room.png`. Its floor's back corner is the editor's grid origin.
- `draw_iso.py`: furniture and small objects -> `public/cafe/sprites/iso-*.png`.
- Place and arrange everything in the editor at `/cafe?edit` (dev server only).

Older material lives in `archive/` (see its README). The notes below are from the original spec.

# Daniel's café: pixel art kit

Everything the café's art needs to follow so any piece, generated or hand-drawn, drops into the site.

## Files

| File | What it is |
|---|---|
| `cafe-palette.gpl` | Color palette (`.gpl` palette format). Loads in most pixel art and paint apps. |
| `cafe-palette.hex` | Same palette as plain hex codes (for image generators that take a palette). |
| `cafe-palette.png` | Palette as a swatch image. |
| `templates/iso-grid-480x320.png` | Drawing template: the isometric floor grid, café footprint, walls and door gap at real size. Open it in your pixel art app as a bottom layer and draw above it. |
| `templates/layout-guide-4x.png` | Same layout, labeled, enlarged. For reference only. |
| `prompts.md` | Prompts for generating the scene and each object. |

## Rules (so everything matches)

- **Projection:** 2:1 isometric. Floor tiles are 32 x 16 px. Lines step 2 px across for every 1 px down.
- **Scene size:** 480 x 320 px. Shown on the site at 3x or 4x with no smoothing, so never resize art in the editor.
- **Light comes from the upper left** (the window side). Shadows fall to the lower right.
- **Palette only.** Stick to `cafe-palette`. New colors are fine, but add them to the palette so everything stays consistent.
- **Outlines:** a darker shade of the object's own color, not pure black.
- **No anti-aliasing, no soft brushes, no blur.** Every pixel is a solid palette color.
- **Transparent background** on every object sprite.

## What to draw

Sizes are a starting point, measured in pixels at 1x.

| Asset | Size | Notes |
|---|---|---|
| Floor (wood planks) | tiles 32x16 | Or one image for the whole café floor. |
| Back wall (left) | ~200 x 130 | Includes the window. Window glass on its own layer so day/night can swap the sky. |
| Back wall (right) | ~230 x 130 | Menu board can be part of the wall or separate. |
| Front walls (low, cut away) | 2 pieces | Low enough to see inside, with the door gap. |
| Door + frame + awning | ~48 x 80 | 2 frames: closed, open. |
| Counter | ~110 x 60 | |
| Pastry case | ~60 x 40 | One pastry per project on its own layer, so each can be clickable. |
| Espresso machine | ~30 x 30 | |
| Tip jar | ~10 x 14 | |
| Menu board | ~70 x 40 | Blog. |
| Bookshelf | ~48 x 72 | |
| Piano + bench | ~56 x 56 | |
| Record player | ~20 x 14 | 2 frames if you want the record spinning. |
| Window seat / armchair | ~48 x 32 | Where you sit and listen. |
| Table + 2 chairs | ~48 x 40 | |
| Hanging plant (x2) | ~20 x 36 | |
| Flower vase / planter | ~16 x 20, ~40 x 24 | |
| Lamp post | ~16 x 72 | Glow on a separate layer. |
| A-frame sign | ~20 x 28 | Special of the day, on the sidewalk. |
| Avatar | ~16 x 28 per frame | 2 facing directions (mirror for the other 2), walk cycle 4 frames, sit 1 frame, idle 1 frame. A few shirt/hair colors. |

## Layers (in your pixel art app)

Name layers like this and the site can use them directly:

- `base`: the object itself, in daytime light.
- `night`: optional night version, drawn over `base`.
- `glow`: lamp light, window glow, candle light. Blended on top at night.
- `shadow`: the object's floor shadow.

## Exporting

- Keep your editable originals (layered files) in `art/source/`.
- Export PNGs to `art/export/` at 1x, same file name as the source.
- Tell Claude which files changed and they'll be wired into the café.

CAFE PEOPLE SAMPLE PACK
Eight sample visitors with varied ethnic backgrounds, skin tones and hair. These are fictional individual designs, not exhaustive representations of any group.

Each character folder contains the ORIGINAL generated RGBA PNG pose sheet, unchanged. These are sample sheets, not individual extracted PNGs or production-ready animations.

Intended 4-column x 4-row pose map, left to right:
Row 1: walk-front-1, walk-front-2, walk-front-3, walk-front-4
Row 2: walk-back-1, walk-back-2, walk-back-3, walk-back-4
Row 3: stand-front, stand-back, sit-front, sit-sip
Row 4: sit-back, empty, empty, empty

CODING AGENT IMPORT:
Preserve source alpha throughout processing. Never convert to RGB and then guess a background colour. Some sheets include semitransparent glow and edge artifacts that need cleanup.
Extract each pose after inspecting actual sprite bounds. Do not assume the generated grid is pixel-perfect. Keep original sheets intact.
These generations generally face screen-right for front views; verify directions and mirror when needed.
Walking poses have limited variation and do not reliably form a complete alternating gait. Clean up or redraw walk frames as needed, keeping character identity.
Align standing frames at the feet, seated frames at the seat contact point. Normalize scale without stretching. Aim for about 58px standing / 44px seated as a starting point, then adjust to furniture.
Use nearest-neighbour scaling and image-rendering: pixelated. Place chair fronts and tables above sprites as appropriate.
Do not recreate avatars using CSS, SVG or emoji. Check character consistency and animation before multiplayer integration.

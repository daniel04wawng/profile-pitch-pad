# Daniel's Café avatar rig and website importer

This package contains six actions in four isometric directions, with the previously approved front frames and newly reviewed back frames, a browser ES module, a TypeScript declaration, a configurable walk-authoring rig, and a canvas integration example. Runtime has no dependencies. Approved frames remain the source of truth.

## Import into your website

Copy `assets/green/` to your site's public folder at `/assets/people/green/`. Copy `src/cafe-avatar.mjs` into your source folder (and its declaration if using TypeScript). All URLs inside the manifest resolve relative to the manifest URL, so folders can move together.

```js
import { loadCafeAvatar } from './cafe-avatar.mjs';

const avatar = await loadCafeAvatar('/assets/people/green/manifest.json');
const position = { x: 200, y: 160 };
avatar.setDirection('NE'); // SE, SW, NE, NW
avatar.play('walk');

// Call once per game tick; dtMs is elapsed milliseconds.
const motion = avatar.update(dtMs);
position.x += motion.dx;
position.y += motion.dy;
avatar.draw(ctx, { ...position });
```

Render with nearest-neighbor sampling. `x/y` represent the character's ground anchor, not its upper-left corner. Sprite canvas is64×70, anchor32×64.5. At draw scale2, multiply root motion by2 as well. If your canvas camera scales the whole world, keep root motion in world units and let the camera scale it.

For navigation, either use the supplied root-motion delta or your game's velocity, never both. The supplied walk curve follows its stance-foot travel rather than guessing a constant speed. It moves approximately19.14 pixels right and10.98 down per1-second cycle at native game size. Validate travel against your café's floor and navigation model.

Use `setDirection('SE'|'SW'|'NE'|'NW')` and `play('walk'|'idle'|'sit-down'|'stand-up'|'coffee-sip'|'seated-idle')`. Front and back have separate sheets. Left views are mirrored, which swaps handedness. Direction changes preserve elapsed time and walk phase; they switch the view instantly, rather than adding a separately drawn turning motion. Root-motion x and attachment points mirror automatically. Avoid overriding `flipX` when using directional movement. The older `setAction()` API remains available for exact clip names; use `play()` for direction-aware actions.

## States and furniture

`setAction(name)` resets time only when the action changes. Use `{restart:true}` to replay the same action. Use the logical names with `play()` above; the manifest lists all twelve underlying clip names.

Sitting and standing-up play once and hold the last frame. `update()` returns `justCompleted` once. On sit completion, call `play('seated-idle')`; on stand-up completion, call `play('idle')`. Those rest endpoints are pixel-exact. Sip can return to seated idle on its rest frame. Walk-to-idle switching requires your game to choose a stopping frame/position; this package does not invent a stopping animation.

Draw chairs/tables separately and use normal scene depth sorting. `attachmentPoints.chairSeat` is a local sprite point for chair calibration, not an automatic furniture placement rule. Test it against your actual chair art. The example uses a ground marker and floor grid.

## Try locally

From this folder, run `python3 -m http.server 8080`, then open `http://localhost:8080/example.html`. Serve over HTTP; ES-module loading through `file://` is unreliable. The canvas example demonstrates actual root movement and one-shot state changes.

## Future character authoring

`authoring/green.rig.json` separates bone rest positions, camera angle, gait amplitudes and layer boundaries from the walk renderer. It references the standing pose at `assets/green/source-standing.png`.

Install packages listed in `authoring/requirements.txt`, then:

```sh
python3 authoring/bake-walk.py --rig authoring/green.rig.json --out output/new-walk
```

The default configuration reproduces all eight approved walk PNGs exactly. For a new character, supply a transparent standing image at the same camera/proportions; copy the configuration and calibrate hip/knee/ankle points, cuffs, sleeve/hand masks and source path. Cloth-color thresholds and a few mask edge details are specific to this outfit; inspect/recalibrate for other wardrobes. No automatic arbitrary-image rigging is claimed.

Sitting and sipping currently use the approved baked sheets, not the walk bones. New seated artwork needs its own matching poses and arm-layer calibration before importing. Add characters by preserving the manifest structure and replacing their sheets; the runtime requires no character-specific changes.

## Verification

Run `node test.mjs` for runtime timing, root motion, loader paths, anchors and completion behavior. The authoring rig was checked against the approved eight walk PNGs pixel for pixel. The code has not been installed into Daniel's actual website repository because that repository is not present in this workspace.

## New back-view authoring and preview

Open `Four_Direction_Preview.html` directly for a self-contained player for every action and direction. `Four_Direction_Walk.gif` and `All_Four_Direction_Actions.gif` are portable previews. `frames/SE`, `SW`, `NE`, and `NW` contain separate 256×280 PNGs for each pose. The game sheets remain 64×70 per frame.

`authoring/back/back.rig.json` holds calibrated back-view joints and gait settings. Regenerate using `python3 authoring/back/bake-back.py`, `python3 authoring/back/seated-actions.py`, and `python3 authoring/back/transitions.py`. These write PNGs beside the scripts. Rebuild sheets from the outputs before importing. Shoe and arm masks are outfit-specific, so calibration is required for future characters. Front/back rest poses are generated separately, so texture details can differ slightly. Seated/sip use their own arm calibration; sit/stand use matched-landmark interpolation between drawn poses. This is a view-specific 2D rig, not a rotatable 3D model.

Back frames were inspected in contact sheets and checked for connected limbs, grounded idle feet, exact rest endpoints, dimensions and timing. Runtime tests cover all four direction mappings, movement signs, phase preservation and all twelve sheets. Actual website integration and browser playback remain to be checked in your website repository.

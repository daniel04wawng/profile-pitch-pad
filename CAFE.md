# Daniel's café: how to work on it

The site is the café at `/` (storefront, then walk in) and `/cafe`. The old portfolio is at
`/classic`. Branch `cafe-3d` is where work happens; `main` is live (Vercel deploys it on every
push).

## Run it

```bash
npm install
npm run dev          # http://localhost:8080
```

Server-side keys for the optional features go in `.env.local` (`vercel env pull .env.local`
restores them). Never commit them.

## Change the content (projects, bakes, menu, music, contact)

1. Open `localhost:8080/cafe` and walk up to the thing (laptop, pastry case, menu board, piano,
   register, bookshelf).
2. Press **✎ edit** on its screen. Click any outlined text and type; **+ add** / **✕** add and
   remove items; **+ photos / videos** adds media; **+ link** adds links.
3. Press **✓ done**. It's already saved to `public/cafe/screens.json` (media in
   `public/cafe/media/`).
4. Commit and push to `main` to put it live.

The edit button only exists on the dev server, never on the live site.

## Move furniture

`localhost:8080/cafe?edit` is the room editor (saves to `public/cafe/layout.json`). `P` tries the
room as a visitor. Each asset's collision is set in its panel.

## Avatars

Avatars come from the skeleton rig in `art/avatar-rig/skeleton/` (Python 3, numpy, Pillow,
scipy). Four base models (man and woman, jacket on and off), nine hairstyles, a beanie and
glasses, eight directions. After changing the rig or the art:

```bash
cd art/avatar-rig/skeleton
python3 cut_women.py            # cut the characters into parts (cut_green.py for the man's diagonals)
python3 hair_swap.py            # hairstyles and things to wear, per model
python3 bake_cafe.py            # bake the café's avatars into public/cafe/avatars/
python3 viewer.py               # public/rig-viewer.html, to look at them (not committed)
```

New art: see `art/avatar-rig/skeleton/characters/GENERATE.md` for the prompts and rules.

## Optional features (each off until switched on)

| Feature | Turn it on | Notes |
|---|---|---|
| Make a tune at the piano | Create the Hugging Face Space from `music-space/`, then on Vercel set `HF_SPACE` (and optionally `HF_TOKEN`) and `VITE_MUSIC_ON=1` | Free on ZeroGPU once the HF account is 30 days old |
| Generate assets in the editor | Free Cloudflare account (Workers Free plan), then `CF_ACCOUNT_ID` and `CF_AI_TOKEN` on Vercel | 10,000 free units a day, stops instead of billing on the free plan |
| The café builder (build your own, publish, share) | A second Vercel project from this repo with `VITE_BUILD_ON=1`; run `supabase/cafes.sql` and turn on anonymous sign-ins in Supabase | Its own site: front page `src/pages/Builder.tsx`. Take a café down: set `hidden` on its row in the `cafes` table; reports land in `cafe_reports` |

## Where things live

- `src/components/cafe/engine/`: the café (room, avatars, screens, multiplayer, editor)
- `public/cafe/`: the room's data and art (layout, screens, sprites, avatars, media)
- `api/`: small server functions (music, asset generator)
- `supabase/`: database setup (notes board, visitor cafés)
- `art/`: scripts that draw and cut the art

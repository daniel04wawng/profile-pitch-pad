// Generate a café asset from a few words: an isometric pixel-art object on a plain background,
// from FLUX.2 [klein] on Cloudflare Workers AI. The browser then makes it real pixel art
// (engine/pixelize.ts: background off, scaled down, a small palette, a dark outline).
//
//   POST /api/asset  {words}  ->  {image: "data:image/...;base64,..."}
//
// Needs CF_ACCOUNT_ID and CF_AI_TOKEN (a Cloudflare API token with Workers AI read/edit), set on
// Vercel as server-side variables. Without them the editor says generating isn't set up yet.
import { clientIp, json, limited, words } from "./_lib";

const MODEL = "@cf/black-forest-labs/flux-2-klein-4b";

const STYLE =
  "isometric pixel art game asset, a single object seen from above at a 2:1 isometric angle, " +
  "cozy warm cafe style, warm palette, clean dark outline, centered, the whole object in frame, " +
  "on a plain flat white background, no floor, no shadow, no text, no border";

export async function POST(req: Request) {
  const account = process.env.CF_ACCOUNT_ID;
  const token = process.env.CF_AI_TOKEN;
  if (!account || !token) return json({ error: "Generating assets isn't set up yet." }, 503);
  if (limited(`asset:${clientIp(req)}`, 8, 10 * 60_000)) return json({ error: "That's a lot of assets. Try again in a few minutes." }, 429);
  let body: { words?: unknown } = {};
  try {
    body = await req.json();
  } catch {
    return json({ error: "bad request" }, 400);
  }
  const what = words(body.words, 100);
  if (!what) return json({ error: "Say what to make." }, 400);
  const form = new FormData();
  form.append("prompt", `${what}, ${STYLE}`);
  form.append("width", "512");
  form.append("height", "512");
  const r = await fetch(`https://api.cloudflare.com/client/v4/accounts/${encodeURIComponent(account)}/ai/run/${MODEL}`, {
    method: "POST",
    headers: { authorization: `Bearer ${token}` },
    body: form,
  });
  if (!r.ok) return json({ error: "Couldn't make that one." }, 502);
  const out = (await r.json()) as { result?: { image?: string }; image?: string };
  const b64 = out.result?.image ?? out.image;
  if (!b64 || !/^[A-Za-z0-9+/=]+$/.test(b64)) return json({ error: "Couldn't make that one." }, 502);
  const type = b64.startsWith("iVBOR") ? "image/png" : b64.startsWith("/9j/") ? "image/jpeg" : "image/webp";
  return json({ image: `data:${type};base64,${b64}` });
}

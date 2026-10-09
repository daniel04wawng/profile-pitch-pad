// Make a tune at the piano: a short instrumental from ACE-Step (fal.ai), in one of the café's
// styles plus a few words of the visitor's own.
//
//   POST /api/music  {style, words?}  ->  {id}      (queued)
//   GET  /api/music?id=...            ->  {status: "waiting" | "making" | "done", url?}
//
// Needs FAL_KEY (fal.ai > API keys), set on Vercel as a server-side variable (never VITE_*).
// Without it the piano says music making isn't set up yet.
import { clientIp, json, limited, words } from "./_lib";

const MODEL = "fal-ai/ace-step";
const QUEUE = `https://queue.fal.run/${MODEL}`;
const SECONDS = 30;

export const STYLES: Record<string, string> = {
  lofi: "lo-fi hip hop, mellow, dusty vinyl crackle, rhodes piano, soft boom bap drums, chill, cozy",
  jazz: "cafe jazz, warm piano trio, upright bass, brushed drums, smooth, relaxed",
  bossa: "bossa nova, nylon string guitar, soft shaker, warm, relaxed, cafe",
  ambient: "ambient, soft pads, gentle felt piano, calm, slow, dreamy",
  piano: "solo piano, gentle, cozy, slow, intimate, cafe",
};

const key = () => process.env.FAL_KEY;
const auth = () => ({ authorization: `Key ${key()}`, "content-type": "application/json" });

export async function POST(req: Request) {
  if (!key()) return json({ error: "Music making isn't set up yet." }, 503);
  if (limited(`music:${clientIp(req)}`, 4, 10 * 60_000)) return json({ error: "That's a lot of tunes. Try again in a few minutes." }, 429);
  let body: { style?: unknown; words?: unknown } = {};
  try {
    body = await req.json();
  } catch {
    return json({ error: "bad request" }, 400);
  }
  const style = typeof body.style === "string" && STYLES[body.style] ? body.style : "lofi";
  const extra = words(body.words, 80);
  const tags = [STYLES[style], extra, "instrumental, no vocals"].filter(Boolean).join(", ");
  const r = await fetch(QUEUE, {
    method: "POST",
    headers: auth(),
    body: JSON.stringify({ tags, lyrics: "[instrumental]", duration: SECONDS }),
  });
  if (!r.ok) return json({ error: "The piano couldn't start that one." }, 502);
  const { request_id } = (await r.json()) as { request_id?: string };
  return request_id ? json({ id: request_id }) : json({ error: "The piano couldn't start that one." }, 502);
}

export async function GET(req: Request) {
  if (!key()) return json({ error: "Music making isn't set up yet." }, 503);
  const id = new URL(req.url).searchParams.get("id") ?? "";
  if (!/^[a-z0-9-]{8,64}$/i.test(id)) return json({ error: "bad request" }, 400);
  const s = await fetch(`${QUEUE}/requests/${id}/status`, { headers: auth() });
  if (!s.ok) return json({ error: "lost track of that tune" }, 502);
  const { status } = (await s.json()) as { status?: string };
  if (status === "IN_QUEUE") return json({ status: "waiting" });
  if (status !== "COMPLETED") return json({ status: "making" });
  const r = await fetch(`${QUEUE}/requests/${id}/response`, { headers: auth() });
  if (!r.ok) return json({ error: "that tune didn't come out" }, 502);
  const out = (await r.json()) as { audio?: { url?: string } };
  const url = out.audio?.url;
  return url && /^https:\/\//.test(url) ? json({ status: "done", url }) : json({ error: "that tune didn't come out" }, 502);
}

// Make a tune at the piano: a short instrumental from ACE-Step, running on Daniel's own Hugging
// Face Space (music-space/, free ZeroGPU), in one of the café's styles plus a few words of the
// visitor's own.
//
//   POST /api/music  {style, words?}  ->  {id}      (queued on the Space)
//   GET  /api/music?id=...            ->  {status: "making" | "done", url?}
//
// Needs HF_SPACE ("user/space-name"); HF_TOKEN (a free read token) is optional and makes the
// calls count against that account's daily GPU minutes instead of the anonymous ones. Both are
// server-side variables (never VITE_*). Without HF_SPACE the piano says it isn't set up yet.
//
// The Space's Gradio API: POST /gradio_api/call/generate {data: [style, words]} -> {event_id};
// GET /gradio_api/call/generate/<event_id> streams server-sent events: heartbeats while it
// works, then "complete" with [{url, ...}] (a temporary file) or "error".
import { clientIp, json, limited, words } from "./_lib";

const STYLES = new Set(["lofi", "jazz", "bossa", "ambient", "piano"]);

const space = () => process.env.HF_SPACE;
const base = () => `https://${space()!.replace("/", "-").replace(/[._]/g, "-").toLowerCase()}.hf.space/gradio_api/call/generate`;
const headers = (): Record<string, string> => ({
  "content-type": "application/json",
  ...(process.env.HF_TOKEN ? { authorization: `Bearer ${process.env.HF_TOKEN}` } : {}),
});

export async function POST(req: Request) {
  if (!space()) return json({ error: "Music making isn't set up yet." }, 503);
  if (limited(`music:${clientIp(req)}`, 4, 10 * 60_000)) return json({ error: "That's a lot of tunes. Try again in a few minutes." }, 429);
  let body: { style?: unknown; words?: unknown } = {};
  try {
    body = await req.json();
  } catch {
    return json({ error: "bad request" }, 400);
  }
  const style = typeof body.style === "string" && STYLES.has(body.style) ? body.style : "lofi";
  const r = await fetch(base(), { method: "POST", headers: headers(), body: JSON.stringify({ data: [style, words(body.words, 80)] }) });
  if (!r.ok) return json({ error: "The piano is asleep. Try again in a minute." }, 502);
  const { event_id } = (await r.json()) as { event_id?: string };
  return event_id ? json({ id: event_id }) : json({ error: "The piano couldn't start that one." }, 502);
}

// Poll: read the event stream for up to ~8 s; if it hasn't finished, say "making" and the page
// asks again (a serverless function can't hold the stream open for the whole tune).
export async function GET(req: Request) {
  if (!space()) return json({ error: "Music making isn't set up yet." }, 503);
  const id = new URL(req.url).searchParams.get("id") ?? "";
  if (!/^[a-z0-9-]{6,64}$/i.test(id)) return json({ error: "bad request" }, 400);
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 8000);
  try {
    const r = await fetch(`${base()}/${id}`, { headers: headers(), signal: ctl.signal });
    if (!r.ok || !r.body) return json({ error: "lost track of that tune" }, 502);
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    let event = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:") && event === "complete") {
          const out = JSON.parse(line.slice(5)) as { url?: string }[];
          const url = out?.[0]?.url;
          ctl.abort();
          return url && /^https:\/\//.test(url) ? json({ status: "done", url }) : json({ error: "that tune didn't come out" }, 502);
        } else if (line.startsWith("data:") && event === "error") {
          ctl.abort();
          return json({ error: "The piano's out of time for today. Try again tomorrow." }, 502);
        }
      }
    }
    return json({ status: "making" });
  } catch {
    return json({ status: "making" }); // the 8 s ran out mid-tune: still going
  } finally {
    clearTimeout(timer);
  }
}

// The radio's GPU worker protocol (a Kaggle notebook running Daniel's fine-tuned ACE-Step; see
// ~/acestep-personalize/personalize/remote/dj_worker.py). Bearer RADIO_WORKER_TOKEN.
//
//   GET  /api/radio-worker  ->  {job: {id, caption, seed, duration} | null}
//   POST /api/radio-worker?claim=<id>&duration=<s>&title=<t>[&caption=..&pinned=1&history=1]
//        body: the song as audio/mpeg (Vercel caps bodies at 4.5 MB; 2 min at 128 kbps ≈ 2 MB)
//
// A job is handed out whenever fewer than 5 songs are queued, or a listener request is waiting.
import { put } from "@vercel/blob";
import { json } from "./_lib";
import { addSong, advance, claimJob } from "./_radio-station";
import { configured, isWorker, withState } from "./_radio-store";

export async function GET(req: Request) {
  if (!configured()) return json({ error: "The radio isn't set up yet." }, 503);
  if (!isWorker(req)) return json({ error: "unauthorized" }, 401);
  const now = Date.now();
  const job = await withState((s) => {
    advance(s, now);
    return claimJob(s, now);
  });
  return json({ job });
}

export async function POST(req: Request) {
  if (!configured()) return json({ error: "The radio isn't set up yet." }, 503);
  if (!isWorker(req)) return json({ error: "unauthorized" }, 401);
  const q = new URL(req.url).searchParams;
  const claim = q.get("claim") ?? "";
  const duration = Number(q.get("duration"));
  if (!/^[\w.~-]{1,80}$/.test(claim) || !(duration > 0 && duration < 900))
    return json({ error: "claim and duration required" }, 400);
  const body = await req.arrayBuffer();
  if (body.byteLength < 1000) return json({ error: "empty audio" }, 400);
  const blob = await put(`radio/${claim}.mp3`, body, {
    access: "public", contentType: "audio/mpeg", addRandomSuffix: true,
  });
  const song = {
    id: claim, url: blob.url, duration,
    title: (q.get("title") || "untitled").slice(0, 80),
    caption: (q.get("caption") || "").slice(0, 300),
    createdAt: Date.now(),
  };
  await withState((s) => addSong(s, claim, song, { pinned: q.get("pinned") === "1", toHistory: q.get("history") === "1" }));
  return json({ ok: true, song });
}

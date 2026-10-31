// A listener skips the song playing now. It's one shared station, so it skips for everyone;
// songId must be the song they hear, so simultaneous presses only skip once.
//
//   POST /api/radio-skip  {songId}  ->  {skipped} | {error}
import { del } from "@vercel/blob";
import { clientIp, json } from "./_lib";
import { skip } from "./_radio-station";
import { configured, db, withState } from "./_radio-store";

const PER_VISITOR_SECONDS = 15;

export async function POST(req: Request) {
  if (!configured()) return json({ error: "The radio isn't set up yet." }, 503);
  let body: { songId?: unknown } = {};
  try {
    body = await req.json();
  } catch {
    // fall through: an unknown song skips nothing
  }
  if (!(await db().set(`radio:skip:${clientIp(req)}`, 1, { nx: true, ex: PER_VISITOR_SECONDS })))
    return json({ error: "Easy, one skip every 15 seconds." }, 429);
  const { skipped, evicted } = await withState((s) => skip(s, body.songId, Date.now()));
  if (evicted.length) await del(evicted.map((e) => e.url)).catch(() => {});
  return json({ skipped });
}

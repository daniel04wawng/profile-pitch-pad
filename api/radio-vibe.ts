// Set the radio's house style, used for every song nobody requested. Bearer RADIO_ADMIN_KEY.
//
//   POST /api/radio-vibe  {vibe}  ->  {ok, vibe}
import { json, words } from "./_lib";
import { configured, isAdmin, withState } from "./_radio-store";

export async function POST(req: Request) {
  if (!configured()) return json({ error: "The radio isn't set up yet." }, 503);
  if (!isAdmin(req)) return json({ error: "unauthorized" }, 401);
  let body: { vibe?: unknown } = {};
  try {
    body = await req.json();
  } catch {
    // fall through
  }
  const vibe = words(body.vibe, 200);
  if (!vibe) return json({ error: "vibe required" }, 400);
  await withState((s) => {
    s.vibe = vibe;
  });
  return json({ ok: true, vibe });
}

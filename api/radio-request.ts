// A listener asks the radio for a song: their words become the next song's prompt (always
// instrumental, always in Daniel's style). Only the requester's browser shows their words.
//
//   POST /api/radio-request  {prompt}  ->  {id, position} | {error}
import { clientIp, json, words } from "./_lib";
import { addRequest } from "./_radio-station";
import { configured, db, withState } from "./_radio-store";

const PER_VISITOR_SECONDS = 600;

export async function POST(req: Request) {
  if (!configured()) return json({ error: "The radio isn't set up yet." }, 503);
  let body: { prompt?: unknown } = {};
  try {
    body = await req.json();
  } catch {
    // fall through to the empty-prompt error
  }
  const prompt = words(body.prompt, 160);
  if (prompt.length < 3) return json({ error: "Describe the song in a few words." }, 400);
  // Shared across serverless instances (unlike _lib's in-memory limit): one request per 10 min.
  const key = `radio:req:${clientIp(req)}`;
  if (!(await db().set(key, 1, { nx: true, ex: PER_VISITOR_SECONDS })))
    return json({ error: "One request every 10 minutes. Hang tight!" }, 429);
  const out = await withState((s) => addRequest(s, prompt, Date.now()));
  if (out.error) {
    await db().del(key); // a turned-away request doesn't use up their turn
    return json(out, 400);
  }
  return json(out);
}

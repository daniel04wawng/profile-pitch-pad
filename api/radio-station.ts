// The radio (/radio): what's playing now, how far in, and what's next.
//
//   GET /api/radio-station  ->  {current, offset, upNext, generatorOnline, pendingRequests, ...}
//
// Every call counts as someone being on the page, which keeps the station clock running; with
// nobody here it freezes, so the queue is still there for the next visitor.
import { del } from "@vercel/blob";
import { json } from "./_lib";
import { publicView, touch } from "./_radio-station";
import { configured, withState } from "./_radio-store";

export async function GET() {
  if (!configured()) return json({ error: "The radio isn't set up yet." }, 503);
  const now = Date.now();
  const { view, evicted } = await withState((s) => ({ evicted: touch(s, now), view: publicView(s, now) }));
  if (evicted.length) await del(evicted.map((e) => e.url)).catch(() => {});
  return json(view);
}

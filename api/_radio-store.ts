// Where the radio keeps its state: one Upstash Redis key (Vercel Marketplace integration, free
// tier), with a short lock around each read-modify-write. Song files live in Vercel Blob.
//
// Needs KV_REST_API_URL + KV_REST_API_TOKEN (or UPSTASH_REDIS_REST_URL/_TOKEN, depending on how
// the integration names them), BLOB_READ_WRITE_TOKEN, RADIO_WORKER_TOKEN (shared with the GPU
// worker) and RADIO_ADMIN_KEY (for /api/radio-vibe). Server-side variables only.
import { Redis } from "@upstash/redis";
import { emptyState, type State } from "./_radio-station";

const KEY = "radio:station:v1";
const LOCK = "radio:station:v1:lock";

let redis: Redis | undefined;
export const configured = () =>
  Boolean((process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL) && process.env.BLOB_READ_WRITE_TOKEN);

export function db() {
  redis ??= new Redis({
    url: (process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL)!,
    token: (process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN)!,
  });
  return redis;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Run fn on the current state under the lock, then save it.
export async function withState<T>(fn: (s: State) => T | Promise<T>): Promise<T> {
  const token = Math.random().toString(36).slice(2);
  for (let i = 0; ; i++) {
    if (await db().set(LOCK, token, { nx: true, px: 5000 })) break;
    if (i === 39) throw new Error("station busy");
    await sleep(100);
  }
  try {
    const state: State = { ...emptyState(), ...((await db().get<State>(KEY)) ?? {}) };
    const out = await fn(state);
    await db().set(KEY, state);
    return out;
  } finally {
    if ((await db().get(LOCK)) === token) await db().del(LOCK);
  }
}

const bearer = (req: Request, want: string | undefined) =>
  Boolean(want) && req.headers.get("authorization") === `Bearer ${want}`;
export const isWorker = (req: Request) => bearer(req, process.env.RADIO_WORKER_TOKEN);
export const isAdmin = (req: Request) => bearer(req, process.env.RADIO_ADMIN_KEY);

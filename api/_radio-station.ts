// The radio's station logic: one shared queue of songs from Daniel's fine-tuned ACE-Step model,
// advanced lazily on every request. Pure (no I/O) so it can be unit-tested
// (tests/radio-station.test.ts); the radio-* routes load and save the state.

export type Song = {
  id: string; url: string; title: string; duration: number;
  caption?: string; createdAt?: number; pinned?: boolean; replay?: boolean; requestId?: string;
};
export type Request_ = { id: string; prompt: string; at: number };
export type Claim = { expiresAt: number; request?: Request_ };
export type State = {
  queue: Song[]; current: Song | null; startedAt: number; pausedAt: number | null;
  history: Song[]; lastSeen: number; workerSeen: number;
  claims: Record<string, Claim>; requests: Request_[]; vibe: string;
};

export const QUEUE_TARGET = 5; // upcoming songs kept ready (not counting the one playing)
export const LISTENER_TTL_MS = 45_000; // a listener counts as present this long after a request
export const CLAIM_TTL_MS = 15 * 60_000; // a GPU job not uploaded in time is given up
export const HISTORY_MAX = 20; // played songs kept for replay when the queue runs dry
export const REQUESTS_MAX = 10; // listener requests waiting for a GPU

export function emptyState(): State {
  return {
    queue: [], // upcoming songs, oldest first
    current: null, // song playing now
    startedAt: 0, // ms when `current` started, in station time
    pausedAt: null, // ms the station froze (nobody listening); null = running
    history: [], // recently played, oldest first; replayed when the queue is empty
    lastSeen: 0, // ms of the last listener request
    workerSeen: 0, // ms of the last GPU worker request
    claims: {}, // claimId -> {expiresAt, request?}
    requests: [], // listener prompts waiting for a GPU, oldest first: {id, prompt, at}
    vibe: "slow lo-fi jazz ballad, soft piano, light drums, warm and melancholic",
  };
}

export function listenersActive(s: State, now: number) {
  return now - s.lastSeen < LISTENER_TTL_MS;
}

// Freeze the clock when the last listener left; resume it when one comes back.
// Station time stands still while frozen, so the queue is still there on return.
function syncPause(s: State, now: number) {
  if (s.pausedAt === null && !listenersActive(s, now) && s.lastSeen > 0) {
    s.pausedAt = Math.min(now, s.lastSeen + LISTENER_TTL_MS);
  }
}

function nextSong(s: State): Song | null {
  if (s.queue.length) return s.queue.shift()!;
  if (!s.history.length) return null;
  const replay = s.history.shift()!; // oldest played song comes round again
  return { ...replay, replay: true };
}

function finish(s: State, song: Song) {
  const { replay, ...clean } = song;
  s.history.push(clean);
  const evicted: Song[] = [];
  while (s.history.length > HISTORY_MAX) {
    const old = s.history.shift()!;
    if (!old.pinned) evicted.push(old);
    else s.history.push(old); // pinned seed songs never leave
    if (s.history.every((h) => h.pinned)) break;
  }
  return evicted;
}

// Advance the station to `now`. Returns songs evicted from history (their files can be deleted).
export function advance(s: State, now: number): Song[] {
  syncPause(s, now);
  const t = s.pausedAt ?? now;
  const evicted: Song[] = [];
  if (!s.current) {
    s.current = nextSong(s);
    s.startedAt = t;
  }
  let guard = 0;
  while (s.current && t >= s.startedAt + s.current.duration * 1000 && guard++ < 500) {
    const end = s.startedAt + s.current.duration * 1000;
    evicted.push(...finish(s, s.current));
    s.current = nextSong(s);
    s.startedAt = end;
  }
  return evicted;
}

// A listener request: mark presence (resuming a frozen clock), then advance.
export function touch(s: State, now: number) {
  if (s.pausedAt !== null) {
    s.startedAt += now - s.pausedAt; // shift the clock by the time nobody was here
    s.pausedAt = null;
  }
  s.lastSeen = now;
  return advance(s, now);
}

export function publicView(s: State, now: number) {
  const t = s.pausedAt ?? now;
  return {
    now,
    current: s.current,
    offset: s.current ? Math.max(0, (t - s.startedAt) / 1000) : 0,
    upNext: s.queue.slice(0, QUEUE_TARGET).map(({ caption, ...q }) => (q.requestId ? q : { ...q, caption })),
    pendingRequests: s.requests.map((r) => r.id).concat(
      Object.values(s.claims).flatMap((c) => (c.request ? [c.request.id] : []))),
    vibe: s.vibe,
    generatorOnline: now - s.workerSeen < 2 * 60_000,
    replaying: Boolean(s.current?.replay),
  };
}

const VARIATIONS = [
  "rainy night", "late night city", "soft Rhodes chords", "brushed drums", "warm upright bass",
  "gentle tenor saxophone", "vinyl crackle", "nostalgic", "dreamy", "slow and intimate",
  "mellow electric guitar", "quiet coffee shop", "golden hour", "after midnight",
];

// GPU worker asks for a job. Hands one out while the queue (plus jobs already in
// flight) is short of the target, or a listener request is waiting.
export function claimJob(s: State, now: number, rand = Math.random) {
  s.workerSeen = now;
  for (const [id, c] of Object.entries(s.claims)) {
    if (c.expiresAt < now) {
      if (c.request) s.requests.unshift(c.request); // a lost request goes back to the front
      delete s.claims[id];
    }
  }
  const inFlight = Object.keys(s.claims).length;
  const request = s.requests[0];
  // Top the queue up to the target whether or not anyone is listening: the
  // station is frozen while nobody is here, so a full queue simply waits for
  // the next visitor and the GPU goes idle. Requests are made even past the
  // target, since someone is waiting for them.
  if (!request && s.queue.length + inFlight >= QUEUE_TARGET) return null;
  if (request) s.requests.shift();
  let id = `${now.toString(36)}-${Math.floor(rand() * 1e9).toString(36)}`;
  for (let n = 2; s.claims[id]; n++) id = `${id.split("~")[0]}~${n}`; // same ms + same random draw
  const extra = VARIATIONS[Math.floor(rand() * VARIATIONS.length)];
  s.claims[id] = { expiresAt: now + CLAIM_TTL_MS, ...(request ? { request } : {}) };
  return {
    id,
    caption: request ? request.prompt : `${s.vibe}, ${extra}`,
    ...(request ? { requestId: request.id } : {}),
    seed: Math.floor(rand() * 2 ** 31),
    duration: 120,
  };
}

export function addSong(s: State, claimId: string, song: Song, { pinned = false, toHistory = false } = {}) {
  const request = s.claims[claimId]?.request;
  delete s.claims[claimId];
  const entry: Song = { ...song, ...(pinned ? { pinned: true } : {}) };
  if (request) {
    // Plays right after the current song, behind any earlier requests already queued.
    entry.requestId = request.id;
    entry.title = "listener request";
    entry.caption = "";
    const firstNormal = s.queue.findIndex((q) => !q.requestId);
    s.queue.splice(firstNormal === -1 ? s.queue.length : firstNormal, 0, entry);
  } else if (toHistory) s.history.push(entry);
  else s.queue.push(entry);
}

// A listener asks for a song. Returns {id, position} or {error}.
export function addRequest(s: State, prompt: unknown, now: number, rand = Math.random): { id?: string; position?: number; error?: string } {
  const clean = String(prompt || "").replace(/\s+/g, " ").trim().slice(0, 160);
  if (clean.length < 3) return { error: "describe the song in a few words" };
  if (s.requests.length >= REQUESTS_MAX) return { error: "lots of requests right now, try again in a few minutes" };
  const id = `r${now.toString(36)}${Math.floor(rand() * 1e6).toString(36)}`;
  s.requests.push({ id, prompt: clean, at: now });
  return { id, position: s.requests.length };
}

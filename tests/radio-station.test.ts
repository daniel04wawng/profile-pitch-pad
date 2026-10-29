import assert from "node:assert/strict";
import test from "node:test";
import {
  addRequest, addSong, advance, claimJob, emptyState, LISTENER_TTL_MS, publicView, QUEUE_TARGET, touch,
} from "../api/_radio-station.ts";

const song = (id, duration = 100) => ({ id, url: `u/${id}`, title: id, duration });
const MIN = 60_000;

function stationWith(n, t0 = 1_000_000) {
  const s = emptyState();
  for (let i = 0; i < n; i++) addSong(s, `c${i}`, song(`s${i}`));
  touch(s, t0);
  return s;
}

test("first listener starts the first song at offset 0", () => {
  const s = stationWith(3);
  const v = publicView(s, 1_000_000);
  assert.equal(v.current.id, "s0");
  assert.equal(v.offset, 0);
  assert.deepEqual(v.upNext.map((x) => x.id), ["s1", "s2"]);
});

test("songs advance with wall time while someone listens", () => {
  const s = stationWith(3);
  for (let t = 1_000_000; t <= 1_000_000 + 150_000; t += 20_000) touch(s, t); // heartbeats every 20 s
  const v = publicView(s, 1_150_000);
  assert.equal(v.current.id, "s1");
  assert.equal(Math.round(v.offset), 50);
});

test("station freezes when everyone leaves and resumes where it was", () => {
  const s = stationWith(5);
  touch(s, 1_030_000); // listening 30 s into s0, then leave
  const later = 1_030_000 + 3 * 60 * MIN; // 3 hours later
  advance(s, later); // e.g. the worker polling while nobody is here
  assert.equal(s.current.id, "s0", "nothing plays while nobody is listening");
  touch(s, later);
  const v = publicView(s, later);
  assert.equal(v.current.id, "s0");
  // froze at lastSeen + TTL, so up to 45 s of "listening" counted after the last heartbeat
  assert.ok(v.offset >= 30 && v.offset <= 30 + LISTENER_TTL_MS / 1000);
  assert.equal(v.upNext.length, 4, "the queue is still there for the returning visitor");
});

test("worker fills the queue to 5 and then stops, listeners or not", () => {
  const s = stationWith(2);
  const jobs = [];
  for (let i = 0; i < 10; i++) {
    const j = claimJob(s, 1_000_100, () => 0.5);
    if (j) jobs.push(j);
  }
  // 1 upcoming (s1) + in-flight claims capped at QUEUE_TARGET
  assert.equal(jobs.length, QUEUE_TARGET - 1);
  assert.equal(claimJob(s, 1_000_200), null, "queue + in-flight full, no work");
});

test("with nobody listening the worker still tops the queue up to 5, then idles", () => {
  const s = stationWith(2);
  const away = 1_000_000 + 10 * MIN; // everyone left long ago
  advance(s, away);
  let made = 0;
  for (let i = 0; i < 10; i++) {
    const j = claimJob(s, away + i);
    if (j) { addSong(s, j.id, song(`n${i}`)); made++; }
  }
  assert.equal(made, QUEUE_TARGET - 1);
  assert.equal(s.queue.length, QUEUE_TARGET);
  assert.equal(s.current.id, "s0", "still frozen on the same song");
});

test("expired claims free their slot", () => {
  const s = stationWith(1);
  for (let i = 0; i < QUEUE_TARGET; i++) claimJob(s, 1_000_100, Math.random);
  assert.equal(claimJob(s, 1_000_200), null);
  touch(s, 1_000_000 + 16 * MIN);
  assert.ok(claimJob(s, 1_000_000 + 16 * MIN), "claims older than 15 min are dropped");
});

test("an upload fills the queue and clears its claim", () => {
  const s = stationWith(1);
  const job = claimJob(s, 1_000_100);
  addSong(s, job.id, song("new"));
  assert.equal(Object.keys(s.claims).length, 0);
  assert.equal(s.queue.at(-1).id, "new");
});

test("an empty queue replays history instead of going silent; pinned songs are kept", () => {
  const s = emptyState();
  addSong(s, "seed", song("seed", 50), { pinned: true, toHistory: true });
  touch(s, 0);
  assert.equal(s.current.id, "seed");
  assert.equal(publicView(s, 0).replaying, true);
  for (let t = 0; t <= 200_000; t += 20_000) touch(s, t);
  assert.equal(s.current.id, "seed", "the only song loops");
  assert.equal(s.history.length + 1, 1);
});

test("history is capped and old generated songs are evicted (pinned survive)", () => {
  const s = emptyState();
  addSong(s, "p", song("pinned", 10), { pinned: true, toHistory: true });
  for (let i = 0; i < 30; i++) addSong(s, `c${i}`, song(`g${i}`, 10));
  let evicted = [];
  for (let t = 0; t <= 400_000; t += 10_000) evicted = evicted.concat(touch(s, t));
  assert.ok(s.history.length <= 20);
  assert.ok(s.history.some((h) => h.id === "pinned") || s.current.id === "pinned");
  assert.ok(evicted.length > 0 && evicted.every((e) => !e.pinned));
});

test("a listener request is generated next and plays right after the current song", () => {
  const s = stationWith(4);
  const r = addRequest(s, "  rainy   jazz with saxophone ", 1_000_100);
  assert.equal(r.position, 1);
  const job = claimJob(s, 1_000_200);
  assert.equal(job.caption, "rainy jazz with saxophone");
  assert.equal(job.requestId, r.id);
  addSong(s, job.id, song("req-song"));
  const v = publicView(s, 1_000_300);
  assert.equal(v.upNext[0].id, "req-song", "jumps ahead of the regular queue");
  assert.equal(v.upNext[0].title, "listener request");
  assert.ok(!JSON.stringify(v).includes("saxophone"), "prompt text is never shown to others");
});

test("requests are made even when the queue is full", () => {
  const s = stationWith(6);
  assert.equal(claimJob(s, 1_000_100), null, "queue full, no regular job");
  addRequest(s, "upbeat bossa nova", 1_000_100);
  assert.ok(claimJob(s, 1_000_200), "a waiting request still gets made");
});

test("a request whose GPU job timed out goes back to the front", () => {
  const s = stationWith(1);
  const r = addRequest(s, "lost request", 1_000_100);
  claimJob(s, 1_000_200);
  touch(s, 1_000_000 + 16 * MIN);
  const job = claimJob(s, 1_000_000 + 16 * MIN);
  assert.equal(job.requestId, r.id);
});

test("request validation and cap", () => {
  const s = stationWith(1);
  assert.ok(addRequest(s, "x", 1).error);
  for (let i = 0; i < 10; i++) assert.ok(addRequest(s, `song ${i}`, 1).id);
  assert.ok(addRequest(s, "one too many", 1).error);
});

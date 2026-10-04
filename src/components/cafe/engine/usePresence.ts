import { useEffect, useRef, useState } from "react";
import { createClient, type RealtimeChannel } from "@supabase/supabase-js";
import { isLook, keyOf, poseActor, roomSize, sitPose, walkPose, type Look, type People } from "./avatar";
import type { Pt, Walk } from "./walk";
import type { Actor } from "./Stage";

// Everyone else in the café (Supabase Realtime). Each visitor shares, through Presence, who
// they are (look, barista or not) and where they rest (a spot, or a seat); it changes rarely.
// A walk is one Broadcast message (start + path); every browser plays it back at the same
// speed, so nothing is sent per frame. Joining mid-walk just shows people at their last spot.

const URL = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;
const ROOM = "cafe";
const CAPACITY = 40; // more than this and newcomers watch without an avatar
const SPEED = 64; // px/s, same as your own avatar
const MAX_PATH = 120;

const client = URL && KEY ? createClient(URL, KEY, { realtime: { params: { eventsPerSecond: 8 } } }) : null;

type Seat = { x: number; y: number; lift: number; back: boolean; flip: boolean; z: number };
type Rest = { at: Pt; seat: Seat | null; back: boolean; flip: boolean };
type Wire = Rest & { look: Look; barista: boolean };
type Me = {
  look: Look | null;
  people: People | null;
  barista: boolean;
  placed: boolean;
  net: React.MutableRefObject<{ walk?: (from: Pt, path: Pt[]) => void; settle?: () => void }>;
  snapshot: () => Rest;
  inFlight: () => { from: Pt; path: Pt[] } | null;
  walk: Walk;
};
type Other = Wire & { id: string; moving: { from: Pt; path: Pt[]; started: number } | null; seen: number };

// ---- never trust what comes off the wire
const num = (v: unknown, lo: number, hi: number) => (typeof v === "number" && Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : null);
const idx = (v: unknown, n: number) => (Number.isInteger(v) && (v as number) >= 0 && (v as number) < n ? (v as number) : 0);
const pt = (v: unknown, w: number, h: number): Pt | null => {
  const o = v as { x?: unknown; y?: unknown } | null;
  const x = num(o?.x, 0, w);
  const y = num(o?.y, 0, h);
  return x === null || y === null ? null : { x, y };
};
function cleanWire(v: unknown, w: number, h: number, people: People | null): Wire | null {
  const o = v as Partial<Wire> | null;
  const at = pt(o?.at, w, h);
  if (!o || !at) return null;
  const l = o.look as Partial<Look> | undefined;
  if (!people || !isLook(people, l)) return null; // only real people in real outfits
  const s = o.seat as Partial<Seat> | null | undefined;
  const sp = s ? pt(s, w, h) : null;
  const seat = s && sp ? { ...sp, lift: num(s.lift, 0, 40) ?? 0, back: !!s.back, flip: !!s.flip, z: num(s.z, 0, 2000) ?? 1 } : null;
  return { at, seat, look: { person: l.person, outfit: l.outfit }, barista: !!o.barista, back: !!o.back, flip: !!o.flip };
}

export function usePresence(me: Me, size: { w: number; h: number }) {
  const [others, setOthers] = useState<Record<string, Other>>({});
  const [full, setFull] = useState(false);
  const [, tick] = useState(0);
  const chan = useRef<RealtimeChannel | null>(null);
  const meRef = useRef(me);
  meRef.current = me;
  const id = useRef(Math.random().toString(36).slice(2, 10));
  const joined = useRef(false);

  // join the room once your avatar has arrived
  useEffect(() => {
    if (!client || !me.placed || chan.current) return;
    const ch = client.channel(ROOM, { config: { presence: { key: id.current }, broadcast: { self: false } } });
    chan.current = ch;
    const sync = () => {
      const state = ch.presenceState() as Record<string, unknown[]>;
      setOthers((prev) => {
        const next: Record<string, Other> = {};
        for (const [key, metas] of Object.entries(state)) {
          if (key === id.current) continue;
          const wire = cleanWire(metas[metas.length - 1], size.w, size.h, meRef.current.people);
          if (!wire) continue;
          const was = prev[key];
          // a fresh resting spot ends any walk we were playing for them
          const moving = was?.moving && (was.at.x !== wire.at.x || was.at.y !== wire.at.y || !!wire.seat !== !!was.seat) ? null : was?.moving ?? null;
          next[key] = { ...wire, id: key, moving, seen: was?.seen ?? performance.now() };
        }
        return next;
      });
    };
    ch.on("presence", { event: "sync" }, sync)
      .on("broadcast", { event: "walk" }, ({ payload }) => {
        const p = payload as { id?: unknown; from?: unknown; path?: unknown };
        if (typeof p.id !== "string" || p.id === id.current || !Array.isArray(p.path)) return;
        const from = pt(p.from, size.w, size.h);
        const path = (p.path as unknown[]).slice(0, MAX_PATH).map((q) => pt(q, size.w, size.h)).filter(Boolean) as Pt[];
        if (!from || !path.length) return;
        setOthers((prev) => (prev[p.id as string] ? { ...prev, [p.id as string]: { ...prev[p.id as string], seat: null, moving: { from, path, started: performance.now() } } } : prev));
      })
      .subscribe(async (status) => {
        if (status !== "SUBSCRIBED") return;
        const count = Object.keys(ch.presenceState()).length;
        if (count >= CAPACITY) {
          setFull(true); // watch only: you see everyone, nobody sees you
          return;
        }
        joined.current = true;
        await track();
        // already walking (in from the street)? let everyone see it
        const w = meRef.current.inFlight();
        if (w) ch.send({ type: "broadcast", event: "walk", payload: { id: id.current, from: w.from, path: w.path.slice(0, MAX_PATH) } });
      });

    const leave = () => {
      ch.untrack();
      client.removeChannel(ch);
    };
    window.addEventListener("pagehide", leave);
    return () => {
      window.removeEventListener("pagehide", leave);
      leave();
      chan.current = null;
      joined.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me.placed]);

  const track = async () => {
    const ch = chan.current;
    if (!ch || !joined.current) return;
    const m = meRef.current;
    if (!m.look) return;
    await ch.track({ ...m.snapshot(), look: m.look, barista: m.barista } satisfies Wire);
  };

  // your avatar tells the room when it starts walking and when it comes to rest
  useEffect(() => {
    let settleTimer = 0;
    let lastWalk = 0;
    me.net.current.walk = (from, path) => {
      const ch = chan.current;
      const now = performance.now();
      if (!ch || !joined.current || now - lastWalk < 120) return; // at most ~8 walks a second
      lastWalk = now;
      ch.send({ type: "broadcast", event: "walk", payload: { id: id.current, from, path: path.slice(0, MAX_PATH) } });
    };
    me.net.current.settle = () => {
      window.clearTimeout(settleTimer);
      settleTimer = window.setTimeout(track, 250); // presence updates are rate-limited: batch them
    };
    return () => window.clearTimeout(settleTimer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me.net]);

  // play back walks
  const anyMoving = Object.values(others).some((o) => o.moving || o.seat || performance.now() - o.seen < 700);
  useEffect(() => {
    if (!anyMoving) return;
    let raf = 0;
    const loop = () => {
      tick((n) => (n + 1) % 1e6);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [anyMoving]);

  const now = performance.now();
  const actors: Actor[] = [];
  const people = me.people;
  for (const o of Object.values(others)) {
    if (!people) break;
    if (!people.characters[keyOf(o.look)]) continue;
    const [fw, fh] = roomSize(people, keyOf(o.look));
    const seed = o.id.charCodeAt(0) + o.id.charCodeAt(1);
    const depth = (p: Pt) => me.walk.depthAt(p, { x0: p.x - fw / 2, y0: p.y - fh, x1: p.x + fw / 2, y1: p.y });
    let a: Actor | null = null;
    if (o.moving) {
      // where along their path they'd be by now
      let left = ((now - o.moving.started) / 1000) * SPEED;
      let pos = o.moving.from;
      let back = o.back;
      let flip = o.flip;
      let done = true;
      for (const to of o.moving.path) {
        const dx = to.x - pos.x;
        const dy = to.y - pos.y;
        const d = Math.hypot(dx, dy);
        if (d > 0.01) {
          back = dy < -0.01;
          flip = dx > 0.01 ? !back : dx < -0.01 ? back : flip;
        }
        if (d <= left) {
          left -= d;
          pos = to;
          continue;
        }
        pos = { x: pos.x + (dx / d) * left, y: pos.y + (dy / d) * left };
        done = false;
        break;
      }
      const pose = done ? (back ? "stand-back" : "stand-front") : walkPose(back, now - o.moving.started);
      a = poseActor(people, o.id, o.look, pose, pos.x, pos.y, flip, depth(pos));
    } else if (o.seat) {
      a = poseActor(people, o.id, o.look, sitPose(o.seat.back, now, seed), o.seat.x, o.seat.y - o.seat.lift, o.seat.flip, o.seat.z);
    } else {
      a = poseActor(people, o.id, o.look, o.back ? "stand-back" : "stand-front", o.at.x, o.at.y, o.flip, depth(o.at));
    }
    if (a) {
      a.opacity = Math.min(1, (now - o.seen) / 650); // newcomers fade in
      actors.push(a);
    }
  }

  return { actors, count: Object.keys(others).length, full, online: !!client };
}

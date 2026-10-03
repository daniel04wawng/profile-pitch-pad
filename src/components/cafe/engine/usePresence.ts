import { useEffect, useRef, useState } from "react";
import { createClient, type RealtimeChannel } from "@supabase/supabase-js";
import { FOOT, FRAME, HAIRS, PANTS, SHIRTS, SKINS, SIT_SEAT, STYLES, avatarSheet, type Look } from "./avatar";
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
const SPEED = 42; // px/s, same as your own avatar
const STEP_MS = 140;
const MAX_PATH = 120;

const client = URL && KEY ? createClient(URL, KEY, { realtime: { params: { eventsPerSecond: 8 } } }) : null;

type Seat = { x: number; y: number; lift: number; back: boolean; flip: boolean; z: number };
type Rest = { at: Pt; seat: Seat | null; back: boolean; flip: boolean };
type Wire = Rest & { look: Look; barista: boolean };
type Me = {
  look: Look;
  barista: boolean;
  placed: boolean;
  net: React.MutableRefObject<{ walk?: (from: Pt, path: Pt[]) => void; settle?: () => void }>;
  snapshot: () => Rest;
  walk: Walk;
};
type Other = Wire & { id: string; moving: { from: Pt; path: Pt[]; started: number } | null };

// ---- never trust what comes off the wire
const num = (v: unknown, lo: number, hi: number) => (typeof v === "number" && Number.isFinite(v) ? Math.max(lo, Math.min(hi, v)) : null);
const idx = (v: unknown, n: number) => (Number.isInteger(v) && (v as number) >= 0 && (v as number) < n ? (v as number) : 0);
const pt = (v: unknown, w: number, h: number): Pt | null => {
  const o = v as { x?: unknown; y?: unknown } | null;
  const x = num(o?.x, 0, w);
  const y = num(o?.y, 0, h);
  return x === null || y === null ? null : { x, y };
};
function cleanWire(v: unknown, w: number, h: number): Wire | null {
  const o = v as Partial<Wire> | null;
  const at = pt(o?.at, w, h);
  if (!o || !at) return null;
  const l = (o.look ?? {}) as Partial<Look>;
  const look: Look = { style: idx(l.style, STYLES.length), skin: idx(l.skin, SKINS.length), hair: idx(l.hair, HAIRS.length), shirt: idx(l.shirt, SHIRTS.length), pants: idx(l.pants, PANTS.length) };
  const s = o.seat as Partial<Seat> | null | undefined;
  const sp = s ? pt(s, w, h) : null;
  const seat = s && sp ? { ...sp, lift: num(s.lift, 0, 40) ?? 0, back: !!s.back, flip: !!s.flip, z: num(s.z, 0, 2000) ?? 1 } : null;
  return { at, seat, look, barista: !!o.barista, back: !!o.back, flip: !!o.flip };
}

export function usePresence(me: Me, size: { w: number; h: number }) {
  const [others, setOthers] = useState<Record<string, Other>>({});
  const [full, setFull] = useState(false);
  const [sheets, setSheets] = useState<Record<string, string>>({});
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
          const wire = cleanWire(metas[metas.length - 1], size.w, size.h);
          if (!wire) continue;
          const was = prev[key];
          // a fresh resting spot ends any walk we were playing for them
          const moving = was?.moving && (was.at.x !== wire.at.x || was.at.y !== wire.at.y || !!wire.seat !== !!was.seat) ? null : was?.moving ?? null;
          next[key] = { ...wire, id: key, moving };
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

  // sprite sheets for everyone's looks
  useEffect(() => {
    for (const o of Object.values(others)) {
      const k = JSON.stringify(o.look);
      if (!sheets[k]) avatarSheet(o.look).then((s) => setSheets((all) => ({ ...all, [k]: s })));
    }
  }, [others, sheets]);

  // play back walks
  const anyMoving = Object.values(others).some((o) => o.moving);
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
  for (const o of Object.values(others)) {
    const sheet = sheets[JSON.stringify(o.look)];
    if (!sheet) continue;
    const base = { id: o.id, sheet, w: FRAME.w, h: FRAME.h, footX: FOOT.x, footY: FOOT.y };
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
      const cycle = Math.floor((now - o.moving.started) / STEP_MS) % 4;
      const frame = (back ? 3 : 0) + (done ? 0 : [1, 0, 2, 0][cycle]);
      const rect = { x0: pos.x - FOOT.x, y0: pos.y - FOOT.y, x1: pos.x + FRAME.w - FOOT.x, y1: pos.y };
      actors.push({ ...base, frame, x: pos.x, y: pos.y, flip, z: me.walk.depthAt(pos, rect) });
    } else if (o.seat) {
      actors.push({ ...base, frame: o.seat.back ? 7 : 6, x: o.seat.x, y: o.seat.y - o.seat.lift + SIT_SEAT, flip: o.seat.flip, z: o.seat.z });
    } else {
      const rect = { x0: o.at.x - FOOT.x, y0: o.at.y - FOOT.y, x1: o.at.x + FRAME.w - FOOT.x, y1: o.at.y };
      actors.push({ ...base, frame: o.back ? 3 : 0, x: o.at.x, y: o.at.y, flip: o.flip, z: me.walk.depthAt(o.at, rect) });
    }
  }

  return { actors, count: Object.keys(others).length, full, online: !!client };
}

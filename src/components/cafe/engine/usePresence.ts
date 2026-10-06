import { useEffect, useRef, useState } from "react";
import type { RealtimeChannel } from "@supabase/supabase-js";
import { supabase as client } from "./supabase";
import { cleanAvatar, isLook, keyOf, poseActor, roomSize, sitPose, walkPose, type Look, type People } from "./avatar";
import { Body, dirOf, facing, isDirection, loadRig, useCatalog, type Rig } from "./rig";
import type { Pt, Walk } from "./walk";
import type { Actor } from "./Stage";

// Everyone else in the café (Supabase Realtime). Each visitor shares, through Presence, who
// they are (look, barista or not) and where they rest (a spot, or a seat); it changes rarely.
// A walk is one Broadcast message (start + path); every browser plays it back at the same
// speed, so nothing is sent per frame. Joining mid-walk just shows people at their last spot.

const ROOM = "cafe";
const CAPACITY = 40; // more than this and newcomers watch without an avatar
const SPEED = 64; // px/s, same as your own avatar
const MAX_PATH = 120;


type Seat = { x: number; y: number; lift: number; back: boolean; flip: boolean; z: number };
// dir: which way they face; since: when they sat down (wall clock), so sips line up
type Rest = { at: Pt; seat: Seat | null; back: boolean; flip: boolean; dir?: string; since?: number };
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
// moving.rise: the seat they're getting up from before the walk starts
type Other = Wire & { id: string; moving: { from: Pt; path: Pt[]; started: number; rise?: Seat | null } | null; seen: number };
const SIT_MS = 1000; // sitting down / getting up (the rig's sit-down and stand-up clips)

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
  const dir = isDirection(o.dir) ? o.dir : dirOf(!!o.back, !!o.flip);
  const since = num(o.since, 0, Date.now() + 60_000) ?? 0;
  return { at, seat, look: { person: l.person, outfit: l.outfit, avatar: cleanAvatar((l as Look).avatar) }, barista: !!o.barista, back: !!o.back, flip: !!o.flip, dir, since };
}

// off (solo) in your own café and in the editor: nobody else is there
export function usePresence(me: Me, size: { w: number; h: number }, on = true) {
  const [others, setOthers] = useState<Record<string, Other>>({});
  const [full, setFull] = useState(false);
  const [, tick] = useState(0);
  const chan = useRef<RealtimeChannel | null>(null);
  const meRef = useRef(me);
  meRef.current = me;
  const id = useRef(Math.random().toString(36).slice(2, 10));
  // everyone's own avatar controller (their own clock), and the avatars loaded so far
  const bodies = useRef(new Map<string, Body>());
  const catalog = useCatalog();
  const [rigs, setRigs] = useState<Record<string, Rig | "failed">>({});
  const joined = useRef(false);

  // join the room once your avatar has arrived
  useEffect(() => {
    if (!client || !on || !me.placed || chan.current) return;
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
        // let go of anyone who left
        for (const k of [...bodies.current.keys()]) if (!next[k]) bodies.current.delete(k);
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
        // someone getting up from a seat stands up first, then walks
        setOthers((prev) => {
          const o = prev[p.id as string];
          if (!o) return prev;
          const rise = o.seat && bodies.current.get(o.id)?.sitting ? o.seat : null;
          return { ...prev, [o.id]: { ...o, seat: null, moving: { from, path, started: performance.now() + (rise ? SIT_MS : 0), rise } } };
        });
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
  }, [me.placed, on]);

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

  // which rigged avatar someone is (null: a classic person)
  const rigIdOf = (o: Other) => (!catalog || o.look.avatar === "" ? null : (catalog.find((a) => a.id === o.look.avatar) ?? catalog[0])?.id ?? null);
  // load the avatars people are using, once each
  const wanted = [...new Set(Object.values(others).map(rigIdOf).filter(Boolean) as string[])].sort().join();
  useEffect(() => {
    for (const r of wanted ? wanted.split(",") : []) {
      if (rigs[r]) continue;
      loadRig(r).then(
        (x) => setRigs((m) => ({ ...m, [r]: x })),
        () => setRigs((m) => ({ ...m, [r]: "failed" })),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wanted]);

  // play back walks, and keep everyone's clocks running (breathing, sitting, sipping): redraw
  // when someone moves or their frame changes
  const othersRef = useRef(others);
  othersRef.current = others;
  const anyone = Object.keys(others).length > 0;
  useEffect(() => {
    if (!anyone) return;
    let raf = 0;
    let last = performance.now();
    let shown = "";
    const loop = (t: number) => {
      const dt = Math.min(500, t - last);
      last = t;
      let busy = false;
      for (const o of Object.values(othersRef.current)) {
        if (o.moving || t - o.seen < 700 || (o.seat && !bodies.current.has(o.id))) busy = true;
      }
      let frames = "";
      for (const [k, b] of bodies.current) {
        b.tick(dt);
        frames += `${k}:${b.av.action}:${b.av.frameIndex}:${b.dir};`;
      }
      if (busy || frames !== shown) {
        shown = frames;
        tick((n) => (n + 1) % 1e6);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [anyone]);

  const now = performance.now();
  const actors: Actor[] = [];
  const people = me.people;
  // where along a walk someone is by now, which way that leg goes, and whether they're there
  const along = (m: NonNullable<Other["moving"]>) => {
    let left = (Math.max(0, now - m.started) / 1000) * SPEED;
    const total = left;
    let pos = m.from;
    let dx = 0;
    let dy = 0;
    for (const to of m.path) {
      const ddx = to.x - pos.x;
      const ddy = to.y - pos.y;
      const d = Math.hypot(ddx, ddy);
      if (d > 0.01) [dx, dy] = [ddx, ddy];
      if (d <= left) {
        left -= d;
        pos = to;
        continue;
      }
      return { pos: { x: pos.x + (ddx / d) * left, y: pos.y + (ddy / d) * left }, dx, dy, done: false, total };
    }
    return { pos, dx, dy, done: true, total: total - left };
  };
  for (const o of Object.values(others)) {
    const rid = rigIdOf(o);
    const rig = rid ? rigs[rid] : undefined;
    let a: Actor | null = null;
    if (rig && rig !== "failed") {
      // ---- a rigged avatar, with its own controller
      let b = bodies.current.get(o.id);
      if (!b || b.rig !== rig) {
        b = new Body(rig, isDirection(o.dir) ? o.dir : "SE");
        bodies.current.set(o.id, b);
      }
      const [fw, fh] = rig.base.manifest.frameSize;
      const depth = (p: Pt) => me.walk.depthAt(p, { x0: p.x - fw / 2, y0: p.y - fh, x1: p.x + fw / 2, y1: p.y });
      const m = o.moving;
      if (m && now < m.started && m.rise) {
        b.standUp(); // getting up from the seat, then the walk
        a = b.actor(o.id, m.rise.x, m.rise.y - m.rise.lift, m.rise.z);
      } else if (m) {
        b.release();
        const w = along(m);
        b.face(facing(b.dir, w.dx, w.dy));
        if (w.done) b.stop();
        else b.walkAt(w.total);
        a = b.actor(o.id, w.pos.x, w.pos.y, depth(w.pos));
      } else if (o.seat) {
        if (!b.sitting) {
          b.face(dirOf(o.seat.back, o.seat.flip));
          // just sat down: watch them sit; sat a while ago: catch their clock up
          const age = o.since ? Date.now() - o.since : SIT_MS * 10;
          if (age < SIT_MS) {
            b.sit();
            b.tick(age);
          } else b.seatedFor(age - SIT_MS);
        }
        a = b.actor(o.id, o.seat.x, o.seat.y - o.seat.lift, o.seat.z);
      } else {
        b.release();
        b.stop();
        if (isDirection(o.dir)) b.face(o.dir);
        a = b.actor(o.id, o.at.x, o.at.y, depth(o.at));
      }
    } else if (people && people.characters[keyOf(o.look)] && !(rid && !rig)) {
      // ---- a classic person (or a rigged avatar that couldn't load)
      bodies.current.delete(o.id);
      const [fw, fh] = roomSize(people, keyOf(o.look));
      const seed = o.id.charCodeAt(0) + o.id.charCodeAt(1);
      const depth = (p: Pt) => me.walk.depthAt(p, { x0: p.x - fw / 2, y0: p.y - fh, x1: p.x + fw / 2, y1: p.y });
      if (o.moving) {
        const w = along(o.moving);
        const back = w.dy < -0.01 || (w.dy === 0 && o.back);
        const flip = w.dx > 0.01 ? !back : w.dx < -0.01 ? back : o.flip;
        const pose = w.done ? (back ? "stand-back" : "stand-front") : walkPose(back, now - o.moving.started);
        a = poseActor(people, o.id, o.look, pose, w.pos.x, w.pos.y, flip, depth(w.pos));
      } else if (o.seat) {
        a = poseActor(people, o.id, o.look, sitPose(o.seat.back, now, seed), o.seat.x, o.seat.y - o.seat.lift, o.seat.flip, o.seat.z);
      } else {
        a = poseActor(people, o.id, o.look, o.back ? "stand-back" : "stand-front", o.at.x, o.at.y, o.flip, depth(o.at));
      }
    }
    if (a) {
      a.opacity = Math.min(1, (now - o.seen) / 650); // newcomers fade in
      actors.push(a);
    }
  }

  return { actors, count: Object.keys(others).length, full, online: !!client && on };
}

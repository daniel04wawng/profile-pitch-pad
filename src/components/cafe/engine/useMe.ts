import { useEffect, useMemo, useRef, useState } from "react";
import { DANIEL, FOOT, FRAME, SIT_SEAT, avatarSheet, isBarista, saveLook, savedLook, type Look } from "./avatar";
import { makeWalk, seatOf, type Cell, type Pt } from "./walk";
import { BASE, BOOT, frontOf, type Layout, type SpriteDef } from "./types";
import { measureSprite, type Measure } from "./measure";
import type { Actor, Companion } from "./Stage";

// The visitor's own avatar: walks in, walks wherever you click (around the furniture), walks
// up to things before their screen opens, and sits in seats.

const SPEED = 42; // px per second across the screen
const STEP_MS = 140; // walk-cycle frame time
const nameOf = (file: string) => file.replace(/^sprites\//, "").replace(/\.png$/, "");

type Seated = { x: number; y: number; lift: number; back: boolean; flip: boolean; z: number; seat: SpriteDef };

// arrow keys / WASD move the way they point on screen: up is straight up the screen (one
// cell back along both floor axes), right is straight right, and so on; two keys together
// walk diagonally, which on this floor is along one of its axes
const KEYS: Record<string, Cell> = {
  ArrowUp: { i: -1, j: -1 }, w: { i: -1, j: -1 },
  ArrowDown: { i: 1, j: 1 }, s: { i: 1, j: 1 },
  ArrowLeft: { i: -1, j: 1 }, a: { i: -1, j: 1 },
  ArrowRight: { i: 1, j: -1 }, d: { i: 1, j: -1 },
};
const keyName = (e: KeyboardEvent) => (e.key.length === 1 ? e.key.toLowerCase() : e.key);

export function useMe(layout: Layout, companions: Record<string, Companion>, enabled = true) {
  // footprints for pieces without a size, read from their pixels
  const [measures, setMeasures] = useState<Record<string, Measure | null>>({});
  useEffect(() => {
    let alive = true;
    const files = [...new Set(layout.assets.map((a) => a.file))];
    Promise.all(files.map((f) => measureSprite(`${BASE}${f}?v=${BOOT}`).then((m) => [f, m] as const))).then(
      (all) => alive && setMeasures(Object.fromEntries(all)),
    );
    return () => {
      alive = false;
    };
  }, [layout.assets]);
  const walk = useMemo(() => makeWalk(layout, companions, measures), [layout, companions, measures]);
  const walkRef = useRef(walk);
  walkRef.current = walk;
  const heldKeys = useRef(new Set<string>());
  // the step the held keys add up to (each part kept to -1..1)
  const held = {
    get current(): Cell | null {
      let i = 0;
      let j = 0;
      for (const k of heldKeys.current) {
        i += KEYS[k].i;
        j += KEYS[k].j;
      }
      i = Math.max(-1, Math.min(1, i));
      j = Math.max(-1, Math.min(1, j));
      return i || j ? { i, j } : null;
    },
  };
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;
  const barista = useMemo(isBarista, []);
  // the barista is always Daniel; everyone else keeps their own look
  const [look, setLook] = useState<Look>(() => (barista ? DANIEL : savedLook()));
  const [sheet, setSheet] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    avatarSheet(look).then((s) => alive && setSheet(s));
    return () => {
      alive = false;
    };
  }, [look, barista]);

  const st = useRef({
    pos: { x: 0, y: 0 } as Pt,
    path: [] as Pt[],
    back: false,
    flip: false,
    seated: null as Seated | null,
    arrive: null as null | (() => void),
    t: 0,
    placed: false,
  });
  if (import.meta.env.DEV) (window as unknown as { __me?: unknown }).__me = { walk, st };
  // multiplayer hooks (usePresence fills these): a walk starting, and coming to rest
  const net = useRef<{ walk?: (from: Pt, path: Pt[]) => void; settle?: () => void }>({});
  const [frame, setFrame] = useState(0);
  const [, tick] = useState(0);

  // arrive: the barista comes out of the kitchen doorway, visitors walk in off the street
  useEffect(() => {
    const s = st.current;
    if (s.placed || !Object.keys(companions).length) return;
    s.placed = true;
    const door = barista ? layout.assets.find((a) => frontOf(nameOf(a.file)) === "kitchen-doorway" && !a.hidden) : undefined;
    if (door) {
      const f = companions["kitchen-doorway"]?.foot ?? { x: door.w / 2, y: door.h };
      const at = { x: door.x + (door.flipX ? door.w - f.x : f.x) + (door.flipX ? -6 : 6), y: door.y + f.y - 2 };
      s.pos = at;
      const route = walk.walkTo(walk.cellAt(at), walk.free);
      const start = route?.[route.length - 1];
      if (start) {
        const inward = walk.walkTo(start, (c) => walk.free(c) && Math.abs(c.i - start.i) + Math.abs(c.j - start.j) >= 3);
        s.path = (inward ?? [start]).map(walk.cellCentre);
      }
    } else {
      const e = walk.entrance();
      s.pos = e.from;
      s.path = [walk.cellCentre(e.to)];
    }
    tick((n) => n + 1);
  }, [companions, walk, barista, layout.assets]);

  // movement
  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    // advance the avatar by dt seconds (the frame loop calls this; tests can too)
    const advance = (dt: number) => {
      const s = st.current;
      const w = walkRef.current;
      if (!s.path.length && held.current && !s.seated) {
        // keep walking cell by cell while an arrow is held; stop at anything in the way
        const here = w.cellAt(s.pos);
        const d = held.current;
        const next = { i: here.i + d.i, j: here.j + d.j };
        // a diagonal step (straight up/down/left/right on screen) mustn't squeeze between two
        // things touching at a corner
        const corners = !d.i || !d.j || (w.free({ i: here.i + d.i, j: here.j }) && w.free({ i: here.i, j: here.j + d.j }));
        if (w.free(next) && corners) {
          s.path = [w.cellCentre(next)];
          net.current.walk?.({ ...s.pos }, [...s.path]);
        } else {
          const c = w.cellCentre(here);
          if (Math.hypot(c.x - s.pos.x, c.y - s.pos.y) > 0.5) {
            s.path = [c];
            net.current.walk?.({ ...s.pos }, [...s.path]);
          }
          else {
            // blocked: just turn to face that way
            const t = w.cellCentre(next);
            s.back = t.y < s.pos.y;
            s.flip = t.x > s.pos.x ? !s.back : s.back;
            setFrame(s.back ? 3 : 0);
          }
        }
      }
      if (s.path.length) {
        let left = SPEED * dt;
        while (left > 0 && s.path.length) {
          const to = s.path[0];
          const dx = to.x - s.pos.x;
          const dy = to.y - s.pos.y;
          const dist = Math.hypot(dx, dy);
          if (dist > 0.01) {
            // face the way you're going: down-right/down-left = toward you, up = away
            s.back = dy < -0.01;
            s.flip = dx > 0.01 ? !s.back : dx < -0.01 ? s.back : s.flip;
          }
          if (dist <= left) {
            s.pos = { ...to };
            s.path.shift();
            left -= dist;
            if (!s.path.length) {
              if (s.arrive) {
                const f = s.arrive;
                s.arrive = null;
                f();
              }
              if (!held.current) net.current.settle?.(); // came to rest (or sat down)
            }
          } else {
            s.pos = { x: s.pos.x + (dx / dist) * left, y: s.pos.y + (dy / dist) * left };
            left = 0;
          }
        }
        s.t += dt * 1000;
        const cycle = Math.floor(s.t / STEP_MS) % 4; // step, stand, other step, stand
        const base = s.back ? 3 : 0;
        setFrame(s.path.length ? base + [1, 0, 2, 0][cycle] : base);
        tick((n) => (n + 1) % 1e6);
      }
    };
    const loop = (now: number) => {
      // time-based, so it walks at the same speed however often frames come (a background tab
      // may only get a couple a second); a long pause (tab hidden) doesn't teleport you though
      advance(Math.min(0.5, (now - last) / 1000));
      last = now;
      raf = requestAnimationFrame(loop);
    };
    if (import.meta.env.DEV) (window as unknown as { __advance?: unknown }).__advance = advance;
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      const k = keyName(e);
      if (!KEYS[k] || !enabledRef.current || (e.target instanceof HTMLElement && e.target.closest("input, textarea, select"))) return;
      e.preventDefault();
      if (!heldKeys.current.size) standUp();
      heldKeys.current.add(k);
      st.current.arrive = null;
    };
    const up = (e: KeyboardEvent) => {
      heldKeys.current.delete(keyName(e));
    };
    const blur = () => heldKeys.current.clear();
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    window.addEventListener("blur", blur);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
      window.removeEventListener("blur", blur);
    };
  });

  const standUp = () => {
    const s = st.current;
    if (!s.seated) return;
    const seat = s.seated.seat;
    s.seated = null;
    // step off to the nearest free cell next to the seat
    const beside = walk.besideOf(seat);
    const from = walk.cellAt({ x: s.pos.x, y: s.pos.y });
    const route = walk.walkTo(from, (c) => beside.has(walk.key(c))) ?? walk.walkTo(from, walk.free);
    const out = route?.[route.length - 1];
    if (out) s.pos = walk.cellCentre(out);
  };

  const go = (cells: Cell[] | null, arrive?: () => void) => {
    const s = st.current;
    if (!cells) return false;
    s.path = cells.slice(1).map(walk.cellCentre);
    // first glide to the middle of the cell you're in, so steps stay on the grid
    s.path.unshift(walk.cellCentre(cells[0]));
    s.arrive = arrive ?? null;
    net.current.walk?.({ ...s.pos }, [...s.path]);
    return true;
  };

  // click on the floor: walk there (or as close as you can get)
  const walkTo = (p: Pt) => {
    standUp();
    const s = st.current;
    const target = walk.cellAt(p);
    if (!walk.inside(target)) return;
    const from = walk.cellAt(s.pos);
    // nearest free cell to where you clicked, then the way there
    const spot = walk.walkTo(target, walk.free)?.slice(-1)[0] ?? target;
    go(walk.walkTo(from, (c) => c.i === spot.i && c.j === spot.j));
  };

  // click on a thing: walk up to it, then `then` (open its screen); seats: sit down first
  const visit = (thing: SpriteDef, then: () => void) => {
    standUp();
    const s = st.current;
    const from = walk.cellAt(s.pos);
    const beside = walk.besideOf(thing);
    const route = walk.walkTo(from, (c) => beside.has(walk.key(c)));
    const seatSpot = seatOf(thing) ? walk.seatSpot(thing) : null;
    const arrive = () => {
      if (seatSpot) {
        s.seated = { ...seatSpot, z: seatSpot.back ? thing.baseY - 1 : thing.baseY + 1, seat: thing };
        s.pos = { x: seatSpot.x, y: seatSpot.y };
      } else {
        // turn to face it
        const c = walk.footprint(thing);
        const mid = c ? walk.toScreen((c.a0 + c.a1) / 2, (c.b0 + c.b1) / 2) : { x: thing.x + thing.w / 2, y: thing.y + thing.h };
        s.back = mid.y < s.pos.y;
        s.flip = mid.x > s.pos.x ? !s.back : s.back;
        setFrame(s.back ? 3 : 0);
      }
      tick((n) => n + 1);
      then();
    };
    if (!go(route, arrive)) arrive(); // nowhere to stand: just open it
  };

  const s = st.current;
  const actor: Actor | null =
    sheet && s.placed
      ? s.seated
        ? {
            id: "me",
            sheet,
            frame: s.seated.back ? 7 : 6,
            w: FRAME.w,
            h: FRAME.h,
            footX: FOOT.x,
            footY: FOOT.y,
            x: s.seated.x,
            // the seat's surface is `lift` above the floor; the sitting frame's seat is SIT_SEAT up
            y: s.seated.y - s.seated.lift + SIT_SEAT,
            flip: s.seated.flip,
            z: s.seated.z,
          }
        : { id: "me", sheet, frame, w: FRAME.w, h: FRAME.h, footX: FOOT.x, footY: FOOT.y, x: s.pos.x, y: s.pos.y, flip: s.flip, z: walk.depthAt(s.pos, { x0: s.pos.x - FOOT.x, y0: s.pos.y - FOOT.y, x1: s.pos.x + FRAME.w - FOOT.x, y1: s.pos.y }) }
      : null;

  const changeLook = (l: Look) => {
    if (barista) return; // Daniel stays Daniel
    setLook(l);
    saveLook(l);
    window.setTimeout(() => net.current.settle?.(), 0); // tell the room about the new look
  };
  // where you are right now, for the room
  const snapshot = () => {
    const s = st.current;
    return {
      at: { x: Math.round(s.pos.x), y: Math.round(s.pos.y) },
      seat: s.seated ? { x: s.seated.x, y: s.seated.y, lift: s.seated.lift, back: s.seated.back, flip: s.seated.flip, z: s.seated.z } : null,
      back: s.back,
      flip: s.flip,
    };
  };

  return { actor, look, setLook: changeLook, barista, walkTo, visit, standUp, net, snapshot, walk, placed: s.placed };
}

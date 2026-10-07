import { DEFAULT_GRID, FLAT_ASSETS, WALL_ITEMS, frontOf, isClutter, rotOf, type Layout, type SpriteDef } from "./types";
import type { Companion } from "./Stage";
import type { Measure } from "./measure";

// Where avatars can walk. The floor is split into half-tile cells; furniture blocks the cells
// its footprint covers (from `size` in _companions.json, measured from its foot). Paths go
// along the two floor axes, like walking along the planks.

type Grid = NonNullable<Layout["grid"]>;
export type Cell = { i: number; j: number }; // i along a (down-right), j along b (down-left)
export type Pt = { x: number; y: number };

const nameOf = (file: string) => file.replace(/^sprites\//, "").replace(/\.png$/, "");

// Seats an avatar can sit on: how high the seat is (px) and how far forward of its centre
// the seat part is (units, toward the front of the piece).
export const SEATS: Record<string, { h: number; forward: number }> = {
  "cafe-chair": { h: 11, forward: 0 },
  "piano-stool": { h: 10, forward: 0 },
  booth: { h: 11, forward: 1.5 },
  couch: { h: 13, forward: 1.5 },
  "sofa-large": { h: 13, forward: 1.5 },
  armchair: { h: 12, forward: 0.3 }, // deep seat: sit well back in it
};
export const seatOf = (s: SpriteDef) => SEATS[frontOf(nameOf(s.file))];

export function makeWalk(layout: Layout, companions: Record<string, Companion>, measures: Record<string, Measure | null> = {}) {
  const g: Grid = layout.grid ?? DEFAULT_GRID;
  const U = g.tile / 4; // grid units per tile (2px across, 1px down each)
  const C = U / 2; // a cell is half a tile
  const I = (g.cols ?? 20) * 2;
  const J = (g.rows ?? 20) * 2;

  const toUnits = (p: Pt) => {
    const d = (p.x - g.ox) / 2;
    const e = p.y - g.oy;
    return { a: (e + d) / 2, b: (e - d) / 2 };
  };
  const toScreen = (a: number, b: number): Pt => ({ x: g.ox + 2 * (a - b), y: g.oy + a + b });
  const cellCentre = (c: Cell) => toScreen((c.i + 0.5) * C, (c.j + 0.5) * C);
  const cellAt = (p: Pt): Cell => {
    const u = toUnits(p);
    return { i: Math.floor(u.a / C), j: Math.floor(u.b / C) };
  };
  const inside = (c: Cell) => c.i >= 0 && c.j >= 0 && c.i < I && c.j < J;
  const key = (c: Cell) => c.j * I + c.i;

  // A piece's footprint as a box in units (a0..a1, b0..b1), or null if it has no size.
  const compOf = (s: SpriteDef) => companions[nameOf(s.file)] ?? companions[frontOf(nameOf(s.file))];
  // the asset's own collision (set in the editor) if it has one; a back view without one uses
  // its front's
  const collisionOf = (s: SpriteDef) => companions[nameOf(s.file)]?.collision ?? companions[frontOf(nameOf(s.file))]?.collision;
  const footprint = (s: SpriteDef) => {
    const own = collisionOf(s);
    const comp = own ? { foot: own.foot, size: own.size } : compOf(s);
    if (!comp?.size || !comp.foot) {
      // no size given: read it off the sprite's outline (front corner + its two extents)
      const m = measures[s.file];
      if (!m) return null;
      const k = s.w / m.w;
      const fx = s.flipX ? s.w - 1 - m.fx * k : m.fx * k;
      const lx = s.flipX ? s.w - 1 - m.rx * k : m.lx * k;
      const rx = s.flipX ? s.w - 1 - m.lx * k : m.rx * k;
      const f = toUnits({ x: s.x + fx + 0.5, y: s.y + m.fy * (s.h / m.h) + 1 });
      const A = Math.max(1, (fx - lx) / 2);
      const B = Math.max(1, (rx - fx) / 2);
      return { a0: f.a - A, a1: f.a, b0: f.b - B, b1: f.b };
    }
    const fx = s.x + (s.flipX ? s.w - comp.foot.x : comp.foot.x);
    const fy = s.y + comp.foot.y;
    const f = toUnits({ x: fx, y: fy });
    // mirroring swaps the two floor axes
    const A = s.flipX ? comp.size.b : comp.size.a;
    const B = s.flipX ? comp.size.a : comp.size.b;
    if (comp.size.from === "centre") return { a0: f.a - A / 2, a1: f.a + A / 2, b0: f.b - B / 2, b1: f.b + B / 2 };
    if (comp.size.from === "back") return { a0: f.a, a1: f.a + A, b0: f.b, b1: f.b + B };
    return { a0: f.a - A, a1: f.a, b0: f.b - B, b1: f.b };
  };
  const cellsOf = (box: { a0: number; a1: number; b0: number; b1: number }) => {
    const out: Cell[] = [];
    for (let i = Math.floor((box.a0 + 0.5) / C); i <= Math.floor((box.a1 - 0.5) / C); i++)
      for (let j = Math.floor((box.b0 + 0.5) / C); j <= Math.floor((box.b1 - 0.5) / C); j++) out.push({ i, j });
    return out.filter(inside);
  };

  // which cells are taken, and by what
  const owner = new Int32Array(I * J).fill(-1);
  const solids: { box: NonNullable<ReturnType<typeof footprint>>; z: number; r: { x0: number; y0: number; x1: number; y1: number } }[] = [];
  layout.assets.forEach((s, n) => {
    const name = nameOf(s.file);
    if (s.hidden || WALL_ITEMS[frontOf(name)]) return;
    // rugs and clutter don't block, unless the asset has a collision of its own
    if (!collisionOf(s) && (FLAT_ASSETS.has(name) || isClutter(layout, name))) return;
    const box = footprint(s);
    if (!box) return;
    solids.push({ box, z: s.baseY, r: { x0: s.x, y0: s.y, x1: s.x + s.w, y1: s.y + s.h } });
    if (collisionOf(s)?.walkable) return; // you can walk through it (it still sorts in depth)
    for (const c of cellsOf(box)) owner[key(c)] = n;
  });

  // Draw order for someone standing at p (their figure covers `rect` on screen): in front of
  // each overlapping piece they're past on either floor axis (further down-right or down-left
  // than its near edge), behind the others. Comparing one screen height can't do this next to
  // long pieces like counters; pieces that don't overlap them on screen don't matter.
  const depthAt = (p: Pt, rect: { x0: number; y0: number; x1: number; y1: number }) => {
    const u = toUnits(p);
    let z = 1;
    let below = Infinity;
    for (const s of solids) {
      if (s.r.x1 <= rect.x0 || s.r.x0 >= rect.x1 || s.r.y1 <= rect.y0 || s.r.y0 >= rect.y1) continue;
      if (u.a >= s.box.a1 - 0.25 || u.b >= s.box.b1 - 0.25) z = Math.max(z, s.z + 1);
      else below = Math.min(below, s.z);
    }
    return below <= z ? Math.max(1, below - 1) : z;
  };

  const free = (c: Cell) => inside(c) && owner[key(c)] < 0;

  const STEPS = [
    { i: 1, j: 0 },
    { i: -1, j: 0 },
    { i: 0, j: 1 },
    { i: 0, j: -1 },
  ];
  // Shortest walk from `from` to the nearest cell where goal() holds (breadth-first: every step
  // costs the same). The start may be inside something (just stood up), the rest must be free.
  const walkTo = (from: Cell, goal: (c: Cell) => boolean): Cell[] | null => {
    const prev = new Int32Array(I * J).fill(-2);
    const q: Cell[] = [from];
    prev[key(from)] = -1;
    for (let h = 0; h < q.length; h++) {
      const c = q[h];
      if (goal(c)) {
        const path: Cell[] = [];
        for (let k = key(c); k >= 0; k = prev[k]) path.unshift({ i: k % I, j: Math.floor(k / I) });
        return path;
      }
      for (const d of STEPS) {
        const n = { i: c.i + d.i, j: c.j + d.j };
        if (free(n) && prev[key(n)] === -2) {
          prev[key(n)] = key(c);
          q.push(n);
        }
      }
    }
    return null;
  };

  // the cells right next to a piece (where you'd stand to use it)
  const besideOf = (s: SpriteDef) => {
    const box = footprint(s);
    if (!box) {
      // no footprint (a poster, the door): stand on the floor just in front of where it is
      return new Set([key(cellAt({ x: s.x + s.w / 2, y: s.y + s.h }))]);
    }
    const near = new Set<number>();
    for (const c of cellsOf(box)) for (const d of STEPS) {
      const n = { i: c.i + d.i, j: c.j + d.j };
      if (free(n)) near.add(key(n));
    }
    return near;
  };

  // where an avatar sits on a seat, and which way it faces
  const seatSpot = (s: SpriteDef) => {
    const seat = seatOf(s);
    const box = footprint(s);
    if (!seat || !box) return null;
    const r = rotOf(s);
    // the piece faces you-left (0), away-left (1), away-right (2) or you-right (3); its front is
    // toward +b for 0, -a for 1, -b for 2, +a for 3
    const fwd = [{ a: 0, b: 1 }, { a: -1, b: 0 }, { a: 0, b: -1 }, { a: 1, b: 0 }][r];
    const a = (box.a0 + box.a1) / 2 + fwd.a * seat.forward;
    const b = (box.b0 + box.b1) / 2 + fwd.b * seat.forward;
    const p = toScreen(a, b);
    return { x: p.x, y: p.y, lift: seat.h, back: r === 1 || r === 2, flip: r === 1 || r === 3 };
  };

  // Where people arrive. The café's front walls are cut away, so they walk in across the open
  // front edge of the floor: from just outside it, onto the floor, a few steps in. The spot is
  // the layout's entrance (set in the editor), or near the front corner.
  const entrance = (): { from: Pt; path: Pt[] } => {
    const want = layout.entrance ? cellAt(layout.entrance) : { i: I - 1, j: J - 5 };
    const c = { i: Math.max(0, Math.min(I - 1, want.i)), j: Math.max(0, Math.min(J - 1, want.j)) };
    // the nearer of the two open edges: down-right (i = I-1) or down-left (j = J-1)
    const alongA = I - 1 - c.i <= J - 1 - c.j;
    const edge = alongA ? { i: I - 1, j: c.j } : { i: c.i, j: J - 1 };
    const out = alongA ? { i: 1, j: 0 } : { i: 0, j: 1 };
    const onFloor = walkTo(edge, free)?.slice(-1)[0] ?? edge;
    const steps = walkTo(onFloor, (q) => free(q) && (alongA ? onFloor.i - q.i : onFloor.j - q.j) >= 5) ?? [onFloor];
    // start well outside, so there's a proper walk in from the street
    const from = cellCentre({ i: onFloor.i + out.i * 6, j: onFloor.j + out.j * 6 });
    const approach = [4, 2].map((k) => cellCentre({ i: onFloor.i + out.i * k, j: onFloor.j + out.j * k }));
    return { from, path: [...approach, ...steps.map(cellCentre)] };
  };

  return { cellAt, cellCentre, inside, free, walkTo, besideOf, seatSpot, footprint, collisionOf, entrance, key, toScreen, toUnits, depthAt };
}
export type Walk = ReturnType<typeof makeWalk>;

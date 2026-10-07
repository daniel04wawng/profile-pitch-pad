import { setCollisionLive, type Collision, type Companion } from "./Stage";
import { saveCollision } from "./store";
import { frontOf } from "./types";
import type { Measure } from "./measure";

// An asset's collision: the patch of floor it takes up (what avatars bump into), set on the
// asset itself so every copy, turn and mirror of it follows. Edited in the café editor (on a
// placed piece) and in the pixel editor (over the art); both write the same thing.
// Coordinates are the art's own pixels; sizes are floor units (8 to a tile, 1 unit = 2px
// across and 1px down).

// what the asset blocks now: its own collision, or the automatic one (the art scripts' foot and
// size, or else read off its pixels)
export function collisionFor(name: string, comps: Record<string, Companion>, measure: Measure | null, wh: { w: number; h: number }, passable = false): { c: Collision; own: boolean } {
  const own = comps[name]?.collision ?? comps[frontOf(name)]?.collision;
  if (own) return { c: own, own: !!comps[name]?.collision };
  const comp = comps[name] ?? comps[frontOf(name)];
  if (comp?.foot && comp.size) return { c: { foot: comp.foot, size: comp.size, walkable: passable }, own: false };
  if (measure) return { c: { foot: { x: measure.fx + 0.5, y: measure.fy + 1 }, size: { a: Math.max(1, (measure.fx - measure.lx) / 2), b: Math.max(1, (measure.rx - measure.fx) / 2), from: "front" }, walkable: passable }, own: false };
  return { c: { foot: { x: wh.w / 2, y: wh.h }, size: { a: 8, b: 8, from: "front" }, walkable: passable }, own: false };
}

export type CollisionChange = { da?: number; db?: number; ma?: number; mb?: number; walkable?: boolean };
// One edit, in what you see. On a mirrored copy the two floor axes swap and left/right flips,
// so the change is turned back into the art's own terms.
export function changed(c: Collision, ch: CollisionChange, flip = false): Collision {
  const [da, db] = flip ? [ch.db ?? 0, ch.da ?? 0] : [ch.da ?? 0, ch.db ?? 0];
  // a step along a (down-right) is 2px right and 1px down; along b, 2px left and 1px down
  const ma = ch.ma ?? 0;
  const mb = ch.mb ?? 0;
  const dx = 2 * (ma - mb);
  const dy = ma + mb;
  return {
    foot: { x: c.foot.x + (flip ? -dx : dx), y: c.foot.y + dy },
    size: { a: Math.max(1, c.size.a + da), b: Math.max(1, c.size.b + db), from: c.size.from },
    ...((ch.walkable ?? c.walkable) ? { walkable: true } : {}),
  };
}

// the floor patch's four corners, in the art's pixels
export function corners(c: Collision): { x: number; y: number }[] {
  const { a: A, b: B, from } = c.size;
  const [a0, a1, b0, b1] = from === "centre" ? [-A / 2, A / 2, -B / 2, B / 2] : from === "back" ? [0, A, 0, B] : [-A, 0, -B, 0];
  const at = (a: number, b: number) => ({ x: c.foot.x + 2 * (a - b), y: c.foot.y + a + b });
  return [at(a0, b0), at(a1, b0), at(a1, b1), at(a0, b1)];
}

// save it (null: back to automatic), live everywhere at once
export async function setAssetCollision(name: string, c: Collision | null) {
  setCollisionLive(name, c);
  await saveCollision(name, c);
}

// a length in floor units as tiles, in quarters: "1 tile", "1¼ tiles"
const tiles = (u: number) => {
  const q = Math.round((u / 8) * 4);
  const whole = Math.floor(q / 4);
  const part = ["", "¼", "½", "¾"][q % 4];
  return `${whole || !part ? whole : ""}${part} tile${q === 4 ? "" : "s"}`;
};

// The controls, the same in both editors.
export function CollisionPanel({
  name,
  c,
  own,
  flip = false,
  onChange,
  onReset,
  btn,
}: {
  name: string;
  c: Collision;
  own: boolean;
  flip?: boolean;
  onChange: (ch: CollisionChange) => void;
  onReset: () => void;
  btn: string;
}) {
  // sizes as you see them (a mirrored copy shows the art's axes swapped)
  const [sa, sb] = flip ? [c.size.b, c.size.a] : [c.size.a, c.size.b];
  const step = (label: string, v: number, da: number, db: number) => (
    <div className="flex items-center gap-1">
      <span className="w-16 opacity-70">{label}</span>
      <button className={btn} onClick={() => onChange({ da: -da, db: -db })}>
        −
      </button>
      <span className="w-16 text-center tabular-nums">{tiles(v)}</span>
      <button className={btn} onClick={() => onChange({ da, db })}>
        +
      </button>
    </div>
  );
  return (
    <div className="space-y-1.5 rounded border border-white/10 p-2 text-[12px]">
      <p className="flex items-center justify-between gap-2">
        <span className="font-medium">collision</span>
        <span className="truncate text-[11px] opacity-60">
          {own ? "set by you" : "automatic"} · every {name}
        </span>
      </p>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={!!c.walkable} onChange={(e) => onChange({ walkable: e.target.checked })} />
        walk through it
      </label>
      {step("↘ length", sa, 2, 0)}
      {step("↙ length", sb, 0, 2)}
      <div className="flex items-center gap-1">
        <span className="w-16 opacity-70">move</span>
        {(
          [
            ["↖", { ma: -1 }],
            ["↗", { mb: -1 }],
            ["↙", { mb: 1 }],
            ["↘", { ma: 1 }],
          ] as const
        ).map(([k, m]) => (
          <button key={k} className={btn} onClick={() => onChange(m)}>
            {k}
          </button>
        ))}
      </div>
      {own && (
        <button className={`${btn} w-full`} onClick={onReset}>
          back to automatic
        </button>
      )}
    </div>
  );
}

export type SpriteDef = {
  id: string;
  file: string;
  x: number;
  y: number;
  w: number;
  h: number;
  // Screen y where the sprite touches the floor. Higher = closer to the viewer = drawn on top.
  baseY: number;
  hotspot: string | null;
  label: string | null;
  hidden?: boolean;
  // Mirror left/right. Lets one asset face either way.
  flipX?: boolean;
};

export type Layout = {
  scene: string;
  width: number;
  height: number;
  assets: SpriteDef[];
  // Isometric floor grid: 2:1 diamond tiles, `tile` px wide, anchored so (ox, oy) is a tile corner.
  grid?: { tile: number; ox: number; oy: number };
};

export const DEFAULT_GRID = { tile: 32, ox: 0, oy: 0 };

// Snap a point to the iso lattice at half-tile resolution (the corners and centers of tiles).
export function snapIso(x: number, y: number, g = DEFAULT_GRID) {
  const sx = g.tile / 4; // half-tile step across
  const sy = g.tile / 8; // half-tile step down
  let m = Math.round((x - g.ox) / sx);
  let n = Math.round((y - g.oy) / sy);
  if ((m + n) % 2 !== 0) {
    // only points with m + n even are on the lattice; pick the nearer neighbour
    const fx = (x - g.ox) / sx - m;
    const fy = (y - g.oy) / sy - n;
    if (Math.abs(fx) * sx > Math.abs(fy) * sy) m += Math.sign(fx) || 1;
    else n += Math.sign(fy) || 1;
  }
  return { x: g.ox + m * sx, y: g.oy + n * sy };
}

export const HOTSPOTS = ["projects", "about", "menu", "now", "contact", "piano", "books", "chill"] as const;

export const BASE = "/cafe/";

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
  // cols x rows = the room's floor size in tiles; the grid is only drawn (and snapped) there.
  grid?: { tile: number; ox: number; oy: number; cols?: number; rows?: number };
  // Optional night layer for the base (lit windows in the buildings), shown as it gets dark.
  sceneNight?: string;
};

export const DEFAULT_GRID: NonNullable<Layout["grid"]> = { tile: 32, ox: 0, oy: 0 };

// Snap a point to the iso lattice at half-tile resolution (the corners and centers of tiles).
export function snapIso(x: number, y: number, g: NonNullable<Layout["grid"]> = DEFAULT_GRID) {
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
  // keep it on the floor: m, n -> tile coords (i along down-right, j along down-left)
  if (g.cols && g.rows) {
    let i = (m + n) / 4;
    let j = (n - m) / 4;
    i = Math.max(0, Math.min(g.cols, i));
    j = Math.max(0, Math.min(g.rows, j));
    m = Math.round(2 * (i - j));
    n = Math.round(2 * (i + j));
  }
  return { x: g.ox + m * sx, y: g.oy + n * sy };
}

export const HOTSPOTS = ["projects", "about", "menu", "now", "contact", "piano", "books", "chill"] as const;

export const BASE = "/cafe/";

// What a freshly placed asset opens, so the furniture works the moment it's moved in.
// Flat things (rugs) lie under everything else.
export const FLAT_ASSETS = new Set(["iso-rug"]);

export const ASSET_DEFAULTS: Record<string, { hotspot: string; label: string }> = {
  "iso-counter": { hotspot: "projects", label: "browse the pastry case" },
  "iso-pastry-case": { hotspot: "projects", label: "browse the pastry case" },
  "iso-bookshelf": { hotspot: "books", label: "books I love" },
  "iso-menu-board": { hotspot: "menu", label: "read the menu" },
  "iso-piano": { hotspot: "piano", label: "play the piano" },
  "iso-record-player": { hotspot: "piano", label: "put on a record" },
  "iso-armchair": { hotspot: "chill", label: "sit and listen" },
  "iso-tip-jar": { hotspot: "contact", label: "say hi" },
  "iso-register": { hotspot: "contact", label: "say hi" },
  // pieces from the original café
  "cafe-pastry-counter": { hotspot: "projects", label: "browse the pastry case" },
  "cafe-piano": { hotspot: "piano", label: "play the piano" },
  "cafe-record-shelf": { hotspot: "books", label: "books + records" },
  "cafe-armchair": { hotspot: "chill", label: "sit and listen" },
  "cafe-menu-board": { hotspot: "menu", label: "read the menu" },
  "cafe-aframe-sign": { hotspot: "now", label: "special of the day" },
  "cafe-till": { hotspot: "contact", label: "say hi" },
  "cafe-espresso-bar": { hotspot: "about", label: "about me" },
};

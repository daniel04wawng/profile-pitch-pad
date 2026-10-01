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

// Things that hang on a wall or from the ceiling. They slide along the wall in grid steps but
// keep whatever height you give them, instead of being snapped down onto the floor.
export const WALL_ASSETS = new Set([
  "window", "wall-lamp", "sax-poster", "chalkboard-menu", "record-art", "framed-picture-tall",
  "kitchen-doorway", "back-bar-shelves", "globe-lamp", "hanging-plant",
]);

// Snap a wall item's foot: along the wall to the half-tile grid, height above the floor line
// to 2px. The wall is picked by which side of the back corner the point is on.
export function snapWall(x: number, y: number, g: NonNullable<Layout["grid"]> = DEFAULT_GRID) {
  const step = g.tile / 4;
  const floorAt = (px: number) => g.oy + Math.abs(px - g.ox) / 2;
  const height = Math.max(0, Math.round((floorAt(x) - y) / 2) * 2);
  const reach = ((g.cols ?? 20) * g.tile) / 2;
  const sx = g.ox + Math.max(-reach, Math.min(reach, Math.round((x - g.ox) / step) * step));
  return { x: sx, y: floorAt(sx) - height };
}

// What a freshly placed asset opens, so the furniture works the moment it's moved in.
// Flat things (rugs) lie under everything else.
export const FLAT_ASSETS = new Set(["iso-rug", "rug"]);

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
  // the original café's pieces, cleaned into standalone assets
  "pastry-counter": { hotspot: "projects", label: "browse the pastry case" },
  "chalkboard-menu": { hotspot: "menu", label: "read the menu" },
  "kitchen-doorway": { hotspot: "now", label: "what's in the oven" },
  "record-art": { hotspot: "piano", label: "my music" },
  "piano": { hotspot: "piano", label: "play the piano" },
  "record-shelf": { hotspot: "books", label: "books + records" },
  "menu-board": { hotspot: "menu", label: "read the menu" },
  "aframe-sign": { hotspot: "now", label: "special of the day" },
  "piano-stool": { hotspot: "piano", label: "play the piano" },
  "cafe-table": { hotspot: "chill", label: "sit for a while" },
  "cafe-chair": { hotspot: "chill", label: "sit for a while" },
  "record-cabinet": { hotspot: "piano", label: "put on a record" },
  "espresso-station": { hotspot: "about", label: "about me" },
  bookshelf: { hotspot: "books", label: "books I love" },
  "special-board": { hotspot: "now", label: "special of the day" },
  booth: { hotspot: "chill", label: "sit for a while" },
  armchair: { hotspot: "chill", label: "sit and listen" },
  "cafe-table-cloth": { hotspot: "chill", label: "sit for a while" },
  "cafe-table-linen": { hotspot: "chill", label: "sit for a while" },
  "cake-stand": { hotspot: "projects", label: "browse the pastry case" },
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

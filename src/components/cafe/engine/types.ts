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
  // Quarter turns (0-3), see turnArt(). `file` and `flipX` are the art for the current turn.
  rot?: number;
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
  // Assets marked as clutter: small things that sit on top of other things (a cup on a table,
  // flowers on the counter). Unset = DEFAULT_CLUTTER. Toggled per asset in the editor.
  clutter?: string[];
  // Where visitors walk in (a point on the floor near its open front edge). Unset = near the
  // front corner. Set it in the editor with "entrance".
  entrance?: { x: number; y: number };
};

// How the asset library is grouped. Clutter-marked assets go under Clutter; anything not
// listed (your own drawings and imports) goes under "Your assets".
export const ASSET_SECTIONS: [string, string[]][] = [
  ["Seating", ["cafe-chair", "armchair", "couch", "sofa-large", "booth", "piano-stool"]],
  ["Tables & counters", ["cafe-table", "cafe-table-cloth", "cafe-table-linen", "coffee-table", "booth-table", "bar-counter", "pastry-counter"]],
  ["Music & books", ["piano", "record-cabinet", "bookshelf"]],
  ["Walls & windows", ["window", "notes-board", "kitchen-doorway", "menu-board", "chalkboard-menu", "back-bar-shelves", "sax-poster", "record-art", "framed-picture-tall", "window-box"]],
  ["Changing", ["wardrobe", "changing-room"]],
  ["Lighting", ["globe-lamp", "wall-lamp", "floor-lamp"]],
  ["Plants", ["potted-plant", "fiddle-leaf-fig", "snake-plant", "fern-stand", "hanging-plant", "tulip-pot"]],
  ["Floor", ["rug", "special-board"]],
];
export function sectionOf(l: Layout, name: string) {
  if (isClutter(l, name)) return "Clutter";
  return ASSET_SECTIONS.find(([, names]) => names.includes(frontOf(name)))?.[0] ?? "Your assets";
}
export const SECTION_ORDER = [...ASSET_SECTIONS.map(([s]) => s), "Clutter", "Your assets"];

export const DEFAULT_CLUTTER = [
  "coffee-cup", "flower-vase", "succulent", "tulip-pot", "laptop", "cake-stand", "espresso-station",
];
export const isClutter = (l: Layout, name: string) => (l.clutter ?? DEFAULT_CLUTTER).includes(frontOf(name));

// Added to image URLs so a fresh editor session never shows a stale copy of art that was
// redrawn while the old one sat in the browser's cache. (Edits made in the session bump
// their own version on top.) In production the art is served with revalidation anyway.
export const BOOT = import.meta.env.DEV ? Date.now() : 0;

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

// Things on a wall or hanging from the ceiling. They slide along the wall in grid steps and
// keep whatever height you give them (doors stay on the floor). `drawnFor` is the wall the art
// was drawn for: dragged onto the other wall, the piece mirrors itself to match.
export const WALL_ITEMS: Record<string, { drawnFor?: "left" | "right"; onFloor?: boolean }> = {
  window: { drawnFor: "right" },
  "sax-poster": { drawnFor: "right" },
  "chalkboard-menu": { drawnFor: "right" },
  "record-art": { drawnFor: "right" },
  "back-bar-shelves": { drawnFor: "right" },
  "window-box": { drawnFor: "right" },
  "menu-board": { drawnFor: "right" },
  "notes-board": { drawnFor: "right" },
  "framed-picture-tall": { drawnFor: "left" },
  "wall-lamp": { drawnFor: "left" },
  "kitchen-doorway": { drawnFor: "left", onFloor: true },
  "changing-room": { drawnFor: "left", onFloor: true },
  "globe-lamp": {},
  "hanging-plant": {},
};

// Snap a wall item's foot: along the wall to the half-tile grid, height above the floor line
// to 2px (or 0 for things that stand on the floor). The wall is the side of the back corner
// the point is on.
export function snapWall(x: number, y: number, g: NonNullable<Layout["grid"]> = DEFAULT_GRID, onFloor = false) {
  const step = g.tile / 4;
  const floorAt = (px: number) => g.oy + Math.abs(px - g.ox) / 2;
  const height = onFloor ? 0 : Math.max(0, Math.round((floorAt(x) - y) / 2) * 2);
  const reach = ((g.cols ?? 20) * g.tile) / 2;
  const sx = g.ox + Math.max(-reach, Math.min(reach, Math.round((x - g.ox) / step) * step));
  return { x: sx, y: floorAt(sx) - height, side: (sx < g.ox ? "left" : "right") as "left" | "right" };
}

// Rotation works the same for every asset: four quarter turns, clockwise.
//   0 facing you, to the left    1 facing away, to the left
//   2 facing away, to the right  3 facing you, to the right
// Turns 1 and 3 are mirrored. Turns 1 and 2 show the asset's back drawing, `<name>-back.png`,
// when it has one; without one they show its front (paint a back in the pixel editor any time).
export const BACK = "-back";
export const frontOf = (name: string) => (name.endsWith(BACK) ? name.slice(0, -BACK.length) : name);
export function turnArt(name: string, rot: number, hasBack: boolean) {
  const r = ((rot % 4) + 4) % 4;
  const away = r === 1 || r === 2;
  return { name: away && hasBack ? frontOf(name) + BACK : frontOf(name), flipX: r === 1 || r === 3 };
}
// Which turn a placed piece is at, for pieces placed before rotation was stored.
export function rotOf(s: Pick<SpriteDef, "file" | "flipX" | "rot">) {
  if (s.rot !== undefined) return s.rot;
  const back = s.file.replace(/\.png$/, "").endsWith(BACK);
  return back ? (s.flipX ? 1 : 2) : s.flipX ? 3 : 0;
}

// A built-in "screen" that isn't text: the changing room, where visitors change their avatar.
export const WARDROBE = "wardrobe";
// Another built-in: the community board, where visitors pin notes and doodles.
export const NOTES = "notes";

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
  "changing-room": { hotspot: WARDROBE, label: "change your look" },
  wardrobe: { hotspot: WARDROBE, label: "change your look" },
  "notes-board": { hotspot: NOTES, label: "leave a note" },
  "bar-counter": { hotspot: "about", label: "about me" },
  "special-board": { hotspot: "now", label: "special of the day" },
  booth: { hotspot: "chill", label: "sit for a while" },
  couch: { hotspot: "chill", label: "sit and listen" },
  "sofa-large": { hotspot: "chill", label: "sit and listen" },
  "coffee-table": { hotspot: "chill", label: "sit for a while" },
  "booth-table": { hotspot: "chill", label: "sit for a while" },
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

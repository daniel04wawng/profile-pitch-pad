import { useEffect, useState } from "react";
import { CafeAvatar, loadCafeAvatar, type Direction, type Motion } from "./rig/cafe-avatar.mjs";
import { BASE } from "./types";
import { cleanColors, MATERIALS, type Colors, type Material } from "./avatar";
import type { Actor } from "./Stage";

// Rigged avatars (the café avatar package): four directions (SE/SW face you, NE/NW face
// away; the W views are the E art mirrored), six actions of eight frames each, drawn at the
// room's own pixel size. Each avatar's sheets load once and are shared; every visitor gets
// their own controller (a Body), so clocks never interfere. The package's runtime does the
// timing and direction mapping; the café draws the frames itself (Stage) so people sort in
// depth with the furniture. Frames are used exactly as authored: never trimmed or resized.

// person/hair: the same person in other hairstyles share a person (the changing room groups them)
// body: which base model it is (man, woman); jacket: "on" or "off" (the same person either way)
export type CatalogEntry = { id: string; label: string; manifest: string; person?: string; hair?: string; body?: string; jacket?: string };
const CATALOG_URL = `${BASE}avatars/catalog.json`;
let catalogLoad: Promise<CatalogEntry[]> | null = null;
export function loadCatalog(): Promise<CatalogEntry[]> {
  catalogLoad ??= fetch(CATALOG_URL, { cache: "no-cache" }) // a new avatar shows up without a hard reload
    .then((r) => (r.ok ? r.json() : { avatars: [] }))
    .then((d) =>
      (Array.isArray(d?.avatars) ? d.avatars : [])
        .filter((a: Partial<CatalogEntry>) => typeof a?.id === "string" && /^[a-z0-9-]{1,32}$/.test(a.id) && typeof a.manifest === "string")
        // the manifest's address is relative to the catalog, so the folder can move as a whole
        .map((a: CatalogEntry) => ({
          id: a.id,
          label: String(a.label ?? a.id).slice(0, 40),
          manifest: new URL(a.manifest, new URL(CATALOG_URL, location.href)).href,
          person: typeof a.person === "string" ? a.person.slice(0, 32) : a.id,
          hair: typeof a.hair === "string" ? a.hair.slice(0, 20) : undefined,
          body: typeof a.body === "string" ? a.body.slice(0, 20) : undefined,
          jacket: a.jacket === "on" || a.jacket === "off" ? a.jacket : undefined,
        })),
    )
    .catch(() => []);
  return catalogLoad;
}
export function useCatalog() {
  const [c, setC] = useState<CatalogEntry[] | null>(null);
  useEffect(() => {
    let alive = true;
    loadCatalog().then((x) => alive && setC(x));
    return () => {
      alive = false;
    };
  }, []);
  return c;
}

// one loaded avatar: its runtime (whose sheets every Body shares) and each clip's sheet URL
export type Rig = { id: string; base: CafeAvatar; urls: Record<string, string>; manifestUrl: string; held?: HTMLImageElement[] }; // held: its decoded sheets, kept
const rigs = new Map<string, Promise<Rig>>();

// What someone has on: a hairstyle and things to wear (layers the avatar's manifest lists), and
// colours. Each different outfit is its own set of sheets, keyed "id|hair|wear|colours".
export type Dress = { hair?: string; wear?: string[]; colors?: Colors };
const word = (v: unknown) => (typeof v === "string" && /^[a-z0-9-]{1,24}$/.test(v) ? v : undefined);
export function cleanDress(d: Partial<Dress> | undefined): Dress {
  return {
    hair: word(d?.hair),
    wear: Array.isArray(d?.wear) ? [...new Set(d.wear.map(word).filter(Boolean) as string[])].sort().slice(0, 4) : undefined,
    colors: cleanColors(d?.colors),
  };
}
export const rigKey = (id: string, dress?: Dress) => {
  const d = cleanDress(dress);
  const c = d.colors ? MATERIALS.filter((m) => d.colors![m]).map((m) => m + d.colors![m]).join(",") : "";
  return [id, d.hair ?? "", (d.wear ?? []).join("+"), c].join("|");
};
export function loadRigKey(key: string): Promise<Rig> {
  const [id, hair, wear, c] = key.split("|");
  const colors: Colors = {};
  for (const part of c ? c.split(",") : []) {
    const m = MATERIALS.find((x) => part.startsWith(x + "#"));
    if (m) colors[m] = part.slice(m.length);
  }
  return loadRig(id, { hair: hair || undefined, wear: wear ? wear.split("+") : undefined, colors });
}

// the avatar as baked (its body sheets), shared by every outfit
const plains = new Map<string, Promise<Rig>>();
function loadPlain(id: string): Promise<Rig> {
  let p = plains.get(id);
  if (!p) {
    p = loadCatalog().then(async (cat) => {
      const e = cat.find((a) => a.id === id);
      if (!e) throw new Error(`no avatar "${id}"`);
      const base = await loadCafeAvatar(e.manifest); // checks every sheet's size and timing
      const urls = Object.fromEntries(Object.entries(base.manifest.animations).map(([k, c]) => [k, new URL(c.sheet, e.manifest).href]));
      return { id, base, urls, manifestUrl: e.manifest };
    });
    p.catch(() => plains.delete(id));
    plains.set(id, p);
  }
  return p;
}

export function loadRig(id: string, dress?: Dress): Promise<Rig> {
  const key = rigKey(id, dress);
  let p = rigs.get(key);
  if (!p) {
    // (an outfit that can't be put together falls back to the model as drawn, never to nothing)
    p = loadPlain(id).then((plain) =>
      dressRig(plain, cleanDress(dress), key).catch((err) => {
        console.warn(`avatar ${key}: couldn't dress it, showing it as drawn`, err);
        return plain;
      }),
    );
    p.catch(() => rigs.delete(key)); // a failed load can be tried again later
    rigs.set(key, p);
  }
  return p;
}

// An avatar in layers (bake_cafe.py): per clip, the body under the hair, the hair, what's worn
// (and what of the hair it hides), and the parts in front (arms, legs), each beside its material
// map (red = material). Stacked here, then recoloured: each material takes the new colour's hue
// and saturation, keeping the art's shading, anchored on its typical brightness (the rule the
// rig's materials.py uses). An avatar baked whole (no layers) only recolours.
type Layers = { hair?: string[]; defaultHair?: string; wear?: string[]; cardinalOnly?: { hair: string[]; wear: string[] } | null };
type Manifest = CafeAvatar["manifest"] & { materials?: { ids: Record<string, number>; refs: Record<string, number>; base?: Partial<Record<Material, string>> }; layers?: Layers };
type Clip = { sheet: string; materialMap?: string; over?: string; overMap?: string };
async function dressRig(plain: Rig, dress: Dress, key: string): Promise<Rig> {
  const manifest = plain.base.manifest as Manifest;
  const layers = manifest.layers;
  const hair = layers ? (dress.hair && layers.hair?.includes(dress.hair) ? dress.hair : layers.defaultHair) : undefined;
  const wear = layers ? (dress.wear ?? []).filter((w) => layers.wear?.includes(w)) : [];
  const colors = manifest.materials ? dress.colors : undefined;
  if (!layers && !colors) return plain;
  // the straight-on directions are drawn in the model's own hair only: in another hairstyle, or
  // with something on, those go and the diagonals stand in (Body.face)
  let dressed = manifest;
  const only = layers?.cardinalOnly;
  if (only && ((hair && !only.hair.includes(hair)) || wear.some((w) => !only.wear.includes(w)))) {
    const directions = Object.fromEntries(Object.entries(manifest.directions).filter(([d]) => d.length === 2));
    dressed = { ...manifest, directions } as Manifest;
  }
  const at = (path: string) => loadImage(new URL(path, plain.manifestUrl).href);
  const targets = new Map<number, { h: number; s: number; v: number; ref: number }>();
  for (const m of MATERIALS) {
    const c = colors?.[m];
    const id = manifest.materials?.ids[m];
    if (!c || !id) continue;
    const [h, s, v] = rgb2hsv(parseInt(c.slice(1, 3), 16) / 255, parseInt(c.slice(3, 5), 16) / 255, parseInt(c.slice(5, 7), 16) / 255);
    targets.set(id, { h, s, v, ref: manifest.materials!.refs[m] ?? 0.5 });
  }
  const sheets: Record<string, HTMLCanvasElement> = {};
  const urls: Record<string, string> = {};
  await Promise.all(
    (Object.entries(manifest.animations) as [string, Clip][]).map(async ([name, clip]) => {
      const body = plain.base.sheets[name] as HTMLImageElement;
      // a clip no direction plays any more (a straight-on view, in another hairstyle): just
      // its body, never its layers (they aren't drawn for it)
      const used = Object.values(dressed.directions).some((d) => (Object.values(d.actions) as string[]).includes(name));
      const w = body.naturalWidth;
      const h = body.naturalHeight;
      const [hairImg, hairMap, worn, hides, over, overMap, bodyMap] = await Promise.all([
        used && hair && layers ? at(`hair/${hair}/${clip.sheet}`) : null,
        used && hair && layers && targets.size ? at(`hair/${hair}/${clip.sheet.replace(/\.png$/, ".mat.png")}`) : null,
        Promise.all((used ? wear : []).map((x) => at(`wear/${x}/${clip.sheet}`))),
        Promise.all((used ? wear : []).map((x) => at(`wear/${x}/${clip.sheet.replace(/\.png$/, ".hide.png")}`))),
        clip.over ? at(clip.over) : null,
        clip.overMap && targets.size ? at(clip.overMap) : null,
        clip.materialMap && targets.size ? at(clip.materialMap) : null,
      ]);
      // the hair, less what's worn over it hides
      const hairOnly = (img: HTMLImageElement | null) => {
        if (!img) return null;
        const c = canvasOf(w, h);
        const g = c.getContext("2d")!;
        g.drawImage(img, 0, 0);
        g.globalCompositeOperation = "destination-out";
        for (const m of hides) g.drawImage(m, 0, 0);
        return c;
      };
      const stack = (parts: (CanvasImageSource | null)[]) => {
        const c = canvasOf(w, h);
        const g = c.getContext("2d", { willReadFrequently: true })!;
        for (const p of parts) if (p) g.drawImage(p, 0, 0);
        return c;
      };
      // worn things are never recoloured: their pixels go on the map as "not a material"
      const blank = (img: HTMLImageElement) => {
        const c = canvasOf(w, h);
        const g = c.getContext("2d")!;
        g.drawImage(img, 0, 0);
        g.globalCompositeOperation = "source-in";
        g.fillStyle = "#000";
        g.fillRect(0, 0, w, h);
        return c;
      };
      const canvas = stack([body, hairOnly(hairImg), ...worn, over]);
      if (targets.size && bodyMap) {
        const map = stack([bodyMap, hairOnly(hairMap), ...worn.map(blank), overMap]);
        const g = canvas.getContext("2d", { willReadFrequently: true })!;
        const px = g.getImageData(0, 0, w, h);
        const ids = map.getContext("2d", { willReadFrequently: true })!.getImageData(0, 0, w, h).data;
        recolourPixels(px.data, ids, targets);
        g.putImageData(px, 0, 0);
      }
      sheets[name] = canvas;
      urls[name] = await new Promise<string>((res) => canvas.toBlob((b) => res(b ? URL.createObjectURL(b) : plain.urls[name]), "image/png"));
    }),
  );
  // every sheet decoded now, before this outfit shows: the stage swaps sheets by address as the
  // avatar turns and changes action, and one that loads only then blinks the avatar out
  const held = await Promise.all(
    Object.values(urls).map((u) => {
      const im = new Image();
      im.src = u;
      return im.decode().then(
        () => im,
        () => im,
      );
    }),
  );
  return { id: key, base: new CafeAvatar(dressed, sheets), urls, manifestUrl: plain.manifestUrl, held };
}
const canvasOf = (w: number, h: number) => Object.assign(document.createElement("canvas"), { width: w, height: h });
function recolourPixels(P: Uint8ClampedArray, ids: Uint8ClampedArray, targets: Map<number, { h: number; s: number; v: number; ref: number }>) {
  for (let i = 0; i < P.length; i += 4) {
    if (!P[i + 3] || !ids[i + 3]) continue;
    const t = targets.get(ids[i]);
    if (!t) continue;
    const [, s, v] = rgb2hsv(P[i] / 255, P[i + 1] / 255, P[i + 2] / 255);
    const pale = t.ref > 0.8; // near-white art (the tee, sneakers): the colour fully, the shading gently
    const nv = pale ? Math.min(1, Math.max(0, t.v + (v - t.ref) * 0.45)) : Math.min(1, (v * t.v) / Math.max(1e-6, t.ref));
    const ns = pale ? t.s : Math.min(1, t.s * (0.6 + 0.4 * Math.min(1.5, s / 0.4)));
    const [r, g, b] = hsv2rgb(t.h, ns, nv);
    P[i] = Math.round(r * 255);
    P[i + 1] = Math.round(g * 255);
    P[i + 2] = Math.round(b * 255);
  }
}
const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error(`couldn't load ${src}`));
    im.src = src;
  });
function rgb2hsv(r: number, g: number, b: number): [number, number, number] {
  const mx = Math.max(r, g, b),
    mn = Math.min(r, g, b),
    d = mx - mn;
  let h = 0;
  if (d) {
    h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    h /= 6;
    if (h < 0) h += 1;
  }
  return [h, mx ? d / mx : 0, mx];
}
function hsv2rgb(h: number, s: number, v: number): [number, number, number] {
  const i = Math.floor(h * 6),
    f = h * 6 - i,
    p = v * (1 - s),
    q = v * (1 - f * s),
    t = v * (1 - (1 - f) * s);
  return ([[v, t, p], [q, v, p], [p, v, t], [p, q, v], [t, p, v], [v, p, q]] as [number, number, number][])[((i % 6) + 6) % 6];
}

// the rig for `id` dressed as `dress`: null while loading, "failed" if it couldn't load (callers
// fall back). While a new outfit is being put together, the last one stays up (never a blank).
export function useRig(id: string | null | undefined, dress?: Dress) {
  const [r, setR] = useState<Rig | "failed" | null>(null);
  const key = id ? rigKey(id, dress) : null;
  useEffect(() => {
    if (!key) return setR(null);
    let alive = true;
    loadRigKey(key).then(
      (x) => alive && setR(x),
      () => alive && setR("failed"),
    );
    return () => {
      alive = false;
    };
  }, [key]);
  return r;
}

// Which way someone faces, from how they move ON SCREEN: down = toward you (S), up = away (N),
// right = E. A purely sideways or purely vertical step keeps the other half as it was.
export function facing(prev: Direction, dx: number, dy: number): Direction {
  if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01) return prev;
  // eight ways, by the screen angle of the step; the floor's diagonals run at about 26.6 degrees
  // (2:1), so a step along one is SE/SW/NE/NW and two arrows together are straight E/W/N/S
  const a = (Math.atan2(dy, dx) * 180) / Math.PI;
  const DIRS: [Direction, number][] = [["E", 0], ["SE", 26.57], ["S", 90], ["SW", 153.43], ["W", 180], ["W", -180], ["NW", -153.43], ["N", -90], ["NE", -26.57]];
  let best = DIRS[0];
  for (const d of DIRS) if (Math.abs(a - d[1]) < Math.abs(a - best[1])) best = d;
  return best[0];
}
// the nearest of the four diagonals (every avatar has those; not every one, or every outfit,
// has the straight ones)
const DIAGONAL: Record<Direction, Direction> = { SE: "SE", SW: "SW", NE: "NE", NW: "NW", S: "SE", N: "NW", E: "SE", W: "SW" };
// the café's older facing flags (back = away from you, flip = mirrored legacy art) as a direction
export const dirOf = (back: boolean, flip: boolean): Direction => `${back ? "N" : "S"}${(back ? !flip : flip) ? "E" : "W"}` as Direction;
export const isDirection = (v: unknown): v is Direction => typeof v === "string" && ["SE", "SW", "NE", "NW", "S", "N", "E", "W"].includes(v);

// seated: a couple of quiet breaths, then a sip of coffee, round and round
const SIP_EVERY = 2; // seated-idle cycles between sips

export type Mode = "stand" | "walk" | "sit-down" | "seated" | "stand-up";

// One visitor's avatar: what it's doing, its own clock, and the frame to draw.
export class Body {
  av: CafeAvatar;
  mode: Mode = "stand";
  private seatedCycles = 0;
  private onUp: (() => void) | null = null;
  constructor(public rig: Rig, dir: Direction = "SE") {
    this.av = new CafeAvatar(rig.base.manifest, rig.base.sheets);
    this.av.setDirection(this.av.manifest.directions?.[dir] ? dir : DIAGONAL[dir]);
    this.av.play("idle");
  }
  get dir() {
    return this.av.direction;
  }
  face(d: Direction) {
    if (!this.av.manifest.directions?.[d]) d = DIAGONAL[d];
    if (d !== this.av.direction) this.av.setDirection(d); // keeps the phase (mid-stride stays mid-stride)
  }
  private to(m: Motion, restart = false) {
    this.av.play(m, { restart });
  }
  // walked `dist` room px this tick: the stride follows the distance, so feet don't slide
  walk(dist: number) {
    if (this.mode === "sit-down" || this.mode === "seated" || this.mode === "stand-up") return;
    if (this.mode !== "walk") {
      this.mode = "walk";
      this.to("walk");
    }
    const curve = this.av.clip.rootMotion;
    const stride = curve ? Math.hypot(...curve[curve.length - 1]) : 22;
    this.av.update((dist / stride) * this.av.durationMs);
  }
  // someone else's walk, `total` px along their path so far: the same phase on every screen
  walkAt(total: number) {
    if (this.mode === "sit-down" || this.mode === "seated" || this.mode === "stand-up") return;
    if (this.mode !== "walk") {
      this.mode = "walk";
      this.to("walk");
    }
    const curve = this.av.clip.rootMotion;
    const stride = curve ? Math.hypot(...curve[curve.length - 1]) : 22;
    this.av.elapsedMs = (total / stride) * this.av.durationMs;
  }
  // someone who sat down `ms` ago (before you arrived): catch their clock up, sips included
  seatedFor(ms: number) {
    this.seated();
    const a = this.av.manifest.animations;
    const sum = (k: keyof typeof a) => a[k].durationMs.reduce((x, y) => x + y, 0);
    const round = SIP_EVERY * sum("seated-idle") + sum("coffee-sip");
    for (let t = Math.max(0, ms) % round; t > 0; t -= 250) this.tick(Math.min(250, t));
  }
  // back on their feet at once (someone else's avatar we lost track of)
  release() {
    if (!this.sitting) return;
    this.mode = "stand";
    this.onUp = null;
    this.to("idle", true);
  }
  stop() {
    if (this.mode !== "walk") return;
    this.mode = "stand";
    this.to("idle", true);
  }
  sit() {
    this.mode = "sit-down";
    this.seatedCycles = 0;
    this.to("sit-down", true);
  }
  // already sitting (someone who was seated before you came in)
  seated() {
    this.mode = "seated";
    this.seatedCycles = 0;
    this.to("seated-idle", true);
  }
  standUp(then?: () => void) {
    if (this.mode === "stand-up") {
      this.onUp = then ?? this.onUp; // already getting up: do this once up instead
      return;
    }
    if (this.mode !== "sit-down" && this.mode !== "seated") return then?.();
    this.mode = "stand-up";
    this.onUp = then ?? null;
    this.to("stand-up", true);
  }
  // advance the clock (not while walking: walking follows distance)
  tick(dtMs: number) {
    if (this.mode === "walk") return;
    const done = this.av.update(Math.max(0, Math.min(dtMs, 500))).justCompleted;
    if (this.mode === "sit-down" && done) {
      this.mode = "seated";
      this.to("seated-idle", true);
    } else if (this.mode === "stand-up" && done) {
      this.mode = "stand";
      this.to("idle", true);
      const f = this.onUp;
      this.onUp = null;
      f?.();
    } else if (this.mode === "seated") {
      // loops: switch at the end of a cycle, where both clips share the same rest frame
      const a = this.av;
      if (a.elapsedMs >= a.durationMs) {
        const sipping = a.action.startsWith("coffee-sip");
        if (sipping) this.to("seated-idle", true);
        else if (++this.seatedCycles >= SIP_EVERY) {
          this.seatedCycles = 0;
          this.to("coffee-sip", true);
        } else a.elapsedMs %= a.durationMs;
      }
    }
  }
  get sitting() {
    return this.mode === "sit-down" || this.mode === "seated" || this.mode === "stand-up";
  }
  // The frame to draw. Standing, its ground point goes at (x, y). Sitting, the sprite's seat
  // point (the manifest's chairSeat) goes on the seat (x, y = the seat's surface).
  actor(id: string, x: number, y: number, z: number): Actor {
    const a = this.av;
    const m = a.manifest;
    const [w, h] = m.frameSize;
    const flip = m.directions[a.direction].flipX;
    const seat = this.sitting ? m.attachments[a.action]?.chairSeat : undefined;
    const [fx, fy] = seat ?? m.anchor;
    return { id, sheet: this.rig.urls[a.action], frame: a.frameIndex, w, h, sheetW: w * a.clip.durationMs.length, footX: fx, footY: fy, x, y, flip, z };
  }
  // where the feet are while seated (to walk up to before sitting, and to stand up from)
  feetFromSeat(seatX: number, seatY: number, dir: Direction): { x: number; y: number } {
    const m = this.av.manifest;
    const act = m.directions[dir].actions["seated-idle"];
    const [sx, sy] = m.attachments[act]?.chairSeat ?? m.anchor;
    const [ax, ay] = m.anchor;
    const flip = m.directions[dir].flipX;
    return { x: seatX + (flip ? -(ax - sx) : ax - sx), y: seatY + (ay - sy) };
  }
}

import { useEffect, useState } from "react";
import { CafeAvatar, loadCafeAvatar, type Direction, type Motion } from "./rig/cafe-avatar.mjs";
import { BASE } from "./types";
import { cleanColors, MATERIALS, type Colors } from "./avatar";
import type { Actor } from "./Stage";

// Rigged avatars (the café avatar package): four directions (SE/SW face you, NE/NW face
// away; the W views are the E art mirrored), six actions of eight frames each, drawn at the
// room's own pixel size. Each avatar's sheets load once and are shared; every visitor gets
// their own controller (a Body), so clocks never interfere. The package's runtime does the
// timing and direction mapping; the café draws the frames itself (Stage) so people sort in
// depth with the furniture. Frames are used exactly as authored: never trimmed or resized.

// person/hair: the same person in other hairstyles share a person (the changing room groups them)
export type CatalogEntry = { id: string; label: string; manifest: string; person?: string; hair?: string; body?: string };
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
export type Rig = { id: string; base: CafeAvatar; urls: Record<string, string>; manifestUrl: string };
const rigs = new Map<string, Promise<Rig>>();

// an avatar in someone's colours is its own set of sheets: keyed "id|skin#aabbcc,hair#..."
export const rigKey = (id: string, colors?: Colors) => {
  const c = cleanColors(colors);
  return c ? `${id}|${MATERIALS.filter((m) => c[m]).map((m) => m + c[m]).join(",")}` : id;
};
export function loadRigKey(key: string): Promise<Rig> {
  const [id, c] = key.split("|");
  const colors: Colors = {};
  for (const part of c ? c.split(",") : []) {
    const m = MATERIALS.find((x) => part.startsWith(x + "#"));
    if (m) colors[m] = part.slice(m.length);
  }
  return loadRig(id, colors);
}

export function loadRig(id: string, colors?: Colors): Promise<Rig> {
  const key = rigKey(id, colors);
  let p = rigs.get(key);
  if (!p) {
    const c = cleanColors(colors);
    p = c
      ? loadRig(id).then((plain) => recolorRig(plain, c, key))
      : loadCatalog().then(async (cat) => {
          const e = cat.find((a) => a.id === id);
          if (!e) throw new Error(`no avatar "${id}"`);
          const base = await loadCafeAvatar(e.manifest); // checks every sheet's size and timing
          const urls = Object.fromEntries(Object.entries(base.manifest.animations).map(([k, c]) => [k, new URL(c.sheet, e.manifest).href]));
          return { id, base, urls, manifestUrl: e.manifest };
        });
    p.catch(() => rigs.delete(key)); // a failed load can be tried again later
    rigs.set(key, p);
  }
  return p;
}

// The avatar recoloured: each sheet beside its material map (<sheet>.mat.png, red = material),
// each material taking the new colour's hue and saturation while keeping the art's shading,
// anchored on the material's typical brightness (manifest.materials.refs). The same rule as the
// rig's materials.py. An avatar without maps is returned as it is.
type Manifest = CafeAvatar["manifest"] & { materials?: { ids: Record<string, number>; refs: Record<string, number> } };
async function recolorRig(plain: Rig, colors: Colors, key: string): Promise<Rig> {
  const manifest = plain.base.manifest as Manifest;
  if (!manifest.materials) return plain;
  const targets = new Map<number, { h: number; s: number; v: number; ref: number }>();
  for (const m of MATERIALS) {
    const c = colors[m];
    const id = manifest.materials.ids[m];
    if (!c || !id) continue;
    const [h, s, v] = rgb2hsv(parseInt(c.slice(1, 3), 16) / 255, parseInt(c.slice(3, 5), 16) / 255, parseInt(c.slice(5, 7), 16) / 255);
    targets.set(id, { h, s, v, ref: manifest.materials.refs[m] ?? 0.5 });
  }
  const sheets: Record<string, HTMLCanvasElement> = {};
  const urls: Record<string, string> = {};
  for (const [name, clip] of Object.entries(manifest.animations) as [string, { sheet: string; materialMap?: string }][]) {
    const img = plain.base.sheets[name] as HTMLImageElement;
    const canvas = document.createElement("canvas");
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const g = canvas.getContext("2d", { willReadFrequently: true })!;
    g.drawImage(img, 0, 0);
    if (clip.materialMap) {
      const map = await loadImage(new URL(clip.materialMap, plain.manifestUrl).href);
      const px = g.getImageData(0, 0, canvas.width, canvas.height);
      g.clearRect(0, 0, canvas.width, canvas.height);
      g.drawImage(map, 0, 0);
      const ids = g.getImageData(0, 0, canvas.width, canvas.height).data;
      const P = px.data;
      for (let i = 0; i < P.length; i += 4) {
        if (!P[i + 3]) continue;
        const t = targets.get(ids[i]);
        if (!t) continue;
        const [, s, v] = rgb2hsv(P[i] / 255, P[i + 1] / 255, P[i + 2] / 255);
        const pale = t.ref > 0.8; // near-white art (the tee, sneakers): the colour fully, the shading gently
        const nv = pale ? Math.min(1, Math.max(0, t.v + (v - t.ref) * 0.45)) : Math.min(1, (v * t.v) / Math.max(1e-6, t.ref));
        const ns = pale ? t.s : Math.min(1, t.s * (0.6 + 0.4 * Math.min(1.5, s / 0.4)));
        const [r, gg, b] = hsv2rgb(t.h, ns, nv);
        P[i] = Math.round(r * 255);
        P[i + 1] = Math.round(gg * 255);
        P[i + 2] = Math.round(b * 255);
      }
      g.putImageData(px, 0, 0);
    }
    sheets[name] = canvas;
    urls[name] = await new Promise<string>((res) => canvas.toBlob((b) => res(b ? URL.createObjectURL(b) : plain.urls[name]), "image/png"));
  }
  return { id: key, base: new CafeAvatar(manifest, sheets), urls, manifestUrl: plain.manifestUrl };
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

// the rig for `id` (in `colors`): null while loading, "failed" if it couldn't load (callers fall back)
export function useRig(id: string | null | undefined, colors?: Colors) {
  const [r, setR] = useState<Rig | "failed" | null>(null);
  const key = id ? rigKey(id, colors) : null;
  useEffect(() => {
    setR(null);
    if (!key || !id) return;
    let alive = true;
    let done = false;
    // in colours: the plain avatar meanwhile (recolouring takes a moment), never a blank
    if (key !== id) loadRig(id).then((x) => alive && !done && setR(x), () => {});
    loadRigKey(key).then(
      (x) => {
        done = true;
        if (alive) setR(x);
      },
      () => alive && setR("failed"),
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return r;
}

// Which way someone faces, from how they move ON SCREEN: down = toward you (S), up = away (N),
// right = E. A purely sideways or purely vertical step keeps the other half as it was.
export function facing(prev: Direction, dx: number, dy: number): Direction {
  const ns = dy > 0.01 ? "S" : dy < -0.01 ? "N" : prev[0];
  const ew = dx > 0.01 ? "E" : dx < -0.01 ? "W" : prev[1];
  return (ns + ew) as Direction;
}
// the café's older facing flags (back = away from you, flip = mirrored legacy art) as a direction
export const dirOf = (back: boolean, flip: boolean): Direction => `${back ? "N" : "S"}${(back ? !flip : flip) ? "E" : "W"}` as Direction;
export const isDirection = (v: unknown): v is Direction => v === "SE" || v === "SW" || v === "NE" || v === "NW";

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
    this.av.setDirection(dir);
    this.av.play("idle");
  }
  get dir() {
    return this.av.direction;
  }
  face(d: Direction) {
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

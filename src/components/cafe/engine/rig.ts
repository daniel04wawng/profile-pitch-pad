import { useEffect, useState } from "react";
import { CafeAvatar, loadCafeAvatar, type Direction, type Motion } from "./rig/cafe-avatar.mjs";
import { BASE } from "./types";
import type { Actor } from "./Stage";

// Rigged avatars (the café avatar package): four directions (SE/SW face you, NE/NW face
// away; the W views are the E art mirrored), six actions of eight frames each, drawn at the
// room's own pixel size. Each avatar's sheets load once and are shared; every visitor gets
// their own controller (a Body), so clocks never interfere. The package's runtime does the
// timing and direction mapping; the café draws the frames itself (Stage) so people sort in
// depth with the furniture. Frames are used exactly as authored: never trimmed or resized.

export type CatalogEntry = { id: string; label: string; manifest: string };
const CATALOG_URL = `${BASE}avatars/catalog.json`;
let catalogLoad: Promise<CatalogEntry[]> | null = null;
export function loadCatalog(): Promise<CatalogEntry[]> {
  catalogLoad ??= fetch(CATALOG_URL, { cache: "no-cache" }) // a new avatar shows up without a hard reload
    .then((r) => (r.ok ? r.json() : { avatars: [] }))
    .then((d) =>
      (Array.isArray(d?.avatars) ? d.avatars : [])
        .filter((a: Partial<CatalogEntry>) => typeof a?.id === "string" && /^[a-z0-9-]{1,32}$/.test(a.id) && typeof a.manifest === "string")
        // the manifest's address is relative to the catalog, so the folder can move as a whole
        .map((a: CatalogEntry) => ({ id: a.id, label: String(a.label ?? a.id).slice(0, 40), manifest: new URL(a.manifest, new URL(CATALOG_URL, location.href)).href })),
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
export type Rig = { id: string; base: CafeAvatar; urls: Record<string, string> };
const rigs = new Map<string, Promise<Rig>>();
export function loadRig(id: string): Promise<Rig> {
  let p = rigs.get(id);
  if (!p) {
    p = loadCatalog().then(async (cat) => {
      const e = cat.find((a) => a.id === id);
      if (!e) throw new Error(`no avatar "${id}"`);
      const base = await loadCafeAvatar(e.manifest); // checks every sheet's size and timing
      const urls = Object.fromEntries(Object.entries(base.manifest.animations).map(([k, c]) => [k, new URL(c.sheet, e.manifest).href]));
      return { id, base, urls };
    });
    p.catch(() => rigs.delete(id)); // a failed load can be tried again later
    rigs.set(id, p);
  }
  return p;
}
// the rig for `id`: null while loading, "failed" if it couldn't load (callers fall back)
export function useRig(id: string | null | undefined) {
  const [r, setR] = useState<Rig | "failed" | null>(null);
  useEffect(() => {
    setR(null);
    if (!id) return;
    let alive = true;
    loadRig(id).then(
      (x) => alive && setR(x),
      () => alive && setR("failed"),
    );
    return () => {
      alive = false;
    };
  }, [id]);
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

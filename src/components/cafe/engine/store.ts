import { BASE, BOOT, frontOf, type Layout } from "./types";
import { SEATS } from "./walk";
import type { Screens } from "./screenData";
import type { Collision } from "./Stage";

// Where a café's files live. Two places:
//  - "disk": the dev server writes straight into public/cafe (how Daniel's café is made).
//  - "browser": your own café, kept in this browser (IndexedDB): its layout, its screens and
//    any pixel art you've drawn or imported (or repainted over a built-in asset). It starts
//    as a copy of Daniel's café. Nothing leaves the browser.
// Every image URL goes through fileUrl, so a browser-saved PNG replaces the built-in one.

export type Where = "disk" | "browser";

const DB = "cafe-mine";
let dbOpen: Promise<IDBDatabase> | null = null;
function db(): Promise<IDBDatabase> {
  dbOpen ??= new Promise((res, rej) => {
    const r = indexedDB.open(DB, 1);
    r.onupgradeneeded = () => {
      r.result.createObjectStore("files"); // path -> PNG blob
      r.result.createObjectStore("docs"); // "layout" | "screens" -> JSON
    };
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
  return dbOpen;
}
async function tx<T>(store: string, mode: IDBTransactionMode, fn: (s: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const d = await db();
  return new Promise((res, rej) => {
    const r = fn(d.transaction(store, mode).objectStore(store));
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}

// browser-saved PNGs, as object URLs (loaded once, before the café draws)
const urls = new Map<string, string>();

export const fileUrl = (file: string, v: number | string = BOOT) => urls.get(file) ?? `${BASE}${file}?v=${v}`;
export const isMine = (file: string) => urls.has(file);

let where: Where = "disk";
export const storage = () => where;

// Collisions you've set on assets in your own café (on top of the café's own, per asset name).
let mineCollisions: Record<string, Collision | null> = {};
export const localCollisions = () => mineCollisions;
// Save an asset's collision (null: back to its automatic one), for every copy of it.
export async function saveCollision(name: string, collision: Collision | null) {
  if (!/^[a-z0-9_-]+$/i.test(name)) throw new Error("bad asset name");
  if (where === "disk") {
    const r = await fetch("/__cafe/collision", { method: "POST", body: JSON.stringify({ name, collision }) });
    if (!r.ok) throw new Error(await r.text());
    return;
  }
  mineCollisions = { ...mineCollisions, [name]: collision };
  await tx("docs", "readwrite", (s) => s.put(mineCollisions, "collisions"));
}

// Tidy a layout from before a rule changed: only seats say "sit" (or open the sit-and-listen
// screen), and the counters and the espresso machine don't open "about me".
const NO_ABOUT = new Set(["bar-counter", "espresso-station", "cafe-espresso-bar"]);
export function tidyLayout(l: Layout): Layout {
  return {
    ...l,
    assets: l.assets.map((a) => {
      const name = frontOf(a.file.replace(/^sprites\//, "").replace(/\.png$/, ""));
      const seat = !!SEATS[name];
      const sits = !seat && (/\bsit\b/i.test(a.label ?? "") || (a.hotspot === "chill" && name !== "record-cabinet"));
      const about = NO_ABOUT.has(name) && a.hotspot === "about";
      return sits || about ? { ...a, hotspot: null, label: null } : a;
    }),
  };
}

// Load a café: Daniel's from the site, or yours from this browser (falling back to his).
export async function openCafe(w: Where): Promise<{ layout: Layout; screens: Screens }> {
  const c = await openCafeRaw(w);
  return { ...c, layout: tidyLayout(c.layout) };
}
async function openCafeRaw(w: Where): Promise<{ layout: Layout; screens: Screens }> {
  where = w;
  const site = async () => {
    const [layout, screens] = await Promise.all([
      fetch(BASE + "layout.json", { cache: "no-store" }).then((r) => r.json() as Promise<Layout>),
      fetch(BASE + "screens.json", { cache: "no-store" }).then((r) => r.json()).then((d) => (d.screens ?? {}) as Screens),
    ]);
    return { layout, screens };
  };
  if (w === "disk") return site();
  try {
    const keys = (await tx("files", "readonly", (s) => s.getAllKeys())) as string[];
    for (const k of keys) {
      const blob = (await tx("files", "readonly", (s) => s.get(k))) as Blob;
      urls.set(k, URL.createObjectURL(blob));
    }
    mineCollisions = ((await tx("docs", "readonly", (s) => s.get("collisions"))) as Record<string, Collision | null> | undefined) ?? {};
    const layout = (await tx("docs", "readonly", (s) => s.get("layout"))) as Layout | undefined;
    const screens = (await tx("docs", "readonly", (s) => s.get("screens"))) as Screens | undefined;
    if (layout && screens) return { layout, screens };
  } catch {
    // no IndexedDB (private window): you can still build, it just won't be kept
  }
  return site();
}

export async function saveCafe(layout: Layout, screens: Screens): Promise<boolean> {
  if (where === "disk") {
    const [r1, r2] = await Promise.all([
      fetch("/__cafe/layout", { method: "POST", body: JSON.stringify(layout) }),
      fetch("/__cafe/screens", { method: "POST", body: JSON.stringify({ screens }) }),
    ]);
    return r1.ok && r2.ok;
  }
  await tx("docs", "readwrite", (s) => s.put(layout, "layout"));
  await tx("docs", "readwrite", (s) => s.put(screens, "screens"));
  return true;
}

// Write a PNG (a data URL) at `file` (a path under public/cafe, like sprites/lamp.png).
export async function writePng(file: string, data: string) {
  if (where === "disk") {
    const r = await fetch("/__cafe/image", { method: "POST", body: JSON.stringify({ file, data }) });
    if (!r.ok) throw new Error(await r.text());
    return;
  }
  const blob = await (await fetch(data)).blob();
  await tx("files", "readwrite", (s) => s.put(blob, file));
  const old = urls.get(file);
  if (old) URL.revokeObjectURL(old);
  urls.set(file, URL.createObjectURL(blob));
}

// Save a photo or video (a bake, a project demo) and return its path (media/<name>). Big
// photos are shrunk to 1600px on their long side first, so the café stays light.
export const MEDIA_TYPES = /^(image\/(jpeg|png|webp|gif)|video\/(mp4|webm))$/;
export async function saveMedia(f: File): Promise<{ src: string; kind: "image" | "video" }> {
  if (!MEDIA_TYPES.test(f.type)) throw new Error(`${f.name}: use a JPEG, PNG, WebP or GIF photo, or an MP4 or WebM video`);
  const kind = f.type.startsWith("video") ? "video" : "image";
  let blob: Blob = f;
  let ext = f.name.split(".").pop()?.toLowerCase() ?? (kind === "video" ? "mp4" : "jpg");
  if (kind === "image" && f.type !== "image/gif") {
    const bmp = await createImageBitmap(f);
    const k = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
    if (k < 1 || f.size > 600_000) {
      const c = document.createElement("canvas");
      c.width = Math.round(bmp.width * k);
      c.height = Math.round(bmp.height * k);
      c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
      const png = f.type === "image/png";
      blob = await new Promise<Blob>((res) => c.toBlob((b) => res(b!), png ? "image/png" : "image/jpeg", 0.86));
      ext = png ? "png" : "jpg";
    }
  }
  const stem = f.name.replace(/\.[^.]+$/, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "media";
  const file = `media/${stem}-${Math.random().toString(36).slice(2, 7)}.${ext}`;
  if (where === "disk") {
    const r = await fetch(`/__cafe/media?file=${encodeURIComponent(file)}`, { method: "POST", body: blob });
    if (!r.ok) throw new Error(await r.text());
  } else {
    await tx("files", "readwrite", (s) => s.put(blob, file));
    urls.set(file, URL.createObjectURL(blob));
  }
  return { src: file, kind };
}

// The dev server only (Daniel's machine): make the café you built in this browser the real
// one, writing its layout, screens, collisions and every drawing or photo it uses into
// public/cafe, exactly as the café editor saves.
export async function publishMineToSite(layout: Layout, screens: Screens) {
  if (!import.meta.env.DEV) throw new Error("only on the dev server");
  const post = async (url: string, body: BodyInit) => {
    const r = await fetch(url, { method: "POST", body });
    if (!r.ok) throw new Error(`${url}: ${await r.text()}`);
  };
  for (const k of (await tx("files", "readonly", (s) => s.getAllKeys())) as string[]) {
    const blob = (await tx("files", "readonly", (s) => s.get(k))) as Blob;
    if (/\.png$/i.test(k) && !k.startsWith("media/")) {
      const data = await new Promise<string>((res) => {
        const fr = new FileReader();
        fr.onload = () => res(fr.result as string);
        fr.readAsDataURL(blob);
      });
      await post("/__cafe/image", JSON.stringify({ file: k, data }));
    } else if (k.startsWith("media/")) await post(`/__cafe/media?file=${encodeURIComponent(k)}`, blob);
  }
  for (const [name, collision] of Object.entries(mineCollisions)) await post("/__cafe/collision", JSON.stringify({ name, collision }));
  await post("/__cafe/layout", JSON.stringify(layout));
  await post("/__cafe/screens", JSON.stringify({ screens }));
}

// Every asset you can place: the built-in sprites, plus your own.
export async function listAssets(): Promise<string[]> {
  if (where === "disk") return (await fetch("/__cafe/assets")).json();
  const built: string[] = await fetch(BASE + "assets.json").then((r) => r.json()).catch(() => []);
  return [...new Set([...built, ...[...urls.keys()].filter((k) => k.startsWith("sprites/"))])].sort();
}

// Start over from Daniel's café (your drawings are kept unless `all`).
export async function resetCafe(all = false) {
  await tx("docs", "readwrite", (s) => s.clear());
  mineCollisions = {};
  if (all) {
    await tx("files", "readwrite", (s) => s.clear());
    urls.forEach((u) => URL.revokeObjectURL(u));
    urls.clear();
  }
}

// Your café as one file (layout, screens and your PNGs), to keep or share; and back.
export async function exportCafe(layout: Layout, screens: Screens): Promise<Blob> {
  const files: Record<string, string> = {};
  for (const [k, u] of urls) {
    const b = await (await fetch(u)).blob();
    files[k] = await new Promise<string>((res) => {
      const fr = new FileReader();
      fr.onload = () => res(fr.result as string);
      fr.readAsDataURL(b);
    });
  }
  return new Blob([JSON.stringify({ cafe: 1, layout, screens, files, collisions: mineCollisions })], { type: "application/json" });
}
export async function importCafe(f: File): Promise<{ layout: Layout; screens: Screens }> {
  const d = JSON.parse(await f.text());
  if (d?.cafe !== 1 || !Array.isArray(d.layout?.assets) || typeof d.screens !== "object") throw new Error("That isn't a café file.");
  for (const [k, v] of Object.entries(d.files ?? {})) {
    if (/^[a-z0-9_\-/]+\.png$/i.test(k) && !k.includes("..") && typeof v === "string" && v.startsWith("data:image/png;base64,")) await writePng(k, v);
    else if (/^media\/[a-z0-9-]+\.(jpg|jpeg|png|webp|gif|mp4|webm)$/i.test(k) && typeof v === "string" && /^data:(image|video)\//.test(v)) {
      const blob = await (await fetch(v)).blob();
      await tx("files", "readwrite", (s) => s.put(blob, k));
      urls.set(k, URL.createObjectURL(blob));
    }
  }
  for (const [k, v] of Object.entries(d.collisions ?? {})) {
    const c = v as Collision | null;
    const ok = c === null || (c && typeof c.foot?.x === "number" && typeof c.foot?.y === "number" && typeof c.size?.a === "number" && typeof c.size?.b === "number");
    if (ok && /^[a-z0-9_-]+$/i.test(k)) await saveCollision(k, c);
  }
  await saveCafe(d.layout, d.screens);
  return { layout: d.layout, screens: d.screens };
}

import { BASE, BOOT, type Layout } from "./types";
import type { Screens } from "./screenData";

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

// Load a café: Daniel's from the site, or yours from this browser (falling back to his).
export async function openCafe(w: Where): Promise<{ layout: Layout; screens: Screens }> {
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

// Every asset you can place: the built-in sprites, plus your own.
export async function listAssets(): Promise<string[]> {
  if (where === "disk") return (await fetch("/__cafe/assets")).json();
  const built: string[] = await fetch(BASE + "assets.json").then((r) => r.json()).catch(() => []);
  return [...new Set([...built, ...[...urls.keys()].filter((k) => k.startsWith("sprites/"))])].sort();
}

// Start over from Daniel's café (your drawings are kept unless `all`).
export async function resetCafe(all = false) {
  await tx("docs", "readwrite", (s) => s.clear());
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
  return new Blob([JSON.stringify({ cafe: 1, layout, screens, files })], { type: "application/json" });
}
export async function importCafe(f: File): Promise<{ layout: Layout; screens: Screens }> {
  const d = JSON.parse(await f.text());
  if (d?.cafe !== 1 || !Array.isArray(d.layout?.assets) || typeof d.screens !== "object") throw new Error("That isn't a café file.");
  for (const [k, v] of Object.entries(d.files ?? {})) {
    if (/^[a-z0-9_\-/]+\.png$/i.test(k) && !k.includes("..") && typeof v === "string" && v.startsWith("data:image/png;base64,")) await writePng(k, v);
  }
  await saveCafe(d.layout, d.screens);
  return { layout: d.layout, screens: d.screens };
}

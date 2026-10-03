import { BASE } from "./types";

// Visitors' avatars. The art (art/draw_avatar.py) is drawn in layers with KEY colours; here a
// visitor's look picks a hairstyle and a palette, the layers are recoloured and outlined into
// one sprite sheet, and the look is remembered in this browser.

export const FRAME = { w: 20, h: 40 };
// where the avatar stands, within a frame
export const FOOT = { x: 10, y: 35 };
// in the sitting frames, how far the seat of the trousers is above the foot point
export const SIT_SEAT = 3;
export const FRAMES = ["front", "front-a", "front-b", "back", "back-a", "back-b", "front-sit", "back-sit"] as const;
export const STYLES = ["messy", "long", "bun", "curly", "buzz"] as const;

type Ramp = [string, string, string];
export const SKINS: Ramp[] = [
  ["#965c3e", "#be7e58", "#d6986e"], // Daniel
  ["#5e3a26", "#80503a", "#9c6a4c"],
  ["#8d5536", "#b0704a", "#cc8c62"],
  ["#b07a52", "#cf9a70", "#e6b88e"],
  ["#d9a47e", "#ecc29c", "#f8dcbc"],
  ["#e6b896", "#f4d2b4", "#fde8d4"],
];
export const HAIRS: Ramp[] = [
  ["#2e1e16", "#543a2a", "#7a5a42"], // Daniel
  ["#1c1418", "#2e2228", "#463640"],
  ["#2e1c12", "#4a2e1c", "#6a4428"],
  ["#6a3418", "#94502a", "#bc7040"],
  ["#a8682c", "#d09040", "#ecb868"],
  ["#c8a058", "#e8c880", "#f8e4b0"],
  ["#6e6e78", "#9a9aa4", "#c8c8d0"],
  ["#2c3a5c", "#405684", "#6078ac"],
  ["#7a3048", "#a84a66", "#d06c88"],
];
export const SHIRTS: Ramp[] = [
  ["#28282c", "#3a3a40", "#4e4e56"], // Daniel: charcoal tee
  ["#46522c", "#647538", "#8a9a4e"],
  ["#6e2c1a", "#94402a", "#b85a3a"],
  ["#2c3463", "#46508a", "#6a74b0"],
  ["#c8aa78", "#e2c898", "#f4e2c0"],
  ["#5a2e46", "#7e4462", "#a46284"],
  ["#2a5450", "#3c726c", "#5a948c"],
  ["#a8682c", "#d09040", "#ecb868"],
  ["#3a2a22", "#54402e", "#74583e"],
];
export const PANTS: [string, string][] = [
  ["#1e1618", "#2e2224"], // Daniel: black
  ["#2a2632", "#423c4c"],
  ["#2c3a52", "#405274"],
  ["#4a3626", "#6a4c34"],
  ["#5a5446", "#7a7260"],
];
const SHOE = "#b0acb2"; // grey sneakers (soles are drawn white)
const APRON: Ramp = ["#28463a", "#3a604e", "#527e68"];
const OUTLINE: [number, number, number] = [36, 20, 13];

export type Look = { style: number; skin: number; hair: number; shirt: number; pants: number };

// The barista is Daniel, and always looks like him: messy brown hair, tan skin, charcoal tee,
// black trousers, grey sneakers (index 0 of each palette is his).
export const DANIEL: Look = { style: 0, skin: 0, hair: 0, shirt: 0, pants: 0 };

const pick = (n: number) => Math.floor(Math.random() * n);
const pickNotDaniel = (n: number) => 1 + pick(n - 1); // index 0 is Daniel's
export const randomLook = (): Look => ({
  style: pick(STYLES.length),
  skin: pick(SKINS.length),
  hair: pickNotDaniel(HAIRS.length),
  shirt: pickNotDaniel(SHIRTS.length),
  pants: pick(PANTS.length),
});

const LOOK_KEY = "cafe-look";
export function savedLook(): Look {
  try {
    const raw = localStorage.getItem(LOOK_KEY);
    if (raw) {
      const l = JSON.parse(raw) as Look;
      if ([l.style, l.skin, l.hair, l.shirt, l.pants].every((n) => Number.isInteger(n) && n >= 0)) return l;
    }
  } catch {
    // private window or blocked storage: a fresh look each visit is fine
  }
  const l = randomLook();
  saveLook(l);
  return l;
}
export function saveLook(l: Look) {
  try {
    localStorage.setItem(LOOK_KEY, JSON.stringify(l));
  } catch {
    // ignore
  }
}

// The café recognises its barista (Daniel) on this browser once he's opened the private link
// (/cafe?barista=<code>); in the dev server it's always him. It only changes how his avatar
// looks and where he starts, so a client-side flag is enough.
const BARISTA_KEY = "cafe-barista";
export function isBarista(): boolean {
  if (import.meta.env.DEV) return true;
  try {
    const code = new URLSearchParams(location.search).get("barista");
    const want = import.meta.env.VITE_BARISTA_CODE as string | undefined;
    if (code && want && code === want) localStorage.setItem(BARISTA_KEY, "1");
    return localStorage.getItem(BARISTA_KEY) === "1";
  } catch {
    return false;
  }
}

const hex = (c: string): [number, number, number] => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16)) as [number, number, number];

let metaKeys: Record<string, string> | null = null;
const images = new Map<string, Promise<HTMLImageElement>>();
function load(src: string) {
  let p = images.get(src);
  if (!p) {
    p = new Promise((res, rej) => {
      const img = new Image();
      img.onload = () => res(img);
      img.onerror = rej;
      img.src = src;
    });
    images.set(src, p);
  }
  return p;
}

const sheets = new Map<string, Promise<string>>();
// One recoloured, outlined sheet (all 8 frames side by side) as a data URL, cached per look.
export function avatarSheet(look: Look, barista = false): Promise<string> {
  const id = JSON.stringify([look, barista]);
  let p = sheets.get(id);
  if (!p) {
    p = build(look, barista);
    sheets.set(id, p);
  }
  return p;
}

async function build(look: Look, barista: boolean) {
  metaKeys ??= (await (await fetch(`${BASE}avatar/meta.json`)).json()).keys as Record<string, string>;
  const layers = [`${BASE}avatar/body.png`, `${BASE}avatar/hair-${STYLES[look.style % STYLES.length]}.png`];
  if (barista) layers.push(`${BASE}avatar/apron.png`);
  const imgs = await Promise.all(layers.map(load));
  const w = imgs[0].width;
  const h = imgs[0].height;
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  for (const im of imgs) ctx.drawImage(im, 0, 0);
  const data = ctx.getImageData(0, 0, w, h);
  const d = data.data;

  const skin = SKINS[look.skin % SKINS.length];
  const hair = HAIRS[look.hair % HAIRS.length];
  const shirt = SHIRTS[look.shirt % SHIRTS.length];
  const pants = PANTS[look.pants % PANTS.length];
  const colours: Record<string, string> = {
    skin0: skin[0], skin1: skin[1], skin2: skin[2],
    hair0: hair[0], hair1: hair[1], hair2: hair[2],
    shirt0: shirt[0], shirt1: shirt[1], shirt2: shirt[2],
    pants0: pants[0], pants1: pants[1], shoe: SHOE,
    apron0: APRON[0], apron1: APRON[1], apron2: APRON[2],
  };
  const swap = new Map<number, [number, number, number]>();
  for (const [k, key] of Object.entries(metaKeys)) {
    const [r, g, b] = hex(key);
    if (colours[k]) swap.set((r << 16) | (g << 8) | b, hex(colours[k]));
  }
  for (let i = 0; i < d.length; i += 4) {
    if (!d[i + 3]) continue;
    const to = swap.get((d[i] << 16) | (d[i + 1] << 8) | d[i + 2]);
    if (to) [d[i], d[i + 1], d[i + 2]] = to;
  }
  // 1px dark outline around the whole figure, kept within each frame
  const solid = (x: number, y: number) => x >= 0 && y >= 0 && x < w && y < h && d[(y * w + x) * 4 + 3] > 0;
  const out = new Uint8ClampedArray(d);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (solid(x, y)) continue;
      const f = Math.floor(x / FRAME.w);
      const near = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => Math.floor((x + dx) / FRAME.w) === f && solid(x + dx, y + dy));
      if (near) {
        const i = (y * w + x) * 4;
        [out[i], out[i + 1], out[i + 2], out[i + 3]] = [...OUTLINE, 255];
      }
    }
  }
  ctx.putImageData(new ImageData(out, w, h), 0, 0);
  return c.toDataURL("image/png");
}

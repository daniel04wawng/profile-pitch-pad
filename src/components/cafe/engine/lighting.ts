// Time of day for the café. It runs on Daniel's clock (San Francisco), not the visitor's,
// and drives everything the light touches: the sky in the windows, sun patches on the
// floor, the room's color cast, and whether lamps glow.

export function pacificHour(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    hour: "numeric",
    minute: "numeric",
    hourCycle: "h23",
  }).formatToParts(date);
  const h = Number(parts.find((p) => p.type === "hour")?.value ?? 12);
  const m = Number(parts.find((p) => p.type === "minute")?.value ?? 0);
  return h + m / 60;
}

export function formatHour(hour: number) {
  const h = Math.floor(hour) % 24;
  const m = Math.floor((hour % 1) * 60);
  return `${h % 12 === 0 ? 12 : h % 12}:${String(m).padStart(2, "0")}${h < 12 ? "am" : "pm"}`;
}

export function phaseName(hour: number) {
  if (hour < 5.5 || hour >= 20.5) return "night";
  if (hour < 9) return "morning";
  if (hour < 16.5) return "day";
  if (hour < 19) return "golden hour";
  return "evening";
}

export type Light = {
  skyTop: string;
  skyBottom: string;
  tint: string; // multiplied over the whole room
  tintAlpha: number;
  sun: number; // 0..1 strength of the sun patches through windows
  sunColor: string;
  lamps: number; // 0..1 how bright lamps glow
  stars: number; // 0..1
};

type Key = [hour: number, light: Light];

const NIGHT: Light = { skyTop: "#0e1230", skyBottom: "#27305a", tint: "#3a3f7a", tintAlpha: 0.55, sun: 0, sunColor: "#9fb3ff", lamps: 1, stars: 1 };
const KEYS: Key[] = [
  [0, NIGHT],
  [5, NIGHT],
  [6.5, { skyTop: "#5b6aa6", skyBottom: "#f2b48a", tint: "#c9a0b4", tintAlpha: 0.25, sun: 0.35, sunColor: "#ffd2a8", lamps: 0.6, stars: 0.2 }],
  [8.5, { skyTop: "#8ec5ea", skyBottom: "#f6dcb8", tint: "#ffe2c0", tintAlpha: 0.08, sun: 0.75, sunColor: "#fff0d0", lamps: 0.1, stars: 0 }],
  [12, { skyTop: "#7cc0ee", skyBottom: "#cfeaf7", tint: "#ffffff", tintAlpha: 0, sun: 0.9, sunColor: "#fff6e0", lamps: 0, stars: 0 }],
  [16.5, { skyTop: "#86bde6", skyBottom: "#f3dcb4", tint: "#ffe6c4", tintAlpha: 0.08, sun: 0.85, sunColor: "#ffe7bf", lamps: 0.1, stars: 0 }],
  [18.6, { skyTop: "#e48a5a", skyBottom: "#f7c27a", tint: "#ff9d5c", tintAlpha: 0.22, sun: 0.8, sunColor: "#ffb36b", lamps: 0.55, stars: 0 }],
  [20, { skyTop: "#2c2a5c", skyBottom: "#a0587a", tint: "#6a4f8a", tintAlpha: 0.42, sun: 0.1, sunColor: "#c88ab0", lamps: 0.9, stars: 0.5 }],
  [21.5, NIGHT],
  [24, NIGHT],
];

const hex = (c: string) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
const mixColor = (a: string, b: string, t: number) =>
  "#" + hex(a).map((v, i) => Math.round(v + (hex(b)[i] - v) * t).toString(16).padStart(2, "0")).join("");
const mix = (a: number, b: number, t: number) => a + (b - a) * t;

export function lightAt(hour: number): Light {
  const h = ((hour % 24) + 24) % 24;
  let i = 0;
  while (i < KEYS.length - 2 && KEYS[i + 1][0] <= h) i++;
  const [h0, a] = KEYS[i];
  const [h1, b] = KEYS[i + 1];
  const t = h1 === h0 ? 0 : (h - h0) / (h1 - h0);
  return {
    skyTop: mixColor(a.skyTop, b.skyTop, t),
    skyBottom: mixColor(a.skyBottom, b.skyBottom, t),
    tint: mixColor(a.tint, b.tint, t),
    tintAlpha: mix(a.tintAlpha, b.tintAlpha, t),
    sun: mix(a.sun, b.sun, t),
    sunColor: mixColor(a.sunColor, b.sunColor, t),
    lamps: mix(a.lamps, b.lamps, t),
    stars: mix(a.stars, b.stars, t),
  };
}

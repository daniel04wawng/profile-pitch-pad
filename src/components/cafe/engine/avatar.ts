import { useEffect, useState } from "react";
import { BASE, BOOT } from "./types";
import type { Actor } from "./Stage";

// The café's people. Each character is a sprite sheet of named poses (imported from generated
// pose sheets by art/import_people.py into public/cafe/people/): walking toward you and away
// (4 frames each), standing, sitting, sipping, sitting seen from behind. 'front' poses face the
// viewer's left and 'back' poses face away to the right; the other two directions are mirrors.
// Standing and walking frames meet the floor at the anchor; seated frames meet the seat there.

export type CharacterMeta = { frame: [number, number]; anchor: [number, number]; frames: string[] };
export type People = { standHeight: number; characters: Record<string, CharacterMeta> };
export type Pose =
  | "walk-front-1" | "walk-front-2" | "walk-front-3" | "walk-front-4"
  | "walk-back-1" | "walk-back-2" | "walk-back-3" | "walk-back-4"
  | "stand-front" | "stand-back" | "sit-front" | "sit-sip" | "sit-back";

// The barista is Daniel. Visitors are any of the others.
export const BARISTA_CHARACTER = "olive";

export type Look = { character: string };

let peopleLoad: Promise<People> | null = null;
export function loadPeople(): Promise<People> {
  peopleLoad ??= fetch(`${BASE}people/people.json?v=${BOOT}`, { cache: "no-store" })
    .then((r) => r.json() as Promise<People>)
    .catch(() => ({ standHeight: 58, characters: {} }));
  return peopleLoad;
}
export function usePeople(): People | null {
  const [p, setP] = useState<People | null>(null);
  useEffect(() => {
    let alive = true;
    loadPeople().then((x) => alive && setP(x));
    return () => {
      alive = false;
    };
  }, []);
  return p;
}

export const sheetOf = (character: string) => `${BASE}people/${character}.png?v=${BOOT}`;
export const visitorCharacters = (p: People) => Object.keys(p.characters).filter((c) => c !== BARISTA_CHARACTER);

// a walking frame: four steps per stride
export const walkPose = (back: boolean, t: number, stepMs = 130): Pose =>
  `walk-${back ? "back" : "front"}-${(Math.floor(t / stepMs) % 4) + 1}` as Pose;
// sitting facing you, a sip of coffee now and then (every ~7s, for ~1.4s), offset per person
export const sitPose = (back: boolean, t: number, seed = 0): Pose =>
  back ? "sit-back" : (t + seed * 977) % 7000 < 1400 ? "sit-sip" : "sit-front";

// An actor (for the Stage) showing `character` in `pose`, standing (or sitting) at x, y.
export function poseActor(p: People, id: string, character: string, pose: Pose, x: number, y: number, flip: boolean, z: number): Actor | null {
  const m = p.characters[character];
  if (!m) return null;
  const i = m.frames.indexOf(pose);
  return { id, sheet: sheetOf(character), frame: Math.max(0, i), w: m.frame[0], h: m.frame[1], footX: m.anchor[0], footY: m.anchor[1], x, y, flip, z };
}

const LOOK_KEY = "cafe-look";
export function savedLook(p: People): Look {
  const all = visitorCharacters(p);
  try {
    const raw = localStorage.getItem(LOOK_KEY);
    const l = raw ? (JSON.parse(raw) as Partial<Look>) : null;
    if (l && typeof l.character === "string" && all.includes(l.character)) return { character: l.character };
  } catch {
    // private window or blocked storage: a fresh look each visit is fine
  }
  const l = { character: all[Math.floor(Math.random() * all.length)] ?? BARISTA_CHARACTER };
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
// looks, so a client-side flag is enough for now.
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

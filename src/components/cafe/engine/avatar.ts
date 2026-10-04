import { useEffect, useState } from "react";
import { BASE, BOOT } from "./types";
import type { Actor } from "./Stage";

// The café's people. Each character is a sprite sheet of named poses (imported from generated
// pose sheets by art/import_people.py into public/cafe/people/): walking toward you and away
// (4 frames each), standing, sitting, sipping, sitting seen from behind. 'front' poses face the
// viewer's left and 'back' poses face away to the right; the other two directions are mirrors.
// Standing and walking frames meet the floor at the anchor; seated frames meet the seat there.

export type CharacterMeta = { frame: [number, number]; anchor: [number, number]; frames: string[] };
// people: person -> their outfits; characters: "person/outfit" -> that sheet's frames
// density: sprite pixels per room pixel (people are drawn finer than the room, for faces)
export type People = { standHeight: number; density?: number; people: Record<string, string[]>; characters: Record<string, CharacterMeta> };
export type Pose =
  | "walk-front-1" | "walk-front-2" | "walk-front-3" | "walk-front-4"
  | "walk-back-1" | "walk-back-2" | "walk-back-3" | "walk-back-4"
  | "stand-front" | "stand-back" | "sit-front" | "sit-sip" | "sit-back";

// The barista is Daniel (always this person, in any of his outfits). Visitors are the others.
export const BARISTA_PERSON = "olive";

// who you are (skin, hair: the person) and what you're wearing
export type Look = { person: string; outfit: string };
export const keyOf = (l: Look) => `${l.person}/${l.outfit}`;

let peopleLoad: Promise<People> | null = null;
export function loadPeople(): Promise<People> {
  peopleLoad ??= fetch(`${BASE}people/people.json?v=${BOOT}`, { cache: "no-store" })
    .then((r) => r.json() as Promise<People>)
    .catch(() => ({ standHeight: 58, people: {}, characters: {} }));
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

export const sheetOf = (key: string) => `${BASE}people/${key.replace("/", "--")}.png?v=${BOOT}`;
export const visitorPeople = (p: People) => Object.keys(p.people).filter((x) => x !== BARISTA_PERSON);
export const isLook = (p: People, l: Partial<Look> | null | undefined): l is Look =>
  !!l && typeof l.person === "string" && typeof l.outfit === "string" && !!p.people[l.person]?.includes(l.outfit);
export const firstOutfit = (p: People, person: string) => p.people[person]?.[0] ?? "original";

// a walking frame: four steps per stride
export const walkPose = (back: boolean, t: number, stepMs = 105): Pose =>
  `walk-${back ? "back" : "front"}-${(Math.floor(t / stepMs) % 4) + 1}` as Pose;
// sitting facing you, a sip of coffee now and then (every ~7s, for ~1.4s), offset per person
export const sitPose = (back: boolean, t: number, seed = 0): Pose =>
  back ? "sit-back" : (t + seed * 977) % 7000 < 1400 ? "sit-sip" : "sit-front";

// An actor (for the Stage) showing `look` in `pose`, standing (or sitting) at x, y.
export function poseActor(p: People, id: string, look: Look, pose: Pose, x: number, y: number, flip: boolean, z: number): Actor | null {
  const key = keyOf(look);
  const m = p.characters[key];
  if (!m) return null;
  const i = m.frames.indexOf(pose);
  const d = p.density ?? 1; // everything below in room pixels
  return {
    id, sheet: sheetOf(key), frame: Math.max(0, i),
    w: m.frame[0] / d, h: m.frame[1] / d, footX: m.anchor[0] / d, footY: m.anchor[1] / d,
    sheetW: (m.frame[0] * m.frames.length) / d,
    x, y, flip, z,
  };
}
// a character's frame size in room pixels
export const roomSize = (p: People, key: string): [number, number] => {
  const m = p.characters[key];
  const d = p.density ?? 1;
  return m ? [m.frame[0] / d, m.frame[1] / d] : [30, 60];
};

const LOOK_KEY = "cafe-look";
// Your look as last chosen in this browser (the barista: Daniel, in his last outfit).
export function savedLook(p: People, barista: boolean): Look {
  let l: Partial<Look> | null = null;
  try {
    l = JSON.parse(localStorage.getItem(LOOK_KEY) ?? "null");
  } catch {
    // private window or blocked storage: a fresh look each visit is fine
  }
  if (barista) return isLook(p, l) && l.person === BARISTA_PERSON ? l : { person: BARISTA_PERSON, outfit: firstOutfit(p, BARISTA_PERSON) };
  if (isLook(p, l) && l.person !== BARISTA_PERSON) return l;
  const all = visitorPeople(p);
  const person = all[Math.floor(Math.random() * all.length)] ?? BARISTA_PERSON;
  const pick = p.people[person] ?? ["original"];
  const look = { person, outfit: pick[Math.floor(Math.random() * pick.length)] };
  saveLook(look);
  return look;
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

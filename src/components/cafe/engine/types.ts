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
};

export type Layout = {
  scene: string;
  width: number;
  height: number;
  assets: SpriteDef[];
};

export const HOTSPOTS = ["projects", "about", "menu", "now", "contact", "piano", "books", "chill"] as const;

export const BASE = "/cafe/";

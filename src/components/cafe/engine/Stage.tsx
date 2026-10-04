import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { fileUrl } from "./store";
import { Fragment } from "react";
import { BASE, BOOT, DEFAULT_GRID, type Layout, type SpriteDef } from "./types";
import type { Light } from "./lighting";

// Extra info drawn alongside some sprites (art/draw_props.py): window sky masks, sun patches,
// lamp glow points, and `foot`, the point that stands on the floor grid (an iso piece's front
// corner, a round piece's centre), so the editor can snap it exactly.
export type Companion = {
  foot?: { x: number; y: number };
  // floor the piece covers, in grid units, measured from its foot (front corner, back corner or centre)
  size?: { a: number; b: number; from: "front" | "back" | "centre" };
  sky?: string;
  light?: { file: string; dx: number; dy: number; w: number; h: number };
  glow?: { x: number; y: number; r: number };
};
export type Actor = {
  id: string;
  sheet: string; // sprite sheet (data URL), frames side by side
  frame: number;
  w: number;
  h: number;
  sheetW?: number; // the whole sheet's width (room px), when drawn finer than the room
  footX: number; // where it stands, within a frame
  footY: number;
  x: number; // where it stands, in the scene
  y: number;
  flip: boolean;
  z: number; // drawn above sprites whose floor point is lower than this
  opacity?: number; // fading in as they arrive
};
let companionsCache: Promise<Record<string, Companion>> | null = null;
export function useCompanions() {
  const [c, setC] = useState<Record<string, Companion>>({});
  useEffect(() => {
    companionsCache ??= fetch(`${BASE}sprites/_companions.json`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : {}))
      .catch(() => ({}));
    companionsCache.then(setC);
  }, []);
  return c;
}
export const assetName = (file: string) => file.replace(/^sprites\//, "").replace(/\.png$/, "");
const maskStyle = (url: string): React.CSSProperties => ({
  WebkitMaskImage: `url(${url})`,
  maskImage: `url(${url})`,
  WebkitMaskSize: "100% 100%",
  maskSize: "100% 100%",
});

// Alpha masks so clicks land on the actual drawn pixels, not the sprite's bounding box.
// Shared with the editor (opaqueAt) so clutter can tell what it's sitting on.
const MASKS = new Map<string, { w: number; data: Uint8ClampedArray }>();
export function opaqueAt(s: SpriteDef, p: { x: number; y: number }, versions: Record<string, number> = {}) {
  const rx = Math.floor(p.x - s.x);
  const lx = s.flipX ? s.w - 1 - rx : rx;
  const ly = Math.floor(p.y - s.y);
  if (lx < 0 || ly < 0 || lx >= s.w || ly >= s.h) return false;
  const m = MASKS.get(`${s.file}?v=${versions[s.file] ?? BOOT}`);
  return !m || m.data[(ly * m.w + lx) * 4 + 3] > 0;
}
function useAlphaMasks(layout: Layout | null, versions: Record<string, number>) {
  const [masks, setMasks] = useState<Record<string, { w: number; data: Uint8ClampedArray }>>({});
  useEffect(() => {
    if (!layout) return;
    let alive = true;
    layout.assets.forEach((s) => {
      const key = `${s.file}?v=${versions[s.file] ?? BOOT}`;
      if (masks[key]) return;
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = img.width;
        c.height = img.height;
        const ctx = c.getContext("2d")!;
        ctx.drawImage(img, 0, 0);
        const data = ctx.getImageData(0, 0, img.width, img.height).data;
        MASKS.set(key, { w: img.width, data });
        if (alive) setMasks((m) => ({ ...m, [key]: { w: img.width, data } }));
      };
      img.src = fileUrl(s.file, versions[s.file] ?? BOOT);
    });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layout?.assets.length, JSON.stringify(versions)]);
  return masks;
}

export type StageHandlers = {
  onHover?: (s: SpriteDef | null) => void;
  onPointerDown?: (s: SpriteDef | null, scene: { x: number; y: number }, e: ReactPointerEvent) => void;
  onPointerMove?: (scene: { x: number; y: number }, e: ReactPointerEvent) => void;
  onPointerUp?: (e: ReactPointerEvent) => void;
  // Something dragged in (a library asset or an image file) was dropped at this scene point.
  onDrop?: (e: React.DragEvent, scene: { x: number; y: number }) => void;
};

export function Stage({
  layout,
  interactive,
  hovered,
  selected,
  showBackground = true,
  showOutlines = false,
  showGrid = false,
  versions = {},
  marker = null,
  camera = null,
  light = null,
  handlers,
  actors = [],
  children,
}: {
  layout: Layout;
  // Which sprites respond to the pointer (play mode: hotspots only, edit mode: all).
  interactive: (s: SpriteDef) => boolean;
  hovered: string | null;
  selected?: string | null;
  showBackground?: boolean;
  showOutlines?: boolean;
  showGrid?: boolean;
  // Bumped after a pixel edit so the browser reloads that PNG instead of using its cache.
  versions?: Record<string, number>;
  // Floor tile to highlight (scene point at a tile's center), e.g. where a dragged object will land.
  marker?: { x: number; y: number } | null;
  // Scene rect to glide the camera into (walking up to an object). null = whole room.
  camera?: { x: number; y: number; w: number; h: number } | null;
  // Time-of-day lighting; null draws the room flat (no sky, sun or lamps).
  light?: Light | null;
  handlers: StageHandlers;
  // People in the room (avatars), drawn among the furniture by where they stand.
  actors?: Actor[];
  children?: React.ReactNode;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({ w: window.innerWidth, h: window.innerHeight });
  const masks = useAlphaMasks(layout, versions);
  const companions = useCompanions();
  const src = (file: string) => fileUrl(file, versions[file] ?? BOOT);

  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setBox({ w: e.contentRect.width, h: e.contentRect.height }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Whole-number scaling keeps every art pixel the same size; below 2x we allow fractions so phones still fit.
  const fit = Math.min(box.w / layout.width, box.h / layout.height);
  const scale = fit >= 2 ? Math.floor(fit) : fit;
  const ox = Math.round((box.w - layout.width * scale) / 2);
  const oy = Math.round((box.h - layout.height * scale) / 2);

  const g = layout.grid ?? DEFAULT_GRID;
  const ordered = useMemo(() => [...layout.assets].sort((a, b) => a.baseY - b.baseY), [layout.assets]);

  // Camera: zoom so the focused rect fills a good chunk of the screen, centered a little high.
  let cam = { k: 1, tx: 0, ty: 0 };
  if (camera) {
    const k = Math.max(1.4, Math.min(5, (box.w * 0.5) / (camera.w * scale), (box.h * 0.45) / (camera.h * scale)));
    const cx = ox + (camera.x + camera.w / 2) * scale;
    const cy = oy + (camera.y + camera.h / 2) * scale;
    cam = { k, tx: box.w / 2 - k * cx, ty: box.h * 0.42 - k * cy };
  }

  const toScene = (e: { clientX: number; clientY: number }) => {
    const r = wrap.current!.getBoundingClientRect();
    return { x: (e.clientX - r.left - ox) / scale, y: (e.clientY - r.top - oy) / scale };
  };

  const hit = (p: { x: number; y: number }) => {
    for (let i = ordered.length - 1; i >= 0; i--) {
      const s = ordered[i];
      if (s.hidden || !interactive(s)) continue;
      const rx = Math.floor(p.x - s.x);
      const lx = s.flipX ? s.w - 1 - rx : rx;
      const ly = Math.floor(p.y - s.y);
      if (lx < 0 || ly < 0 || lx >= s.w || ly >= s.h) continue;
      const m = masks[`${s.file}?v=${versions[s.file] ?? BOOT}`];
      if (!m || m.data[(ly * m.w + lx) * 4 + 3] > 0) return s;
    }
    return null;
  };

  const outline = (color: string) =>
    `drop-shadow(1px 0 0 ${color}) drop-shadow(-1px 0 0 ${color}) drop-shadow(0 1px 0 ${color}) drop-shadow(0 -1px 0 ${color})`;

  return (
    <div
      ref={wrap}
      className="absolute inset-0 touch-none select-none overflow-hidden"
      onPointerMove={(e) => {
        const p = toScene(e);
        handlers.onHover?.(hit(p));
        handlers.onPointerMove?.(p, e);
      }}
      onPointerDown={(e) => {
        const p = toScene(e);
        handlers.onPointerDown?.(hit(p), p, e);
      }}
      onPointerUp={(e) => handlers.onPointerUp?.(e)}
      onPointerLeave={() => handlers.onHover?.(null)}
      onDragOver={(e) => handlers.onDrop && e.preventDefault()}
      onDrop={(e) => {
        if (!handlers.onDrop) return;
        e.preventDefault();
        handlers.onDrop(e, toScene(e));
      }}
    >
      <div
        className="absolute inset-0 origin-top-left transition-transform duration-700 ease-[cubic-bezier(.65,0,.35,1)]"
        style={{ transform: `translate(${cam.tx}px, ${cam.ty}px) scale(${cam.k})` }}
      >
      <div
        className="absolute origin-top-left [&_img]:[image-rendering:pixelated]"
        style={{ left: ox, top: oy, width: layout.width, height: layout.height, transform: `scale(${scale})` }}
      >
        <img
          src={src(layout.scene)}
          alt=""
          draggable={false}
          className="absolute left-0 top-0 max-w-none"
          style={{ opacity: showBackground ? 1 : 0.12 }}
        />
        {ordered.map((s) => {
          if (s.hidden) return null;
          const comp = companions[assetName(s.file)];
          const flip = s.flipX ? "scaleX(-1)" : undefined;
          return (
            <Fragment key={s.id}>
              {/* the window's glass: today's sky (and stars at night) */}
              {light && comp?.sky && (
                <div
                  className="pointer-events-none absolute"
                  style={{
                    left: s.x,
                    top: s.y,
                    width: s.w,
                    height: s.h,
                    zIndex: s.baseY,
                    transform: flip,
                    background: `linear-gradient(${light.skyTop}, ${light.skyBottom})`,
                    ...maskStyle(BASE + comp.sky),
                  }}
                >
                  {light.stars > 0.05 && (
                    <div
                      className="absolute inset-0"
                      style={{
                        opacity: light.stars,
                        backgroundImage: "radial-gradient(#fff 0.5px, transparent 0.6px), radial-gradient(#fff6c8 0.5px, transparent 0.6px)",
                        backgroundSize: "9px 11px, 13px 7px",
                        backgroundPosition: "1px 2px, 5px 4px",
                      }}
                    />
                  )}
                </div>
              )}
              {/* the sun patch the window throws on the floor */}
              {light && comp?.light && light.sun > 0.02 && (
                <div
                  className="pointer-events-none absolute mix-blend-screen"
                  style={{
                    left: s.flipX ? s.x + s.w - comp.light.dx - comp.light.w : s.x + comp.light.dx,
                    top: s.y + comp.light.dy,
                    width: comp.light.w,
                    height: comp.light.h,
                    zIndex: 1,
                    transform: flip,
                    opacity: light.sun * 0.55,
                    background: light.sunColor,
                    ...maskStyle(BASE + comp.light.file),
                  }}
                />
              )}
            <img
              src={src(s.file)}
              alt=""
              draggable={false}
              className="pointer-events-none absolute max-w-none"
              style={{
                left: s.x,
                top: s.y,
                width: s.w,
                height: s.h,
                zIndex: s.baseY,
                transform: s.flipX ? "scaleX(-1)" : undefined,
                filter:
                  selected === s.id
                    ? outline("#9bbf7a")
                    : hovered === s.id
                      ? `brightness(1.18) ${outline("#fff3cf")}`
                      : showOutlines
                        ? outline("rgba(255,120,210,0.8)")
                        : undefined,
              }}
            />
            </Fragment>
          );
        })}
        {actors.map((a) => (
          <div
            key={a.id}
            className="pointer-events-none absolute [image-rendering:pixelated]"
            style={{
              // whole pixels only, so the pixel art never lands between pixels
              left: Math.round(a.x) - Math.round(a.flip ? a.w - a.footX : a.footX),
              top: Math.round(a.y) - Math.round(a.footY),
              width: a.w,
              height: a.h,
              zIndex: a.z,
              backgroundImage: `url(${a.sheet})`,
              backgroundSize: a.sheetW ? `${a.sheetW}px ${a.h}px` : undefined,
              backgroundPosition: `${-a.frame * a.w}px 0`,
              transform: a.flip ? "scaleX(-1)" : undefined,
              opacity: a.opacity ?? 1,
            }}
          />
        ))}
        {light && (
          <>
            {/* the room's color cast for the time of day, kept to the room itself */}
            <div
              className="pointer-events-none absolute left-0 top-0 mix-blend-multiply"
              style={{
                width: layout.width,
                height: layout.height,
                zIndex: 900,
                background: light.tint,
                opacity: light.tintAlpha,
                ...maskStyle(src(layout.scene)),
              }}
            />
            {/* the city's windows light up after dark */}
            {layout.sceneNight && light.lamps > 0.02 && (
              <img
                src={src(layout.sceneNight)}
                alt=""
                draggable={false}
                className="pointer-events-none absolute left-0 top-0 max-w-none mix-blend-screen"
                style={{ zIndex: 940, opacity: light.lamps }}
              />
            )}
            {/* lamps glow once it gets dark */}
            {light.lamps > 0.02 &&
              ordered.map((s) => {
                const g = !s.hidden && companions[assetName(s.file)]?.glow;
                if (!g) return null;
                const gx = s.flipX ? s.x + s.w - g.x : s.x + g.x;
                return (
                  <div
                    key={`glow-${s.id}`}
                    className="pointer-events-none absolute rounded-full mix-blend-screen"
                    style={{
                      left: gx - g.r,
                      top: s.y + g.y - g.r,
                      width: g.r * 2,
                      height: g.r * 2,
                      zIndex: 950,
                      opacity: light.lamps,
                      background: "radial-gradient(circle, rgba(255,214,140,0.55) 0%, rgba(255,180,100,0.22) 35%, rgba(255,160,80,0) 70%)",
                    }}
                  />
                );
              })}
          </>
        )}
        {(showGrid || marker) && (
          <svg
            className="pointer-events-none absolute left-0 top-0 z-[999] overflow-visible"
            width={layout.width}
            height={layout.height}
            shapeRendering="crispEdges"
          >
            {showGrid &&
              (g.cols && g.rows ? (
                // just the floor: one line per tile edge along each iso axis
                <g stroke="rgba(255,236,190,0.35)" strokeWidth={1} fill="none">
                  {Array.from({ length: g.cols + 1 }, (_, i) => (
                    <line
                      key={`i${i}`}
                      x1={g.ox + (i * g.tile) / 2}
                      y1={g.oy + (i * g.tile) / 4}
                      x2={g.ox + ((i - g.rows) * g.tile) / 2}
                      y2={g.oy + ((i + g.rows) * g.tile) / 4}
                    />
                  ))}
                  {Array.from({ length: g.rows + 1 }, (_, j) => (
                    <line
                      key={`j${j}`}
                      x1={g.ox - (j * g.tile) / 2}
                      y1={g.oy + (j * g.tile) / 4}
                      x2={g.ox + ((g.cols - j) * g.tile) / 2}
                      y2={g.oy + ((g.cols + j) * g.tile) / 4}
                    />
                  ))}
                </g>
              ) : (
                <>
                  <defs>
                    <pattern id="iso-grid" patternUnits="userSpaceOnUse" x={g.ox} y={g.oy} width={g.tile} height={g.tile / 2}>
                      <path
                        d={`M0 ${g.tile / 4} L${g.tile / 2} 0 L${g.tile} ${g.tile / 4} L${g.tile / 2} ${g.tile / 2} Z`}
                        fill="none"
                        stroke="rgba(120,255,240,0.35)"
                        strokeWidth={0.5}
                      />
                    </pattern>
                  </defs>
                  <rect width={layout.width} height={layout.height} fill="url(#iso-grid)" />
                </>
              ))}
            {marker && (
              <path
                d={`M${marker.x - g.tile / 2} ${marker.y} L${marker.x} ${marker.y - g.tile / 4} L${marker.x + g.tile / 2} ${marker.y} L${marker.x} ${marker.y + g.tile / 4} Z`}
                fill="rgba(155,191,122,0.35)"
                stroke="#9bbf7a"
                strokeWidth={0.75}
              />
            )}
          </svg>
        )}
        {children}
      </div>
      </div>
    </div>
  );
}

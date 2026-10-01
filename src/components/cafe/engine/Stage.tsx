import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { BASE, type Layout, type SpriteDef } from "./types";

// Alpha masks so clicks land on the actual drawn pixels, not the sprite's bounding box.
function useAlphaMasks(layout: Layout | null, versions: Record<string, number>) {
  const [masks, setMasks] = useState<Record<string, { w: number; data: Uint8ClampedArray }>>({});
  useEffect(() => {
    if (!layout) return;
    let alive = true;
    layout.assets.forEach((s) => {
      const key = `${s.file}?v=${versions[s.file] ?? 0}`;
      if (masks[key]) return;
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = img.width;
        c.height = img.height;
        const ctx = c.getContext("2d")!;
        ctx.drawImage(img, 0, 0);
        const data = ctx.getImageData(0, 0, img.width, img.height).data;
        if (alive) setMasks((m) => ({ ...m, [key]: { w: img.width, data } }));
      };
      img.src = BASE + key;
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
  handlers,
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
  handlers: StageHandlers;
  children?: React.ReactNode;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const [box, setBox] = useState({ w: window.innerWidth, h: window.innerHeight });
  const masks = useAlphaMasks(layout, versions);
  const src = (file: string) => `${BASE}${file}?v=${versions[file] ?? 0}`;

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

  const ordered = useMemo(() => [...layout.assets].sort((a, b) => a.baseY - b.baseY), [layout.assets]);

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
      const m = masks[`${s.file}?v=${versions[s.file] ?? 0}`];
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
        {ordered.map((s) =>
          s.hidden ? null : (
            <img
              key={s.id}
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
          ),
        )}
        {showGrid && (
          <div
            className="pointer-events-none absolute inset-0 z-[999]"
            style={{
              backgroundImage:
                "linear-gradient(to right, rgba(0,255,255,.18) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,255,255,.18) 1px, transparent 1px)",
              backgroundSize: "16px 16px",
            }}
          />
        )}
        {children}
      </div>
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { BASE } from "./types";

// A small Aseprite-style pixel editor for touching up café sprites and the background.
// Edits the PNG at public/cafe/<file> and saves it straight back (dev server only).

type Tool = "pencil" | "eraser" | "fill" | "picker" | "select" | "hand";
type Rect = { x: number; y: number; w: number; h: number };
type Float = { data: Uint8ClampedArray; w: number; h: number; x: number; y: number };

const ZOOMS = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48];
const TOOLS: { id: Tool; key: string; label: string }[] = [
  { id: "pencil", key: "b", label: "Pencil" },
  { id: "eraser", key: "e", label: "Eraser" },
  { id: "fill", key: "g", label: "Fill" },
  { id: "picker", key: "i", label: "Eyedropper" },
  { id: "select", key: "m", label: "Select" },
  { id: "hand", key: "h", label: "Pan" },
];

const hex = (r: number, g: number, b: number) => "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
const rgb = (h: string): [number, number, number] => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];

async function loadPixels(src: string) {
  const img = new Image();
  img.src = src;
  await img.decode();
  const c = document.createElement("canvas");
  c.width = img.width;
  c.height = img.height;
  const ctx = c.getContext("2d")!;
  ctx.drawImage(img, 0, 0);
  return { w: img.width, h: img.height, data: ctx.getImageData(0, 0, img.width, img.height).data };
}

function colorsOf(data: Uint8ClampedArray, limit = 256) {
  const seen = new Set<string>();
  for (let i = 0; i < data.length && seen.size < limit; i += 4) if (data[i + 3] > 0) seen.add(hex(data[i], data[i + 1], data[i + 2]));
  // Group by hue, then dark to light, so the palette reads like a set of ramps.
  const hsl = (h: string) => {
    const [r, g, b] = rgb(h).map((v) => v / 255);
    const mx = Math.max(r, g, b);
    const mn = Math.min(r, g, b);
    const l = (mx + mn) / 2;
    let hue = 0;
    if (mx !== mn) {
      const d = mx - mn;
      hue = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    }
    return { hue: mx - mn < 0.08 ? -1 : Math.round(((hue * 60 + 360) % 360) / 30), l };
  };
  return [...seen].sort((a, b) => {
    const A = hsl(a);
    const B = hsl(b);
    return A.hue - B.hue || A.l - B.l;
  });
}

export function PixelEditor({ file, paletteFrom, onClose }: { file: string; paletteFrom: string; onClose: (saved: boolean) => void }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const img = useRef<{ w: number; h: number; data: Uint8ClampedArray } | null>(null);
  const off = useRef(document.createElement("canvas"));
  const floatCanvas = useRef(document.createElement("canvas"));
  const view = useRef({ z: 8, x: 40, y: 40 });
  const history = useRef<Uint8ClampedArray[]>([]);
  const future = useRef<Uint8ClampedArray[]>([]);
  const sel = useRef<Rect | null>(null);
  const float = useRef<Float | null>(null);
  const clip = useRef<Float | null>(null);
  const hover = useRef<{ x: number; y: number } | null>(null);
  const drag = useRef<{ kind: string; x: number; y: number; ax: number; ay: number } | null>(null);
  const space = useRef(false);

  const [tool, setTool] = useState<Tool>("pencil");
  const [prevTool, setPrevTool] = useState<Tool>("pencil");
  const [color, setColor] = useState("#f2c1b0");
  const [palette, setPalette] = useState<string[]>([]);
  const [grid, setGrid] = useState(true);
  const [zoomLabel, setZoomLabel] = useState(8);
  const [dirty, setDirty] = useState(false);
  const [status, setStatus] = useState("");
  const [ready, setReady] = useState(false);
  const [cursor, setCursor] = useState<{ x: number; y: number } | null>(null);

  // ---------- drawing to screen ----------

  const draw = useCallback(() => {
    const cv = canvas.current;
    const im = img.current;
    if (!cv || !im) return;
    const dpr = window.devicePixelRatio || 1;
    const ctx = cv.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
    const { z, x: ox, y: oy } = view.current;
    ctx.fillStyle = "#1f1c28";
    ctx.fillRect(0, 0, cv.width, cv.height);

    // checkerboard under transparent pixels
    const cs = 8;
    ctx.save();
    ctx.beginPath();
    ctx.rect(ox, oy, im.w * z, im.h * z);
    ctx.clip();
    for (let yy = 0; yy < im.h * z; yy += cs)
      for (let xx = 0; xx < im.w * z; xx += cs) {
        ctx.fillStyle = (xx / cs + yy / cs) % 2 ? "#3a3646" : "#4a4658";
        ctx.fillRect(ox + xx, oy + yy, cs, cs);
      }
    ctx.restore();

    const o = off.current;
    o.getContext("2d")!.putImageData(new ImageData(im.data, im.w, im.h), 0, 0);
    ctx.drawImage(o, ox, oy, im.w * z, im.h * z);

    const f = float.current;
    if (f) {
      const fc = floatCanvas.current;
      fc.width = f.w;
      fc.height = f.h;
      fc.getContext("2d")!.putImageData(new ImageData(f.data, f.w, f.h), 0, 0);
      ctx.drawImage(fc, ox + f.x * z, oy + f.y * z, f.w * z, f.h * z);
    }

    if (grid && z >= 6) {
      ctx.beginPath();
      for (let i = 0; i <= im.w; i++) {
        ctx.moveTo(ox + i * z + 0.5, oy);
        ctx.lineTo(ox + i * z + 0.5, oy + im.h * z);
      }
      for (let j = 0; j <= im.h; j++) {
        ctx.moveTo(ox, oy + j * z + 0.5);
        ctx.lineTo(ox + im.w * z, oy + j * z + 0.5);
      }
      ctx.strokeStyle = "rgba(255,255,255,0.07)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    ctx.strokeStyle = "rgba(255,255,255,0.35)";
    ctx.strokeRect(ox - 0.5, oy - 0.5, im.w * z + 1, im.h * z + 1);

    const r = f ? { x: f.x, y: f.y, w: f.w, h: f.h } : sel.current;
    if (r) {
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = "#fff";
      ctx.strokeRect(ox + r.x * z + 0.5, oy + r.y * z + 0.5, r.w * z, r.h * z);
      ctx.setLineDash([]);
    }

    const h = hover.current;
    if (h && (tool === "pencil" || tool === "eraser")) {
      ctx.fillStyle = tool === "eraser" ? "rgba(255,255,255,0.25)" : color;
      ctx.globalAlpha = 0.6;
      ctx.fillRect(ox + h.x * z, oy + h.y * z, z, z);
      ctx.globalAlpha = 1;
    }
  }, [grid, tool, color]);

  useEffect(() => {
    let alive = true;
    Promise.all([loadPixels(`${BASE}${file}?t=${Date.now()}`), loadPixels(`${BASE}${paletteFrom}?t=${Date.now()}`)]).then(([im, pal]) => {
      if (!alive) return;
      img.current = im;
      off.current.width = im.w;
      off.current.height = im.h;
      const colors = colorsOf(pal.data);
      for (const c of colorsOf(im.data)) if (!colors.includes(c)) colors.push(c);
      setPalette(colors);
      // Fit the image in the window at a whole-number zoom.
      const cv = canvas.current!;
      const fit = Math.max(1, Math.min(cv.clientWidth / im.w, cv.clientHeight / im.h) * 0.9);
      const z = [...ZOOMS].reverse().find((v) => v <= fit) ?? 1;
      view.current = { z, x: Math.round((cv.clientWidth - im.w * z) / 2), y: Math.round((cv.clientHeight - im.h * z) / 2) };
      setZoomLabel(z);
      setReady(true);
    });
    return () => {
      alive = false;
    };
  }, [file, paletteFrom]);

  useEffect(() => {
    const cv = canvas.current!;
    const ro = new ResizeObserver(() => {
      const dpr = window.devicePixelRatio || 1;
      cv.width = cv.clientWidth * dpr;
      cv.height = cv.clientHeight * dpr;
      draw();
    });
    ro.observe(cv);
    return () => ro.disconnect();
  }, [draw]);

  useEffect(draw, [draw, ready]);

  // ---------- pixel operations ----------

  const snapshot = () => {
    history.current.push(img.current!.data.slice());
    if (history.current.length > 200) history.current.shift();
    future.current = [];
    setDirty(true);
  };

  const setPx = (x: number, y: number, c: [number, number, number, number]) => {
    const im = img.current!;
    if (x < 0 || y < 0 || x >= im.w || y >= im.h) return;
    im.data.set(c, (y * im.w + x) * 4);
  };

  const paintColor = (): [number, number, number, number] => (tool === "eraser" ? [0, 0, 0, 0] : [...rgb(color), 255]);

  const line = (x0: number, y0: number, x1: number, y1: number, c: [number, number, number, number]) => {
    const dx = Math.abs(x1 - x0);
    const dy = -Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1;
    const sy = y0 < y1 ? 1 : -1;
    let err = dx + dy;
    for (;;) {
      setPx(x0, y0, c);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) {
        err += dy;
        x0 += sx;
      }
      if (e2 <= dx) {
        err += dx;
        y0 += sy;
      }
    }
  };

  const fill = (x: number, y: number) => {
    const im = img.current!;
    if (x < 0 || y < 0 || x >= im.w || y >= im.h) return;
    const d = im.data;
    const i0 = (y * im.w + x) * 4;
    const target = [d[i0], d[i0 + 1], d[i0 + 2], d[i0 + 3]];
    const c = [...rgb(color), 255];
    if (target.every((v, k) => v === c[k])) return;
    snapshot();
    const same = (i: number) => d[i] === target[0] && d[i + 1] === target[1] && d[i + 2] === target[2] && d[i + 3] === target[3];
    const stack = [x, y];
    while (stack.length) {
      const py = stack.pop()!;
      const px = stack.pop()!;
      if (px < 0 || py < 0 || px >= im.w || py >= im.h) continue;
      const i = (py * im.w + px) * 4;
      if (!same(i)) continue;
      d.set(c, i);
      stack.push(px + 1, py, px - 1, py, px, py + 1, px, py - 1);
    }
  };

  const pick = (x: number, y: number) => {
    const im = img.current!;
    if (x < 0 || y < 0 || x >= im.w || y >= im.h) return;
    const i = (y * im.w + x) * 4;
    if (im.data[i + 3] === 0) return;
    const h = hex(im.data[i], im.data[i + 1], im.data[i + 2]);
    setColor(h);
    setPalette((p) => (p.includes(h) ? p : [...p, h]));
  };

  const copyRect = (r: Rect): Float => {
    const im = img.current!;
    const data = new Uint8ClampedArray(r.w * r.h * 4);
    for (let y = 0; y < r.h; y++)
      for (let x = 0; x < r.w; x++) {
        const s = ((r.y + y) * im.w + r.x + x) * 4;
        data.set(im.data.subarray(s, s + 4), (y * r.w + x) * 4);
      }
    return { data, w: r.w, h: r.h, x: r.x, y: r.y };
  };

  const clearRect = (r: Rect) => {
    for (let y = r.y; y < r.y + r.h; y++) for (let x = r.x; x < r.x + r.w; x++) setPx(x, y, [0, 0, 0, 0]);
  };

  // Drop the floating selection into the image; transparent pixels don't overwrite.
  const commitFloat = () => {
    const f = float.current;
    if (!f) return;
    for (let y = 0; y < f.h; y++)
      for (let x = 0; x < f.w; x++) {
        const s = (y * f.w + x) * 4;
        if (f.data[s + 3] > 0) setPx(f.x + x, f.y + y, [f.data[s], f.data[s + 1], f.data[s + 2], f.data[s + 3]]);
      }
    sel.current = { x: f.x, y: f.y, w: f.w, h: f.h };
    float.current = null;
  };

  const undo = () => {
    commitFloat();
    const prev = history.current.pop();
    if (!prev) return;
    future.current.push(img.current!.data.slice());
    img.current!.data.set(prev);
    draw();
  };
  const redo = () => {
    const next = future.current.pop();
    if (!next) return;
    history.current.push(img.current!.data.slice());
    img.current!.data.set(next);
    draw();
  };

  const clampRect = (r: Rect): Rect | null => {
    const im = img.current!;
    const x0 = Math.max(0, Math.min(r.x, r.x + r.w));
    const y0 = Math.max(0, Math.min(r.y, r.y + r.h));
    const x1 = Math.min(im.w, Math.max(r.x, r.x + r.w));
    const y1 = Math.min(im.h, Math.max(r.y, r.y + r.h));
    return x1 > x0 && y1 > y0 ? { x: x0, y: y0, w: x1 - x0, h: y1 - y0 } : null;
  };

  const save = async () => {
    commitFloat();
    const im = img.current!;
    const c = document.createElement("canvas");
    c.width = im.w;
    c.height = im.h;
    c.getContext("2d")!.putImageData(new ImageData(im.data, im.w, im.h), 0, 0);
    setStatus("saving…");
    try {
      const r = await fetch("/__cafe/image", { method: "POST", body: JSON.stringify({ file, data: c.toDataURL("image/png") }) });
      if (!r.ok) throw new Error(await r.text());
      setDirty(false);
      setStatus("saved");
    } catch (e) {
      setStatus("save failed: " + String(e));
    }
    draw();
  };

  const close = () => {
    if (dirty && !window.confirm("Discard unsaved pixel changes?")) return;
    onClose(status === "saved" || history.current.length > 0);
  };

  const zoomAt = (dir: number, sx: number, sy: number) => {
    const v = view.current;
    const i = ZOOMS.indexOf(v.z);
    const z = ZOOMS[Math.max(0, Math.min(ZOOMS.length - 1, (i === -1 ? 4 : i) + dir))];
    // keep the pixel under the cursor fixed
    v.x = Math.round(sx - ((sx - v.x) * z) / v.z);
    v.y = Math.round(sy - ((sy - v.y) * z) / v.z);
    v.z = z;
    setZoomLabel(z);
    draw();
  };

  // ---------- input ----------

  const toPixel = (e: { clientX: number; clientY: number }) => {
    const r = canvas.current!.getBoundingClientRect();
    const v = view.current;
    return { x: Math.floor((e.clientX - r.left - v.x) / v.z), y: Math.floor((e.clientY - r.top - v.y) / v.z), sx: e.clientX - r.left, sy: e.clientY - r.top };
  };

  const onDown = (e: React.PointerEvent) => {
    if (!img.current) return;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    const p = toPixel(e);
    if (tool === "hand" || space.current || e.button === 1) {
      drag.current = { kind: "pan", x: e.clientX, y: e.clientY, ax: view.current.x, ay: view.current.y };
      return;
    }
    if (tool === "pencil" || tool === "eraser") {
      snapshot();
      setPx(p.x, p.y, paintColor());
      drag.current = { kind: "paint", x: p.x, y: p.y, ax: 0, ay: 0 };
    } else if (tool === "fill") {
      fill(p.x, p.y);
    } else if (tool === "picker") {
      pick(p.x, p.y);
      setTool(prevTool);
    } else if (tool === "select") {
      const f = float.current;
      const inside = (r: Rect) => p.x >= r.x && p.y >= r.y && p.x < r.x + r.w && p.y < r.y + r.h;
      if (f && inside(f)) {
        drag.current = { kind: "float", x: p.x, y: p.y, ax: f.x, ay: f.y };
      } else if (!f && sel.current && inside(sel.current)) {
        // Lift the selection so it can be moved. Alt/Option-drag leaves a copy behind.
        snapshot();
        float.current = copyRect(sel.current);
        if (!e.altKey) clearRect(sel.current);
        drag.current = { kind: "float", x: p.x, y: p.y, ax: float.current.x, ay: float.current.y };
      } else {
        commitFloat();
        sel.current = null;
        drag.current = { kind: "select", x: p.x, y: p.y, ax: p.x, ay: p.y };
      }
    }
    draw();
  };

  const onMove = (e: React.PointerEvent) => {
    if (!img.current) return;
    const p = toPixel(e);
    hover.current = { x: p.x, y: p.y };
    setCursor({ x: p.x, y: p.y });
    const d = drag.current;
    if (d?.kind === "pan") {
      view.current.x = d.ax + e.clientX - d.x;
      view.current.y = d.ay + e.clientY - d.y;
    } else if (d?.kind === "paint") {
      line(d.x, d.y, p.x, p.y, paintColor());
      d.x = p.x;
      d.y = p.y;
    } else if (d?.kind === "select") {
      sel.current = clampRect({ x: d.ax, y: d.ay, w: p.x - d.ax + (p.x >= d.ax ? 1 : 0), h: p.y - d.ay + (p.y >= d.ay ? 1 : 0) });
    } else if (d?.kind === "float" && float.current) {
      float.current.x = d.ax + p.x - d.x;
      float.current.y = d.ay + p.y - d.y;
    }
    draw();
  };

  const onUp = () => {
    drag.current = null;
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).closest("input")) return;
      const mod = e.metaKey || e.ctrlKey;
      const k = e.key.toLowerCase();
      if (e.key === " ") {
        space.current = e.type === "keydown";
        e.preventDefault();
        return;
      }
      if (e.type !== "keydown") return;
      if (mod && k === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      } else if (mod && k === "y") {
        e.preventDefault();
        redo();
      } else if (mod && k === "s") {
        e.preventDefault();
        save();
      } else if (mod && (k === "c" || k === "x")) {
        const r = float.current ?? sel.current;
        if (!r) return;
        e.preventDefault();
        clip.current = float.current ? { ...float.current, data: float.current.data.slice() } : copyRect(sel.current!);
        if (k === "x") {
          snapshot();
          if (float.current) float.current = null;
          else clearRect(sel.current!);
          sel.current = null;
        }
      } else if (mod && k === "v") {
        if (!clip.current) return;
        e.preventDefault();
        commitFloat();
        snapshot();
        const at = hover.current ?? { x: 0, y: 0 };
        float.current = { ...clip.current, data: clip.current.data.slice(), x: at.x, y: at.y };
        setTool("select");
      } else if (mod && k === "a") {
        e.preventDefault();
        commitFloat();
        sel.current = { x: 0, y: 0, w: img.current!.w, h: img.current!.h };
        setTool("select");
      } else if (e.key === "Delete" || e.key === "Backspace") {
        if (float.current) float.current = null;
        else if (sel.current) {
          snapshot();
          clearRect(sel.current);
        }
      } else if (e.key === "Enter" || e.key === "Escape") {
        commitFloat();
        if (e.key === "Escape") sel.current = null;
      } else if (e.key === "+" || e.key === "=") {
        zoomAt(1, canvas.current!.clientWidth / 2, canvas.current!.clientHeight / 2);
      } else if (e.key === "-") {
        zoomAt(-1, canvas.current!.clientWidth / 2, canvas.current!.clientHeight / 2);
      } else if (e.key === "'") {
        setGrid((g) => !g);
      } else if (!mod) {
        const t = TOOLS.find((t) => t.key === k);
        if (t) {
          if (t.id === "picker") setPrevTool(tool === "picker" ? prevTool : tool);
          if (t.id !== "select") commitFloat();
          setTool(t.id);
        }
      }
      draw();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("keyup", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("keyup", onKey);
    };
  });

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#15131c] font-['Space_Grotesk'] text-[13px] text-[#f3ecdc]">
      <header className="flex items-center gap-3 border-b border-white/10 bg-[#1d1a26] px-3 py-2">
        <span className="font-['Silkscreen'] text-xs">pixel editor</span>
        <span className="truncate opacity-60">{file}</span>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => zoomAt(-1, canvas.current!.clientWidth / 2, canvas.current!.clientHeight / 2)} className="h-7 w-7 rounded border border-white/15">
            −
          </button>
          <span className="w-12 text-center tabular-nums">{zoomLabel * 100}%</span>
          <button onClick={() => zoomAt(1, canvas.current!.clientWidth / 2, canvas.current!.clientHeight / 2)} className="h-7 w-7 rounded border border-white/15">
            +
          </button>
          <label className="ml-2 flex items-center gap-1.5">
            <input type="checkbox" checked={grid} onChange={(e) => setGrid(e.target.checked)} /> grid
          </label>
          <button onClick={undo} className="rounded border border-white/15 px-2 py-1" title="⌘Z">
            undo
          </button>
          <button onClick={redo} className="rounded border border-white/15 px-2 py-1" title="⇧⌘Z">
            redo
          </button>
          <span className={`w-28 text-right text-[11px] ${status.startsWith("save failed") ? "text-red-300" : dirty ? "text-amber-200" : "opacity-50"}`}>
            {status.startsWith("save failed") ? status : dirty ? "unsaved" : status}
          </span>
          <button onClick={save} className="rounded bg-[#9bbf7a] px-3 py-1 font-medium text-[#1a1512]">
            Save
          </button>
          <button onClick={close} className="rounded border border-white/15 px-3 py-1">
            Done
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <nav className="flex w-12 flex-col items-center gap-1 border-r border-white/10 bg-[#1d1a26] py-2">
          {TOOLS.map((t) => (
            <button
              key={t.id}
              onClick={() => {
                if (t.id === "picker") setPrevTool(tool);
                if (t.id !== "select") commitFloat();
                setTool(t.id);
                draw();
              }}
              title={`${t.label} (${t.key.toUpperCase()})`}
              className={`h-9 w-9 rounded font-['Silkscreen'] text-[10px] ${tool === t.id ? "bg-[#9bbf7a] text-[#1a1512]" : "hover:bg-white/10"}`}
            >
              {t.key.toUpperCase()}
            </button>
          ))}
        </nav>

        <canvas
          ref={canvas}
          className={`min-w-0 flex-1 ${tool === "hand" ? "cursor-grab" : tool === "select" ? "cursor-crosshair" : "cursor-cell"}`}
          onPointerDown={onDown}
          onPointerMove={onMove}
          onPointerUp={onUp}
          onPointerLeave={() => {
            hover.current = null;
            setCursor(null);
            draw();
          }}
          onWheel={(e) => {
            const p = toPixel(e);
            // Pinch or ⌘/Ctrl + scroll zooms; plain scroll pans.
            if (e.ctrlKey || e.metaKey) zoomAt(e.deltaY < 0 ? 1 : -1, p.sx, p.sy);
            else {
              view.current.x -= e.deltaX;
              view.current.y -= e.deltaY;
              draw();
            }
          }}
          onContextMenu={(e) => e.preventDefault()}
        />

        <aside className="flex w-56 flex-col border-l border-white/10 bg-[#1d1a26]">
          <div className="flex items-center gap-3 border-b border-white/10 p-3">
            <label className="relative h-10 w-10 cursor-pointer rounded border border-white/30" style={{ background: color }} title="Pick any color">
              <input
                type="color"
                value={color}
                onChange={(e) => {
                  setColor(e.target.value);
                  setPalette((p) => (p.includes(e.target.value) ? p : [...p, e.target.value]));
                }}
                className="absolute inset-0 opacity-0"
              />
            </label>
            <div>
              <p className="font-mono text-[12px]">{color}</p>
              <p className="text-[11px] opacity-50">{palette.length} colors</p>
            </div>
          </div>
          <div className="grid flex-1 auto-rows-min grid-cols-8 gap-px overflow-y-auto p-2">
            {palette.map((c) => (
              <button
                key={c}
                onClick={() => {
                  setColor(c);
                  if (tool === "eraser" || tool === "picker" || tool === "hand") setTool("pencil");
                }}
                title={c}
                className={`aspect-square ${c === color ? "outline outline-2 outline-white" : ""}`}
                style={{ background: c }}
              />
            ))}
          </div>
          <div className="space-y-0.5 border-t border-white/10 p-3 text-[11px] leading-relaxed opacity-55">
            <p>{cursor && img.current ? `x ${cursor.x}, y ${cursor.y}` : " "}</p>
            <p>B pencil · E eraser · G fill · I pick · M select · H / space pan</p>
            <p>select + drag moves · ⌥ drag copies · ⌘C ⌘X ⌘V · ⌫ clear · ⏎ drop</p>
            <p>⌘Z undo · ⌘S save · ⌘/pinch scroll zoom · ' grid</p>
          </div>
        </aside>
      </div>
    </div>
  );
}

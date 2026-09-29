import { useEffect, useRef, useState } from "react";
import { Stage } from "./Stage";
import { PixelEditor } from "./PixelEditor";
import { BASE, HOTSPOTS, type Layout, type SpriteDef } from "./types";

// In-site level editor. Open /cafe?edit while running `npm run dev`.
// Drag sprites, nudge with arrow keys, change depth, assign what they open, save to public/cafe/layout.json.
export function Editor({ initial }: { initial: Layout }) {
  const [layout, setLayout] = useState(initial);
  const [cut, setCut] = useState<Layout | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [showBg, setShowBg] = useState(true);
  const [outlines, setOutlines] = useState(true);
  const [grid, setGrid] = useState(false);
  const [status, setStatus] = useState<"saved" | "unsaved" | "saving" | "error">("saved");
  const drag = useRef<{ id: string; sx: number; sy: number; x: number; y: number } | null>(null);
  const [painting, setPainting] = useState<string | null>(null);
  const [versions, setVersions] = useState<Record<string, number>>({});

  const newSprite = async () => {
    const name = window.prompt("Name for the new sprite (letters, numbers, dashes)", "new-sprite")?.trim().toLowerCase();
    if (!name || !/^[a-z0-9-]+$/.test(name)) return;
    if (layout.assets.some((a) => a.id === name)) return window.alert("There's already a sprite with that name.");
    const size = window.prompt("Size in pixels, width x height", "32x32")?.match(/^(\d+)\s*x\s*(\d+)$/i);
    if (!size) return;
    const [w, h] = [Number(size[1]), Number(size[2])];
    const c = document.createElement("canvas");
    c.width = w;
    c.height = h;
    const file = `sprites/${name}.png`;
    const r = await fetch("/__cafe/image", { method: "POST", body: JSON.stringify({ file, data: c.toDataURL("image/png") }) });
    if (!r.ok) return window.alert("Couldn't create the file. Is the dev server running?");
    const x = Math.round((layout.width - w) / 2);
    const y = Math.round((layout.height - h) / 2);
    setLayout((l) => ({ ...l, assets: [...l.assets, { id: name, file, x, y, w, h, baseY: y + h, hotspot: null, label: null }] }));
    setStatus("unsaved");
    setSelected(name);
    setPainting(file);
  };

  const removeSprite = (id: string) => {
    if (!window.confirm(`Remove "${id}" from the café? (The PNG file stays on disk.)`)) return;
    setLayout((l) => ({ ...l, assets: l.assets.filter((a) => a.id !== id) }));
    setSelected(null);
    setStatus("unsaved");
  };

  useEffect(() => {
    fetch(BASE + "cut-manifest.json")
      .then((r) => r.json())
      .then((c: Layout) => {
        setCut(c);
        // Sprites cut after this layout was made get added in their original spot.
        setLayout((l) => {
          const have = new Set(l.assets.map((a) => a.id));
          const fresh = c.assets.filter((a) => !have.has(a.id));
          return fresh.length ? { ...l, assets: [...l.assets, ...fresh] } : l;
        });
      })
      .catch(() => {});
  }, []);

  const sel = layout.assets.find((a) => a.id === selected) ?? null;

  const update = (id: string, patch: Partial<SpriteDef>) => {
    setLayout((l) => ({ ...l, assets: l.assets.map((a) => (a.id === id ? { ...a, ...patch } : a)) }));
    setStatus("unsaved");
  };

  const save = async () => {
    setStatus("saving");
    try {
      const r = await fetch("/__cafe/layout", { method: "POST", body: JSON.stringify(layout) });
      setStatus(r.ok ? "saved" : "error");
    } catch {
      setStatus("error");
    }
  };

  const download = () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(layout, null, 2)], { type: "application/json" }));
    a.download = "layout.json";
    a.click();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (painting || (e.target as HTMLElement).closest("input, select, textarea")) return;
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        save();
        return;
      }
      if (!sel) return;
      const step = e.shiftKey ? 8 : 1;
      const moves: Record<string, [number, number]> = {
        ArrowLeft: [-step, 0],
        ArrowRight: [step, 0],
        ArrowUp: [0, -step],
        ArrowDown: [0, step],
      };
      if (moves[e.key]) {
        e.preventDefault();
        const [dx, dy] = moves[e.key];
        update(sel.id, { x: sel.x + dx, y: sel.y + dy, baseY: sel.baseY + dy });
      } else if (e.key === "[" || e.key === "]") {
        update(sel.id, { baseY: sel.baseY + (e.key === "]" ? step : -step) });
      } else if (e.key === "h") {
        update(sel.id, { hidden: !sel.hidden });
      } else if (e.key === "Escape") {
        setSelected(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const original = cut?.assets.find((a) => a.id === selected);
  const statusText = { saved: "saved", unsaved: "unsaved changes", saving: "saving…", error: "save failed (use download)" }[status];

  return (
    <div className="fixed inset-0 bg-[#15131c] font-['Space_Grotesk'] text-[13px] text-[#f3ecdc]">
      <div className="absolute inset-y-0 left-0 right-[300px]">
        <Stage
          layout={layout}
          interactive={() => true}
          hovered={hovered}
          selected={selected}
          showBackground={showBg}
          showOutlines={outlines}
          showGrid={grid}
          versions={versions}
          handlers={{
            onHover: (s) => !drag.current && setHovered(s?.id ?? null),
            onPointerDown: (s, p, e) => {
              setSelected(s?.id ?? null);
              if (s) {
                (e.target as HTMLElement).setPointerCapture(e.pointerId);
                drag.current = { id: s.id, sx: p.x, sy: p.y, x: s.x, y: s.y };
              }
            },
            onPointerMove: (p) => {
              const d = drag.current;
              if (!d) return;
              const s = layout.assets.find((a) => a.id === d.id)!;
              const nx = Math.round(d.x + p.x - d.sx);
              const ny = Math.round(d.y + p.y - d.sy);
              if (nx !== s.x || ny !== s.y) update(d.id, { x: nx, y: ny, baseY: s.baseY + (ny - s.y) });
            },
            onPointerUp: () => (drag.current = null),
          }}
        />
      </div>

      <aside className="absolute inset-y-0 right-0 flex w-[300px] flex-col border-l border-white/10 bg-[#1d1a26]">
        <div className="border-b border-white/10 p-4">
          <div className="flex items-center justify-between">
            <h1 className="font-['Silkscreen'] text-sm">café editor</h1>
            <a href="/cafe" className="text-[11px] underline opacity-60 hover:opacity-100">
              play →
            </a>
          </div>
          <div className="mt-3 flex gap-2">
            <button onClick={save} className="flex-1 rounded bg-[#9bbf7a] px-3 py-1.5 font-medium text-[#1a1512]">
              Save
            </button>
            <button onClick={download} className="rounded border border-white/20 px-3 py-1.5">
              Download
            </button>
          </div>
          <p className={`mt-2 text-[11px] ${status === "error" ? "text-red-300" : status === "unsaved" ? "text-amber-200" : "opacity-50"}`}>
            {statusText}
          </p>
          <div className="mt-2 flex gap-2">
            <button onClick={() => setPainting(layout.scene)} className="flex-1 rounded border border-white/20 px-2 py-1.5">
              Paint background
            </button>
            <button onClick={newSprite} className="flex-1 rounded border border-white/20 px-2 py-1.5">
              New sprite
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[12px]">
            {[
              ["background", showBg, setShowBg],
              ["outlines", outlines, setOutlines],
              ["grid", grid, setGrid],
            ].map(([name, v, set]) => (
              <label key={name as string} className="flex items-center gap-1.5">
                <input type="checkbox" checked={v as boolean} onChange={(e) => (set as (b: boolean) => void)(e.target.checked)} />
                {name as string}
              </label>
            ))}
          </div>
        </div>

        {sel ? (
          <div className="space-y-3 border-b border-white/10 p-4">
            <div className="flex items-center gap-3">
              <img src={BASE + sel.file} alt="" className="h-12 w-12 bg-black/30 object-contain [image-rendering:pixelated]" />
              <div className="min-w-0">
                <p className="truncate font-medium">{sel.id}</p>
                <p className="text-[11px] opacity-50">
                  {sel.w}×{sel.h}px
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(["x", "y", "baseY"] as const).map((k) => (
                <label key={k} className="text-[11px] opacity-80">
                  {k === "baseY" ? "depth" : k}
                  <input
                    type="number"
                    value={sel[k]}
                    onChange={(e) => update(sel.id, { [k]: Number(e.target.value) })}
                    className="mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]"
                  />
                </label>
              ))}
            </div>
            <label className="block text-[11px] opacity-80">
              clicking it opens
              <select
                value={sel.hotspot ?? ""}
                onChange={(e) => update(sel.id, { hotspot: e.target.value || null })}
                className="mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]"
              >
                <option value="">nothing (decoration)</option>
                {HOTSPOTS.map((h) => (
                  <option key={h} value={h}>
                    {h}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-[11px] opacity-80">
              hover label
              <input
                value={sel.label ?? ""}
                onChange={(e) => update(sel.id, { label: e.target.value || null })}
                className="mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]"
              />
            </label>
            <button onClick={() => setPainting(sel.file)} className="w-full rounded bg-[#f2c1b0] px-2 py-1.5 font-medium text-[#1a1512]">
              Edit pixels
            </button>
            <div className="flex flex-wrap gap-2">
              <button onClick={() => update(sel.id, { hidden: !sel.hidden })} className="rounded border border-white/20 px-2 py-1">
                {sel.hidden ? "show" : "hide"}
              </button>
              {original && (
                <button
                  onClick={() => update(sel.id, { x: original.x, y: original.y, baseY: original.baseY })}
                  className="rounded border border-white/20 px-2 py-1"
                >
                  reset position
                </button>
              )}
              <button onClick={() => removeSprite(sel.id)} className="rounded border border-red-300/40 px-2 py-1 text-red-200">
                remove
              </button>
            </div>
          </div>
        ) : (
          <p className="border-b border-white/10 p-4 text-[12px] opacity-60">Click a sprite to select it. Drag to move.</p>
        )}

        <ul className="flex-1 overflow-y-auto p-2">
          {[...layout.assets]
            .sort((a, b) => b.baseY - a.baseY)
            .map((a) => (
              <li key={a.id}>
                <button
                  onClick={() => setSelected(a.id)}
                  onMouseEnter={() => setHovered(a.id)}
                  onMouseLeave={() => setHovered(null)}
                  className={`flex w-full items-center justify-between rounded px-2 py-1 text-left ${selected === a.id ? "bg-white/15" : "hover:bg-white/5"} ${a.hidden ? "opacity-40" : ""}`}
                >
                  <span className="truncate">{a.id}</span>
                  <span className="ml-2 shrink-0 text-[11px] opacity-50">{a.hotspot ?? ""}</span>
                </button>
              </li>
            ))}
        </ul>
        <p className="border-t border-white/10 p-3 text-[11px] leading-relaxed opacity-50">
          arrows move 1px (shift 8px) · [ ] depth · h hide · esc deselect · ⌘S save
        </p>
      </aside>

      {painting && (
        <PixelEditor
          file={painting}
          paletteFrom={layout.scene}
          onClose={(changed) => {
            if (changed) {
              setVersions((v) => ({ ...v, [painting]: (v[painting] ?? 0) + 1 }));
              // A resized/new sprite keeps its layout size in sync with the PNG.
              const img = new Image();
              img.onload = () => {
                const a = layout.assets.find((s) => s.file === painting);
                if (a && (a.w !== img.width || a.h !== img.height)) update(a.id, { w: img.width, h: img.height });
              };
              img.src = `${BASE}${painting}?t=${Date.now()}`;
            }
            setPainting(null);
          }}
        />
      )}
    </div>
  );
}

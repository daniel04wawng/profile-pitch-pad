import { useCallback, useEffect, useRef, useState } from "react";
import { Stage, assetName, useCompanions } from "./Stage";
import { PixelEditor } from "./PixelEditor";
import { Play } from "./Play";
import { CafeScreen } from "./Screens";
import { formatHour, lightAt, pacificHour, phaseName } from "./lighting";
import { ScreenEditor } from "./ScreenEditor";
import { blankScreen, type ScreenDef, type Screens } from "./screenData";
import { ASSET_DEFAULTS, BASE, FLAT_ASSETS, DEFAULT_GRID, BACK, WALL_ITEMS, frontOf, rotOf, turnArt, snapIso, snapWall, type Layout, type SpriteDef } from "./types";

// The café's level editor. Open /cafe?edit while running `npm run dev`.
//  - Assets tab: every sprite PNG. Drag one onto the scene (or click) to place it; drop image files in to import.
//  - Scene tab: placed objects. Move, nudge, flip, duplicate, delete, layer, set what they open.
//  - Pixel editor for any asset or the background. Play (P) tries the scene in place.
// Saving writes public/cafe/layout.json; pixel edits write the PNGs.

type Size = { w: number; h: number };
const DRAG_TYPE = "text/cafe-asset";

const nameOf = (file: string) => file.replace(/^sprites\//, "").replace(/\.png$/, "");
const slug = (s: string) =>
  s
    .toLowerCase()
    .replace(/\.[a-z0-9]+$/, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "asset";

function sizeOf(src: string): Promise<Size> {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => res({ w: img.width, h: img.height });
    img.onerror = rej;
    img.src = src;
  });
}

async function toPngDataUrl(file: File) {
  const bmp = await createImageBitmap(file);
  const c = document.createElement("canvas");
  c.width = bmp.width;
  c.height = bmp.height;
  const ctx = c.getContext("2d")!;
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(bmp, 0, 0);
  return c.toDataURL("image/png");
}

async function writePng(file: string, data: string) {
  const r = await fetch("/__cafe/image", { method: "POST", body: JSON.stringify({ file, data }) });
  if (!r.ok) throw new Error(await r.text());
}

export function Editor({ initial, initialScreens }: { initial: Layout; initialScreens: Screens }) {
  const [screens, setScreens] = useState(initialScreens);
  const [screenSel, setScreenSel] = useState<string | null>(null);
  const [layout, setLayoutRaw] = useState(initial);
  const past = useRef<Layout[]>([]);
  const future = useRef<Layout[]>([]);
  const [cut, setCut] = useState<Layout | null>(null);
  const [assets, setAssets] = useState<string[]>([]);
  const [allFiles, setAllFiles] = useState<string[]>([]);
  const [sizes, setSizes] = useState<Record<string, Size>>({});
  const companions = useCompanions();
  // The point of a sprite that stands on the grid: its drawn foot if it has one (scaled to
  // its current size, mirrored when flipped), otherwise its bottom-centre.
  const footOf = (s: Pick<SpriteDef, "file" | "w" | "h" | "flipX">) => {
    // a back drawing without its own foot (one you painted) stands where its front does
    const f = companions[assetName(s.file)]?.foot ?? companions[frontOf(assetName(s.file))]?.foot;
    const nat = sizes[s.file];
    if (!f) return { x: s.w / 2, y: s.h };
    const kx = nat ? s.w / nat.w : 1;
    const ky = nat ? s.h / nat.h : 1;
    return { x: s.flipX ? s.w - f.x * kx : f.x * kx, y: f.y * ky };
  };
  const [tab, setTab] = useState<"scene" | "assets" | "screens">("scene");
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [showBg, setShowBg] = useState(true);
  const [outlines, setOutlines] = useState(true);
  const [grid, setGrid] = useState(true);
  const [snap, setSnap] = useState(true);
  const [marker, setMarker] = useState<{ x: number; y: number } | null>(null);
  const [playing, setPlaying] = useState(false);
  const [status, setStatus] = useState<"saved" | "unsaved" | "saving" | "error">("saved");
  const [painting, setPainting] = useState<string | null>(null);
  const [previewing, setPreviewing] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);
  // lighting preview: null = live San Francisco time; a number previews that hour
  const [lightOn, setLightOn] = useState(true);
  const [previewHour, setPreviewHour] = useState<number | null>(null);
  const hour = previewHour ?? pacificHour();
  // live preview of the screen being designed, shown over the room while you edit it
  const [designOpen, setDesignOpen] = useState(true);
  const [versions, setVersions] = useState<Record<string, number>>({});
  const drag = useRef<{ id: string; sx: number; sy: number; x: number; y: number; baseY: number; footX: number; footY: number } | null>(null);
  const gridOf = (l: Layout) => l.grid ?? DEFAULT_GRID;

  // ---------- history ----------

  // Every edit goes through here so it can be undone.
  const edit = (fn: (l: Layout) => Layout) => {
    past.current.push(layout);
    if (past.current.length > 300) past.current.shift();
    future.current = [];
    setLayoutRaw(fn(layout));
    setStatus("unsaved");
  };
  // For continuous changes (dragging): the undo point was taken when the drag started.
  const editLive = (fn: (l: Layout) => Layout) => {
    setLayoutRaw(fn);
    setStatus("unsaved");
  };
  const undo = () => {
    const prev = past.current.pop();
    if (!prev) return;
    future.current.push(layout);
    setLayoutRaw(prev);
    setStatus("unsaved");
  };
  const redo = () => {
    const next = future.current.pop();
    if (!next) return;
    past.current.push(layout);
    setLayoutRaw(next);
    setStatus("unsaved");
  };

  const patchObj = (id: string, patch: Partial<SpriteDef>) =>
    edit((l) => ({ ...l, assets: l.assets.map((a) => (a.id === id ? { ...a, ...patch } : a)) }));

  // ---------- assets ----------

  const refreshAssets = useCallback(async () => {
    try {
      const files: string[] = await (await fetch("/__cafe/assets")).json();
      setAllFiles(files);
      // back drawings belong to their asset (Rotate shows them), so the library hides them
      setAssets(files.filter((f) => !(nameOf(f).endsWith(BACK) && files.includes(`sprites/${frontOf(nameOf(f))}.png`))));
    } catch {
      setAssets([...new Set(layout.assets.map((a) => a.file))].sort());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If an asset's PNG changed size since the layout was saved (re-drawn, re-cleaned), resize every
  // placed copy to match while keeping its base on the same floor spot.
  useEffect(() => {
    const files = [...new Set(layout.assets.map((a) => a.file))];
    Promise.all(files.map((f) => sizeOf(`${BASE}${f}?t=${Date.now()}`).then((sz) => [f, sz] as const).catch(() => null))).then((res) => {
      const real = new Map(res.filter(Boolean) as [string, Size][]);
      const stale = layout.assets.some((a) => {
        const r = real.get(a.file);
        return r && (r.w !== a.w || r.h !== a.h);
      });
      if (!stale) return;
      editLive((l) => ({
        ...l,
        assets: l.assets.map((a) => {
          const r = real.get(a.file);
          if (!r || (r.w === a.w && r.h === a.h)) return a;
          return { ...a, x: Math.round(a.x + (a.w - r.w) / 2), y: a.y + (a.h - r.h), w: r.w, h: r.h };
        }),
      }));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    refreshAssets();
    fetch(BASE + "cut-manifest.json")
      .then((r) => r.json())
      .then(setCut)
      .catch(() => {});
  }, [refreshAssets]);

  const uniqueId = (base: string, taken = layout.assets) => {
    const ids = new Set(taken.map((a) => a.id));
    if (!ids.has(base)) return base;
    let n = 2;
    while (ids.has(`${base}-${n}`)) n++;
    return `${base}-${n}`;
  };

  // Place an asset with its feet at `at` (scene pixels); defaults to the middle of the scene.
  const place = async (file: string, at?: { x: number; y: number }) => {
    const { w, h } = sizes[file] ?? (await sizeOf(`${BASE}${file}?v=${versions[file] ?? 0}`));
    let fx = at ? Math.round(at.x) : Math.round(layout.width / 2);
    let fy = at ? Math.round(at.y) : Math.round(layout.height / 2 + h / 2);
    const wall = WALL_ITEMS[nameOf(file)];
    let flipX = false;
    if (snap && wall) {
      const p = snapWall(fx, fy, gridOf(layout), wall.onFloor);
      ({ x: fx, y: fy } = p);
      flipX = !!wall.drawnFor && p.side !== wall.drawnFor;
    } else if (snap) ({ x: fx, y: fy } = snapIso(fx, fy, gridOf(layout)));
    const id = uniqueId(nameOf(file));
    const foot = footOf({ file, w, h, flipX });
    edit((l) => ({
      ...l,
      assets: [
        ...l.assets,
        { id, file, x: fx - Math.round(foot.x), y: fy - Math.round(foot.y), w, h, ...(flipX ? { flipX } : {}), baseY: FLAT_ASSETS.has(nameOf(file)) ? fy - Math.round(foot.y) : fy - Math.round(foot.y) + h, hotspot: ASSET_DEFAULTS[nameOf(file)]?.hotspot ?? null, label: ASSET_DEFAULTS[nameOf(file)]?.label ?? null },
      ],
    }));
    setSelected(id);
    setTab("scene");
  };

  const duplicate = (id: string) => {
    const s = layout.assets.find((a) => a.id === id);
    if (!s) return;
    const nid = uniqueId(s.id.replace(/-\d+$/, ""));
    edit((l) => ({ ...l, assets: [...l.assets, { ...s, id: nid, x: s.x + 6, y: s.y + 6, baseY: s.baseY + 6 }] }));
    setSelected(nid);
  };

  // ---------- rotation (the same for every asset, see turnArt in types.ts) ----------

  const hasBack = (name: string) => allFiles.includes(`sprites/${frontOf(name)}${BACK}.png`);
  // The changes that put piece `s` at turn `rot`, keeping it on the same floor spot.
  const turnPatch = async (s: SpriteDef, rot: number, back = hasBack(nameOf(s.file))) => {
    const art = turnArt(nameOf(s.file), rot, back);
    const file = `sprites/${art.name}.png`;
    const nat = file === s.file ? { w: s.w, h: s.h } : sizes[file] ?? (await sizeOf(`${BASE}${file}?v=${versions[file] ?? 0}`));
    const here = footOf(s);
    const there = footOf({ file, w: nat.w, h: nat.h, flipX: art.flipX });
    const x = Math.round(s.x + here.x - there.x);
    const y = Math.round(s.y + here.y - there.y);
    return { file, w: nat.w, h: nat.h, flipX: art.flipX, rot: ((rot % 4) + 4) % 4, x, y, baseY: s.baseY + (y + nat.h) - (s.y + s.h) };
  };
  const rotate = async (id: string) => {
    const s = layout.assets.find((a) => a.id === id);
    if (!s) return;
    const patch = await turnPatch(s, rotOf(s) + 1);
    edit((l) => ({ ...l, assets: l.assets.map((a) => (a.id === id ? { ...a, ...patch } : a)) }));
  };
  // Paint what you see. A piece turned away from you with no back drawing yet gets one,
  // started as a copy of its front, and every copy of it switches to the new back.
  const paint = async (s: SpriteDef) => {
    const r = rotOf(s);
    const name = nameOf(s.file);
    if ((r === 1 || r === 2) && !hasBack(name)) {
      const back = `sprites/${frontOf(name)}${BACK}.png`;
      try {
        const blob = await (await fetch(`${BASE}${s.file}?v=${versions[s.file] ?? 0}`)).blob();
        await writePng(back, await toPngDataUrl(new File([blob], "back.png", { type: "image/png" })));
      } catch (e) {
        return window.alert(`Couldn't make a back drawing: ${e}`);
      }
      setAllFiles((f) => [...f, back]);
      const patches = await Promise.all(
        layout.assets.map(async (a) => (frontOf(nameOf(a.file)) === frontOf(name) && (rotOf(a) === 1 || rotOf(a) === 2) ? { ...a, ...(await turnPatch(a, rotOf(a), true)) } : a)),
      );
      edit((l) => ({ ...l, assets: patches }));
      return setPainting(back);
    }
    setPainting(s.file);
  };

  const remove = (id: string) => {
    edit((l) => ({ ...l, assets: l.assets.filter((a) => a.id !== id) }));
    setSelected(null);
  };

  const importFiles = async (files: FileList | File[], at?: { x: number; y: number }) => {
    const imgs = [...files].filter((f) => f.type.startsWith("image/"));
    const existing = new Set(assets);
    for (const f of imgs) {
      let name = slug(f.name);
      for (let n = 2; existing.has(`sprites/${name}.png`); n++) name = `${slug(f.name)}-${n}`;
      const file = `sprites/${name}.png`;
      existing.add(file);
      try {
        await writePng(file, await toPngDataUrl(f));
      } catch (e) {
        window.alert(`Couldn't import ${f.name}: ${e}`);
        continue;
      }
      if (at) await place(file, at);
    }
    await refreshAssets();
    if (!at) setTab("assets");
  };

  const newAsset = async () => {
    const name = slug(window.prompt("Name for the new asset", "new-asset") ?? "");
    if (!name) return;
    const file = `sprites/${name}.png`;
    if (assets.includes(file)) return window.alert("There's already an asset with that name.");
    const size = window.prompt("Size in pixels, width x height", "32x32")?.match(/^\s*(\d+)\s*x\s*(\d+)\s*$/i);
    if (!size) return;
    const c = document.createElement("canvas");
    c.width = Number(size[1]);
    c.height = Number(size[2]);
    try {
      await writePng(file, c.toDataURL("image/png"));
    } catch (e) {
      return window.alert(`Couldn't create the file: ${e}`);
    }
    await refreshAssets();
    await place(file);
    setPainting(file);
  };

  // ---------- screens ----------

  const newScreen = (): string | null => {
    const name = window.prompt("Name for the new screen", "My new screen")?.trim();
    if (!name) return null;
    const base = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "screen";
    let id = base;
    for (let n = 2; screens[id]; n++) id = `${base}-${n}`;
    setScreens((all) => ({ ...all, [id]: blankScreen(name) }));
    setStatus("unsaved");
    return id;
  };
  const changeScreen = (id: string, def: ScreenDef) => {
    setScreens((all) => ({ ...all, [id]: def }));
    setStatus("unsaved");
  };
  const deleteScreen = (id: string) => {
    setScreens((all) => {
      const next = { ...all };
      delete next[id];
      return next;
    });
    edit((l) => ({ ...l, assets: l.assets.map((a) => (a.hotspot === id ? { ...a, hotspot: null } : a)) }));
    setScreenSel(null);
  };
  const usedBy = (id: string) => layout.assets.filter((a) => a.hotspot === id).map((a) => a.id);

  // ---------- saving ----------

  const save = async () => {
    setStatus("saving");
    try {
      const [r1, r2] = await Promise.all([
        fetch("/__cafe/layout", { method: "POST", body: JSON.stringify(layout) }),
        fetch("/__cafe/screens", { method: "POST", body: JSON.stringify({ screens }) }),
      ]);
      setStatus(r1.ok && r2.ok ? "saved" : "error");
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

  // ---------- keyboard ----------

  const sel = layout.assets.find((a) => a.id === selected) ?? null;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (previewing) {
        if (e.key === "Escape") setPreviewing(null);
        return;
      }
      if (painting || (e.target as HTMLElement).closest("input, select, textarea")) return;
      const mod = e.metaKey || e.ctrlKey;
      const k = e.key.toLowerCase();
      if (k === "p" && !mod) return setPlaying((p) => !p);
      if (e.key === "\\" && !mod) return setPanelOpen((o) => !o);
      if (playing) return;
      if (mod && k === "s") {
        e.preventDefault();
        save();
      } else if (mod && k === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      } else if (mod && k === "y") {
        e.preventDefault();
        redo();
      } else if (mod && k === "d" && sel) {
        e.preventDefault();
        duplicate(sel.id);
      } else if ((e.key === "Backspace" || e.key === "Delete") && sel) {
        e.preventDefault();
        remove(sel.id);
      } else if (e.key === "Escape") {
        setSelected(null);
      } else if (sel && !mod) {
        const step = e.shiftKey ? 8 : 1;
        // With snap on, arrows hop one grid step (half a tile) and stay on the grid.
        const gx = gridOf(layout).tile / 2;
        const gy = gridOf(layout).tile / 4;
        const moves: Record<string, [number, number]> = snap
          ? { ArrowLeft: [-gx, 0], ArrowRight: [gx, 0], ArrowUp: [0, -gy], ArrowDown: [0, gy] }
          : { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
        if (moves[e.key]) {
          e.preventDefault();
          const [dx, dy] = moves[e.key];
          patchObj(sel.id, { x: sel.x + dx, y: sel.y + dy, baseY: sel.baseY + dy });
        } else if (e.key === "[" || e.key === "]") {
          patchObj(sel.id, { baseY: sel.baseY + (e.key === "]" ? step : -step) });
        } else if (k === "f" || k === "r") {
          rotate(sel.id);
        } else if (k === "h") {
          patchObj(sel.id, { hidden: !sel.hidden });
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // ---------- render ----------

  if (playing) return <Play layout={layout} screens={screens} versions={versions} hour={previewHour} onExit={() => setPlaying(false)} />;

  const original = cut?.assets.find((a) => a.id === selected);
  const statusText = { saved: "saved", unsaved: "unsaved changes", saving: "saving…", error: "save failed (use download)" }[status];
  const btn = "rounded border border-white/15 px-2.5 py-1 hover:bg-white/10 disabled:opacity-30";
  const thumb = (file: string) => `${BASE}${file}?v=${versions[file] ?? 0}`;

  return (
    <div className="fixed inset-0 flex flex-col bg-[#15131c] font-['Space_Grotesk'] text-[13px] text-[#f3ecdc]">
      <header className="flex flex-wrap items-center gap-2 border-b border-white/10 bg-[#1d1a26] px-3 py-2">
        <span className="mr-2 font-['Silkscreen'] text-xs">café editor</span>
        <button onClick={save} className="rounded bg-[#9bbf7a] px-3 py-1 font-medium text-[#1a1512]" title="⌘S">
          Save
        </button>
        <span className={`w-28 text-[11px] ${status === "error" ? "text-red-300" : status === "unsaved" ? "text-amber-200" : "opacity-50"}`}>
          {statusText}
        </span>
        <button onClick={undo} disabled={!past.current.length} className={btn} title="⌘Z">
          undo
        </button>
        <button onClick={redo} disabled={!future.current.length} className={btn} title="⇧⌘Z">
          redo
        </button>
        <span className="mx-1 h-5 w-px bg-white/10" />
        <button onClick={() => setPainting(layout.scene)} className={btn}>
          Paint background
        </button>
        <span className="mx-1 h-5 w-px bg-white/10" />
        {(
          [
            ["background", showBg, setShowBg],
            ["outlines", outlines, setOutlines],
            ["grid", grid, setGrid],
            ["snap", snap, setSnap],
          ] as const
        ).map(([name, v, set]) => (
          <label key={name} className="flex items-center gap-1.5 text-[12px]">
            <input type="checkbox" checked={v} onChange={(e) => set(e.target.checked)} />
            {name}
          </label>
        ))}
        <span className="mx-1 h-5 w-px bg-white/10" />
        <label className="flex items-center gap-1.5 text-[12px]">
          <input type="checkbox" checked={lightOn} onChange={(e) => setLightOn(e.target.checked)} />
          lighting
        </label>
        {lightOn && (
          <div className="flex items-center gap-2 text-[12px]">
            <input
              type="range"
              min={0}
              max={23.99}
              step={0.05}
              value={hour}
              onChange={(e) => setPreviewHour(Number(e.target.value))}
              className="w-28 accent-[#9bbf7a]"
              aria-label="Preview time of day"
            />
            <span className="w-32 tabular-nums opacity-80">
              {formatHour(hour)} · {phaseName(hour)}
            </span>
            {previewHour !== null && (
              <button onClick={() => setPreviewHour(null)} className={btn} title="Follow the real time in San Francisco">
                live
              </button>
            )}
          </div>
        )}
        <div className="ml-auto flex items-center gap-2">
          <button onClick={download} className={btn}>
            Download layout
          </button>
          <button onClick={() => setPlaying(true)} className="rounded bg-[#f2c1b0] px-3 py-1 font-medium text-[#1a1512]" title="P">
            ▶ Play
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <div className="relative min-w-0 flex-1">
          <Stage
            layout={layout}
            interactive={() => true}
            hovered={hovered}
            selected={selected}
            showBackground={showBg}
            showOutlines={outlines}
            showGrid={grid}
            versions={versions}
            marker={marker}
            light={lightOn ? lightAt(hour) : null}
            handlers={{
              onHover: (s) => !drag.current && setHovered(s?.id ?? null),
              onPointerDown: (s, p, e) => {
                setSelected(s?.id ?? null);
                if (!s) return;
                (e.target as HTMLElement).setPointerCapture(e.pointerId);
                // one undo step per drag
                past.current.push(layout);
                future.current = [];
                const foot = footOf(s);
                drag.current = { id: s.id, sx: p.x, sy: p.y, x: s.x, y: s.y, baseY: s.baseY, footX: s.x + foot.x, footY: s.y + foot.y };
              },
              onPointerMove: (p, e) => {
                const d = drag.current;
                if (!d) return;
                let dx = Math.round(p.x - d.sx);
                let dy = Math.round(p.y - d.sy);
                // hold Shift to place freely (e.g. a cup on top of the counter)
                if (snap && !e.shiftKey) {
                  // snap the object's foot (its floor corner, or bottom-centre) onto the iso grid
                  // wall items slide along the wall, keep their height and face the wall they're on
                  const s = layout.assets.find((a) => a.id === d.id);
                  const wall = s && WALL_ITEMS[nameOf(s.file)];
                  if (s && wall) {
                    const p = snapWall(d.footX + dx, d.footY + dy, gridOf(layout), wall.onFloor);
                    const flipX = wall.drawnFor ? p.side !== wall.drawnFor : !!s.flipX;
                    const off = footOf({ ...s, flipX });
                    const x = Math.round(p.x - off.x);
                    const y = Math.round(p.y - off.y);
                    setMarker({ x: p.x, y: p.y });
                    editLive((l) => ({
                      ...l,
                      assets: l.assets.map((a) => (a.id === d.id ? { ...a, x, y, baseY: y + a.h, flipX } : a)),
                    }));
                    return;
                  }
                  const foot = snapIso(d.footX + dx, d.footY + dy, gridOf(layout));
                  dx = Math.round(foot.x - d.footX);
                  dy = Math.round(foot.y - d.footY);
                  setMarker(foot);
                } else setMarker(null);
                editLive((l) => ({
                  ...l,
                  assets: l.assets.map((a) => (a.id === d.id ? { ...a, x: d.x + dx, y: d.y + dy, baseY: d.baseY + dy } : a)),
                }));
              },
              onPointerUp: () => {
                const d = drag.current;
                drag.current = null;
                setMarker(null);
                // a click without movement shouldn't leave an empty undo step
                const s = d && layout.assets.find((a) => a.id === d.id);
                if (s && s.x === d.x && s.y === d.y) past.current.pop();
              },
              onDrop: (e, p) => {
                const file = e.dataTransfer.getData(DRAG_TYPE);
                if (file) place(file, p);
                else if (e.dataTransfer.files.length) importFiles(e.dataTransfer.files, p);
              },
            }}
          />
          {tab === "screens" && screenSel && screens[screenSel] && (
            <>
              <div
                className={`absolute inset-0 z-[5] flex items-center justify-center bg-[#15131c]/55 p-4 backdrop-blur-[2px] transition-all duration-300 ease-out ${
                  designOpen ? "opacity-100" : "pointer-events-none translate-x-10 opacity-0"
                }`}
              >
                <CafeScreen screen={screens[screenSel]} playing={false} onMusic={() => {}} onClose={() => setDesignOpen(false)} />
              </div>
              <button
                onClick={() => setDesignOpen((o) => !o)}
                className="absolute left-3 top-3 z-10 rounded border border-white/15 bg-[#1d1a26] px-2.5 py-1 text-[12px] hover:bg-white/10"
              >
                {designOpen ? "hide screen preview" : "show screen preview"}
              </button>
            </>
          )}
          <button
            onClick={() => setPanelOpen((o) => !o)}
            title={panelOpen ? "Hide the side panel (\\)" : "Show the side panel (\\)"}
            className="absolute right-0 top-1/2 z-10 -translate-y-1/2 rounded-l border border-r-0 border-white/15 bg-[#1d1a26] px-1 py-4 text-[12px] opacity-70 hover:opacity-100"
          >
            {panelOpen ? "›" : "‹"}
          </button>
          <p className="pointer-events-none absolute bottom-2 left-3 text-[11px] opacity-40">
            drag to move (⇧ drag = no snap) · arrows move{snap ? " 1 grid step" : " 1px (⇧ 8px)"} · [ ] layer · R rotate · H hide · ⌘D duplicate · ⌫ delete · ⌘Z undo · P play · \\ panel
          </p>
        </div>

        <aside
          className={`flex shrink-0 flex-col overflow-hidden border-l border-white/10 bg-[#1d1a26] transition-[width] duration-300 ease-out ${panelOpen ? "w-[300px]" : "w-0 border-l-0"}`}
        >
          <div className="flex w-[300px] min-h-0 flex-1 flex-col">
          <div className="flex border-b border-white/10">
            {(["scene", "assets", "screens"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 py-2 font-['Silkscreen'] text-[11px] uppercase ${tab === t ? "border-b-2 border-[#9bbf7a]" : "opacity-50"}`}
              >
                {t === "scene" ? `scene (${layout.assets.length})` : t === "assets" ? `assets (${assets.length})` : `screens (${Object.keys(screens).length})`}
              </button>
            ))}
          </div>

          {tab === "scene" ? (
            <>
              {sel ? (
                <div className="space-y-3 border-b border-white/10 p-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={thumb(sel.file)}
                      alt=""
                      className="h-12 w-12 bg-black/30 object-contain [image-rendering:pixelated]"
                      style={{ transform: sel.flipX ? "scaleX(-1)" : undefined }}
                    />
                    <div className="min-w-0">
                      <p className="truncate font-medium">{sel.id}</p>
                      <p className="truncate text-[11px] opacity-50">
                        {nameOf(sel.file)} · {sel.w}×{sel.h}px
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {(["x", "y", "baseY"] as const).map((k) => (
                      <label key={k} className="text-[11px] opacity-80">
                        {k === "baseY" ? "layer" : k}
                        <input
                          type="number"
                          value={sel[k]}
                          onChange={(e) => patchObj(sel.id, { [k]: Number(e.target.value) })}
                          className="mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]"
                        />
                      </label>
                    ))}
                  </div>
                  <div className="rounded border border-white/10 bg-black/20 p-2">
                    <label className="block text-[11px] opacity-80">
                      screen (what opens when you walk up to it)
                      <select
                        value={sel.hotspot ?? ""}
                        onChange={(e) => {
                          if (e.target.value === "__new") {
                            const id = newScreen();
                            if (id) patchObj(sel.id, { hotspot: id });
                          } else patchObj(sel.id, { hotspot: e.target.value || null });
                        }}
                        className="mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]"
                      >
                        <option value="">none (just decoration)</option>
                        {Object.entries(screens).map(([id, def]) => (
                          <option key={id} value={id}>
                            {def.name}
                          </option>
                        ))}
                        {sel.hotspot && !screens[sel.hotspot] && <option value={sel.hotspot}>{sel.hotspot} (missing)</option>}
                        <option value="__new">+ new screen…</option>
                      </select>
                    </label>
                    {sel.hotspot && screens[sel.hotspot] && (
                      <div className="mt-2 flex gap-1.5">
                        <button onClick={() => setPreviewing(sel.hotspot)} className={`${btn} flex-1`}>
                          Preview screen
                        </button>
                        <button
                          onClick={() => {
                            setScreenSel(sel.hotspot);
                            setTab("screens");
                          }}
                          className={`${btn} flex-1`}
                        >
                          Edit screen
                        </button>
                      </div>
                    )}
                  </div>
                  <label className="block text-[11px] opacity-80">
                    hover label
                    <input
                      value={sel.label ?? ""}
                      onChange={(e) => patchObj(sel.id, { label: e.target.value || null })}
                      className="mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]"
                    />
                  </label>
                  <button onClick={() => paint(sel)} className="w-full rounded bg-[#f2c1b0] px-2 py-1.5 font-medium text-[#1a1512]">
                    Edit pixels
                  </button>
                  <div className="flex flex-wrap gap-1.5">
                    <button onClick={() => rotate(sel.id)} className={btn} title="Turn a quarter turn (R)">
                      rotate
                    </button>
                    <button onClick={() => duplicate(sel.id)} className={btn}>
                      duplicate
                    </button>
                    <button onClick={() => patchObj(sel.id, { hidden: !sel.hidden })} className={btn}>
                      {sel.hidden ? "show" : "hide"}
                    </button>
                    {original && original.file === sel.file && (
                      <button onClick={() => patchObj(sel.id, { x: original.x, y: original.y, baseY: original.baseY })} className={btn}>
                        reset
                      </button>
                    )}
                    <button onClick={() => remove(sel.id)} className="rounded border border-red-300/40 px-2.5 py-1 text-red-200 hover:bg-red-300/10">
                      delete
                    </button>
                  </div>
                </div>
              ) : (
                <p className="border-b border-white/10 p-4 text-[12px] opacity-60">
                  Click an object to select it, or drag one in from Assets.
                </p>
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
                        className={`flex w-full items-center gap-2 rounded px-2 py-1 text-left ${selected === a.id ? "bg-white/15" : "hover:bg-white/5"} ${a.hidden ? "opacity-40" : ""}`}
                      >
                        <img src={thumb(a.file)} alt="" className="h-5 w-5 object-contain [image-rendering:pixelated]" />
                        <span className="flex-1 truncate">{a.id}</span>
                        <span className="shrink-0 text-[11px] opacity-50">{a.hotspot ?? ""}</span>
                      </button>
                    </li>
                  ))}
              </ul>
            </>
          ) : tab === "screens" ? (
            <ScreenEditor
              screens={screens}
              selected={screenSel}
              setSelected={(id) => {
                setScreenSel(id);
                if (id) setDesignOpen(true);
              }}
              usedBy={usedBy}
              onChange={changeScreen}
              onCreate={() => {
                const id = newScreen();
                if (id) setScreenSel(id);
              }}
              onDelete={deleteScreen}
              onPreview={setPreviewing}
            />
          ) : (
            <div
              className="flex min-h-0 flex-1 flex-col"
              onDragOver={(e) => e.dataTransfer.types.includes("Files") && e.preventDefault()}
              onDrop={(e) => {
                if (!e.dataTransfer.files.length) return;
                e.preventDefault();
                importFiles(e.dataTransfer.files);
              }}
            >
              <div className="flex gap-2 border-b border-white/10 p-3">
                <button onClick={newAsset} className={`${btn} flex-1`}>
                  New asset
                </button>
                <label className={`${btn} flex-1 cursor-pointer text-center`}>
                  Import PNG
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files) importFiles(e.target.files);
                      e.target.value = "";
                    }}
                  />
                </label>
              </div>
              <div className="grid flex-1 auto-rows-min grid-cols-3 gap-2 overflow-y-auto p-3">
                {assets.map((file) => {
                  const used = layout.assets.filter((a) => a.file === file).length;
                  return (
                    <div key={file} className="group relative rounded bg-black/25 p-1.5 hover:bg-black/40">
                      <button
                        draggable
                        onDragStart={(e) => e.dataTransfer.setData(DRAG_TYPE, file)}
                        onClick={() => place(file)}
                        title="Drag onto the scene, or click to place in the middle"
                        className="flex aspect-square w-full items-center justify-center"
                      >
                        <img
                          src={thumb(file)}
                          alt=""
                          draggable={false}
                          className="max-h-full max-w-full [image-rendering:pixelated]"
                          onLoad={(e) => {
                            const im = e.currentTarget;
                            setSizes((s) => ({ ...s, [file]: { w: im.naturalWidth, h: im.naturalHeight } }));
                          }}
                        />
                      </button>
                      <p className="mt-1 truncate text-[10px] opacity-70">{nameOf(file)}</p>
                      <p className="text-[10px] opacity-40">{used ? `${used} in scene` : "not placed"}</p>
                      <button
                        onClick={() => setPainting(file)}
                        className="absolute right-1 top-1 hidden rounded bg-[#f2c1b0] px-1.5 text-[10px] font-medium text-[#1a1512] group-hover:block"
                      >
                        edit
                      </button>
                    </div>
                  );
                })}
              </div>
              <p className="border-t border-white/10 p-3 text-[11px] opacity-50">Drag assets onto the scene. Drop image files here to import.</p>
            </div>
          )}
          </div>
        </aside>
      </div>

      {previewing && (
        <div
          onClick={() => setPreviewing(null)}
          className="fixed inset-0 z-40 flex items-center justify-center bg-[#15131c]/60 p-3 backdrop-blur-[3px]"
        >
          {screens[previewing] && <CafeScreen screen={screens[previewing]} playing={false} onMusic={() => {}} onClose={() => setPreviewing(null)} />}
        </div>
      )}

      {painting && (
        <PixelEditor
          file={painting}
          paletteFrom={layout.scene}
          onClose={async (changed, shift) => {
            const file = painting;
            setPainting(null);
            if (!changed) return;
            setVersions((v) => ({ ...v, [file]: (v[file] ?? 0) + 1 }));
            // A resized canvas keeps every placed copy's size in sync with the PNG, and growing it
            // on the top/left moves the copies so the art itself stays put in the café.
            const { w, h } = await sizeOf(`${BASE}${file}?t=${Date.now()}`);
            setSizes((s) => ({ ...s, [file]: { w, h } }));
            if (layout.assets.some((a) => a.file === file && (a.w !== w || a.h !== h || shift.x || shift.y)))
              editLive((l) => ({
                ...l,
                assets: l.assets.map((a) =>
                  a.file === file ? { ...a, w, h, x: a.x - (a.flipX ? w - a.w - shift.x : shift.x), y: a.y - shift.y } : a,
                ),
              }));
          }}
        />
      )}
    </div>
  );
}

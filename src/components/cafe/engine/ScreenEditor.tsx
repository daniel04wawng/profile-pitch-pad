import { BASE } from "./types";
import { TEMPLATES, TONES, UI_SPRITES, type ScreenDef, type ScreenItem, type Screens, type Template, type Tone } from "./screenData";

// The editor's Screens tab: create screens, edit their words, items and links, pick a
// template and a style, preview them. Objects in the room connect to a screen by id.

const input = "mt-0.5 w-full rounded bg-black/30 px-2 py-1 text-[13px]";
const small = "rounded border border-white/15 px-2 py-0.5 text-[11px] hover:bg-white/10";

export function ScreenEditor({
  screens,
  selected,
  setSelected,
  usedBy,
  onChange,
  onCreate,
  onDelete,
  onPreview,
}: {
  screens: Screens;
  selected: string | null;
  setSelected: (id: string | null) => void;
  usedBy: (id: string) => string[];
  onChange: (id: string, def: ScreenDef) => void;
  onCreate: () => void;
  onDelete: (id: string) => void;
  onPreview: (id: string) => void;
}) {
  const s = selected ? screens[selected] : null;

  if (!s || !selected) {
    return (
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="border-b border-white/10 p-3">
          <button onClick={onCreate} className="w-full rounded bg-[#9bbf7a] px-3 py-1.5 font-medium text-[#1a1512]">
            + New screen
          </button>
        </div>
        <ul className="flex-1 overflow-y-auto p-2">
          {Object.entries(screens).map(([id, def]) => {
            const users = usedBy(id);
            return (
              <li key={id}>
                <button onClick={() => setSelected(id)} className="w-full rounded px-2 py-1.5 text-left hover:bg-white/5">
                  <p className="truncate">{def.name}</p>
                  <p className="truncate text-[11px] opacity-50">
                    {TEMPLATES[def.template]?.split(" (")[0]} · {users.length ? `on ${users.join(", ")}` : "not connected yet"}
                  </p>
                </button>
              </li>
            );
          })}
        </ul>
        <p className="border-t border-white/10 p-3 text-[11px] opacity-50">Connect a screen to an object in the Scene tab (select the object, pick its Screen).</p>
      </div>
    );
  }

  const set = (patch: Partial<ScreenDef>) => onChange(selected, { ...s, ...patch });
  const setItem = (i: number, patch: Partial<ScreenItem>) => set({ items: s.items.map((it, k) => (k === i ? { ...it, ...patch } : it)) });
  const moveItem = (i: number, d: number) => {
    const j = i + d;
    if (j < 0 || j >= s.items.length) return;
    const items = [...s.items];
    [items[i], items[j]] = [items[j], items[i]];
    set({ items });
  };
  const users = usedBy(selected);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center gap-2 border-b border-white/10 p-3">
        <button onClick={() => setSelected(null)} className={small}>
          ← all screens
        </button>
        <span className="flex-1" />
        <button onClick={() => onPreview(selected)} className="rounded bg-[#f2c1b0] px-2.5 py-1 text-[12px] font-medium text-[#1a1512]">
          Preview
        </button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        <label className="block text-[11px] opacity-80">
          name (shown in the Screen picker)
          <input value={s.name} onChange={(e) => set({ name: e.target.value })} className={input} />
        </label>
        <div className="grid grid-cols-2 gap-2">
          <label className="block text-[11px] opacity-80">
            template
            <select value={s.template} onChange={(e) => set({ template: e.target.value as Template })} className={input}>
              {Object.entries(TEMPLATES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-[11px] opacity-80">
            style
            <select value={s.tone} onChange={(e) => set({ tone: e.target.value as Tone })} className={input}>
              {Object.entries(TONES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="block text-[11px] opacity-80">
          small heading
          <input value={s.kicker} onChange={(e) => set({ kicker: e.target.value })} className={input} />
        </label>
        <label className="block text-[11px] opacity-80">
          title
          <input value={s.title} onChange={(e) => set({ title: e.target.value })} className={input} />
        </label>
        <label className="block text-[11px] opacity-80">
          text (one paragraph per line)
          <textarea value={s.body.join("\n")} onChange={(e) => set({ body: e.target.value.split("\n") })} rows={4} className={input} />
        </label>

        <div>
          <div className="flex items-center justify-between">
            <p className="text-[11px] opacity-80">
              items ({s.template === "case" ? "pastries" : s.template === "shelf" ? "books" : s.template === "music" ? "tracks" : "rows"})
            </p>
            <button onClick={() => set({ items: [...s.items, { title: "New item" }] })} className={small}>
              + add
            </button>
          </div>
          <div className="mt-1 space-y-2">
            {s.items.map((it, i) => (
              <div key={i} className="rounded border border-white/10 bg-black/20 p-2">
                <div className="flex items-center gap-1">
                  {s.template === "case" && it.sprite && <img src={`${BASE}ui/${it.sprite}.png`} alt="" className="h-5 w-auto [image-rendering:pixelated]" />}
                  <input value={it.title} onChange={(e) => setItem(i, { title: e.target.value })} className="min-w-0 flex-1 rounded bg-black/30 px-2 py-1 text-[13px]" placeholder="title" />
                  <button onClick={() => moveItem(i, -1)} className={small} title="Move up">
                    ↑
                  </button>
                  <button onClick={() => moveItem(i, 1)} className={small} title="Move down">
                    ↓
                  </button>
                  <button onClick={() => set({ items: s.items.filter((_, k) => k !== i) })} className={`${small} text-red-200`} title="Remove">
                    ✕
                  </button>
                </div>
                <input value={it.meta ?? ""} onChange={(e) => setItem(i, { meta: e.target.value || undefined })} className={input} placeholder="right side: price, date, subtitle" />
                <textarea value={it.note ?? ""} onChange={(e) => setItem(i, { note: e.target.value || undefined })} rows={2} className={input} placeholder="details shown when opened" />
                <input value={it.href ?? ""} onChange={(e) => setItem(i, { href: e.target.value || undefined })} className={input} placeholder="link (optional)" />
                {s.template === "case" && (
                  <select value={it.sprite ?? ""} onChange={(e) => setItem(i, { sprite: e.target.value || undefined })} className={input}>
                    <option value="">pastry sprite…</option>
                    {UI_SPRITES.map((sp) => (
                      <option key={sp} value={sp}>
                        {sp.replace("pastry-", "")}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <p className="text-[11px] opacity-80">links (buttons)</p>
            <button onClick={() => set({ links: [...s.links, { label: "Link", href: "https://" }] })} className={small}>
              + add
            </button>
          </div>
          <div className="mt-1 space-y-1">
            {s.links.map((l, i) => (
              <div key={i} className="flex gap-1">
                <input value={l.label} onChange={(e) => set({ links: s.links.map((x, k) => (k === i ? { ...x, label: e.target.value } : x)) })} className="w-24 rounded bg-black/30 px-2 py-1 text-[13px]" />
                <input value={l.href} onChange={(e) => set({ links: s.links.map((x, k) => (k === i ? { ...x, href: e.target.value } : x)) })} className="min-w-0 flex-1 rounded bg-black/30 px-2 py-1 text-[13px]" />
                <button onClick={() => set({ links: s.links.filter((_, k) => k !== i) })} className={`${small} text-red-200`}>
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-white/10 pt-3 text-[11px] opacity-60">
          {users.length ? `Connected to: ${users.join(", ")}` : "Not connected to anything yet. Select an object in Scene and pick this screen."}
        </div>
        <button
          onClick={() => {
            if (window.confirm(`Delete the screen "${s.name}"?${users.length ? ` ${users.length} object(s) will be disconnected.` : ""}`)) onDelete(selected);
          }}
          className="rounded border border-red-300/40 px-2.5 py-1 text-[12px] text-red-200 hover:bg-red-300/10"
        >
          delete screen
        </button>
      </div>
    </div>
  );
}

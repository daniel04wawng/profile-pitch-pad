import { createContext, useContext, useEffect, useRef, useState, type CSSProperties } from "react";
import { saveMedia, MEDIA_TYPES } from "./store";
import type { Media, ScreenDef, ScreenItem } from "./screenData";

// Editing a screen in place: Daniel opens a screen in his café (on the dev server), presses
// ✎ edit, and every bit of text in it can be clicked and typed over; items, links and photos can
// be added and removed right there. Visitors never get an editing screen (Play only passes an
// `onEdit` on the dev server). The change goes up to Play, which saves it to disk.

type Edit = { on: boolean; can: boolean; toggle: () => void; set: (s: ScreenDef) => void; screen: ScreenDef };
export const EditCtx = createContext<Edit | null>(null);
export const useEdit = () => useContext(EditCtx);

const EDIT_RING: CSSProperties = { outline: "2px dashed rgba(232,180,92,0.9)", outlineOffset: 2, minWidth: "2ch", cursor: "text" };

// A bit of text you can type over while editing (plain text; Enter makes a new line where it
// can have several, and finishes the edit where it can't). Otherwise just the text.
export function Ed({ value, onChange, multi = false, placeholder = "…", className, style }: { value: string; onChange: (v: string) => void; multi?: boolean; placeholder?: string; className?: string; style?: CSSProperties }) {
  const e = useEdit();
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (ref.current && document.activeElement !== ref.current) ref.current.innerText = value;
  }, [value, e?.on]);
  if (!e?.on) return <span className={className} style={{ whiteSpace: multi ? "pre-wrap" : undefined, ...style }}>{value}</span>;
  return (
    <span
      ref={ref}
      contentEditable="plaintext-only"
      suppressContentEditableWarning
      data-placeholder={placeholder}
      className={`${className ?? ""} empty:before:opacity-40 empty:before:content-[attr(data-placeholder)]`}
      style={{ ...EDIT_RING, whiteSpace: multi ? "pre-wrap" : undefined, display: "inline-block", ...style }}
      onClick={(ev) => ev.stopPropagation()}
      onKeyDown={(ev) => {
        ev.stopPropagation(); // (the café's own keys: walking, Esc)
        if (ev.key === "Enter" && !multi) {
          ev.preventDefault();
          (ev.target as HTMLElement).blur();
        }
      }}
      onBlur={(ev) => {
        const v = (ev.target as HTMLElement).innerText.replace(/\n$/, "");
        if (v !== value) onChange(v);
      }}
    />
  );
}

// small buttons used only while editing
export function EditButton({ onClick, children, title }: { onClick: () => void; children: string; title?: string }) {
  return (
    <button
      title={title}
      onClick={(ev) => {
        ev.stopPropagation();
        onClick();
      }}
      className="px-2 py-0.5 font-['Silkscreen'] text-[10px] uppercase tracking-wider"
      style={{ background: "#e8b45c", color: "#2b1d1a", boxShadow: "0 2px 0 rgba(0,0,0,0.3)" }}
    >
      {children}
    </button>
  );
}

// the screen with one item changed (or removed, with null)
export function withItem(s: ScreenDef, i: number, it: ScreenItem | null): ScreenDef {
  const items = [...s.items];
  if (it) items[i] = it;
  else items.splice(i, 1);
  return { ...s, items };
}

// Photos and videos of an item, while editing: add more, take one off, move one first.
export function MediaEdit({ media, onChange }: { media: Media[]; onChange: (m: Media[]) => void }) {
  const [busy, setBusy] = useState("");
  const add = async (files: FileList) => {
    const next = [...media];
    for (const f of [...files]) {
      if (!MEDIA_TYPES.test(f.type)) continue;
      setBusy(`adding ${f.name}…`);
      try {
        next.push(await saveMedia(f));
      } catch (err) {
        window.alert(String(err instanceof Error ? err.message : err));
      }
    }
    setBusy("");
    onChange(next);
  };
  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 font-['Silkscreen'] text-[10px]" onClick={(ev) => ev.stopPropagation()}>
      {media.map((m, k) => (
        <span key={m.src + k} className="flex items-center gap-1 bg-black/10 px-2 py-1">
          {m.kind === "video" ? "▶" : "▣"} {m.src.split("/").pop()}
          {k > 0 && <EditButton onClick={() => onChange([m, ...media.filter((_, j) => j !== k)])} title="Show this first">first</EditButton>}
          <EditButton onClick={() => onChange(media.filter((_, j) => j !== k))} title="Take it off">✕</EditButton>
        </span>
      ))}
      <label className="cursor-pointer px-2 py-1 uppercase tracking-wider" style={{ background: "#86a86b", color: "#1a1512" }}>
        {busy || "+ photos / videos"}
        <input type="file" accept="image/*,video/mp4,video/webm" multiple className="hidden" onChange={(ev) => ev.target.files && add(ev.target.files)} />
      </label>
    </div>
  );
}

// Links (label → address), while editing.
export function LinksEdit({ links, onChange }: { links: { label: string; href: string }[]; onChange: (l: { label: string; href: string }[]) => void }) {
  return (
    <div className="mt-3 space-y-1 font-['VT323'] text-[18px]" onClick={(ev) => ev.stopPropagation()}>
      {links.map((l, k) => (
        <div key={k} className="flex items-center gap-2">
          <Ed value={l.label} placeholder="label" onChange={(v) => onChange(links.map((x, j) => (j === k ? { ...x, label: v } : x)))} />
          →
          <Ed value={l.href} placeholder="https://…" onChange={(v) => onChange(links.map((x, j) => (j === k ? { ...x, href: v.trim() } : x)))} className="opacity-80" />
          <EditButton onClick={() => onChange(links.filter((_, j) => j !== k))}>✕</EditButton>
        </div>
      ))}
      <EditButton onClick={() => onChange([...links, { label: "a link", href: "https://" }])}>+ link</EditButton>
    </div>
  );
}

import { TuneMaker } from "./TuneMaker";
import { useState, type CSSProperties, type ReactNode } from "react";
import { Ed, EditButton, EditCtx, LinksEdit, MediaEdit, useEdit, withItem } from "./screenEdit";
import { BASE } from "./types";
import { fileUrl } from "./store";
import type { Media, ScreenDef, ScreenItem, Tone } from "./screenData";

// What you see after walking up to an object: a full screen in the café's pixel style
// (pixel fonts, notched frames, hard shadows, pixel sprites). Each screen is data from
// screens.json and is drawn with one of a few templates: a glass case you browse, a
// chalkboard menu, a bookshelf, a record player, a receipt, or a plain text page.

type Props = { screen: ScreenDef; playing: boolean; onMusic: (on: boolean) => void; onClose: () => void; onEdit?: (s: ScreenDef) => void };

const SPINES = ["#cf7a56", "#86a86b", "#6488aa", "#e8b45c", "#e89aa8", "#a3523a", "#5f8251", "#3c5878"];
const INK = "#2b1d1a";

// A box with notched pixel corners and a hard drop shadow, made from stacked box-shadows.
export function pixelBox(fill: string, edge = INK, px = 4, shadow = "rgba(0,0,0,0.35)"): CSSProperties {
  return {
    background: fill,
    boxShadow: [
      `0 -${px}px 0 0 ${edge}`,
      `0 ${px}px 0 0 ${edge}`,
      `-${px}px 0 0 0 ${edge}`,
      `${px}px 0 0 0 ${edge}`,
      `0 ${px * 2}px 0 0 ${shadow}`,
      `${px}px ${px}px 0 0 ${shadow}`,
      `-${px}px ${px}px 0 0 ${shadow}`,
    ].join(", "),
  };
}

const sprite = (name: string) => `${BASE}ui/${name}.png`;

const TONES: Record<Tone, { fill: string; ink: string; soft: string; accent: string; edge: string }> = {
  cream: { fill: "#f7efe1", ink: "#2b1d1a", soft: "rgba(43,29,26,0.25)", accent: "#5f8251", edge: INK },
  chalk: { fill: "#24342c", ink: "#f3e6c9", soft: "rgba(243,230,201,0.25)", accent: "#f6d58a", edge: "#8f5b3e" },
  wood: { fill: "#3a2219", ink: "#f3e6c9", soft: "rgba(243,230,201,0.22)", accent: "#e8b45c", edge: "#8f5b3e" },
};

export function PixelButton({ onClick, children, fill = "#86a86b", ink = INK, title, disabled }: { onClick: () => void; children: ReactNode; fill?: string; ink?: string; title?: string; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      title={title}
      disabled={disabled}
      className="px-3 py-1 font-['Pixelify_Sans'] text-[15px] transition-transform active:translate-y-[2px] disabled:opacity-60"
      style={{ ...pixelBox(fill, ink, 2, "rgba(0,0,0,0.3)"), color: ink }}
    >
      {children}
    </button>
  );
}

export function Frame({ screen, title, kicker, onBack, onClose, children }: { screen: ScreenDef; title?: ReactNode; kicker?: ReactNode; onBack?: () => void; onClose: () => void; children: ReactNode }) {
  const t = TONES[screen.tone] ?? TONES.cream;
  const e = useEdit();
  return (
    <div
      className="relative m-2 flex max-h-[min(640px,84dvh)] w-[min(680px,90vw)] flex-col [&_img]:[image-rendering:pixelated]"
      style={{ ...pixelBox(t.fill, t.edge), color: t.ink }}
      onClick={(e) => e.stopPropagation()}
    >
      <header className="flex items-start gap-3 px-6 pb-4 pt-5" style={{ borderBottom: `4px dashed ${t.soft}` }}>
        {onBack && (
          <PixelButton onClick={onBack} fill={t.fill} ink={t.ink}>
            ← back
          </PixelButton>
        )}
        <div className="min-w-0 flex-1">
          <p className="font-['Silkscreen'] text-[11px] uppercase tracking-wider" style={{ color: t.accent }}>
            {kicker ?? <Ed value={screen.kicker} placeholder="kicker" onChange={(v) => e?.set({ ...screen, kicker: v })} />}
          </p>
          <h2 className="mt-1 font-['Pixelify_Sans'] text-4xl leading-tight sm:text-[44px]">{title ?? <Ed value={screen.title} placeholder="title" onChange={(v) => e?.set({ ...screen, title: v })} />}</h2>
        </div>
        <EditToggle />
        <PixelButton onClick={onClose} fill={t.fill} ink={t.ink} title="Close (Esc)">
          x
        </PixelButton>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5 font-['VT323'] text-[22px] leading-snug">{children}</div>
    </div>
  );
}

function Body({ lines, onChange }: { lines: string[]; onChange?: (lines: string[]) => void }) {
  const e = useEdit();
  if (e?.on && onChange)
    return (
      <div className="opacity-90">
        <Ed multi value={lines.join("\n")} placeholder="write something…" onChange={(v) => onChange(v.split("\n"))} />
      </div>
    );
  return (
    <div className="space-y-2 opacity-90">
      {lines.filter(Boolean).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
    </div>
  );
}

function LinkRow({ links, screen, onChange }: { links: { label: string; href: string }[]; screen: ScreenDef; onChange?: (l: { label: string; href: string }[]) => void }) {
  const t = TONES[screen.tone] ?? TONES.cream;
  const e = useEdit();
  if (e?.on && onChange) return <LinksEdit links={links} onChange={onChange} />;
  if (!links.length) return null;
  return (
    <div className="mt-6 flex flex-wrap gap-4">
      {links.map((l) => (
        <a
          key={l.label + l.href}
          href={l.href}
          target={l.href.startsWith("http") ? "_blank" : undefined}
          rel="noreferrer"
          className="px-3 py-1 font-['Pixelify_Sans'] text-[15px] transition-transform hover:-translate-y-0.5"
          style={{ ...pixelBox(t.fill, t.ink, 2, "rgba(0,0,0,0.3)"), color: t.ink }}
        >
          {l.label}
        </a>
      ))}
    </div>
  );
}

function Dotted({ item, color, onChange }: { item: ScreenItem; color: string; onChange?: (it: ScreenItem | null) => void }) {
  const e = useEdit();
  if (e?.on && onChange)
    return (
      <div className="flex items-baseline gap-3">
        <Ed value={item.title} placeholder="name" onChange={(v) => onChange({ ...item, title: v })} />
        <span className="flex-1" style={{ borderBottom: `4px dotted ${color}` }} />
        <Ed value={item.meta ?? ""} placeholder="price / date" onChange={(v) => onChange({ ...item, meta: v })} className="opacity-70" />
        <EditButton onClick={() => onChange(null)}>✕</EditButton>
      </div>
    );
  const row = (
    <>
      <span>{item.title}</span>
      <span className="flex-1" style={{ borderBottom: `4px dotted ${color}` }} />
      <span className="opacity-70">{item.meta}</span>
    </>
  );
  return item.href ? (
    <a href={item.href} target={item.href.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="flex items-baseline gap-3 hover:opacity-80">
      {row}
    </a>
  ) : (
    <div className="flex items-baseline gap-3">{row}</div>
  );
}

// One photo or video, as big as it fits; videos play muted on a loop (with controls).
function MediaView({ m, className = "", fit = "contain" }: { m: Media; className?: string; fit?: "contain" | "cover" }) {
  const style = { objectFit: fit, imageRendering: "auto" } as CSSProperties;
  return m.kind === "video" ? (
    <video src={fileUrl(m.src)} className={className} style={style} autoPlay muted loop playsInline controls={fit === "contain"} />
  ) : (
    <img src={fileUrl(m.src)} alt="" className={className} style={style} loading="lazy" />
  );
}

// A gallery: the picked photo or video large, the rest as thumbnails to pick from.
function Gallery({ media, frame = "#2b1d1a" }: { media: Media[]; frame?: string }) {
  const [i, setI] = useState(0);
  const m = media[Math.min(i, media.length - 1)];
  if (!m) return null;
  return (
    <div>
      <div className="flex h-[min(46dvh,340px)] items-center justify-center bg-black/80" style={pixelBox("#15131c", frame, 3, "rgba(0,0,0,0.25)")}>
        <MediaView m={m} className="h-full w-full" />
      </div>
      {media.length > 1 && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {media.map((x, k) => (
            <button key={x.src + k} onClick={() => setI(k)} className="relative h-14 w-14 shrink-0 overflow-hidden" style={{ outline: k === i ? `3px solid ${frame}` : "none", opacity: k === i ? 1 : 0.7 }}>
              <MediaView m={x} className="h-full w-full" fit="cover" />
              {x.kind === "video" && <span className="absolute bottom-0 left-0 bg-black/70 px-1 font-['Silkscreen'] text-[8px] text-white">▶</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Detail page for one item (a pastry you picked, a book you pulled out).
function ItemDetail({ screen, item, index, onBack, onClose }: { screen: ScreenDef; item: ScreenItem; index: number; onBack: () => void; onClose: () => void }) {
  const e = useEdit();
  const put = (it: ScreenItem) => e?.set(withItem(screen, index, it));
  return (
    <Frame
      screen={screen}
      title={<Ed value={item.title} placeholder="name" onChange={(v) => put({ ...item, title: v })} />}
      kicker={e?.on ? <Ed value={item.meta ?? ""} placeholder="subtitle / date" onChange={(v) => put({ ...item, meta: v })} /> : item.meta || screen.kicker}
      onBack={onBack}
      onClose={onClose}
    >
      {item.media?.length ? (
        <div className="mb-5">
          <Gallery media={item.media} />
        </div>
      ) : null}
      {e?.on && <MediaEdit media={item.media ?? []} onChange={(m) => put({ ...item, media: m })} />}
      <div className="flex items-start gap-5">
        {item.sprite && (
          <div className="shrink-0 p-3" style={pixelBox("#d6eef1", "#c98f3c", 4, "rgba(0,0,0,0.2)")}>
            <img src={sprite(item.sprite)} alt="" className="h-16 w-auto" />
          </div>
        )}
        <Body lines={(item.note ?? "").split("\n")} onChange={(l) => put({ ...item, note: l.join("\n") })} />
      </div>
      {e?.on ? (
        <LinksEdit links={item.links ?? []} onChange={(l) => put({ ...item, links: l })} />
      ) : (
        <LinkRow links={[...(item.href ? [{ label: "Open", href: item.href }] : []), ...(item.links ?? [])]} screen={screen} />
      )}
    </Frame>
  );
}

// ---------------------------------------------------------------- templates

function CaseTemplate({ screen, onClose }: Props) {
  const e = useEdit();
  const [open, setOpen] = useState<number | null>(null);
  if (open !== null && screen.items[open]) return <ItemDetail screen={screen} item={screen.items[open]} index={open} onBack={() => setOpen(null)} onClose={onClose} />;
  return (
    <Frame screen={screen} onClose={onClose}>
      <div className="mb-6">
        <Body lines={screen.body} onChange={(l) => e?.set({ ...screen, body: l })} />
      </div>
      <div className="p-4" style={pixelBox("#d6eef1", "#c98f3c", 4, "rgba(0,0,0,0.25)")}>
        <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-4">
          {screen.items.map((it, i) => (
            <button key={i} onClick={() => setOpen(i)} className="group flex flex-col items-center">
              <span className="flex h-20 items-end transition-transform group-hover:-translate-y-1.5">
                <img src={sprite(it.sprite || "pastry-croissant")} alt="" className="h-14 w-auto" />
              </span>
              <span className="mt-1 h-1 w-20 bg-[#9fcbd3]" />
              <span className="mt-2 px-2 font-['Silkscreen'] text-[10px] text-[#2b1d1a]" style={pixelBox("#fdf8ef", INK, 2, "transparent")}>
                {it.title}
              </span>
              {e?.on && <EditButton onClick={() => e.set(withItem(screen, i, null))}>✕</EditButton>}
            </button>
          ))}
        </div>
        {e?.on && <AddItem />}
      </div>
      <LinkRow links={screen.links} screen={screen} onChange={(l) => e?.set({ ...screen, links: l })} />
    </Frame>
  );
}

function MenuTemplate({ screen, onClose }: Props) {
  const e = useEdit();
  const t = TONES[screen.tone] ?? TONES.chalk;
  const [open, setOpen] = useState<number | null>(null);
  if (open !== null && screen.items[open]) return <ItemDetail screen={screen} item={screen.items[open]} index={open} onBack={() => setOpen(null)} onClose={onClose} />;
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} onChange={(l) => e?.set({ ...screen, body: l })} />
      <ul className="mt-6 space-y-3">
        {screen.items.map((it, i) => (
          <li key={i}>
            {e?.on ? (
              <Dotted item={it} color={t.soft} onChange={(x) => e.set(withItem(screen, i, x))} />
            ) : it.note ? (
              <button onClick={() => setOpen(i)} className="w-full text-left hover:opacity-80">
                <Dotted item={{ ...it, href: undefined }} color={t.soft} />
              </button>
            ) : (
              <Dotted item={it} color={t.soft} />
            )}
          </li>
        ))}
      </ul>
      {e?.on && <AddItem />}
      <LinkRow links={screen.links} screen={screen} onChange={(l) => e?.set({ ...screen, links: l })} />
    </Frame>
  );
}

function ShelfTemplate({ screen, onClose }: Props) {
  const e = useEdit();
  const [pick, setPick] = useState<number | null>(null);
  const t = TONES[screen.tone] ?? TONES.wood;
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} onChange={(l) => e?.set({ ...screen, body: l })} />
      <div className="mt-6 flex h-44 items-end gap-2 overflow-x-auto px-3">
        {screen.items.map((b, i) => (
          <button
            key={i}
            onClick={() => setPick(i)}
            className={`relative flex w-11 shrink-0 items-center justify-center transition-transform hover:-translate-y-2 ${pick === i ? "-translate-y-4" : ""}`}
            style={{ ...pixelBox(SPINES[i % SPINES.length], INK, 3, "transparent"), height: `${72 + ((i * 37) % 26)}%` }}
            title={b.title}
          >
            <span className="absolute inset-x-0 top-3 h-1 bg-black/25" />
            <span className="absolute inset-x-0 bottom-3 h-1 bg-black/25" />
            <span className="absolute left-1 top-1 h-[calc(100%-8px)] w-1 bg-white/25" />
            <span className="rotate-[-90deg] whitespace-nowrap font-['Silkscreen'] text-[9px] text-[#fdf8ef]">{b.title}</span>
          </button>
        ))}
      </div>
      <div className="h-3 bg-[#8f5b3e]" style={{ boxShadow: "0 3px 0 0 #6b4232" }} />
      {e?.on && <AddItem />}
      <div className="mt-5 min-h-7">
        {pick === null ? (
          <p className="opacity-80">Pull a book off the shelf.</p>
        ) : (
          <>
            <p style={{ color: t.accent }}>
              <Ed value={screen.items[pick].title} placeholder="title" onChange={(v) => e?.set(withItem(screen, pick, { ...screen.items[pick], title: v }))} />
              {e?.on ? (
                <>
                  {" · "}
                  <Ed value={screen.items[pick].meta ?? ""} placeholder="author" onChange={(v) => e.set(withItem(screen, pick, { ...screen.items[pick], meta: v }))} />{" "}
                  <EditButton onClick={() => (setPick(null), e.set(withItem(screen, pick, null)))}>✕</EditButton>
                </>
              ) : screen.items[pick].meta ? (
                ` · ${screen.items[pick].meta}`
              ) : (
                ""
              )}
            </p>
            <Body lines={(screen.items[pick].note ?? "").split("\n")} onChange={(l) => e?.set(withItem(screen, pick, { ...screen.items[pick], note: l.join("\n") }))} />
          </>
        )}
      </div>
      <LinkRow links={screen.links} screen={screen} onChange={(l) => e?.set({ ...screen, links: l })} />
    </Frame>
  );
}

function MusicTemplate({ screen, playing, onMusic, onClose }: Props) {
  const e = useEdit();
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} onChange={(l) => e?.set({ ...screen, body: l })} />
      <div className="mt-6 flex items-center gap-6">
        {/* stepped spin keeps the record looking like pixel art */}
        <img src={sprite("record")} alt="" className={`h-32 w-32 shrink-0 ${playing ? "animate-spin [animation-duration:2.4s] [animation-timing-function:steps(8)]" : ""}`} />
        <div>
          <PixelButton onClick={() => onMusic(!playing)}>{playing ? "■ pause" : "▶ play café loop"}</PixelButton>
          <ul className="mt-4 space-y-1 opacity-90">
            {screen.items.map((it, i) => (
              <li key={i}>
                {e?.on ? (
                  <Dotted item={it} color="rgba(243,230,201,0.25)" onChange={(x) => e.set(withItem(screen, i, x))} />
                ) : (
                  <>
                    ♪ {it.title} {it.meta && <span className="opacity-60">· {it.meta}</span>}
                  </>
                )}
              </li>
            ))}
          </ul>
          {e?.on && <AddItem />}
        </div>
      </div>
      {/* make-a-tune (api/music.ts + music-space/): off until the Hugging Face Space is up */}
      {import.meta.env.VITE_MUSIC_ON === "1" && <TuneMaker onPlay={() => playing && onMusic(false)} />}
      <LinkRow links={screen.links} screen={screen} onChange={(l) => e?.set({ ...screen, links: l })} />
    </Frame>
  );
}

function ReceiptTemplate({ screen, onClose }: Props) {
  const e = useEdit();
  return (
    <Frame screen={screen} onClose={onClose}>
      <div className="mx-auto max-w-sm px-6 py-5 text-[#2b1d1a]" style={pixelBox("#fdf8ef", "#e2cfa8", 3, "rgba(0,0,0,0.15)")}>
        <p className="text-center font-['Silkscreen'] text-sm">DANIEL'S CAFÉ</p>
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        <Body lines={screen.body} onChange={(l) => e?.set({ ...screen, body: l })} />
        {(screen.items.length > 0 || e?.on) && (
          <>
            <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
            {screen.items.map((it, i) => (
              <Dotted key={i} item={it} color="rgba(43,29,26,0.25)" onChange={(x) => e?.set(withItem(screen, i, x))} />
            ))}
            {e?.on && <AddItem />}
          </>
        )}
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        {e?.on && <LinksEdit links={screen.links} onChange={(l) => e.set({ ...screen, links: l })} />}
        {!e?.on && screen.links.map((l) => (
          <a key={l.label + l.href} href={l.href} target={l.href.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="flex justify-between hover:text-[#5f8251]">
            <span>{l.label}</span>
            <span>→</span>
          </a>
        ))}
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        <p className="flex items-center justify-center gap-2">
          thanks for stopping by <img src={sprite("cup")} alt="" className="h-6 w-auto" />
        </p>
      </div>
    </Frame>
  );
}

function TextTemplate({ screen, onClose }: Props) {
  const e = useEdit();
  const t = TONES[screen.tone] ?? TONES.cream;
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} onChange={(l) => e?.set({ ...screen, body: l })} />
      {(screen.items.length > 0 || e?.on) && (
        <div className="mt-5 space-y-2">
          {screen.items.map((it, i) => (
            <Dotted key={i} item={it} color={t.soft} onChange={(x) => e?.set(withItem(screen, i, x))} />
          ))}
          {e?.on && <AddItem />}
        </div>
      )}
      <LinkRow links={screen.links} screen={screen} onChange={(l) => e?.set({ ...screen, links: l })} />
    </Frame>
  );
}

// ---------------------------------------------------------------- the laptop

// Projects on the café laptop: a pixel laptop with a little website open on it. Each project
// is a box (its demo playing, or its sprite), and opens to its demo, the story and its links.
function LaptopTemplate({ screen, onClose }: Props) {
  const e = useEdit();
  const [open, setOpen] = useState<number | null>(null);
  const item = open !== null ? screen.items[open] : null;
  const put = (it: ScreenItem | null) => open !== null && e?.set(withItem(screen, open, it));
  const tags = (t?: string) =>
    (t ?? "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  return (
    <div className="relative m-2 flex w-[min(880px,94vw)] flex-col items-center" onClick={(e) => e.stopPropagation()}>
      {/* the lid: dark bezel, the screen inside */}
      <div className="w-full p-3 sm:p-4" style={pixelBox("#2f2b33", INK, 4, "rgba(0,0,0,0.4)")}>
        <div className="flex h-[min(560px,70dvh)] flex-col overflow-hidden bg-[#fbf6ec] text-[#2b1d1a]">
          {/* a browser bar */}
          <div className="flex shrink-0 items-center gap-2 border-b-2 border-[#2b1d1a]/15 bg-[#efe4d0] px-3 py-1.5">
            <span className="flex gap-1">
              {["#e0695a", "#e8b45c", "#86a86b"].map((c) => (
                <span key={c} className="h-2.5 w-2.5" style={{ background: c }} />
              ))}
            </span>
            {item && (
              <button onClick={() => setOpen(null)} className="font-['Silkscreen'] text-[10px] hover:opacity-70">
                ← back
              </button>
            )}
            <span className="min-w-0 flex-1 truncate bg-white/70 px-2 py-0.5 font-['VT323'] text-[15px] opacity-80">
              daniel.cafe/{item ? `projects/${item.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}` : "projects"}
            </span>
            <EditToggle />
            <button onClick={onClose} className="font-['Silkscreen'] text-[12px] hover:opacity-70" title="Close">
              ✕
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-7">
            {item ? (
              <article className="mx-auto max-w-2xl">
                <p className="font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-60">
                  <Ed value={item.meta ?? ""} placeholder="when / what" onChange={(v) => put({ ...item, meta: v })} />
                </p>
                <h2 className="mt-1 font-['Instrument_Serif'] text-4xl italic leading-tight">
                  <Ed value={item.title} placeholder="project name" onChange={(v) => put({ ...item, title: v })} />
                </h2>
                {e?.on && (
                  <p className="mt-2 font-['Silkscreen'] text-[10px]">
                    tags: <Ed value={item.tags ?? ""} placeholder="react, python, …" onChange={(v) => put({ ...item, tags: v })} />{" "}
                    <EditButton onClick={() => (setOpen(null), put(null))}>delete project</EditButton>
                  </p>
                )}
                {!e?.on && tags(item.tags).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {tags(item.tags).map((t) => (
                      <span key={t} className="bg-[#2b1d1a]/8 px-2 py-0.5 font-['Silkscreen'] text-[9px] uppercase tracking-wider" style={{ background: "rgba(43,29,26,0.08)" }}>
                        {t}
                      </span>
                    ))}
                  </div>
                )}
                {item.media?.length ? (
                  <div className="mt-5">
                    <Gallery media={item.media} />
                  </div>
                ) : null}
                {e?.on && <MediaEdit media={item.media ?? []} onChange={(m) => put({ ...item, media: m })} />}
                <div className="mt-5 space-y-3 font-['Space_Grotesk'] text-[15px] leading-relaxed">
                  {e?.on ? (
                    <Ed multi value={item.note ?? ""} placeholder="what it is, what you did, what you learned…" onChange={(v) => put({ ...item, note: v })} />
                  ) : (
                    (item.note ?? "").split("\n").filter((l) => l.trim()).map((l, k) => <p key={k}>{l}</p>)
                  )}
                </div>
                {e?.on && <LinksEdit links={item.links ?? []} onChange={(l) => put({ ...item, links: l })} />}
                <div className={`mt-6 flex flex-wrap gap-3 ${e?.on ? "hidden" : ""}`}>
                  {[...(item.href ? [{ label: "Open", href: item.href }] : []), ...(item.links ?? [])].map((l) => (
                    <a key={l.label + l.href} href={l.href} target="_blank" rel="noreferrer" className="px-3 py-1 font-['Pixelify_Sans'] text-[15px] transition-transform hover:-translate-y-0.5" style={pixelBox("#e8b45c", INK, 2, "rgba(0,0,0,0.25)")}>
                      {l.label} ↗
                    </a>
                  ))}
                </div>
              </article>
            ) : (
              <>
                <header className="mb-6">
                  <p className="font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-60">
                    <Ed value={screen.kicker} placeholder="kicker" onChange={(v) => e?.set({ ...screen, kicker: v })} />
                  </p>
                  <h2 className="mt-1 font-['Instrument_Serif'] text-4xl italic leading-tight">
                    <Ed value={screen.title} placeholder="title" onChange={(v) => e?.set({ ...screen, title: v })} />
                  </h2>
                  {e?.on ? (
                    <p className="mt-2 max-w-xl font-['Space_Grotesk'] text-[15px] opacity-80">
                      <Ed multi value={screen.body.join("\n")} placeholder="a line about your projects" onChange={(v) => e.set({ ...screen, body: v.split("\n") })} />
                    </p>
                  ) : (
                    screen.body.filter((l) => l.trim()).map((l, k) => (
                      <p key={k} className="mt-2 max-w-xl font-['Space_Grotesk'] text-[15px] opacity-80">
                        {l}
                      </p>
                    ))
                  )}
                </header>
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                  {screen.items.map((it, i) => (
                    <button key={i} onClick={() => setOpen(i)} className="group text-left transition-transform hover:-translate-y-1" style={pixelBox("#ffffff", INK, 3, "rgba(0,0,0,0.18)")}>
                      <div className="flex aspect-video items-center justify-center overflow-hidden bg-[#efe4d0]">
                        {it.media?.[0] ? (
                          <MediaView m={it.media[0]} className="h-full w-full" fit="cover" />
                        ) : (
                          <img src={sprite(it.sprite || "cup")} alt="" className="h-16 w-auto [image-rendering:pixelated] transition-transform group-hover:scale-110" />
                        )}
                      </div>
                      <div className="p-3">
                        <p className="font-['Pixelify_Sans'] text-[18px] leading-tight">{it.title}</p>
                        {it.meta && <p className="mt-0.5 font-['Silkscreen'] text-[9px] uppercase tracking-wider opacity-60">{it.meta}</p>}
                        {it.note && <p className="mt-2 line-clamp-2 font-['Space_Grotesk'] text-[13px] opacity-75">{it.note}</p>}
                        {tags(it.tags).length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {tags(it.tags).slice(0, 4).map((t) => (
                              <span key={t} className="px-1.5 py-px font-['Silkscreen'] text-[8px] uppercase tracking-wider" style={{ background: "rgba(43,29,26,0.08)" }}>
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                {e?.on && (
                  <div className="mt-4">
                    <EditButton onClick={() => (e.set({ ...screen, items: [...screen.items, { title: "New project", meta: "", note: "", tags: "" }] }), setOpen(screen.items.length))}>+ add project</EditButton>
                    <LinksEdit links={screen.links} onChange={(l) => e.set({ ...screen, links: l })} />
                  </div>
                )}
                {!e?.on && screen.links.length > 0 && (
                  <div className="mt-8 flex flex-wrap gap-3 border-t-2 border-dashed border-[#2b1d1a]/15 pt-5">
                    {screen.links.map((l) => (
                      <a key={l.href} href={l.href} target="_blank" rel="noreferrer" className="font-['Pixelify_Sans'] text-[15px] underline decoration-2 underline-offset-4 hover:opacity-70">
                        {l.label} ↗
                      </a>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      {/* the base: the keyboard deck, a little wider than the lid */}
      <div className="h-3 w-[104%]" style={{ ...pixelBox("#9a93a0", INK, 3, "rgba(0,0,0,0.35)") }} />
    </div>
  );
}

// while editing: a new item at the end of the screen's list
function AddItem() {
  const e = useEdit();
  if (!e?.on) return null;
  return (
    <div className="mt-4">
      <EditButton onClick={() => e.set({ ...e.screen, items: [...e.screen.items, { title: "new", meta: "", note: "" }] })}>+ add</EditButton>
    </div>
  );
}

// the ✎ edit / done switch in a screen's corner (only where editing is possible: Daniel's dev server)
function EditToggle() {
  const e = useEdit();
  if (!e?.can) return null;
  return (
    <button
      onClick={(ev) => {
        ev.stopPropagation();
        (document.activeElement as HTMLElement | null)?.blur(); // (finish a field being typed in)
        e.toggle();
      }}
      className="shrink-0 px-2 py-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider"
      style={{ background: e.on ? "#86a86b" : "#e8b45c", color: "#1a1512", boxShadow: "0 2px 0 rgba(0,0,0,0.3)" }}
      title="Edit this screen in place"
    >
      {e.on ? "✓ done" : "✎ edit"}
    </button>
  );
}

export function CafeScreen(props: Props) {
  const [on, setOn] = useState(false);
  const can = !!props.onEdit;
  return (
    <EditCtx.Provider value={{ on: on && can, can, toggle: () => setOn((x) => !x), set: (s) => props.onEdit?.(s), screen: props.screen }}>
      <TemplateOf {...props} />
    </EditCtx.Provider>
  );
}

function TemplateOf(props: Props) {
  switch (props.screen.template) {
    case "laptop":
      return <LaptopTemplate {...props} />;
    case "case":
      return <CaseTemplate {...props} />;
    case "menu":
      return <MenuTemplate {...props} />;
    case "shelf":
      return <ShelfTemplate {...props} />;
    case "music":
      return <MusicTemplate {...props} />;
    case "receipt":
      return <ReceiptTemplate {...props} />;
    default:
      return <TextTemplate {...props} />;
  }
}

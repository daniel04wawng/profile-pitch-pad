import { useState, type CSSProperties, type ReactNode } from "react";
import { BASE } from "./types";
import type { ScreenDef, ScreenItem, Tone } from "./screenData";

// What you see after walking up to an object: a full screen in the café's pixel style
// (pixel fonts, notched frames, hard shadows, pixel sprites). Each screen is data from
// screens.json and is drawn with one of a few templates: a glass case you browse, a
// chalkboard menu, a bookshelf, a record player, a receipt, or a plain text page.

type Props = { screen: ScreenDef; playing: boolean; onMusic: (on: boolean) => void; onClose: () => void };

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

export function PixelButton({ onClick, children, fill = "#86a86b", ink = INK, title }: { onClick: () => void; children: ReactNode; fill?: string; ink?: string; title?: string }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="px-3 py-1 font-['Pixelify_Sans'] text-[15px] transition-transform active:translate-y-[2px]"
      style={{ ...pixelBox(fill, ink, 2, "rgba(0,0,0,0.3)"), color: ink }}
    >
      {children}
    </button>
  );
}

export function Frame({ screen, title, kicker, onBack, onClose, children }: { screen: ScreenDef; title?: string; kicker?: string; onBack?: () => void; onClose: () => void; children: ReactNode }) {
  const t = TONES[screen.tone] ?? TONES.cream;
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
            {kicker ?? screen.kicker}
          </p>
          <h2 className="mt-1 font-['Pixelify_Sans'] text-4xl leading-tight sm:text-[44px]">{title ?? screen.title}</h2>
        </div>
        <PixelButton onClick={onClose} fill={t.fill} ink={t.ink} title="Close (Esc)">
          x
        </PixelButton>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5 font-['VT323'] text-[22px] leading-snug">{children}</div>
    </div>
  );
}

function Body({ lines }: { lines: string[] }) {
  return (
    <div className="space-y-2 opacity-90">
      {lines.filter(Boolean).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
    </div>
  );
}

function LinkRow({ links, screen }: { links: { label: string; href: string }[]; screen: ScreenDef }) {
  const t = TONES[screen.tone] ?? TONES.cream;
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

function Dotted({ item, color }: { item: ScreenItem; color: string }) {
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

// Detail page for one item (a pastry you picked, a book you pulled out).
function ItemDetail({ screen, item, onBack, onClose }: { screen: ScreenDef; item: ScreenItem; onBack: () => void; onClose: () => void }) {
  return (
    <Frame screen={screen} title={item.title} kicker={item.meta || screen.kicker} onBack={onBack} onClose={onClose}>
      <div className="flex items-start gap-5">
        {item.sprite && (
          <div className="shrink-0 p-3" style={pixelBox("#d6eef1", "#c98f3c", 4, "rgba(0,0,0,0.2)")}>
            <img src={sprite(item.sprite)} alt="" className="h-16 w-auto" />
          </div>
        )}
        <Body lines={(item.note ?? "").split("\n")} />
      </div>
      {item.href && <LinkRow links={[{ label: "Open", href: item.href }]} screen={screen} />}
    </Frame>
  );
}

// ---------------------------------------------------------------- templates

function CaseTemplate({ screen, onClose }: Props) {
  const [open, setOpen] = useState<number | null>(null);
  if (open !== null && screen.items[open]) return <ItemDetail screen={screen} item={screen.items[open]} onBack={() => setOpen(null)} onClose={onClose} />;
  return (
    <Frame screen={screen} onClose={onClose}>
      <div className="mb-6">
        <Body lines={screen.body} />
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
            </button>
          ))}
        </div>
      </div>
      <LinkRow links={screen.links} screen={screen} />
    </Frame>
  );
}

function MenuTemplate({ screen, onClose }: Props) {
  const t = TONES[screen.tone] ?? TONES.chalk;
  const [open, setOpen] = useState<number | null>(null);
  if (open !== null && screen.items[open]) return <ItemDetail screen={screen} item={screen.items[open]} onBack={() => setOpen(null)} onClose={onClose} />;
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} />
      <ul className="mt-6 space-y-3">
        {screen.items.map((it, i) => (
          <li key={i}>
            {it.note ? (
              <button onClick={() => setOpen(i)} className="w-full text-left hover:opacity-80">
                <Dotted item={{ ...it, href: undefined }} color={t.soft} />
              </button>
            ) : (
              <Dotted item={it} color={t.soft} />
            )}
          </li>
        ))}
      </ul>
      <LinkRow links={screen.links} screen={screen} />
    </Frame>
  );
}

function ShelfTemplate({ screen, onClose }: Props) {
  const [pick, setPick] = useState<number | null>(null);
  const t = TONES[screen.tone] ?? TONES.wood;
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} />
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
      <div className="mt-5 min-h-7">
        {pick === null ? (
          <p className="opacity-80">Pull a book off the shelf.</p>
        ) : (
          <>
            <p style={{ color: t.accent }}>
              {screen.items[pick].title}
              {screen.items[pick].meta ? ` · ${screen.items[pick].meta}` : ""}
            </p>
            <Body lines={(screen.items[pick].note ?? "").split("\n")} />
          </>
        )}
      </div>
      <LinkRow links={screen.links} screen={screen} />
    </Frame>
  );
}

function MusicTemplate({ screen, playing, onMusic, onClose }: Props) {
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} />
      <div className="mt-6 flex items-center gap-6">
        {/* stepped spin keeps the record looking like pixel art */}
        <img src={sprite("record")} alt="" className={`h-32 w-32 shrink-0 ${playing ? "animate-spin [animation-duration:2.4s] [animation-timing-function:steps(8)]" : ""}`} />
        <div>
          <PixelButton onClick={() => onMusic(!playing)}>{playing ? "■ pause" : "▶ play café loop"}</PixelButton>
          <ul className="mt-4 space-y-1 opacity-90">
            {screen.items.map((it, i) => (
              <li key={i}>
                ♪ {it.title} {it.meta && <span className="opacity-60">· {it.meta}</span>}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <LinkRow links={screen.links} screen={screen} />
    </Frame>
  );
}

function ReceiptTemplate({ screen, onClose }: Props) {
  return (
    <Frame screen={screen} onClose={onClose}>
      <div className="mx-auto max-w-sm px-6 py-5 text-[#2b1d1a]" style={pixelBox("#fdf8ef", "#e2cfa8", 3, "rgba(0,0,0,0.15)")}>
        <p className="text-center font-['Silkscreen'] text-sm">DANIEL'S CAFÉ</p>
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        <Body lines={screen.body} />
        {screen.items.length > 0 && (
          <>
            <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
            {screen.items.map((it, i) => (
              <Dotted key={i} item={it} color="rgba(43,29,26,0.25)" />
            ))}
          </>
        )}
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        {screen.links.map((l) => (
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
  const t = TONES[screen.tone] ?? TONES.cream;
  return (
    <Frame screen={screen} onClose={onClose}>
      <Body lines={screen.body} />
      {screen.items.length > 0 && (
        <div className="mt-5 space-y-2">
          {screen.items.map((it, i) => (
            <Dotted key={i} item={it} color={t.soft} />
          ))}
        </div>
      )}
      <LinkRow links={screen.links} screen={screen} />
    </Frame>
  );
}

export function CafeScreen(props: Props) {
  switch (props.screen.template) {
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

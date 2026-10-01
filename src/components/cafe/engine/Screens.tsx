import { useState, type CSSProperties, type ReactNode } from "react";
import { PROJECTS, SECTIONS, type Section } from "../content";
import { BASE } from "./types";

// What you see after walking up to an object: a full screen themed to that object,
// drawn in the same pixel style as the café (pixel fonts, notched frames, hard shadows,
// pixel sprites). The pastry case is a case you browse, the menu is a chalkboard, and so on.

type ScreenProps = { hotspot: string; playing: boolean; onMusic: (on: boolean) => void; onClose: () => void };

// Which screen each hotspot opens, with a name for the editor's "Screen" picker.
export const SCREENS: Record<string, string> = {
  projects: "Pastry case: projects",
  menu: "Menu board: blog",
  books: "Bookshelf: books I love",
  piano: "Music player",
  chill: "Sit and listen: music",
  contact: "Receipt: contact",
  about: "About me",
  now: "Special of the day",
};

const PASTRY_SPRITE: Record<string, string> = {
  croissant: "pastry-croissant",
  macaron: "pastry-macaron",
  cinnamon: "pastry-cinnamon",
  muffin: "pastry-muffin",
};
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

function PixelButton({ onClick, children, fill = "#86a86b", ink = INK, title }: { onClick: () => void; children: ReactNode; fill?: string; ink?: string; title?: string }) {
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

const TONES = {
  cream: { fill: "#f7efe1", ink: "#2b1d1a", soft: "rgba(43,29,26,0.25)", accent: "#5f8251" },
  chalk: { fill: "#24342c", ink: "#f3e6c9", soft: "rgba(243,230,201,0.25)", accent: "#f6d58a" },
  wood: { fill: "#3a2219", ink: "#f3e6c9", soft: "rgba(243,230,201,0.22)", accent: "#e8b45c" },
};

function Frame({
  kicker,
  title,
  tone = "cream",
  onBack,
  onClose,
  children,
}: {
  kicker: string;
  title: string;
  tone?: keyof typeof TONES;
  onBack?: () => void;
  onClose: () => void;
  children: ReactNode;
}) {
  const t = TONES[tone];
  return (
    <div
      className="relative m-2 flex max-h-[min(640px,84dvh)] w-[min(680px,90vw)] flex-col [&_img]:[image-rendering:pixelated]"
      style={{ ...pixelBox(t.fill, tone === "cream" ? INK : "#8f5b3e"), color: t.ink }}
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
            {kicker}
          </p>
          <h2 className="mt-1 font-['Pixelify_Sans'] text-4xl leading-tight sm:text-[44px]">{title}</h2>
        </div>
        <PixelButton onClick={onClose} fill={t.fill} ink={t.ink} title="Close (Esc)">
          x
        </PixelButton>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5 font-['VT323'] text-[22px] leading-snug">{children}</div>
    </div>
  );
}

function Body({ section }: { section: Section }) {
  return (
    <div className="space-y-2 opacity-90">
      {section.body.map((p) => (
        <p key={p}>{p}</p>
      ))}
    </div>
  );
}

function Links({ section, ink, fill }: { section: Section; ink: string; fill: string }) {
  if (!section.links) return null;
  return (
    <div className="mt-6 flex flex-wrap gap-4">
      {section.links.map((l) => (
        <a
          key={l.label}
          href={l.href}
          target={l.href.startsWith("http") ? "_blank" : undefined}
          rel="noreferrer"
          className="px-3 py-1 font-['Pixelify_Sans'] text-[15px] transition-transform hover:-translate-y-0.5"
          style={{ ...pixelBox(fill, ink, 2, "rgba(0,0,0,0.3)"), color: ink }}
        >
          {l.label}
        </a>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- screens

function PastryCase({ onClose }: ScreenProps) {
  const [open, setOpen] = useState<string | null>(null);
  const section = SECTIONS.projects;
  if (open) {
    const proj = PROJECTS.find((p) => p.id === open)!;
    const p = SECTIONS[`project:${open}`];
    return (
      <Frame kicker={p.kicker} title={p.title} onBack={() => setOpen(null)} onClose={onClose}>
        <div className="flex items-start gap-5">
          <div className="shrink-0 p-3" style={pixelBox("#d6eef1", "#c98f3c", 4, "rgba(0,0,0,0.2)")}>
            <img src={sprite(PASTRY_SPRITE[proj.pastry])} alt="" className="h-16 w-auto" />
          </div>
          <Body section={p} />
        </div>
        <Links section={p} ink={INK} fill="#f7efe1" />
      </Frame>
    );
  }
  return (
    <Frame kicker={section.kicker} title={section.title} onClose={onClose}>
      <p className="mb-6 opacity-80">Each pastry is a project. Pick one to read the story behind it.</p>
      {/* the glass case: brass frame, two glass shelves */}
      <div className="p-4" style={pixelBox("#d6eef1", "#c98f3c", 4, "rgba(0,0,0,0.25)")}>
        <div className="grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-4">
          {PROJECTS.map((p) => (
            <button key={p.id} onClick={() => setOpen(p.id)} className="group flex flex-col items-center">
              <span className="flex h-20 items-end transition-transform group-hover:-translate-y-1.5">
                <img src={sprite(PASTRY_SPRITE[p.pastry])} alt="" className="h-14 w-auto" />
              </span>
              {/* the glass shelf + a little price tag */}
              <span className="mt-1 h-1 w-20 bg-[#9fcbd3]" />
              <span className="mt-2 px-2 font-['Silkscreen'] text-[10px] text-[#2b1d1a]" style={pixelBox("#fdf8ef", INK, 2, "transparent")}>
                {p.name}
              </span>
            </button>
          ))}
        </div>
      </div>
    </Frame>
  );
}

function MenuBoard({ onClose }: ScreenProps) {
  const section = SECTIONS.menu;
  return (
    <Frame kicker={section.kicker} title={section.title} tone="chalk" onClose={onClose}>
      <Body section={section} />
      <ul className="mt-6 space-y-3">
        {(section.items ?? []).map((it) => (
          <li key={it.title} className="flex items-baseline gap-3">
            <span>{it.title}</span>
            <span className="flex-1" style={{ borderBottom: "4px dotted rgba(243,230,201,0.3)" }} />
            <span className="text-[#f6d58a]">{it.meta}</span>
          </li>
        ))}
      </ul>
    </Frame>
  );
}

function Bookshelf({ onClose }: ScreenProps) {
  const section = SECTIONS.books;
  const books = ["Favourite book", "Another one", "A third", "Something else", "One more"];
  const [pick, setPick] = useState<number | null>(null);
  return (
    <Frame kicker={section.kicker} title={section.title} tone="wood" onClose={onClose}>
      <Body section={section} />
      <div className="mt-6 flex h-44 items-end gap-2 px-3">
        {books.map((b, i) => {
          const h = 72 + ((i * 37) % 26);
          return (
            <button
              key={b}
              onClick={() => setPick(i)}
              className={`relative flex w-11 items-center justify-center transition-transform hover:-translate-y-2 ${pick === i ? "-translate-y-4" : ""}`}
              style={{ ...pixelBox(SPINES[i % SPINES.length], INK, 3, "transparent"), height: `${h}%` }}
              title={b}
            >
              {/* pixel bands near the top and bottom of the spine */}
              <span className="absolute inset-x-0 top-3 h-1 bg-black/25" />
              <span className="absolute inset-x-0 bottom-3 h-1 bg-black/25" />
              <span className="absolute left-1 top-1 h-[calc(100%-8px)] w-1 bg-white/25" />
              <span className="rotate-[-90deg] whitespace-nowrap font-['Silkscreen'] text-[9px] text-[#fdf8ef]">{b}</span>
            </button>
          );
        })}
      </div>
      <div className="h-3 bg-[#8f5b3e]" style={{ boxShadow: "0 3px 0 0 #6b4232" }} />
      <p className="mt-5 min-h-7 opacity-90">{pick === null ? "Pull a book off the shelf." : `${books[pick]}: placeholder note on why it stuck with you.`}</p>
    </Frame>
  );
}

function Music({ hotspot, playing, onMusic, onClose }: ScreenProps) {
  const section = SECTIONS[hotspot] ?? SECTIONS.piano;
  return (
    <Frame kicker={section.kicker} title={section.title} tone="wood" onClose={onClose}>
      <Body section={section} />
      <div className="mt-6 flex items-center gap-6">
        {/* stepped spin keeps the record looking like pixel art */}
        <img
          src={sprite("record")}
          alt=""
          className={`h-32 w-32 shrink-0 ${playing ? "animate-spin [animation-duration:2.4s] [animation-timing-function:steps(8)]" : ""}`}
        />
        <div>
          <PixelButton onClick={() => onMusic(!playing)}>{playing ? "■ pause" : "▶ play café loop"}</PixelButton>
          <ul className="mt-4 space-y-1 opacity-90">
            {(section.items ?? []).map((it) => (
              <li key={it.title}>
                ♪ {it.title} <span className="opacity-60">· {it.meta}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Frame>
  );
}

function Receipt({ onClose }: ScreenProps) {
  const section = SECTIONS.contact;
  return (
    <Frame kicker={section.kicker} title={section.title} onClose={onClose}>
      <div className="mx-auto max-w-sm px-6 py-5" style={pixelBox("#fdf8ef", "#e2cfa8", 3, "rgba(0,0,0,0.15)")}>
        <p className="text-center font-['Silkscreen'] text-sm">DANIEL'S CAFÉ</p>
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        {section.body.map((b) => (
          <p key={b} className="mb-1">
            {b}
          </p>
        ))}
        <div className="my-3" style={{ borderTop: "3px dashed rgba(43,29,26,0.35)" }} />
        {(section.links ?? []).map((l) => (
          <a key={l.label} href={l.href} target={l.href.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="flex justify-between hover:text-[#5f8251]">
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

function Generic({ hotspot, onClose }: ScreenProps) {
  const section = SECTIONS[hotspot];
  if (!section) return null;
  return (
    <Frame kicker={section.kicker} title={section.title} onClose={onClose}>
      <Body section={section} />
      {section.items && (
        <ul className="mt-5 space-y-2">
          {section.items.map((it) => (
            <li key={it.title} className="flex items-baseline gap-3">
              <span>{it.title}</span>
              <span className="flex-1" style={{ borderBottom: "4px dotted rgba(43,29,26,0.25)" }} />
              <span className="opacity-60">{it.meta}</span>
            </li>
          ))}
        </ul>
      )}
      <Links section={section} ink={INK} fill="#f7efe1" />
    </Frame>
  );
}

export function CafeScreen(props: ScreenProps) {
  switch (props.hotspot) {
    case "projects":
      return <PastryCase {...props} />;
    case "menu":
      return <MenuBoard {...props} />;
    case "books":
      return <Bookshelf {...props} />;
    case "piano":
    case "chill":
      return <Music {...props} />;
    case "contact":
      return <Receipt {...props} />;
    default:
      return <Generic {...props} />;
  }
}

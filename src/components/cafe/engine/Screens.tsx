import { useState, type ReactNode } from "react";
import { PROJECTS, SECTIONS, type Section } from "../content";

// What you see after walking up to an object: a full screen themed to that object.
// The pastry case is a case you browse, the menu is a chalkboard, and so on.

type ScreenProps = { hotspot: string; playing: boolean; onMusic: (on: boolean) => void; onClose: () => void };

const PASTRY_COLORS = ["#e8b45c", "#e89aa8", "#b5cf8f", "#cf7a56", "#9dbad3", "#f6d58a"];
const SPINES = ["#cf7a56", "#86a86b", "#6488aa", "#e8b45c", "#e89aa8", "#a3523a", "#5f8251", "#3c5878"];

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
  tone?: "cream" | "chalk" | "wood";
  onBack?: () => void;
  onClose: () => void;
  children: ReactNode;
}) {
  const skin = {
    cream: "bg-[#f7efe1] text-[#2a1f18] border-[#2a1f18]",
    chalk: "bg-[#24342c] text-[#f3e6c9] border-[#6b4232]",
    wood: "bg-[#3a2219] text-[#f3e6c9] border-[#8f5b3e]",
  }[tone];
  return (
    <div
      className={`relative flex max-h-[min(640px,86dvh)] w-[min(680px,94vw)] flex-col rounded-md border-4 ${skin} shadow-[0_8px_0_rgba(0,0,0,0.35)]`}
      onClick={(e) => e.stopPropagation()}
    >
      <header className="flex items-start gap-3 border-b-2 border-current/15 px-6 pb-4 pt-5">
        {onBack && (
          <button onClick={onBack} className="mt-1 rounded border-2 border-current px-2 font-['Silkscreen'] text-[11px] opacity-80 hover:opacity-100">
            ← back
          </button>
        )}
        <div className="min-w-0 flex-1">
          <p className="font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-60">{kicker}</p>
          <h2 className="mt-1 font-['Instrument_Serif'] text-4xl leading-tight sm:text-5xl">{title}</h2>
        </div>
        <button
          onClick={onClose}
          aria-label="Close"
          className="h-9 w-9 shrink-0 rounded border-2 border-current font-['Silkscreen'] text-sm opacity-80 hover:opacity-100"
        >
          x
        </button>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">{children}</div>
    </div>
  );
}

function Body({ section }: { section: Section }) {
  return (
    <div className="space-y-3 text-[16px] leading-relaxed opacity-85">
      {section.body.map((p) => (
        <p key={p}>{p}</p>
      ))}
    </div>
  );
}

function Links({ section }: { section: Section }) {
  if (!section.links) return null;
  return (
    <div className="mt-6 flex flex-wrap gap-2">
      {section.links.map((l) => (
        <a
          key={l.label}
          href={l.href}
          target={l.href.startsWith("http") ? "_blank" : undefined}
          rel="noreferrer"
          className="rounded border-2 border-current px-4 py-1.5 font-['Silkscreen'] text-[11px] shadow-[3px_3px_0_currentColor] transition hover:-translate-y-0.5"
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
    const p = SECTIONS[`project:${open}`];
    return (
      <Frame kicker={p.kicker} title={p.title} onBack={() => setOpen(null)} onClose={onClose}>
        <Body section={p} />
        <Links section={p} />
      </Frame>
    );
  }
  return (
    <Frame kicker={section.kicker} title={section.title} onClose={onClose}>
      <p className="mb-5 opacity-75">Each pastry is a project. Pick one to read the story behind it.</p>
      {/* the glass case: two shelves of pastries */}
      <div className="rounded border-4 border-[#c98f3c] bg-[#d6eef1] p-3 shadow-[inset_0_0_0_2px_#fdf8ef]">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {PROJECTS.map((p, i) => (
            <button
              key={p.id}
              onClick={() => setOpen(p.id)}
              className="group flex flex-col items-center rounded bg-[#fdf8ef]/70 p-3 transition hover:-translate-y-1 hover:bg-[#fdf8ef]"
            >
              <span
                className="mb-2 block h-10 w-14 rounded-t-full border-2 border-[#2b1d1a] shadow-[inset_0_-6px_0_rgba(0,0,0,0.15)]"
                style={{ background: PASTRY_COLORS[i % PASTRY_COLORS.length] }}
              />
              <span className="h-1.5 w-16 rounded-full bg-[#2b1d1a]/15" />
              <span className="mt-2 font-['Silkscreen'] text-[11px]">{p.name}</span>
              <span className="text-[11px] opacity-60">{SECTIONS[`project:${p.id}`]?.kicker}</span>
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
      <ul className="mt-6 space-y-3 font-['Silkscreen'] text-[13px]">
        {(section.items ?? []).map((it) => (
          <li key={it.title} className="flex items-baseline gap-3">
            <span>{it.title}</span>
            <span className="flex-1 border-b-2 border-dotted border-[#f3e6c9]/30" />
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
      <div className="mt-6 flex h-40 items-end gap-1 border-b-8 border-[#8f5b3e] px-2">
        {books.map((b, i) => (
          <button
            key={b}
            onClick={() => setPick(i)}
            className={`flex w-10 items-center justify-center rounded-t border-2 border-[#2b1d1a] transition hover:-translate-y-2 ${pick === i ? "-translate-y-3" : ""}`}
            style={{ background: SPINES[i % SPINES.length], height: `${70 + ((i * 37) % 30)}%` }}
            title={b}
          >
            <span className="rotate-[-90deg] whitespace-nowrap font-['Silkscreen'] text-[9px] text-[#fdf8ef]">{b}</span>
          </button>
        ))}
      </div>
      <p className="mt-4 min-h-6 text-sm opacity-80">{pick === null ? "Pull a book off the shelf." : `${books[pick]}: placeholder note on why it stuck with you.`}</p>
    </Frame>
  );
}

function Music({ hotspot, playing, onMusic, onClose }: ScreenProps) {
  const section = SECTIONS[hotspot] ?? SECTIONS.piano;
  return (
    <Frame kicker={section.kicker} title={section.title} tone="wood" onClose={onClose}>
      <Body section={section} />
      <div className="mt-6 flex items-center gap-5">
        <div className={`relative h-28 w-28 shrink-0 rounded-full border-4 border-[#1c1717] bg-[#1c1717] ${playing ? "animate-spin [animation-duration:3s]" : ""}`}>
          <div className="absolute inset-3 rounded-full border border-white/10" />
          <div className="absolute inset-6 rounded-full border border-white/10" />
          <div className="absolute inset-[38%] rounded-full bg-[#cf7a56]" />
        </div>
        <div>
          <button
            onClick={() => onMusic(!playing)}
            className="rounded border-2 border-[#f3e6c9] bg-[#86a86b] px-5 py-2 font-['Silkscreen'] text-xs text-[#1c1717] shadow-[3px_3px_0_#f3e6c9]"
          >
            {playing ? "pause" : "play café loop"}
          </button>
          <ul className="mt-4 space-y-1 text-sm opacity-80">
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
      <div className="mx-auto max-w-sm bg-[#fdf8ef] px-6 py-5 font-mono text-[13px] shadow-[0_0_0_2px_#e2cfa8]">
        <p className="text-center font-['Silkscreen']">DANIEL'S CAFÉ</p>
        <div className="my-3 border-t border-dashed border-[#2a1f18]/40" />
        {section.body.map((b) => (
          <p key={b} className="mb-1">
            {b}
          </p>
        ))}
        <div className="my-3 border-t border-dashed border-[#2a1f18]/40" />
        {(section.links ?? []).map((l) => (
          <a key={l.label} href={l.href} target={l.href.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="flex justify-between hover:underline">
            <span>{l.label}</span>
            <span>→</span>
          </a>
        ))}
        <div className="my-3 border-t border-dashed border-[#2a1f18]/40" />
        <p className="text-center">thanks for stopping by ☕</p>
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
        <ul className="mt-5 divide-y divide-dashed divide-current/20 border-y border-dashed border-current/20">
          {section.items.map((it) => (
            <li key={it.title} className="flex justify-between py-2.5 text-sm">
              <span>{it.title}</span>
              <span className="opacity-50">{it.meta}</span>
            </li>
          ))}
        </ul>
      )}
      <Links section={section} />
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

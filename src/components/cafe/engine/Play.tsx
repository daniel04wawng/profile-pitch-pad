import { useEffect, useRef, useState } from "react";
import { Stage } from "./Stage";
import { type Layout, type SpriteDef } from "./types";
import { SECTIONS } from "../content";
import { LofiPlayer } from "../lofi";

const MUSIC_IDS = new Set(["piano", "chill"]);

// What visitors see: hover lights objects up, clicking opens their panel.
// The editor also runs this in place (P) to try a scene before saving it.
export function Play({ layout, versions, onExit }: { layout: Layout; versions?: Record<string, number>; onExit?: () => void }) {
  const [hovered, setHovered] = useState<SpriteDef | null>(null);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [open, setOpen] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [wide, setWide] = useState(() => window.innerWidth >= 640);
  const player = useRef<LofiPlayer | null>(null);

  useEffect(() => {
    const onResize = () => setWide(window.innerWidth >= 640);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null);
    window.addEventListener("resize", onResize);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("keydown", onKey);
      player.current?.stop();
    };
  }, []);

  const setMusic = (on: boolean) => {
    player.current ??= new LofiPlayer();
    if (on) player.current.start();
    else player.current.stop();
    setPlaying(on);
  };

  const section = open ? SECTIONS[open] : null;
  // Keep the last section's text while the panel slides away.
  const shown = useRef(section);
  if (section) shown.current = section;
  const panel = shown.current;

  return (
    <div className={`relative h-[100dvh] w-full overflow-hidden bg-[#15131c] font-['Space_Grotesk'] ${hovered ? "cursor-pointer" : ""}`}>
      <Stage
        layout={layout}
        versions={versions}
        interactive={(s) => !!s.hotspot}
        hovered={hovered?.id ?? null}
        handlers={{
          onHover: setHovered,
          onPointerMove: (_, e) => setMouse({ x: e.clientX, y: e.clientY }),
          onPointerDown: (s) => {
            if (!s?.hotspot) return setOpen(null);
            setOpen(s.hotspot);
            if (s.hotspot === "chill") setMusic(true);
          },
        }}
      />

      {hovered?.label && (
        <div
          className="pointer-events-none fixed z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded bg-[#1a1512]/90 px-2 py-1 font-['Silkscreen'] text-[11px] text-[#f7efe1]"
          style={{ left: mouse.x, top: mouse.y - 14 }}
        >
          {hovered.label}
        </div>
      )}

      <div className="pointer-events-none absolute left-0 top-0 p-4 text-[#f7efe1] sm:p-6">
        <h1 className="font-['Instrument_Serif'] text-3xl italic leading-none sm:text-4xl">Daniel's café</h1>
        <p className="mt-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-70">coffee · pastries · records</p>
      </div>
      <button
        onClick={() => setMusic(!playing)}
        className="absolute bottom-4 left-4 rounded bg-[#f7efe1]/15 px-3 py-2 font-['Silkscreen'] text-[11px] text-[#f7efe1] backdrop-blur"
      >
        {playing ? "♪ pause" : "♪ music"}
      </button>
      {onExit ? (
        <button onClick={onExit} className="absolute bottom-4 right-4 rounded bg-[#9bbf7a] px-3 py-2 font-['Silkscreen'] text-[11px] text-[#1a1512]">
          ◼ back to editor (P)
        </button>
      ) : (
        import.meta.env.DEV && (
          <a href="/cafe?edit" className="absolute bottom-4 right-4 rounded bg-[#9bbf7a] px-3 py-2 font-['Silkscreen'] text-[11px] text-[#1a1512]">
            edit café
          </a>
        )
      )}

      <aside
        className={`absolute z-20 overflow-y-auto bg-[#f7efe1] text-[#2a1f18] shadow-2xl transition-transform duration-500 ease-out ${
          wide
            ? `right-0 top-0 h-full w-[min(420px,45vw)] rounded-l-xl p-8 ${section ? "translate-x-0" : "translate-x-full"}`
            : `inset-x-0 bottom-0 max-h-[55dvh] rounded-t-xl p-6 ${section ? "translate-y-0" : "translate-y-full"}`
        }`}
        aria-hidden={!section}
      >
        {panel && (
          <>
            <button
              onClick={() => setOpen(null)}
              aria-label="Close"
              className="absolute right-5 top-5 h-8 w-8 rounded border-2 border-[#2a1f18] font-['Silkscreen'] text-sm leading-none"
            >
              x
            </button>
            <p className="font-['Silkscreen'] text-[11px] uppercase tracking-wider text-[#5f7f4c]">{panel.kicker}</p>
            <h2 className="mt-2 font-['Instrument_Serif'] text-4xl leading-tight sm:text-5xl">{panel.title}</h2>
            <div className="mt-5 space-y-3 text-[16px] leading-relaxed text-[#2a1f18]/80">
              {panel.body.map((p) => (
                <p key={p}>{p}</p>
              ))}
            </div>
            {panel.items && (
              <ul className="mt-5 divide-y divide-dashed divide-[#2a1f18]/20 border-y border-dashed border-[#2a1f18]/20">
                {panel.items.map((it) => (
                  <li key={it.title} className="flex justify-between py-2.5 text-sm">
                    <span>{it.title}</span>
                    <span className="text-[#2a1f18]/50">{it.meta}</span>
                  </li>
                ))}
              </ul>
            )}
            {open && MUSIC_IDS.has(open) && (
              <button
                onClick={() => setMusic(!playing)}
                className="mt-6 rounded border-2 border-[#2a1f18] bg-[#9bbf7a] px-5 py-2 font-['Silkscreen'] text-xs shadow-[3px_3px_0_#2a1f18]"
              >
                {playing ? "pause café loop" : "play café loop"}
              </button>
            )}
            {panel.links && (
              <div className="mt-6 flex flex-wrap gap-2">
                {panel.links.map((l) => (
                  <a
                    key={l.label}
                    href={l.href}
                    target={l.href.startsWith("http") ? "_blank" : undefined}
                    rel="noreferrer"
                    className="rounded border-2 border-[#2a1f18] px-4 py-1.5 font-['Silkscreen'] text-[11px] shadow-[3px_3px_0_#2a1f18] transition hover:bg-[#2a1f18] hover:text-[#f7efe1]"
                  >
                    {l.label}
                  </a>
                ))}
              </div>
            )}
            <p className="mt-8 font-['Silkscreen'] text-[10px] uppercase tracking-wider text-[#2a1f18]/35">draft copy</p>
          </>
        )}
      </aside>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { Stage, useCompanions } from "./Stage";
import { useMe } from "./useMe";
import { seatOf } from "./walk";
import { usePresence } from "./usePresence";
import { CafeScreen } from "./Screens";
import { NOTES, WARDROBE, type Layout, type SpriteDef } from "./types";
import { NotesBoard } from "./NotesBoard";
import { Wardrobe } from "./Wardrobe";
import type { Screens } from "./screenData";
import { formatHour, lightAt, pacificHour, phaseName } from "./lighting";
import { LofiPlayer } from "../lofi";

// What visitors see. You're a little avatar in the café: click the floor to walk there, click
// an object and you walk up to it, then the camera moves in, the room softly blurs and that
// object's own screen opens (browse the pastry case, read the menu...). Seats: you sit down.
// The editor also runs this in place (P) to try a scene before saving it.
export function Play({
  layout,
  screens,
  versions,
  onExit,
  hour: forcedHour,
}: {
  layout: Layout;
  screens: Screens;
  versions?: Record<string, number>;
  onExit?: () => void;
  // the editor passes its preview time; visitors get the live time in San Francisco
  hour?: number | null;
}) {
  const [liveHour, setLiveHour] = useState(pacificHour);
  useEffect(() => {
    const t = window.setInterval(() => setLiveHour(pacificHour()), 30_000);
    return () => window.clearInterval(t);
  }, []);
  const hour = forcedHour ?? liveHour;
  const [hovered, setHovered] = useState<SpriteDef | null>(null);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [focus, setFocus] = useState<SpriteDef | null>(null);
  // the screen appears once the camera has arrived
  const [screenOpen, setScreenOpen] = useState(false);
  const [playing, setPlaying] = useState(false);
  const player = useRef<LofiPlayer | null>(null);
  const companions = useCompanions();
  const me = useMe(layout, companions, !focus);
  const room = usePresence(me, { w: layout.width, h: layout.height });
  const timer = useRef<number>();

  const close = () => {
    window.clearTimeout(timer.current);
    setScreenOpen(false);
    setFocus(null);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.clearTimeout(timer.current);
      player.current?.stop();
    };
  }, []);

  const setMusic = (on: boolean) => {
    player.current ??= new LofiPlayer();
    if (on) player.current.start();
    else player.current.stop();
    setPlaying(on);
  };

  const visit = (s: SpriteDef) => {
    setHovered(null);
    setFocus(s);
    setScreenOpen(false);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setScreenOpen(true), 650);
    if (s.hotspot === "chill") setMusic(true);
  };

  return (
    <div className={`relative h-[100dvh] w-full overflow-hidden bg-[#15131c] font-['Space_Grotesk'] ${hovered && !focus ? "cursor-pointer" : ""}`}>
      <Stage
        layout={layout}
        versions={versions}
        // seats are always clickable (to sit); other things when they open a screen
        interactive={(s) => !focus && (!!seatOf(s) || (!!s.hotspot && (!!screens[s.hotspot] || s.hotspot === WARDROBE || s.hotspot === NOTES)))}
        hovered={focus ? null : hovered?.id ?? null}
        camera={focus ? { x: focus.x, y: focus.y, w: focus.w, h: focus.h } : null}
        light={lightAt(hour)}
        handlers={{
          onHover: (s) => !focus && setHovered(s),
          onPointerMove: (_, e) => setMouse({ x: e.clientX, y: e.clientY }),
          onPointerDown: (s, p) => {
            if (focus) return;
            // a seat: walk over and sit down, no screen (the chill corner starts the music)
            if (s && seatOf(s)) me.visit(s, () => s.hotspot === "chill" && setMusic(true));
            else if (s?.hotspot) me.visit(s, () => visit(s));
            else me.walkTo(p);
          },
        }}
        actors={[...room.actors, ...(me.actor ? [me.actor] : [])]}
      />

      {hovered?.label && !focus && (
        <div
          className="pointer-events-none fixed z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded bg-[#1a1512]/90 px-2 py-1 font-['Silkscreen'] text-[11px] text-[#f7efe1]"
          style={{ left: mouse.x, top: mouse.y - 14 }}
        >
          {hovered.label}
        </div>
      )}

      <div className={`pointer-events-none absolute left-0 top-0 p-4 text-[#f7efe1] transition-opacity duration-500 sm:p-6 ${focus ? "opacity-0" : ""}`}>
        <h1 className="font-['Instrument_Serif'] text-3xl italic leading-none sm:text-4xl">Daniel's café</h1>
        <p className="mt-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-70">coffee · pastries · records</p>
      </div>
      <div
        className={`pointer-events-none absolute right-4 top-4 bg-[#f7efe1]/12 px-3 py-1 font-['Silkscreen'] text-[11px] text-[#f7efe1] backdrop-blur transition-opacity duration-500 sm:right-6 sm:top-6 ${focus ? "opacity-0" : ""}`}
      >
        {formatHour(hour)} in SF · {phaseName(hour)}
        {room.online && <span className="opacity-80"> · {room.count + (room.full ? 0 : 1)} here{room.full ? " (café's full: watching)" : ""}</span>}
      </div>

      {/* the room blurs and dims behind the object's screen */}
      <div
        onClick={close}
        className={`absolute inset-0 z-20 flex items-center justify-center p-3 transition-all duration-500 ${
          screenOpen ? "bg-[#15131c]/45 backdrop-blur-[3px]" : "pointer-events-none bg-transparent backdrop-blur-0"
        }`}
      >
        <div className={`transition-all duration-500 ${screenOpen ? "translate-y-0 scale-100 opacity-100" : "translate-y-4 scale-95 opacity-0"}`}>
          {focus?.hotspot === NOTES ? (
            <NotesBoard onClose={close} />
          ) : focus?.hotspot === WARDROBE ? (
            <Wardrobe people={me.people} look={me.look} barista={me.barista} onChange={me.setLook} onClose={close} />
          ) : (
            focus?.hotspot &&
            screens[focus.hotspot] && <CafeScreen screen={screens[focus.hotspot]} playing={playing} onMusic={setMusic} onClose={close} />
          )}
        </div>
      </div>

      <button
        onClick={() => setMusic(!playing)}
        className="absolute bottom-4 left-4 z-30 rounded bg-[#f7efe1]/15 px-3 py-2 font-['Silkscreen'] text-[11px] text-[#f7efe1] backdrop-blur"
      >
        {playing ? "♪ pause" : "♪ music"}
      </button>
      {onExit ? (
        <button onClick={onExit} className="absolute bottom-4 right-4 z-30 rounded bg-[#9bbf7a] px-3 py-2 font-['Silkscreen'] text-[11px] text-[#1a1512]">
          ◼ back to editor (P)
        </button>
      ) : (
        import.meta.env.DEV && (
          <a href="/cafe?edit" className="absolute bottom-4 right-4 z-30 rounded bg-[#9bbf7a] px-3 py-2 font-['Silkscreen'] text-[11px] text-[#1a1512]">
            edit café
          </a>
        )
      )}
    </div>
  );
}

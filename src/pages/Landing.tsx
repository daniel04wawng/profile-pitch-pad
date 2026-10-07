import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { formatHour, lightAt, pacificHour, phaseName } from "@/components/cafe/engine/lighting";
import { BASE, type Layout } from "@/components/cafe/engine/types";
import { fileUrl } from "@/components/cafe/engine/store";
import { Body, facing, loadCatalog, loadRig } from "@/components/cafe/engine/rig";
import type { Actor } from "@/components/cafe/engine/Stage";

// The front door. Daniel's café seen from the street, lit for the time of day in San
// Francisco, while the café itself loads behind it (its code, layout, every piece of art, your
// avatar). When it's ready, "step inside" zooms through the door and you walk in.

const FONTS =
  "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@400;500&family=Silkscreen&family=Pixelify+Sans:wght@400;600&family=VT323&display=swap";
const ART = `${BASE}landing/`;

// the café's page code: loading it here means stepping in is instant
const loadCafePage = () => import("./Cafe");

function preloadImage(src: string) {
  return new Promise<void>((res) => {
    const img = new Image();
    img.onload = img.onerror = () => res();
    img.src = src;
  });
}

// Load everything the café needs, reporting how far along it is (0..1).
async function preloadCafe(progress: (p: number) => void) {
  let done = 0;
  let total = 4;
  const tick = () => progress(Math.min(1, ++done / total));
  const task = <T,>(p: Promise<T>) => p.catch(() => undefined).finally(tick);
  const layout = await task(fetch(BASE + "layout.json").then((r) => r.json() as Promise<Layout>));
  const jobs: Promise<unknown>[] = [
    task(loadCafePage()),
    task(fetch(BASE + "screens.json").then((r) => r.json())),
    // your avatar (the catalog's first; the café reuses what's loaded here)
    task(loadCatalog().then((c) => (c[0] ? loadRig(c[0].id) : null))),
  ];
  if (layout) {
    const files = [...new Set([layout.scene, layout.sceneNight, ...layout.assets.map((a) => a.file)].filter(Boolean) as string[])];
    total += files.length;
    for (const f of files) jobs.push(task(preloadImage(fileUrl(f))));
  }
  await Promise.all(jobs);
  progress(1);
}

// a few stars, scattered the same way every time
function useStars(n: number) {
  return useMemo(() => {
    let s = 7;
    const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    return Array.from({ length: n }, () => ({ x: r() * 100, y: r() * 55, big: r() > 0.85, d: r() * 4 }));
  }, [n]);
}

// your avatar on the street: a little smaller than inside, to suit the doorway out here
const STREET_SCALE = 0.8;
const STREET_SPEED = 46; // art px per second
// the avatar you chose in the changing room (or the catalog's first)
function chosenAvatar(ids: string[]) {
  try {
    const a = JSON.parse(localStorage.getItem("cafe-look") ?? "null")?.avatar;
    if (typeof a === "string" && ids.includes(a)) return a;
  } catch {
    // no storage: the default
  }
  return ids[0];
}

// the next frame; a hidden page gets no animation frames, so a timer keeps the walk going
const next = (f: (t: number) => void) => (document.hidden ? window.setTimeout(() => f(performance.now()), 50) : requestAnimationFrame(f));

const reduceMotion = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function Landing() {
  const navigate = useNavigate();
  // (the dev server takes ?hour=22 to try another time of day)
  const forced = import.meta.env.DEV ? Number(new URLSearchParams(location.search).get("hour") ?? NaN) : NaN;
  const [liveHour, setHour] = useState(pacificHour);
  const hour = Number.isFinite(forced) ? forced : liveHour;
  const light = lightAt(hour);
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [entering, setEntering] = useState(false);
  const [art, setArt] = useState<{ w: number; h: number; door: { x: number; y: number }; walk?: { x: number; y: number }[] } | null>(null);
  // after "step inside": your avatar walking up to the door, then the zoom through it
  const [walker, setWalker] = useState<(Actor & { opacity: number }) | null>(null);
  const [zooming, setZooming] = useState(false);
  const [view, setView] = useState({ w: window.innerWidth, h: window.innerHeight });
  const stars = useStars(70);
  const started = useRef(false);

  useEffect(() => {
    document.title = "Daniel's café";
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = FONTS;
    document.head.appendChild(link);
    const onResize = () => setView({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener("resize", onResize);
    const t = window.setInterval(() => setHour(pacificHour()), 30_000);
    fetch(ART + "storefront.json")
      .then((r) => r.json())
      .then(setArt)
      .catch(() => setArt({ w: 420, h: 352, door: { x: 269, y: 204 } }));
    if (!started.current) {
      started.current = true;
      preloadCafe(setProgress).then(() => setReady(true));
    }
    return () => {
      link.remove();
      window.removeEventListener("resize", onResize);
      window.clearInterval(t);
    };
  }, []);

  const zoomIn = () => {
    setZooming(true);
    window.setTimeout(() => navigate("/cafe"), reduceMotion() ? 0 : 950);
  };
  const enter = async () => {
    if (!ready || entering) return;
    setEntering(true);
    const path = art?.walk;
    if (reduceMotion() || !path || path.length < 2) return zoomIn();
    const cat = await loadCatalog().catch(() => []);
    const id = chosenAvatar(cat.map((c) => c.id));
    const rig = id ? await loadRig(id).catch(() => null) : null;
    if (!rig) return zoomIn();
    const body = new Body(rig, "SW");
    let pos = { ...path[0] };
    let leg = 1;
    let walked = 0;
    const total = path.slice(1).reduce((n, p, i) => n + Math.hypot(p.x - path[i].x, p.y - path[i].y), 0);
    let last = performance.now();
    const step = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      let left = STREET_SPEED * dt;
      let moved = 0;
      while (left > 0 && leg < path.length) {
        const to = path[leg];
        const dx = to.x - pos.x;
        const dy = to.y - pos.y;
        const d = Math.hypot(dx, dy);
        if (d > 0.01) body.face(facing(body.dir, dx, dy));
        if (d <= left) {
          pos = { ...to };
          left -= d;
          moved += d;
          leg++;
        } else {
          pos = { x: pos.x + (dx / d) * left, y: pos.y + (dy / d) * left };
          moved += left;
          left = 0;
        }
      }
      walked += moved;
      // the stride follows the distance (in the avatar's own pixels)
      body.walk(moved / STREET_SCALE);
      // fade in at the street's end, out as you go through the door
      const opacity = Math.min(1, walked / 14, (total - walked) / 6 + 0.15);
      setWalker({ ...body.actor("me", pos.x, pos.y, 0), opacity: Math.max(0, opacity) });
      if (leg < path.length) next(step);
      else {
        setWalker(null);
        zoomIn();
      }
    };
    next(step);
  };
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Enter" && enter();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // the storefront as big as fits (drawn pixelated, like the room inside)
  const W = art?.w ?? 420;
  const H = art?.h ?? 352;
  const k = Math.max(1, Math.min((view.w * 0.94) / W, (view.h * 0.74) / H));
  const night = Math.max(light.lamps, light.stars);
  const door = art?.door ?? { x: 269, y: 204 };
  const pct = Math.round(progress * 100);
  const loadingLine = pct < 35 ? "warming up the espresso machine" : pct < 70 ? "putting out the pastries" : pct < 100 ? "dimming the lights" : "come on in";

  return (
    <div
      className="relative h-[100dvh] w-full overflow-hidden font-['Space_Grotesk'] text-[#f7efe1]"
      style={{ background: `linear-gradient(${light.skyTop}, ${light.skyBottom})` }}
    >
      {/* stars, at night */}
      {light.stars > 0.02 &&
        stars.map((s, i) => (
          <span
            key={i}
            className="absolute animate-pulse bg-[#fff6e0]"
            style={{ left: `${s.x}%`, top: `${s.y}%`, width: s.big ? 3 : 2, height: s.big ? 3 : 2, opacity: light.stars * (s.big ? 0.9 : 0.6), animationDelay: `${s.d}s`, animationDuration: "4s" }}
          />
        ))}

      <header className={`absolute left-0 top-0 z-10 p-5 transition-opacity duration-500 sm:p-8 ${entering ? "opacity-0" : ""}`}>
        <h1 className="font-['Instrument_Serif'] text-4xl italic leading-none sm:text-5xl">Daniel's café</h1>
        <p className="mt-2 font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-75">coffee · pastries · records</p>
        <p className="mt-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-75 sm:hidden">
          {formatHour(hour)} in SF · {phaseName(hour)}
        </p>
      </header>
      <p className={`absolute right-5 top-5 z-10 hidden sm:block bg-[#f7efe1]/12 px-3 py-1 font-['Silkscreen'] text-[11px] backdrop-blur transition-opacity duration-500 sm:right-8 sm:top-8 ${entering ? "opacity-0" : ""}`}>
        {formatHour(hour)} in SF · {phaseName(hour)}
      </p>

      {/* the street corner; stepping in zooms through the door */}
      <div className="absolute inset-0 flex items-center justify-center pt-8">
        <button
          onClick={enter}
          aria-label={ready ? "Step inside the café" : "The café is getting ready"}
          className="relative block [image-rendering:pixelated] focus:outline-none"
          style={{
            width: W * k,
            height: H * k,
            cursor: ready ? "pointer" : "progress",
            transformOrigin: `${door.x * k}px ${door.y * k}px`,
            transform: zooming && !reduceMotion() ? "scale(7)" : "scale(1)",
            transition: "transform 950ms cubic-bezier(.6,0,.9,.5)",
          }}
        >
          <img src={ART + "storefront.png"} alt="Daniel's café on a street corner" className="absolute inset-0 h-full w-full" draggable={false} />
          {/* the day's light over the street (masked to the art), darker at night */}
          <div
            className="absolute inset-0 mix-blend-multiply"
            style={{
              background: light.tint,
              opacity: light.tintAlpha,
              WebkitMaskImage: `url(${ART}storefront.png)`,
              maskImage: `url(${ART}storefront.png)`,
              WebkitMaskSize: "100% 100%",
              maskSize: "100% 100%",
            }}
          />
          {/* the windows and the lamp keep their warmth, and bloom a little after dark */}
          <img src={ART + "storefront.glow.png"} alt="" className="absolute inset-0 h-full w-full" style={{ opacity: Math.min(1, light.tintAlpha * 1.4) }} draggable={false} />
          <img
            src={ART + "storefront.glow.png"}
            alt=""
            className="pointer-events-none absolute inset-0 h-full w-full mix-blend-screen"
            style={{ opacity: night * 0.9, filter: `blur(${3 * k}px)` }}
            draggable={false}
          />
          {walker &&
            (() => {
              const s = STREET_SCALE * k;
              return (
                <div
                  className="pointer-events-none absolute [image-rendering:pixelated]"
                  style={{
                    left: walker.x * k - (walker.flip ? walker.w - walker.footX : walker.footX) * s,
                    top: walker.y * k - walker.footY * s,
                    width: walker.w * s,
                    height: walker.h * s,
                    backgroundImage: `url(${walker.sheet})`,
                    backgroundSize: `${(walker.sheetW ?? walker.w) * s}px ${walker.h * s}px`,
                    backgroundPosition: `${-walker.frame * walker.w * s}px 0`,
                    transform: walker.flip ? "scaleX(-1)" : undefined,
                    opacity: walker.opacity,
                  }}
                />
              );
            })()}
        </button>
      </div>

      {/* loading, then the way in */}
      <div className={`absolute inset-x-0 bottom-0 z-10 flex flex-col items-center gap-3 p-6 pb-8 transition-opacity duration-500 ${entering ? "opacity-0" : ""}`}>
        {ready ? (
          <button
            onClick={enter}
            autoFocus
            className="bg-[#e8b45c] px-6 py-3 font-['Silkscreen'] text-[14px] uppercase tracking-wider text-[#2b1d1a] shadow-[0_4px_0_#8a5a22] transition-transform hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[0_2px_0_#8a5a22]"
          >
            step inside →
          </button>
        ) : (
          <div className="flex w-64 flex-col items-center gap-2">
            <div className="h-4 w-full bg-[#2b1d1a] p-[3px] shadow-[0_0_0_2px_#f7efe1]" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
              <div className="h-full bg-[#e8b45c] transition-[width] duration-200" style={{ width: `${pct}%` }} />
            </div>
          </div>
        )}
        <p className={`font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-70 ${ready ? "hidden sm:block" : ""}`}>{ready ? "or press enter" : `${loadingLine}… ${pct}%`}</p>
      </div>

      {/* the doorway: the screen warms to the café's dark as you step through */}
      <div className="pointer-events-none absolute inset-0 z-20 bg-[#15131c] transition-opacity duration-500" style={{ opacity: zooming ? 1 : 0, transitionDelay: zooming ? "500ms" : "0ms" }} />
    </div>
  );
}

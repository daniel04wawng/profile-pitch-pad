import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BASE } from "@/components/cafe/engine/types";
import { hasOwnCafe, listCafes, publishedId, startCafe } from "@/components/cafe/engine/store";

// The café builder's front page (its own site, VITE_BUILD_ON=1): start a café of your own
// (from the starter café or an empty room), carry on with yours, and walk into other people's.

const FONTS =
  "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@400;500&family=Silkscreen&family=Pixelify+Sans:wght@400;600&family=VT323&display=swap";

const box = (fill: string) => ({ background: fill, boxShadow: "0 -4px 0 #2b1d1a, 0 4px 0 #2b1d1a, -4px 0 0 #2b1d1a, 4px 0 0 #2b1d1a, 0 8px 0 rgba(0,0,0,0.35)" });

export default function Builder() {
  const go = useNavigate();
  const [mine, setMine] = useState(false);
  const [shared, setShared] = useState<string | null>(null);
  const [cafes, setCafes] = useState<{ id: string; name: string; updated_at: string }[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.title = "Build a café";
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = FONTS;
    document.head.appendChild(link);
    hasOwnCafe().then(setMine);
    publishedId().then(setShared);
    listCafes().then(setCafes);
    return () => link.remove();
  }, []);

  const start = async (kind: "starter" | "empty") => {
    if (mine && !window.confirm("Start over? The café you're building in this browser will be replaced.")) return;
    setBusy(true);
    await startCafe(kind);
    go("/cafe?build");
  };

  return (
    <main className="min-h-[100dvh] bg-[#15131c] px-4 py-10 font-['Space_Grotesk'] text-[#f3ecdc] sm:px-8">
      <div className="mx-auto max-w-4xl">
        <p className="font-['Silkscreen'] text-[11px] uppercase tracking-widest text-[#e8b45c]">the café builder</p>
        <h1 className="mt-2 font-['Instrument_Serif'] text-5xl italic leading-tight sm:text-6xl">Build your own little café.</h1>
        <p className="mt-4 max-w-xl text-[17px] opacity-80">
          Move the furniture, paint your own pixel art, write what's on the menu and the screens, then publish it and send the link. Friends who open it walk around in it with you.
        </p>

        <div className="mt-8 grid gap-6 sm:grid-cols-[1.4fr_1fr]">
          <div className="overflow-hidden" style={box("#2a2433")}>
            <img src={`${BASE}landing/storefront.png`} alt="" className="h-56 w-full object-contain p-4 [image-rendering:pixelated]" />
          </div>
          <div className="flex flex-col gap-4">
            {mine && (
              <button disabled={busy} onClick={() => go("/cafe?build")} className="px-4 py-3 text-left font-['Pixelify_Sans'] text-[18px] text-[#1a1512]" style={box("#86a86b")}>
                Carry on with your café →
              </button>
            )}
            <button disabled={busy} onClick={() => start("starter")} className="px-4 py-3 text-left font-['Pixelify_Sans'] text-[18px] text-[#1a1512]" style={box("#e8b45c")}>
              Start from the starter café
              <span className="block font-['Space_Grotesk'] text-[13px] opacity-75">a furnished room to make your own</span>
            </button>
            <button disabled={busy} onClick={() => start("empty")} className="px-4 py-3 text-left font-['Pixelify_Sans'] text-[18px] text-[#1a1512]" style={box("#f7efe1")}>
              Start from an empty room
              <span className="block font-['Space_Grotesk'] text-[13px] opacity-75">just the walls and the floor</span>
            </button>
            {shared && (
              <a href={`/cafe?visit=${shared}`} className="text-[14px] underline opacity-80">
                your published café →
              </a>
            )}
          </div>
        </div>

        <section className="mt-14">
          <h2 className="font-['Silkscreen'] text-[12px] uppercase tracking-widest opacity-70">cafés people have built</h2>
          {cafes.length === 0 ? (
            <p className="mt-3 opacity-60">None yet. Yours could be the first.</p>
          ) : (
            <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {cafes.map((c) => (
                <a key={c.id} href={`/cafe?visit=${c.id}`} className="block p-3 transition-transform hover:-translate-y-1" style={box("#2a2433")}>
                  <p className="font-['Pixelify_Sans'] text-[17px] leading-tight">{c.name}</p>
                  <p className="mt-1 font-['Silkscreen'] text-[9px] uppercase opacity-60">{new Date(c.updated_at).toLocaleDateString()}</p>
                </a>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

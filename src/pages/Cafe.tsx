import { useEffect, useState } from "react";
import { Play } from "@/components/cafe/engine/Play";
import { Editor } from "@/components/cafe/engine/Editor";
import type { Layout } from "@/components/cafe/engine/types";
import { openCafe, openHosted } from "@/components/cafe/engine/store";
import { BUILDER_OR_DEV } from "@/components/cafe/engine/release";
import type { Screens } from "@/components/cafe/engine/screenData";

const FONTS =
  "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@400;500&family=Silkscreen&family=Pixelify+Sans:wght@400;600&family=VT323&display=swap";

// Three ways in:
//  /cafe          Daniel's café, with everyone else in it
//  /cafe?build    build your own café (the editor, saving to this browser)
//  /cafe?mine     visit your own café
//  /cafe?visit=id someone's published café
//  /cafe?edit     the dev server only: edit Daniel's café, saving to disk
const q = new URLSearchParams(window.location.search);
const VISIT = q.get("visit");
// (build, mine and someone's café are the café builder's: not in the portfolio's release)
const MODE =
  import.meta.env.DEV && q.has("edit") ? "edit" : !BUILDER_OR_DEV ? "visit" : q.has("build") ? "build" : q.has("mine") ? "mine" : VISIT ? "hosted" : "visit";

const Cafe = () => {
  const [cafe, setCafe] = useState<{ layout: Layout; screens: Screens; name?: string } | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    document.title = MODE === "edit" ? "Café editor" : MODE === "visit" ? "Daniel's café" : MODE === "hosted" ? "A café" : "Your café";
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = FONTS;
    document.head.appendChild(link);
    if (MODE === "hosted")
      openHosted(VISIT!).then(
        (c) => {
          setCafe(c);
          document.title = c.name;
        },
        () => setMissing(true),
      );
    else openCafe(MODE === "build" || MODE === "mine" ? "browser" : "disk").then(setCafe);
    return () => link.remove();
  }, []);

  if (missing)
    return (
      <div className="flex h-[100dvh] flex-col items-center justify-center gap-4 bg-[#15131c] font-['Silkscreen'] text-[#f3ecdc]">
        <p>this café isn't here (or isn't open yet)</p>
        <a href="/cafe" className="rounded bg-[#9bbf7a] px-3 py-2 text-[11px] text-[#1a1512]">
          go to Daniel's café
        </a>
      </div>
    );
  if (!cafe) return <div className="h-[100dvh] bg-[#15131c]" />;
  if (MODE === "hosted") return <Play title={cafe.name} space={`v-${VISIT}`} layout={cafe.layout} screens={cafe.screens} />;
  if (MODE === "edit" || MODE === "build") return <Editor initial={cafe.layout} initialScreens={cafe.screens} />;
  return MODE === "mine" ? <Play solo title="Your café" layout={cafe.layout} screens={cafe.screens} /> : <Play layout={cafe.layout} screens={cafe.screens} />;
};

export default Cafe;

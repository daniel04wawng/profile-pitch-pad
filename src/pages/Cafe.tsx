import { useEffect, useState } from "react";
import { Play } from "@/components/cafe/engine/Play";
import { Editor } from "@/components/cafe/engine/Editor";
import type { Layout } from "@/components/cafe/engine/types";
import { openCafe } from "@/components/cafe/engine/store";
import type { Screens } from "@/components/cafe/engine/screenData";

const FONTS =
  "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@400;500&family=Silkscreen&family=Pixelify+Sans:wght@400;600&family=VT323&display=swap";

// Three ways in:
//  /cafe          Daniel's café, with everyone else in it
//  /cafe?build    build your own café (the editor, saving to this browser)
//  /cafe?mine     visit your own café
//  /cafe?edit     the dev server only: edit Daniel's café, saving to disk
const q = new URLSearchParams(window.location.search);
const MODE = import.meta.env.DEV && q.has("edit") ? "edit" : q.has("build") ? "build" : q.has("mine") ? "mine" : "visit";

const Cafe = () => {
  const [cafe, setCafe] = useState<{ layout: Layout; screens: Screens } | null>(null);

  useEffect(() => {
    document.title = MODE === "edit" ? "Café editor" : MODE === "visit" ? "Daniel's café" : "Your café";
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = FONTS;
    document.head.appendChild(link);
    openCafe(MODE === "build" || MODE === "mine" ? "browser" : "disk").then(setCafe);
    return () => link.remove();
  }, []);

  if (!cafe) return <div className="h-[100dvh] bg-[#15131c]" />;
  if (MODE === "edit" || MODE === "build") return <Editor initial={cafe.layout} initialScreens={cafe.screens} />;
  return MODE === "mine" ? <Play solo title="Your café" layout={cafe.layout} screens={cafe.screens} /> : <Play layout={cafe.layout} screens={cafe.screens} />;
};

export default Cafe;

import { useEffect, useState } from "react";
import { Play } from "@/components/cafe/engine/Play";
import { Editor } from "@/components/cafe/engine/Editor";
import { BASE, type Layout } from "@/components/cafe/engine/types";

const FONTS =
  "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@400;500&family=Silkscreen&family=Pixelify+Sans:wght@400;600&family=VT323&display=swap";

// The editor only exists on the dev server; production builds drop it entirely.
const EDIT = import.meta.env.DEV && new URLSearchParams(window.location.search).has("edit");

const Cafe = () => {
  const [layout, setLayout] = useState<Layout | null>(null);

  useEffect(() => {
    document.title = EDIT ? "Café editor" : "Daniel's café";
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = FONTS;
    document.head.appendChild(link);
    // no-store so the editor's saves show up on reload
    fetch(BASE + "layout.json", { cache: "no-store" })
      .then((r) => r.json())
      .then(setLayout);
    return () => link.remove();
  }, []);

  if (!layout) return <div className="h-[100dvh] bg-[#15131c]" />;
  return EDIT ? <Editor initial={layout} /> : <Play layout={layout} />;
};

export default Cafe;

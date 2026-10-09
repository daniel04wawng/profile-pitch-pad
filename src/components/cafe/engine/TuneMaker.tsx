import { useEffect, useRef, useState } from "react";
import { PixelButton } from "./Screens";

// Make a tune at the piano: pick a style, add a few words, and a short instrumental is made for
// you (api/music.ts, ACE-Step). It plays here; Daniel's own music stays the café's.

const STYLES = [
  ["lofi", "lo-fi"],
  ["jazz", "café jazz"],
  ["bossa", "bossa nova"],
  ["ambient", "ambient"],
  ["piano", "solo piano"],
] as const;
const WAIT = ["warming up the keys…", "finding the groove…", "pressing the record…"];

type State = { kind: "idle" } | { kind: "making"; id: string; since: number } | { kind: "done"; url: string } | { kind: "error"; message: string };

export function TuneMaker({ onPlay }: { onPlay: () => void }) {
  const [style, setStyle] = useState<string>("lofi");
  const [words, setWords] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });
  const [tick, setTick] = useState(0);
  const audio = useRef<HTMLAudioElement | null>(null);

  // poll while it's being made (a tune takes a little while)
  useEffect(() => {
    if (state.kind !== "making") return;
    let alive = true;
    const poll = async () => {
      if (!alive) return;
      if (Date.now() - state.since > 4 * 60_000) return setState({ kind: "error", message: "That one took too long. Try again?" });
      try {
        const r = await fetch(`/api/music?id=${encodeURIComponent(state.id)}`);
        const out = (await r.json()) as { status?: string; url?: string; error?: string };
        if (!alive) return;
        if (!r.ok) return setState({ kind: "error", message: out.error ?? "Something went wrong." });
        if (out.status === "done" && out.url) return setState({ kind: "done", url: out.url });
      } catch {
        // a dropped poll: try again next time
      }
      setTick((t) => t + 1);
      timer = window.setTimeout(poll, 3000);
    };
    let timer = window.setTimeout(poll, 3000);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [state]);

  const make = async () => {
    setState({ kind: "making", id: "", since: Date.now() });
    try {
      const r = await fetch("/api/music", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ style, words }) });
      const out = (await r.json()) as { id?: string; error?: string };
      if (!r.ok || !out.id) return setState({ kind: "error", message: out.error ?? "Something went wrong." });
      setState({ kind: "making", id: out.id, since: Date.now() });
    } catch {
      setState({ kind: "error", message: "Couldn't reach the piano. Try again?" });
    }
  };

  return (
    <div className="mt-6 border-t-[3px] border-dashed border-current/30 pt-4" style={{ borderColor: "rgba(243,230,201,0.25)" }}>
      <p className="font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">make a tune</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {STYLES.map(([id, name]) => (
          <button
            key={id}
            onClick={() => setStyle(id)}
            className="px-3 py-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider"
            style={{ boxShadow: style === id ? "0 0 0 3px #e8b45c, 0 0 0 5px #2b1d1a" : "0 0 0 2px rgba(243,230,201,0.25)" }}
          >
            {name}
          </button>
        ))}
      </div>
      <input
        value={words}
        onChange={(e) => setWords(e.target.value.slice(0, 80))}
        placeholder="a few words: rainy evening, sleepy, warm…"
        className="mt-3 w-full bg-black/20 px-3 py-2 text-[18px] outline-none placeholder:opacity-50"
        style={{ boxShadow: "inset 0 0 0 2px rgba(243,230,201,0.2)" }}
      />
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <PixelButton onClick={make} disabled={state.kind === "making"} fill="#86a86b">
          {state.kind === "making" ? "making…" : "▶ make it"}
        </PixelButton>
        {state.kind === "making" && <span className="opacity-80">{WAIT[Math.floor(tick / 4) % WAIT.length]}</span>}
        {state.kind === "error" && <span className="opacity-80">{state.message}</span>}
      </div>
      {state.kind === "done" && (
        <audio ref={audio} src={state.url} controls autoPlay onPlay={onPlay} className="mt-3 w-full">
          your browser can't play this tune
        </audio>
      )}
    </div>
  );
}

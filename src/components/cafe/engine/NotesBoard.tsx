import { useEffect, useMemo, useRef, useState } from "react";
import { Frame, PixelButton } from "./Screens";
import type { ScreenDef } from "./screenData";
import { DOODLE, MAX_BODY, MAX_NAME, NOTE_COLOURS, PEN, pinNote, problem, takeDown, useNotes, type Note } from "./notes";

// The community board: everyone's sticky notes on cork, and a little composer to pin your
// own: a colour, a line of text, a doodle, a name if you like.

const BOARD = { name: "Community board", template: "text", tone: "wood", kicker: "the community board", title: "Leave a note", body: [], items: [], links: [] } as unknown as ScreenDef;
const blank = () => "0".repeat(DOODLE * DOODLE);

// a doodle string as an image (transparent where there's no ink)
function doodleUrl(d: string) {
  if (!/[1-7]/.test(d)) return null;
  const c = document.createElement("canvas");
  c.width = c.height = DOODLE;
  const ctx = c.getContext("2d")!;
  for (let i = 0; i < d.length; i++) {
    const k = d.charCodeAt(i) - 48;
    if (k > 0) {
      ctx.fillStyle = PEN[k];
      ctx.fillRect(i % DOODLE, Math.floor(i / DOODLE), 1, 1);
    }
  }
  return c.toDataURL();
}

const ago = (iso: string) => {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  if (m < 60 * 24) return `${Math.round(m / 60)}h ago`;
  return `${Math.round(m / 1440)}d ago`;
};

function Sticky({ note, barista, onRemoved }: { note: Note; barista: boolean; onRemoved: () => void }) {
  const tilt = ((note.id.charCodeAt(0) + note.id.charCodeAt(5)) % 7) - 3; // a slightly crooked pin
  const img = useMemo(() => doodleUrl(note.doodle), [note.doodle]);
  return (
    <div
      className="relative flex min-h-[120px] flex-col p-3 text-[#2b1d1a] shadow-[3px_4px_0_rgba(0,0,0,0.35)]"
      style={{ background: NOTE_COLOURS[note.color] ?? NOTE_COLOURS[0], transform: `rotate(${tilt * 0.8}deg)` }}
    >
      <span className="absolute left-1/2 top-[-5px] h-3 w-3 -translate-x-1/2 rounded-full bg-[#c83c32] shadow-[inset_-2px_-2px_0_rgba(0,0,0,0.25)]" />
      {img && <img src={img} alt="a doodle" className="mx-auto mb-1 h-24 w-24 [image-rendering:pixelated]" />}
      {note.body && <p className="whitespace-pre-wrap break-words text-[19px] leading-tight">{note.body}</p>}
      <p className="mt-auto pt-2 text-[15px] opacity-60">
        {note.name ? `— ${note.name}` : "— someone"} · {ago(note.created_at)}
      </p>
      {barista && (
        <button
          onClick={async () => (await takeDown(note.id)) && onRemoved()}
          title="Take this note down"
          className="absolute right-1 top-1 px-1 font-['Silkscreen'] text-[10px] opacity-50 hover:opacity-100"
        >
          take down
        </button>
      )}
    </div>
  );
}

function DoodlePad({ value, onChange, pen }: { value: string; onChange: (v: string) => void; pen: number }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const down = useRef(false);
  const cur = useRef(value);
  cur.current = value;
  useEffect(() => {
    const ctx = ref.current?.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, DOODLE, DOODLE);
    for (let i = 0; i < value.length; i++) {
      const k = value.charCodeAt(i) - 48;
      if (k > 0) {
        ctx.fillStyle = PEN[k];
        ctx.fillRect(i % DOODLE, Math.floor(i / DOODLE), 1, 1);
      }
    }
  }, [value]);
  const paint = (e: React.PointerEvent) => {
    const r = ref.current!.getBoundingClientRect();
    const x = Math.floor(((e.clientX - r.left) / r.width) * DOODLE);
    const y = Math.floor(((e.clientY - r.top) / r.height) * DOODLE);
    if (x < 0 || y < 0 || x >= DOODLE || y >= DOODLE) return;
    const i = y * DOODLE + x;
    const ch = String(pen);
    if (cur.current[i] === ch) return;
    onChange(cur.current.slice(0, i) + ch + cur.current.slice(i + 1));
  };
  return (
    <canvas
      ref={ref}
      width={DOODLE}
      height={DOODLE}
      className="h-48 w-48 cursor-crosshair touch-none bg-[#fffdf6] [image-rendering:pixelated]"
      style={{ boxShadow: "0 0 0 2px #2b1d1a" }}
      onPointerDown={(e) => {
        down.current = true;
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        paint(e);
      }}
      onPointerMove={(e) => down.current && paint(e)}
      onPointerUp={() => (down.current = false)}
    />
  );
}

export function NotesBoard({ barista, onClose }: { barista: boolean; onClose: () => void }) {
  const { notes, error, remove } = useNotes(true);
  const [writing, setWriting] = useState(false);
  const [body, setBody] = useState("");
  const [name, setName] = useState("");
  const [color, setColor] = useState(0);
  const [doodle, setDoodle] = useState(blank);
  const [pen, setPen] = useState(1);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pin = async () => {
    setBusy(true);
    const err = await pinNote({ body, name, color, doodle });
    setBusy(false);
    if (err) return setStatus(err);
    setBody("");
    setDoodle(blank());
    setWriting(false);
    setStatus("Pinned! Thanks for leaving a note.");
  };

  return (
    <Frame screen={BOARD} onClose={onClose}>
      {writing ? (
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex flex-col items-center gap-2">
            <DoodlePad value={doodle} onChange={setDoodle} pen={pen} />
            <div className="flex flex-wrap justify-center gap-1">
              {PEN.slice(1).map((c, i) => (
                <button key={c} onClick={() => setPen(i + 1)} title="pen colour" className="h-6 w-6" style={{ background: c, boxShadow: pen === i + 1 ? "0 0 0 3px #e8b45c" : "0 0 0 2px #2b1d1a" }} />
              ))}
              <button onClick={() => setPen(0)} className="px-1 font-['Silkscreen'] text-[10px]" style={{ boxShadow: pen === 0 ? "0 0 0 3px #e8b45c" : "0 0 0 2px rgba(243,230,201,0.4)" }}>
                rub out
              </button>
              <button onClick={() => setDoodle(blank())} className="px-1 font-['Silkscreen'] text-[10px] opacity-70">
                clear
              </button>
            </div>
          </div>
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex gap-2">
              {NOTE_COLOURS.map((c, i) => (
                <button key={c} onClick={() => setColor(i)} title="note colour" className="h-7 w-7" style={{ background: c, boxShadow: color === i ? "0 0 0 3px #e8b45c, 0 0 0 5px #2b1d1a" : "0 0 0 2px #2b1d1a" }} />
              ))}
            </div>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value.slice(0, MAX_BODY))}
              rows={4}
              placeholder="say hi, leave a recommendation, a thought…"
              className="w-full p-2 text-[20px] text-[#2b1d1a] outline-none"
              style={{ background: NOTE_COLOURS[color] }}
            />
            <p className="text-right text-[15px] opacity-60">
              {body.length}/{MAX_BODY}
            </p>
            <input
              value={name}
              onChange={(e) => setName(e.target.value.slice(0, MAX_NAME))}
              placeholder="your name (optional)"
              className="mt-1 w-full bg-black/25 px-2 py-1 text-[19px] outline-none"
            />
            {status && <p className="mt-2 text-[18px] text-[#f6d58a]">{status}</p>}
            <div className="mt-3 flex gap-3">
              <PixelButton onClick={() => !busy && pin()} fill="#e8b45c">
                {busy ? "pinning…" : "pin it"}
              </PixelButton>
              <PixelButton onClick={() => (setWriting(false), setStatus(null))} fill="#3a2219" ink="#f3e6c9">
                back
              </PixelButton>
            </div>
            {problem(body, name, doodle) === "Let's keep the board kind." && <p className="mt-2 text-[16px] opacity-70">Let's keep the board kind.</p>}
          </div>
        </div>
      ) : (
        <>
          <div className="mb-4 flex items-center gap-3">
            <PixelButton onClick={() => (setWriting(true), setStatus(null))} fill="#e8b45c">
              + pin a note
            </PixelButton>
            {status && <p className="text-[18px] text-[#f6d58a]">{status}</p>}
          </div>
          <div className="p-3" style={{ background: "#c49460", boxShadow: "inset 0 0 0 4px #6e4024" }}>
            {error && <p className="text-[19px] text-[#2b1d1a]">{error}</p>}
            {!notes && !error && <p className="text-[19px] text-[#2b1d1a]">Loading the board…</p>}
            {notes && !notes.length && <p className="text-[19px] text-[#2b1d1a]">No notes yet. Be the first!</p>}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {notes?.map((n) => <Sticky key={n.id} note={n} barista={barista} onRemoved={() => remove(n.id)} />)}
            </div>
          </div>
        </>
      )}
    </Frame>
  );
}

import { useEffect, useState } from "react";
import { FRAME, HAIRS, PANTS, SHIRTS, SKINS, STYLES, avatarSheet, randomLook, type Look } from "./avatar";
import { Frame, PixelButton } from "./Screens";
import type { ScreenDef } from "./screenData";

// The changing room: pick your hairstyle and colours, see yourself from the front and back,
// or shuffle. Opens when you walk up to the changing-room curtain.

const ROOM = { name: "Changing room", template: "text", tone: "wood", kicker: "the changing room", title: "Change your look", body: [], items: [], links: [] } as unknown as ScreenDef;
const SCALE = 6;

function Swatches({ label, colours, value, onPick }: { label: string; colours: string[]; value: number; onPick: (i: number) => void }) {
  return (
    <div className="mb-3">
      <p className="mb-1 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">{label}</p>
      <div className="flex flex-wrap gap-2">
        {colours.map((c, i) => (
          <button
            key={c + i}
            onClick={() => onPick(i)}
            title={`${label} ${i + 1}`}
            className="h-7 w-7"
            style={{ background: c, boxShadow: i === value ? "0 0 0 3px #f3e6c9, 0 0 0 5px #2b1d1a" : "0 0 0 2px #2b1d1a" }}
          />
        ))}
      </div>
    </div>
  );
}

export function Wardrobe({ look, barista, onChange, onClose }: { look: Look; barista: boolean; onChange: (l: Look) => void; onClose: () => void }) {
  const [sheet, setSheet] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    avatarSheet(look).then((s) => alive && setSheet(s));
    return () => {
      alive = false;
    };
  }, [look, barista]);
  const set = (patch: Partial<Look>) => onChange({ ...look, ...patch });

  const pose = (frame: number) => (
    <div
      className="[image-rendering:pixelated]"
      style={{
        width: FRAME.w * SCALE,
        height: FRAME.h * SCALE,
        backgroundImage: sheet ? `url(${sheet})` : undefined,
        backgroundSize: `${FRAME.w * 8 * SCALE}px ${FRAME.h * SCALE}px`,
        backgroundPosition: `${-frame * FRAME.w * SCALE}px 0`,
      }}
    />
  );

  return (
    <Frame screen={ROOM} onClose={onClose}>
      <div className="flex flex-col gap-6 sm:flex-row">
        <div className="flex shrink-0 items-end justify-center gap-2 sm:flex-col sm:items-center">
          {pose(0)}
          {pose(3)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-3">
            <p className="mb-1 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">hair</p>
            <div className="flex flex-wrap gap-2">
              {STYLES.map((st, i) => (
                <PixelButton key={st} onClick={() => set({ style: i })} fill={i === look.style ? "#e8b45c" : "#3a2219"} ink={i === look.style ? "#2b1d1a" : "#f3e6c9"}>
                  {st}
                </PixelButton>
              ))}
            </div>
          </div>
          <Swatches label="hair colour" colours={HAIRS.map((r) => r[1])} value={look.hair} onPick={(i) => set({ hair: i })} />
          <Swatches label="skin" colours={SKINS.map((r) => r[1])} value={look.skin} onPick={(i) => set({ skin: i })} />
          <Swatches label="top" colours={SHIRTS.map((r) => r[1])} value={look.shirt} onPick={(i) => set({ shirt: i })} />
          <Swatches label="trousers" colours={PANTS.map((r) => r[1])} value={look.pants} onPick={(i) => set({ pants: i })} />
          <div className="mt-4 flex gap-3">
            <PixelButton onClick={() => onChange(randomLook())} fill="#86a86b">
              shuffle
            </PixelButton>
            <PixelButton onClick={onClose} fill="#e8b45c">
              done
            </PixelButton>
          </div>
          {barista && <p className="mt-3 text-[18px] opacity-70">You're the barista, so you always look like you. Visitors can change here.</p>}
        </div>
      </div>
    </Frame>
  );
}

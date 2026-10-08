import { keyOf, MATERIALS, sheetOf, type Colors, type Look, type Material, type People } from "./avatar";
import { Frame, PixelButton } from "./Screens";
import { useCatalog, useRig, type Dress } from "./rig";
import type { ScreenDef } from "./screenData";

// The changing room: pick who you are from the café's avatars (rig.ts catalog), with a front
// and back preview. (The classic people still stand in if an avatar can't load.)

const ROOM = { name: "Changing room", template: "text", tone: "wood", kicker: "the changing room", title: "Who are you today?", body: [], items: [], links: [] } as unknown as ScreenDef;

function Pose({ people, look, pose, scale }: { people: People; look: Look; pose: string; scale: number }) {
  const key = keyOf(look);
  const m = people.characters[key];
  if (!m) return null;
  const i = Math.max(0, m.frames.indexOf(pose));
  const d = people.density ?? 1;
  const [w, h] = [m.frame[0] / d, m.frame[1] / d]; // room pixels; the art inside is finer
  return (
    <div
      className="[image-rendering:pixelated]"
      style={{
        width: w * scale,
        height: h * scale,
        backgroundImage: `url(${sheetOf(key)})`,
        backgroundSize: `${w * m.frames.length * scale}px ${h * scale}px`,
        backgroundPosition: `${-i * w * scale}px 0`,
      }}
    />
  );
}

// a rigged avatar standing (or doing `action`, frame 0), drawn crisp at `scale`
function RigPose({ id, action = "idle-front", scale, dress }: { id: string; action?: string; scale: number; dress?: Dress }) {
  const rig = useRig(id, dress);
  if (rig === "failed") return <div className="flex h-[70px] w-16 items-center justify-center text-[12px] opacity-60">couldn't load</div>;
  if (!rig) return <div style={{ width: 64 * scale, height: 70 * scale }} />;
  const [w, h] = rig.base.manifest.frameSize;
  const n = rig.base.manifest.animations[action as keyof typeof rig.base.manifest.animations]?.durationMs.length ?? 8;
  return (
    <div
      className="[image-rendering:pixelated]"
      style={{ width: w * scale, height: h * scale, backgroundImage: `url(${rig.urls[action]})`, backgroundSize: `${w * n * scale}px ${h * scale}px`, backgroundPosition: "0 0" }}
    />
  );
}

const label = (s: string) => s.replace(/-/g, " ");
// the colours on offer per material (null: as drawn)
const PALETTES: Record<Material, (string | null)[]> = {
  skin: [null, "#f6d2b8", "#eab896", "#d39a72", "#b07650", "#8a5636", "#5e3a24"],
  hair: [null, "#1c1614", "#5a3a24", "#8a4a2a", "#c88a4a", "#e8c27a", "#9a9a9a", "#d86a8a"],
  shirt: [null, "#3c5878", "#a8432c", "#e3d6b8", "#2a2a2e", "#7a2a3a", "#4f7a8a", "#6b7f3a"],
  tee: [null, "#2a2a2e", "#a8c8e0", "#e8b45c", "#c86a5a"],
  trousers: [null, "#3a5a8a", "#b8a07a", "#1e1e22", "#5a6a4a"],
  shoes: [null, "#1e1e22", "#c84a3a", "#3a5a8a"],
};
const MATERIAL_LABEL: Record<Material, string> = { skin: "skin", hair: "hair colour", shirt: "top", tee: "tee", trousers: "trousers", shoes: "shoes" };
const ring = (on: boolean) => ({ boxShadow: on ? "0 0 0 3px #e8b45c, 0 0 0 5px #2b1d1a" : "0 0 0 2px rgba(243,230,201,0.25)" });

const Heading = ({ children }: { children: string }) => <p className="mb-2 mt-4 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">{children}</p>;
const Choice = ({ on, onClick, children }: { on: boolean; onClick: () => void; children: string }) => (
  <button onClick={onClick} className="px-3 py-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider" style={ring(on)}>
    {children}
  </button>
);

// The changing room: who you are (a base model: man or woman, jacket on or off), your
// hairstyle, what you wear, and your colours. All of it is the rig's layers (rig.ts).
export function Wardrobe({ people, look, onChange, onClose }: { people: People | null; look: Look | null; barista: boolean; onChange: (l: Look) => void; onClose: () => void }) {
  const catalog = useCatalog();
  const rigId = !catalog || !look ? null : (catalog.find((a) => a.id === look.avatar) ?? catalog[0])?.id ?? null;
  const rig = useRig(rigId, look ?? undefined);
  if (!people || !look) return null;
  const all = catalog ?? [];
  const me = all.find((a) => a.id === rigId);
  const bodies = [...new Set(all.map((a) => a.body ?? a.id))];
  const variants = all.filter((a) => (a.body ?? a.id) === (me?.body ?? me?.id));
  const manifest = rig && rig !== "failed" ? (rig.base.manifest as { materials?: { base?: Partial<Record<Material, string>> }; layers?: { hair?: string[]; defaultHair?: string; wear?: string[] } }) : null;
  const base = manifest?.materials?.base;
  const hairs = manifest?.layers?.hair ?? [];
  const hair = look.hair && hairs.includes(look.hair) ? look.hair : manifest?.layers?.defaultHair;
  const wearable = manifest?.layers?.wear ?? [];
  const wearing = new Set(look.wear ?? []);
  const set = (l: Partial<Look>) => onChange({ ...look, ...l });
  // a body: its jacket-on model, or whichever it has
  const pickBody = (body: string) => {
    const m = all.filter((a) => (a.body ?? a.id) === body);
    const pick = m.find((a) => a.jacket === me?.jacket) ?? m.find((a) => a.jacket !== "off") ?? m[0];
    if (pick) set({ avatar: pick.id });
  };
  const shuffle = () => {
    const pick = all[Math.floor(Math.random() * all.length)];
    if (pick) set({ avatar: pick.id, hair: hairs[Math.floor(Math.random() * hairs.length)] });
  };

  return (
    <Frame screen={ROOM} onClose={onClose}>
      <div className="flex flex-col gap-6 sm:flex-row">
        <div className="flex shrink-0 items-end justify-center gap-2 pt-4">
          {rigId ? (
            <>
              <RigPose id={rigId} scale={3} dress={look} />
              <RigPose id={rigId} action="idle-back" scale={3} dress={look} />
            </>
          ) : (
            <>
              <Pose people={people} look={look} pose="stand-front" scale={3} />
              <Pose people={people} look={look} pose="stand-back" scale={3} />
            </>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="mb-2 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">who you are</p>
          <div className="flex flex-wrap gap-2">
            {bodies.map((b) => {
              const tile = all.find((a) => (a.body ?? a.id) === b && a.jacket !== "off") ?? all.find((a) => (a.body ?? a.id) === b)!;
              return (
                <button key={b} onClick={() => pickBody(b)} className="flex flex-col items-center gap-1 p-1" style={ring((me?.body ?? me?.id) === b)}>
                  <RigPose id={tile.id} scale={1} />
                  <span className="font-['Silkscreen'] text-[9px] uppercase tracking-wider opacity-80">{b}</span>
                </button>
              );
            })}
          </div>
          {variants.length > 1 && (
            <>
              <Heading>jacket</Heading>
              <div className="flex flex-wrap gap-2">
                {variants.map((a) => (
                  <Choice key={a.id} on={a.id === rigId} onClick={() => set({ avatar: a.id })}>
                    {a.jacket ?? a.label}
                  </Choice>
                ))}
              </div>
            </>
          )}
          {hairs.length > 1 && (
            <>
              <Heading>hair</Heading>
              <div className="flex flex-wrap gap-2">
                {hairs.map((h) => (
                  <Choice key={h} on={h === hair} onClick={() => set({ hair: h })}>
                    {h}
                  </Choice>
                ))}
              </div>
            </>
          )}
          {wearable.length > 0 && (
            <>
              <Heading>wear</Heading>
              <div className="flex flex-wrap gap-2">
                <Choice on={!wearing.size} onClick={() => set({ wear: undefined })}>
                  nothing
                </Choice>
                {wearable.map((w) => (
                  <Choice
                    key={w}
                    on={wearing.has(w)}
                    onClick={() => {
                      const next = new Set(wearing);
                      if (next.has(w)) next.delete(w);
                      else next.add(w);
                      set({ wear: next.size ? [...next].sort() : undefined });
                    }}
                  >
                    {w}
                  </Choice>
                ))}
              </div>
            </>
          )}
          {rigId && (
            <>
              <Heading>colours</Heading>
              <div className="flex flex-col gap-1.5">
                {MATERIALS.filter((m) => !base || base[m]).map((m) => (
                  <div key={m} className="flex items-center gap-1.5">
                    <span className="w-20 shrink-0 font-['Silkscreen'] text-[9px] uppercase tracking-wider opacity-70">{MATERIAL_LABEL[m]}</span>
                    {PALETTES[m].map((c) => {
                      const on = (look.colors?.[m] ?? null) === c;
                      return (
                        <button
                          key={c ?? "drawn"}
                          aria-label={c ? `${MATERIAL_LABEL[m]} ${c}` : `${MATERIAL_LABEL[m]} as drawn`}
                          title={c ? undefined : "as drawn"}
                          onClick={() => {
                            const next: Colors = { ...look.colors };
                            if (c) next[m] = c;
                            else delete next[m];
                            set({ colors: Object.keys(next).length ? next : undefined });
                          }}
                          className="h-5 w-5 shrink-0"
                          style={{ ...ring(on), background: c ?? base?.[m] ?? "#888" }}
                        >
                          {!c && <span className="block h-full w-full" style={{ boxShadow: "inset 0 0 0 2px rgba(43,29,26,0.55)" }} />}
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </>
          )}
          <div className="mt-5 flex gap-3">
            <PixelButton onClick={shuffle} fill="#86a86b">
              shuffle
            </PixelButton>
            <PixelButton onClick={onClose} fill="#e8b45c">
              done
            </PixelButton>
          </div>
        </div>
      </div>
    </Frame>
  );
}

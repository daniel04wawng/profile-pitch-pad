import { keyOf, MATERIALS, sheetOf, type Colors, type Look, type Material, type People } from "./avatar";
import { Frame, PixelButton } from "./Screens";
import { useCatalog, useRig } from "./rig";
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
function RigPose({ id, action = "idle-front", scale, colors }: { id: string; action?: string; scale: number; colors?: Colors }) {
  const rig = useRig(id, colors);
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

export function Wardrobe({ people, look, barista, onChange, onClose }: { people: People | null; look: Look | null; barista: boolean; onChange: (l: Look) => void; onClose: () => void }) {
  const catalog = useCatalog();
  // which rigged avatar you are (null: a classic person); unset means the catalog's first
  const rigId = !catalog || !look ? null : (catalog.find((a) => a.id === look.avatar) ?? catalog[0])?.id ?? null;
  const rig = useRig(rigId); // (its manifest says each material's own colour, for the "as drawn" swatch)
  if (!people || !look) return null;
  // the base models (one tile each, in their own hair), grouped by body; then hairstyles; then colours
  const all = catalog ?? [];
  const me = all.find((a) => a.id === rigId);
  const models = all.filter((a, i) => all.findIndex((b) => b.person === a.person) === i);
  const bodies = [...new Set(models.map((a) => a.body ?? ""))];
  const hairs = me ? all.filter((a) => a.person === me.person && a.hair) : [];
  // a new model keeps your hairstyle when it can
  const pickModel = (person: string) => {
    const same = all.find((a) => a.person === person && a.hair === me?.hair) ?? all.find((a) => a.person === person);
    if (same) onChange({ ...look, avatar: same.id });
  };
  const base = rig && rig !== "failed" ? (rig.base.manifest as { materials?: { base?: Partial<Record<Material, string>> } }).materials?.base : undefined;
  const shuffle = () => {
    const pick = all[Math.floor(Math.random() * all.length)];
    if (pick) onChange({ ...look, avatar: pick.id });
  };

  return (
    <Frame screen={ROOM} onClose={onClose}>
      <div className="flex flex-col gap-6 sm:flex-row">
        <div className="flex shrink-0 items-end justify-center gap-2 pt-4">
          {rigId ? (
            <>
              <RigPose id={rigId} scale={3} colors={look.colors} />
              <RigPose id={rigId} action="idle-back" scale={3} colors={look.colors} />
            </>
          ) : (
            <>
              <Pose people={people} look={look} pose="stand-front" scale={3} />
              <Pose people={people} look={look} pose="stand-back" scale={3} />
            </>
          )}
        </div>
        <div className="min-w-0 flex-1">
          {bodies.map((body) => (
            <div key={body} className="mb-3">
              <p className="mb-2 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">{body || "who you are"}</p>
              <div className="flex flex-wrap gap-2">
                {models
                  .filter((a) => (a.body ?? "") === body)
                  .map((a) => (
                    <button key={a.id} onClick={() => pickModel(a.person ?? a.id)} className="p-1" style={ring(me?.person === a.person)} aria-label={`${a.body ?? "model"} ${models.indexOf(a) + 1}`}>
                      <RigPose id={a.id} scale={1} />
                    </button>
                  ))}
              </div>
            </div>
          ))}
          {hairs.length > 1 && (
            <>
              <p className="mb-2 mt-4 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">hair</p>
              <div className="flex flex-wrap gap-2">
                {hairs.map((a) => (
                  <button key={a.id} onClick={() => onChange({ ...look, avatar: a.id })} className="px-3 py-1 font-['Silkscreen'] text-[10px] uppercase tracking-wider" style={ring(rigId === a.id)}>
                    {a.hair}
                  </button>
                ))}
              </div>
            </>
          )}
          {(catalog?.length ?? 0) < 2 && <p className="mt-2 text-[17px] opacity-60">More people coming soon.</p>}
          {rigId && (
            <>
              <p className="mb-2 mt-4 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">colours</p>
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
                            onChange({ ...look, colors: Object.keys(next).length ? next : undefined });
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

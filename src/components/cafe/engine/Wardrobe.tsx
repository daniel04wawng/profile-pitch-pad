import { BARISTA_PERSON, firstOutfit, keyOf, sheetOf, visitorPeople, type Look, type People } from "./avatar";
import { Frame, PixelButton } from "./Screens";
import { useCatalog, useRig } from "./rig";
import type { ScreenDef } from "./screenData";

// The changing room: choose who you are (a person: their skin and hair) and what you're
// wearing (that person's outfits), with a front and back preview. The barista is always
// Daniel but can change his outfit here.

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
function RigPose({ id, action = "idle-front", scale }: { id: string; action?: string; scale: number }) {
  const rig = useRig(id);
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
const ring = (on: boolean) => ({ boxShadow: on ? "0 0 0 3px #e8b45c, 0 0 0 5px #2b1d1a" : "0 0 0 2px rgba(243,230,201,0.25)" });

export function Wardrobe({ people, look, barista, onChange, onClose }: { people: People | null; look: Look | null; barista: boolean; onChange: (l: Look) => void; onClose: () => void }) {
  const catalog = useCatalog();
  if (!people || !look) return null;
  const persons = barista ? [BARISTA_PERSON] : visitorPeople(people);
  // which rigged avatar you are (null: a classic person); unset means the catalog's first
  const rigId = !catalog || look.avatar === "" ? null : (catalog.find((a) => a.id === look.avatar) ?? catalog[0])?.id ?? null;
  const outfits = people.people[look.person] ?? [];
  const shuffle = () => {
    const person = barista ? BARISTA_PERSON : persons[Math.floor(Math.random() * persons.length)];
    const fits = people.people[person] ?? [];
    onChange({ person, outfit: fits[Math.floor(Math.random() * fits.length)] ?? firstOutfit(people, person), avatar: "" });
  };

  return (
    <Frame screen={ROOM} onClose={onClose}>
      <div className="flex flex-col gap-6 sm:flex-row">
        <div className="flex shrink-0 items-end justify-center gap-2">
          {rigId ? (
            <>
              <RigPose id={rigId} scale={3} />
              <RigPose id={rigId} action="idle-back" scale={3} />
            </>
          ) : (
            <>
              <Pose people={people} look={look} pose="stand-front" scale={3} />
              <Pose people={people} look={look} pose="stand-back" scale={3} />
            </>
          )}
        </div>
        <div className="min-w-0 flex-1">
          {!!catalog?.length && (
            <>
              <p className="mb-2 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">avatar</p>
              <div className="mb-4 flex flex-wrap gap-2">
                {catalog.map((a) => (
                  <button key={a.id} onClick={() => onChange({ ...look, avatar: a.id })} className="flex flex-col items-center gap-1 p-1" style={ring(rigId === a.id)} title={a.label}>
                    <RigPose id={a.id} scale={1} />
                    <span className="font-['Silkscreen'] text-[9px] uppercase tracking-wider opacity-80">{a.label}</span>
                  </button>
                ))}
              </div>
              <p className="mb-2 text-[16px] opacity-60">{barista ? "or your classic barista look:" : "or one of the classic café people:"}</p>
            </>
          )}
          {barista ? (
            <p className="mb-3 text-[20px]">You're the barista, so you're always you. Pick what you're wearing.</p>
          ) : (
            <>
              <p className="mb-2 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">who</p>
              <div className="mb-4 flex flex-wrap gap-2">
                {persons.map((person) => (
                  <button
                    key={person}
                    onClick={() => onChange({ person, outfit: people.people[person]?.includes(look.outfit) ? look.outfit : firstOutfit(people, person), avatar: "" })}
                    className="p-1"
                    style={ring(!rigId && look.person === person)}
                    title={label(person)}
                  >
                    <Pose people={people} look={{ person, outfit: firstOutfit(people, person) }} pose="stand-front" scale={1} />
                  </button>
                ))}
              </div>
            </>
          )}
          <p className="mb-2 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">outfit</p>
          <div className="flex flex-wrap gap-2">
            {outfits.map((outfit) => (
              <button key={outfit} onClick={() => onChange({ person: look.person, outfit, avatar: "" })} className="flex flex-col items-center gap-1 p-1" style={ring(!rigId && look.outfit === outfit)}>
                <Pose people={people} look={{ person: look.person, outfit }} pose="stand-front" scale={1} />
                <span className="font-['Silkscreen'] text-[9px] uppercase tracking-wider opacity-80">{label(outfit)}</span>
              </button>
            ))}
          </div>
          {outfits.length < 2 && <p className="mt-2 text-[17px] opacity-60">More outfits coming soon.</p>}
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

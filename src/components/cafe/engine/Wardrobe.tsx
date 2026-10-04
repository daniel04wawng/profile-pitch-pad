import { BARISTA_PERSON, firstOutfit, keyOf, sheetOf, visitorPeople, type Look, type People } from "./avatar";
import { Frame, PixelButton } from "./Screens";
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

const label = (s: string) => s.replace(/-/g, " ");
const ring = (on: boolean) => ({ boxShadow: on ? "0 0 0 3px #e8b45c, 0 0 0 5px #2b1d1a" : "0 0 0 2px rgba(243,230,201,0.25)" });

export function Wardrobe({ people, look, barista, onChange, onClose }: { people: People | null; look: Look | null; barista: boolean; onChange: (l: Look) => void; onClose: () => void }) {
  if (!people || !look) return null;
  const persons = barista ? [BARISTA_PERSON] : visitorPeople(people);
  const outfits = people.people[look.person] ?? [];
  const shuffle = () => {
    const person = barista ? BARISTA_PERSON : persons[Math.floor(Math.random() * persons.length)];
    const fits = people.people[person] ?? [];
    onChange({ person, outfit: fits[Math.floor(Math.random() * fits.length)] ?? firstOutfit(people, person) });
  };

  return (
    <Frame screen={ROOM} onClose={onClose}>
      <div className="flex flex-col gap-6 sm:flex-row">
        <div className="flex shrink-0 items-end justify-center gap-2">
          <Pose people={people} look={look} pose="stand-front" scale={3} />
          <Pose people={people} look={look} pose="stand-back" scale={3} />
        </div>
        <div className="min-w-0 flex-1">
          {barista ? (
            <p className="mb-3 text-[20px]">You're the barista, so you're always you. Pick what you're wearing.</p>
          ) : (
            <>
              <p className="mb-2 font-['Silkscreen'] text-[11px] uppercase tracking-wider opacity-70">who</p>
              <div className="mb-4 flex flex-wrap gap-2">
                {persons.map((person) => (
                  <button
                    key={person}
                    onClick={() => onChange({ person, outfit: people.people[person]?.includes(look.outfit) ? look.outfit : firstOutfit(people, person) })}
                    className="p-1"
                    style={ring(look.person === person)}
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
              <button key={outfit} onClick={() => onChange({ person: look.person, outfit })} className="flex flex-col items-center gap-1 p-1" style={ring(look.outfit === outfit)}>
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

import { BARISTA_CHARACTER, sheetOf, visitorCharacters, type Look, type People } from "./avatar";
import { Frame, PixelButton } from "./Screens";
import type { ScreenDef } from "./screenData";

// The changing room: pick who you are in the café. Each character is shown standing, from
// the front and from behind.

const ROOM = { name: "Changing room", template: "text", tone: "wood", kicker: "the changing room", title: "Who are you today?", body: [], items: [], links: [] } as unknown as ScreenDef;
const SCALE = 2;

function Pose({ people, character, pose }: { people: People; character: string; pose: string }) {
  const m = people.characters[character];
  if (!m) return null;
  const i = Math.max(0, m.frames.indexOf(pose));
  const [w, h] = m.frame;
  return (
    <div
      className="[image-rendering:pixelated]"
      style={{
        width: w * SCALE,
        height: h * SCALE,
        backgroundImage: `url(${sheetOf(character)})`,
        backgroundSize: `${w * m.frames.length * SCALE}px ${h * SCALE}px`,
        backgroundPosition: `${-i * w * SCALE}px 0`,
      }}
    />
  );
}

export function Wardrobe({ people, look, barista, onChange, onClose }: { people: People | null; look: Look | null; barista: boolean; onChange: (l: Look) => void; onClose: () => void }) {
  if (!people) return null;
  const all = visitorCharacters(people);
  const shuffle = () => {
    const others = all.filter((c) => c !== look?.character);
    onChange({ character: others[Math.floor(Math.random() * others.length)] });
  };
  return (
    <Frame screen={ROOM} onClose={onClose}>
      {barista ? (
        <div className="flex items-end gap-4">
          <Pose people={people} character={BARISTA_CHARACTER} pose="stand-front" />
          <p className="text-[20px]">You're the barista, so you always look like you. Visitors pick who they are here.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
            {all.map((c) => {
              const on = look?.character === c;
              return (
                <button
                  key={c}
                  onClick={() => onChange({ character: c })}
                  className="flex flex-col items-center gap-1 p-2"
                  style={{ boxShadow: on ? "0 0 0 3px #e8b45c, 0 0 0 5px #2b1d1a" : "0 0 0 2px rgba(243,230,201,0.25)" }}
                  title={c}
                >
                  <div className="flex items-end gap-1">
                    <Pose people={people} character={c} pose="stand-front" />
                    <Pose people={people} character={c} pose="stand-back" />
                  </div>
                  <span className="font-['Silkscreen'] text-[10px] uppercase tracking-wider opacity-80">{c}</span>
                </button>
              );
            })}
          </div>
          <div className="mt-4 flex gap-3">
            <PixelButton onClick={shuffle} fill="#86a86b">
              shuffle
            </PixelButton>
            <PixelButton onClick={onClose} fill="#e8b45c">
              done
            </PixelButton>
          </div>
        </>
      )}
    </Frame>
  );
}

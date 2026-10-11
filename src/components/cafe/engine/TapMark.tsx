// Where you tapped to walk: a pixel arrow drops onto the spot and bobs there, and a ring
// ripples out across the floor under it. Drawn in scene pixels (it's a Stage child), so it's as
// chunky as the room. `id` restarts the animation for a new tap.

const ARROW = [
  "..XXX..",
  "..XXX..",
  "XXXXXXX",
  ".XXXXX.",
  "..XXX..",
  "...X...",
];
const FILL = "#f6d58a";
const INK = "#3d2418";

// the arrow's pixels, then its 1px outline (every empty pixel touching one)
const pixels: [number, number][] = [];
ARROW.forEach((row, y) => [...row].forEach((c, x) => c === "X" && pixels.push([x, y])));
const filled = new Set(pixels.map(([x, y]) => `${x},${y}`));
const outline: [number, number][] = [];
for (let y = -1; y <= ARROW.length; y++)
  for (let x = -1; x <= ARROW[0].length; x++)
    if (!filled.has(`${x},${y}`) && [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => filled.has(`${x + dx},${y + dy}`))) outline.push([x, y]);

const CSS = `
@keyframes tapmark-ring { from { transform: scale(0.3); opacity: 1 } to { transform: scale(1.5); opacity: 0 } }
@keyframes tapmark-drop { 0% { transform: translateY(-10px); opacity: 0 } 40% { transform: translateY(0); opacity: 1 } 100% { transform: translateY(0); opacity: 1 } }
@keyframes tapmark-bob { 0%, 100% { transform: translateY(0) } 50% { transform: translateY(-2px) } }
@keyframes tapmark-out { 0%, 80% { opacity: 1 } 100% { opacity: 0 } }
`;

// each of the arrow's pixels is P scene pixels (the room's own are 1: a 1px arrow is lost on a laptop)
const P = 2;

export function TapMark({ x, y, id }: { x: number; y: number; id: number }) {
  const w = ARROW[0].length;
  const h = ARROW.length;
  return (
    <div key={id} className="pointer-events-none absolute" style={{ left: x, top: y, zIndex: 100000, animation: "tapmark-out 1.6s steps(8) forwards" }}>
      <style>{CSS}</style>
      {/* the ring on the floor, flattened like the room's tiles */}
      <svg className="absolute overflow-visible" style={{ left: -14, top: -7, width: 28, height: 14 }} shapeRendering="crispEdges">
        <g style={{ transformOrigin: "14px 7px", animation: "tapmark-ring 0.9s steps(6) infinite" }}>
          <ellipse cx={14} cy={7} rx={13} ry={6.5} fill="none" stroke={INK} strokeWidth={3} opacity={0.5} />
          <ellipse cx={14} cy={7} rx={13} ry={6.5} fill="none" stroke={FILL} strokeWidth={1.5} />
        </g>
      </svg>
      {/* the arrow above it */}
      <div className="absolute" style={{ left: -Math.floor((w * P) / 2), top: -(h + 4) * P, animation: "tapmark-drop 0.35s steps(4) forwards" }}>
        <svg className="overflow-visible" width={w * P} height={h * P} viewBox={`0 0 ${w} ${h}`} shapeRendering="crispEdges" style={{ animation: "tapmark-bob 0.8s steps(2) 0.35s infinite" }}>
          {outline.map(([px, py]) => (
            <rect key={`o${px},${py}`} x={px} y={py} width={1} height={1} fill={INK} />
          ))}
          {pixels.map(([px, py]) => (
            <rect key={`f${px},${py}`} x={px} y={py} width={1} height={1} fill={FILL} />
          ))}
        </svg>
      </div>
    </div>
  );
}

// A short buzz for a tap, where the phone allows it (Android; iPhones don't let pages vibrate).
export function buzz(ms = 10) {
  try {
    navigator.vibrate?.(ms);
  } catch {
    // (some browsers throw without a user gesture)
  }
}

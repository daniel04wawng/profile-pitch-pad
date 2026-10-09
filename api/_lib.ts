// Shared bits for the café's server functions (Vercel Functions, Web-standard handlers; the dev
// server runs the same files, vite.config.ts). Files starting with "_" aren't routes.

export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });

export const clientIp = (req: Request) => req.headers.get("x-forwarded-for")?.split(",")[0].trim() || req.headers.get("x-real-ip") || "local";

// A small per-visitor limit, kept in this instance's memory: a serverless instance is reused for
// a while, so it stops someone hammering a button, not a determined abuser (the provider's own
// spending cap, set in its dashboard, is the real backstop).
const hits = new Map<string, number[]>();
export function limited(key: string, max: number, windowMs: number): boolean {
  const now = Date.now();
  const recent = (hits.get(key) ?? []).filter((t) => now - t < windowMs);
  if (recent.length >= max) {
    hits.set(key, recent);
    return true;
  }
  recent.push(now);
  hits.set(key, recent);
  return false;
}

// Free text from a visitor, cut down to plain words: letters, digits, spaces and a little
// punctuation, at most `max` characters.
export const words = (v: unknown, max: number) =>
  typeof v === "string"
    ? v
        .toLowerCase()
        .replace(/[^a-z0-9 ,'-]+/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, max)
    : "";

import { createClient } from "@supabase/supabase-js";

// The café's Supabase project (multiplayer room, community board, barista check). Only the
// public URL and publishable key live in the site; what visitors may do is enforced by the
// database (supabase/cafe.sql).
const URL = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string | undefined;

export const supabase = URL && KEY ? createClient(URL, KEY, { realtime: { params: { eventsPerSecond: 8 } } }) : null;

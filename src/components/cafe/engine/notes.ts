import { useEffect, useState } from "react";
import { RegExpMatcher, englishDataset, englishRecommendedTransformers } from "obscenity";
import { supabase } from "./supabase";
import { baristaCode } from "./avatar";

// The community board: notes anyone can pin (text and/or a tiny doodle), stored in the café's
// Supabase project. The database enforces the rules (lengths, no links, a flood guard, only
// the barista can take notes down); the site also filters words before posting.

export const NOTE_COLOURS = ["#f8e278", "#f6b0ba", "#b0e2be", "#b0cef0", "#fafaf4", "#f4c8a0"];
export const PEN = ["", "#2b1d1a", "#c8443c", "#e8a23a", "#4f8a4a", "#3c64a8", "#8a4aa8", "#f4f0e6"]; // 1-7
export const DOODLE = 32; // the doodle is DOODLE x DOODLE pixels
export const MAX_BODY = 140;
export const MAX_NAME = 24;

export type Note = { id: string; created_at: string; body: string; name: string; color: number; doodle: string };

const matcher = new RegExpMatcher({ ...englishDataset.build(), ...englishRecommendedTransformers });
const LINK = /(https?:\/\/|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\b)/i;

// Why a note can't be pinned (or null if it's fine).
export function problem(body: string, name: string, doodle: string): string | null {
  if (!body.trim() && !/[1-7]/.test(doodle)) return "Write something or draw something first.";
  if (body.length > MAX_BODY || name.length > MAX_NAME) return "That's a bit long for a sticky note.";
  if (LINK.test(body) || LINK.test(name)) return "No links on the board, sorry.";
  if (matcher.hasMatch(body) || matcher.hasMatch(name)) return "Let's keep the board kind.";
  return null;
}

export async function pinNote(n: { body: string; name: string; color: number; doodle: string }): Promise<string | null> {
  if (!supabase) return "The board is offline right now.";
  const why = problem(n.body, n.name, n.doodle);
  if (why) return why;
  const { error } = await supabase.from("notes").insert({ body: n.body.trim(), name: n.name.trim(), color: n.color, doodle: /[1-7]/.test(n.doodle) ? n.doodle : "" });
  return error ? (error.message.includes("busy") ? "The board is busy, try again in a minute." : "Couldn't pin that, try again.") : null;
}

export async function takeDown(id: string): Promise<boolean> {
  const code = baristaCode();
  if (!supabase || !code) return false;
  const { error } = await supabase.rpc("hide_note", { note: id, code });
  return !error;
}

export async function checkBarista(code: string): Promise<boolean> {
  if (!supabase) return false;
  const { data, error } = await supabase.rpc("is_barista", { code });
  return !error && data === true;
}

// The latest notes, kept up to date as people pin them (or the barista takes them down).
export function useNotes(open: boolean) {
  const [notes, setNotes] = useState<Note[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!open || !supabase) return;
    let alive = true;
    const load = async () => {
      const { data, error } = await supabase!.from("notes").select("id, created_at, body, name, color, doodle").order("created_at", { ascending: false }).limit(60);
      if (!alive) return;
      if (error) setError("Couldn't load the board.");
      else setNotes(data as Note[]);
    };
    load();
    const ch = supabase
      .channel("notes-board")
      .on("postgres_changes", { event: "*", schema: "public", table: "notes" }, () => load())
      .subscribe();
    return () => {
      alive = false;
      supabase!.removeChannel(ch);
    };
  }, [open]);
  return { notes, error, remove: (id: string) => setNotes((n) => n?.filter((x) => x.id !== id) ?? null) };
}

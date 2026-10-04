-- Daniel's café: everything the site needs in its Supabase project. Run once in the SQL
-- Editor (it's safe to run again). Nothing secret is in here: the barista's code is only
-- stored as a SHA-256 hash.

-- ---------------------------------------------------------------- keep the project awake
-- The GitHub Actions job reads this row twice a week (free projects pause after a week idle).
create table if not exists public.keepalive (id int primary key default 1);
insert into public.keepalive default values on conflict do nothing;
alter table public.keepalive enable row level security;
drop policy if exists "anyone can read keepalive" on public.keepalive;
create policy "anyone can read keepalive" on public.keepalive for select using (true);
grant select on public.keepalive to anon;

-- ---------------------------------------------------------------- the barista
create extension if not exists pgcrypto with schema extensions;
create table if not exists public.barista (code_hash text primary key);
alter table public.barista enable row level security; -- no policies: visitors can't see it
insert into public.barista values ('a589e7c37adfcdfae68555c73a6d851559480d1ebc041524f67f1ead4b464548') on conflict do nothing;

create or replace function public.is_barista(code text) returns boolean
language sql security definer set search_path = public, extensions as $$
  select exists (select 1 from public.barista where code_hash = encode(extensions.digest(code, 'sha256'), 'hex'));
$$;
revoke all on function public.is_barista(text) from public;
grant execute on function public.is_barista(text) to anon;

-- ---------------------------------------------------------------- the community board
create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  body text not null default '' check (char_length(body) <= 140),
  name text not null default '' check (char_length(name) <= 24),
  color smallint not null default 0 check (color between 0 and 5),
  -- a 32x32 doodle, one character per pixel: 0 = paper, 1-7 = pen colours
  doodle text not null default '' check (char_length(doodle) in (0, 1024) and doodle ~ '^[0-7]*$'),
  hidden boolean not null default false,
  check (char_length(trim(body)) > 0 or doodle ~ '[1-7]'), -- something on it
  check (body !~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\b)'), -- no links
  check (name !~* '(https?://|www\.)')
);
alter table public.notes enable row level security;
drop policy if exists "read the board" on public.notes;
create policy "read the board" on public.notes for select to anon using (not hidden);
drop policy if exists "pin a note" on public.notes;
create policy "pin a note" on public.notes for insert to anon with check (not hidden);
grant select, insert on public.notes to anon;

-- flood guard: at most 30 new notes a minute across the whole café
create or replace function public.notes_flood_guard() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from public.notes where created_at > now() - interval '1 minute') >= 30 then
    raise exception 'the board is busy, try again in a minute';
  end if;
  return new;
end $$;
drop trigger if exists notes_flood_guard on public.notes;
create trigger notes_flood_guard before insert on public.notes for each row execute function public.notes_flood_guard();

-- the barista takes a note down
create or replace function public.hide_note(note uuid, code text) returns void
language plpgsql security definer set search_path = public, extensions as $$
begin
  if not public.is_barista(code) then
    raise exception 'only the barista can take notes down';
  end if;
  update public.notes set hidden = true where id = note;
end $$;
revoke all on function public.hide_note(uuid, text) from public;
grant execute on function public.hide_note(uuid, text) to anon;

-- new notes appear live on the board
do $$ begin
  alter publication supabase_realtime add table public.notes;
exception when duplicate_object then null; end $$;

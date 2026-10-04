-- Daniel's café: everything the site needs in its Supabase project. Run once in the SQL
-- Editor (it's safe to run again). Nothing secret is in here. To take a note down, delete
-- its row (or tick `hidden`) in the Table Editor.

-- ---------------------------------------------------------------- keep the project awake
-- The GitHub Actions job reads this row twice a week (free projects pause after a week idle).
create table if not exists public.keepalive (id int primary key default 1);
insert into public.keepalive default values on conflict do nothing;
alter table public.keepalive enable row level security;
drop policy if exists "anyone can read keepalive" on public.keepalive;
create policy "anyone can read keepalive" on public.keepalive for select using (true);
grant select on public.keepalive to anon;

-- ---------------------------------------------------------------- the community board
create extension if not exists pgcrypto with schema extensions;
create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  body text not null default '' check (char_length(body) <= 140),
  name text not null default '' check (char_length(name) <= 24),
  color smallint not null default 0 check (color between 0 and 5),
  -- a 32x32 doodle, one character per pixel: 0 = paper, 1-7 = pen colours
  doodle text not null default '' check (char_length(doodle) in (0, 1024) and doodle ~ '^[0-7]*$'),
  -- where it's pinned on the board, 0-1000 across and down
  x smallint not null default 500 check (x between 0 and 1000),
  y smallint not null default 500 check (y between 0 and 1000),
  hidden boolean not null default false,
  check (char_length(trim(body)) > 0 or doodle ~ '[1-7]'), -- something on it
  constraint notes_no_links check (body !~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\y)'), -- \y: a word boundary in Postgres
  constraint notes_name_no_links check (name !~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\y)')
);
-- older versions of this file wrote the link checks with \b (a backspace in Postgres, so
-- domains slipped through): swap them for the ones above
do $$ declare c record; begin
  for c in select conname from pg_constraint where conrelid = 'public.notes'::regclass and contype = 'c'
      and pg_get_constraintdef(oid) like '%https?%' and conname not in ('notes_no_links', 'notes_name_no_links') loop
    execute format('alter table public.notes drop constraint %I', c.conname);
  end loop;
end $$;
delete from public.notes where body ~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\y)'
  or name ~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\y)';
alter table public.notes drop constraint if exists notes_no_links;
alter table public.notes add constraint notes_no_links check (body !~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\y)');
alter table public.notes drop constraint if exists notes_name_no_links;
alter table public.notes add constraint notes_name_no_links check (name !~* '(https?://|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|gg|ly|co)\y)');
alter table public.notes add column if not exists x smallint not null default 500 check (x between 0 and 1000);
alter table public.notes add column if not exists y smallint not null default 500 check (y between 0 and 1000);
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

-- new notes appear live on the board
do $$ begin
  alter publication supabase_realtime add table public.notes;
exception when duplicate_object then null; end $$;

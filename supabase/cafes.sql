-- Visitors' cafés: one per person, published from /cafe?build, visited at /cafe?visit=<id>.
--
-- Run once in the Supabase SQL editor (project lepsbyqwrplrcmvsofjy). Also turn on
-- Authentication > Sign In / Providers > "Allow anonymous sign-ins": a visitor publishing their
-- café gets an anonymous account in their browser, which owns the café.
--
-- What's stored: the café's layout, screens and collisions (one JSON doc, capped), and its own
-- PNGs and photos in the public "cafes" storage bucket under <café id>/. Anyone can look; only
-- the owner can change or delete. Links are never shown in visitors' cafés (the site strips
-- them when it opens one), so a café can't be used to spread links.

create table if not exists public.cafes (
  id text primary key default encode(gen_random_bytes(5), 'hex'),
  owner uuid not null unique default auth.uid() references auth.users (id) on delete cascade,
  name text not null default 'My café' check (char_length(name) between 1 and 40),
  doc jsonb not null check (octet_length(doc::text) < 600000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.cafes enable row level security;

drop policy if exists "cafes are public" on public.cafes;
create policy "cafes are public" on public.cafes for select using (true);
drop policy if exists "make your own cafe" on public.cafes;
create policy "make your own cafe" on public.cafes for insert to authenticated with check (owner = auth.uid());
drop policy if exists "change your own cafe" on public.cafes;
create policy "change your own cafe" on public.cafes for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists "remove your own cafe" on public.cafes;
create policy "remove your own cafe" on public.cafes for delete to authenticated using (owner = auth.uid());

create or replace function public.cafes_touch() returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  new.id := old.id; -- a café keeps its address
  new.owner := old.owner;
  return new;
end $$;
drop trigger if exists cafes_touch on public.cafes;
create trigger cafes_touch before update on public.cafes for each row execute function public.cafes_touch();

-- the files: public to read, 400 KB each, pictures only
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('cafes', 'cafes', true, 409600, array['image/png', 'image/jpeg', 'image/webp', 'image/gif'])
on conflict (id) do update set public = excluded.public, file_size_limit = excluded.file_size_limit, allowed_mime_types = excluded.allowed_mime_types;

-- only into your own café's folder
drop policy if exists "cafe files: add to your own" on storage.objects;
create policy "cafe files: add to your own" on storage.objects for insert to authenticated
  with check (bucket_id = 'cafes' and (storage.foldername(name))[1] in (select id from public.cafes where owner = auth.uid()));
drop policy if exists "cafe files: change your own" on storage.objects;
create policy "cafe files: change your own" on storage.objects for update to authenticated
  using (bucket_id = 'cafes' and (storage.foldername(name))[1] in (select id from public.cafes where owner = auth.uid()));
drop policy if exists "cafe files: remove your own" on storage.objects;
create policy "cafe files: remove your own" on storage.objects for delete to authenticated
  using (bucket_id = 'cafes' and (storage.foldername(name))[1] in (select id from public.cafes where owner = auth.uid()));
-- (re-publishing overwrites files, which also needs to read them)
drop policy if exists "cafe files: read" on storage.objects;
create policy "cafe files: read" on storage.objects for select using (bucket_id = 'cafes');

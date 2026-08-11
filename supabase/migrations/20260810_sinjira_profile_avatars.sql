-- SINJIRA V14 — photos de profil
alter table public.profiles add column if not exists avatar_path text;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('sinjira-avatars','sinjira-avatars',true,5242880,array['image/webp','image/jpeg','image/png'])
on conflict(id) do update set public=true,file_size_limit=5242880,allowed_mime_types=array['image/webp','image/jpeg','image/png'];

drop policy if exists "sinjira avatars upload own" on storage.objects;
create policy "sinjira avatars upload own" on storage.objects for insert to authenticated
with check(bucket_id='sinjira-avatars' and (storage.foldername(name))[1]=auth.uid()::text);

drop policy if exists "sinjira avatars update own" on storage.objects;
create policy "sinjira avatars update own" on storage.objects for update to authenticated
using(bucket_id='sinjira-avatars' and (storage.foldername(name))[1]=auth.uid()::text)
with check(bucket_id='sinjira-avatars' and (storage.foldername(name))[1]=auth.uid()::text);

drop policy if exists "sinjira avatars delete own" on storage.objects;
create policy "sinjira avatars delete own" on storage.objects for delete to authenticated
using(bucket_id='sinjira-avatars' and (storage.foldername(name))[1]=auth.uid()::text);

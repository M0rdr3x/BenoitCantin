-- PRO V15 — déjà appliqué au projet Supabase gpvivleexywljowcqkru.
-- Supabase Storage upsert nécessite SELECT + INSERT + UPDATE.
drop policy if exists "sinjira avatars select own" on storage.objects;
create policy "sinjira avatars select own" on storage.objects
for select to authenticated
using (
  bucket_id = 'sinjira-avatars'
  and (storage.foldername(name))[1] = auth.uid()::text
);

insert into public.internal_admin_users(user_id)
select id from auth.users where lower(email)=lower('kingtyrano@gmail.com')
on conflict (user_id) do nothing;

revoke all on function public.is_sinjira_admin(uuid) from public, anon;
grant execute on function public.is_sinjira_admin(uuid) to authenticated, service_role;

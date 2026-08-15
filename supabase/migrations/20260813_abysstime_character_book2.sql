-- SINJIRA V23 — compte propriétaire + personnage AbyssTime
-- À appliquer dans Supabase après le déploiement des fichiers du site.

do $$
declare
  v_user uuid;
begin
  select id into v_user from auth.users where lower(email)=lower('kingtyrano@gmail.com') limit 1;
  if v_user is null then
    raise exception 'Compte kingtyrano@gmail.com introuvable dans auth.users';
  end if;

  insert into public.internal_admin_users(user_id)
  values(v_user)
  on conflict(user_id) do nothing;

  insert into public.profiles(user_id,pseudo,display_name)
  values(v_user,'AbyssTime','Benoit Cantin')
  on conflict(user_id) do update set
    pseudo='AbyssTime',
    display_name='Benoit Cantin',
    updated_at=now();

  if exists(select 1 from public.characters where user_id=v_user) then
    update public.characters
    set public_name='AbyssTime',
        public_description='Personnage officiel associé au compte de Benoit Cantin.',
        portrait_path='/assets/media/characters/abysstime.webp',
        status='assigned',
        novel_id=null,
        novel_note='SINJIRA — Livre II (titre à confirmer)',
        visible_to_user=true,
        canon_status='PROVISOIRE',
        updated_at=now()
    where user_id=v_user;
  else
    insert into public.characters(
      user_id,public_name,public_description,portrait_path,status,novel_note,
      bible,ai_generated,visible_to_user,canon_status,canon_version
    ) values(
      v_user,'AbyssTime','Personnage officiel associé au compte de Benoit Cantin.',
      '/assets/media/characters/abysstime.webp','assigned','SINJIRA — Livre II (titre à confirmer)',
      jsonb_build_object(
        'owner','Benoit Cantin',
        'account','AbyssTime',
        'placement','SINJIRA — Livre II (titre à confirmer)',
        'source','Ajout manuel V23',
        'notes','Compléter la Bible narrative depuis l’administration SINJIRA.'
      ),false,true,'PROVISOIRE','v1.0'
    );
  end if;
end $$;

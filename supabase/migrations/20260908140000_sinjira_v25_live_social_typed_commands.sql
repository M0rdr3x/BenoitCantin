-- SINJIRA V25 — commandes typées « En direct ».
-- L'HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.
-- Les commandes visibles /join, /rooms et /me seront parsées côté client puis
-- mappées vers ces RPC nommées. Aucun interpréteur de commande ni SQL dynamique.

create or replace function public.social_live_join_public_room(p_slug text)
returns jsonb
language plpgsql
security invoker
set search_path=pg_catalog,public,auth
as $$
declare
  v_user uuid:=auth.uid();
  v_slug text:=lower(btrim(coalesce(p_slug,'')));
  v_room_id uuid;
  v_name text;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if v_slug !~ '^[a-z0-9][a-z0-9-]{2,47}$' then
    raise exception 'SOCIAL_LIVE_ROOM_UNAVAILABLE';
  end if;

  -- SECURITY INVOKER + RLS : un salon masqué par cohorte, blocage, suspension
  -- ou règles communautaires reste indistinguable d'un salon inexistant.
  select r.id,r.name into v_room_id,v_name
  from public.social_live_rooms r
  where r.slug=v_slug
    and r.visibility='public'
    and not r.is_archived
  limit 1;

  if v_room_id is null then
    raise exception 'SOCIAL_LIVE_ROOM_UNAVAILABLE';
  end if;

  -- Le client ne fournit que room_id. user_id et role restent dérivés côté DB;
  -- la policy + le trigger anti-raid de la fondation restent la source d'autorité.
  insert into public.social_live_room_members(room_id)
  values(v_room_id)
  on conflict do nothing;

  return jsonb_build_object(
    'ok',true,
    'joined',true,
    'room',jsonb_build_object(
      'room_id',v_room_id,
      'slug',v_slug,
      'name',v_name,
      'visibility','public'
    )
  );
end;
$$;

revoke all on function public.social_live_join_public_room(text) from public,anon;
grant execute on function public.social_live_join_public_room(text) to authenticated;

create or replace function public.social_live_list_rooms(p_limit integer default 50)
returns jsonb
language plpgsql
stable
security invoker
set search_path=pg_catalog,public,auth
as $$
declare
  v_user uuid:=auth.uid();
  v_limit integer:=greatest(1,least(coalesce(p_limit,50),100));
  v_rooms jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  -- La RLS de social_live_rooms décide seule des salons visibles. Aucun annuaire
  -- de membres n'est exposé; joined/owned sont uniquement des booléens self-only.
  select coalesce(jsonb_agg(to_jsonb(x) order by x.created_at desc),'[]'::jsonb)
  into v_rooms
  from (
    select
      r.id as room_id,
      r.slug,
      r.name,
      r.description,
      r.visibility,
      r.created_at,
      (r.owner_user_id=v_user) as owned,
      exists(
        select 1 from public.social_live_room_members m
        where m.room_id=r.id and m.user_id=v_user
      ) as joined
    from public.social_live_rooms r
    where not r.is_archived
    order by r.created_at desc
    limit v_limit
  ) x;

  return jsonb_build_object('ok',true,'rooms',v_rooms);
end;
$$;

revoke all on function public.social_live_list_rooms(integer) from public,anon;
grant execute on function public.social_live_list_rooms(integer) to authenticated;

create or replace function public.social_live_me()
returns jsonb
language plpgsql
stable
security invoker
set search_path=pg_catalog,public,auth
as $$
declare
  v_user uuid:=auth.uid();
  v_label text;
  v_owned integer:=0;
  v_joined integer:=0;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  select coalesce(nullif(btrim(sp.display_name),''),nullif(btrim(sp.pseudo),''),'Membre SINJIRA')
  into v_label
  from public.social_profiles sp
  where sp.user_id=v_user
  limit 1;

  v_label:=coalesce(v_label,'Membre SINJIRA');

  select count(*)::integer into v_owned
  from public.social_live_rooms r
  where r.owner_user_id=v_user and not r.is_archived;

  select count(*)::integer into v_joined
  from public.social_live_room_members m
  where m.user_id=v_user;

  -- Aucun UUID utilisateur, date de naissance, IP, localisation ou détail
  -- d'adhésion d'autrui n'est retourné par /me.
  return jsonb_build_object(
    'ok',true,
    'profile_label',v_label,
    'owned_rooms',v_owned,
    'joined_rooms',v_joined
  );
end;
$$;

revoke all on function public.social_live_me() from public,anon;
grant execute on function public.social_live_me() to authenticated;

comment on function public.social_live_join_public_room(text) is
  'Commande typée derrière /join <slug>. SECURITY INVOKER; salons publics seulement; RLS et anti-raid existants restent autorité.';
comment on function public.social_live_list_rooms(integer) is
  'Commande typée derrière /rooms. Retourne uniquement les salons visibles par la RLS, sans annuaire de membres.';
comment on function public.social_live_me() is
  'Commande typée derrière /me. Résumé self-only sans UUID utilisateur ni donnée sensible.';

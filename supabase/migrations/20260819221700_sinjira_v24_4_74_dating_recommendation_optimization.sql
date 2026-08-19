-- SINJIRA™ V24.4.74 — optimisation du moteur de recommandations.
-- Calcule le payload de compatibilité une seule fois par candidat retenu et évite les opérateurs least/greatest sur UUID.

create or replace function public.dating_recommendations(p_limit integer default 8)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not exists(select 1 from public.dating_profiles where user_id=uid and active=true) then return '[]'::jsonb; end if;
  if not private.dating_is_eligible(uid) then return '[]'::jsonb; end if;

  with candidates as materialized (
    select d.user_id,sp.pseudo,sp.display_name
    from public.dating_profiles d
    join public.social_profiles sp on sp.user_id=d.user_id
    where d.user_id<>uid
      and d.active=true
      and private.dating_pair_allowed(uid,d.user_id)
      and not exists(
        select 1 from public.dating_introductions i
        where (i.user_a=uid and i.user_b=d.user_id)
           or (i.user_a=d.user_id and i.user_b=uid)
      )
  ), scored as materialized (
    select c.*,private.dating_pair_score(uid,c.user_id) as payload
    from candidates c
  ), limited as (
    select s.*,(s.payload->>'score')::integer as score
    from scored s
    where (s.payload->>'score')::integer>0
    order by (s.payload->>'score')::integer desc,s.pseudo
    limit greatest(1,least(coalesce(p_limit,8),20))
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'user_id',l.user_id,
    'pseudo',coalesce(nullif(l.pseudo,''),nullif(l.display_name,''),'Membre SINJIRA'),
    'compatibility_score',l.score,
    'strengths',l.payload->'strengths',
    'explore',l.payload->'explore'
  ) order by l.score desc,l.pseudo),'[]'::jsonb)
  into result
  from limited l;

  return result;
end;
$$;

revoke all on function public.dating_recommendations(integer) from public,anon;
grant execute on function public.dating_recommendations(integer) to authenticated;

comment on function public.dating_recommendations(integer) is 'Moteur local explicable V24.4.74 optimisé. Ne renvoie ni photo, ni courriel, ni réponses brutes du Registre.';

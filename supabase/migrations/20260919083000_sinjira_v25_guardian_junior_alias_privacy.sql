-- SINJIRA™ V25 — ne pas révéler l'alias Junior au tuteur.
-- L'alias Junior sert à pseudonymiser l'enfant dans la Communauté Junior.
-- Le tuteur a besoin de l'état et du lien de supervision, pas de cet alias public.

create or replace function public.guardian_junior_community_children()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  uid uuid:=auth.uid();
  result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(uid)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'minor_user_id',g.minor_user_id,
        'label',coalesce(nullif(p.pseudo,''),'Compte enfant'),
        'age_band',public.sinjira_age_band(g.minor_user_id),
        'enabled',c.revoked_at is null and c.minor_user_id is not null
      )
      order by p.pseudo nulls last
    ),
    '[]'::jsonb
  )
  into result
  from public.guardian_links g
  left join public.profiles p
    on p.user_id=g.minor_user_id
  left join public.junior_community_guardian_consents c
    on c.minor_user_id=g.minor_user_id
   and c.guardian_user_id=g.guardian_user_id
  where g.guardian_user_id=uid
    and g.status='verified'
    and g.revoked_at is null
    and public.sinjira_age_band(g.minor_user_id)='child';

  return result;
end;
$$;

revoke all on function public.guardian_junior_community_children()
from public,anon;
grant execute on function public.guardian_junior_community_children()
to authenticated;

comment on function public.guardian_junior_community_children() is
  'V25: liste parent minimale; n expose jamais junior_alias. L alias pseudonyme Junior reste réservé au contexte Junior de l enfant.';

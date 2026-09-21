-- SINJIRA™ V25 — fail-closed révocation tuteur Communauté Junior.
-- L'HUMAIN AVANT TOUT : un lien guardian_links révoqué ne doit jamais continuer
-- à activer Junior ni rester visible dans la liste du tuteur, y compris lorsqu'un
-- second tuteur valide maintient la bande d'âge `child`.

begin;

create or replace function private.sinjira_junior_community_enabled(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $junior$
  select private.sinjira_is_junior(p_user_id)
    and exists(
      select 1
      from public.guardian_links g
      join public.junior_community_guardian_consents c
        on c.minor_user_id=g.minor_user_id
       and c.guardian_user_id=g.guardian_user_id
       and c.revoked_at is null
      where g.minor_user_id=p_user_id
        and g.status='verified'
        and g.revoked_at is null
        and public.sinjira_age_band(g.guardian_user_id)='adult'
    );
$junior$;

revoke all on function private.sinjira_junior_community_enabled(uuid)
from public,anon,authenticated;
grant execute on function private.sinjira_junior_community_enabled(uuid)
to service_role;

create or replace function public.guardian_junior_community_children()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $
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
$;

revoke all on function public.guardian_junior_community_children()
from public,anon;
grant execute on function public.guardian_junior_community_children()
to authenticated;


comment on function private.sinjira_junior_community_enabled(uuid) is
'Communauté Junior V25: exige un lien tuteur vérifié non révoqué et un consentement Junior non révoqué; fail-closed en scénario multi-tuteur.';

comment on function public.guardian_junior_community_children() is
'Liste Junior parent V25: lien vérifié non révoqué, état minimal uniquement; junior_alias reste privé du contexte enfant.';

commit;

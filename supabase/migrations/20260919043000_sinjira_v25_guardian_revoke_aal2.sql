-- SINJIRA™ V25 — révocation de supervision avec agence de l'enfant préservée.
-- Un tuteur doit confirmer ce geste sensible en AAL2. Le mineur lié conserve
-- le droit de couper immédiatement son propre lien sans dépendre d'un second facteur.

create or replace function public.revoke_guardian_link(p_link_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $$
declare
  uid uuid:=auth.uid();
  r public.guardian_links%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  select * into r
  from public.guardian_links
  where id=p_link_id
    and uid in (guardian_user_id,minor_user_id)
  for update;

  if r.id is null then
    raise exception 'GUARDIAN_LINK_UNAVAILABLE';
  end if;

  if r.status='revoked' or r.revoked_at is not null then
    return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
  end if;

  -- Le tuteur doit step-up; le mineur garde une sortie immédiate fail-safe.
  if uid=r.guardian_user_id
     and coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  update public.guardian_links
  set status='revoked',
      revoked_at=now(),
      updated_at=now()
  where id=r.id;

  return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
end;
$$;

revoke all on function public.revoke_guardian_link(uuid)
from public,anon;
grant execute on function public.revoke_guardian_link(uuid)
to authenticated;

comment on function public.revoke_guardian_link(uuid) is
  'V25: tuteur exige AAL2 pour révoquer; mineur lié peut révoquer immédiatement son propre lien sans MFA; lien absent ou tiers partage la même erreur fail-closed.';

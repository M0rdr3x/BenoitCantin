-- SINJIRA™ V24.4.12 — finalisation sécurisée de la supervision jeunesse
-- Les liens tuteur/mineur ne sont plus modifiables directement par le navigateur.
-- Un jeune 14–17 en youth_pending peut consommer après inscription un code parental valide.

create or replace function public.redeem_guardian_signup_invite(p_code text)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  v_code text:=upper(trim(coalesce(p_code,'')));
  band text;
  inv public.guardian_signup_invites%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  band:=public.sinjira_age_band(uid);
  if band not in ('youth_pending','youth') then raise exception 'YOUTH_ACCOUNT_REQUIRED'; end if;
  if band='youth' and exists(select 1 from public.guardian_links g where g.minor_user_id=uid and g.status='verified') then
    raise exception 'GUARDIAN_ALREADY_VERIFIED';
  end if;
  if v_code !~ '^YOUTH-[A-Z0-9]{10}$' then raise exception 'INVALID_GUARDIAN_CODE_FORMAT'; end if;

  select * into inv
  from public.guardian_signup_invites
  where invite_code=v_code and used_at is null and expires_at>now()
  for update;
  if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
  if inv.guardian_user_id=uid then raise exception 'SELF_GUARDIAN_FORBIDDEN'; end if;
  if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;

  update public.guardian_signup_invites
  set used_at=now(),minor_user_id=uid
  where id=inv.id;
  -- Le trigger sync_guardian_signup_invite_link crée/réactive guardian_links en verified.

  return jsonb_build_object('ok',true,'status','verified','minor_user_id',uid);
end;
$$;
revoke all on function public.redeem_guardian_signup_invite(text) from public,anon;
grant execute on function public.redeem_guardian_signup_invite(text) to authenticated;

create or replace function public.revoke_guardian_link(p_link_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  r public.guardian_links%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into r from public.guardian_links where id=p_link_id for update;
  if r.id is null then raise exception 'GUARDIAN_LINK_NOT_FOUND'; end if;
  if uid not in (r.guardian_user_id,r.minor_user_id) then raise exception 'GUARDIAN_LINK_FORBIDDEN'; end if;
  if r.status='revoked' then return jsonb_build_object('ok',true,'status','revoked','link_id',r.id); end if;
  update public.guardian_links set status='revoked',revoked_at=now(),updated_at=now() where id=r.id;
  return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
end;
$$;
revoke all on function public.revoke_guardian_link(uuid) from public,anon;
grant execute on function public.revoke_guardian_link(uuid) to authenticated;

-- Le navigateur ne modifie plus directement les colonnes structurelles du lien.
drop policy if exists guardian_guardian_update on public.guardian_links;
drop policy if exists guardian_minor_request on public.guardian_links;
revoke insert,update,delete,truncate,references,trigger on public.guardian_links from authenticated;
grant select on public.guardian_links to authenticated;

-- Lecture des deux parties avec auth.uid() initialisé une seule fois par requête.
drop policy if exists guardian_read_parties on public.guardian_links;
create policy guardian_read_parties on public.guardian_links
for select to authenticated
using ((select auth.uid())=minor_user_id or (select auth.uid())=guardian_user_id);

comment on function public.redeem_guardian_signup_invite(text) is
  'Consomme un code parental à usage unique pour vérifier un compte jeunesse après inscription.';
comment on function public.revoke_guardian_link(uuid) is
  'Permet au tuteur ou au mineur lié de révoquer le lien de supervision sans modifier les autres colonnes.';

-- SINJIRA™ V24.4.13 — confidentialité des helpers de contexte
-- Copie conforme de la migration appliquée en production.

create or replace function public.is_fracture_party_member(
  p_party_id uuid,
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_party_id is null or p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')='service_role' or auth.uid() is null or p_user_id=auth.uid() then
      exists(select 1 from public.fracture_party_members m where m.party_id=p_party_id and m.user_id=p_user_id)
    else false
  end;
$$;
revoke all on function public.is_fracture_party_member(uuid,uuid) from public,anon;
grant execute on function public.is_fracture_party_member(uuid,uuid) to authenticated,service_role;

create or replace function public.sinjira_content_allowed(p_user_id uuid,p_body text)
returns boolean
language plpgsql
stable
security definer
set search_path=public,auth
as $$
declare
  band text;
  t text:=lower(coalesce(p_body,''));
begin
  if p_user_id is null then return false; end if;
  if coalesce(auth.jwt()->>'role','')<>'service_role' and auth.uid() is not null and p_user_id<>auth.uid() then return false; end if;
  band:=public.sinjira_age_band(p_user_id);
  if t ~ '(onlyfans|fansly|manyvids|justfor\.fans|loyalfans|chaturbate|myfreecams|sexcam|webcam adulte|vente de nudes|nudes for sale|escort service|service d.escolte)' then return false; end if;
  if band='youth' and t ~ '(\bnsfw\b|\b18\+\b|\bporn\b|\bporno\b|pornhub|xvideos|xnxx|redtube|sexting|nude|nudité sexuelle|contenu sexuel|rencontre sexuelle|sugar daddy|sugar baby)' then return false; end if;
  return band in ('adult','youth');
end;
$$;
revoke all on function public.sinjira_content_allowed(uuid,text) from public,anon;
grant execute on function public.sinjira_content_allowed(uuid,text) to authenticated,service_role;

create or replace function public.sinjira_cycle_allowed(
  p_cycle_id uuid,
  p_user_id uuid default auth.uid()
)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_cycle_id is null or p_user_id is null then false
    when coalesce(auth.jwt()->>'role','')<>'service_role' and auth.uid() is not null and p_user_id<>auth.uid() then false
    else exists(
      select 1 from public.parallel_world_cycles c
      where c.id=p_cycle_id and (
        c.audience='all' or
        (c.audience='adult' and public.sinjira_age_band(p_user_id)='adult') or
        (c.audience='youth' and public.sinjira_age_band(p_user_id)='youth')
      )
    )
  end;
$$;
revoke all on function public.sinjira_cycle_allowed(uuid,uuid) from public,anon;
grant execute on function public.sinjira_cycle_allowed(uuid,uuid) to authenticated,service_role;

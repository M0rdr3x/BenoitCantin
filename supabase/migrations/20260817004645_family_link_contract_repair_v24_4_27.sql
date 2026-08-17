begin;

-- V24.4.27
-- Répare le contrat des liens familiaux : la RPC de rédemption utilisait
-- d'anciennes valeurs ('active', 'adult_child', 'family') incompatibles avec
-- les contraintes actuelles de private_family_links. L'invitation du compte
-- source vaut consentement au lien, et la rédemption du second adulte confirme
-- le lien. Le miroir fiction reste désactivé à la création : seul le propriétaire
-- peut ensuite l'activer via sa politique RLS/MFA, ce qui évite qu'un invité
-- décide unilatéralement de projeter une relation privée dans la fiction.

create or replace function public.redeem_family_link_invite(
  p_code text,
  p_relationship_type text,
  p_started_on date default null::date,
  p_mirror_to_fiction boolean default false
)
returns uuid
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  inv public.family_link_invites%rowtype;
  lid uuid;
  rel_input text := lower(trim(coalesce(p_relationship_type,'')));
  rel text;
begin
  if auth.uid() is null then
    raise exception 'Connexion requise.';
  end if;

  if public.sinjira_age_band(auth.uid()) <> 'adult' then
    raise exception 'Les liens familiaux de compte sont gérés par un compte adulte.';
  end if;

  rel := case rel_input
    when 'partner' then 'partner'
    when 'spouse' then 'spouse'
    when 'sibling' then 'sibling'
    when 'parent' then 'parent'
    when 'child' then 'child'
    when 'adult_child' then 'child'
    when 'family' then 'other'
    when 'other' then 'other'
    else null
  end;

  if rel is null then
    raise exception 'Type de lien non permis.';
  end if;

  select * into inv
  from public.family_link_invites
  where invite_code = upper(trim(coalesce(p_code,'')))
    and used_at is null
    and expires_at > now()
  for update;

  if inv.id is null then
    raise exception 'Code expiré ou invalide.';
  end if;

  if inv.owner_user_id = auth.uid() then
    raise exception 'Vous ne pouvez pas relier votre compte à lui-même.';
  end if;

  if public.sinjira_age_band(inv.owner_user_id) <> 'adult' then
    raise exception 'Le compte source doit être adulte.';
  end if;

  insert into public.private_family_links(
    owner_user_id,
    related_user_id,
    relationship_type,
    status,
    started_on,
    mirror_to_fiction,
    owner_consented_at,
    related_consented_at
  )
  values(
    inv.owner_user_id,
    auth.uid(),
    rel,
    'confirmed',
    p_started_on,
    false,
    inv.created_at,
    now()
  )
  returning id into lid;

  update public.family_link_invites
  set used_at = now()
  where id = inv.id;

  return lid;
end;
$$;

revoke all on function public.redeem_family_link_invite(text,text,date,boolean) from public, anon;
grant execute on function public.redeem_family_link_invite(text,text,date,boolean) to authenticated;

create or replace function public.sinjira_family_link_health()
returns jsonb
language sql
stable
security invoker
set search_path = public, pg_catalog
as $$
  with fn as (
    select lower(pg_get_functiondef('public.redeem_family_link_invite(text,text,date,boolean)'::regprocedure)) as def
  ), checks as (
    select
      position('''confirmed''' in def) > 0 as confirmed_status,
      position('when ''adult_child'' then ''child''' in def) > 0 as adult_child_mapped,
      position('when ''family'' then ''other''' in def) > 0 as family_mapped,
      position('p_mirror_to_fiction boolean default false' in def) > 0
        and position('mirror_to_fiction,' in def) > 0
        and position('false,' in def) > 0 as mirror_defaults_private
    from fn
  )
  select jsonb_build_object(
    'ok', confirmed_status and adult_child_mapped and family_mapped and mirror_defaults_private,
    'version','24.4.27',
    'confirmed_status',confirmed_status,
    'legacy_relationship_mapping',adult_child_mapped and family_mapped,
    'mirror_defaults_private',mirror_defaults_private
  )
  from checks;
$$;

revoke all on function public.sinjira_family_link_health() from public, anon, authenticated;
grant execute on function public.sinjira_family_link_health() to service_role;

commit;

-- SINJIRA™ V25 — consentement et step-up pour les métadonnées de contacts jeunesse.
-- Ce RPC ne révèle jamais le contenu des messages, mais retourne des métadonnées
-- relationnelles sensibles (identité/pseudo, réseau, dernière date de contact).
-- Il exige donc à la fois l'autorisation explicite du lien et une session AAL2.

create or replace function public.get_guardian_youth_contacts(p_child_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $$
declare
  uid uuid:=auth.uid();
  result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  if not public.sinjira_parent_can_supervise(uid,p_child_user_id) then
    raise exception 'GUARDIAN_ACCESS_REQUIRED';
  end if;

  if not exists(
    select 1
    from public.guardian_links g
    where g.guardian_user_id=uid
      and g.minor_user_id=p_child_user_id
      and g.status='verified'
      and g.revoked_at is null
      and g.can_view_contact_metadata is true
  ) then
    raise exception 'GUARDIAN_CONTACT_METADATA_NOT_ALLOWED';
  end if;

  if coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  with contacts as (
    select
      case
        when m.sender_user_id=p_child_user_id then m.recipient_user_id
        else m.sender_user_id
      end other_user_id,
      max(m.created_at) last_contact_at,
      'Compte'::text network
    from public.social_real_messages m
    where p_child_user_id in(m.sender_user_id,m.recipient_user_id)
    group by 1

    union all

    select
      case
        when m.sender_user_id=p_child_user_id then m.recipient_user_id
        else m.sender_user_id
      end,
      max(m.created_at),
      'Personnage'::text
    from public.social_character_messages m
    where p_child_user_id in(m.sender_user_id,m.recipient_user_id)
    group by 1
  ),
  grouped as (
    select
      other_user_id,
      max(last_contact_at) last_contact_at,
      array_agg(distinct network) networks
    from contacts
    group by other_user_id
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'user_id',g.other_user_id,
        'pseudo',coalesce(sp.pseudo,'Membre SINJIRA'),
        'display_name',sp.display_name,
        'networks',g.networks,
        'last_contact_at',g.last_contact_at
      )
      order by g.last_contact_at desc
    ),
    '[]'::jsonb
  )
  into result
  from grouped g
  left join public.social_profiles sp on sp.user_id=g.other_user_id;

  return result;
end;
$$;

revoke all on function public.get_guardian_youth_contacts(uuid)
from public,anon;
grant execute on function public.get_guardian_youth_contacts(uuid)
to authenticated;

comment on function public.get_guardian_youth_contacts(uuid) is
  'V25: métadonnées de contacts jeunesse uniquement; exige supervision active, consentement can_view_contact_metadata=true et session tuteur AAL2; aucun contenu de message.';

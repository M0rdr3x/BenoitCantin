-- SINJIRA™ V25 — consentement et step-up pour les métadonnées de contacts jeunesse.
-- Ce RPC ne révèle jamais le contenu des messages. Dès sa première exposition il
-- minimise les métadonnées et cloisonne l'identité Compte de l'identité Personnage.
-- Il exige l'autorisation explicite du compte jeunesse et une session tuteur AAL2.

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

  with contact_events as (
    select
      'Compte'::text network,
      case
        when m.sender_user_id=p_child_user_id then m.recipient_user_id
        else m.sender_user_id
      end contact_key,
      coalesce(sp.pseudo,'Membre SINJIRA') contact_label,
      m.created_at
    from public.social_real_messages m
    left join public.social_profiles sp
      on sp.user_id=case
        when m.sender_user_id=p_child_user_id then m.recipient_user_id
        else m.sender_user_id
      end
    where p_child_user_id in(m.sender_user_id,m.recipient_user_id)

    union all

    select
      'Personnage'::text network,
      case
        when m.sender_user_id=p_child_user_id then m.recipient_character_id
        else m.sender_character_id
      end contact_key,
      coalesce(csp.public_name,'Personnage SINJIRA') contact_label,
      m.created_at
    from public.social_character_messages m
    left join public.character_social_profiles csp
      on csp.character_id=case
        when m.sender_user_id=p_child_user_id then m.recipient_character_id
        else m.sender_character_id
      end
    where p_child_user_id in(m.sender_user_id,m.recipient_user_id)
  ),
  grouped as (
    select
      network,
      contact_key,
      contact_label,
      max(created_at) last_contact_at
    from contact_events
    group by network,contact_key,contact_label
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'contact_label',g.contact_label,
        'network',g.network,
        'last_contact_date',(timezone('UTC',g.last_contact_at))::date
      )
      order by g.last_contact_at desc,g.network,g.contact_label
    ),
    '[]'::jsonb
  )
  into result
  from grouped g;

  return result;
end;
$$;

revoke all on function public.get_guardian_youth_contacts(uuid)
from public,anon;
grant execute on function public.get_guardian_youth_contacts(uuid)
to authenticated;

comment on function public.get_guardian_youth_contacts(uuid) is
  'V25 dès première exposition: supervision active + opt-in jeunesse + AAL2; identité Compte/Personnage cloisonnée; renvoie seulement contact_label, network et last_contact_date. Aucun UUID, display_name, heure précise ou contenu.';

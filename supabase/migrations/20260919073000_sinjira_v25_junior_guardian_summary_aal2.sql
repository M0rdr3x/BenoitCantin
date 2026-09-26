-- SINJIRA™ V25 — résumé parental Junior minimisé et protégé par AAL2.
-- La désactivation Junior reste volontairement disponible en AAL1; seule la lecture
-- du résumé d'activité nécessite un step-up, car il révèle des métadonnées comportementales.

create or replace function public.junior_guardian_summary(p_child_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  uid uuid:=auth.uid();
  last_activity timestamptz;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  if not public.sinjira_parent_can_supervise(uid,p_child_user_id) then
    raise exception 'GUARDIAN_ACCESS_REQUIRED';
  end if;

  if coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  select max(x.at)
  into last_activity
  from (
    select max(p.created_at) at
    from public.junior_community_posts p
    where p.author_user_id=p_child_user_id

    union all

    select max(c.created_at) at
    from public.junior_community_comments c
    where c.author_user_id=p_child_user_id
  ) x;

  return jsonb_build_object(
    'enabled',private.sinjira_junior_community_enabled(p_child_user_id),
    'age_band',public.sinjira_age_band(p_child_user_id),
    'posts',(
      select count(*)
      from public.junior_community_posts p
      where p.author_user_id=p_child_user_id
        and p.status='active'
    ),
    'comments',(
      select count(*)
      from public.junior_community_comments c
      where c.author_user_id=p_child_user_id
        and c.status='active'
    ),
    'last_activity_date',
      case
        when last_activity is null then null
        else (timezone('UTC',last_activity))::date
      end,
    'content_visible_to_guardian',false,
    'private_messages_available',false
  );
end;
$$;

revoke all on function public.junior_guardian_summary(uuid)
from public,anon;
grant execute on function public.junior_guardian_summary(uuid)
to authenticated;

comment on function public.junior_guardian_summary(uuid) is
  'V25: résumé parental sans contenu, lecture AAL2 obligatoire, dernière activité réduite à la date UTC; désactivation Junior reste fail-safe AAL1.';

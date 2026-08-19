-- SINJIRA V24.4.78 — signalement Rencontres, preuves minimales et suspension sociale.
-- Les identités restent résolues côté serveur; aucun user_id cible n'est exposé au membre signalant.

create or replace function private.dating_is_eligible(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
select coalesce(
  private.dating_age(p_user_id)>=18
  and s.legacy_status='active'
  and s.relationship_data_opt_in is true
  and s.relationship_status='single'
  and p.enabled is true
  and p.serious_intent_confirmed is true
  and p.single_confirmed_at is not null
  and p.single_confirmed_at>=now()-interval '90 days'
  and p.gender_identity is not null
  and btrim(p.intro)<>''
  and not exists(
    select 1
    from public.social_suspensions ss
    where ss.user_id=p_user_id
      and (ss.until_at is null or ss.until_at>now())
  )
  and not private.dating_contains_contact_info(p.region)
  and not private.dating_contains_contact_info(p.intro)
  and not private.dating_array_contains_contact_info(p.values_tags)
  and not private.dating_array_contains_contact_info(p.interests_tags)
  and not private.dating_array_contains_contact_info(p.lifestyle_tags)
  and not private.dating_array_contains_contact_info(p.communication_tags)
  and not private.dating_array_contains_contact_info(p.goals_tags)
  and not private.dating_array_contains_contact_info(p.registry_traits)
  and exists(
    select 1 from public.dating_preferences d
    where d.user_id=p_user_id
      and cardinality(d.seeking_genders)>0
      and not private.dating_contains_contact_info(d.partner_description)
      and not private.dating_contains_contact_info(d.dealbreakers)
      and not private.dating_array_contains_contact_info(d.wanted_values)
      and not private.dating_array_contains_contact_info(d.wanted_interests)
      and not private.dating_array_contains_contact_info(d.wanted_lifestyle)
      and not private.dating_array_contains_contact_info(d.wanted_communication)
      and not private.dating_array_contains_contact_info(d.wanted_goals)
  ),false)
from public.account_safety_profiles s
join public.dating_profiles p on p.user_id=s.user_id
where s.user_id=p_user_id;
$$;

create or replace function public.dating_report_connection(
  p_connection_id uuid,
  p_reason text,
  p_details text default null,
  p_block boolean default false
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_other_profile uuid;
  v_status text;
  v_report_id uuid;
  v_details text:=nullif(btrim(coalesce(p_details,'')),'');
  v_my_count integer:=0;
  v_their_count integer:=0;
  v_messages jsonb:='[]'::jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if coalesce(p_reason,'') not in ('harassment','sexual_content','pressure','scam','hate','threats','impersonation','other') then
    raise exception 'DATING_REPORT_REASON_INVALID';
  end if;
  if v_details is not null and char_length(v_details)>1200 then
    raise exception 'DATING_REPORT_DETAILS_TOO_LONG';
  end if;

  select id into v_me from public.dating_profiles where user_id=v_user;
  if v_me is null then raise exception 'DATING_PROFILE_REQUIRED'; end if;

  select
    case when c.profile_a_id=v_me then c.profile_b_id else c.profile_a_id end,
    c.status
  into v_other_profile,v_status
  from public.dating_connections c
  where c.id=p_connection_id
    and v_me in(c.profile_a_id,c.profile_b_id);

  if v_other_profile is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;

  if exists(
    select 1 from public.social_reports r
    where r.reporter_user_id=v_user
      and r.network='real'
      and r.target_type='profile'
      and r.target_id=v_other_profile
      and r.status='open'
      and r.snapshot->>'source'='dating'
      and r.snapshot->>'dating_connection_id'=p_connection_id::text
  ) then
    raise exception 'DATING_REPORT_ALREADY_OPEN';
  end if;

  if (
    select count(*)
    from public.social_reports r
    where r.reporter_user_id=v_user
      and r.created_at>now()-interval '1 hour'
  )>=10 then
    raise exception 'DATING_REPORT_RATE_LIMIT';
  end if;

  select
    count(*) filter(where dm.sender_profile_id=v_me)::int,
    count(*) filter(where dm.sender_profile_id=v_other_profile)::int
  into v_my_count,v_their_count
  from public.dating_messages dm
  where dm.connection_id=p_connection_id;

  select coalesce(jsonb_agg(jsonb_build_object(
    'side',case when x.sender_profile_id=v_me then 'reporter' else 'other' end,
    'body',x.body,
    'created_at',x.created_at
  ) order by x.created_at),'[]'::jsonb)
  into v_messages
  from (
    select dm.sender_profile_id,dm.body,dm.created_at
    from public.dating_messages dm
    where dm.connection_id=p_connection_id
    order by dm.created_at desc
    limit 30
  ) x;

  insert into public.social_reports(
    reporter_user_id,network,target_type,target_id,reason,snapshot
  ) values(
    v_user,
    'real',
    'profile',
    v_other_profile,
    p_reason,
    jsonb_build_object(
      'source','dating',
      'dating_connection_id',p_connection_id,
      'dating_profile_id',v_other_profile,
      'connection_status',v_status,
      'details',v_details,
      'message_counts',jsonb_build_object('reporter',v_my_count,'other',v_their_count),
      'messages',v_messages,
      'identity_data_included',false
    )
  ) returning id into v_report_id;

  if coalesce(p_block,false) then
    insert into public.social_blocks(blocker_user_id,blocked_user_id)
    select v_user,p.user_id
    from public.dating_profiles p
    where p.id=v_other_profile
    on conflict (blocker_user_id,blocked_user_id) do nothing;

    update public.dating_connections
    set status='closed',closed_at=now(),a_photo_consent=false,b_photo_consent=false
    where id=p_connection_id;
  end if;

  return jsonb_build_object('ok',true,'report_id',v_report_id,'blocked',coalesce(p_block,false));
end;
$$;

revoke all on function public.dating_report_connection(uuid,text,text,boolean) from public,anon;
grant execute on function public.dating_report_connection(uuid,text,text,boolean) to authenticated;

comment on function public.dating_report_connection(uuid,text,text,boolean) is
'Crée un signalement Rencontres dans social_reports avec transcript limité et sans identifiant utilisateur cible exposé; peut bloquer et fermer la rencontre atomiquement.';
create table if not exists private.moderation_decisions (
  id uuid primary key default gen_random_uuid(),
  subject_user_id uuid null references auth.users(id) on delete set null,
  report_id uuid null references public.social_reports(id) on delete set null,
  network text not null check (network in ('real','character','dating','account')),
  target_type text not null check (target_type in ('post','comment','message','profile','account')),
  target_id uuid null,
  action text not null check (action in ('no_action','hide_content','suspend_social','disable_dating')),
  status text not null default 'active' check (status in ('active','reversed','expired')),
  policy_rule text not null check (char_length(btrim(policy_rule)) between 3 and 240),
  statement_of_reasons text not null check (char_length(btrim(statement_of_reasons)) between 20 and 4000),
  evidence_snapshot jsonb not null default '{}'::jsonb,
  urgency text not null default 'standard' check (urgency in ('standard','urgent_harm','illegal_content')),
  decision_source text not null default 'human_admin' check (decision_source='human_admin'),
  starts_at timestamptz not null default now(),
  ends_at timestamptz null,
  appeal_deadline timestamptz not null default (now()+interval '6 months'),
  decided_by uuid null references auth.users(id) on delete set null,
  decided_at timestamptz not null default now(),
  reversed_at timestamptz null,
  reversed_by uuid null references auth.users(id) on delete set null,
  reversal_reason text null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (ends_at is null or ends_at>starts_at),
  check (appeal_deadline>=decided_at+interval '6 months')
);

create index if not exists moderation_decisions_subject_idx on private.moderation_decisions(subject_user_id,decided_at desc);
create index if not exists moderation_decisions_target_idx on private.moderation_decisions(network,target_type,target_id,status);
create index if not exists moderation_decisions_report_idx on private.moderation_decisions(report_id);

create table if not exists private.moderation_appeals (
  id uuid primary key default gen_random_uuid(),
  decision_id uuid not null references private.moderation_decisions(id) on delete cascade,
  appellant_user_id uuid null references auth.users(id) on delete set null,
  appeal_text text not null check (char_length(btrim(appeal_text)) between 20 and 4000),
  status text not null default 'pending' check (status in ('pending','upheld','reversed','withdrawn')),
  submitted_at timestamptz not null default now(),
  reviewed_by uuid null references auth.users(id) on delete set null,
  reviewed_at timestamptz null,
  review_reason text null,
  human_review_required boolean not null default true check (human_review_required=true),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(decision_id,appellant_user_id),
  check ((status='pending' and reviewed_at is null and reviewed_by is null) or status='withdrawn' or (status in ('upheld','reversed') and reviewed_at is not null and reviewed_by is not null and char_length(btrim(coalesce(review_reason,'')))>=20))
);

create index if not exists moderation_appeals_pending_idx on private.moderation_appeals(status,submitted_at);
create index if not exists moderation_appeals_appellant_idx on private.moderation_appeals(appellant_user_id,submitted_at desc);

alter table private.moderation_decisions enable row level security;
alter table private.moderation_appeals enable row level security;
revoke all on table private.moderation_decisions from public,anon,authenticated;
revoke all on table private.moderation_appeals from public,anon,authenticated;

comment on table private.moderation_decisions is 'Décisions humaines de modération SINJIRA. Les contenus ordinaires sont masqués de façon réversible plutôt que supprimés physiquement.';
comment on table private.moderation_appeals is 'Appels internes gratuits contre les décisions de modération. Toute issue finale exige une révision humaine.';

alter table public.social_suspensions add column if not exists moderation_decision_id uuid null references private.moderation_decisions(id) on delete set null;
create index if not exists social_suspensions_moderation_decision_idx on public.social_suspensions(moderation_decision_id);

create or replace function public.moderation_content_visible(p_network text,p_target_type text,p_target_id uuid)
returns boolean language sql stable security definer set search_path=pg_catalog,private as $$
  select not exists(
    select 1 from private.moderation_decisions d
    where d.network=p_network and d.target_type=p_target_type and d.target_id=p_target_id
      and d.action='hide_content' and d.status='active' and d.starts_at<=now()
      and (d.ends_at is null or d.ends_at>now())
  );
$$;
revoke all on function public.moderation_content_visible(text,text,uuid) from public,anon;
grant execute on function public.moderation_content_visible(text,text,uuid) to authenticated;

create or replace function public.moderation_my_decisions(p_limit integer default 50)
returns jsonb language plpgsql stable security definer set search_path=pg_catalog,public,private,auth as $$
declare v_user uuid:=auth.uid(); v_rows jsonb;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select coalesce(jsonb_agg(to_jsonb(x) order by x.decided_at desc),'[]'::jsonb) into v_rows
  from (
    select d.id as decision_id,d.network,d.target_type,d.action,d.status,d.policy_rule,d.statement_of_reasons,
           d.urgency,d.starts_at,d.ends_at,d.appeal_deadline,d.decided_at,
           a.id as appeal_id,a.status as appeal_status,a.submitted_at as appeal_submitted_at,
           a.reviewed_at as appeal_reviewed_at,a.review_reason,
           (d.status='active' and d.appeal_deadline>=now() and a.id is null) as can_appeal
    from private.moderation_decisions d
    left join lateral (
      select ma.id,ma.status,ma.submitted_at,ma.reviewed_at,ma.review_reason
      from private.moderation_appeals ma
      where ma.decision_id=d.id and ma.appellant_user_id=v_user
      order by ma.submitted_at desc limit 1
    ) a on true
    where d.subject_user_id=v_user
    order by d.decided_at desc
    limit greatest(1,least(coalesce(p_limit,50),100))
  ) x;
  return jsonb_build_object('ok',true,'decisions',v_rows);
end;
$$;
revoke all on function public.moderation_my_decisions(integer) from public,anon;
grant execute on function public.moderation_my_decisions(integer) to authenticated;

create or replace function public.moderation_submit_appeal(p_decision_id uuid,p_appeal_text text)
returns jsonb language plpgsql security definer set search_path=pg_catalog,public,private,auth as $$
declare v_user uuid:=auth.uid(); v_text text:=btrim(coalesce(p_appeal_text,'')); v_decision private.moderation_decisions%rowtype; v_appeal uuid;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  if char_length(v_text)<20 or char_length(v_text)>4000 then raise exception 'APPEAL_TEXT_LENGTH'; end if;
  select * into v_decision from private.moderation_decisions where id=p_decision_id and subject_user_id=v_user;
  if v_decision.id is null then raise exception 'DECISION_NOT_FOUND'; end if;
  if v_decision.status<>'active' then raise exception 'DECISION_NOT_APPEALABLE'; end if;
  if v_decision.appeal_deadline<now() then raise exception 'APPEAL_DEADLINE_PASSED'; end if;
  if exists(select 1 from private.moderation_appeals where decision_id=p_decision_id and appellant_user_id=v_user) then raise exception 'APPEAL_ALREADY_EXISTS'; end if;
  insert into private.moderation_appeals(decision_id,appellant_user_id,appeal_text) values(p_decision_id,v_user,v_text) returning id into v_appeal;
  return jsonb_build_object('ok',true,'appeal_id',v_appeal,'status','pending','fee',0,'human_review_required',true);
end;
$$;
revoke all on function public.moderation_submit_appeal(uuid,text) from public,anon;
grant execute on function public.moderation_submit_appeal(uuid,text) to authenticated;

drop policy if exists real_posts_read on public.social_real_posts;
create policy real_posts_read on public.social_real_posts for select to authenticated using (
  public.sinjira_can_social_interact((select auth.uid()),user_id)
  and not public.social_is_blocked((select auth.uid()),user_id)
  and public.moderation_content_visible('real','post',id)
);

drop policy if exists real_comments_read on public.social_real_comments;
create policy real_comments_read on public.social_real_comments for select to authenticated using (
  public.sinjira_can_social_interact((select auth.uid()),user_id)
  and not public.social_is_blocked((select auth.uid()),user_id)
  and public.moderation_content_visible('real','comment',id)
  and exists(select 1 from public.social_real_posts p where p.id=social_real_comments.post_id
    and public.sinjira_can_social_interact((select auth.uid()),p.user_id)
    and public.moderation_content_visible('real','post',p.id))
);

drop policy if exists char_posts_read on public.social_character_posts;
create policy char_posts_read on public.social_character_posts for select to authenticated using (
  public.sinjira_can_social_interact((select auth.uid()),user_id)
  and not public.social_is_blocked((select auth.uid()),user_id)
  and public.moderation_content_visible('character','post',id)
);

drop policy if exists char_comments_read on public.social_character_comments;
create policy char_comments_read on public.social_character_comments for select to authenticated using (
  public.sinjira_can_social_interact((select auth.uid()),user_id)
  and not public.social_is_blocked((select auth.uid()),user_id)
  and public.moderation_content_visible('character','comment',id)
  and exists(select 1 from public.social_character_posts p where p.id=social_character_comments.post_id
    and public.sinjira_can_social_interact((select auth.uid()),p.user_id)
    and public.moderation_content_visible('character','post',p.id))
);

drop policy if exists real_messages_read on public.social_real_messages;
create policy real_messages_read on public.social_real_messages for select to authenticated using (
  (((select auth.uid())=sender_user_id) or ((select auth.uid())=recipient_user_id))
  and public.sinjira_can_social_interact(sender_user_id,recipient_user_id)
  and public.moderation_content_visible('real','message',id)
);

drop policy if exists char_messages_read on public.social_character_messages;
create policy char_messages_read on public.social_character_messages for select to authenticated using (
  (((select auth.uid())=sender_user_id) or ((select auth.uid())=recipient_user_id))
  and public.sinjira_can_social_interact(sender_user_id,recipient_user_id)
  and public.moderation_content_visible('character','message',id)
);

drop policy if exists real_messages_mark_read on public.social_real_messages;
create policy real_messages_mark_read on public.social_real_messages for update to authenticated
using (((select auth.uid())=recipient_user_id) and public.moderation_content_visible('real','message',id))
with check (((select auth.uid())=recipient_user_id) and read_at is not null and public.moderation_content_visible('real','message',id));

drop policy if exists char_messages_mark_read on public.social_character_messages;
create policy char_messages_mark_read on public.social_character_messages for update to authenticated
using (((select auth.uid())=recipient_user_id) and public.moderation_content_visible('character','message',id))
with check (((select auth.uid())=recipient_user_id) and read_at is not null and public.moderation_content_visible('character','message',id));

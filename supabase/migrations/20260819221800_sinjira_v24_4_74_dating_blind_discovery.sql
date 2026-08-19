-- SINJIRA™ V24.4.74 — découverte réellement aveugle.
-- Avant acceptation mutuelle, le navigateur ne reçoit ni user_id cible, ni pseudo, ni avatar.
-- Une recommandation est représentée par un jeton opaque, court et révocable.

create table if not exists public.dating_recommendation_tokens (
  id uuid primary key default gen_random_uuid(),
  viewer_user_id uuid not null references auth.users(id) on delete cascade,
  target_user_id uuid not null references auth.users(id) on delete cascade,
  expires_at timestamptz not null default (now()+interval '24 hours'),
  created_at timestamptz not null default now(),
  check (viewer_user_id<>target_user_id),
  unique(viewer_user_id,target_user_id)
);

create index if not exists dating_recommendation_tokens_expiry_idx
  on public.dating_recommendation_tokens(expires_at);

alter table public.dating_recommendation_tokens enable row level security;
revoke all on table public.dating_recommendation_tokens from public,anon,authenticated;
grant all on table public.dating_recommendation_tokens to service_role;

create or replace function private.dating_issue_recommendation_token(p_viewer uuid,p_target uuid)
returns uuid
language plpgsql volatile security definer
set search_path=pg_catalog,public
as $$
declare token_id uuid;
begin
  insert into public.dating_recommendation_tokens(viewer_user_id,target_user_id,expires_at)
  values(p_viewer,p_target,now()+interval '24 hours')
  on conflict(viewer_user_id,target_user_id) do update
    set expires_at=excluded.expires_at
  returning id into token_id;
  return token_id;
end;
$$;
revoke all on function private.dating_issue_recommendation_token(uuid,uuid) from public,anon,authenticated;
grant execute on function private.dating_issue_recommendation_token(uuid,uuid) to service_role;

create or replace function public.dating_recommendations(p_limit integer default 8)
returns jsonb
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not exists(select 1 from public.dating_profiles where user_id=uid and active=true) then return '[]'::jsonb; end if;
  if not private.dating_is_eligible(uid) then return '[]'::jsonb; end if;

  delete from public.dating_recommendation_tokens where expires_at<=now();

  with candidates as materialized (
    select d.user_id
    from public.dating_profiles d
    where d.user_id<>uid
      and d.active=true
      and private.dating_pair_allowed(uid,d.user_id)
      and not exists(
        select 1 from public.dating_introductions i
        where (i.user_a=uid and i.user_b=d.user_id)
           or (i.user_a=d.user_id and i.user_b=uid)
      )
  ), scored as materialized (
    select c.user_id,private.dating_pair_score(uid,c.user_id) as payload
    from candidates c
  ), limited as materialized (
    select s.user_id,s.payload,(s.payload->>'score')::integer as score
    from scored s
    where (s.payload->>'score')::integer>0
    order by (s.payload->>'score')::integer desc,s.user_id
    limit greatest(1,least(coalesce(p_limit,8),20))
  ), tokenized as (
    select l.*,private.dating_issue_recommendation_token(uid,l.user_id) as recommendation_token
    from limited l
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'recommendation_token',t.recommendation_token,
    'compatibility_score',t.score,
    'strengths',t.payload->'strengths',
    'explore',t.payload->'explore'
  ) order by t.score desc,t.recommendation_token),'[]'::jsonb)
  into result
  from tokenized t;

  return result;
end;
$$;
revoke all on function public.dating_recommendations(integer) from public,anon;
grant execute on function public.dating_recommendations(integer) to authenticated;

create or replace function public.dating_request_introduction(p_recommendation_token uuid)
returns uuid
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); target_id uuid; a uuid; b uuid; rid uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select t.target_user_id into target_id
  from public.dating_recommendation_tokens t
  where t.id=p_recommendation_token and t.viewer_user_id=uid and t.expires_at>now()
  for update;
  if target_id is null then raise exception 'DATING_RECOMMENDATION_EXPIRED'; end if;
  if not private.dating_pair_allowed(uid,target_id) then raise exception 'DATING_PAIR_NOT_ALLOWED'; end if;
  if uid::text<target_id::text then a:=uid;b:=target_id; else a:=target_id;b:=uid; end if;
  if exists(select 1 from public.dating_introductions where user_a=a and user_b=b) then raise exception 'INTRO_ALREADY_EXISTS'; end if;

  insert into public.dating_introductions(user_a,user_b,requested_by)
  values(a,b,uid) returning id into rid;

  delete from public.dating_recommendation_tokens
  where (viewer_user_id=uid and target_user_id=target_id)
     or (viewer_user_id=target_id and target_user_id=uid);

  insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
  values(target_id,'dating_intro','Nouvelle présentation proposée','Une personne compatible souhaite ouvrir une présentation.','dating_introduction',rid,'/compte/rencontres.html');
  return rid;
end;
$$;
revoke all on function public.dating_request_introduction(uuid) from public,anon;
grant execute on function public.dating_request_introduction(uuid) to authenticated;

create or replace function public.dating_my_introductions()
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'id',i.id,
    'status',i.status,
    'requested_by_me',i.requested_by=uid,
    'other_user_id',case when i.status='accepted' then case when i.user_a=uid then i.user_b else i.user_a end else null end,
    'other_pseudo',case when i.status='accepted' then coalesce(nullif(sp.pseudo,''),nullif(sp.display_name,''),'Membre SINJIRA') else 'Membre compatible' end,
    'accepted_at',i.accepted_at,
    'created_at',i.created_at
  ) order by i.updated_at desc),'[]'::jsonb) into result
  from public.dating_introductions i
  left join public.social_profiles sp
    on sp.user_id=case when i.user_a=uid then i.user_b else i.user_a end
  where uid in(i.user_a,i.user_b);
  return result;
end;
$$;
revoke all on function public.dating_my_introductions() from public,anon;
grant execute on function public.dating_my_introductions() to authenticated;

comment on table public.dating_recommendation_tokens is 'Jetons opaques de découverte Rencontres. Aucun accès navigateur direct; durée 24 h.';
comment on function public.dating_recommendations(integer) is 'Découverte aveugle V24.4.74: aucun user_id cible, pseudo, courriel ou avatar avant présentation acceptée.';
comment on function public.dating_request_introduction(uuid) is 'Consomme un jeton opaque de recommandation appartenant au compte courant et revalide la compatibilité mutuelle.';

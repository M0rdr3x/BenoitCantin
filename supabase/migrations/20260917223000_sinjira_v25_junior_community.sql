-- SINJIRA™ V25 — Communauté Junior 11–12 ans, isolée et activée par un parent/tuteur.
-- Principe : L'humain avant tout. Protéger sans surveiller.
-- La Communauté Junior est séparée des réseaux adulte/jeunesse existants :
--   * 11–12 ans seulement (bande child);
--   * activation explicite par un parent/tuteur vérifié sous AAL2; la désactivation reste fail-safe en AAL1;
--   * pseudonyme Junior généré, sans nom réel, avatar, courriel ni UUID exposé au client;
--   * texte uniquement, sans liens/coordonnées, sans rencontres, sans commerce et sans messagerie privée;
--   * signalement + blocage disponibles; les adultes et les 13–17 ans ne peuvent pas lire ce fil.

create table if not exists public.junior_community_guardian_consents(
  minor_user_id uuid not null references auth.users(id) on delete cascade,
  guardian_user_id uuid not null references auth.users(id) on delete cascade,
  consented_at timestamptz not null default now(),
  revoked_at timestamptz,
  primary key(minor_user_id,guardian_user_id)
);

create table if not exists public.junior_community_posts(
  id uuid primary key default gen_random_uuid(),
  author_user_id uuid not null references auth.users(id) on delete cascade,
  body text not null check(char_length(body) between 1 and 500),
  status text not null default 'active' check(status in('active','removed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.junior_community_comments(
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.junior_community_posts(id) on delete cascade,
  author_user_id uuid not null references auth.users(id) on delete cascade,
  body text not null check(char_length(body) between 1 and 300),
  status text not null default 'active' check(status in('active','removed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.junior_community_guardian_consents enable row level security;
alter table public.junior_community_posts enable row level security;
alter table public.junior_community_comments enable row level security;

-- Aucun accès table direct depuis le navigateur. Toute lecture/écriture passe par des RPC bornées.
revoke all on table public.junior_community_guardian_consents from public,anon,authenticated;
revoke all on table public.junior_community_posts from public,anon,authenticated;
revoke all on table public.junior_community_comments from public,anon,authenticated;
grant select,insert,update,delete on table public.junior_community_guardian_consents to service_role;
grant select,insert,update,delete on table public.junior_community_posts to service_role;
grant select,insert,update,delete on table public.junior_community_comments to service_role;

drop trigger if exists junior_community_posts_updated_at on public.junior_community_posts;
create trigger junior_community_posts_updated_at
before update on public.junior_community_posts
for each row execute function public.set_updated_at();

drop trigger if exists junior_community_comments_updated_at on public.junior_community_comments;
create trigger junior_community_comments_updated_at
before update on public.junior_community_comments
for each row execute function public.set_updated_at();

create index if not exists junior_community_posts_created_idx
  on public.junior_community_posts(created_at desc);
create index if not exists junior_community_comments_post_idx
  on public.junior_community_comments(post_id,created_at);
create index if not exists junior_community_guardian_active_idx
  on public.junior_community_guardian_consents(minor_user_id,guardian_user_id)
  where revoked_at is null;

create or replace function public.sinjira_my_age_band()
returns text
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $self_age$
  select public.sinjira_age_band(auth.uid());
$self_age$;
revoke all on function public.sinjira_my_age_band() from public,anon,authenticated;
grant execute on function public.sinjira_my_age_band() to anon,authenticated,service_role;

-- Helpers arbitraires strictement privés. Un enfant authentifié ne peut jamais
-- sonder l'âge, l'activation Junior ou l'acceptation des règles d'un autre compte par UUID.
create or replace function private.sinjira_is_junior(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public
as $junior$
  select p_user_id is not null and public.sinjira_age_band(p_user_id)='child';
$junior$;
revoke all on function private.sinjira_is_junior(uuid) from public,anon,authenticated;
grant execute on function private.sinjira_is_junior(uuid) to service_role;

create or replace function private.sinjira_junior_community_enabled(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $junior$
  select private.sinjira_is_junior(p_user_id)
    and exists(
      select 1
      from public.guardian_links g
      join public.junior_community_guardian_consents c
        on c.minor_user_id=g.minor_user_id
       and c.guardian_user_id=g.guardian_user_id
       and c.revoked_at is null
      where g.minor_user_id=p_user_id
        and g.status='verified'
        and g.revoked_at is null
        and public.sinjira_age_band(g.guardian_user_id)='adult'
    );
$junior$;

revoke all on function private.sinjira_junior_community_enabled(uuid)
from public,anon,authenticated;
grant execute on function private.sinjira_junior_community_enabled(uuid)
to service_role;


create or replace function private.has_accepted_junior_community_rules(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public
as $junior$
  select exists(
    select 1
    from public.community_rule_acceptances a
    where a.user_id=p_user_id
      and a.rules_version='sinjira-junior-rules-v1-2026-09-17'
  );
$junior$;
revoke all on function private.has_accepted_junior_community_rules(uuid) from public,anon,authenticated;
grant execute on function private.has_accepted_junior_community_rules(uuid) to service_role;

-- Les deux RPC publiques d'état sont self-only et n'acceptent aucun UUID utilisateur.
create or replace function public.sinjira_junior_community_enabled()
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $junior$ select private.sinjira_junior_community_enabled(auth.uid()); $junior$;
revoke all on function public.sinjira_junior_community_enabled() from public,anon;
grant execute on function public.sinjira_junior_community_enabled() to authenticated,service_role;

create or replace function public.has_accepted_junior_community_rules()
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $junior$ select private.has_accepted_junior_community_rules(auth.uid()); $junior$;
revoke all on function public.has_accepted_junior_community_rules() from public,anon;
grant execute on function public.has_accepted_junior_community_rules() to authenticated,service_role;

create or replace function private.sinjira_junior_alias(p_user_id uuid)
returns text
language sql
immutable
security definer
set search_path=pg_catalog
as $$
  select 'Explorateur-' || upper(substr(md5(p_user_id::text || ':sinjira-junior-v1'),1,8));
$$;
revoke all on function private.sinjira_junior_alias(uuid) from public,anon,authenticated;
grant execute on function private.sinjira_junior_alias(uuid) to service_role;

create or replace function private.sinjira_junior_content_code(p_body text)
returns text
language plpgsql
immutable
security definer
set search_path=pg_catalog
as $$
declare
  v text:=lower(coalesce(p_body,''));
begin
  if btrim(v)='' then return 'EMPTY'; end if;

  if v ~ '(https?://|www\.|discord|snapchat|instagram|tiktok|telegram|whatsapp|signal app|t\.me/|@[a-z0-9_]{3,}|[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}|[+]?([0-9][ ()\.\-]?){7,}[0-9])' then
    return 'EXTERNAL_CONTACT_FORBIDDEN';
  end if;

  if v ~ '(sexting|nude[s]?|photo[s]? nue[s]?|photo intime|contenu sexuel|porn|onlyfans|fansly|rencontre sexuelle|montre[- ]?moi.*corps)' then
    return 'SEXUAL_CONTENT_FORBIDDEN';
  end if;

  if v ~ '(viens chez moi|on se rencontre|rencontre[- ]?moi|donne.*adresse|mon adresse|où j.habite|ou j.habite|mon école|mon ecole|garde [cç]a secret|ne dis pas.*parent|ne le dis pas.*parent)' then
    return 'MEETUP_OR_SECRECY_FORBIDDEN';
  end if;

  if v ~ '(je vends|a vendre|à vendre|prix|tarif|paiement|paye[- ]?moi|paie[- ]?moi|carte cadeau|gift card|virement|crypto|abonnement|commande|livraison)' then
    return 'MONEY_OR_COMMERCE_FORBIDDEN';
  end if;

  return null;
end;
$$;
revoke all on function private.sinjira_junior_content_code(text) from public,anon,authenticated;
grant execute on function private.sinjira_junior_content_code(text) to service_role;

create or replace function private.sinjira_junior_require_access(p_require_rules boolean default true)
returns uuid
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid();
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not private.sinjira_is_junior(uid) then raise exception 'JUNIOR_COMMUNITY_11_12_ONLY'; end if;
  if not private.sinjira_junior_community_enabled(uid) then raise exception 'JUNIOR_GUARDIAN_CONSENT_REQUIRED'; end if;
  if coalesce(p_require_rules,true) and not private.has_accepted_junior_community_rules(uid) then
    raise exception 'JUNIOR_RULES_REQUIRED';
  end if;
  if public.social_is_suspended(uid) then raise exception 'SOCIAL_SUSPENDED'; end if;
  return uid;
end;
$$;
revoke all on function private.sinjira_junior_require_access(boolean) from public,anon,authenticated;
grant execute on function private.sinjira_junior_require_access(boolean) to service_role;

create or replace function private.sinjira_revoke_junior_consent_on_guardian_link()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_minor uuid;
  v_guardian uuid;
begin
  if tg_op='DELETE' then
    v_minor:=old.minor_user_id;
    v_guardian:=old.guardian_user_id;
  elsif coalesce(new.status,'')<>'verified' or new.revoked_at is not null then
    v_minor:=new.minor_user_id;
    v_guardian:=new.guardian_user_id;
  else
    return new;
  end if;

  update public.junior_community_guardian_consents
  set revoked_at=coalesce(revoked_at,now())
  where minor_user_id=v_minor
    and guardian_user_id=v_guardian
    and revoked_at is null;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$$;

revoke all on function private.sinjira_revoke_junior_consent_on_guardian_link()
from public,anon,authenticated;

drop trigger if exists sinjira_revoke_junior_consent_on_guardian_link
on public.guardian_links;

create trigger sinjira_revoke_junior_consent_on_guardian_link
after update of status,revoked_at or delete on public.guardian_links
for each row
execute function private.sinjira_revoke_junior_consent_on_guardian_link();


create or replace function public.guardian_set_junior_community(
  p_child_user_id uuid,
  p_enabled boolean
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $guardian_set$
declare
  uid uuid:=auth.uid();
  v_enabled boolean:=coalesce(p_enabled,false);
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_parent_can_supervise(uid,p_child_user_id) then
    raise exception 'GUARDIAN_ACCESS_REQUIRED';
  end if;
  if public.sinjira_age_band(p_child_user_id)<>'child' then
    raise exception 'JUNIOR_COMMUNITY_11_12_ONLY';
  end if;

  -- L'activation est un consentement parental qui augmente les capacités sociales.
  -- Le retrait reste disponible sans step-up pour être fail-safe.
  if v_enabled and coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  insert into public.junior_community_guardian_consents(
    minor_user_id,guardian_user_id,consented_at,revoked_at
  )
  values(
    p_child_user_id,uid,now(),case when v_enabled then null else now() end
  )
  on conflict(minor_user_id,guardian_user_id)
  do update set
    consented_at=case
      when v_enabled then now()
      else public.junior_community_guardian_consents.consented_at
    end,
    revoked_at=case when v_enabled then null else now() end;

  return jsonb_build_object('ok',true,'enabled',v_enabled);
end;
$guardian_set$;

revoke all on function public.guardian_set_junior_community(uuid,boolean)
from public,anon;
grant execute on function public.guardian_set_junior_community(uuid,boolean)
to authenticated;


create or replace function public.guardian_junior_community_children()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $guardian_children$
declare
  uid uuid:=auth.uid();
  result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(uid)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'minor_user_id',g.minor_user_id,
        'label',coalesce(nullif(p.pseudo,''),'Compte enfant'),
        'age_band',public.sinjira_age_band(g.minor_user_id),
        'enabled',c.revoked_at is null and c.minor_user_id is not null
      )
      order by p.pseudo nulls last
    ),
    '[]'::jsonb
  )
  into result
  from public.guardian_links g
  left join public.profiles p
    on p.user_id=g.minor_user_id
  left join public.junior_community_guardian_consents c
    on c.minor_user_id=g.minor_user_id
   and c.guardian_user_id=g.guardian_user_id
  where g.guardian_user_id=uid
    and g.status='verified'
    and g.revoked_at is null
    and public.sinjira_age_band(g.minor_user_id)='child';

  return result;
end;
$guardian_children$;

revoke all on function public.guardian_junior_community_children()
from public,anon;
grant execute on function public.guardian_junior_community_children()
to authenticated;


create or replace function public.junior_community_accept_rules()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare uid uuid;
begin
  uid:=private.sinjira_junior_require_access(false);
  insert into public.community_rule_acceptances(user_id,rules_version,accepted_at)
  values(uid,'sinjira-junior-rules-v1-2026-09-17',now())
  on conflict(user_id,rules_version) do update set accepted_at=excluded.accepted_at;
  return jsonb_build_object('ok',true,'rules_version','sinjira-junior-rules-v1-2026-09-17');
end;
$$;
revoke all on function public.junior_community_accept_rules() from public,anon;
grant execute on function public.junior_community_accept_rules() to authenticated;

create or replace function public.junior_community_feed(p_limit integer default 30)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid; result jsonb;
begin
  uid:=private.sinjira_junior_require_access(true);

  select coalesce(jsonb_agg(jsonb_build_object(
    'id',x.id,
    'author_alias',x.author_alias,
    'body',x.body,
    'created_at',x.created_at,
    'mine',x.mine,
    'comments',x.comments
  ) order by x.created_at desc),'[]'::jsonb)
  into result
  from (
    select
      p.id,
      private.sinjira_junior_alias(p.author_user_id) author_alias,
      p.body,
      p.created_at,
      p.author_user_id=uid mine,
      (
        select coalesce(jsonb_agg(jsonb_build_object(
          'id',c.id,
          'author_alias',private.sinjira_junior_alias(c.author_user_id),
          'body',c.body,
          'created_at',c.created_at,
          'mine',c.author_user_id=uid
        ) order by c.created_at),'[]'::jsonb)
        from public.junior_community_comments c
        where c.post_id=p.id
          and c.status='active'
          and public.moderation_content_visible('real','comment',c.id)
          and not public.social_is_blocked(uid,c.author_user_id)
      ) comments
    from public.junior_community_posts p
    where p.status='active'
      and public.moderation_content_visible('real','post',p.id)
      and private.sinjira_is_junior(p.author_user_id)
      and private.sinjira_junior_community_enabled(p.author_user_id)
      and not public.social_is_blocked(uid,p.author_user_id)
    order by p.created_at desc
    limit least(greatest(coalesce(p_limit,30),1),50)
  ) x;

  return result;
end;
$$;
revoke all on function public.junior_community_feed(integer) from public,anon;
grant execute on function public.junior_community_feed(integer) to authenticated;

create or replace function public.junior_community_create_post(p_body text)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid; body text:=btrim(coalesce(p_body,'')); code text; new_id uuid;
begin
  uid:=private.sinjira_junior_require_access(true);
  if char_length(body)<1 or char_length(body)>500 then raise exception 'JUNIOR_POST_LENGTH_INVALID'; end if;
  if (select count(*) from public.junior_community_posts p where p.author_user_id=uid and p.created_at>now()-interval '1 hour')>=5 then
    raise exception 'JUNIOR_POST_RATE_LIMIT';
  end if;
  code:=private.sinjira_junior_content_code(body);
  if code is not null then raise exception 'SINJIRA_JUNIOR_%',code using errcode='P0001'; end if;

  insert into public.junior_community_posts(author_user_id,body)
  values(uid,body) returning id into new_id;
  return jsonb_build_object('ok',true,'id',new_id);
end;
$$;
revoke all on function public.junior_community_create_post(text) from public,anon;
grant execute on function public.junior_community_create_post(text) to authenticated;

create or replace function public.junior_community_create_comment(p_post_id uuid,p_body text)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid; body text:=btrim(coalesce(p_body,'')); code text; new_id uuid; author_id uuid;
begin
  uid:=private.sinjira_junior_require_access(true);
  if char_length(body)<1 or char_length(body)>300 then raise exception 'JUNIOR_COMMENT_LENGTH_INVALID'; end if;
  if (select count(*) from public.junior_community_comments c where c.author_user_id=uid and c.created_at>now()-interval '1 hour')>=30 then
    raise exception 'JUNIOR_COMMENT_RATE_LIMIT';
  end if;
  select p.author_user_id into author_id
  from public.junior_community_posts p
  where p.id=p_post_id and p.status='active';
  if author_id is null or not private.sinjira_is_junior(author_id) or not private.sinjira_junior_community_enabled(author_id) then
    raise exception 'JUNIOR_POST_UNAVAILABLE';
  end if;
  if public.social_is_blocked(uid,author_id) then raise exception 'JUNIOR_POST_UNAVAILABLE'; end if;

  code:=private.sinjira_junior_content_code(body);
  if code is not null then raise exception 'SINJIRA_JUNIOR_%',code using errcode='P0001'; end if;

  insert into public.junior_community_comments(post_id,author_user_id,body)
  values(p_post_id,uid,body) returning id into new_id;
  return jsonb_build_object('ok',true,'id',new_id);
end;
$$;
revoke all on function public.junior_community_create_comment(uuid,text) from public,anon;
grant execute on function public.junior_community_create_comment(uuid,text) to authenticated;

create or replace function public.junior_community_delete_post(p_post_id uuid)
returns boolean
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid;
begin
  uid:=private.sinjira_junior_require_access(true);
  update public.junior_community_posts
  set status='removed'
  where id=p_post_id and author_user_id=uid and status='active';
  return found;
end;
$$;
revoke all on function public.junior_community_delete_post(uuid) from public,anon;
grant execute on function public.junior_community_delete_post(uuid) to authenticated;

create or replace function public.junior_community_delete_comment(p_comment_id uuid)
returns boolean
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid;
begin
  uid:=private.sinjira_junior_require_access(true);
  update public.junior_community_comments
  set status='removed'
  where id=p_comment_id and author_user_id=uid and status='active';
  return found;
end;
$$;
revoke all on function public.junior_community_delete_comment(uuid) from public,anon;
grant execute on function public.junior_community_delete_comment(uuid) to authenticated;

create or replace function public.junior_community_report_content(
  p_target_type text,
  p_target_id uuid,
  p_reason text default 'other',
  p_details text default null,
  p_block boolean default true
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  uid uuid:=auth.uid();
  author_id uuid;
  body text;
  created_at_value timestamptz;
  report_id uuid;
  details text:=nullif(btrim(coalesce(p_details,'')),'');
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not private.sinjira_is_junior(uid) then raise exception 'JUNIOR_COMMUNITY_11_12_ONLY'; end if;
  if not private.sinjira_junior_community_enabled(uid) then raise exception 'JUNIOR_GUARDIAN_CONSENT_REQUIRED'; end if;
  if coalesce(p_target_type,'') not in('post','comment') then raise exception 'JUNIOR_REPORT_TARGET_INVALID'; end if;
  if not private.sinjira_report_reason_allowed(coalesce(p_reason,'other')) then raise exception 'SOCIAL_REPORT_REASON_INVALID'; end if;
  if details is not null and char_length(details)>1200 then raise exception 'SOCIAL_REPORT_DETAILS_TOO_LONG'; end if;
  if (select count(*) from public.social_reports r where r.reporter_user_id=uid and r.created_at>now()-interval '1 hour')>=10 then
    raise exception 'SOCIAL_REPORT_RATE_LIMIT';
  end if;

  if p_target_type='post' then
    select p.author_user_id,p.body,p.created_at into author_id,body,created_at_value
    from public.junior_community_posts p where p.id=p_target_id and p.status='active';
  else
    select c.author_user_id,c.body,c.created_at into author_id,body,created_at_value
    from public.junior_community_comments c where c.id=p_target_id and c.status='active';
  end if;

  if author_id is null or author_id=uid or not private.sinjira_is_junior(author_id) then
    raise exception 'JUNIOR_REPORT_TARGET_UNAVAILABLE';
  end if;

  insert into public.social_reports(reporter_user_id,network,target_type,target_id,reason,snapshot)
  values(uid,'real',p_target_type,p_target_id,coalesce(p_reason,'other'),jsonb_strip_nulls(jsonb_build_object(
    'source','junior_community',
    'body',left(coalesce(body,''),500),
    'details',details,
    'content_created_at',created_at_value,
    'author_alias',private.sinjira_junior_alias(author_id),
    'identity_data_included',false,
    'priority_safety',true
  ))) returning id into report_id;

  if coalesce(p_block,true) then
    insert into public.social_blocks(blocker_user_id,blocked_user_id)
    values(uid,author_id)
    on conflict(blocker_user_id,blocked_user_id) do nothing;
  end if;

  return jsonb_build_object('ok',true,'report_id',report_id,'blocked',coalesce(p_block,true));
end;
$$;
revoke all on function public.junior_community_report_content(text,uuid,text,text,boolean) from public,anon;
grant execute on function public.junior_community_report_content(text,uuid,text,text,boolean) to authenticated;

create or replace function public.junior_guardian_summary(p_child_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $guardian_summary$
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
$guardian_summary$;

revoke all on function public.junior_guardian_summary(uuid)
from public,anon;
grant execute on function public.junior_guardian_summary(uuid)
to authenticated;


comment on function public.sinjira_junior_community_enabled() is
'Communauté Junior activée uniquement pour un compte child 11–12 avec lien tuteur vérifié et consentement Junior non révoqué.';
comment on function public.junior_community_feed(integer) is
'Fil Junior pseudonymisé: aucun UUID auteur, nom réel, avatar, courriel ou coordonnée n est renvoyé au client.';
comment on function public.junior_guardian_summary(uuid) is
'Résumé de supervision sans contenu: protège sans donner au parent un accès de lecture aux publications ou commentaires.';

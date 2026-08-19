create table if not exists public.dating_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  serious_intent_confirmed boolean not null default false,
  single_confirmed_at timestamptz,
  gender_identity text check (gender_identity is null or gender_identity in ('woman','man','nonbinary','other','prefer_not_say')),
  region text not null default '' check (char_length(region) <= 120),
  intro text not null default '' check (char_length(intro) <= 1200),
  values_tags text[] not null default '{}',
  interests_tags text[] not null default '{}',
  lifestyle_tags text[] not null default '{}',
  communication_tags text[] not null default '{}',
  goals_tags text[] not null default '{}',
  registry_traits text[] not null default '{}',
  use_registry_answers boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (cardinality(values_tags) <= 20),
  check (cardinality(interests_tags) <= 20),
  check (cardinality(lifestyle_tags) <= 20),
  check (cardinality(communication_tags) <= 20),
  check (cardinality(goals_tags) <= 20),
  check (cardinality(registry_traits) <= 20)
);

create table if not exists public.dating_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  min_age smallint not null default 18 check (min_age between 18 and 99),
  max_age smallint not null default 99 check (max_age between 18 and 99 and max_age >= min_age),
  seeking_genders text[] not null default '{}',
  wanted_values text[] not null default '{}',
  wanted_interests text[] not null default '{}',
  wanted_lifestyle text[] not null default '{}',
  wanted_communication text[] not null default '{}',
  wanted_goals text[] not null default '{}',
  partner_description text not null default '' check (char_length(partner_description) <= 1600),
  dealbreakers text not null default '' check (char_length(dealbreakers) <= 1200),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (seeking_genders <@ array['woman','man','nonbinary','other','prefer_not_say']::text[]),
  check (cardinality(wanted_values) <= 20),
  check (cardinality(wanted_interests) <= 20),
  check (cardinality(wanted_lifestyle) <= 20),
  check (cardinality(wanted_communication) <= 20),
  check (cardinality(wanted_goals) <= 20)
);

create table if not exists public.dating_connections (
  id uuid primary key default gen_random_uuid(),
  profile_a_id uuid not null references public.dating_profiles(id) on delete cascade,
  profile_b_id uuid not null references public.dating_profiles(id) on delete cascade,
  requested_by_profile_id uuid not null references public.dating_profiles(id) on delete cascade,
  status text not null default 'pending' check (status in ('pending','accepted','declined','closed')),
  a_photo_consent boolean not null default false,
  b_photo_consent boolean not null default false,
  created_at timestamptz not null default now(),
  accepted_at timestamptz,
  closed_at timestamptz,
  check (profile_a_id <> profile_b_id),
  check (requested_by_profile_id = profile_a_id or requested_by_profile_id = profile_b_id),
  unique(profile_a_id, profile_b_id)
);

create table if not exists public.dating_messages (
  id uuid primary key default gen_random_uuid(),
  connection_id uuid not null references public.dating_connections(id) on delete cascade,
  sender_profile_id uuid not null references public.dating_profiles(id) on delete cascade,
  body text not null check (char_length(btrim(body)) between 1 and 2000),
  created_at timestamptz not null default now()
);

alter table public.dating_profiles enable row level security;
alter table public.dating_preferences enable row level security;
alter table public.dating_connections enable row level security;
alter table public.dating_messages enable row level security;

revoke all on public.dating_profiles, public.dating_preferences, public.dating_connections, public.dating_messages from public, anon, authenticated;
grant select,insert,update,delete on public.dating_profiles to authenticated;
grant select,insert,update,delete on public.dating_preferences to authenticated;
grant select,insert,update,delete on public.dating_profiles, public.dating_preferences, public.dating_connections, public.dating_messages to service_role;

drop policy if exists dating_profiles_self on public.dating_profiles;
create policy dating_profiles_self on public.dating_profiles for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists dating_preferences_self on public.dating_preferences;
create policy dating_preferences_self on public.dating_preferences for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

create index if not exists dating_profiles_enabled_idx on public.dating_profiles(enabled) where enabled = true;
create index if not exists dating_connections_a_idx on public.dating_connections(profile_a_id, created_at desc);
create index if not exists dating_connections_b_idx on public.dating_connections(profile_b_id, created_at desc);
create index if not exists dating_messages_connection_idx on public.dating_messages(connection_id, created_at);

create or replace function private.dating_touch_updated_at() returns trigger language plpgsql set search_path=pg_catalog,public as $$ begin new.updated_at=now(); return new; end; $$;
drop trigger if exists dating_profiles_updated_at on public.dating_profiles;
create trigger dating_profiles_updated_at before update on public.dating_profiles for each row execute function private.dating_touch_updated_at();
drop trigger if exists dating_preferences_updated_at on public.dating_preferences;
create trigger dating_preferences_updated_at before update on public.dating_preferences for each row execute function private.dating_touch_updated_at();

create or replace function private.dating_age(p_user_id uuid) returns integer language sql stable security definer set search_path=pg_catalog,public as $$
  select case when s.date_of_birth is null then null else extract(year from age(current_date,s.date_of_birth))::int end from public.account_safety_profiles s where s.user_id=p_user_id;
$$;

create or replace function private.dating_overlap_ratio(a text[], b text[]) returns numeric language sql immutable set search_path=pg_catalog as $$
with aa as (select distinct lower(btrim(x)) x from unnest(coalesce(a,'{}'::text[])) x where btrim(x)<>''), bb as (select distinct lower(btrim(x)) x from unnest(coalesce(b,'{}'::text[])) x where btrim(x)<>''), u as (select x from aa union select x from bb), i as (select x from aa intersect select x from bb)
select case when (select count(*) from u)=0 then 0 else (select count(*)::numeric from i)/(select count(*) from u) end;
$$;

create or replace function private.dating_dimension_fit(me_tags text[], my_wanted text[], other_tags text[], other_wanted text[]) returns numeric language sql immutable set search_path=pg_catalog,private as $$
select (private.dating_overlap_ratio(other_tags,case when cardinality(coalesce(my_wanted,'{}'::text[]))>0 then my_wanted else me_tags end)+private.dating_overlap_ratio(me_tags,case when cardinality(coalesce(other_wanted,'{}'::text[]))>0 then other_wanted else other_tags end))/2;
$$;

create or replace function private.dating_is_eligible(p_user_id uuid) returns boolean language sql stable security definer set search_path=pg_catalog,public,private as $$
select coalesce(private.dating_age(p_user_id) >= 18 and s.legacy_status='active' and s.relationship_data_opt_in is true and s.relationship_status='single' and p.enabled is true and p.serious_intent_confirmed is true and p.single_confirmed_at is not null and p.single_confirmed_at >= now()-interval '90 days' and p.gender_identity is not null and btrim(p.intro)<>'' and exists(select 1 from public.dating_preferences d where d.user_id=p_user_id and cardinality(d.seeking_genders)>0),false)
from public.account_safety_profiles s join public.dating_profiles p on p.user_id=s.user_id where s.user_id=p_user_id;
$$;

revoke all on function private.dating_age(uuid), private.dating_overlap_ratio(text[],text[]), private.dating_dimension_fit(text[],text[],text[],text[]), private.dating_is_eligible(uuid), private.dating_touch_updated_at() from public,anon,authenticated;
grant execute on function private.dating_age(uuid), private.dating_overlap_ratio(text[],text[]), private.dating_dimension_fit(text[],text[],text[],text[]), private.dating_is_eligible(uuid), private.dating_touch_updated_at() to service_role;

create or replace function public.dating_confirm_single_and_serious() returns jsonb language plpgsql security definer set search_path=pg_catalog,public,private as $$
declare v_user uuid:=auth.uid(); v_age int;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
 v_age:=private.dating_age(v_user); if v_age is null or v_age<18 then raise exception 'ADULTS_ONLY'; end if;
 if not exists(select 1 from public.dating_profiles p join public.dating_preferences d on d.user_id=p.user_id where p.user_id=v_user and p.gender_identity is not null and btrim(p.intro)<>'' and cardinality(d.seeking_genders)>0) then raise exception 'PROFILE_INCOMPLETE'; end if;
 update public.account_safety_profiles set relationship_data_opt_in=true,relationship_status='single',relationship_status_updated_at=now(),updated_at=now() where user_id=v_user;
 update public.dating_profiles set enabled=true,serious_intent_confirmed=true,single_confirmed_at=now(),updated_at=now() where user_id=v_user;
 return jsonb_build_object('ok',true,'eligible',private.dating_is_eligible(v_user),'reconfirm_by',now()+interval '90 days');
end; $$;

create or replace function public.dating_pause_profile(p_relationship_status text default null) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare v_user uuid:=auth.uid(); v_profile uuid;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
 select id into v_profile from public.dating_profiles where user_id=v_user; update public.dating_profiles set enabled=false,updated_at=now() where user_id=v_user;
 if p_relationship_status is not null then
  if p_relationship_status not in ('partnered','not_available','prefer_not_say') then raise exception 'INVALID_STATUS'; end if;
  update public.account_safety_profiles set relationship_data_opt_in=true,relationship_status=p_relationship_status,relationship_status_updated_at=now(),updated_at=now() where user_id=v_user;
  update public.dating_connections set status='closed',closed_at=now(),a_photo_consent=false,b_photo_consent=false where status in ('pending','accepted') and v_profile in(profile_a_id,profile_b_id);
 end if;
 return jsonb_build_object('ok',true,'eligible',false);
end; $$;

create or replace function public.dating_import_registry_traits() returns text[] language plpgsql security definer set search_path=pg_catalog,public as $$
declare v_user uuid:=auth.uid(); v_answers jsonb; v_traits text[]:='{}';
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
 if not exists(select 1 from public.dating_profiles where user_id=v_user and use_registry_answers=true) then raise exception 'REGISTRY_CONSENT_REQUIRED'; end if;
 select a.answers into v_answers from public.sinjira_character_applications a where a.user_id=v_user and a.answers is not null and a.source_purged_at is null order by coalesce(a.submitted_at,a.updated_at,a.created_at) desc limit 1;
 if v_answers is null then raise exception 'NO_REGISTRY_SOURCE'; end if;
 select coalesce(array_agg(distinct val),'{}'::text[]) into v_traits from (select left(btrim(v_answers->>k),80) val from unnest(array['core_value','conflict_style','decision_style','sociability','trust_style','natural_role']) k where nullif(btrim(v_answers->>k),'') is not null) q;
 update public.dating_profiles set registry_traits=v_traits,updated_at=now() where user_id=v_user; return v_traits;
end; $$;

create or replace function public.dating_self_status() returns jsonb language plpgsql stable security definer set search_path=pg_catalog,public,private as $$
declare v_user uuid:=auth.uid(); v_age int; v_status text; v_enabled bool; v_confirm timestamptz;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
 v_age:=private.dating_age(v_user); select s.relationship_status,p.enabled,p.single_confirmed_at into v_status,v_enabled,v_confirm from public.account_safety_profiles s left join public.dating_profiles p on p.user_id=s.user_id where s.user_id=v_user;
 return jsonb_build_object('adult',coalesce(v_age>=18,false),'age',v_age,'relationship_status',coalesce(v_status,'not_set'),'enabled',coalesce(v_enabled,false),'single_confirmed_at',v_confirm,'eligible',private.dating_is_eligible(v_user),'messages_each_before_reveal',10);
end; $$;

create or replace function public.dating_compatibility_candidates(p_limit integer default 8)
returns table(profile_id uuid,blind_alias text,age_band text,region text,intro text,compatibility_score integer,reasons text[])
language sql stable security definer set search_path=pg_catalog,public,private as $$
with me as (
 select p.id me_profile_id,p.user_id me_user_id,p.gender_identity me_gender,p.values_tags me_values,p.interests_tags me_interests,p.lifestyle_tags me_lifestyle,p.communication_tags me_communication,p.goals_tags me_goals,p.registry_traits me_registry,p.use_registry_answers me_use_registry,d.min_age me_min_age,d.max_age me_max_age,d.seeking_genders me_seeking,d.wanted_values me_wanted_values,d.wanted_interests me_wanted_interests,d.wanted_lifestyle me_wanted_lifestyle,d.wanted_communication me_wanted_communication,d.wanted_goals me_wanted_goals,private.dating_age(p.user_id) me_age
 from public.dating_profiles p join public.dating_preferences d on d.user_id=p.user_id where p.user_id=auth.uid() and private.dating_is_eligible(p.user_id)
), raw as (
 select c.id candidate_id,c.user_id candidate_user_id,c.region candidate_region,c.intro candidate_intro,c.use_registry_answers candidate_use_registry,c.registry_traits candidate_registry,private.dating_age(c.user_id) other_age,private.dating_dimension_fit(m.me_values,m.me_wanted_values,c.values_tags,cp.wanted_values) value_fit,private.dating_dimension_fit(m.me_goals,m.me_wanted_goals,c.goals_tags,cp.wanted_goals) goal_fit,private.dating_dimension_fit(m.me_communication,m.me_wanted_communication,c.communication_tags,cp.wanted_communication) comm_fit,private.dating_dimension_fit(m.me_lifestyle,m.me_wanted_lifestyle,c.lifestyle_tags,cp.wanted_lifestyle) life_fit,private.dating_dimension_fit(m.me_interests,m.me_wanted_interests,c.interests_tags,cp.wanted_interests) interest_fit,private.dating_overlap_ratio(m.me_registry,c.registry_traits) registry_fit,(m.me_use_registry and c.use_registry_answers) registry_on
 from me m join public.dating_profiles c on c.user_id<>m.me_user_id join public.dating_preferences cp on cp.user_id=c.user_id
 where private.dating_is_eligible(c.user_id) and c.gender_identity=any(m.me_seeking) and m.me_gender=any(cp.seeking_genders) and private.dating_age(c.user_id) between m.me_min_age and m.me_max_age and m.me_age between cp.min_age and cp.max_age
 and not exists(select 1 from public.social_blocks b where (b.blocker_user_id=m.me_user_id and b.blocked_user_id=c.user_id) or (b.blocker_user_id=c.user_id and b.blocked_user_id=m.me_user_id))
 and not exists(select 1 from public.dating_connections x where (x.profile_a_id=m.me_profile_id and x.profile_b_id=c.id) or (x.profile_a_id=c.id and x.profile_b_id=m.me_profile_id))
), scored as (select r.*,round(100*(.25*r.value_fit+.25*r.goal_fit+.20*r.comm_fit+.15*r.life_fit+(case when r.registry_on then .10*r.interest_fit+.05*r.registry_fit else .15*r.interest_fit end)))::int score from raw r)
select s.candidate_id,'Profil '||upper(substr(replace(s.candidate_id::text,'-',''),1,6)),case when s.other_age between 18 and 24 then '18–24' when s.other_age between 25 and 34 then '25–34' when s.other_age between 35 and 44 then '35–44' when s.other_age between 45 and 54 then '45–54' when s.other_age between 55 and 64 then '55–64' else '65+' end,s.candidate_region,s.candidate_intro,s.score,array_remove(array[case when s.value_fit>=.35 then 'Valeurs compatibles' end,case when s.goal_fit>=.35 then 'Projets de relation convergents' end,case when s.comm_fit>=.35 then 'Communication compatible' end,case when s.life_fit>=.35 then 'Rythmes de vie compatibles' end,case when s.interest_fit>=.35 then 'Intérêts partagés' end,case when s.registry_on and s.registry_fit>=.35 then 'Repères du Registre compatibles' end],null)::text[]
from scored s where s.score>=35 order by s.score desc,s.candidate_id limit greatest(1,least(coalesce(p_limit,8),20));
$$;

create or replace function public.dating_request_conversation(p_candidate_profile_id uuid) returns uuid language plpgsql security definer set search_path=pg_catalog,public,private as $$
declare v_user uuid:=auth.uid(); v_me uuid; v_id uuid; v_a uuid; v_b uuid; v_recipient uuid;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if; select id into v_me from public.dating_profiles where user_id=v_user;
 if v_me is null or not private.dating_is_eligible(v_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;
 if not exists(select 1 from public.dating_compatibility_candidates(20) dc where dc.profile_id=p_candidate_profile_id) then raise exception 'CANDIDATE_NOT_AVAILABLE'; end if;
 if v_me < p_candidate_profile_id then v_a:=v_me;v_b:=p_candidate_profile_id;else v_a:=p_candidate_profile_id;v_b:=v_me;end if;
 insert into public.dating_connections(profile_a_id,profile_b_id,requested_by_profile_id) values(v_a,v_b,v_me) returning id into v_id; select user_id into v_recipient from public.dating_profiles where id=p_candidate_profile_id;
 insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path) values(v_recipient,'dating','Nouvelle proposition de discussion','Une personne compatible souhaite ouvrir une discussion anonyme avec vous.','dating_connection',v_id,'/compte/rencontres.html'); return v_id;
end; $$;

create or replace function public.dating_connections_overview()
returns table(connection_id uuid,status text,direction text,blind_alias text,intro text,region text,my_message_count integer,their_message_count integer,photo_unlock_available boolean,my_photo_consent boolean,their_photo_consent boolean,identity_revealed boolean,revealed_name text,revealed_avatar_path text,created_at timestamptz)
language sql stable security definer set search_path=pg_catalog,public,private as $$
with me as (select p.id,p.user_id from public.dating_profiles p where p.user_id=auth.uid()), c as (select x.*,m.id me_id,case when x.profile_a_id=m.id then x.profile_b_id else x.profile_a_id end other_id,case when x.requested_by_profile_id=m.id then 'outgoing' else 'incoming' end dir,m.user_id me_user_id from public.dating_connections x join me m on m.id in (x.profile_a_id,x.profile_b_id)), counts as (select c.*,(select count(*)::int from public.dating_messages dm where dm.connection_id=c.id and dm.sender_profile_id=c.me_id) my_count,(select count(*)::int from public.dating_messages dm where dm.connection_id=c.id and dm.sender_profile_id=c.other_id) their_count from c), ready as (select counts.*,case when profile_a_id=me_id then a_photo_consent else b_photo_consent end my_consent,case when profile_a_id=me_id then b_photo_consent else a_photo_consent end their_consent from counts)
select r.id,r.status,r.dir,'Profil '||upper(substr(replace(o.id::text,'-',''),1,6)),o.intro,o.region,r.my_count,r.their_count,(r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10),r.my_consent,r.their_consent,(r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10 and r.my_consent and r.their_consent),case when r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10 and r.my_consent and r.their_consent then coalesce(sp.pseudo,sp.display_name,'Membre SINJIRA™') end,case when r.status='accepted' and private.dating_is_eligible(r.me_user_id) and private.dating_is_eligible(o.user_id) and r.my_count>=10 and r.their_count>=10 and r.my_consent and r.their_consent then sp.avatar_path end,r.created_at
from ready r join public.dating_profiles o on o.id=r.other_id left join public.social_profiles sp on sp.user_id=o.user_id order by r.created_at desc;
$$;

create or replace function public.dating_respond_connection(p_connection_id uuid,p_accept boolean) returns jsonb language plpgsql security definer set search_path=pg_catalog,public,private as $$
declare v_user uuid:=auth.uid(); v_me uuid; v_sender_user uuid;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if; select id into v_me from public.dating_profiles where user_id=v_user; if not private.dating_is_eligible(v_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;
 if not exists(select 1 from public.dating_connections c where c.id=p_connection_id and c.status='pending' and c.requested_by_profile_id<>v_me and v_me in(c.profile_a_id,c.profile_b_id)) then raise exception 'REQUEST_NOT_AVAILABLE'; end if;
 update public.dating_connections set status=case when p_accept then 'accepted' else 'declined' end,accepted_at=case when p_accept then now() else null end,closed_at=case when p_accept then null else now() end where id=p_connection_id;
 select p.user_id into v_sender_user from public.dating_connections c join public.dating_profiles p on p.id=c.requested_by_profile_id where c.id=p_connection_id;
 insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path) values(v_sender_user,'dating',case when p_accept then 'Discussion de compatibilité acceptée' else 'Proposition de discussion terminée' end,case when p_accept then 'Votre discussion anonyme peut commencer.' else 'Cette proposition de discussion ne se poursuivra pas.' end,'dating_connection',p_connection_id,'/compte/rencontres.html'); return jsonb_build_object('ok',true,'status',case when p_accept then 'accepted' else 'declined' end);
end; $$;

create or replace function public.dating_send_message(p_connection_id uuid,p_body text) returns uuid language plpgsql security definer set search_path=pg_catalog,public,private as $$
declare v_user uuid:=auth.uid(); v_me uuid; v_other uuid; v_other_user uuid; v_id uuid;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if; if char_length(btrim(coalesce(p_body,''))) not between 1 and 2000 then raise exception 'INVALID_MESSAGE'; end if; select id into v_me from public.dating_profiles where user_id=v_user;
 select case when c.profile_a_id=v_me then c.profile_b_id else c.profile_a_id end into v_other from public.dating_connections c where c.id=p_connection_id and c.status='accepted' and v_me in(c.profile_a_id,c.profile_b_id); if v_other is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;
 select user_id into v_other_user from public.dating_profiles where id=v_other; if not private.dating_is_eligible(v_user) or not private.dating_is_eligible(v_other_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;
 insert into public.dating_messages(connection_id,sender_profile_id,body) values(p_connection_id,v_me,btrim(p_body)) returning id into v_id; return v_id;
end; $$;

create or replace function public.dating_conversation(p_connection_id uuid)
returns table(message_id uuid,sender_is_me boolean,body text,created_at timestamptz) language sql stable security definer set search_path=pg_catalog,public as $$
with me as (select p.id from public.dating_profiles p where p.user_id=auth.uid()), allowed as (select c.id,m.id me_id from public.dating_connections c join me m on m.id in(c.profile_a_id,c.profile_b_id) where c.id=p_connection_id and c.status='accepted') select dm.id,dm.sender_profile_id=a.me_id,dm.body,dm.created_at from public.dating_messages dm join allowed a on a.id=dm.connection_id order by dm.created_at asc limit 500;
$$;

create or replace function public.dating_set_photo_consent(p_connection_id uuid,p_consent boolean) returns jsonb language plpgsql security definer set search_path=pg_catalog,public as $$
declare v_user uuid:=auth.uid(); v_me uuid; v_a uuid; v_b uuid; v_my int; v_their int;
begin
 if v_user is null then raise exception 'AUTH_REQUIRED'; end if; select id into v_me from public.dating_profiles where user_id=v_user; select c.profile_a_id,c.profile_b_id into v_a,v_b from public.dating_connections c where c.id=p_connection_id and c.status='accepted' and v_me in(c.profile_a_id,c.profile_b_id); if v_a is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;
 select count(*)::int into v_my from public.dating_messages dm where dm.connection_id=p_connection_id and dm.sender_profile_id=v_me; select count(*)::int into v_their from public.dating_messages dm where dm.connection_id=p_connection_id and dm.sender_profile_id<>v_me; if p_consent and (v_my<10 or v_their<10) then raise exception 'PHOTO_REVEAL_TOO_EARLY'; end if;
 if v_me=v_a then update public.dating_connections set a_photo_consent=p_consent where id=p_connection_id; else update public.dating_connections set b_photo_consent=p_consent where id=p_connection_id; end if; return jsonb_build_object('ok',true,'my_messages',v_my,'their_messages',v_their,'threshold',10);
end; $$;

revoke all on function public.dating_confirm_single_and_serious(), public.dating_pause_profile(text), public.dating_import_registry_traits(), public.dating_self_status(), public.dating_compatibility_candidates(integer), public.dating_request_conversation(uuid), public.dating_connections_overview(), public.dating_respond_connection(uuid,boolean), public.dating_send_message(uuid,text), public.dating_conversation(uuid), public.dating_set_photo_consent(uuid,boolean) from public,anon;
grant execute on function public.dating_confirm_single_and_serious(), public.dating_pause_profile(text), public.dating_import_registry_traits(), public.dating_self_status(), public.dating_compatibility_candidates(integer), public.dating_request_conversation(uuid), public.dating_connections_overview(), public.dating_respond_connection(uuid,boolean), public.dating_send_message(uuid,text), public.dating_conversation(uuid), public.dating_set_photo_consent(uuid,boolean) to authenticated;

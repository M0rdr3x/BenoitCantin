-- SINJIRA™ V24.4.74 — Rencontres privées par compatibilité.
-- 18+ seulement, participation volontaire, aucun catalogue public, aucune photo dans la découverte.
-- Le moteur V1 est déterministe, explicable et sans service IA externe/payant.

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;

do $$ begin
  if to_regprocedure('public.set_updated_at()') is null then
    raise exception 'DEPENDENCY_MISSING: public.set_updated_at()';
  end if;
  if to_regprocedure('public.sinjira_age_band(uuid)') is null then
    raise exception 'DEPENDENCY_MISSING: public.sinjira_age_band(uuid)';
  end if;
  if to_regprocedure('public.social_is_blocked(uuid,uuid)') is null then
    raise exception 'DEPENDENCY_MISSING: public.social_is_blocked(uuid,uuid)';
  end if;
end $$;

create table if not exists public.dating_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  active boolean not null default false,
  relationship_goal text not null default 'serious' check (relationship_goal = 'serious'),
  preferred_age_min integer not null default 18 check (preferred_age_min between 18 and 99),
  preferred_age_max integer not null default 80 check (preferred_age_max between 18 and 99),
  preferred_partner_genders text[] not null default '{}',
  values_sought text[] not null default '{}',
  interests text[] not null default '{}',
  communication_style text not null default 'balanced' check (communication_style in ('frequent','balanced','independent')),
  life_rhythm text not null default 'balanced' check (life_rhythm in ('calm','balanced','active')),
  social_energy text not null default 'balanced' check (social_energy in ('reserved','balanced','social')),
  distance_scope text not null default 'same_region' check (distance_scope in ('same_region','same_country','open_distance')),
  questionnaire_opt_in boolean not null default false,
  questionnaire_traits jsonb not null default '{}'::jsonb,
  serious_intent_confirmed boolean not null default false,
  consent_version text,
  consented_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (preferred_age_max >= preferred_age_min),
  check (cardinality(preferred_partner_genders) <= 5),
  check (cardinality(values_sought) <= 8),
  check (cardinality(interests) <= 12)
);

create table if not exists public.dating_introductions (
  id uuid primary key default gen_random_uuid(),
  user_a uuid not null references auth.users(id) on delete cascade,
  user_b uuid not null references auth.users(id) on delete cascade,
  requested_by uuid not null references auth.users(id) on delete cascade,
  status text not null default 'requested' check (status in ('requested','accepted','declined','closed')),
  accepted_at timestamptz,
  closed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (user_a <> user_b),
  check (user_a::text < user_b::text),
  check (requested_by = user_a or requested_by = user_b),
  unique (user_a,user_b)
);

create table if not exists public.dating_photo_reveal_consents (
  introduction_id uuid not null references public.dating_introductions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  consented_at timestamptz not null default now(),
  primary key (introduction_id,user_id)
);

create index if not exists dating_profiles_active_idx on public.dating_profiles(active,updated_at desc) where active=true;
create index if not exists dating_introductions_user_a_idx on public.dating_introductions(user_a,updated_at desc);
create index if not exists dating_introductions_user_b_idx on public.dating_introductions(user_b,updated_at desc);

drop trigger if exists dating_profiles_updated_at on public.dating_profiles;
create trigger dating_profiles_updated_at before update on public.dating_profiles
for each row execute function public.set_updated_at();
drop trigger if exists dating_introductions_updated_at on public.dating_introductions;
create trigger dating_introductions_updated_at before update on public.dating_introductions
for each row execute function public.set_updated_at();

alter table public.dating_profiles enable row level security;
alter table public.dating_introductions enable row level security;
alter table public.dating_photo_reveal_consents enable row level security;

revoke all on table public.dating_profiles from public,anon,authenticated;
revoke all on table public.dating_introductions from public,anon,authenticated;
revoke all on table public.dating_photo_reveal_consents from public,anon,authenticated;
grant select on table public.dating_profiles to authenticated;
grant select on table public.dating_introductions to authenticated;
grant all on table public.dating_profiles to service_role;
grant all on table public.dating_introductions to service_role;
grant all on table public.dating_photo_reveal_consents to service_role;

drop policy if exists dating_profiles_self_select on public.dating_profiles;
create policy dating_profiles_self_select on public.dating_profiles
for select to authenticated using ((select auth.uid())=user_id);

drop policy if exists dating_introductions_participants_select on public.dating_introductions;
create policy dating_introductions_participants_select on public.dating_introductions
for select to authenticated using ((select auth.uid()) in (user_a,user_b));

create or replace function private.dating_allowed_relationship_status(p_status text)
returns boolean
language sql immutable
set search_path=pg_catalog
as $$
  select coalesce(p_status,'') = any(array['Célibataire','Divorcé(e)','Veuf / veuve']::text[]);
$$;
revoke all on function private.dating_allowed_relationship_status(text) from public,anon,authenticated;

create or replace function private.dating_json_text_array(p_value jsonb)
returns text[]
language sql immutable
set search_path=pg_catalog
as $$
  select case when jsonb_typeof(p_value)='array'
    then coalesce(array(select jsonb_array_elements_text(p_value)),'{}'::text[])
    else '{}'::text[] end;
$$;
revoke all on function private.dating_json_text_array(jsonb) from public,anon,authenticated;

create or replace function private.dating_overlap_count(p_a text[],p_b text[])
returns integer
language sql immutable
set search_path=pg_catalog
as $$
  select count(*)::integer from (
    select distinct lower(btrim(x)) v from unnest(coalesce(p_a,'{}'::text[])) x where btrim(x)<>''
    intersect
    select distinct lower(btrim(y)) v from unnest(coalesce(p_b,'{}'::text[])) y where btrim(y)<>''
  ) s;
$$;
revoke all on function private.dating_overlap_count(text[],text[]) from public,anon,authenticated;

create or replace function private.dating_latest_payload(p_user_id uuid)
returns jsonb
language sql stable security definer
set search_path=pg_catalog,public
as $$
  select coalesce((
    select s.source_payload
    from public.character_submissions s
    where s.user_id=p_user_id and s.source_payload is not null and s.source_purged_at is null
    order by s.created_at desc limit 1
  ),'{}'::jsonb);
$$;
revoke all on function private.dating_latest_payload(uuid) from public,anon,authenticated;

create or replace function private.dating_safe_questionnaire_traits(p_user_id uuid)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare p jsonb:=private.dating_latest_payload(p_user_id); out jsonb:='{}'::jsonb; k text;
begin
  if jsonb_typeof(p->'values')='array' then out:=jsonb_set(out,'{values}',p->'values',true); end if;
  foreach k in array array[
    'scale_reserved_social','scale_cautious_bold','scale_calm_impulsive','scale_logic_instinct',
    'scale_conciliatory_confrontational','scale_follower_leader','scale_wary_trusting','scale_flexible_rigid'
  ] loop
    if coalesce(p->>k,'') ~ '^[1-5]$' then out:=jsonb_set(out,array[k],to_jsonb((p->>k)::integer),true); end if;
  end loop;
  return out;
end;
$$;
revoke all on function private.dating_safe_questionnaire_traits(uuid) from public,anon,authenticated;

create or replace function private.dating_is_eligible(p_user_id uuid)
returns boolean
language sql stable security definer
set search_path=pg_catalog,public,private
as $$
  select p_user_id is not null
    and public.sinjira_age_band(p_user_id)='adult'
    and exists(
      select 1 from public.private_profiles p
      where p.user_id=p_user_id and private.dating_allowed_relationship_status(p.relationship_status)
    )
    and public.has_accepted_community_rules(p_user_id)
    and not public.social_is_suspended(p_user_id);
$$;
revoke all on function private.dating_is_eligible(uuid) from public,anon,authenticated;

create or replace function private.dating_age(p_user_id uuid)
returns integer
language sql stable security definer
set search_path=pg_catalog,public
as $$
  select case when s.date_of_birth is null then null
    else extract(year from age(current_date,s.date_of_birth))::integer end
  from public.account_safety_profiles s where s.user_id=p_user_id;
$$;
revoke all on function private.dating_age(uuid) from public,anon,authenticated;

create or replace function private.dating_distance_allowed(p_owner uuid,p_other uuid,p_scope text)
returns boolean
language plpgsql stable security definer
set search_path=pg_catalog,public
as $$
declare a public.private_profiles%rowtype; b public.private_profiles%rowtype;
begin
  if p_scope='open_distance' then return true; end if;
  select * into a from public.private_profiles where user_id=p_owner;
  select * into b from public.private_profiles where user_id=p_other;
  if a.user_id is null or b.user_id is null then return false; end if;
  if p_scope='same_country' then
    return nullif(lower(btrim(a.residence_country)),'') is not null
      and lower(btrim(a.residence_country))=lower(btrim(b.residence_country));
  end if;
  return nullif(lower(btrim(a.residence_region)),'') is not null
    and nullif(lower(btrim(a.residence_country)),'') is not null
    and lower(btrim(a.residence_region))=lower(btrim(b.residence_region))
    and lower(btrim(a.residence_country))=lower(btrim(b.residence_country));
end;
$$;
revoke all on function private.dating_distance_allowed(uuid,uuid,text) from public,anon,authenticated;

create or replace function private.dating_pair_allowed(p_a uuid,p_b uuid)
returns boolean
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare da public.dating_profiles%rowtype; db public.dating_profiles%rowtype;
  pa public.private_profiles%rowtype; pb public.private_profiles%rowtype; age_a integer; age_b integer;
begin
  if p_a is null or p_b is null or p_a=p_b then return false; end if;
  if not private.dating_is_eligible(p_a) or not private.dating_is_eligible(p_b) then return false; end if;
  if public.social_is_blocked(p_a,p_b) then return false; end if;
  select * into da from public.dating_profiles where user_id=p_a and active=true and serious_intent_confirmed=true;
  select * into db from public.dating_profiles where user_id=p_b and active=true and serious_intent_confirmed=true;
  if da.user_id is null or db.user_id is null then return false; end if;
  select * into pa from public.private_profiles where user_id=p_a;
  select * into pb from public.private_profiles where user_id=p_b;
  age_a:=private.dating_age(p_a); age_b:=private.dating_age(p_b);
  if age_a is null or age_b is null then return false; end if;
  if age_b not between da.preferred_age_min and da.preferred_age_max then return false; end if;
  if age_a not between db.preferred_age_min and db.preferred_age_max then return false; end if;
  if cardinality(da.preferred_partner_genders)>0 and not (coalesce(pb.gender,'')=any(da.preferred_partner_genders)) then return false; end if;
  if cardinality(db.preferred_partner_genders)>0 and not (coalesce(pa.gender,'')=any(db.preferred_partner_genders)) then return false; end if;
  if not private.dating_distance_allowed(p_a,p_b,da.distance_scope) then return false; end if;
  if not private.dating_distance_allowed(p_b,p_a,db.distance_scope) then return false; end if;
  return true;
end;
$$;
revoke all on function private.dating_pair_allowed(uuid,uuid) from public,anon,authenticated;

create or replace function private.dating_personality_points(p_a jsonb,p_b jsonb)
returns integer
language plpgsql immutable
set search_path=pg_catalog
as $$
declare k text; va integer; vb integer; n integer:=0; total numeric:=0;
begin
  foreach k in array array[
    'scale_reserved_social','scale_cautious_bold','scale_calm_impulsive','scale_logic_instinct',
    'scale_conciliatory_confrontational','scale_follower_leader','scale_wary_trusting','scale_flexible_rigid'
  ] loop
    if coalesce(p_a->>k,'') ~ '^[1-5]$' and coalesce(p_b->>k,'') ~ '^[1-5]$' then
      va:=(p_a->>k)::integer; vb:=(p_b->>k)::integer; n:=n+1;
      total:=total + case abs(va-vb) when 0 then 1.0 when 1 then 0.8 when 2 then 0.5 when 3 then 0.2 else 0 end;
    end if;
  end loop;
  if n=0 then return 0; end if;
  return round((total/n)*15)::integer;
end;
$$;
revoke all on function private.dating_personality_points(jsonb,jsonb) from public,anon,authenticated;

create or replace function private.dating_pair_score(p_a uuid,p_b uuid)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare a public.dating_profiles%rowtype; b public.dating_profiles%rowtype;
  pa public.private_profiles%rowtype; pb public.private_profiles%rowtype;
  interest_n integer:=0; value_ab integer:=0; value_ba integer:=0; personality integer:=0; score integer:=35;
  strengths text[]:='{}'; explore text[]:='{}'; av text[]:='{}'; bv text[]:='{}';
begin
  if not private.dating_pair_allowed(p_a,p_b) then return jsonb_build_object('score',0,'strengths','[]'::jsonb,'explore','[]'::jsonb); end if;
  select * into a from public.dating_profiles where user_id=p_a;
  select * into b from public.dating_profiles where user_id=p_b;
  select * into pa from public.private_profiles where user_id=p_a;
  select * into pb from public.private_profiles where user_id=p_b;

  interest_n:=private.dating_overlap_count(a.interests,b.interests);
  if interest_n>0 then score:=score+least(15,interest_n*4); strengths:=array_append(strengths,'Centres d’intérêt compatibles'); end if;

  av:=private.dating_json_text_array(a.questionnaire_traits->'values');
  bv:=private.dating_json_text_array(b.questionnaire_traits->'values');
  value_ab:=private.dating_overlap_count(a.values_sought,bv);
  value_ba:=private.dating_overlap_count(b.values_sought,av);
  if value_ab+value_ba>0 then score:=score+least(15,(value_ab+value_ba)*3); strengths:=array_append(strengths,'Valeurs recherchées qui se rejoignent'); end if;

  if a.communication_style=b.communication_style then score:=score+12; strengths:=array_append(strengths,'Façon de communiquer proche');
  elsif a.communication_style='balanced' or b.communication_style='balanced' then score:=score+6;
  else explore:=array_append(explore,'Rythme de communication différent'); end if;

  if a.life_rhythm=b.life_rhythm then score:=score+8; strengths:=array_append(strengths,'Rythme de vie compatible');
  elsif a.life_rhythm='balanced' or b.life_rhythm='balanced' then score:=score+4;
  else explore:=array_append(explore,'Rythmes de vie à concilier'); end if;

  if a.social_energy=b.social_energy then score:=score+5; strengths:=array_append(strengths,'Énergie sociale similaire');
  elsif a.social_energy='balanced' or b.social_energy='balanced' then score:=score+3;
  else explore:=array_append(explore,'Besoins sociaux différents'); end if;

  if a.questionnaire_opt_in and b.questionnaire_opt_in then
    personality:=private.dating_personality_points(a.questionnaire_traits,b.questionnaire_traits);
    score:=score+personality;
    if personality>=11 then strengths:=array_append(strengths,'Personnalités naturellement compatibles');
    elsif personality<=5 then explore:=array_append(explore,'Personnalités plus contrastées'); end if;
  end if;

  if score>100 then score:=100; end if;
  if cardinality(strengths)=0 then strengths:=array['Préférences de base mutuellement compatibles']; end if;
  return jsonb_build_object('score',score,'strengths',to_jsonb(strengths),'explore',to_jsonb(explore));
end;
$$;
revoke all on function private.dating_pair_score(uuid,uuid) from public,anon,authenticated;

create or replace function public.dating_my_eligibility()
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); band text; rel text; reason text:='eligible'; ok boolean:=false;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  band:=public.sinjira_age_band(uid);
  select relationship_status into rel from public.private_profiles where user_id=uid;
  if band<>'adult' then reason:='adult_only';
  elsif not private.dating_allowed_relationship_status(rel) then reason:='single_status_required';
  elsif not public.has_accepted_community_rules(uid) then reason:='community_rules_required';
  elsif public.social_is_suspended(uid) then reason:='community_suspended';
  else ok:=true; end if;
  return jsonb_build_object('eligible',ok,'reason',reason,'age_band',band,'relationship_status',rel);
end;
$$;
revoke all on function public.dating_my_eligibility() from public,anon;
grant execute on function public.dating_my_eligibility() to authenticated;

create or replace function public.dating_save_profile(p_input jsonb)
returns jsonb
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); genders text[]; vals text[]; ints text[]; qopt boolean; activate boolean; serious boolean;
  amin integer; amax integer; comm text; rhythm text; energy text; dist text; traits jsonb:='{}'::jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not private.dating_is_eligible(uid) then raise exception 'DATING_NOT_ELIGIBLE'; end if;
  genders:=private.dating_json_text_array(p_input->'preferred_partner_genders');
  vals:=private.dating_json_text_array(p_input->'values_sought');
  ints:=private.dating_json_text_array(p_input->'interests');
  if exists(select 1 from unnest(genders) g where g<>all(array['Femme','Homme','Non binaire','Autre']::text[])) then raise exception 'INVALID_GENDER_PREFERENCE'; end if;
  if cardinality(genders)>5 or cardinality(vals)>8 or cardinality(ints)>12 then raise exception 'TOO_MANY_PREFERENCES'; end if;
  amin:=coalesce(nullif(p_input->>'preferred_age_min','')::integer,18);
  amax:=coalesce(nullif(p_input->>'preferred_age_max','')::integer,80);
  if amin<18 or amax>99 or amax<amin then raise exception 'INVALID_AGE_RANGE'; end if;
  comm:=coalesce(nullif(p_input->>'communication_style',''),'balanced');
  rhythm:=coalesce(nullif(p_input->>'life_rhythm',''),'balanced');
  energy:=coalesce(nullif(p_input->>'social_energy',''),'balanced');
  dist:=coalesce(nullif(p_input->>'distance_scope',''),'same_region');
  if comm<>all(array['frequent','balanced','independent']::text[]) then raise exception 'INVALID_COMMUNICATION_STYLE'; end if;
  if rhythm<>all(array['calm','balanced','active']::text[]) then raise exception 'INVALID_LIFE_RHYTHM'; end if;
  if energy<>all(array['reserved','balanced','social']::text[]) then raise exception 'INVALID_SOCIAL_ENERGY'; end if;
  if dist<>all(array['same_region','same_country','open_distance']::text[]) then raise exception 'INVALID_DISTANCE_SCOPE'; end if;
  qopt:=coalesce((p_input->>'questionnaire_opt_in')::boolean,false);
  activate:=coalesce((p_input->>'active')::boolean,false);
  serious:=coalesce((p_input->>'serious_intent_confirmed')::boolean,false);
  if activate and not serious then raise exception 'SERIOUS_INTENT_REQUIRED'; end if;
  if qopt then traits:=private.dating_safe_questionnaire_traits(uid); end if;

  insert into public.dating_profiles(
    user_id,active,relationship_goal,preferred_age_min,preferred_age_max,preferred_partner_genders,
    values_sought,interests,communication_style,life_rhythm,social_energy,distance_scope,
    questionnaire_opt_in,questionnaire_traits,serious_intent_confirmed,consent_version,consented_at
  ) values (
    uid,activate,'serious',amin,amax,genders,vals,ints,comm,rhythm,energy,dist,
    qopt,traits,serious,case when activate then 'sinjira-dating-v1-2026-08-19' else null end,
    case when activate then now() else null end
  ) on conflict(user_id) do update set
    active=excluded.active,relationship_goal='serious',preferred_age_min=excluded.preferred_age_min,
    preferred_age_max=excluded.preferred_age_max,preferred_partner_genders=excluded.preferred_partner_genders,
    values_sought=excluded.values_sought,interests=excluded.interests,communication_style=excluded.communication_style,
    life_rhythm=excluded.life_rhythm,social_energy=excluded.social_energy,distance_scope=excluded.distance_scope,
    questionnaire_opt_in=excluded.questionnaire_opt_in,questionnaire_traits=excluded.questionnaire_traits,
    serious_intent_confirmed=excluded.serious_intent_confirmed,
    consent_version=case when excluded.active then excluded.consent_version else public.dating_profiles.consent_version end,
    consented_at=case when excluded.active then coalesce(public.dating_profiles.consented_at,excluded.consented_at) else public.dating_profiles.consented_at end,
    updated_at=now();
  return jsonb_build_object('saved',true,'active',activate,'questionnaire_traits_used',qopt and traits<>'{}'::jsonb);
end;
$$;
revoke all on function public.dating_save_profile(jsonb) from public,anon;
grant execute on function public.dating_save_profile(jsonb) to authenticated;

create or replace function public.dating_delete_my_profile()
returns boolean
language plpgsql volatile security definer
set search_path=pg_catalog,public
as $$
declare uid uuid:=auth.uid();
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  delete from public.dating_introductions where uid in(user_a,user_b);
  delete from public.dating_profiles where user_id=uid;
  return true;
end;
$$;
revoke all on function public.dating_delete_my_profile() from public,anon;
grant execute on function public.dating_delete_my_profile() to authenticated;

create or replace function public.dating_recommendations(p_limit integer default 8)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not exists(select 1 from public.dating_profiles where user_id=uid and active=true) then return '[]'::jsonb; end if;
  if not private.dating_is_eligible(uid) then return '[]'::jsonb; end if;
  select coalesce(jsonb_agg(x.item order by x.score desc,x.pseudo),'[]'::jsonb) into result
  from (
    select sp.pseudo,
      (private.dating_pair_score(uid,d.user_id)->>'score')::integer score,
      jsonb_build_object(
        'user_id',d.user_id,
        'pseudo',coalesce(nullif(sp.pseudo,''),nullif(sp.display_name,''),'Membre SINJIRA'),
        'compatibility_score',(private.dating_pair_score(uid,d.user_id)->>'score')::integer,
        'strengths',private.dating_pair_score(uid,d.user_id)->'strengths',
        'explore',private.dating_pair_score(uid,d.user_id)->'explore'
      ) item
    from public.dating_profiles d
    join public.social_profiles sp on sp.user_id=d.user_id
    where d.user_id<>uid and d.active=true and private.dating_pair_allowed(uid,d.user_id)
      and not exists(select 1 from public.dating_introductions i where (i.user_a=least(uid,d.user_id) and i.user_b=greatest(uid,d.user_id)))
    order by score desc,sp.pseudo
    limit greatest(1,least(coalesce(p_limit,8),20))
  ) x;
  return result;
end;
$$;
revoke all on function public.dating_recommendations(integer) from public,anon;
grant execute on function public.dating_recommendations(integer) to authenticated;

create or replace function public.dating_request_introduction(p_target_user_id uuid)
returns uuid
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); a uuid; b uuid; rid uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not private.dating_pair_allowed(uid,p_target_user_id) then raise exception 'DATING_PAIR_NOT_ALLOWED'; end if;
  if uid::text<p_target_user_id::text then a:=uid;b:=p_target_user_id; else a:=p_target_user_id;b:=uid; end if;
  if exists(select 1 from public.dating_introductions where user_a=a and user_b=b) then raise exception 'INTRO_ALREADY_EXISTS'; end if;
  insert into public.dating_introductions(user_a,user_b,requested_by) values(a,b,uid) returning id into rid;
  insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
  values(p_target_user_id,'dating_intro','Nouvelle présentation proposée','Une personne compatible souhaite ouvrir une présentation.','dating_introduction',rid,'/compte/rencontres.html');
  return rid;
end;
$$;
revoke all on function public.dating_request_introduction(uuid) from public,anon;
grant execute on function public.dating_request_introduction(uuid) to authenticated;

create or replace function public.dating_respond_introduction(p_introduction_id uuid,p_accept boolean)
returns boolean
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); i public.dating_introductions%rowtype; other_id uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into i from public.dating_introductions where id=p_introduction_id for update;
  if i.id is null or uid not in(i.user_a,i.user_b) then raise exception 'INTRO_NOT_FOUND'; end if;
  if i.requested_by=uid or i.status<>'requested' then raise exception 'INTRO_RESPONSE_NOT_ALLOWED'; end if;
  other_id:=case when uid=i.user_a then i.user_b else i.user_a end;
  if p_accept and not private.dating_pair_allowed(uid,other_id) then raise exception 'DATING_PAIR_NOT_ALLOWED'; end if;
  update public.dating_introductions set status=case when p_accept then 'accepted' else 'declined' end,
    accepted_at=case when p_accept then now() else null end,closed_at=case when p_accept then null else now() end,updated_at=now()
  where id=i.id;
  insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
  values(other_id,'dating_intro',case when p_accept then 'Présentation acceptée' else 'Présentation non retenue' end,
    case when p_accept then 'Vous pouvez maintenant commencer une conversation dans la messagerie.' else 'La proposition de présentation a été fermée.' end,
    'dating_introduction',i.id,'/compte/rencontres.html');
  return true;
end;
$$;
revoke all on function public.dating_respond_introduction(uuid,boolean) from public,anon;
grant execute on function public.dating_respond_introduction(uuid,boolean) to authenticated;

create or replace function public.dating_close_introduction(p_introduction_id uuid)
returns boolean
language plpgsql volatile security definer
set search_path=pg_catalog,public
as $$
declare uid uuid:=auth.uid();
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  update public.dating_introductions set status='closed',closed_at=now(),updated_at=now()
  where id=p_introduction_id and uid in(user_a,user_b) and status in('requested','accepted');
  if not found then raise exception 'INTRO_CLOSE_NOT_ALLOWED'; end if;
  return true;
end;
$$;
revoke all on function public.dating_close_introduction(uuid) from public,anon;
grant execute on function public.dating_close_introduction(uuid) to authenticated;

create or replace function public.dating_my_introductions()
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'id',i.id,'status',i.status,'requested_by_me',i.requested_by=uid,
    'other_user_id',case when i.user_a=uid then i.user_b else i.user_a end,
    'other_pseudo',coalesce(nullif(sp.pseudo,''),nullif(sp.display_name,''),'Membre SINJIRA'),
    'accepted_at',i.accepted_at,'created_at',i.created_at
  ) order by i.updated_at desc),'[]'::jsonb) into result
  from public.dating_introductions i
  join public.social_profiles sp on sp.user_id=case when i.user_a=uid then i.user_b else i.user_a end
  where uid in(i.user_a,i.user_b);
  return result;
end;
$$;
revoke all on function public.dating_my_introductions() from public,anon;
grant execute on function public.dating_my_introductions() to authenticated;

create or replace function private.dating_photo_status(p_introduction_id uuid,p_viewer uuid)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public
as $$
declare i public.dating_introductions%rowtype; other_id uuid; sent_n integer:=0; received_n integer:=0; mine boolean:=false; theirs boolean:=false; unlocked boolean:=false; avatar text;
begin
  select * into i from public.dating_introductions where id=p_introduction_id;
  if i.id is null or i.status<>'accepted' or p_viewer not in(i.user_a,i.user_b) then raise exception 'ACCEPTED_INTRO_REQUIRED'; end if;
  other_id:=case when p_viewer=i.user_a then i.user_b else i.user_a end;
  select count(*) filter(where m.sender_user_id=p_viewer),count(*) filter(where m.sender_user_id=other_id)
  into sent_n,received_n from public.social_real_messages m
  where ((m.sender_user_id=p_viewer and m.recipient_user_id=other_id) or (m.sender_user_id=other_id and m.recipient_user_id=p_viewer))
    and m.created_at>=coalesce(i.accepted_at,i.created_at) and char_length(btrim(m.body))>=2;
  select exists(select 1 from public.dating_photo_reveal_consents c where c.introduction_id=i.id and c.user_id=p_viewer) into mine;
  select exists(select 1 from public.dating_photo_reveal_consents c where c.introduction_id=i.id and c.user_id=other_id) into theirs;
  unlocked:=sent_n>=10 and received_n>=10 and mine and theirs;
  if unlocked then select avatar_path into avatar from public.social_profiles where user_id=other_id; end if;
  return jsonb_build_object('sent_count',sent_n,'received_count',received_n,'threshold',10,'my_consent',mine,'other_consent',theirs,'unlocked',unlocked,'other_avatar_path',case when unlocked then avatar else null end);
end;
$$;
revoke all on function private.dating_photo_status(uuid,uuid) from public,anon,authenticated;

create or replace function public.dating_photo_reveal_status(p_introduction_id uuid)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid();
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  return private.dating_photo_status(p_introduction_id,uid);
end;
$$;
revoke all on function public.dating_photo_reveal_status(uuid) from public,anon;
grant execute on function public.dating_photo_reveal_status(uuid) to authenticated;

create or replace function public.dating_request_photo_reveal(p_introduction_id uuid)
returns jsonb
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); s jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  s:=private.dating_photo_status(p_introduction_id,uid);
  if (s->>'sent_count')::integer<10 or (s->>'received_count')::integer<10 then raise exception 'PHOTO_THRESHOLD_NOT_MET'; end if;
  insert into public.dating_photo_reveal_consents(introduction_id,user_id) values(p_introduction_id,uid)
  on conflict(introduction_id,user_id) do nothing;
  return private.dating_photo_status(p_introduction_id,uid);
end;
$$;
revoke all on function public.dating_request_photo_reveal(uuid) from public,anon;
grant execute on function public.dating_request_photo_reveal(uuid) to authenticated;

create or replace function public.dating_revoke_photo_reveal(p_introduction_id uuid)
returns jsonb
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid();
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not exists(select 1 from public.dating_introductions i where i.id=p_introduction_id and uid in(i.user_a,i.user_b)) then raise exception 'INTRO_NOT_FOUND'; end if;
  delete from public.dating_photo_reveal_consents where introduction_id=p_introduction_id and user_id=uid;
  return private.dating_photo_status(p_introduction_id,uid);
end;
$$;
revoke all on function public.dating_revoke_photo_reveal(uuid) from public,anon;
grant execute on function public.dating_revoke_photo_reveal(uuid) to authenticated;

-- Si le statut relationnel devient non admissible, le profil est immédiatement mis en pause.
create or replace function private.dating_deactivate_on_private_profile_change()
returns trigger
language plpgsql security definer
set search_path=pg_catalog,public,private
as $$
begin
  if not private.dating_allowed_relationship_status(new.relationship_status) then
    update public.dating_profiles set active=false,updated_at=now() where user_id=new.user_id and active=true;
  end if;
  return new;
end;
$$;
revoke all on function private.dating_deactivate_on_private_profile_change() from public,anon,authenticated;
drop trigger if exists dating_private_profile_guard on public.private_profiles;
create trigger dating_private_profile_guard after insert or update of relationship_status on public.private_profiles
for each row execute function private.dating_deactivate_on_private_profile_change();

create or replace function private.dating_deactivate_on_safety_change()
returns trigger
language plpgsql security definer
set search_path=pg_catalog,public
as $$
begin
  if public.sinjira_age_band(new.user_id)<>'adult' then
    update public.dating_profiles set active=false,updated_at=now() where user_id=new.user_id and active=true;
  end if;
  return new;
end;
$$;
revoke all on function private.dating_deactivate_on_safety_change() from public,anon,authenticated;
drop trigger if exists dating_safety_profile_guard on public.account_safety_profiles;
create trigger dating_safety_profile_guard after insert or update of date_of_birth,legacy_status on public.account_safety_profiles
for each row execute function private.dating_deactivate_on_safety_change();

comment on table public.dating_profiles is 'Rencontres SINJIRA™ 18+ opt-in. Profil privé; recommandations via RPC uniquement, sans photo.';
comment on table public.dating_introductions is 'Présentations mutuelles entre adultes admissibles. Aucune liste publique des participants.';
comment on table public.dating_photo_reveal_consents is 'Consentements de révélation de photo après 10 messages de chaque côté; lecture directe interdite.';
comment on function public.dating_recommendations(integer) is 'Moteur local explicable V24.4.74. Ne renvoie ni photo, ni courriel, ni réponses brutes du Registre.';

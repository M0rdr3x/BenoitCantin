-- SINJIRA™ V24.4.81
-- Rencontres strictement réservées aux célibataires + portefeuille universel Points SINJIRA™.
-- 1 Point SINJIRA est débité pour une recommandation de première rencontre, uniquement après consentement mutuel.
-- Le portefeuille est volontairement générique afin d'être réutilisé par la boutique et les autres services SINJIRA™.

create table if not exists public.sinjira_points_accounts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  balance integer not null default 0 check (balance >= 0),
  lifetime_earned integer not null default 0 check (lifetime_earned >= 0),
  lifetime_spent integer not null default 0 check (lifetime_spent >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.sinjira_points_ledger (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  delta integer not null check (delta <> 0),
  reason text not null check (char_length(reason) between 1 and 80),
  source_type text not null check (char_length(source_type) between 1 and 60),
  source_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.dating_meet_requests (
  id uuid primary key default gen_random_uuid(),
  connection_id uuid not null unique references public.dating_connections(id) on delete cascade,
  payer_profile_id uuid not null references public.dating_profiles(id) on delete cascade,
  profile_a_consent boolean not null default false,
  profile_b_consent boolean not null default false,
  profile_a_preferences text[] not null default '{}',
  profile_b_preferences text[] not null default '{}',
  meeting_area text not null default '' check (char_length(meeting_area) between 1 and 120),
  status text not null default 'waiting' check (status in ('waiting','generated','cancelled')),
  point_spent boolean not null default false,
  recommendation jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.sinjira_points_accounts enable row level security;
alter table public.sinjira_points_ledger enable row level security;
alter table public.dating_meet_requests enable row level security;

revoke all on public.sinjira_points_accounts, public.sinjira_points_ledger, public.dating_meet_requests from public, anon, authenticated;
grant select,insert,update,delete on public.sinjira_points_accounts, public.sinjira_points_ledger, public.dating_meet_requests to service_role;

create index if not exists sinjira_points_ledger_user_created_idx on public.sinjira_points_ledger(user_id,created_at desc);
create unique index if not exists sinjira_points_one_safe_meet_debit_idx on public.sinjira_points_ledger(source_id)
  where source_type='dating_safe_meet' and reason='safe_meet_recommendation' and delta<0 and source_id is not null;
create index if not exists dating_meet_requests_payer_idx on public.dating_meet_requests(payer_profile_id,created_at desc);

create or replace function private.sinjira_points_touch_updated_at() returns trigger
language plpgsql set search_path=pg_catalog,public as $$
begin
  new.updated_at=now();
  return new;
end;
$$;

drop trigger if exists sinjira_points_accounts_updated_at on public.sinjira_points_accounts;
create trigger sinjira_points_accounts_updated_at before update on public.sinjira_points_accounts
for each row execute function private.sinjira_points_touch_updated_at();

drop trigger if exists dating_meet_requests_updated_at on public.dating_meet_requests;
create trigger dating_meet_requests_updated_at before update on public.dating_meet_requests
for each row execute function private.sinjira_points_touch_updated_at();

create or replace function private.sinjira_points_ensure_account(p_user_id uuid)
returns integer
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_balance integer;
begin
  if p_user_id is null then raise exception 'AUTH_REQUIRED'; end if;
  insert into public.sinjira_points_accounts(user_id) values(p_user_id)
  on conflict (user_id) do nothing;
  select balance into v_balance from public.sinjira_points_accounts where user_id=p_user_id;
  return coalesce(v_balance,0);
end;
$$;

create or replace function private.sinjira_points_spend(
  p_user_id uuid,
  p_amount integer,
  p_reason text,
  p_source_type text,
  p_source_id uuid,
  p_metadata jsonb default '{}'::jsonb
)
returns integer
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_balance integer;
begin
  if p_user_id is null then raise exception 'AUTH_REQUIRED'; end if;
  if p_amount is null or p_amount<=0 then raise exception 'POINTS_AMOUNT_INVALID'; end if;
  if nullif(btrim(coalesce(p_reason,'')),'') is null or char_length(p_reason)>80 then raise exception 'POINTS_REASON_INVALID'; end if;
  if nullif(btrim(coalesce(p_source_type,'')),'') is null or char_length(p_source_type)>60 then raise exception 'POINTS_SOURCE_INVALID'; end if;

  perform private.sinjira_points_ensure_account(p_user_id);
  select balance into v_balance from public.sinjira_points_accounts where user_id=p_user_id for update;
  if v_balance<p_amount then raise exception 'SINJIRA_POINTS_REQUIRED'; end if;

  update public.sinjira_points_accounts
  set balance=balance-p_amount,lifetime_spent=lifetime_spent+p_amount
  where user_id=p_user_id
  returning balance into v_balance;

  insert into public.sinjira_points_ledger(user_id,delta,reason,source_type,source_id,metadata)
  values(p_user_id,-p_amount,p_reason,p_source_type,p_source_id,coalesce(p_metadata,'{}'::jsonb));
  return v_balance;
end;
$$;

create or replace function private.dating_connection_identity_revealed(p_connection_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
select coalesce(
  c.status='accepted'
  and private.dating_is_eligible(pa.user_id)
  and private.dating_is_eligible(pb.user_id)
  and coalesce(c.a_photo_consent,false)
  and coalesce(c.b_photo_consent,false)
  and (select count(*) from public.dating_messages m where m.connection_id=c.id and m.sender_profile_id=c.profile_a_id)>=10
  and (select count(*) from public.dating_messages m where m.connection_id=c.id and m.sender_profile_id=c.profile_b_id)>=10,
false)
from public.dating_connections c
join public.dating_profiles pa on pa.id=c.profile_a_id
join public.dating_profiles pb on pb.id=c.profile_b_id
where c.id=p_connection_id;
$$;

create or replace function private.dating_safe_meet_recommendation(p_a text[],p_b text[],p_area text)
returns jsonb
language sql
immutable
set search_path=pg_catalog
as $$
with catalogue(code,title,detail,priority) as (
  values
    ('coffee','Café calme et fréquenté','Un café public avec personnel présent permet une première rencontre simple et facile à écourter.',1),
    ('tea','Salon de thé public','Un salon de thé public favorise une conversation calme dans un lieu encadré.',2),
    ('dessert','Café-dessert','Une courte sortie dessert garde la première rencontre légère et dans un commerce public.',3),
    ('brunch','Brunch dans un restaurant fréquenté','Un brunch de jour offre un cadre public, animé et structuré.',4),
    ('restaurant','Restaurant assis et achalandé','Un restaurant avec personnel présent offre un cadre public et prévisible.',5),
    ('museum','Musée','Un musée permet de marcher et discuter autour d’un intérêt commun dans un espace public.',6),
    ('gallery','Galerie ou centre d’exposition','Une exposition publique offre un sujet de conversation naturel sans pression.',7),
    ('bookstore','Librairie avec espace café','Une librairie publique convient bien aux personnes qui aiment lire et discuter calmement.',8),
    ('library','Bibliothèque ou espace culturel public','Un espace culturel public convient à une rencontre calme, accessible et non axée sur l’alcool.',9),
    ('board_games','Café de jeux de société','Une activité structurée peut réduire la pression tout en gardant la rencontre dans un commerce public.',10),
    ('public_market','Marché public','Un marché public fréquenté donne plusieurs options et permet une rencontre courte ou prolongée.',11),
    ('culture','Centre culturel ou activité publique','Une activité culturelle publique crée un contexte partagé sans exiger une longue rencontre.',12),
    ('outdoor_walk','Promenade publique achalandée, de jour','À retenir seulement dans un secteur public fréquenté, en journée et avec un plan de retour indépendant.',13)
), ranked as (
  select c.*,
    case
      when c.code=any(coalesce(p_a,'{}'::text[])) and c.code=any(coalesce(p_b,'{}'::text[])) then 0
      when c.code=any(coalesce(p_a,'{}'::text[])) or c.code=any(coalesce(p_b,'{}'::text[])) then 1
      when c.code in ('coffee','museum','public_market') then 2
      else 3
    end as fit_rank
  from catalogue c
), picked as (
  select * from ranked order by fit_rank,priority limit 3
)
select jsonb_build_object(
  'area',p_area,
  'generated_locally',true,
  'external_paid_provider_used',false,
  'safety_notice','Ces suggestions privilégient des catégories de lieux publics; SINJIRA™ ne garantit jamais la sécurité d’un établissement. Vérifiez vous-mêmes les heures, l’accessibilité et les conditions actuelles avant de vous déplacer.',
  'shared_preferences',(
    select coalesce(jsonb_agg(x order by x),'[]'::jsonb)
    from (select distinct x from unnest(coalesce(p_a,'{}'::text[])) x intersect select distinct y from unnest(coalesce(p_b,'{}'::text[])) y) q
  ),
  'places',(
    select coalesce(jsonb_agg(jsonb_build_object(
      'type',code,
      'title',title,
      'why',case when fit_rank=0 then 'Vous avez tous les deux choisi ce type de sortie.' when fit_rank=1 then 'Ce type rejoint au moins une de vos préférences et reste adapté à une première rencontre publique.' else 'Option publique de repli lorsque vos préférences ne donnent pas trois choix communs.' end,
      'detail',detail,
      'search_query',title||' '||p_area
    ) order by fit_rank,priority),'[]'::jsonb)
    from picked
  ),
  'checklist',jsonb_build_array(
    'Choisissez un lieu public avec personnel ou passage régulier.',
    'Gardez chacun votre propre moyen de retour.',
    'Informez une personne de confiance du lieu et de l’heure.',
    'Ne partagez pas votre adresse résidentielle pour une première rencontre.',
    'Privilégiez le jour ou le début de soirée et vérifiez les heures d’ouverture.'
  )
);
$$;

revoke all on function private.sinjira_points_touch_updated_at(), private.sinjira_points_ensure_account(uuid), private.sinjira_points_spend(uuid,integer,text,text,uuid,jsonb), private.dating_connection_identity_revealed(uuid), private.dating_safe_meet_recommendation(text[],text[],text) from public,anon,authenticated;
grant execute on function private.sinjira_points_touch_updated_at(), private.sinjira_points_ensure_account(uuid), private.sinjira_points_spend(uuid,integer,text,text,uuid,jsonb), private.dating_connection_identity_revealed(uuid), private.dating_safe_meet_recommendation(text[],text[],text) to service_role;

-- Le statut amoureux central est la source de vérité. Rencontres ne le modifie jamais.
create or replace function public.dating_confirm_single_and_serious()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_age int;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  v_age:=private.dating_age(v_user);
  if v_age is null or v_age<18 then raise exception 'ADULTS_ONLY'; end if;

  if not exists(
    select 1 from public.account_safety_profiles s
    where s.user_id=v_user
      and s.legacy_status='active'
      and s.relationship_data_opt_in is true
      and s.relationship_status='single'
  ) then raise exception 'DATING_NOT_ELIGIBLE'; end if;

  if not exists(
    select 1 from public.dating_profiles p
    join public.dating_preferences d on d.user_id=p.user_id
    where p.user_id=v_user
      and p.gender_identity is not null
      and btrim(p.intro)<>''
      and cardinality(d.seeking_genders)>0
  ) then raise exception 'PROFILE_INCOMPLETE'; end if;

  update public.dating_profiles
  set enabled=true,serious_intent_confirmed=true,single_confirmed_at=now(),updated_at=now()
  where user_id=v_user;

  return jsonb_build_object('ok',true,'eligible',private.dating_is_eligible(v_user),'relationship_status','single','reconfirm_by',now()+interval '90 days');
end;
$$;

create or replace function private.dating_enforce_relationship_gate()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_profile uuid;
begin
  if new.relationship_status<>'single' or new.relationship_data_opt_in is not true or new.legacy_status<>'active' then
    select id into v_profile from public.dating_profiles where user_id=new.user_id;
    if v_profile is not null then
      update public.dating_profiles
      set enabled=false,serious_intent_confirmed=false,single_confirmed_at=null,updated_at=now()
      where id=v_profile;

      update public.dating_connections
      set status='closed',closed_at=coalesce(closed_at,now()),a_photo_consent=false,b_photo_consent=false
      where status in ('pending','accepted') and v_profile in(profile_a_id,profile_b_id);

      update public.dating_meet_requests r
      set status='cancelled'
      from public.dating_connections c
      where r.connection_id=c.id and r.status='waiting' and v_profile in(c.profile_a_id,c.profile_b_id);
    end if;
  end if;
  return new;
end;
$$;

revoke all on function private.dating_enforce_relationship_gate() from public,anon,authenticated;
grant execute on function private.dating_enforce_relationship_gate() to service_role;

drop trigger if exists dating_relationship_gate on public.account_safety_profiles;
create trigger dating_relationship_gate
after update of relationship_status,relationship_data_opt_in,legacy_status on public.account_safety_profiles
for each row
when (
  old.relationship_status is distinct from new.relationship_status
  or old.relationship_data_opt_in is distinct from new.relationship_data_opt_in
  or old.legacy_status is distinct from new.legacy_status
)
execute function private.dating_enforce_relationship_gate();

create or replace function public.dating_respond_connection(p_connection_id uuid,p_accept boolean)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_other uuid;
  v_other_user uuid;
  v_sender_user uuid;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;
  if not private.dating_is_eligible(v_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;

  select case when c.profile_a_id=v_me then c.profile_b_id else c.profile_a_id end into v_other
  from public.dating_connections c
  where c.id=p_connection_id and c.status='pending' and c.requested_by_profile_id<>v_me and v_me in(c.profile_a_id,c.profile_b_id);
  if v_other is null then raise exception 'REQUEST_NOT_AVAILABLE'; end if;

  select user_id into v_other_user from public.dating_profiles where id=v_other;
  if p_accept and not private.dating_is_eligible(v_other_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;

  update public.dating_connections
  set status=case when p_accept then 'accepted' else 'declined' end,
      accepted_at=case when p_accept then now() else null end,
      closed_at=case when p_accept then null else now() end,
      a_photo_consent=case when p_accept then a_photo_consent else false end,
      b_photo_consent=case when p_accept then b_photo_consent else false end
  where id=p_connection_id;

  select p.user_id into v_sender_user
  from public.dating_connections c join public.dating_profiles p on p.id=c.requested_by_profile_id
  where c.id=p_connection_id;

  insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
  values(v_sender_user,'dating',case when p_accept then 'Discussion de compatibilité acceptée' else 'Proposition de discussion terminée' end,case when p_accept then 'Votre discussion anonyme peut commencer.' else 'Cette proposition de discussion ne se poursuivra pas.' end,'dating_connection',p_connection_id,'/compte/rencontres.html');
  return jsonb_build_object('ok',true,'status',case when p_accept then 'accepted' else 'declined' end);
end;
$$;

create or replace function public.dating_conversation(p_connection_id uuid)
returns table(message_id uuid,sender_is_me boolean,body text,created_at timestamptz)
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
with me as (
  select p.id,p.user_id from public.dating_profiles p where p.user_id=auth.uid()
), allowed as (
  select c.id,m.id me_id
  from public.dating_connections c
  join me m on m.id in(c.profile_a_id,c.profile_b_id)
  join public.dating_profiles pa on pa.id=c.profile_a_id
  join public.dating_profiles pb on pb.id=c.profile_b_id
  where c.id=p_connection_id and c.status='accepted'
    and private.dating_is_eligible(pa.user_id)
    and private.dating_is_eligible(pb.user_id)
)
select dm.id,dm.sender_profile_id=a.me_id,dm.body,dm.created_at
from public.dating_messages dm join allowed a on a.id=dm.connection_id
order by dm.created_at asc limit 500;
$$;

create or replace function public.dating_set_photo_consent(p_connection_id uuid,p_consent boolean)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_a uuid;
  v_b uuid;
  v_a_user uuid;
  v_b_user uuid;
  v_my int;
  v_their int;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;
  select c.profile_a_id,c.profile_b_id,pa.user_id,pb.user_id into v_a,v_b,v_a_user,v_b_user
  from public.dating_connections c
  join public.dating_profiles pa on pa.id=c.profile_a_id
  join public.dating_profiles pb on pb.id=c.profile_b_id
  where c.id=p_connection_id and c.status='accepted' and v_me in(c.profile_a_id,c.profile_b_id);
  if v_a is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;
  if not private.dating_is_eligible(v_a_user) or not private.dating_is_eligible(v_b_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;

  select count(*)::int into v_my from public.dating_messages dm where dm.connection_id=p_connection_id and dm.sender_profile_id=v_me;
  select count(*)::int into v_their from public.dating_messages dm where dm.connection_id=p_connection_id and dm.sender_profile_id<>v_me;
  if p_consent and (v_my<10 or v_their<10) then raise exception 'PHOTO_REVEAL_TOO_EARLY'; end if;

  if v_me=v_a then update public.dating_connections set a_photo_consent=p_consent where id=p_connection_id;
  else update public.dating_connections set b_photo_consent=p_consent where id=p_connection_id; end if;
  return jsonb_build_object('ok',true,'my_messages',v_my,'their_messages',v_their,'threshold',10);
end;
$$;

create or replace function public.sinjira_points_status()
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_balance integer;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  v_balance:=private.sinjira_points_ensure_account(v_user);
  return jsonb_build_object('balance',v_balance,'currency','SINJIRA_POINT','purchases_enabled',false);
end;
$$;

create or replace function public.dating_safe_meet_status(p_connection_id uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_a uuid;
  v_b uuid;
  v_req public.dating_meet_requests%rowtype;
  v_balance integer:=0;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;
  select profile_a_id,profile_b_id into v_a,v_b from public.dating_connections
  where id=p_connection_id and v_me in(profile_a_id,profile_b_id);
  if v_a is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;

  select * into v_req from public.dating_meet_requests where connection_id=p_connection_id;
  select coalesce(balance,0) into v_balance from public.sinjira_points_accounts where user_id=v_user;

  return jsonb_build_object(
    'connection_id',p_connection_id,
    'identity_revealed',private.dating_connection_identity_revealed(p_connection_id),
    'status',coalesce(v_req.status,'not_started'),
    'my_consent',case when v_req.id is null then false when v_me=v_a then v_req.profile_a_consent else v_req.profile_b_consent end,
    'other_consent',case when v_req.id is null then false when v_me=v_a then v_req.profile_b_consent else v_req.profile_a_consent end,
    'payer_is_me',coalesce(v_req.payer_profile_id=v_me,false),
    'meeting_area',case when v_req.id is null then null else v_req.meeting_area end,
    'recommendation',case when v_req.status='generated' then v_req.recommendation else null end,
    'point_spent',coalesce(v_req.point_spent,false),
    'points_balance',v_balance,
    'cost_points',1
  );
end;
$$;

create or replace function public.dating_safe_meet_opt_in(p_connection_id uuid,p_preferences text[],p_meeting_area text default null)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_a uuid;
  v_b uuid;
  v_a_user uuid;
  v_b_user uuid;
  v_area text:=nullif(btrim(coalesce(p_meeting_area,'')),'');
  v_prefs text[];
  v_req public.dating_meet_requests%rowtype;
  v_payer_user uuid;
  v_balance integer;
  v_recommendation jsonb;
  v_allowed constant text[]:=array['coffee','tea','dessert','brunch','restaurant','museum','gallery','bookstore','library','board_games','public_market','culture','outdoor_walk','quiet','accessible','low_cost','alcohol_free','indoor','daytime'];
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;

  select c.profile_a_id,c.profile_b_id,pa.user_id,pb.user_id into v_a,v_b,v_a_user,v_b_user
  from public.dating_connections c
  join public.dating_profiles pa on pa.id=c.profile_a_id
  join public.dating_profiles pb on pb.id=c.profile_b_id
  where c.id=p_connection_id and c.status='accepted' and v_me in(c.profile_a_id,c.profile_b_id);
  if v_a is null then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;
  if not private.dating_is_eligible(v_a_user) or not private.dating_is_eligible(v_b_user) then raise exception 'DATING_NOT_ELIGIBLE'; end if;
  if not private.dating_connection_identity_revealed(p_connection_id) then raise exception 'DATING_MEET_REVEAL_REQUIRED'; end if;
  if exists(select 1 from public.social_blocks b where (b.blocker_user_id=v_a_user and b.blocked_user_id=v_b_user) or (b.blocker_user_id=v_b_user and b.blocked_user_id=v_a_user)) then raise exception 'CONVERSATION_NOT_AVAILABLE'; end if;

  select coalesce(array_agg(distinct x order by x),'{}'::text[]) into v_prefs
  from unnest(coalesce(p_preferences,'{}'::text[])) x where x=any(v_allowed);
  if exists(select 1 from unnest(coalesce(p_preferences,'{}'::text[])) x where not (x=any(v_allowed))) then raise exception 'DATING_MEET_PREFERENCE_INVALID'; end if;
  if cardinality(v_prefs)>12 then raise exception 'DATING_MEET_PREFERENCE_INVALID'; end if;

  insert into public.dating_meet_requests(connection_id,payer_profile_id,meeting_area)
  select p_connection_id,v_me,v_area
  where not exists(select 1 from public.dating_meet_requests where connection_id=p_connection_id) and v_area is not null
  on conflict (connection_id) do nothing;

  select * into v_req from public.dating_meet_requests where connection_id=p_connection_id for update;
  if v_req.id is null then raise exception 'DATING_MEET_AREA_REQUIRED'; end if;
  if v_req.status='generated' then return public.dating_safe_meet_status(p_connection_id); end if;

  if v_req.status='cancelled' then
    if v_area is null then raise exception 'DATING_MEET_AREA_REQUIRED'; end if;
    update public.dating_meet_requests
    set payer_profile_id=v_me,profile_a_consent=false,profile_b_consent=false,
        profile_a_preferences='{}',profile_b_preferences='{}',meeting_area=v_area,
        status='waiting',point_spent=false,recommendation=null
    where id=v_req.id returning * into v_req;
  end if;

  if v_area is null then v_area:=v_req.meeting_area; end if;
  if char_length(v_area)>120 or char_length(v_area)<2 then raise exception 'DATING_MEET_AREA_REQUIRED'; end if;
  if private.dating_contains_contact_info(v_area) then raise exception 'DATING_CONTACT_INFO_FORBIDDEN'; end if;
  if lower(btrim(v_area))<>lower(btrim(v_req.meeting_area)) then raise exception 'DATING_MEET_AREA_MISMATCH'; end if;

  select user_id into v_payer_user from public.dating_profiles where id=v_req.payer_profile_id;
  v_balance:=private.sinjira_points_ensure_account(v_payer_user);
  if v_balance<1 then raise exception 'SINJIRA_POINTS_REQUIRED'; end if;

  if v_me=v_a then
    update public.dating_meet_requests set profile_a_consent=true,profile_a_preferences=v_prefs where id=v_req.id returning * into v_req;
  else
    update public.dating_meet_requests set profile_b_consent=true,profile_b_preferences=v_prefs where id=v_req.id returning * into v_req;
  end if;

  if v_req.profile_a_consent and v_req.profile_b_consent then
    perform private.sinjira_points_spend(v_payer_user,1,'safe_meet_recommendation','dating_safe_meet',p_connection_id,jsonb_build_object('module','rencontres'));
    v_recommendation:=private.dating_safe_meet_recommendation(v_req.profile_a_preferences,v_req.profile_b_preferences,v_req.meeting_area);
    update public.dating_meet_requests set status='generated',point_spent=true,recommendation=v_recommendation where id=v_req.id;

    insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
    values
      (v_a_user,'dating','Suggestions pour une rencontre publique','Vous avez tous les deux accepté. Les suggestions de lieu public sont prêtes dans Rencontres.','dating_connection',p_connection_id,'/compte/rencontres.html'),
      (v_b_user,'dating','Suggestions pour une rencontre publique','Vous avez tous les deux accepté. Les suggestions de lieu public sont prêtes dans Rencontres.','dating_connection',p_connection_id,'/compte/rencontres.html');
  else
    insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
    select case when v_me=v_a then v_b_user else v_a_user end,'dating','Proposition de lieu de rencontre','L’autre personne propose de chercher ensemble un lieu public adapté à vos goûts. Aucun Point SINJIRA n’est débité avant votre accord.','dating_connection',p_connection_id,'/compte/rencontres.html';
  end if;

  return public.dating_safe_meet_status(p_connection_id);
end;
$$;

create or replace function public.dating_safe_meet_cancel(p_connection_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare
  v_user uuid:=auth.uid();
  v_me uuid;
  v_req uuid;
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;
  select id into v_me from public.dating_profiles where user_id=v_user;
  select r.id into v_req
  from public.dating_meet_requests r join public.dating_connections c on c.id=r.connection_id
  where r.connection_id=p_connection_id and r.status='waiting' and v_me in(c.profile_a_id,c.profile_b_id)
  for update;
  if v_req is null then raise exception 'DATING_MEET_NOT_CANCELLABLE'; end if;
  update public.dating_meet_requests
  set status='cancelled',profile_a_consent=false,profile_b_consent=false,profile_a_preferences='{}',profile_b_preferences='{}'
  where id=v_req;
  return jsonb_build_object('ok',true,'status','cancelled','point_spent',false);
end;
$$;

revoke all on function public.dating_confirm_single_and_serious(), public.dating_respond_connection(uuid,boolean), public.dating_conversation(uuid), public.dating_set_photo_consent(uuid,boolean), public.sinjira_points_status(), public.dating_safe_meet_status(uuid), public.dating_safe_meet_opt_in(uuid,text[],text), public.dating_safe_meet_cancel(uuid) from public,anon;
grant execute on function public.dating_confirm_single_and_serious(), public.dating_respond_connection(uuid,boolean), public.dating_conversation(uuid), public.dating_set_photo_consent(uuid,boolean), public.sinjira_points_status(), public.dating_safe_meet_status(uuid), public.dating_safe_meet_opt_in(uuid,text[],text), public.dating_safe_meet_cancel(uuid) to authenticated,service_role;

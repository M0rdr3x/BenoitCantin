-- Schéma FICTIF uniquement pour le service PostgreSQL éphémère de GitHub Actions.
-- Ne jamais exécuter ces fixtures sur le projet Supabase réel.
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;
create schema auth;
create schema private;
grant usage on schema public to service_role;
grant usage on schema auth to service_role;
grant usage on schema auth to authenticated;

create table auth.users(id uuid primary key);
create table public.internal_admin_users(user_id uuid primary key references auth.users(id));
create or replace function auth.jwt() returns jsonb
language sql stable set search_path=''
as $$
 select coalesce(nullif(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
$$;
create or replace function public.is_sinjira_admin(p_user_id uuid)
returns boolean language sql stable set search_path=''
as $$
 select p_user_id is not null
   and coalesce(auth.jwt()->>'role','')='service_role'
   and exists(select 1 from public.internal_admin_users a where a.user_id=p_user_id);
$$;

create table public.social_real_posts(id uuid primary key,user_id uuid not null references auth.users(id),body text);
create table public.social_real_comments(id uuid primary key,user_id uuid not null references auth.users(id),body text);
create table public.social_real_messages(id uuid primary key,sender_user_id uuid not null references auth.users(id),body text);
create table public.social_profiles(user_id uuid primary key references auth.users(id));
create table public.social_character_posts(id uuid primary key,user_id uuid not null references auth.users(id),body text);
create table public.social_character_comments(id uuid primary key,user_id uuid not null references auth.users(id),body text);
create table public.social_character_messages(id uuid primary key,sender_user_id uuid not null references auth.users(id),body text);
create table public.character_social_profiles(character_id uuid primary key,user_id uuid not null references auth.users(id));
create table public.dating_profiles(id uuid primary key,user_id uuid not null references auth.users(id));

create table public.social_reports(
 id uuid primary key,
 reporter_user_id uuid not null references auth.users(id),
 network text not null,
 target_type text not null,
 target_id uuid not null,
 reason text not null,
 snapshot jsonb not null default '{}'::jsonb,
 status text not null default 'open',
 created_at timestamptz not null default now(),
 reviewed_at timestamptz,
 reviewed_by uuid references auth.users(id)
);
create table private.moderation_decisions(
 id uuid primary key default gen_random_uuid(),
 subject_user_id uuid references auth.users(id),
 report_id uuid references public.social_reports(id),
 network text not null check(network in ('real','character','dating','account')),
 target_type text not null check(target_type in ('post','comment','message','profile','account')),
 target_id uuid,
 action text not null check(action in ('hide_content','suspend_social','no_action','disable_dating')),
 status text not null default 'active' check(status in ('active','reversed','expired')),
 policy_rule text not null check(char_length(btrim(policy_rule)) between 3 and 240),
 statement_of_reasons text not null check(char_length(btrim(statement_of_reasons)) between 20 and 4000),
 evidence_snapshot jsonb not null default '{}'::jsonb,
 urgency text not null default 'standard' check(urgency in ('standard','urgent_harm','illegal_content')),
 decision_source text not null default 'human_admin' check(decision_source='human_admin'),
 starts_at timestamptz not null default now(),
 ends_at timestamptz,
 appeal_deadline timestamptz not null default (now()+interval '6 months'),
 decided_by uuid references auth.users(id),
 decided_at timestamptz not null default now(),
 reversed_at timestamptz,
 reversed_by uuid references auth.users(id),
 reversal_reason text,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 check(ends_at is null or ends_at>starts_at)
);
create table private.moderation_appeals(
 id uuid primary key default gen_random_uuid(),
 decision_id uuid not null references private.moderation_decisions(id),
 appellant_user_id uuid references auth.users(id),
 appeal_text text not null,
 status text not null default 'pending' check(status in ('pending','upheld','reversed','withdrawn')),
 submitted_at timestamptz not null default now(),
 reviewed_by uuid references auth.users(id),
 reviewed_at timestamptz,
 review_reason text,
 human_review_required boolean not null default true,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(decision_id,appellant_user_id)
);
create table public.social_suspensions(
 user_id uuid primary key references auth.users(id),
 reason text,
 until_at timestamptz,
 created_by uuid references auth.users(id),
 moderation_decision_id uuid references private.moderation_decisions(id)
);
create table public.user_notifications(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id),
 notification_type text not null,
 title text not null check(char_length(title)<=160),
 body text not null check(char_length(body)<=1000),
 related_entity_type text,
 related_entity_id uuid,
 action_path text
);

-- Reproduire le contrôle RLS public : autoriser uniquement le propriétaire
-- d'un signalement fictif, puis ajouter la politique restrictive candidate.
create or replace function auth.uid()
returns uuid language sql stable set search_path=''
as $
  select nullif(auth.jwt()->>'sub','')::uuid;
$;
grant usage on schema public to authenticated;
grant insert on public.social_reports to authenticated;
alter table public.social_reports enable row level security;
create policy social_reports_own_insert on public.social_reports
for insert to authenticated
with check (auth.uid()=reporter_user_id);

alter table private.moderation_decisions enable row level security;
alter table private.moderation_appeals enable row level security;
revoke all on table private.moderation_decisions,private.moderation_appeals from public,anon,authenticated,service_role;

create or replace function public.fixture_assert_true(p_test boolean,p_reason text)
returns void language plpgsql set search_path=''
as $$
begin
 if p_test is distinct from true then raise exception 'FIXTURE_ASSERTION_FAILED: %',p_reason; end if;
end;
$$;

-- Fausse panne après insertion de décision et suspension.
create or replace function public.fixture_fail_notice()
returns trigger language plpgsql set search_path=''
as $$
begin
 if new.body like '%FORCE_ROLLBACK%' then raise exception 'FIXTURE_FORCED_FAILURE'; end if;
 return new;
end;
$$;
create trigger fixture_notification_failure
before insert on public.user_notifications
for each row execute function public.fixture_fail_notice();

insert into auth.users(id) values
 ('aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa'),
 ('bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb'),
 ('cccccccc-cccc-4ccc-cccc-cccccccccccc');
insert into public.internal_admin_users(user_id)
values('aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa');
insert into public.social_real_posts(id,user_id,body)
values('eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb','texte de test');
insert into public.social_reports(
 id,reporter_user_id,network,target_type,target_id,reason
) values
 ('dddddddd-dddd-4ddd-dddd-dddddddddddd','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','threats'),
 ('dddddddd-dddd-4ddd-dddd-ddddddddddde','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','threats'),
 ('dddddddd-dddd-4ddd-dddd-dddddddddddf','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','threats'),
 ('dddddddd-dddd-4ddd-dddd-ddddddddddd0','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','99999999-9999-4999-9999-999999999999','unknown'),
 ('dddddddd-dddd-4ddd-dddd-ddddddddddd1','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','threats'),
 ('dddddddd-dddd-4ddd-dddd-ddddddddddd2','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','threats'),
 ('dddddddd-dddd-4ddd-dddd-ddddddddddd3','cccccccc-cccc-4ccc-cccc-cccccccccccc',
  'real','post','eeeeeeee-eeee-4eee-eeee-eeeeeeeeeeee','threats');

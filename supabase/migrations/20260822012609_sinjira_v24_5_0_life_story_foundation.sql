create table public.life_story_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  entry_type text not null default 'memory' check (entry_type = any (array['childhood','memory','relationship','milestone','travel','passion','choice','value','person','event','anecdote','reflection','other']::text[])),
  title text not null check (char_length(btrim(title)) between 1 and 200),
  body text not null check (char_length(btrim(body)) between 1 and 20000),
  occurred_on date,
  knowledge_status text not null default 'declared_fact' check (knowledge_status = any (array['declared_fact','reflection','reconstruction']::text[])),
  source_kind text not null default 'self_declared' check (source_kind = any (array['self_declared','user_imported','ai_assisted_draft']::text[])),
  approval_status text not null default 'draft' check (approval_status = any (array['draft','approved']::text[])),
  posthumous_disclosure text not null default 'never' check (posthumous_disclosure = any (array['never','selected_versions']::text[])),
  user_approved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint life_story_entries_reconstruction_source check (knowledge_status <> 'reconstruction' or source_kind = 'ai_assisted_draft'),
  constraint life_story_entries_approved_timestamp check (approval_status <> 'approved' or user_approved_at is not null),
  constraint life_story_entries_disclosure_consent check (posthumous_disclosure = 'never' or (approval_status = 'approved' and user_approved_at is not null)),
  unique (id,user_id)
);

create table public.life_story_versions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  audience text not null check (audience = any (array['family','personal','general']::text[])),
  name text not null check (char_length(btrim(name)) between 1 and 120),
  title text check (title is null or char_length(btrim(title)) between 1 and 200),
  instructions text check (instructions is null or char_length(instructions) <= 5000),
  status text not null default 'draft' check (status = any (array['draft','ready']::text[])),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id,user_id),
  unique (user_id,audience)
);

create table public.life_story_version_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  version_id uuid not null,
  entry_id uuid not null,
  sort_order integer not null default 0 check (sort_order >= 0),
  created_at timestamptz not null default now(),
  constraint life_story_version_entries_version_owner_fkey foreign key (version_id,user_id) references public.life_story_versions(id,user_id) on delete cascade,
  constraint life_story_version_entries_entry_owner_fkey foreign key (entry_id,user_id) references public.life_story_entries(id,user_id) on delete cascade,
  unique (version_id,entry_id)
);

create table public.life_story_recipients (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  version_id uuid not null,
  recipient_kind text not null default 'named_contact' check (recipient_kind = any (array['sinjira_user','email','named_contact']::text[])),
  recipient_user_id uuid references auth.users(id) on delete set null,
  recipient_label text not null check (char_length(btrim(recipient_label)) between 1 and 160),
  recipient_email text check (recipient_email is null or char_length(btrim(recipient_email)) between 3 and 320),
  status text not null default 'active' check (status = any (array['active','revoked']::text[])),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint life_story_recipients_version_owner_fkey foreign key (version_id,user_id) references public.life_story_versions(id,user_id) on delete cascade,
  constraint life_story_recipient_shape check (
    (recipient_kind='sinjira_user' and recipient_user_id is not null)
    or (recipient_kind='email' and recipient_email is not null)
    or recipient_kind='named_contact'
  )
);

create table public.life_story_legacy_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  delivery_enabled boolean not null default false,
  output_format text not null default 'pdf' check (output_format='pdf'),
  source_boundary text not null default 'life_story_only' check (source_boundary='life_story_only'),
  death_verification_required boolean not null default true check (death_verification_required=true),
  posthumous_ai_clone_allowed boolean not null default false check (posthumous_ai_clone_allowed=false),
  legacy_directive_review_required boolean not null default false,
  updated_at timestamptz not null default now()
);

comment on table public.life_story_entries is 'Histoire de vie volontaire et privée. Aucune copie automatique du Registre des Consciences.';
comment on table public.life_story_versions is 'Versions de l œuvre biographique préparées par la personne; jamais accès direct au Registre.';
comment on table public.life_story_recipients is 'Destinataires choisis par la personne. Leur présence ne leur accorde aucun accès aux données source.';
comment on table public.life_story_legacy_settings is 'Directive posthume Histoire de vie: PDF uniquement, source Histoire de vie uniquement, vérification de décès obligatoire, clone IA interdit.';

create index life_story_entries_user_updated_idx on public.life_story_entries(user_id,updated_at desc);
create index life_story_entries_user_disclosure_idx on public.life_story_entries(user_id,posthumous_disclosure,approval_status);
create index life_story_versions_user_idx on public.life_story_versions(user_id);
create index life_story_version_entries_user_idx on public.life_story_version_entries(user_id);
create index life_story_version_entries_version_idx on public.life_story_version_entries(version_id,sort_order);
create index life_story_version_entries_entry_idx on public.life_story_version_entries(entry_id);
create index life_story_recipients_user_idx on public.life_story_recipients(user_id,status);
create index life_story_recipients_version_idx on public.life_story_recipients(version_id,status);
create index life_story_recipients_user_target_idx on public.life_story_recipients(recipient_user_id) where recipient_user_id is not null;

create or replace function private.life_story_touch_updated_at()
returns trigger
language plpgsql
set search_path to 'pg_catalog','public','private'
as $$
begin
  new.updated_at=now();
  return new;
end;
$$;

create or replace function private.life_story_validate_version_entry()
returns trigger
language plpgsql
set search_path to 'pg_catalog','public','private'
as $$
begin
  if not exists (
    select 1 from public.life_story_entries e
    where e.id=new.entry_id and e.user_id=new.user_id
      and e.approval_status='approved'
      and e.posthumous_disclosure='selected_versions'
      and e.user_approved_at is not null
  ) then
    raise exception 'LIFE_STORY_ENTRY_NOT_AUTHORIZED';
  end if;
  if not exists (
    select 1 from public.life_story_versions v
    where v.id=new.version_id and v.user_id=new.user_id
  ) then
    raise exception 'LIFE_STORY_VERSION_NOT_OWNED';
  end if;
  return new;
end;
$$;

create or replace function private.life_story_remove_private_mappings()
returns trigger
language plpgsql
set search_path to 'pg_catalog','public','private'
as $$
begin
  if new.posthumous_disclosure<>'selected_versions' or new.approval_status<>'approved' or new.user_approved_at is null then
    delete from public.life_story_version_entries where entry_id=new.id and user_id=new.user_id;
  end if;
  return new;
end;
$$;

create trigger life_story_entries_touch before update on public.life_story_entries for each row execute function private.life_story_touch_updated_at();
create trigger life_story_versions_touch before update on public.life_story_versions for each row execute function private.life_story_touch_updated_at();
create trigger life_story_recipients_touch before update on public.life_story_recipients for each row execute function private.life_story_touch_updated_at();
create trigger life_story_settings_touch before update on public.life_story_legacy_settings for each row execute function private.life_story_touch_updated_at();
create trigger life_story_version_entry_guard before insert or update on public.life_story_version_entries for each row execute function private.life_story_validate_version_entry();
create trigger life_story_entry_privacy_cleanup after update of approval_status,posthumous_disclosure,user_approved_at on public.life_story_entries for each row execute function private.life_story_remove_private_mappings();

revoke all on function private.life_story_touch_updated_at() from public,anon,authenticated;
revoke all on function private.life_story_validate_version_entry() from public,anon,authenticated;
revoke all on function private.life_story_remove_private_mappings() from public,anon,authenticated;

alter table public.life_story_entries enable row level security;
alter table public.life_story_versions enable row level security;
alter table public.life_story_version_entries enable row level security;
alter table public.life_story_recipients enable row level security;
alter table public.life_story_legacy_settings enable row level security;

create policy life_story_entries_own on public.life_story_entries for all to authenticated
using ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy life_story_versions_own on public.life_story_versions for all to authenticated
using ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy life_story_version_entries_own on public.life_story_version_entries for all to authenticated
using ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy life_story_recipients_own on public.life_story_recipients for all to authenticated
using ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())));
create policy life_story_legacy_settings_own on public.life_story_legacy_settings for all to authenticated
using ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())))
with check ((select auth.uid())=user_id and public.sinjira_mfa_access_allowed((select auth.uid())));

revoke all on public.life_story_entries,public.life_story_versions,public.life_story_version_entries,public.life_story_recipients,public.life_story_legacy_settings from public,anon;
grant select,insert,update,delete on public.life_story_entries,public.life_story_versions,public.life_story_version_entries,public.life_story_recipients to authenticated;
grant select,insert,update on public.life_story_legacy_settings to authenticated;

insert into public.life_story_legacy_settings(user_id,legacy_directive_review_required)
select user_id,true from public.legacy_directives
on conflict (user_id) do nothing;

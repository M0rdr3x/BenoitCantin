-- SINJIRA™ V25.0 — Registre personnel des consciences
-- IMPORTANT : ce coffre concerne la personne réelle. Il est distinct du Registre narratif SINJIRA.
-- Principe : L'HUMAIN AVANT TOUT. Le contenu intime n'est jamais une donnée d'héritage.
-- Aucun accès direct navigateur/mobile n'est accordé aux tables privées.
-- L'accès passe par une session courte, AAL2 obligatoire et risque V25 approuvé.

begin;

create table if not exists private.conscience_entries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  entry_type text not null default 'reflection'
    check (char_length(entry_type) between 1 and 64),
  content_payload text not null
    check (octet_length(content_payload) between 1 and 1048576),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists conscience_entries_user_created_idx
  on private.conscience_entries(user_id, created_at desc);

comment on table private.conscience_entries is
  'Coffre personnel réel, distinct du Registre narratif. Contenu privé serveur uniquement; aucune promesse E2EE n est faite par ce schéma.';
comment on column private.conscience_entries.content_payload is
  'Contenu intime. Ne jamais copier vers Histoire de vie, héritage, journal sécurité, analytics, publicité ou recommandation.';

create table if not exists private.conscience_vault_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  scope text not null default 'conscience_vault'
    check (scope = 'conscience_vault'),
  aal text not null check (aal = 'aal2'),
  risk_score smallint not null check (risk_score between 0 and 74),
  risk_band text not null check (risk_band in ('low','medium','high')),
  risk_outcome text not null check (risk_outcome in ('allow','approved')),
  risk_model_version text not null check (risk_model_version = 'v25.0'),
  issued_at timestamptz not null default now(),
  expires_at timestamptz not null,
  last_used_at timestamptz,
  revoked_at timestamptz,
  check (expires_at > issued_at),
  check (expires_at <= issued_at + interval '10 minutes')
);
create index if not exists conscience_vault_sessions_user_active_idx
  on private.conscience_vault_sessions(user_id, expires_at desc)
  where revoked_at is null;

comment on table private.conscience_vault_sessions is
  'Capacités temporaires du coffre. AAL2 est obligatoire et non désactivable; Mode Voyage/appareil fiable ne le suppriment jamais.';

create table if not exists private.conscience_vault_audit (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid references private.conscience_vault_sessions(id) on delete set null,
  entry_id uuid,
  event_type text not null check (event_type in (
    'session_open','session_revoke','entries_list','entry_create','entry_update','entry_delete'
  )),
  occurred_at timestamptz not null default now()
);
create index if not exists conscience_vault_audit_user_time_idx
  on private.conscience_vault_audit(user_id, occurred_at desc);

comment on table private.conscience_vault_audit is
  'Audit métadonnées seulement. Aucun contenu, résumé intime, IP brute, GPS ou texte du Registre n y est journalisé.';

alter table private.conscience_entries enable row level security;
alter table private.conscience_vault_sessions enable row level security;
alter table private.conscience_vault_audit enable row level security;

-- Même service_role n'obtient aucun accès direct aux tables : les seules voies prévues
-- sont les fonctions SECURITY DEFINER étroites ci-dessous.
revoke all on table private.conscience_entries from public, anon, authenticated, service_role;
revoke all on table private.conscience_vault_sessions from public, anon, authenticated, service_role;
revoke all on table private.conscience_vault_audit from public, anon, authenticated, service_role;

create or replace function private.conscience_vault_require_service_role()
returns void
language plpgsql
security definer
set search_path = pg_catalog, auth, private
as $$
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED' using errcode='42501';
  end if;
end;
$$;
revoke all on function private.conscience_vault_require_service_role() from public, anon, authenticated, service_role;

create or replace function private.conscience_vault_assert_session(
  p_user_id uuid,
  p_session_id uuid
)
returns void
language plpgsql
security definer
set search_path = pg_catalog, private
as $$
begin
  if p_user_id is null or p_session_id is null then
    raise exception 'VAULT_SESSION_REQUIRED' using errcode='42501';
  end if;

  update private.conscience_vault_sessions
     set last_used_at = now()
   where id = p_session_id
     and user_id = p_user_id
     and revoked_at is null
     and expires_at > now();

  if not found then
    raise exception 'VAULT_SESSION_INVALID' using errcode='42501';
  end if;
end;
$$;
revoke all on function private.conscience_vault_assert_session(uuid,uuid) from public, anon, authenticated, service_role;

create or replace function public.service_conscience_open_session(
  p_user_id uuid,
  p_aal text,
  p_risk_score integer,
  p_risk_outcome text,
  p_risk_model_version text default 'v25.0',
  p_ttl_seconds integer default 300
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_id uuid;
  v_band text;
begin
  perform private.conscience_vault_require_service_role();

  -- AAL2 reste obligatoire même si la préférence sensitive_step_up est désactivée.
  if p_aal is distinct from 'aal2' then
    raise exception 'AAL2_REQUIRED' using errcode='42501';
  end if;
  if p_risk_model_version is distinct from 'v25.0' then
    raise exception 'RISK_MODEL_V25_REQUIRED' using errcode='42501';
  end if;
  if p_risk_outcome is null or p_risk_outcome not in ('allow','approved') then
    raise exception 'RISK_APPROVAL_REQUIRED' using errcode='42501';
  end if;
  if p_risk_score is null or p_risk_score < 0 or p_risk_score >= 75 then
    raise exception 'RISK_NOT_ACCEPTABLE' using errcode='42501';
  end if;
  if p_ttl_seconds is null or p_ttl_seconds < 60 or p_ttl_seconds > 600 then
    raise exception 'VAULT_TTL_INVALID' using errcode='22023';
  end if;
  if p_user_id is null or not exists(select 1 from auth.users where id=p_user_id) then
    raise exception 'VAULT_USER_INVALID' using errcode='22023';
  end if;

  v_band := case
    when p_risk_score <= 24 then 'low'
    when p_risk_score <= 49 then 'medium'
    else 'high'
  end;

  -- Une seule capacité active à la fois par personne.
  update private.conscience_vault_sessions
     set revoked_at = now()
   where user_id = p_user_id
     and revoked_at is null
     and expires_at > now();

  insert into private.conscience_vault_sessions(
    user_id, aal, risk_score, risk_band, risk_outcome, risk_model_version, expires_at
  ) values(
    p_user_id, 'aal2', p_risk_score, v_band, p_risk_outcome, 'v25.0',
    now() + make_interval(secs => p_ttl_seconds)
  ) returning id into v_id;

  insert into private.conscience_vault_audit(user_id,session_id,event_type)
  values(p_user_id,v_id,'session_open');

  return v_id;
end;
$$;

create or replace function public.service_conscience_revoke_session(
  p_user_id uuid,
  p_session_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
begin
  perform private.conscience_vault_require_service_role();

  update private.conscience_vault_sessions
     set revoked_at = coalesce(revoked_at,now())
   where id=p_session_id and user_id=p_user_id and revoked_at is null;

  if not found then
    return false;
  end if;

  insert into private.conscience_vault_audit(user_id,session_id,event_type)
  values(p_user_id,p_session_id,'session_revoke');
  return true;
end;
$$;

create or replace function public.service_conscience_list_entries(
  p_user_id uuid,
  p_session_id uuid
)
returns table(
  id uuid,
  entry_type text,
  content_payload text,
  created_at timestamptz,
  updated_at timestamptz
)
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_session(p_user_id,p_session_id);

  insert into private.conscience_vault_audit(user_id,session_id,event_type)
  values(p_user_id,p_session_id,'entries_list');

  return query
  select e.id,e.entry_type,e.content_payload,e.created_at,e.updated_at
  from private.conscience_entries e
  where e.user_id=p_user_id
  order by e.created_at desc;
end;
$$;

create or replace function public.service_conscience_create_entry(
  p_user_id uuid,
  p_session_id uuid,
  p_entry_type text,
  p_content_payload text
)
returns uuid
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
declare
  v_id uuid;
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_session(p_user_id,p_session_id);

  if p_entry_type is null or char_length(trim(p_entry_type)) not between 1 and 64 then
    raise exception 'VAULT_ENTRY_TYPE_INVALID' using errcode='22023';
  end if;
  if p_content_payload is null or octet_length(p_content_payload) not between 1 and 1048576 then
    raise exception 'VAULT_ENTRY_CONTENT_INVALID' using errcode='22023';
  end if;

  insert into private.conscience_entries(user_id,entry_type,content_payload)
  values(p_user_id,left(trim(p_entry_type),64),p_content_payload)
  returning id into v_id;

  insert into private.conscience_vault_audit(user_id,session_id,entry_id,event_type)
  values(p_user_id,p_session_id,v_id,'entry_create');

  return v_id;
end;
$$;

create or replace function public.service_conscience_update_entry(
  p_user_id uuid,
  p_session_id uuid,
  p_entry_id uuid,
  p_entry_type text,
  p_content_payload text
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_session(p_user_id,p_session_id);

  if p_entry_type is null or char_length(trim(p_entry_type)) not between 1 and 64 then
    raise exception 'VAULT_ENTRY_TYPE_INVALID' using errcode='22023';
  end if;
  if p_content_payload is null or octet_length(p_content_payload) not between 1 and 1048576 then
    raise exception 'VAULT_ENTRY_CONTENT_INVALID' using errcode='22023';
  end if;

  update private.conscience_entries
     set entry_type=left(trim(p_entry_type),64),
         content_payload=p_content_payload,
         updated_at=now()
   where id=p_entry_id and user_id=p_user_id;

  if not found then
    return false;
  end if;

  insert into private.conscience_vault_audit(user_id,session_id,entry_id,event_type)
  values(p_user_id,p_session_id,p_entry_id,'entry_update');
  return true;
end;
$$;

create or replace function public.service_conscience_delete_entry(
  p_user_id uuid,
  p_session_id uuid,
  p_entry_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = pg_catalog, public, private, auth
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_session(p_user_id,p_session_id);

  delete from private.conscience_entries
   where id=p_entry_id and user_id=p_user_id;

  if not found then
    return false;
  end if;

  insert into private.conscience_vault_audit(user_id,session_id,entry_id,event_type)
  values(p_user_id,p_session_id,p_entry_id,'entry_delete');
  return true;
end;
$$;

revoke all on function public.service_conscience_open_session(uuid,text,integer,text,text,integer) from public, anon, authenticated;
revoke all on function public.service_conscience_revoke_session(uuid,uuid) from public, anon, authenticated;
revoke all on function public.service_conscience_list_entries(uuid,uuid) from public, anon, authenticated;
revoke all on function public.service_conscience_create_entry(uuid,uuid,text,text) from public, anon, authenticated;
revoke all on function public.service_conscience_update_entry(uuid,uuid,uuid,text,text) from public, anon, authenticated;
revoke all on function public.service_conscience_delete_entry(uuid,uuid,uuid) from public, anon, authenticated;

grant execute on function public.service_conscience_open_session(uuid,text,integer,text,text,integer) to service_role;
grant execute on function public.service_conscience_revoke_session(uuid,uuid) to service_role;
grant execute on function public.service_conscience_list_entries(uuid,uuid) to service_role;
grant execute on function public.service_conscience_create_entry(uuid,uuid,text,text) to service_role;
grant execute on function public.service_conscience_update_entry(uuid,uuid,uuid,text,text) to service_role;
grant execute on function public.service_conscience_delete_entry(uuid,uuid,uuid) to service_role;

comment on function public.service_conscience_open_session(uuid,text,integer,text,text,integer) is
  'Serveur seulement. Exige AAL2, décision de risque V25 approuvée et capacité <=10 min. Le périmètre attendu du moteur est conscience_vault.';
comment on function public.service_conscience_list_entries(uuid,uuid) is
  'Serveur seulement. Jamais utilisé par le pipeline Histoire de vie/héritage.';
comment on function public.service_conscience_create_entry(uuid,uuid,text,text) is
  'Serveur seulement. Le contenu du Registre personnel ne doit jamais être copié vers un PDF posthume.';

commit;

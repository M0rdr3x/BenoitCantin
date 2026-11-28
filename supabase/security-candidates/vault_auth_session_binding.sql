-- CANDIDATE ONLY: isolated rehearsal, not a canonical migration.
-- Legacy service grants are removed; coordinated Edge rollout is required.
begin;
set local lock_timeout = '5s';
set local statement_timeout = '60s';
alter table private.conscience_vault_sessions add column auth_session_id uuid;
-- Preserve audit history; invalidate capabilities created without origin binding.
update private.conscience_vault_sessions set revoked_at=now() where revoked_at is null;
comment on column private.conscience_vault_sessions.auth_session_id is
  'Verified Auth session UUID at issuance; no FK so revocation preserves audit history. Live check is mandatory.';

create function private.conscience_vault_require_live_auth(p_user_id uuid,p_auth_session_id uuid)
returns void language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform 1 from auth.sessions s
   where s.id=p_auth_session_id and s.user_id=p_user_id and s.aal::text='aal2'
     and (s.not_after is null or s.not_after > clock_timestamp())
   for share;
  if not found then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
end;
$$;
revoke all on function private.conscience_vault_require_live_auth(uuid,uuid) from public,anon,authenticated,service_role;

create function private.conscience_vault_assert_bound(p_user_id uuid,p_session_id uuid,p_auth_session_id uuid)
returns void language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform private.conscience_vault_require_live_auth(p_user_id,p_auth_session_id);
  perform 1 from private.conscience_vault_sessions v
   where v.id=p_session_id and v.user_id=p_user_id and v.auth_session_id=p_auth_session_id
     and v.revoked_at is null and v.expires_at > clock_timestamp()
   for update;
  if not found then raise exception 'VAULT_SESSION_INVALID' using errcode='42501'; end if;
end;
$$;
revoke all on function private.conscience_vault_assert_bound(uuid,uuid,uuid) from public,anon,authenticated,service_role;

create function public.service_conscience_open_session_bound(p_user_id uuid, p_auth_session_id uuid, p_aal text, p_risk_score integer, p_risk_outcome text, p_risk_action text, p_risk_model_version text, p_ttl_seconds integer)
returns uuid language plpgsql security definer set search_path = pg_catalog
as $$
declare v_id uuid;
begin
  perform private.conscience_vault_require_service_role();
  -- Serialize concurrent opens for the same account before rotating its capability.
  perform 1 from auth.users u where u.id=p_user_id for no key update;
  if not found then raise exception 'AUTH_REQUIRED' using errcode='42501'; end if;
  perform private.conscience_vault_require_live_auth(p_user_id,p_auth_session_id);
  v_id := public.service_conscience_open_session(p_user_id,p_aal,p_risk_score,p_risk_outcome,p_risk_action,p_risk_model_version,p_ttl_seconds);
  update private.conscience_vault_sessions set auth_session_id=p_auth_session_id where id=v_id and user_id=p_user_id;
  if not found then raise exception 'VAULT_SESSION_INVALID' using errcode='42501'; end if;
  return v_id;
end;
$$;
revoke all on function public.service_conscience_open_session_bound(uuid,uuid,text,integer,text,text,text,integer) from public,anon,authenticated,service_role;
grant execute on function public.service_conscience_open_session_bound(uuid,uuid,text,integer,text,text,text,integer) to service_role;
revoke all on function public.service_conscience_open_session(uuid,text,integer,text,text,text,integer) from public,anon,authenticated,service_role;

create function public.service_conscience_list_entries_bound(p_user_id uuid, p_session_id uuid, p_auth_session_id uuid)
returns table(id uuid, entry_type text, content_payload text, created_at timestamptz, updated_at timestamptz) language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_bound(p_user_id,p_session_id,p_auth_session_id);
  return query select * from public.service_conscience_list_entries(p_user_id,p_session_id);
end;
$$;
revoke all on function public.service_conscience_list_entries_bound(uuid,uuid,uuid) from public,anon,authenticated,service_role;
grant execute on function public.service_conscience_list_entries_bound(uuid,uuid,uuid) to service_role;
revoke all on function public.service_conscience_list_entries(uuid,uuid) from public,anon,authenticated,service_role;

create function public.service_conscience_create_entry_bound(p_user_id uuid, p_session_id uuid, p_auth_session_id uuid, p_entry_type text, p_content_payload text)
returns uuid language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_bound(p_user_id,p_session_id,p_auth_session_id);
  return public.service_conscience_create_entry(p_user_id,p_session_id,p_entry_type,p_content_payload);
end;
$$;
revoke all on function public.service_conscience_create_entry_bound(uuid,uuid,uuid,text,text) from public,anon,authenticated,service_role;
grant execute on function public.service_conscience_create_entry_bound(uuid,uuid,uuid,text,text) to service_role;
revoke all on function public.service_conscience_create_entry(uuid,uuid,text,text) from public,anon,authenticated,service_role;

create function public.service_conscience_update_entry_bound(p_user_id uuid, p_session_id uuid, p_auth_session_id uuid, p_entry_id uuid, p_entry_type text, p_content_payload text)
returns boolean language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_bound(p_user_id,p_session_id,p_auth_session_id);
  return public.service_conscience_update_entry(p_user_id,p_session_id,p_entry_id,p_entry_type,p_content_payload);
end;
$$;
revoke all on function public.service_conscience_update_entry_bound(uuid,uuid,uuid,uuid,text,text) from public,anon,authenticated,service_role;
grant execute on function public.service_conscience_update_entry_bound(uuid,uuid,uuid,uuid,text,text) to service_role;
revoke all on function public.service_conscience_update_entry(uuid,uuid,uuid,text,text) from public,anon,authenticated,service_role;

create function public.service_conscience_delete_entry_bound(p_user_id uuid, p_session_id uuid, p_auth_session_id uuid, p_entry_id uuid)
returns boolean language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_assert_bound(p_user_id,p_session_id,p_auth_session_id);
  return public.service_conscience_delete_entry(p_user_id,p_session_id,p_entry_id);
end;
$$;
revoke all on function public.service_conscience_delete_entry_bound(uuid,uuid,uuid,uuid) from public,anon,authenticated,service_role;
grant execute on function public.service_conscience_delete_entry_bound(uuid,uuid,uuid,uuid) to service_role;
revoke all on function public.service_conscience_delete_entry(uuid,uuid,uuid) from public,anon,authenticated,service_role;

create function public.service_conscience_revoke_session_bound(p_user_id uuid, p_session_id uuid, p_auth_session_id uuid)
returns boolean language plpgsql security definer set search_path = pg_catalog
as $$
begin
  perform private.conscience_vault_require_service_role();
  perform private.conscience_vault_require_live_auth(p_user_id,p_auth_session_id);
  perform 1 from private.conscience_vault_sessions v
   where v.id=p_session_id and v.user_id=p_user_id and v.auth_session_id=p_auth_session_id
     and v.revoked_at is null for update;
  if not found then return false; end if;
  return public.service_conscience_revoke_session(p_user_id,p_session_id);
end;
$$;
revoke all on function public.service_conscience_revoke_session_bound(uuid,uuid,uuid) from public,anon,authenticated,service_role;
grant execute on function public.service_conscience_revoke_session_bound(uuid,uuid,uuid) to service_role;
revoke all on function public.service_conscience_revoke_session(uuid,uuid) from public,anon,authenticated,service_role;

commit;

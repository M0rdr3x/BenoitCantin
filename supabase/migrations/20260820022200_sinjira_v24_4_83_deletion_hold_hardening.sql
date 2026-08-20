-- SINJIRA™ V24.4.83 — suppression de compte compatible avec les obligations de conservation.
-- Une conservation légale active bloque explicitement l'autosuppression; les journaux de traitement
-- restent conservables sans empêcher une suppression ordinaire lorsqu'aucun hold n'est actif.

-- Les demandes de vie privée servent aussi de trace de traitement. Elles ne doivent pas disparaître
-- uniquement parce que le compte a ensuite été supprimé.
alter table private.privacy_requests alter column user_id drop not null;
alter table private.privacy_requests drop constraint if exists privacy_requests_user_id_fkey;
alter table private.privacy_requests
  add constraint privacy_requests_user_id_fkey foreign key(user_id) references auth.users(id) on delete set null;

-- Un dossier d'escalade doit pouvoir subsister comme trace de triage sans bloquer à lui seul
-- une suppression de compte. Une vraie obligation de conservation est représentée par privacy_legal_holds.
alter table private.safety_escalation_cases alter column source_report_id drop not null;
alter table private.safety_escalation_cases drop constraint if exists safety_escalation_cases_source_report_id_fkey;
alter table private.safety_escalation_cases
  add constraint safety_escalation_cases_source_report_id_fkey foreign key(source_report_id) references public.social_reports(id) on delete set null;

create or replace function private.privacy_has_active_legal_hold(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,private
as $$
select exists(
  select 1
  from private.privacy_legal_holds h
  where h.user_id=p_user_id
    and h.released_at is null
    and h.starts_at<=now()
    and (h.expires_at is null or h.expires_at>now())
);
$$;

revoke all on function private.privacy_has_active_legal_hold(uuid) from public,anon,authenticated;
grant execute on function private.privacy_has_active_legal_hold(uuid) to service_role;

-- RPC service-only utilisée par l'Edge Function de suppression; ne révèle pas l'existence d'un hold au navigateur.
create or replace function public.privacy_service_can_delete_user(p_user_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public,private
as $$
select not private.privacy_has_active_legal_hold(p_user_id);
$$;
revoke all on function public.privacy_service_can_delete_user(uuid) from public,anon,authenticated;
grant execute on function public.privacy_service_can_delete_user(uuid) to service_role;

comment on function public.privacy_service_can_delete_user(uuid) is
'Contrat service-only: refuse une suppression de compte lorsqu’une conservation légale documentée est active.';

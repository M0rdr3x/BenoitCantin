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

-- Complément serveur à l'export navigateur historique. Il couvre les modules privés ajoutés après V24.4.70
-- sans ouvrir les tables Dating/Points au navigateur. Les snapshots de signalement pouvant contenir
-- des renseignements sur une autre personne ne sont pas inclus dans l'export automatique.
create or replace function public.privacy_export_my_extended_data()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v_user uuid:=auth.uid();
  v_profile uuid;
  v_connections uuid[]:='{}'::uuid[];
begin
  if v_user is null then raise exception 'AUTH_REQUIRED'; end if;

  select p.id into v_profile from public.dating_profiles p where p.user_id=v_user;
  if v_profile is not null then
    select coalesce(array_agg(c.id),'{}'::uuid[])
      into v_connections
    from public.dating_connections c
    where v_profile in(c.profile_a_id,c.profile_b_id);
  end if;

  return jsonb_build_object(
    'privacy_requests',coalesce((
      select jsonb_agg(to_jsonb(r)-'user_id' order by r.created_at)
      from private.privacy_requests r where r.user_id=v_user
    ),'[]'::jsonb),
    'points_account',(
      select to_jsonb(a)-'user_id' from public.sinjira_points_accounts a where a.user_id=v_user
    ),
    'points_ledger',coalesce((
      select jsonb_agg(to_jsonb(l)-'user_id' order by l.created_at)
      from public.sinjira_points_ledger l where l.user_id=v_user
    ),'[]'::jsonb),
    'dating_profile',(
      select to_jsonb(p)-'user_id' from public.dating_profiles p where p.user_id=v_user
    ),
    'dating_preferences',(
      select to_jsonb(d)-'user_id' from public.dating_preferences d where d.user_id=v_user
    ),
    'dating_connections',coalesce((
      select jsonb_agg(to_jsonb(c) order by c.created_at)
      from public.dating_connections c where c.id=any(v_connections)
    ),'[]'::jsonb),
    'dating_messages',coalesce((
      select jsonb_agg(to_jsonb(m) order by m.created_at)
      from public.dating_messages m where m.connection_id=any(v_connections)
    ),'[]'::jsonb),
    'dating_meet_requests',coalesce((
      select jsonb_agg(to_jsonb(mr) order by mr.created_at)
      from public.dating_meet_requests mr where mr.connection_id=any(v_connections)
    ),'[]'::jsonb),
    'reports_submitted',coalesce((
      select jsonb_agg((to_jsonb(r)-'reporter_user_id'-'snapshot') order by r.created_at)
      from public.social_reports r where r.reporter_user_id=v_user
    ),'[]'::jsonb)
  );
end;
$$;

revoke all on function public.privacy_export_my_extended_data() from public,anon;
grant execute on function public.privacy_export_my_extended_data() to authenticated,service_role;

comment on function public.privacy_service_can_delete_user(uuid) is
'Contrat service-only: refuse une suppression de compte lorsqu’une conservation légale documentée est active.';
comment on function public.privacy_export_my_extended_data() is
'Complément self-only de l’export utilisateur: demandes vie privée, Points SINJIRA, Rencontres/Safe Meet et métadonnées de signalements, sans snapshots tiers.';

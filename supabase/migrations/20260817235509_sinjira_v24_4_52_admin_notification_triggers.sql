-- SINJIRA V24.4.52 — notifications administratives transactionnelles.
-- Les événements importants créent désormais un avis interne au moment exact
-- où la donnée métier est enregistrée/soumise.

create or replace function public.notify_sinjira_admin_access_request()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare
  v_pseudo text;
  v_project text;
begin
  if new.status <> 'pending' then return new; end if;
  select coalesce(p.pseudo,p.display_name,'Compte SINJIRA™') into v_pseudo
  from public.profiles p where p.user_id=new.user_id;
  select coalesce(pr.name,'Projet SINJIRA™') into v_project
  from public.projects pr where pr.id=new.project_id;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
  values(
    case when new.requested_level='tester' then 'tester_request' else 'access_request' end,
    case when new.requested_level='tester' then 'Nouvelle demande testeur' else 'Nouvelle demande d’accès' end,
    coalesce(v_pseudo,'Compte SINJIRA™') || ' demande le niveau « ' || new.requested_level || ' » pour ' || coalesce(v_project,'un projet') || '.',
    new.user_id,'access_request',new.id
  );
  return new;
end;
$$;

create or replace function public.notify_sinjira_admin_novel_comment()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
begin
  if new.status <> 'pending' then return new; end if;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
  values(
    'novel_comment','Nouveau commentaire roman à modérer',
    coalesce(nullif(new.display_name_snapshot,''),'Lecteur SINJIRA™') || ' a soumis un commentaire en attente de modération.',
    new.user_id,'novel_comment',new.id
  );
  return new;
end;
$$;

create or replace function public.notify_sinjira_admin_social_report()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
begin
  if new.status <> 'open' then return new; end if;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
  values(
    'social_report','Nouveau signalement social',
    'Signalement « ' || new.network || ' » concernant un élément de type « ' || new.target_type || ' ».',
    new.reporter_user_id,'social_report',new.id
  );
  return new;
end;
$$;

create or replace function public.notify_sinjira_admin_fracture_report()
returns trigger
language plpgsql
security definer
set search_path=public
as $$
declare
  v_party_code text;
begin
  if new.submitted_at is null then return new; end if;
  if tg_op='UPDATE' and old.submitted_at is not null then return new; end if;
  select fp.party_code into v_party_code from public.fracture_parties fp where fp.id=new.party_id;
  insert into public.admin_notifications(notification_type,title,body,related_user_id,related_entity_type,related_entity_id)
  values(
    'fracture_report','Nouveau rapport Fracture du Réseau-Mère',
    'Une feuille de fin de partie a été transmise' || case when v_party_code is not null then ' pour la partie ' || v_party_code else '' end || '.',
    new.owner_user_id,'fracture_endgame_report',new.id
  );
  return new;
end;
$$;

revoke all on function public.notify_sinjira_admin_access_request() from public,anon,authenticated;
revoke all on function public.notify_sinjira_admin_novel_comment() from public,anon,authenticated;
revoke all on function public.notify_sinjira_admin_social_report() from public,anon,authenticated;
revoke all on function public.notify_sinjira_admin_fracture_report() from public,anon,authenticated;

drop trigger if exists trg_admin_notify_access_request on public.access_requests;
create trigger trg_admin_notify_access_request
after insert on public.access_requests
for each row execute function public.notify_sinjira_admin_access_request();

drop trigger if exists trg_admin_notify_novel_comment on public.novel_comments;
create trigger trg_admin_notify_novel_comment
after insert on public.novel_comments
for each row execute function public.notify_sinjira_admin_novel_comment();

drop trigger if exists trg_admin_notify_social_report on public.social_reports;
create trigger trg_admin_notify_social_report
after insert on public.social_reports
for each row execute function public.notify_sinjira_admin_social_report();

drop trigger if exists trg_admin_notify_fracture_report_insert on public.fracture_endgame_reports;
create trigger trg_admin_notify_fracture_report_insert
after insert on public.fracture_endgame_reports
for each row when (new.submitted_at is not null)
execute function public.notify_sinjira_admin_fracture_report();

drop trigger if exists trg_admin_notify_fracture_report_submit on public.fracture_endgame_reports;
create trigger trg_admin_notify_fracture_report_submit
after update of submitted_at on public.fracture_endgame_reports
for each row when (old.submitted_at is null and new.submitted_at is not null)
execute function public.notify_sinjira_admin_fracture_report();

create or replace function public.sinjira_admin_notifications_health()
returns jsonb
language sql
stable
security invoker
set search_path=public
as $$
  select jsonb_build_object(
    'ok',
      exists(select 1 from pg_trigger where tgname='trg_admin_notify_access_request' and not tgisinternal) and
      exists(select 1 from pg_trigger where tgname='trg_admin_notify_novel_comment' and not tgisinternal) and
      exists(select 1 from pg_trigger where tgname='trg_admin_notify_social_report' and not tgisinternal) and
      exists(select 1 from pg_trigger where tgname='trg_admin_notify_fracture_report_insert' and not tgisinternal) and
      exists(select 1 from pg_trigger where tgname='trg_admin_notify_fracture_report_submit' and not tgisinternal),
    'access_request',exists(select 1 from pg_trigger where tgname='trg_admin_notify_access_request' and not tgisinternal),
    'novel_comment',exists(select 1 from pg_trigger where tgname='trg_admin_notify_novel_comment' and not tgisinternal),
    'social_report',exists(select 1 from pg_trigger where tgname='trg_admin_notify_social_report' and not tgisinternal),
    'fracture_insert',exists(select 1 from pg_trigger where tgname='trg_admin_notify_fracture_report_insert' and not tgisinternal),
    'fracture_submit',exists(select 1 from pg_trigger where tgname='trg_admin_notify_fracture_report_submit' and not tgisinternal),
    'version','24.4.52'
  );
$$;
revoke all on function public.sinjira_admin_notifications_health() from public,anon,authenticated;
grant execute on function public.sinjira_admin_notifications_health() to service_role;

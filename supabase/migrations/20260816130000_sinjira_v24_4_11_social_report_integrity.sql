-- SINJIRA™ V24.4.11 — intégrité et confidentialité des signalements sociaux
-- Un signalement ne doit jamais pouvoir fabriquer sa cible, son état administratif
-- ni son snapshot depuis le navigateur. Le pont identité narrative -> compte réel
-- reste exclusivement côté serveur.

create or replace function public.get_sinjira_server_version()
returns text
language sql
stable
security definer
set search_path=public
as $$ select '24.4.11'::text; $$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

create table if not exists public.social_report_targets(
  report_id uuid primary key references public.social_reports(id) on delete cascade,
  target_user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);
alter table public.social_report_targets enable row level security;
revoke all on public.social_report_targets from public,anon,authenticated;
grant select,insert,update,delete on public.social_report_targets to service_role;
create index if not exists social_report_targets_user_idx
  on public.social_report_targets(target_user_id,created_at desc);

create or replace function public.canonicalize_social_report()
returns trigger
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  target_user uuid;
  sender_user uuid;
  recipient_user uuid;
  character_ref uuid;
  target_body text;
  target_created timestamptz;
  target_pseudo text;
  target_display text;
  target_name text;
begin
  if uid is null or new.reporter_user_id is distinct from uid then
    raise exception 'REPORTER_MISMATCH';
  end if;

  new.reason:=btrim(coalesce(new.reason,''));
  if char_length(new.reason)<3 or char_length(new.reason)>1000 then
    raise exception 'INVALID_REPORT_REASON';
  end if;

  -- Les champs de revue sont exclusivement administratifs. Même si un client modifié
  -- les envoie dans l'INSERT, le serveur repart toujours d'un signalement ouvert neuf.
  new.status:='open';
  new.reviewed_at:=null;
  new.reviewed_by:=null;
  new.created_at:=now();

  if new.network='real' and new.target_type='post' then
    select p.user_id,p.body,p.created_at
      into target_user,target_body,target_created
      from public.social_real_posts p where p.id=new.target_id;
    if target_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if target_user=uid then raise exception 'CANNOT_REPORT_SELF'; end if;
    new.snapshot:=jsonb_build_object(
      'body',left(coalesce(target_body,''),3000),
      'created_at',target_created
    );

  elsif new.network='real' and new.target_type='comment' then
    select c.user_id,c.body,c.created_at
      into target_user,target_body,target_created
      from public.social_real_comments c where c.id=new.target_id;
    if target_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if target_user=uid then raise exception 'CANNOT_REPORT_SELF'; end if;
    new.snapshot:=jsonb_build_object(
      'body',left(coalesce(target_body,''),1000),
      'created_at',target_created
    );

  elsif new.network='real' and new.target_type='message' then
    select m.sender_user_id,m.recipient_user_id,m.body,m.created_at
      into sender_user,recipient_user,target_body,target_created
      from public.social_real_messages m where m.id=new.target_id;
    if sender_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    -- Seul le destinataire peut signaler le message reçu. Cela empêche un UUID deviné
    -- de devenir un canal de lecture d'un message privé via le snapshot du signalement.
    if recipient_user is distinct from uid or sender_user=uid then
      raise exception 'REPORT_MESSAGE_NOT_RECEIVED';
    end if;
    target_user:=sender_user;
    new.snapshot:=jsonb_build_object(
      'body',left(coalesce(target_body,''),4000),
      'created_at',target_created
    );

  elsif new.network='real' and new.target_type='profile' then
    select p.user_id,p.pseudo,p.display_name
      into target_user,target_pseudo,target_display
      from public.social_profiles p where p.user_id=new.target_id;
    if target_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if target_user=uid then raise exception 'CANNOT_REPORT_SELF'; end if;
    new.snapshot:=jsonb_build_object(
      'pseudo',left(coalesce(target_pseudo,''),120),
      'display_name',left(coalesce(target_display,''),160)
    );

  elsif new.network='character' and new.target_type='post' then
    select p.user_id,p.character_id,p.body,p.created_at
      into target_user,character_ref,target_body,target_created
      from public.social_character_posts p where p.id=new.target_id;
    if target_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if target_user=uid then raise exception 'CANNOT_REPORT_SELF'; end if;
    -- Aucun user_id réel n'est copié dans un snapshot de réseau personnage.
    new.snapshot:=jsonb_build_object(
      'character_id',character_ref,
      'body',left(coalesce(target_body,''),3000),
      'created_at',target_created
    );

  elsif new.network='character' and new.target_type='comment' then
    select c.user_id,c.character_id,c.body,c.created_at
      into target_user,character_ref,target_body,target_created
      from public.social_character_comments c where c.id=new.target_id;
    if target_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if target_user=uid then raise exception 'CANNOT_REPORT_SELF'; end if;
    new.snapshot:=jsonb_build_object(
      'character_id',character_ref,
      'body',left(coalesce(target_body,''),1000),
      'created_at',target_created
    );

  elsif new.network='character' and new.target_type='message' then
    select m.sender_user_id,m.recipient_user_id,m.sender_character_id,m.body,m.created_at
      into sender_user,recipient_user,character_ref,target_body,target_created
      from public.social_character_messages m where m.id=new.target_id;
    if sender_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if recipient_user is distinct from uid or sender_user=uid then
      raise exception 'REPORT_MESSAGE_NOT_RECEIVED';
    end if;
    target_user:=sender_user;
    new.snapshot:=jsonb_build_object(
      'sender_character_id',character_ref,
      'body',left(coalesce(target_body,''),4000),
      'created_at',target_created
    );

  elsif new.network='character' and new.target_type='profile' then
    select c.user_id,c.character_id,c.public_name
      into target_user,character_ref,target_name
      from public.character_social_profiles c where c.character_id=new.target_id;
    if target_user is null then raise exception 'REPORT_TARGET_NOT_FOUND'; end if;
    if target_user=uid then raise exception 'CANNOT_REPORT_SELF'; end if;
    new.snapshot:=jsonb_build_object(
      'character_id',character_ref,
      'public_name',left(coalesce(target_name,''),160)
    );

  else
    raise exception 'INVALID_REPORT_TARGET';
  end if;

  return new;
end;
$$;
revoke all on function public.canonicalize_social_report() from public,anon,authenticated;

-- La correspondance cible -> compte réel est persistée dans une table privée.
-- Elle permet à la modération d'agir même si le contenu signalé est ensuite supprimé,
-- sans exposer le pont entre identité narrative et identité de compte au déclarant.
create or replace function public.persist_social_report_target()
returns trigger
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  target_user uuid;
begin
  if new.network='real' and new.target_type='post' then
    select p.user_id into target_user from public.social_real_posts p where p.id=new.target_id;
  elsif new.network='real' and new.target_type='comment' then
    select c.user_id into target_user from public.social_real_comments c where c.id=new.target_id;
  elsif new.network='real' and new.target_type='message' then
    select m.sender_user_id into target_user from public.social_real_messages m where m.id=new.target_id;
  elsif new.network='real' and new.target_type='profile' then
    select p.user_id into target_user from public.social_profiles p where p.user_id=new.target_id;
  elsif new.network='character' and new.target_type='post' then
    select p.user_id into target_user from public.social_character_posts p where p.id=new.target_id;
  elsif new.network='character' and new.target_type='comment' then
    select c.user_id into target_user from public.social_character_comments c where c.id=new.target_id;
  elsif new.network='character' and new.target_type='message' then
    select m.sender_user_id into target_user from public.social_character_messages m where m.id=new.target_id;
  elsif new.network='character' and new.target_type='profile' then
    select c.user_id into target_user from public.character_social_profiles c where c.character_id=new.target_id;
  end if;

  if target_user is null then
    raise exception 'REPORT_TARGET_NOT_FOUND';
  end if;

  insert into public.social_report_targets(report_id,target_user_id)
  values(new.id,target_user)
  on conflict(report_id) do update
    set target_user_id=excluded.target_user_id,
        created_at=now();
  return new;
end;
$$;
revoke all on function public.persist_social_report_target() from public,anon,authenticated;

-- CHECK NOT VALID protège toutes les nouvelles écritures sans risquer de bloquer le
-- déploiement si un ancien signalement historique possède une raison trop courte.
do $$
begin
  if not exists(
    select 1 from pg_constraint
    where conname='social_reports_reason_length_v24411'
      and conrelid='public.social_reports'::regclass
  ) then
    alter table public.social_reports
      add constraint social_reports_reason_length_v24411
      check(char_length(btrim(reason)) between 3 and 1000) not valid;
  end if;
end $$;

drop trigger if exists canonicalize_social_report_before_insert on public.social_reports;
create trigger canonicalize_social_report_before_insert
before insert on public.social_reports
for each row execute function public.canonicalize_social_report();

drop trigger if exists persist_social_report_target_after_insert on public.social_reports;
create trigger persist_social_report_target_after_insert
after insert on public.social_reports
for each row execute function public.persist_social_report_target();

-- L'utilisateur ne doit pas pouvoir altérer un signalement après sa création.
revoke update,delete on public.social_reports from authenticated;

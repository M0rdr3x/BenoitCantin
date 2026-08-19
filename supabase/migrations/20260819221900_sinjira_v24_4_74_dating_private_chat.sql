-- SINJIRA™ V24.4.74 — conversation Rencontres isolée.
-- Aucun identifiant de l'autre compte n'est retourné pendant l'échange aveugle.
-- Aucun fichier/photo n'est accepté dans ce canal: texte uniquement.

create table if not exists public.dating_messages (
  id uuid primary key default gen_random_uuid(),
  introduction_id uuid not null references public.dating_introductions(id) on delete cascade,
  sender_user_id uuid not null references auth.users(id) on delete cascade,
  body text not null check(char_length(btrim(body)) between 2 and 4000),
  created_at timestamptz not null default now()
);
create index if not exists dating_messages_intro_created_idx on public.dating_messages(introduction_id,created_at,id);
create index if not exists dating_messages_sender_idx on public.dating_messages(sender_user_id,created_at desc);

alter table public.dating_messages enable row level security;
revoke all on table public.dating_messages from public,anon,authenticated;
grant all on table public.dating_messages to service_role;

create or replace function private.dating_intro_other_user(p_intro public.dating_introductions,p_viewer uuid)
returns uuid
language sql immutable
set search_path=pg_catalog
as $$
  select case when p_viewer=p_intro.user_a then p_intro.user_b when p_viewer=p_intro.user_b then p_intro.user_a else null end;
$$;
revoke all on function private.dating_intro_other_user(public.dating_introductions,uuid) from public,anon,authenticated;

create or replace function public.dating_my_introductions()
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'id',i.id,
    'status',i.status,
    'requested_by_me',i.requested_by=uid,
    'other_user_id',null,
    'other_pseudo','Membre compatible',
    'accepted_at',i.accepted_at,
    'created_at',i.created_at
  ) order by i.updated_at desc),'[]'::jsonb)
  into result
  from public.dating_introductions i
  where uid in(i.user_a,i.user_b);
  return result;
end;
$$;
revoke all on function public.dating_my_introductions() from public,anon;
grant execute on function public.dating_my_introductions() to authenticated;

create or replace function public.dating_conversation(p_introduction_id uuid)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); i public.dating_introductions%rowtype; result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into i from public.dating_introductions where id=p_introduction_id;
  if i.id is null or uid not in(i.user_a,i.user_b) or i.status not in('accepted','closed') then raise exception 'DATING_CONVERSATION_NOT_ALLOWED'; end if;
  select coalesce(jsonb_agg(jsonb_build_object(
    'id',m.id,
    'mine',m.sender_user_id=uid,
    'body',m.body,
    'created_at',m.created_at
  ) order by m.created_at,m.id),'[]'::jsonb)
  into result
  from public.dating_messages m
  where m.introduction_id=i.id;
  return result;
end;
$$;
revoke all on function public.dating_conversation(uuid) from public,anon;
grant execute on function public.dating_conversation(uuid) to authenticated;

create or replace function public.dating_send_message(p_introduction_id uuid,p_body text)
returns uuid
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); i public.dating_introductions%rowtype; other_id uuid; msg_id uuid; clean_body text:=btrim(coalesce(p_body,''));
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into i from public.dating_introductions where id=p_introduction_id for update;
  if i.id is null or uid not in(i.user_a,i.user_b) or i.status<>'accepted' then raise exception 'DATING_CONVERSATION_NOT_ALLOWED'; end if;
  other_id:=private.dating_intro_other_user(i,uid);
  if other_id is null then raise exception 'DATING_CONVERSATION_NOT_ALLOWED'; end if;
  if char_length(clean_body)<2 or char_length(clean_body)>4000 then raise exception 'DATING_MESSAGE_LENGTH'; end if;
  if public.social_is_suspended(uid) then raise exception 'COMMUNITY_SUSPENDED'; end if;
  if not public.has_accepted_community_rules(uid) then raise exception 'RULES_REQUIRED'; end if;
  if public.social_is_blocked(uid,other_id) then raise exception 'SOCIAL_BLOCKED'; end if;
  insert into public.dating_messages(introduction_id,sender_user_id,body)
  values(i.id,uid,clean_body) returning id into msg_id;
  return msg_id;
end;
$$;
revoke all on function public.dating_send_message(uuid,text) from public,anon;
grant execute on function public.dating_send_message(uuid,text) to authenticated;

create or replace function public.dating_report_message(p_message_id uuid,p_reason text)
returns uuid
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); m public.dating_messages%rowtype; i public.dating_introductions%rowtype; report_id uuid; clean_reason text:=btrim(coalesce(p_reason,''));
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if char_length(clean_reason)<3 or char_length(clean_reason)>500 then raise exception 'REPORT_REASON_LENGTH'; end if;
  select * into m from public.dating_messages where id=p_message_id;
  if m.id is null then raise exception 'DATING_MESSAGE_NOT_FOUND'; end if;
  select * into i from public.dating_introductions where id=m.introduction_id;
  if i.id is null or uid not in(i.user_a,i.user_b) or m.sender_user_id=uid then raise exception 'DATING_REPORT_NOT_ALLOWED'; end if;
  insert into public.social_reports(reporter_user_id,network,target_type,target_id,reason,snapshot)
  values(uid,'real','message',m.id,clean_reason,jsonb_build_object(
    'dating',true,
    'introduction_id',m.introduction_id,
    'body',m.body,
    'sender_user_id',m.sender_user_id,
    'reported_by',uid
  )) returning id into report_id;
  return report_id;
end;
$$;
revoke all on function public.dating_report_message(uuid,text) from public,anon;
grant execute on function public.dating_report_message(uuid,text) to authenticated;

create or replace function private.dating_photo_status(p_introduction_id uuid,p_viewer uuid)
returns jsonb
language plpgsql stable security definer
set search_path=pg_catalog,public
as $$
declare i public.dating_introductions%rowtype; other_id uuid; sent_n integer:=0; received_n integer:=0; mine boolean:=false; theirs boolean:=false; unlocked boolean:=false; avatar text; pseudo text;
begin
  select * into i from public.dating_introductions where id=p_introduction_id;
  if i.id is null or i.status<>'accepted' or p_viewer not in(i.user_a,i.user_b) then raise exception 'ACCEPTED_INTRO_REQUIRED'; end if;
  other_id:=case when p_viewer=i.user_a then i.user_b else i.user_a end;
  select count(*) filter(where m.sender_user_id=p_viewer),count(*) filter(where m.sender_user_id=other_id)
  into sent_n,received_n
  from public.dating_messages m
  where m.introduction_id=i.id and m.created_at>=coalesce(i.accepted_at,i.created_at);
  select exists(select 1 from public.dating_photo_reveal_consents c where c.introduction_id=i.id and c.user_id=p_viewer) into mine;
  select exists(select 1 from public.dating_photo_reveal_consents c where c.introduction_id=i.id and c.user_id=other_id) into theirs;
  unlocked:=sent_n>=10 and received_n>=10 and mine and theirs;
  if unlocked then
    select sp.avatar_path,coalesce(nullif(sp.pseudo,''),nullif(sp.display_name,''),'Membre SINJIRA')
    into avatar,pseudo from public.social_profiles sp where sp.user_id=other_id;
  end if;
  return jsonb_build_object(
    'sent_count',sent_n,'received_count',received_n,'threshold',10,
    'my_consent',mine,'other_consent',theirs,'unlocked',unlocked,
    'other_avatar_path',case when unlocked then avatar else null end,
    'other_pseudo',case when unlocked then pseudo else null end
  );
end;
$$;
revoke all on function private.dating_photo_status(uuid,uuid) from public,anon,authenticated;

comment on table public.dating_messages is 'Conversation texte Rencontres isolée. Aucun accès direct client et aucune pièce jointe.';
comment on function public.dating_conversation(uuid) is 'Retourne seulement mine/body/date; jamais sender_user_id ou identité de l’autre compte.';
comment on function public.dating_send_message(uuid,text) is 'Envoi texte dans une présentation acceptée, sans exposer le destinataire au navigateur.';
comment on function public.dating_report_message(uuid,text) is 'Signale un message reçu de Rencontres à la modération avec le minimum de contexte nécessaire.';
comment on function private.dating_photo_status(uuid,uuid) is 'Révélation identité/photo uniquement après 10 messages de chaque côté et consentement des deux comptes.';

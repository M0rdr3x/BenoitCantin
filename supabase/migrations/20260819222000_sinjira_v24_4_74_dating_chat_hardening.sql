-- SINJIRA™ V24.4.74 — durcissement final du chat aveugle.
-- Anti-spam, notifications cohérentes et suppression complète du sous-système Rencontres.

create or replace function public.dating_send_message(p_introduction_id uuid,p_body text)
returns uuid
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); i public.dating_introductions%rowtype; other_id uuid; msg_id uuid; clean_body text:=btrim(coalesce(p_body,'')); recent_count integer;
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
  if exists(select 1 from public.dating_messages m where m.introduction_id=i.id and m.sender_user_id=uid and m.created_at>now()-interval '2 seconds') then
    raise exception 'DATING_RATE_LIMIT';
  end if;
  select count(*)::integer into recent_count from public.dating_messages m
  where m.introduction_id=i.id and m.sender_user_id=uid and m.created_at>now()-interval '1 hour';
  if recent_count>=120 then raise exception 'DATING_RATE_LIMIT'; end if;
  insert into public.dating_messages(introduction_id,sender_user_id,body)
  values(i.id,uid,clean_body) returning id into msg_id;
  return msg_id;
end;
$$;
revoke all on function public.dating_send_message(uuid,text) from public,anon;
grant execute on function public.dating_send_message(uuid,text) to authenticated;

create or replace function public.dating_respond_introduction(p_introduction_id uuid,p_accept boolean)
returns boolean
language plpgsql volatile security definer
set search_path=pg_catalog,public,private
as $$
declare uid uuid:=auth.uid(); i public.dating_introductions%rowtype; other_id uuid;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into i from public.dating_introductions where id=p_introduction_id for update;
  if i.id is null or uid not in(i.user_a,i.user_b) then raise exception 'INTRO_NOT_FOUND'; end if;
  if i.requested_by=uid or i.status<>'requested' then raise exception 'INTRO_RESPONSE_NOT_ALLOWED'; end if;
  other_id:=private.dating_intro_other_user(i,uid);
  if p_accept and not private.dating_pair_allowed(uid,other_id) then raise exception 'DATING_PAIR_NOT_ALLOWED'; end if;
  update public.dating_introductions set
    status=case when p_accept then 'accepted' else 'declined' end,
    accepted_at=case when p_accept then now() else null end,
    closed_at=case when p_accept then null else now() end,
    updated_at=now()
  where id=i.id;
  insert into public.user_notifications(user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path)
  values(other_id,'dating_intro',case when p_accept then 'Présentation acceptée' else 'Présentation non retenue' end,
    case when p_accept then 'Une conversation Rencontres anonyme en texte est maintenant ouverte.' else 'La proposition de présentation a été fermée.' end,
    'dating_introduction',i.id,'/compte/rencontres.html');
  return true;
end;
$$;
revoke all on function public.dating_respond_introduction(uuid,boolean) from public,anon;
grant execute on function public.dating_respond_introduction(uuid,boolean) to authenticated;

create or replace function public.dating_delete_my_profile()
returns boolean
language plpgsql volatile security definer
set search_path=pg_catalog,public
as $$
declare uid uuid:=auth.uid();
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  delete from public.dating_recommendation_tokens where viewer_user_id=uid or target_user_id=uid;
  delete from public.dating_introductions where uid in(user_a,user_b);
  delete from public.dating_profiles where user_id=uid;
  return true;
end;
$$;
revoke all on function public.dating_delete_my_profile() from public,anon;
grant execute on function public.dating_delete_my_profile() to authenticated;

comment on function public.dating_send_message(uuid,text) is 'Chat texte Rencontres: 2–4000 caractères, max 1 message/2s et 120 messages/h par participant/conversation.';
comment on function public.dating_delete_my_profile() is 'Supprime profil, jetons et présentations Rencontres; la cascade supprime messages et consentements associés.';

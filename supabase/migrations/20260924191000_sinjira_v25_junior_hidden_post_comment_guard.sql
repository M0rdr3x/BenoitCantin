-- SINJIRA™ V25 — un contenu Junior masqué ne reçoit plus de nouveaux commentaires.
-- L'HUMAIN AVANT TOUT : une décision humaine de modération doit arrêter
-- immédiatement l'interaction sur la publication concernée, sans supprimer
-- l'historique ni exposer davantage d'identité.

begin;

create or replace function sinjira_v25_internal.junior_community_create_comment(
  p_post_id uuid,
  p_body text
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $junior_comment$
declare
  uid uuid;
  body text:=btrim(coalesce(p_body,''));
  code text;
  new_id uuid;
  author_id uuid;
begin
  uid:=private.sinjira_junior_require_access(true);

  if char_length(body)<1 or char_length(body)>300 then
    raise exception 'JUNIOR_COMMENT_LENGTH_INVALID';
  end if;

  if (
    select count(*)
    from public.junior_community_comments c
    where c.author_user_id=uid
      and c.created_at>now()-interval '1 hour'
  )>=30 then
    raise exception 'JUNIOR_COMMENT_RATE_LIMIT';
  end if;

  select p.author_user_id
    into author_id
  from public.junior_community_posts p
  where p.id=p_post_id
    and p.status='active'
    and public.moderation_content_visible('real','post',p.id);

  if author_id is null
     or not private.sinjira_is_junior(author_id)
     or not private.sinjira_junior_community_enabled(author_id) then
    raise exception 'JUNIOR_POST_UNAVAILABLE';
  end if;

  if public.social_is_blocked(uid,author_id) then
    raise exception 'JUNIOR_POST_UNAVAILABLE';
  end if;

  code:=private.sinjira_junior_content_code(body);
  if code is not null then
    raise exception 'SINJIRA_JUNIOR_%',code using errcode='P0001';
  end if;

  insert into public.junior_community_comments(post_id,author_user_id,body)
  values(p_post_id,uid,body)
  returning id into new_id;

  return jsonb_build_object('ok',true,'id',new_id);
end;
$junior_comment$;

revoke all on function sinjira_v25_internal.junior_community_create_comment(uuid,text)
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.junior_community_create_comment(uuid,text)
to authenticated,service_role;

comment on function sinjira_v25_internal.junior_community_create_comment(uuid,text) is
  'Création commentaire Junior: le post doit rester actif, visible selon la modération, appartenir à un auteur Junior encore autorisé et ne pas être bloqué.';

commit;

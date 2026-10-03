-- SINJIRA™ V25 — visibilité des commentaires Junior liée à l'accès courant de l'auteur.
-- L'HUMAIN AVANT TOUT : une révocation ou une sortie de la bande 11–12 doit
-- retirer immédiatement du fil les contenus de cet auteur, sans supprimer
-- l'historique et sans exposer son identité réelle.

begin;

create or replace function sinjira_v25_internal.junior_community_feed(
  p_limit integer default 30
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $junior_feed$
declare
  uid uuid;
  result jsonb;
begin
  uid:=private.sinjira_junior_require_access(true);

  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',x.id,
        'author_alias',x.author_alias,
        'body',x.body,
        'created_at',x.created_at,
        'mine',x.mine,
        'comments',x.comments
      )
      order by x.created_at desc
    ),
    '[]'::jsonb
  )
  into result
  from (
    select
      p.id,
      private.sinjira_junior_alias(p.author_user_id) author_alias,
      p.body,
      p.created_at,
      p.author_user_id=uid mine,
      (
        select coalesce(
          jsonb_agg(
            jsonb_build_object(
              'id',c.id,
              'author_alias',private.sinjira_junior_alias(c.author_user_id),
              'body',c.body,
              'created_at',c.created_at,
              'mine',c.author_user_id=uid
            )
            order by c.created_at
          ),
          '[]'::jsonb
        )
        from public.junior_community_comments c
        where c.post_id=p.id
          and c.status='active'
          and public.moderation_content_visible('real','comment',c.id)
          and private.sinjira_is_junior(c.author_user_id)
          and private.sinjira_junior_community_enabled(c.author_user_id)
          and not public.social_is_blocked(uid,c.author_user_id)
      ) comments
    from public.junior_community_posts p
    where p.status='active'
      and public.moderation_content_visible('real','post',p.id)
      and private.sinjira_is_junior(p.author_user_id)
      and private.sinjira_junior_community_enabled(p.author_user_id)
      and not public.social_is_blocked(uid,p.author_user_id)
    order by p.created_at desc
    limit least(greatest(coalesce(p_limit,30),1),50)
  ) x;

  return result;
end;
$junior_feed$;

revoke all on function sinjira_v25_internal.junior_community_feed(integer)
from public,anon,authenticated;
grant execute on function sinjira_v25_internal.junior_community_feed(integer)
to authenticated,service_role;

comment on function sinjira_v25_internal.junior_community_feed(integer) is
  'Fil Junior pseudonymisé: publications et commentaires restent visibles uniquement tant que leur auteur est encore child 11–12 et dispose d un consentement Junior actif. Une révocation masque immédiatement le contenu sans le supprimer.';

commit;

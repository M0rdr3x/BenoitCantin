-- SINJIRA V24.4.55 — lecture publique des commentaires sans SECURITY DEFINER.
-- Les informations publiques de l’auteur du commentaire sont figées côté serveur
-- au moment de la soumission, sans ouvrir la table profiles aux visiteurs.

alter table public.sinjira_novel_comments
  add column if not exists avatar_path_snapshot text;

update public.sinjira_novel_comments c
set display_name_snapshot = coalesce(nullif(p.pseudo,''),nullif(p.display_name,''),'Lecteur SINJIRA'),
    avatar_path_snapshot = p.avatar_path
from public.profiles p
where p.user_id=c.user_id;

create or replace function public.set_sinjira_comment_public_snapshot()
returns trigger
language plpgsql
security definer
set search_path=public,pg_temp
as $$
declare
  v_pseudo text;
  v_display text;
  v_avatar text;
begin
  select p.pseudo,p.display_name,p.avatar_path
  into v_pseudo,v_display,v_avatar
  from public.profiles p
  where p.user_id=new.user_id;

  new.display_name_snapshot := coalesce(nullif(v_pseudo,''),nullif(v_display,''),'Lecteur SINJIRA');
  new.avatar_path_snapshot := v_avatar;
  return new;
end;
$$;

revoke all on function public.set_sinjira_comment_public_snapshot() from public,anon,authenticated;
grant execute on function public.set_sinjira_comment_public_snapshot() to service_role;

drop trigger if exists trg_sinjira_comment_public_snapshot on public.sinjira_novel_comments;
create trigger trg_sinjira_comment_public_snapshot
before insert or update of user_id on public.sinjira_novel_comments
for each row execute function public.set_sinjira_comment_public_snapshot();

create or replace function public.list_sinjira_novel_comments(p_novel_slug text)
returns table(id uuid, body text, spoiler boolean, created_at timestamptz, pseudo text, avatar_path text)
language sql
stable
security invoker
set search_path=public,pg_temp
as $$
  select c.id,
         c.body,
         c.spoiler,
         c.created_at,
         coalesce(nullif(c.display_name_snapshot,''),'Lecteur SINJIRA') as pseudo,
         c.avatar_path_snapshot as avatar_path
  from public.sinjira_novel_comments c
  join public.sinjira_novels n on n.id=c.novel_id
  where char_length(trim(coalesce(p_novel_slug,''))) between 1 and 120
    and n.slug=trim(p_novel_slug)
    and n.comments_enabled=true
    and c.status='approved'
  order by c.created_at desc
  limit 250;
$$;

revoke all on function public.list_sinjira_novel_comments(text) from public;
grant execute on function public.list_sinjira_novel_comments(text) to anon,authenticated;

create or replace function public.sinjira_public_comments_security_health()
returns jsonb
language sql
stable
security invoker
set search_path=public,pg_temp
as $$
  select jsonb_build_object(
    'ok',
      exists(
        select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
        where n.nspname='public' and p.proname='list_sinjira_novel_comments' and p.prosecdef=false
      ) and
      exists(
        select 1 from information_schema.columns
        where table_schema='public' and table_name='sinjira_novel_comments' and column_name='avatar_path_snapshot'
      ) and
      exists(select 1 from pg_trigger where tgname='trg_sinjira_comment_public_snapshot' and not tgisinternal),
    'list_security_invoker',exists(
      select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
      where n.nspname='public' and p.proname='list_sinjira_novel_comments' and p.prosecdef=false
    ),
    'snapshot_column',exists(
      select 1 from information_schema.columns
      where table_schema='public' and table_name='sinjira_novel_comments' and column_name='avatar_path_snapshot'
    ),
    'snapshot_trigger',exists(select 1 from pg_trigger where tgname='trg_sinjira_comment_public_snapshot' and not tgisinternal),
    'version','24.4.55'
  );
$$;

revoke all on function public.sinjira_public_comments_security_health() from public,anon,authenticated;
grant execute on function public.sinjira_public_comments_security_health() to service_role;

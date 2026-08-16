-- SINJIRA™ V24.4.12 — sécurité jeunesse canonique
-- Une seule source d'âge : account_safety_profiles.
-- 12–17 ans = jeunesse sociale uniquement avec un guardian_links vérifié.
-- Les cohortes jeunesse/adulte ne peuvent pas interagir entre elles.

create or replace function public.sinjira_age_band(p_user_id uuid default auth.uid())
returns text
language sql
stable
security definer
set search_path=public
as $$
  select case
    when s.user_id is null or s.date_of_birth is null or s.date_of_birth>current_date then 'unverified'
    when s.legacy_status='memorialized' then 'memorial'
    when age(current_date,s.date_of_birth)<interval '12 years' then 'under12'
    when age(current_date,s.date_of_birth)<interval '18 years' then
      case when exists(select 1 from public.guardian_links g where g.minor_user_id=s.user_id and g.status='verified') then 'youth' else 'youth_pending' end
    else 'adult'
  end
  from (select p_user_id user_id) x
  left join public.account_safety_profiles s on s.user_id=x.user_id;
$$;
revoke all on function public.sinjira_age_band(uuid) from public,anon;
grant execute on function public.sinjira_age_band(uuid) to authenticated,service_role;

create or replace function public.sinjira_can_social_interact(p_a uuid,p_b uuid)
returns boolean
language sql
stable
security definer
set search_path=public
as $$
  select case
    when p_a is null or p_b is null then false
    when p_a=p_b then public.sinjira_age_band(p_a) in ('adult','youth')
    when public.sinjira_age_band(p_a)='adult' and public.sinjira_age_band(p_b)='adult' then true
    when public.sinjira_age_band(p_a)='youth' and public.sinjira_age_band(p_b)='youth' then true
    else false
  end;
$$;
revoke all on function public.sinjira_can_social_interact(uuid,uuid) from public,anon;
grant execute on function public.sinjira_can_social_interact(uuid,uuid) to authenticated,service_role;

-- Alias de compatibilité pour les premiers écrans V24; même règle stricte.
create or replace function public.sinjira_social_compatible(a uuid,b uuid)
returns boolean
language sql
stable
security definer
set search_path=public
as $$ select public.sinjira_can_social_interact(a,b); $$;
revoke all on function public.sinjira_social_compatible(uuid,uuid) from public,anon;
grant execute on function public.sinjira_social_compatible(uuid,uuid) to authenticated,service_role;

create or replace function public.sinjira_parent_can_supervise(p_parent uuid,p_child uuid)
returns boolean
language sql
stable
security definer
set search_path=public
as $$
  select public.sinjira_age_band(p_parent)='adult'
    and public.sinjira_age_band(p_child)='youth'
    and exists(select 1 from public.guardian_links g where g.guardian_user_id=p_parent and g.minor_user_id=p_child and g.status='verified');
$$;
revoke all on function public.sinjira_parent_can_supervise(uuid,uuid) from public,anon;
grant execute on function public.sinjira_parent_can_supervise(uuid,uuid) to authenticated,service_role;

create or replace function public.get_guardian_youth_contacts(p_child_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare uid uuid:=auth.uid(); result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_parent_can_supervise(uid,p_child_user_id) then raise exception 'GUARDIAN_ACCESS_REQUIRED'; end if;
  with contacts as (
    select case when m.sender_user_id=p_child_user_id then m.recipient_user_id else m.sender_user_id end other_user_id,max(m.created_at) last_contact_at,'Compte'::text network
    from public.social_real_messages m where p_child_user_id in(m.sender_user_id,m.recipient_user_id) group by 1
    union all
    select case when m.sender_user_id=p_child_user_id then m.recipient_user_id else m.sender_user_id end,max(m.created_at),'Personnage'::text
    from public.social_character_messages m where p_child_user_id in(m.sender_user_id,m.recipient_user_id) group by 1
  ), grouped as (
    select other_user_id,max(last_contact_at) last_contact_at,array_agg(distinct network) networks from contacts group by other_user_id
  )
  select coalesce(jsonb_agg(jsonb_build_object('user_id',g.other_user_id,'pseudo',coalesce(sp.pseudo,'Membre SINJIRA'),'display_name',sp.display_name,'networks',g.networks,'last_contact_at',g.last_contact_at) order by g.last_contact_at desc),'[]'::jsonb)
  into result from grouped g left join public.social_profiles sp on sp.user_id=g.other_user_id;
  return result;
end;
$$;
revoke all on function public.get_guardian_youth_contacts(uuid) from public,anon;
grant execute on function public.get_guardian_youth_contacts(uuid) to authenticated;

-- Profils visibles seulement à soi ou à une personne de la même cohorte autorisée.
drop policy if exists social_profiles_read on public.social_profiles;
create policy social_profiles_read on public.social_profiles for select to authenticated
using(auth.uid()=user_id or (public.sinjira_can_social_interact(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id)));

drop policy if exists character_social_profiles_read on public.character_social_profiles;
create policy character_social_profiles_read on public.character_social_profiles for select to authenticated
using(auth.uid()=user_id or (public.sinjira_can_social_interact(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id)));

-- Réseau compte réel.
drop policy if exists real_posts_read on public.social_real_posts;
create policy real_posts_read on public.social_real_posts for select to authenticated
using(public.sinjira_can_social_interact(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id));
drop policy if exists real_posts_insert on public.social_real_posts;
create policy real_posts_insert on public.social_real_posts for insert to authenticated
with check(auth.uid()=user_id and public.sinjira_age_band(auth.uid()) in ('youth','adult') and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()));

drop policy if exists real_comments_read on public.social_real_comments;
create policy real_comments_read on public.social_real_comments for select to authenticated
using(public.sinjira_can_social_interact(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id) and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));
drop policy if exists real_comments_insert on public.social_real_comments;
create policy real_comments_insert on public.social_real_comments for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));

drop policy if exists real_likes_read on public.social_real_likes;
create policy real_likes_read on public.social_real_likes for select to authenticated
using(public.sinjira_can_social_interact(auth.uid(),user_id) and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));
drop policy if exists real_likes_own on public.social_real_likes;
create policy real_likes_own on public.social_real_likes for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));

drop policy if exists real_messages_read on public.social_real_messages;
create policy real_messages_read on public.social_real_messages for select to authenticated
using(auth.uid() in(sender_user_id,recipient_user_id) and public.sinjira_can_social_interact(sender_user_id,recipient_user_id));
drop policy if exists real_messages_insert on public.social_real_messages;
create policy real_messages_insert on public.social_real_messages for insert to authenticated
with check(auth.uid()=sender_user_id and public.sinjira_can_social_interact(sender_user_id,recipient_user_id) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and not public.social_is_blocked(sender_user_id,recipient_user_id));

-- Réseau personnage.
drop policy if exists char_posts_read on public.social_character_posts;
create policy char_posts_read on public.social_character_posts for select to authenticated
using(public.sinjira_can_social_interact(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id));
drop policy if exists char_posts_insert on public.social_character_posts;
create policy char_posts_insert on public.social_character_posts for insert to authenticated
with check(auth.uid()=user_id and public.sinjira_age_band(auth.uid()) in ('youth','adult') and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=character_id and c.user_id=auth.uid()));

drop policy if exists char_comments_read on public.social_character_comments;
create policy char_comments_read on public.social_character_comments for select to authenticated
using(public.sinjira_can_social_interact(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));
drop policy if exists char_comments_insert on public.social_character_comments;
create policy char_comments_insert on public.social_character_comments for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=character_id and c.user_id=auth.uid()) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));

drop policy if exists char_likes_read on public.social_character_likes;
create policy char_likes_read on public.social_character_likes for select to authenticated
using(public.sinjira_can_social_interact(auth.uid(),user_id) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));
drop policy if exists char_likes_insert on public.social_character_likes;
create policy char_likes_insert on public.social_character_likes for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=character_id and c.user_id=auth.uid()) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_can_social_interact(auth.uid(),p.user_id)));

drop policy if exists char_messages_read on public.social_character_messages;
create policy char_messages_read on public.social_character_messages for select to authenticated
using(auth.uid() in(sender_user_id,recipient_user_id) and public.sinjira_can_social_interact(sender_user_id,recipient_user_id));
drop policy if exists char_messages_insert on public.social_character_messages;
create policy char_messages_insert on public.social_character_messages for insert to authenticated
with check(auth.uid()=sender_user_id and public.sinjira_can_social_interact(sender_user_id,recipient_user_id) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and not public.social_is_blocked(sender_user_id,recipient_user_id) and exists(select 1 from public.character_social_profiles c where c.character_id=sender_character_id and c.user_id=auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=recipient_character_id and c.user_id=recipient_user_id));

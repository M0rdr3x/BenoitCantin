-- SINJIRA™ V24.4.12 — séparation jeunesse/adulte appliquée au backend
-- Objectif : 12–17 ans et 18+ ne peuvent pas interagir entre eux dans les réseaux SINJIRA™.
-- Les moins de 12 ans et les comptes sans date de naissance valide n'accèdent pas aux fonctions sociales.
-- Un parent/tuteur relié et confirmé peut voir QUI échange avec son enfant, jamais le contenu libre des messages via cette fonction.

-- ---------------------------------------------------------------------------
-- PROFIL : Homme / Femme uniquement selon la règle produit actuelle.
-- ---------------------------------------------------------------------------
update public.private_profiles
set gender = case lower(trim(coalesce(gender,'')))
  when 'homme' then 'Homme'
  when 'femme' then 'Femme'
  else null
end
where gender is not null;

alter table public.private_profiles drop constraint if exists private_profiles_gender_check;
alter table public.private_profiles add constraint private_profiles_gender_check
  check (gender is null or gender in ('Homme','Femme'));

-- ---------------------------------------------------------------------------
-- COHORTE CALCULÉE EN TEMPS RÉEL À PARTIR DE LA DATE DE NAISSANCE.
-- ---------------------------------------------------------------------------
create or replace function public.sinjira_age_band(p_user_id uuid default auth.uid())
returns text
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when p_user_id is null then 'unknown'
    when pp.birth_date is null or pp.birth_date > current_date then 'unknown'
    when extract(year from age(current_date,pp.birth_date)) < 12 then 'under_12'
    when extract(year from age(current_date,pp.birth_date)) < 18 then 'youth_12_17'
    else 'adult_18_plus'
  end
  from (select p_user_id as id) x
  left join public.private_profiles pp on pp.user_id=x.id;
$$;
revoke all on function public.sinjira_age_band(uuid) from public,anon;
grant execute on function public.sinjira_age_band(uuid) to authenticated,service_role;

create or replace function public.sinjira_social_compatible(a uuid,b uuid)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select case
    when a is null or b is null then false
    when a=b then public.sinjira_age_band(a) in ('youth_12_17','adult_18_plus')
    else public.sinjira_age_band(a)=public.sinjira_age_band(b)
      and public.sinjira_age_band(a) in ('youth_12_17','adult_18_plus')
  end;
$$;
revoke all on function public.sinjira_social_compatible(uuid,uuid) from public,anon;
grant execute on function public.sinjira_social_compatible(uuid,uuid) to authenticated,service_role;

-- ---------------------------------------------------------------------------
-- RELATIONS FAMILIALES LIÉES : l'autre compte doit accepter explicitement.
-- Un propriétaire de fiche ne peut plus se déclarer lui-même « accepté ».
-- ---------------------------------------------------------------------------
drop policy if exists family_relationships_own on public.family_relationships;
drop policy if exists family_relationships_read_parties on public.family_relationships;
drop policy if exists family_relationships_insert_owner on public.family_relationships;
drop policy if exists family_relationships_update_owner on public.family_relationships;
drop policy if exists family_relationships_delete_owner on public.family_relationships;

create policy family_relationships_read_parties on public.family_relationships
for select to authenticated
using(auth.uid()=owner_user_id or auth.uid()=related_user_id);

create policy family_relationships_insert_owner on public.family_relationships
for insert to authenticated
with check(
  auth.uid()=owner_user_id
  and (
    (related_user_id is null and status='private_record')
    or
    (related_user_id is not null and related_user_id<>owner_user_id and status='pending')
  )
);

create policy family_relationships_update_owner on public.family_relationships
for update to authenticated
using(auth.uid()=owner_user_id)
with check(
  auth.uid()=owner_user_id
  and (
    (related_user_id is null and status in ('private_record','ended'))
    or
    (related_user_id is not null and status in ('pending','ended'))
  )
);

create policy family_relationships_delete_owner on public.family_relationships
for delete to authenticated
using(auth.uid()=owner_user_id);

create or replace function public.respond_family_relationship(p_relationship_id uuid,p_accept boolean)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  r public.family_relationships%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  select * into r from public.family_relationships where id=p_relationship_id for update;
  if r.id is null then raise exception 'RELATIONSHIP_NOT_FOUND'; end if;
  if r.related_user_id is distinct from uid then raise exception 'RELATIONSHIP_RESPONSE_FORBIDDEN'; end if;
  if r.status<>'pending' then raise exception 'RELATIONSHIP_NOT_PENDING'; end if;
  update public.family_relationships
  set status=case when p_accept then 'accepted' else 'rejected' end,updated_at=now()
  where id=r.id;
  return jsonb_build_object('ok',true,'relationship_id',r.id,'status',case when p_accept then 'accepted' else 'rejected' end);
end;
$$;
revoke all on function public.respond_family_relationship(uuid,boolean) from public,anon;
grant execute on function public.respond_family_relationship(uuid,boolean) to authenticated;

create or replace function public.sinjira_parent_can_supervise(p_parent uuid,p_child uuid)
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select public.sinjira_age_band(p_parent)='adult_18_plus'
    and public.sinjira_age_band(p_child)='youth_12_17'
    and exists(
      select 1 from public.family_relationships fr
      where fr.status='accepted'
        and lower(fr.relationship_type) in ('parent','guardian','tuteur','tutrice','père','pere','mère','mere','father','mother')
        and ((fr.owner_user_id=p_parent and fr.related_user_id=p_child)
          or (fr.owner_user_id=p_child and fr.related_user_id=p_parent))
    );
$$;
revoke all on function public.sinjira_parent_can_supervise(uuid,uuid) from public,anon;
grant execute on function public.sinjira_parent_can_supervise(uuid,uuid) to authenticated,service_role;

-- Aperçu parental : identité des contacts et dernière interaction seulement, aucun corps de message.
create or replace function public.get_guardian_youth_contacts(p_child_user_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if not public.sinjira_parent_can_supervise(uid,p_child_user_id) then raise exception 'GUARDIAN_ACCESS_REQUIRED'; end if;

  with contacts as (
    select case when m.sender_user_id=p_child_user_id then m.recipient_user_id else m.sender_user_id end other_user_id,
           max(m.created_at) last_contact_at,
           'Compte'::text network
    from public.social_real_messages m
    where p_child_user_id in (m.sender_user_id,m.recipient_user_id)
    group by 1
    union all
    select case when m.sender_user_id=p_child_user_id then m.recipient_user_id else m.sender_user_id end,
           max(m.created_at),
           'Personnage'::text
    from public.social_character_messages m
    where p_child_user_id in (m.sender_user_id,m.recipient_user_id)
    group by 1
  ), grouped as (
    select c.other_user_id,max(c.last_contact_at) last_contact_at,array_agg(distinct c.network) networks
    from contacts c group by c.other_user_id
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'user_id',g.other_user_id,
    'pseudo',coalesce(sp.pseudo,'Membre SINJIRA'),
    'display_name',sp.display_name,
    'networks',g.networks,
    'last_contact_at',g.last_contact_at
  ) order by g.last_contact_at desc),'[]'::jsonb)
  into result
  from grouped g
  left join public.social_profiles sp on sp.user_id=g.other_user_id;

  return result;
end;
$$;
revoke all on function public.get_guardian_youth_contacts(uuid) from public,anon;
grant execute on function public.get_guardian_youth_contacts(uuid) to authenticated;

-- ---------------------------------------------------------------------------
-- PROFILS ET FLUX : visibilité limitée à la même cohorte.
-- ---------------------------------------------------------------------------
drop policy if exists social_profiles_read on public.social_profiles;
create policy social_profiles_read on public.social_profiles for select to authenticated
using(auth.uid()=user_id or (public.sinjira_social_compatible(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id)));

drop policy if exists character_social_profiles_read on public.character_social_profiles;
create policy character_social_profiles_read on public.character_social_profiles for select to authenticated
using(auth.uid()=user_id or (public.sinjira_social_compatible(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id)));

-- Réseau compte réel.
drop policy if exists real_posts_read on public.social_real_posts;
create policy real_posts_read on public.social_real_posts for select to authenticated
using(public.sinjira_social_compatible(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id));

drop policy if exists real_posts_insert on public.social_real_posts;
create policy real_posts_insert on public.social_real_posts for insert to authenticated
with check(auth.uid()=user_id and public.sinjira_age_band(auth.uid()) in ('youth_12_17','adult_18_plus') and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()));

drop policy if exists real_comments_read on public.social_real_comments;
create policy real_comments_read on public.social_real_comments for select to authenticated
using(
  public.sinjira_social_compatible(auth.uid(),user_id)
  and not public.social_is_blocked(auth.uid(),user_id)
  and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id))
);

drop policy if exists real_comments_insert on public.social_real_comments;
create policy real_comments_insert on public.social_real_comments for insert to authenticated
with check(
  auth.uid()=user_id
  and public.has_accepted_community_rules(auth.uid())
  and not public.social_is_suspended(auth.uid())
  and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id))
);

drop policy if exists real_likes_read on public.social_real_likes;
create policy real_likes_read on public.social_real_likes for select to authenticated
using(public.sinjira_social_compatible(auth.uid(),user_id) and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id)));

drop policy if exists real_likes_own on public.social_real_likes;
create policy real_likes_own on public.social_real_likes for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.social_real_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id)));

drop policy if exists real_messages_read on public.social_real_messages;
create policy real_messages_read on public.social_real_messages for select to authenticated
using(auth.uid() in(sender_user_id,recipient_user_id) and public.sinjira_social_compatible(sender_user_id,recipient_user_id));

drop policy if exists real_messages_insert on public.social_real_messages;
create policy real_messages_insert on public.social_real_messages for insert to authenticated
with check(auth.uid()=sender_user_id and public.sinjira_social_compatible(sender_user_id,recipient_user_id) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and not public.social_is_blocked(sender_user_id,recipient_user_id));

-- Réseau personnage.
drop policy if exists char_posts_read on public.social_character_posts;
create policy char_posts_read on public.social_character_posts for select to authenticated
using(public.sinjira_social_compatible(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id));

drop policy if exists char_posts_insert on public.social_character_posts;
create policy char_posts_insert on public.social_character_posts for insert to authenticated
with check(auth.uid()=user_id and public.sinjira_age_band(auth.uid()) in ('youth_12_17','adult_18_plus') and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=character_id and c.user_id=auth.uid()));

drop policy if exists char_comments_read on public.social_character_comments;
create policy char_comments_read on public.social_character_comments for select to authenticated
using(public.sinjira_social_compatible(auth.uid(),user_id) and not public.social_is_blocked(auth.uid(),user_id) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id)));

drop policy if exists char_comments_insert on public.social_character_comments;
create policy char_comments_insert on public.social_character_comments for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=character_id and c.user_id=auth.uid()) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id)));

drop policy if exists char_likes_read on public.social_character_likes;
create policy char_likes_read on public.social_character_likes for select to authenticated
using(public.sinjira_social_compatible(auth.uid(),user_id) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id)));

drop policy if exists char_likes_insert on public.social_character_likes;
create policy char_likes_insert on public.social_character_likes for insert to authenticated
with check(auth.uid()=user_id and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=character_id and c.user_id=auth.uid()) and exists(select 1 from public.social_character_posts p where p.id=post_id and public.sinjira_social_compatible(auth.uid(),p.user_id)));

drop policy if exists char_messages_read on public.social_character_messages;
create policy char_messages_read on public.social_character_messages for select to authenticated
using(auth.uid() in(sender_user_id,recipient_user_id) and public.sinjira_social_compatible(sender_user_id,recipient_user_id));

drop policy if exists char_messages_insert on public.social_character_messages;
create policy char_messages_insert on public.social_character_messages for insert to authenticated
with check(auth.uid()=sender_user_id and public.sinjira_social_compatible(sender_user_id,recipient_user_id) and public.has_accepted_community_rules(auth.uid()) and not public.social_is_suspended(auth.uid()) and not public.social_is_blocked(sender_user_id,recipient_user_id) and exists(select 1 from public.character_social_profiles c where c.character_id=sender_character_id and c.user_id=auth.uid()) and exists(select 1 from public.character_social_profiles c where c.character_id=recipient_character_id and c.user_id=recipient_user_id));

-- Les politiques de modification/suppression existantes restent limitées au propriétaire du contenu.

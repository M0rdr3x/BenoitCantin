-- SINJIRA™ V25 — comptes enfants supervisés 11–12 ans.
-- Objectifs :
--  * permettre la création d'un compte dès 11 ans uniquement avec un parent/tuteur adulte vérifié;
--  * conserver la validation serveur comme autorité de l'âge;
--  * maintenir les comptes 11–12 hors des fonctions sociales jusqu'à 13 ans;
--  * conserver la porte de juridiction jeunesse canadienne pour les 11–17 ans.

create or replace function public.enforce_sinjira_account_safety_age()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $$
declare years integer;
begin
  if new.date_of_birth is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if new.date_of_birth>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,new.date_of_birth))::integer;
  if years<11 then raise exception 'SINJIRA_MINIMUM_AGE_11'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;
  if new.sex is not null and new.sex not in ('female','male') then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;
  return new;
end;
$$;
revoke all on function public.enforce_sinjira_account_safety_age() from public,anon,authenticated;

-- Privacy-by-default dès la première consommation/réactivation d'un code parental V25.
-- Le trigger historique sync_guardian_signup_invite_link_trigger appelle cette fonction :
-- sa logique doit donc être sûre avant que handle_new_sinjira_user ou child_pending ne
-- consomme une invitation, sans attendre une migration de minimisation ultérieure.
create or replace function public.sync_guardian_signup_invite_link()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $guardian_sync$
begin
  if new.used_at is not null and new.minor_user_id is not null then
    insert into public.guardian_links(
      minor_user_id,guardian_user_id,status,guardian_role,
      can_view_contact_metadata,consented_at,revoked_at
    )
    values(
      new.minor_user_id,new.guardian_user_id,'verified','parent',
      false,new.consented_at,null
    )
    on conflict(minor_user_id,guardian_user_id) do update
      set status='verified',
          guardian_role='parent',
          can_view_contact_metadata=false,
          consented_at=excluded.consented_at,
          revoked_at=null,
          updated_at=now();
  end if;
  return new;
end;
$guardian_sync$;
revoke all on function public.sync_guardian_signup_invite_link()
from public,anon,authenticated;

comment on function public.sync_guardian_signup_invite_link() is
  'V25 privacy-by-default: toute création ou réactivation de supervision via invitation remet can_view_contact_metadata à false.';

-- guardian_code est une capacité à usage unique. Elle est retirée des métadonnées Auth
-- dès la même migration qui ouvre l'inscription enfant, sans fenêtre de conservation.
create or replace function private.sinjira_strip_guardian_signup_secret()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,auth
as $guardian_secret$
begin
  if coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'guardian_code' then
    update auth.users
    set raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'
    where id=new.id;
  end if;
  return new;
end;
$guardian_secret$;

revoke all on function private.sinjira_strip_guardian_signup_secret()
from public,anon,authenticated;

drop trigger if exists zz_sinjira_strip_guardian_signup_secret
on auth.users;

create trigger zz_sinjira_strip_guardian_signup_secret
after insert on auth.users
for each row
when (coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'guardian_code')
execute function private.sinjira_strip_guardian_signup_secret();

-- Nettoyage des comptes déjà créés avant cette frontière V25.
update auth.users
set raw_user_meta_data=coalesce(raw_user_meta_data,'{}'::jsonb)-'guardian_code'
where coalesce(raw_user_meta_data,'{}'::jsonb) ? 'guardian_code';

comment on function private.sinjira_strip_guardian_signup_secret() is
  'V25 initial: guardian_code est retiré des métadonnées Auth après création; les secrets historiques résiduels sont aussi purgés.';

-- 11–12 ans : bande `child`, volontairement exclue des autorisations sociales existantes.
-- À 13 ans, la bande est recalculée automatiquement depuis la date de naissance et devient `youth`
-- lorsque le lien de supervision est toujours vérifié.
create or replace function public.sinjira_age_band(p_user_id uuid default auth.uid())
returns text
language sql
stable
security definer
set search_path=pg_catalog,public,auth
as $$
  select case
    when exists(
      select 1
      from auth.users u
      where u.id=p_user_id
        and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
    ) then 'adult'
    when s.user_id is null or s.date_of_birth is null or s.date_of_birth>current_date then 'unverified'
    when s.legacy_status='memorialized' then 'memorial'
    when age(current_date,s.date_of_birth)<interval '11 years' then 'under11'
    when age(current_date,s.date_of_birth)<interval '13 years' then
      case
        when exists(
          select 1 from public.guardian_links g
          where g.minor_user_id=s.user_id and g.status='verified' and g.revoked_at is null
        ) then 'child'
        else 'child_pending'
      end
    when age(current_date,s.date_of_birth)<interval '18 years' then
      case
        when exists(
          select 1 from public.guardian_links g
          where g.minor_user_id=s.user_id and g.status='verified' and g.revoked_at is null
        ) then 'youth'
        else 'youth_pending'
      end
    else 'adult'
  end
  from (select p_user_id user_id) x
  left join public.account_safety_profiles s on s.user_id=x.user_id;
$$;
revoke all on function public.sinjira_age_band(uuid) from public,anon,authenticated;
grant execute on function public.sinjira_age_band(uuid) to service_role;

revoke all on function public.sinjira_my_age_band() from public,anon,authenticated;
grant execute on function public.sinjira_my_age_band() to anon,authenticated,service_role;

-- Un parent peut superviser un compte enfant ou jeunesse lié et vérifié.
create or replace function public.sinjira_parent_can_supervise(p_parent uuid,p_child uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public
as $$
  select public.sinjira_age_band(p_parent)='adult'
    and public.sinjira_age_band(p_child) in ('child','youth')
    and exists(
      select 1 from public.guardian_links g
      where g.guardian_user_id=p_parent
        and g.minor_user_id=p_child
        and g.status='verified'
        and g.revoked_at is null
    );
$$;
revoke all on function public.sinjira_parent_can_supervise(uuid,uuid) from public,anon,authenticated;
grant execute on function public.sinjira_parent_can_supervise(uuid,uuid) to service_role;

-- La supervision historique reste privée au compte concerné après sa majorité.
-- L'ancien tuteur ne conserve aucune visibilité une fois la bande devenue adult.
create or replace function public.sinjira_can_read_guardian_link(p_link_id uuid)
returns boolean
language sql
stable
security definer
set search_path=pg_catalog,public
as $guardian_visibility$
  select coalesce((
    select case
      when auth.uid()=g.minor_user_id then true
      when auth.uid()=g.guardian_user_id
        then public.sinjira_age_band(g.minor_user_id) in (
          'child','child_pending','youth','youth_pending'
        )
      else false
    end
    from public.guardian_links g
    where g.id=p_link_id
  ),false);
$guardian_visibility$;

revoke all on function public.sinjira_can_read_guardian_link(uuid)
from public,anon,authenticated;
grant execute on function public.sinjira_can_read_guardian_link(uuid)
to authenticated;

drop policy if exists guardian_read_parties on public.guardian_links;
drop policy if exists guardian_read_parties_age_bounded on public.guardian_links;

create policy guardian_read_parties_age_bounded
on public.guardian_links
for select
to authenticated
using (public.sinjira_can_read_guardian_link(id));

-- Les codes parentaux deviennent une capacité d'accès dès l'ouverture du parcours 11 ans.
-- Leur émission et leur relecture exigent donc AAL2 dès cette migration, sans fenêtre AAL1.
create or replace function public.create_guardian_signup_invite()
returns text
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $guardian_invite$
declare
  uid uuid:=auth.uid();
  v_code text;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if public.sinjira_age_band(uid)<>'adult' then
    raise exception 'ADULT_GUARDIAN_REQUIRED';
  end if;
  if coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;
  if not public.sinjira_mfa_access_allowed(uid) then
    raise exception 'MFA_REQUIRED';
  end if;

  delete from public.guardian_signup_invites
  where guardian_user_id=uid
    and used_at is null;

  loop
    v_code:='YOUTH-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,10));
    exit when not exists(
      select 1 from public.guardian_signup_invites where invite_code=v_code
    );
  end loop;

  insert into public.guardian_signup_invites(guardian_user_id,invite_code)
  values(uid,v_code);

  return v_code;
end;
$guardian_invite$;

revoke all on function public.create_guardian_signup_invite()
from public,anon;
grant execute on function public.create_guardian_signup_invite()
to authenticated;

drop policy if exists guardian_signup_invites_own
on public.guardian_signup_invites;
drop policy if exists guardian_signup_invites_own_aal2
on public.guardian_signup_invites;

create policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites
for select
to authenticated
using (
  (select auth.uid())=guardian_user_id
  and coalesce(auth.jwt()->>'aal','aal1')='aal2'
  and (
    minor_user_id is null
    or exists(
      select 1
      from public.guardian_links g
      where g.guardian_user_id=(select auth.uid())
        and g.minor_user_id=guardian_signup_invites.minor_user_id
    )
  )
);

revoke all on table public.guardian_signup_invites from anon;
grant select on table public.guardian_signup_invites to authenticated;

-- La révocation par le tuteur est sensible et exige AAL2.
-- Le mineur lié garde une voie de sortie immédiate, sans dépendre du second facteur du tuteur.
create or replace function public.revoke_guardian_link(p_link_id uuid)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $guardian_revoke$
declare
  uid uuid:=auth.uid();
  r public.guardian_links%rowtype;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  select * into r
  from public.guardian_links
  where id=p_link_id
  for update;

  if r.id is null then raise exception 'GUARDIAN_LINK_NOT_FOUND'; end if;
  if uid not in (r.guardian_user_id,r.minor_user_id) then
    raise exception 'GUARDIAN_LINK_FORBIDDEN';
  end if;

  if r.status='revoked' or r.revoked_at is not null then
    return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
  end if;

  if uid=r.guardian_user_id
     and coalesce(auth.jwt()->>'aal','aal1')<>'aal2' then
    raise exception 'MFA_AAL2_REQUIRED';
  end if;

  update public.guardian_links
  set status='revoked',
      revoked_at=now(),
      updated_at=now()
  where id=r.id;

  return jsonb_build_object('ok',true,'status','revoked','link_id',r.id);
end;
$guardian_revoke$;

revoke all on function public.revoke_guardian_link(uuid)
from public,anon;
grant execute on function public.revoke_guardian_link(uuid)
to authenticated;

-- Défense en profondeur : tout lien actif créé ou réactivé repart sans permission
-- de métadonnées. Les permissions historiques implicites sont retirées immédiatement.
alter table public.guardian_links
  alter column can_view_contact_metadata set default false;

create or replace function private.sinjira_guardian_contact_metadata_default_off()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public
as $guardian_metadata$
begin
  if new.status='verified' and new.revoked_at is null then
    new.can_view_contact_metadata:=false;
  end if;
  return new;
end;
$guardian_metadata$;

revoke all on function private.sinjira_guardian_contact_metadata_default_off()
from public,anon,authenticated;

drop trigger if exists guardian_contact_metadata_default_off
on public.guardian_links;

create trigger guardian_contact_metadata_default_off
before insert or update of status,revoked_at
on public.guardian_links
for each row
execute function private.sinjira_guardian_contact_metadata_default_off();

update public.guardian_links
set can_view_contact_metadata=false,
    updated_at=now()
where status='verified'
  and revoked_at is null
  and can_view_contact_metadata is true;

comment on function public.create_guardian_signup_invite() is
  'V25 initial: code parental réservé à un adulte AAL2; anciens codes ouverts invalidés.';
comment on function public.sinjira_can_read_guardian_link(uuid) is
  'V25 initial: le compte concerné garde son historique; le tuteur ne voit le lien que tant que le compte est mineur.';
comment on policy guardian_read_parties_age_bounded
on public.guardian_links is
  'V25 initial: visibilité tuteur automatiquement coupée au passage à adult.';
comment on policy guardian_signup_invites_own_aal2
on public.guardian_signup_invites is
  'V25 initial: AAL2 self-only; invitation consommée lisible uniquement tant que le guardian_link reste visible.';
comment on function public.revoke_guardian_link(uuid) is
  'V25 initial: tuteur AAL2 pour révoquer; mineur lié peut sortir immédiatement.';
comment on function private.sinjira_guardian_contact_metadata_default_off() is
  'V25 initial privacy-by-default: création/réactivation de guardian_link remet la permission de métadonnées à false.';

-- IMPORTANT : cette frontière est volontairement installée avant le hook de création
-- de compte enfant. Une migration ultérieure la réapplique comme convergence, mais aucun
-- compte 11–12 ne doit exister même transitoirement sans ces refus côté base.
-- Frontière serveur 11–12 ans activée dès l'ouverture du parcours enfant.
-- La navigation Junior est fail-closed, mais la sécurité ne dépend jamais de l'interface.
-- Toute mutation sensible déclenchée par un compte child est refusée côté base.

create or replace function private.sinjira_child_sensitive_write_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $child$
declare
  uid uuid:=auth.uid();
  band text;
  target_band text;
begin
  if uid is not null then
    band:=public.sinjira_age_band(uid);
    if band='child' then
      raise exception 'CHILD_ACTION_NOT_AVAILABLE_11_12' using errcode='42501';
    elsif coalesce(band,'unverified') not in ('adult','youth') then
      raise exception 'ACCOUNT_ACTION_NOT_AVAILABLE_RESTRICTED' using errcode='42501';
    end if;
  end if;

  -- Un adulte/admin ne peut pas créer ou maintenir une participation Playtest
  -- ciblant un compte child ou une bande restreinte. DELETE reste permis pour nettoyage.
  if tg_table_name='playtest_participants' and tg_op<>'DELETE' then
    target_band:=public.sinjira_age_band(new.user_id);
    if target_band='child' then
      raise exception 'CHILD_TARGET_NOT_AVAILABLE_11_12' using errcode='42501';
    elsif coalesce(target_band,'unverified') not in ('adult','youth') then
      raise exception 'ACCOUNT_TARGET_NOT_AVAILABLE_RESTRICTED' using errcode='42501';
    end if;
  end if;

  if tg_op='DELETE' then return old; end if;
  return new;
end;
$child$;
revoke all on function private.sinjira_child_sensitive_write_guard() from public,anon,authenticated;

do $child$
declare t text;
begin
  foreach t in array array[
    'access_requests','playtest_participants',
    'parallel_responses','parallel_character_state',
    'market_listings','market_favorites',
    'license_redemptions','product_preorders','orders','order_items',
    'employment_profiles','employment_applications',
    'game_sessions','player_sheets','endgame_sheets',
    'novel_comments','reader_comments','sinjira_novel_comments'
  ] loop
    if to_regclass('public.'||t) is not null then
      execute format('drop trigger if exists sinjira_child_sensitive_write_guard on public.%I',t);
      execute format('create trigger sinjira_child_sensitive_write_guard before insert or update or delete on public.%I for each row execute function private.sinjira_child_sensitive_write_guard()',t);
    end if;
  end loop;
end;
$child$;

-- Le consentement recherche/contribution reste modifiable vers OFF, jamais vers ON à 11–12 ans.
create or replace function private.sinjira_child_research_consent_guard()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $child$
declare
  uid uuid:=auth.uid();
  band text;
begin
  if uid is not null then
    band:=public.sinjira_age_band(uid);
  end if;
  if uid is not null and coalesce(band,'unverified') not in ('adult','youth') then
    new.participate:=false;
    new.share_free_text:=false;
    new.consented_at:=null;
  end if;
  return new;
end;
$child$;
revoke all on function private.sinjira_child_research_consent_guard() from public,anon,authenticated;

drop trigger if exists sinjira_child_research_consent_guard on public.research_consents;
create trigger sinjira_child_research_consent_guard
before insert or update on public.research_consents
for each row execute function private.sinjira_child_research_consent_guard();

-- Les contenus de compte/projet non encore classés pour 11–12 ans ne sont pas délivrés au child.
-- Les contenus réellement publics restent visibles comme ils le seraient sans connexion.
drop policy if exists "projects readable when accessible" on public.projects;
create policy "projects readable when accessible" on public.projects for select to anon,authenticated
using(
  status<>'draft' and (
    visibility='public'
    or (
      (select auth.uid()) is not null
      and public.sinjira_my_age_band() in ('adult','youth')
      and (visibility='account' or public.project_access_rank(id,(select auth.uid()))>=20)
    )
  )
);

drop policy if exists "approved documents visible by access" on public.documents;
create policy "approved documents visible by access" on public.documents for select to anon,authenticated
using(
  status='approved'
  and public.project_access_rank(project_id,(select auth.uid()))>=public.document_access_rank(access_level)
  and (
    (select auth.uid()) is null
    or public.sinjira_my_age_band() in ('adult','youth')
    or (
      public.sinjira_my_age_band()='child'
      and access_level='public'
      and exists(
        select 1 from public.projects p
        where p.id=project_id and p.visibility='public' and p.status<>'draft'
      )
    )
  )
);

-- Une seule politique SELECT Playtests doit rester active. Les anciennes politiques
-- permissives seraient combinées par OR et pourraient sinon contourner la fermeture child.
drop policy if exists "playtests readable" on public.playtests;
drop policy if exists playtests_read on public.playtests;
drop policy if exists admin_read_all_playtests on public.playtests;
drop policy if exists playtests_read_authorized on public.playtests;
create policy playtests_read_authorized on public.playtests for select to authenticated
using(
  (select auth.uid()) is not null
  and public.sinjira_my_age_band() in ('adult','youth')
  and (
    public.is_sinjira_admin((select auth.uid()))
    or exists(
      select 1
      from public.playtest_participants pp
      where pp.playtest_id=playtests.id
        and pp.user_id=(select auth.uid())
    )
    or (
      status in ('open','active')
      and public.project_access_rank(project_id,(select auth.uid()))>=case required_access
        when 'tester' then 30
        when 'player' then 20
        else 10
      end
    )
  )
);

-- Même règle pour l'historique des participations : un ancien compte 12 ans
-- devenu child ne doit pas pouvoir relire ses anciennes participations.
drop policy if exists "participants own select" on public.playtest_participants;
drop policy if exists playtest_participants_select_own on public.playtest_participants;
drop policy if exists admin_read_all_playtest_participants on public.playtest_participants;
drop policy if exists playtest_participants_read_authorized on public.playtest_participants;
create policy playtest_participants_read_authorized on public.playtest_participants for select to authenticated
using(
  (select auth.uid()) is not null
  and public.sinjira_my_age_band() in ('adult','youth')
  and (
    (select auth.uid())=user_id
    or public.is_sinjira_admin((select auth.uid()))
  )
);

drop policy if exists "requests own insert" on public.access_requests;
create policy "requests own insert" on public.access_requests for insert to authenticated
with check(
  (select auth.uid())=user_id
  and public.sinjira_my_age_band() in ('adult','youth')
  and status='pending'
);

drop policy if exists "participants own apply" on public.playtest_participants;
create policy "participants own apply" on public.playtest_participants for insert to authenticated
with check(
  (select auth.uid())=user_id
  and public.sinjira_my_age_band() in ('adult','youth')
  and status='applied'
);

comment on function private.sinjira_child_sensitive_write_guard() is
  'Refuse côté base toute mutation vers les modules non certifiés 11–12 ans, indépendamment de la navigation client.';

-- Toute bande mineure, pending, non vérifiée ou future/inconnue doit être protégée
-- dès que child existe, sans attendre une migration de convergence ultérieure.
-- Classifieur de contenu fail-closed activé dès l'apparition des bandes child/child_pending.
-- Forward-only : la migration V24.4.82 reste immuable.
-- La garde de messagerie mineur doit reconnaître child/child_pending et échouer fermé
-- pour toute bande non adulte ou inconnue.

create or replace function private.sinjira_content_policy_code(
  p_body text,
  p_actor_user_id uuid,
  p_recipient_user_id uuid default null,
  p_surface text default 'content'
)
returns text
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare
  v text:=lower(coalesce(p_body,''));
  v_actor_band text:=public.sinjira_age_band(p_actor_user_id);
  v_recipient_band text:=case when p_recipient_user_id is null then null else public.sinjira_age_band(p_recipient_user_id) end;
  -- V25 fail-closed: seules les bandes explicitement adultes/mémorialisées
  -- sortent de la garde renforcée. Toute bande mineure, pending, non vérifiée
  -- ou future/inconnue reste protégée.
  v_youth boolean:=coalesce(v_actor_band not in ('adult','memorial'),true)
    or (
      p_recipient_user_id is not null
      and coalesce(v_recipient_band not in ('adult','memorial'),true)
    );
  v_message boolean:=coalesce(p_surface,'') in ('message','dating_message');
  v_external boolean;
  v_commerce boolean;
  v_sexual boolean;
  v_drugs boolean;
begin
  if btrim(v)='' then return null; end if;

  v_external := v ~ '(https?://|www\.|onlyfans\.|fansly\.|telegram|whatsapp|snapchat|discord|instagram|signal app|t\.me/|@[a-z0-9_]{3,}|[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}|[+]?([0-9][ ()\.\-]?){7,}[0-9])';
  v_commerce := v ~ '(je vends|j[’'']?offre|a vendre|à vendre|prix|tarif|paiement|payer pour|paye[- ]?moi|paie[- ]?moi|cash|virement|crypto|abonnement|abonne[- ]?toi|abonnez[- ]?vous|subscribe|subscription|premium|viens en dm|viens en mp|ecris[- ]?moi|écris[- ]?moi|contacte[- ]?moi|commande|livraison|dollars?|euros?|\$|€)';
  v_sexual := v ~ '(prostitut|escort(e|es|ing)?|prox[eé]n[eé]t|pimp|service[s]? sexuel|massage [eé]rotique|sexe contre argent|contenu adulte|contenu sexuel payant|photo[s]? nue[s]?|nude[s]?|sexting|camgirl|camboy|webcam sex|onlyfans|fansly)';
  v_drugs := v ~ '(drogue[s]?|coca[iï]ne|crack|h[eé]ro[iï]ne|fentanyl|m[eé]thamph[eé]tamine|\mmeth\M|mdma|ecstasy|ghb|lsd|k[eé]tamine|opio[iï]de[s]?)';

  -- Toute promotion/vente de contenu sexuel payant ou de services sexuels est interdite.
  if (v ~ '(onlyfans|fansly|contenu adulte|contenu sexuel payant|photo[s]? nue[s]?|nude[s]?|camgirl|camboy|webcam sex)')
     and (v_commerce or v_external) then
    return 'PAID_SEXUAL_CONTENT';
  end if;

  if (v ~ '(prostitut|escort(e|es|ing)?|prox[eé]n[eé]t|pimp|service[s]? sexuel|massage [eé]rotique|sexe contre argent)')
     and (v_commerce or v_external or v ~ 'sexe contre argent') then
    return 'SEXUAL_EXPLOITATION';
  end if;

  -- Vente/traite de personnes : tolérance zéro lorsqu'une intention transactionnelle ou de contact est présente.
  if (v ~ '(traite des personnes|trafic humain|human trafficking|vente de personne|vente de personnes|personne a vendre|personne à vendre|fille a vendre|fille à vendre|femme a vendre|femme à vendre|acheter une personne|acheter une fille|acheter une femme)')
     and (v_commerce or v_external) then
    return 'HUMAN_TRAFFICKING';
  end if;

  -- Le site ne peut pas servir de marché de drogues.
  if v_drugs and v_commerce then
    return 'ILLICIT_DRUG_SALES';
  end if;

  -- Garde renforcée pour toute messagerie impliquant une personne mineure/jeunesse.
  if v_youth and v_message then
    if v_external then
      return 'MINOR_OFF_PLATFORM_CONTACT';
    end if;
    if v_sexual or v ~ '(photo intime|photo[s]? sexy|envoie.*photo|montre[- ]?moi.*corps|rencontre sexuelle|viens chez moi|viens seul|viens seule|garde [cç]a secret|ne dis pas.*parent|ne le dis pas.*parent)' then
      return 'MINOR_SEXUAL_SOLICITATION';
    end if;
    if v ~ '(envoie[- ]?moi.*argent|donne[- ]?moi.*argent|paye[- ]?moi|paie[- ]?moi|carte cadeau|gift card|virement|crypto)' then
      return 'MINOR_FINANCIAL_SOLICITATION';
    end if;
  end if;

  return null;
end;
$$;

revoke all on function private.sinjira_content_policy_code(text,uuid,uuid,text) from public,anon,authenticated;
grant execute on function private.sinjira_content_policy_code(text,uuid,uuid,text) to service_role;

comment on function private.sinjira_content_policy_code(text,uuid,uuid,text) is
'Classifie côté serveur les sollicitations interdites; V25 traite toute bande autre que adult/memorial comme protégée pour la messagerie afin de rester fail-closed.';

create or replace function public.handle_new_sinjira_user()
returns trigger
language plpgsql
security definer
set search_path=pg_catalog,public,auth
as $$
declare
  c boolean:=coalesce((new.raw_user_meta_data->>'initial_contributor_opt_in')::boolean,false);
  f boolean:=coalesce((new.raw_user_meta_data->>'initial_share_free_text')::boolean,false);
  dob date;
  sx text;
  raw_dob text;
  raw_sex text;
  years integer;
  guardian_code text:=upper(trim(coalesce(new.raw_user_meta_data->>'guardian_code','')));
  residence_country text:=lower(trim(coalesce(new.raw_user_meta_data->>'residence_country','')));
  inv public.guardian_signup_invites%rowtype;
begin
  raw_dob:=coalesce(nullif(new.raw_user_meta_data->>'birth_date',''),nullif(new.raw_user_meta_data->>'date_of_birth',''));
  begin dob:=raw_dob::date; exception when others then dob:=null; end;
  if dob is null then raise exception 'BIRTH_DATE_REQUIRED'; end if;
  if dob>current_date then raise exception 'INVALID_BIRTH_DATE'; end if;
  years:=extract(year from age(current_date,dob))::integer;
  if years<11 then raise exception 'SINJIRA_MINIMUM_AGE_11'; end if;
  if years>120 then raise exception 'INVALID_BIRTH_DATE'; end if;

  -- Le lancement jeunesse reste limité au Canada jusqu'à validation spécifique d'autres juridictions.
  if years<18 and residence_country not in ('canada','ca','can') then
    raise exception 'YOUTH_JURISDICTION_NOT_ENABLED';
  end if;

  raw_sex:=trim(coalesce(new.raw_user_meta_data->>'gender',new.raw_user_meta_data->>'sex',''));
  sx:=case lower(raw_sex)
    when 'femme' then 'female' when 'female' then 'female'
    when 'homme' then 'male' when 'male' then 'male'
    else null end;
  if sx is null then raise exception 'SEX_REQUIRED_FEMALE_OR_MALE'; end if;

  -- 11, 12 et 13 ans : aucun compte sans autorisation parentale/tuteur vérifiée.
  if years<14 then
    if guardian_code='' then raise exception 'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14'; end if;
    select * into inv from public.guardian_signup_invites
      where invite_code=guardian_code and used_at is null and expires_at>now()
      for update;
    if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
    if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  elsif guardian_code<>'' then
    select * into inv from public.guardian_signup_invites
      where invite_code=guardian_code and used_at is null and expires_at>now()
      for update;
    if inv.id is null then raise exception 'INVALID_OR_EXPIRED_GUARDIAN_CODE'; end if;
    if public.sinjira_age_band(inv.guardian_user_id)<>'adult' then raise exception 'ADULT_GUARDIAN_REQUIRED'; end if;
  end if;

  -- Les comptes enfants 11–12 ans ne participent jamais au Programme Contributeur.
  if years<13 then
    c:=false;
    f:=false;
  end if;

  insert into public.profiles(user_id,pseudo,display_name)
    values(new.id,coalesce(nullif(new.raw_user_meta_data->>'pseudo',''),'Joueur SINJIRA'),nullif(new.raw_user_meta_data->>'display_name',''))
    on conflict(user_id) do update set pseudo=excluded.pseudo,display_name=excluded.display_name,updated_at=now();

  insert into public.research_consents(user_id,participate,share_free_text,consent_version,consented_at)
    values(new.id,c,c and f,'sinjira-gameplay-v2',case when c then now() else null end)
    on conflict(user_id) do nothing;

  insert into public.account_safety_profiles(user_id,date_of_birth,sex,birthday_greeting_opt_in,real_life_to_fiction_opt_in,relationship_data_opt_in,relationship_status,legacy_status)
    values(new.id,dob,sx,true,false,false,'not_specified','active')
    on conflict(user_id) do update set date_of_birth=excluded.date_of_birth,sex=excluded.sex,updated_at=now();

  insert into public.account_legacy_preferences(user_id,account_after_death,final_story_tone,memorial_public_opt_in,transfer_private_story_to_family)
    values(new.id,'memorialize','peaceful',true,false)
    on conflict(user_id) do nothing;

  if inv.id is not null and years<18 then
    insert into public.guardian_links(minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at)
      values(new.id,inv.guardian_user_id,'verified','parent',false,inv.consented_at)
      on conflict do nothing;
    update public.guardian_signup_invites
      set used_at=now(),minor_user_id=new.id
      where id=inv.id;
  end if;

  return new;
end;
$$;
revoke all on function public.handle_new_sinjira_user() from public,anon,authenticated;

-- SINJIRA™ V24.1 — correctifs observés en production
-- - restaure/synchronise le personnage AbyssTime du propriétaire
-- - donne au compte propriétaire un accès permanent à tous les projets/produits/romans
-- - définit les jetons du propriétaire comme illimités côté serveur
-- - ajoute les notifications internes du Registre
-- - corrige l'ambiguïté party_code des RPC Fracture Online

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- NOTIFICATIONS ADMIN INTERNES : un questionnaire ne dépend plus d'un courriel
-- ---------------------------------------------------------------------------
create table if not exists public.admin_notifications (
  id uuid primary key default gen_random_uuid(),
  notification_type text not null,
  title text not null,
  body text,
  related_user_id uuid references auth.users(id) on delete set null,
  related_entity_type text,
  related_entity_id uuid,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists admin_notifications_unread_idx
  on public.admin_notifications(is_read,created_at desc);
alter table public.admin_notifications enable row level security;
revoke all on public.admin_notifications from anon, authenticated;

-- ---------------------------------------------------------------------------
-- IDENTITÉ DU PROPRIÉTAIRE : source de vérité serveur
-- ---------------------------------------------------------------------------
create or replace function public.is_sinjira_owner(p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select exists(
    select 1 from auth.users u
    where u.id=p_user_id and lower(coalesce(u.email,''))='kingtyrano@gmail.com'
  );
$$;
revoke all on function public.is_sinjira_owner(uuid) from public,anon;
grant execute on function public.is_sinjira_owner(uuid) to authenticated,service_role;

create or replace function public.get_sinjira_account_capabilities()
returns jsonb
language sql
stable
security definer
set search_path=public,auth
as $$
  select case when public.is_sinjira_owner(auth.uid()) then
    jsonb_build_object(
      'owner',true,
      'unlimited_tokens',true,
      'all_content',true,
      'all_games',true,
      'all_romans',true,
      'all_licenses',true,
      'admin',true
    )
  else
    jsonb_build_object(
      'owner',false,
      'unlimited_tokens',false,
      'all_content',false,
      'all_games',false,
      'all_romans',false,
      'all_licenses',false,
      'admin',false
    )
  end;
$$;
revoke all on function public.get_sinjira_account_capabilities() from public,anon;
grant execute on function public.get_sinjira_account_capabilities() to authenticated;

-- Toute future vérification de licence doit passer par cette fonction.
create or replace function public.has_sinjira_product(p_product_slug text,p_user_id uuid default auth.uid())
returns boolean
language sql
stable
security definer
set search_path=public,auth
as $$
  select public.is_sinjira_owner(p_user_id)
  or exists(
    select 1
    from public.user_entitlements ue
    join public.products p on p.id=ue.product_id
    where ue.user_id=p_user_id and p.slug=p_product_slug and p.active=true
  );
$$;
revoke all on function public.has_sinjira_product(text,uuid) from public,anon;
grant execute on function public.has_sinjira_product(text,uuid) to authenticated,service_role;

-- Débit de jetons côté serveur. Le propriétaire ne consomme jamais de jetons.
create or replace function public.spend_sinjira_tokens(
  p_amount integer,
  p_entry_type text,
  p_description text default null,
  p_reference_type text default null,
  p_reference_id uuid default null
)
returns boolean
language plpgsql
security definer
set search_path=public,auth
as $$
declare
  uid uuid:=auth.uid();
  bal bigint;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;
  if p_amount is null or p_amount <= 0 then raise exception 'INVALID_TOKEN_AMOUNT'; end if;
  if public.is_sinjira_owner(uid) then return true; end if;

  perform pg_advisory_xact_lock(hashtext(uid::text));
  select coalesce(sum(amount),0) into bal from public.token_ledger where user_id=uid;
  if bal < p_amount then return false; end if;

  insert into public.token_ledger(user_id,amount,entry_type,description,reference_type,reference_id)
  values(uid,-p_amount,p_entry_type,p_description,p_reference_type,p_reference_id);
  return true;
end;
$$;
revoke all on function public.spend_sinjira_tokens(integer,text,text,text,uuid) from public,anon;
grant execute on function public.spend_sinjira_tokens(integer,text,text,text,uuid) to authenticated;

-- ---------------------------------------------------------------------------
-- SYNCHRONISATION DU COMPTE ABYSSTIME
-- ---------------------------------------------------------------------------
do $$
declare
  v_user uuid;
  v_submission uuid;
  v_character uuid;
begin
  select id into v_user from auth.users where lower(email)='kingtyrano@gmail.com' limit 1;
  if v_user is null then
    raise notice 'Compte propriétaire kingtyrano@gmail.com non trouvé; synchronisation reportée.';
    return;
  end if;

  insert into public.internal_admin_users(user_id)
  values(v_user)
  on conflict(user_id) do nothing;

  insert into public.profiles(user_id,pseudo,display_name)
  values(v_user,'AbyssTime','Benoit Cantin')
  on conflict(user_id) do update set
    pseudo='AbyssTime',display_name='Benoit Cantin',updated_at=now();

  select id into v_submission
  from public.character_submissions
  where user_id=v_user
  order by created_at desc
  limit 1;

  -- On garde les anciennes soumissions comme historique au lieu de les supprimer.
  update public.character_submissions
  set status='archived',updated_at=now()
  where user_id=v_user and id is distinct from v_submission and status not in ('archived','published');

  select id into v_character from public.characters where user_id=v_user order by updated_at desc limit 1;

  if v_character is null then
    insert into public.characters(
      submission_id,user_id,public_name,public_description,portrait_path,status,
      novel_id,novel_note,bible,ai_generated,visible_to_user,canon_status,canon_version
    ) values(
      v_submission,v_user,'AbyssTime','Personnage officiel associé au compte de Benoit Cantin.',
      '/assets/media/characters/abysstime.webp','assigned',null,
      'SINJIRA — Livre II (titre à confirmer)',
      jsonb_build_object(
        'owner','Benoit Cantin',
        'account','AbyssTime',
        'placement','SINJIRA — Livre II (titre à confirmer)',
        'source','Synchronisation propriétaire V24.1',
        'notes','Compléter la Bible narrative depuis l’administration SINJIRA™.'
      ),false,true,'PROVISOIRE','v1.0'
    ) returning id into v_character;
  else
    update public.characters
    set submission_id=coalesce(v_submission,submission_id),
        public_name='AbyssTime',
        public_description=coalesce(nullif(public_description,''),'Personnage officiel associé au compte de Benoit Cantin.'),
        portrait_path='/assets/media/characters/abysstime.webp',
        status='assigned',
        novel_id=null,
        novel_note='SINJIRA — Livre II (titre à confirmer)',
        visible_to_user=true,
        canon_status=coalesce(canon_status,'PROVISOIRE'),
        updated_at=now()
    where id=v_character;
  end if;

  if v_submission is not null then
    update public.character_submissions set status='assigned',updated_at=now() where id=v_submission;
  end if;

  -- Garantit aussi la fiche sociale du personnage, même si un ancien trigger n'avait pas tourné.
  if to_regclass('public.character_social_profiles') is not null then
    insert into public.character_social_profiles(character_id,user_id,public_name,public_description,portrait_path,status,updated_at)
    select c.id,c.user_id,c.public_name,c.public_description,c.portrait_path,c.status,now()
    from public.characters c where c.id=v_character
    on conflict(character_id) do update set
      user_id=excluded.user_id,public_name=excluded.public_name,
      public_description=excluded.public_description,portrait_path=excluded.portrait_path,
      status=excluded.status,updated_at=now();
  end if;

  -- Accès testeur/propriétaire à tous les projets existants.
  insert into public.project_access(user_id,project_id,access_level,granted_by,source)
  select v_user,p.id,'tester',v_user,'migration' from public.projects p
  on conflict(user_id,project_id) do update set
    access_level='tester',granted_by=v_user,source='migration',expires_at=null,updated_at=now();

  -- Accès permanent à tous les produits existants, actifs ou futurs lorsqu'ils seront activés.
  insert into public.user_entitlements(user_id,product_id,source)
  select v_user,p.id,'owner' from public.products p
  on conflict(user_id,product_id) do nothing;

  -- Tous les romans existants apparaissent dans la bibliothèque du propriétaire.
  insert into public.reader_library(user_id,novel_id,last_opened_at)
  select v_user,n.id,now() from public.novels n
  on conflict(user_id,novel_id) do nothing;

  -- Prépare sa Chronique privée si la fondation Monde parallèle est installée.
  if to_regclass('public.parallel_character_state') is not null and v_character is not null then
    insert into public.parallel_character_state(character_id,user_id,private_summary,state)
    values(v_character,v_user,'Chronique propriétaire prête à être initialisée.','{}'::jsonb)
    on conflict(character_id) do update set user_id=excluded.user_id,updated_at=now();
  end if;
end $$;

-- Donne automatiquement au propriétaire tout nouveau projet.
create or replace function public.grant_owner_project_access()
returns trigger
language plpgsql
security definer
set search_path=public,auth
as $$
declare owner_id uuid;
begin
  select id into owner_id from auth.users where lower(email)='kingtyrano@gmail.com' limit 1;
  if owner_id is not null then
    insert into public.project_access(user_id,project_id,access_level,granted_by,source)
    values(owner_id,new.id,'tester',owner_id,'migration')
    on conflict(user_id,project_id) do update set access_level='tester',expires_at=null,updated_at=now();
  end if;
  return new;
end;
$$;
drop trigger if exists grant_owner_project_access_trigger on public.projects;
create trigger grant_owner_project_access_trigger after insert or update on public.projects
for each row execute function public.grant_owner_project_access();

-- Donne automatiquement au propriétaire tout nouveau produit.
create or replace function public.grant_owner_product_entitlement()
returns trigger
language plpgsql
security definer
set search_path=public,auth
as $$
declare owner_id uuid;
begin
  select id into owner_id from auth.users where lower(email)='kingtyrano@gmail.com' limit 1;
  if owner_id is not null then
    insert into public.user_entitlements(user_id,product_id,source)
    values(owner_id,new.id,'owner') on conflict(user_id,product_id) do nothing;
  end if;
  return new;
end;
$$;
drop trigger if exists grant_owner_product_entitlement_trigger on public.products;
create trigger grant_owner_product_entitlement_trigger after insert or update on public.products
for each row execute function public.grant_owner_product_entitlement();

-- Ajoute automatiquement tout nouveau roman à la bibliothèque du propriétaire.
create or replace function public.grant_owner_novel_library()
returns trigger
language plpgsql
security definer
set search_path=public,auth
as $$
declare owner_id uuid;
begin
  select id into owner_id from auth.users where lower(email)='kingtyrano@gmail.com' limit 1;
  if owner_id is not null then
    insert into public.reader_library(user_id,novel_id,last_opened_at)
    values(owner_id,new.id,now()) on conflict(user_id,novel_id) do nothing;
  end if;
  return new;
end;
$$;
drop trigger if exists grant_owner_novel_library_trigger on public.novels;
create trigger grant_owner_novel_library_trigger after insert or update on public.novels
for each row execute function public.grant_owner_novel_library();

-- ---------------------------------------------------------------------------
-- FRACTURE ONLINE — correction « column reference party_code is ambiguous »
-- ---------------------------------------------------------------------------
create or replace function public.create_fracture_party(
  p_human_player_count integer,
  p_round_count integer default 10,
  p_duo_first_player_seat integer default 1
)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql
security definer
set search_path=public
as $$
declare uid uuid:=auth.uid(); pid uuid; code text; eff integer; mode text; rounds integer; project_uuid uuid;
begin
  if uid is null then raise exception 'Connexion requise.'; end if;
  if p_human_player_count not between 1 and 20 then raise exception 'Nombre de joueurs invalide.'; end if;
  eff:=case when p_human_player_count<=2 then 3 else p_human_player_count end;
  mode:=case when p_human_player_count=1 then 'solo' when p_human_player_count=2 then 'duo' else 'multiplayer' end;
  rounds:=case when p_human_player_count>=13 and p_round_count=6 then 6 else 10 end;
  loop
    code:='FRM-'||upper(substr(replace(gen_random_uuid()::text,'-',''),1,6));
    exit when not exists(select 1 from public.fracture_parties fp where fp.party_code=code);
  end loop;

  insert into public.fracture_parties(party_code,owner_user_id,human_player_count,effective_player_count,play_mode,round_count,duo_first_player_seat)
  values(code,uid,p_human_player_count,eff,mode,rounds,case when mode='duo' then greatest(1,least(2,coalesce(p_duo_first_player_seat,1))) else null end)
  returning id into pid;

  insert into public.fracture_party_members(party_id,user_id,seat_number) values(pid,uid,1);
  select pr.id into project_uuid from public.projects pr where pr.slug='fracture-du-reseau-mere' limit 1;

  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||code||' - Fracture du Réseau-Mère','in_progress',p_human_player_count,p_human_player_count,eff,mode,code)
  on conflict do nothing;

  return query select pid,code,1,p_human_player_count,eff,mode,rounds;
end;
$$;
revoke all on function public.create_fracture_party(integer,integer,integer) from public;
grant execute on function public.create_fracture_party(integer,integer,integer) to authenticated;

create or replace function public.join_fracture_party(p_party_code text,p_seat_number integer default null)
returns table(party_id uuid,party_code text,seat_number integer,human_player_count integer,effective_player_count integer,play_mode text,round_count integer)
language plpgsql
security definer
set search_path=public
as $$
declare uid uuid:=auth.uid(); p public.fracture_parties%rowtype; seat integer; existing integer; project_uuid uuid;
begin
  if uid is null then raise exception 'Connexion requise.'; end if;
  select fp.* into p from public.fracture_parties fp
  where upper(fp.party_code)=upper(trim(p_party_code)) and fp.status='in_progress' limit 1;
  if p.id is null then raise exception 'Partie introuvable ou terminée.'; end if;

  select m.seat_number into existing from public.fracture_party_members m where m.party_id=p.id and m.user_id=uid;
  if existing is not null then
    return query select p.id,p.party_code,existing,p.human_player_count,p.effective_player_count,p.play_mode,p.round_count;
    return;
  end if;

  if p.human_player_count=1 then raise exception 'Une partie Solo ne peut pas être rejointe.'; end if;
  if p_seat_number is not null then
    if p_seat_number<1 or p_seat_number>p.human_player_count then raise exception 'Siège humain invalide.'; end if;
    if exists(select 1 from public.fracture_party_members m where m.party_id=p.id and m.seat_number=p_seat_number) then raise exception 'Ce siège est déjà occupé.'; end if;
    seat:=p_seat_number;
  else
    select gs into seat from generate_series(1,p.human_player_count) gs
    where not exists(select 1 from public.fracture_party_members m where m.party_id=p.id and m.seat_number=gs)
    order by gs limit 1;
    if seat is null then raise exception 'Tous les sièges humains sont occupés.'; end if;
  end if;

  insert into public.fracture_party_members(party_id,user_id,seat_number) values(p.id,uid,seat);
  select pr.id into project_uuid from public.projects pr where pr.slug='fracture-du-reseau-mere' limit 1;

  insert into public.game_sessions(user_id,project_id,game_slug,title,status,player_count,human_player_count,effective_player_count,play_mode,party_code)
  values(uid,project_uuid,'fracture-du-reseau-mere','Partie '||p.party_code||' - Fracture du Réseau-Mère','in_progress',p.human_player_count,p.human_player_count,p.effective_player_count,p.play_mode,p.party_code)
  on conflict do nothing;

  return query select p.id,p.party_code,seat,p.human_player_count,p.effective_player_count,p.play_mode,p.round_count;
end;
$$;
revoke all on function public.join_fracture_party(text,integer) from public;
grant execute on function public.join_fracture_party(text,integer) to authenticated;

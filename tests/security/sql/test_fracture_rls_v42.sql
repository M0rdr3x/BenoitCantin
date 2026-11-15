-- SINJIRA V42 : tests négatifs RLS sur base PostgreSQL éphémère.
-- Comptes UUID purement fictifs. Aucune table/donnée de production.
\set ON_ERROR_STOP on
create role authenticated nologin;
create schema auth;
grant usage on schema auth to authenticated;
create function auth.uid() returns uuid language sql stable as
  $$ select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
grant execute on function auth.uid() to authenticated;

create schema sinjira_rls_internal;
grant usage on schema sinjira_rls_internal to authenticated;

create table public.fracture_parties (
  id uuid primary key, owner_user_id uuid not null
);
create table public.fracture_party_members (
  party_id uuid not null, user_id uuid not null,
  primary key (party_id,user_id)
);
create table public.fracture_endgame_reports (
  id uuid primary key, party_id uuid not null references public.fracture_parties(id),
  owner_user_id uuid not null, fields jsonb not null default '{}'::jsonb
);
create table public.fracture_player_documents (
  id uuid primary key, party_id uuid not null references public.fracture_parties(id),
  user_id uuid not null, fields jsonb not null default '{}'::jsonb
);

create function sinjira_rls_internal.is_fracture_party_member(p_party_id uuid,p_user_id uuid)
returns boolean language sql stable security definer
set search_path=pg_catalog
as $$select exists (
  select 1 from public.fracture_party_members
  where party_id=p_party_id and user_id=p_user_id
)$$;
revoke all on function sinjira_rls_internal.is_fracture_party_member(uuid,uuid) from public;
grant execute on function sinjira_rls_internal.is_fracture_party_member(uuid,uuid) to authenticated;

alter table public.fracture_endgame_reports enable row level security;
alter table public.fracture_player_documents enable row level security;
grant select on public.fracture_parties,public.fracture_party_members to authenticated;
grant select,update on public.fracture_endgame_reports,public.fracture_player_documents to authenticated;

-- Préconditions : politiques réelles originales avec WITH CHECK insuffisant.
create policy fixture_endgame_read on public.fracture_endgame_reports
  for select to authenticated using (owner_user_id = (select auth.uid()));
create policy "fracture endgame owner update" on public.fracture_endgame_reports
  for update to authenticated
  using (owner_user_id=(select auth.uid()))
  with check (owner_user_id=(select auth.uid()));
create policy fixture_docs_read on public.fracture_player_documents
  for select to authenticated using (user_id=(select auth.uid()));
create policy "fracture docs own update" on public.fracture_player_documents
  for update to authenticated
  using (user_id=(select auth.uid()))
  with check (user_id=(select auth.uid()));

-- Comptes et parties entièrement fictifs :
-- A: ...0001, B: ...0002. Parties A1, B1 et A2.
insert into public.fracture_parties(id,owner_user_id) values
 ('10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001'),
 ('10000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002'),
 ('10000000-0000-0000-0000-000000000003','00000000-0000-0000-0000-000000000001');
insert into public.fracture_party_members(party_id,user_id) values
 ('10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001'),
 ('10000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002'),
 ('10000000-0000-0000-0000-000000000003','00000000-0000-0000-0000-000000000001');
insert into public.fracture_endgame_reports(id,party_id,owner_user_id) values
 ('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001'),
 ('20000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002');
insert into public.fracture_player_documents(id,party_id,user_id) values
 ('30000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001'),
 ('30000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002');

-- Seul le candidat V42 est appliqué à cette base éphémère.
\i scripts/proposals/sinjira_fracture_v42_rls_update_candidate.sql

set role authenticated;
set request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';

-- Écriture normale : les documents de sa propre partie restent modifiables.
do $test$
begin
  update public.fracture_endgame_reports set fields='{"ok":true}'
  where id='20000000-0000-0000-0000-000000000001';
  if not found then raise exception 'V42: mise à jour légitime refusée pour rapport'; end if;
  update public.fracture_player_documents set fields='{"ok":true}'
  where id='30000000-0000-0000-0000-000000000001';
  if not found then raise exception 'V42: mise à jour légitime refusée pour document'; end if;
end $test$;

-- Attaque : transfert vers une partie de B interdit par WITH CHECK.
do $test$
declare rejected boolean:=false;
begin
  begin
    update public.fracture_endgame_reports
    set party_id='10000000-0000-0000-0000-000000000002'
    where id='20000000-0000-0000-0000-000000000001';
  exception when insufficient_privilege then rejected:=true;
  end;
  if not rejected then raise exception 'V42: transfert du rapport vers partie B autorisé'; end if;
end $test$;

do $test$
declare rejected boolean:=false;
begin
  begin
    update public.fracture_player_documents
    set party_id='10000000-0000-0000-0000-000000000002'
    where id='30000000-0000-0000-0000-000000000001';
  exception when insufficient_privilege then rejected:=true;
  end;
  if not rejected then raise exception 'V42: transfert du document vers partie B autorisé'; end if;
end $test$;

-- Attaque : réassigner owner_user_id / user_id interdit.
do $test$
declare rejected boolean:=false;
begin
  begin
    update public.fracture_endgame_reports
    set owner_user_id='00000000-0000-0000-0000-000000000002'
    where id='20000000-0000-0000-0000-000000000001';
  exception when insufficient_privilege then rejected:=true;
  end;
  if not rejected then raise exception 'V42: reassignation du propriétaire du rapport autorisée'; end if;
end $test$;
do $test$
declare rejected boolean:=false;
begin
  begin
    update public.fracture_player_documents
    set user_id='00000000-0000-0000-0000-000000000002'
    where id='30000000-0000-0000-0000-000000000001';
  exception when insufficient_privilege then rejected:=true;
  end;
  if not rejected then raise exception 'V42: reassignation du propriétaire du document autorisée'; end if;
end $test$;

-- Transfert vers sa propre seconde partie : demeure autorisé par cette règle,
-- ce qui prouve que V42 garantit l'AUTORISATION sur la destination, pas
-- l'immuabilité de party_id (arbitrage métier ultérieur si nécessaire).
do $test$
begin
  update public.fracture_endgame_reports
  set party_id='10000000-0000-0000-0000-000000000003'
  where id='20000000-0000-0000-0000-000000000001';
  if not found then raise exception 'V42: partie A2 refusee pour rapport'; end if;
  update public.fracture_player_documents
  set party_id='10000000-0000-0000-0000-000000000003'
  where id='30000000-0000-0000-0000-000000000001';
  if not found then raise exception 'V42: partie A2 refusee pour document'; end if;
end $test$;

-- B ne peut toujours pas modifier les lignes de A.
set request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
do $test$
begin
  update public.fracture_endgame_reports set fields='{"attacker":true}'
  where id='20000000-0000-0000-0000-000000000001';
  if found then raise exception 'V42: B peut modifier le rapport de A'; end if;
  update public.fracture_player_documents set fields='{"attacker":true}'
  where id='30000000-0000-0000-0000-000000000001';
  if found then raise exception 'V42: B peut modifier le document de A'; end if;
  update public.fracture_endgame_reports set fields='{"ok":true}'
  where id='20000000-0000-0000-0000-000000000002';
  if not found then raise exception 'V42: B ne peut pas modifier son rapport'; end if;
  update public.fracture_player_documents set fields='{"ok":true}'
  where id='30000000-0000-0000-0000-000000000002';
  if not found then raise exception 'V42: B ne peut pas modifier son document'; end if;
end $test$;

\echo 'V42-PASS: own writes allowed, cross-party writes denied, ownership unchanged'

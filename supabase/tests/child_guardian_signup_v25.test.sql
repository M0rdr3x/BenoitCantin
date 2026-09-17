begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(12);

select ok(to_regprocedure('public.enforce_sinjira_account_safety_age()') is not null,'garde serveur de date de naissance existe');
select ok(to_regprocedure('public.handle_new_sinjira_user()') is not null,'pont de création de compte existe');
select ok(to_regprocedure('public.sinjira_age_band(uuid)') is not null,'classification d âge existe');
select ok(to_regprocedure('public.sinjira_parent_can_supervise(uuid,uuid)') is not null,'contrôle de supervision existe');

select ok(position('SINJIRA_MINIMUM_AGE_11' in pg_get_functiondef('public.enforce_sinjira_account_safety_age()'::regprocedure))>0,'le profil de sécurité accepte à partir de 11 ans');
select ok(position('SINJIRA_MINIMUM_AGE_11' in pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))>0,'la création serveur applique le minimum de 11 ans');
select ok(position('GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14' in pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))>0,'les 11 à 13 ans exigent une autorisation parentale');
select ok(position('YOUTH_JURISDICTION_NOT_ENABLED' in pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))>0,'la porte de juridiction jeunesse reste active');

select ok(position($q$interval '11 years'$q$ in pg_get_functiondef('public.sinjira_age_band(uuid)'::regprocedure))>0,'la bande d âge distingue les moins de 11 ans');
select ok(position($q$interval '13 years'$q$ in pg_get_functiondef('public.sinjira_age_band(uuid)'::regprocedure))>0,'les 11 à 12 ans ont une bande enfant distincte');
select ok(position($q$then 'child'$q$ in pg_get_functiondef('public.sinjira_age_band(uuid)'::regprocedure))>0,'un enfant supervisé reçoit la bande child');
select ok(position($q$'child'$q$ in pg_get_functiondef('public.sinjira_parent_can_supervise(uuid,uuid)'::regprocedure))>0 and position($q$'youth'$q$ in pg_get_functiondef('public.sinjira_parent_can_supervise(uuid,uuid)'::regprocedure))>0,'le parent peut superviser enfant et jeunesse');

select * from finish();
rollback;

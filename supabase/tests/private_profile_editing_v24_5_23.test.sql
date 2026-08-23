begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(22);

select ok(to_regclass('public.private_profiles') is not null,'table private_profiles existe');
select ok((select relrowsecurity from pg_class where oid='public.private_profiles'::regclass),'RLS private_profiles activée');
select ok(not has_table_privilege('anon','public.private_profiles','SELECT'),'anon ne lit pas private_profiles');
select ok(not has_table_privilege('authenticated','public.private_profiles','SELECT'),'authenticated ne lit pas directement private_profiles');
select ok(not has_table_privilege('authenticated','public.private_profiles','INSERT'),'authenticated ne crée pas directement private_profiles');
select ok(not has_table_privilege('authenticated','public.private_profiles','UPDATE'),'authenticated ne modifie pas directement private_profiles');
select ok(not has_table_privilege('authenticated','public.private_profiles','DELETE'),'authenticated ne supprime pas directement private_profiles');

select ok(to_regprocedure('public.private_profile_get()') is not null,'RPC de lecture existe');
select ok(to_regprocedure('public.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)') is not null,'RPC de sauvegarde existe');
select ok(not (select prosecdef from pg_proc where oid='public.private_profile_get()'::regprocedure),'wrapper lecture SECURITY INVOKER');
select ok(not (select prosecdef from pg_proc where oid='public.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure),'wrapper sauvegarde SECURITY INVOKER');
select ok(not has_function_privilege('anon','public.private_profile_get()','EXECUTE'),'anon ne peut lire le coffre via RPC');
select ok(not has_function_privilege('anon','public.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)','EXECUTE'),'anon ne peut écrire le coffre via RPC');
select ok(has_function_privilege('authenticated','public.private_profile_get()','EXECUTE'),'authenticated peut lire son coffre via RPC');
select ok(has_function_privilege('authenticated','public.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)','EXECUTE'),'authenticated peut sauvegarder son coffre via RPC');

select ok(to_regprocedure('sinjira_profile_internal.private_profile_get()') is not null and (select prosecdef from pg_proc where oid='sinjira_profile_internal.private_profile_get()'::regprocedure),'implémentation lecture interne privilégiée');
select ok(to_regprocedure('sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)') is not null and (select prosecdef from pg_proc where oid='sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure),'implémentation sauvegarde interne privilégiée');
select ok(position('auth.uid()' in pg_get_functiondef('sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure))>0 and position('sinjira_mfa_access_allowed' in pg_get_functiondef('sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure))>0,'sauvegarde exige identité et barrière MFA');
select ok(position('SINJIRA_MINIMUM_AGE_13' in pg_get_functiondef('sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure))>0 and position('YOUTH_JURISDICTION_NOT_ENABLED' in pg_get_functiondef('sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure))>0 and position('GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14' in pg_get_functiondef('sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure))>0,'garde âge juridiction et tuteur conservée');

select is((select count(*)::int from pg_trigger where tgrelid='public.account_safety_profiles'::regclass and tgname='sinjira_birth_date_change_guard' and not tgisinternal),1,'garde correction date de naissance actif');
select ok(position('enabled=false' in replace(pg_get_functiondef('private.sinjira_birth_date_change_guard()'::regprocedure),' ',''))>0 and position('a_photo_consent=false' in replace(pg_get_functiondef('private.sinjira_birth_date_change_guard()'::regprocedure),' ',''))>0 and position('b_photo_consent=false' in replace(pg_get_functiondef('private.sinjira_birth_date_change_guard()'::regprocedure),' ',''))>0,'correction date désactive Rencontres et révoque les consentements si nécessaire');
select is((select count(*)::int from pg_constraint where conrelid='public.private_profiles'::regclass and conname in ('private_profiles_gender_check','private_profiles_relationship_status_check')),2,'contraintes canoniques genre et statut présentes');

select * from finish();
rollback;

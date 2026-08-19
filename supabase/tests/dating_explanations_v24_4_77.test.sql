begin;
create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(12);

select ok(to_regprocedure('public.dating_compatibility_detail(uuid)') is not null,'RPC détail compatibilité existe');
select ok(has_function_privilege('authenticated','public.dating_compatibility_detail(uuid)','EXECUTE'),'authenticated peut demander son détail de compatibilité');
select ok(not has_function_privilege('anon','public.dating_compatibility_detail(uuid)','EXECUTE'),'anon ne peut pas demander un détail de compatibilité');
select ok((select prosecdef from pg_proc where oid='public.dating_compatibility_detail(uuid)'::regprocedure),'détail compatibilité est security definer');

select ok(position('dating_compatibility_candidates(20)' in replace(pg_get_functiondef('public.dating_compatibility_detail(uuid)'::regprocedure),' ',''))>0,'le détail ne fonctionne que pour une proposition actuelle');
select ok(position('remote_ai_used' in pg_get_functiondef('public.dating_compatibility_detail(uuid)'::regprocedure))>0,'la provenance du calcul est déclarée');
select ok(position('raw_registry_answers_returned' in pg_get_functiondef('public.dating_compatibility_detail(uuid)'::regprocedure))>0,'le contrat indique que les réponses brutes ne sont pas retournées');
select ok(position('raw_profile_data_returned' in pg_get_functiondef('public.dating_compatibility_detail(uuid)'::regprocedure))>0,'le contrat indique que le profil brut ne sort pas');

select ok(position('danger_style' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))>0,'import Registre enrichi avec danger_style');
select ok(position('pressure_style' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))>0,'import Registre enrichi avec pressure_style');
select ok(position('main_strength' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))>0 and position('main_weakness' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))>0,'forces et faiblesses structurées peuvent contribuer avec consentement');
select ok(position('personality_notes' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))=0 and position('compte_courriel' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))=0 and position('compte_pseudo' in pg_get_functiondef('public.dating_import_registry_traits()'::regprocedure))=0,'notes libres et identifiants du compte restent exclus de l’import Rencontres');

select * from finish();
rollback;

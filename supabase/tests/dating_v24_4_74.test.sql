begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(25);

select has_table('public','dating_profiles','table profils rencontres présente');
select has_table('public','dating_introductions','table présentations présente');
select has_table('public','dating_photo_reveal_consents','table consentements photo présente');

select ok((select relrowsecurity from pg_class where oid='public.dating_profiles'::regclass),'RLS profils activée');
select ok((select relrowsecurity from pg_class where oid='public.dating_introductions'::regclass),'RLS présentations activée');
select ok((select relrowsecurity from pg_class where oid='public.dating_photo_reveal_consents'::regclass),'RLS consentements photo activée');

select ok(not has_table_privilege('authenticated','public.dating_profiles','INSERT'),'client ne peut pas créer directement un profil rencontre');
select ok(not has_table_privilege('authenticated','public.dating_profiles','UPDATE'),'client ne peut pas modifier directement un profil rencontre');
select ok(not has_table_privilege('authenticated','public.dating_introductions','INSERT'),'client ne peut pas créer directement une présentation');
select ok(not has_table_privilege('authenticated','public.dating_photo_reveal_consents','SELECT'),'consentements photo opaques au client');
select ok(not has_table_privilege('anon','public.dating_profiles','SELECT'),'aucun catalogue anonyme des rencontres');

select has_function('public','dating_my_eligibility',array[]::text[],'RPC admissibilité présente');
select has_function('public','dating_save_profile',array['jsonb'],'RPC sauvegarde profil présente');
select has_function('public','dating_recommendations',array['integer'],'RPC recommandations présente');
select has_function('public','dating_request_introduction',array['uuid'],'RPC demande présentation présente');
select has_function('public','dating_respond_introduction',array['uuid','boolean'],'RPC réponse présentation présente');
select has_function('public','dating_photo_reveal_status',array['uuid'],'RPC état photo présente');
select has_function('public','dating_request_photo_reveal',array['uuid'],'RPC consentement photo présente');

select ok(position("sinjira_age_band(p_user_id) = 'adult'" in replace(pg_get_functiondef(p.oid),E'\n',' '))>0,'admissibilité réutilise la source âge canonique')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_is_eligible';

select ok(position('Célibataire' in pg_get_functiondef(p.oid))>0 and position('Divorcé(e)' in pg_get_functiondef(p.oid))>0 and position('Veuf / veuve' in pg_get_functiondef(p.oid))>0,'statuts admissibles explicites')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_allowed_relationship_status';

select ok(position('source_purged_at is null' in lower(pg_get_functiondef(p.oid)))>0,'questionnaire purgé jamais réutilisé')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_latest_payload';

select ok(position('avatar_path' in lower(pg_get_functiondef(p.oid)))=0 and position('source_payload' in lower(pg_get_functiondef(p.oid)))=0,'recommandations ne renvoient ni avatar ni questionnaire brut')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='dating_recommendations';

select ok(position('sent_n >= 10' in lower(pg_get_functiondef(p.oid)))>0 and position('received_n >= 10' in lower(pg_get_functiondef(p.oid)))>0 and position('mine and theirs' in lower(pg_get_functiondef(p.oid)))>0,'révélation photo exige 10+10 et double consentement')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_photo_status';

select is((select count(*) from pg_trigger where tgrelid='public.private_profiles'::regclass and tgname='dating_private_profile_guard' and not tgisinternal),1::bigint,'changement de statut relationnel coupe le profil');
select is((select count(*) from pg_trigger where tgrelid='public.social_blocks'::regclass and tgname='dating_social_block_guard' and not tgisinternal),1::bigint,'blocage communautaire ferme la présentation');

select * from finish();
rollback;

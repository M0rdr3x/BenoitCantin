begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(34);

select ok(to_regclass('public.sinjira_points_accounts') is not null,'portefeuille universel Points SINJIRA existe');
select ok(to_regclass('public.sinjira_points_ledger') is not null,'ledger universel Points SINJIRA existe');
select ok(to_regclass('public.dating_meet_requests') is not null,'demandes de lieu existent');
select ok((select relrowsecurity from pg_class where oid='public.sinjira_points_accounts'::regclass),'RLS portefeuille Points SINJIRA active');
select ok((select relrowsecurity from pg_class where oid='public.sinjira_points_ledger'::regclass),'RLS ledger Points SINJIRA active');
select ok((select relrowsecurity from pg_class where oid='public.dating_meet_requests'::regclass),'RLS demandes de lieu active');
select ok(not has_table_privilege('authenticated','public.sinjira_points_accounts','SELECT'),'navigateur ne lit pas directement le portefeuille');
select ok(not has_table_privilege('authenticated','public.sinjira_points_ledger','SELECT'),'navigateur ne lit pas directement le ledger');
select ok(not has_table_privilege('authenticated','public.dating_meet_requests','SELECT'),'navigateur ne lit pas directement les demandes de lieu');

select ok(to_regprocedure('public.sinjira_points_status()') is not null,'RPC statut Points SINJIRA existe');
select ok(to_regprocedure('private.sinjira_points_spend(uuid,integer,text,text,uuid,jsonb)') is not null,'moteur de débit universel existe');
select ok(to_regprocedure('public.dating_safe_meet_status(uuid)') is not null,'RPC statut rencontre publique existe');
select ok(to_regprocedure('public.dating_safe_meet_opt_in(uuid,text[],text)') is not null,'RPC consentement rencontre publique existe');
select ok(to_regprocedure('public.dating_safe_meet_cancel(uuid)') is not null,'RPC annulation existe');
select ok(has_function_privilege('authenticated','public.sinjira_points_status()','EXECUTE'),'authenticated peut lire son solde via RPC');
select ok(has_function_privilege('authenticated','public.dating_safe_meet_opt_in(uuid,text[],text)','EXECUTE'),'authenticated peut consentir via RPC');
select ok(not has_function_privilege('anon','public.sinjira_points_status()','EXECUTE'),'anon ne peut pas lire un solde');
select ok(not has_function_privilege('anon','public.dating_safe_meet_opt_in(uuid,text[],text)','EXECUTE'),'anon ne peut pas proposer une rencontre');

select ok(position('update public.account_safety_profiles' in lower(pg_get_functiondef('sinjira_dating_internal.dating_confirm_single_and_serious()'::regprocedure)))=0,'confirmation Rencontres ne modifie plus le statut amoureux central');
select ok(position($q$relationship_status='single'$q$ in replace(pg_get_functiondef('sinjira_dating_internal.dating_confirm_single_and_serious()'::regprocedure),' ',''))>0,'confirmation exige déjà le statut célibataire');
select ok(exists(select 1 from pg_trigger where tgrelid='public.account_safety_profiles'::regclass and tgname='dating_relationship_gate' and not tgisinternal),'trigger de sortie automatique existe');
select ok(position('serious_intent_confirmed=false' in replace(pg_get_functiondef('private.dating_enforce_relationship_gate()'::regprocedure),' ',''))>0,'sortie du célibat révoque intention/activation');
select ok(position($q$status='closed'$q$ in replace(pg_get_functiondef('private.dating_enforce_relationship_gate()'::regprocedure),' ',''))>0,'sortie du célibat ferme les rencontres actives');
select ok(position('a_photo_consent=false' in replace(pg_get_functiondef('private.dating_enforce_relationship_gate()'::regprocedure),' ',''))>0,'sortie du célibat révoque consentements de dévoilement');
select ok(position('private.dating_is_eligible(pb.user_id)' in pg_get_functiondef('sinjira_dating_internal.dating_conversation(uuid)'::regprocedure))>0,'lecture conversation exige encore les deux admissibles');
select ok(position('not private.dating_is_eligible(v_b_user)' in pg_get_functiondef('sinjira_dating_internal.dating_set_photo_consent(uuid,boolean)'::regprocedure))>0,'dévoilement vérifie les deux participants');
select ok(position('not private.dating_is_eligible(v_other_user)' in pg_get_functiondef('sinjira_dating_internal.dating_respond_connection(uuid,boolean)'::regprocedure))>0,'acceptation vérifie encore l’autre participant');

select ok(position('SINJIRA_POINTS_REQUIRED' in pg_get_functiondef('private.sinjira_points_spend(uuid,integer,text,text,uuid,jsonb)'::regprocedure))>0,'débit refuse un solde insuffisant');
select ok(position('insert into public.sinjira_points_ledger' in lower(pg_get_functiondef('private.sinjira_points_spend(uuid,integer,text,text,uuid,jsonb)'::regprocedure)))>0,'débit écrit dans le ledger universel');
select ok(to_regclass('public.sinjira_points_one_safe_meet_debit_idx') is not null,'index anti-double-débit Safe Meet existe');
select ok(position('profile_a_consent' in pg_get_functiondef('sinjira_dating_internal.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure))>0 and position('profile_b_consent' in pg_get_functiondef('sinjira_dating_internal.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure))>0,'les deux consentements sont requis');
select ok(position('dating_connection_identity_revealed' in pg_get_functiondef('sinjira_dating_internal.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure))>0,'suggestions disponibles seulement après dévoilement mutuel');
select ok(position('private.sinjira_points_spend(v_payer_user,1' in replace(pg_get_functiondef('sinjira_dating_internal.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure),' ',''))>0,'exactement 1 Point SINJIRA est débité à la génération');
select ok(position($q$'dating_safe_meet'$q$ in replace(pg_get_functiondef('sinjira_dating_internal.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure),' ',''))>0,'le débit est rattaché au module Rencontres dans le ledger universel');

select * from finish();
rollback;

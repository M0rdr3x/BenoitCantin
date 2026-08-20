begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(32);

select ok(to_regclass('public.dating_credit_accounts') is not null,'compte Crédit Rencontre existe');
select ok(to_regclass('public.dating_credit_ledger') is not null,'ledger Crédit Rencontre existe');
select ok(to_regclass('public.dating_meet_requests') is not null,'demandes de lieu existent');
select ok((select relrowsecurity from pg_class where oid='public.dating_credit_accounts'::regclass),'RLS compte crédits active');
select ok((select relrowsecurity from pg_class where oid='public.dating_credit_ledger'::regclass),'RLS ledger crédits active');
select ok((select relrowsecurity from pg_class where oid='public.dating_meet_requests'::regclass),'RLS demandes de lieu active');
select ok(not has_table_privilege('authenticated','public.dating_credit_accounts','SELECT'),'navigateur ne lit pas directement les crédits');
select ok(not has_table_privilege('authenticated','public.dating_credit_ledger','SELECT'),'navigateur ne lit pas directement le ledger');
select ok(not has_table_privilege('authenticated','public.dating_meet_requests','SELECT'),'navigateur ne lit pas directement les demandes de lieu');

select ok(to_regprocedure('public.dating_credit_status()') is not null,'RPC statut crédits existe');
select ok(to_regprocedure('public.dating_safe_meet_status(uuid)') is not null,'RPC statut rencontre publique existe');
select ok(to_regprocedure('public.dating_safe_meet_opt_in(uuid,text[],text)') is not null,'RPC consentement rencontre publique existe');
select ok(to_regprocedure('public.dating_safe_meet_cancel(uuid)') is not null,'RPC annulation existe');
select ok(has_function_privilege('authenticated','public.dating_credit_status()','EXECUTE'),'authenticated peut lire son solde via RPC');
select ok(has_function_privilege('authenticated','public.dating_safe_meet_opt_in(uuid,text[],text)','EXECUTE'),'authenticated peut consentir via RPC');
select ok(not has_function_privilege('anon','public.dating_credit_status()','EXECUTE'),'anon ne peut pas lire un solde');
select ok(not has_function_privilege('anon','public.dating_safe_meet_opt_in(uuid,text[],text)','EXECUTE'),'anon ne peut pas proposer une rencontre');

select ok(position('update public.account_safety_profiles' in lower(pg_get_functiondef('public.dating_confirm_single_and_serious()'::regprocedure)))=0,'confirmation Rencontres ne modifie plus le statut amoureux central');
select ok(position($q$relationship_status='single'$q$ in replace(pg_get_functiondef('public.dating_confirm_single_and_serious()'::regprocedure),' ',''))>0,'confirmation exige déjà le statut célibataire');
select ok(exists(select 1 from pg_trigger where tgrelid='public.account_safety_profiles'::regclass and tgname='dating_relationship_gate' and not tgisinternal),'trigger de sortie automatique existe');
select ok(position('serious_intent_confirmed=false' in replace(pg_get_functiondef('private.dating_enforce_relationship_gate()'::regprocedure),' ',''))>0,'sortie du célibat révoque intention/activation');
select ok(position($q$status='closed'$q$ in replace(pg_get_functiondef('private.dating_enforce_relationship_gate()'::regprocedure),' ',''))>0,'sortie du célibat ferme les rencontres actives');
select ok(position('a_photo_consent=false' in replace(pg_get_functiondef('private.dating_enforce_relationship_gate()'::regprocedure),' ',''))>0,'sortie du célibat révoque consentements de dévoilement');
select ok(position('private.dating_is_eligible(pb.user_id)' in pg_get_functiondef('public.dating_conversation(uuid)'::regprocedure))>0,'lecture conversation exige encore les deux admissibles');
select ok(position('not private.dating_is_eligible(v_b_user)' in pg_get_functiondef('public.dating_set_photo_consent(uuid,boolean)'::regprocedure))>0,'dévoilement vérifie les deux participants');
select ok(position('not private.dating_is_eligible(v_other_user)' in pg_get_functiondef('public.dating_respond_connection(uuid,boolean)'::regprocedure))>0,'acceptation vérifie encore l’autre participant');

select ok(position($q$'starter_credits',3$q$ in replace(pg_get_functiondef('public.dating_credit_status()'::regprocedure),' ',''))>0,'3 crédits gratuits au départ annoncés côté serveur');
select ok(position($q$'monthly_free_credits',1$q$ in replace(pg_get_functiondef('public.dating_credit_status()'::regprocedure),' ',''))>0,'1 crédit gratuit mensuel annoncé côté serveur');
select ok(position($q$'purchases_enabled',false$q$ in replace(pg_get_functiondef('public.dating_credit_status()'::regprocedure),' ',''))>0,'achat de crédits explicitement désactivé');
select ok(position('profile_a_consent' in pg_get_functiondef('public.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure))>0 and position('profile_b_consent' in pg_get_functiondef('public.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure))>0,'les deux consentements sont requis');
select ok(position('dating_connection_identity_revealed' in pg_get_functiondef('public.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure))>0,'suggestions disponibles seulement après dévoilement mutuel');
select ok(position("values(v_payer_user,-1,'safe_meet_recommendation'" in replace(pg_get_functiondef('public.dating_safe_meet_opt_in(uuid,text[],text)'::regprocedure),' ',''))>0,'un débit interne de 1 crédit est enregistré à la génération');

select * from finish();
rollback;

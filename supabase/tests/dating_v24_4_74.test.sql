begin;

create extension if not exists pgtap with schema extensions;
set local search_path = public, private, extensions;

select plan(38);

select has_table('public','dating_profiles','table profils rencontres présente');
select has_table('public','dating_introductions','table présentations présente');
select has_table('public','dating_photo_reveal_consents','table consentements photo présente');
select has_table('public','dating_recommendation_tokens','table jetons de découverte présente');
select has_table('public','dating_messages','table chat Rencontres isolé présente');

select ok((select relrowsecurity from pg_class where oid='public.dating_profiles'::regclass),'RLS profils activée');
select ok((select relrowsecurity from pg_class where oid='public.dating_introductions'::regclass),'RLS présentations activée');
select ok((select relrowsecurity from pg_class where oid='public.dating_photo_reveal_consents'::regclass),'RLS consentements photo activée');
select ok((select relrowsecurity from pg_class where oid='public.dating_recommendation_tokens'::regclass),'RLS jetons de découverte activée');
select ok((select relrowsecurity from pg_class where oid='public.dating_messages'::regclass),'RLS chat Rencontres activée');

select ok(not has_table_privilege('authenticated','public.dating_profiles','INSERT'),'client ne peut pas créer directement un profil rencontre');
select ok(not has_table_privilege('authenticated','public.dating_profiles','UPDATE'),'client ne peut pas modifier directement un profil rencontre');
select ok(not has_table_privilege('authenticated','public.dating_introductions','INSERT'),'client ne peut pas créer directement une présentation');
select ok(not has_table_privilege('authenticated','public.dating_photo_reveal_consents','SELECT'),'consentements photo opaques au client');
select ok(not has_table_privilege('authenticated','public.dating_recommendation_tokens','SELECT'),'cibles des jetons opaques au client');
select ok(not has_table_privilege('authenticated','public.dating_messages','SELECT'),'chat Rencontres sans accès direct aux identifiants expéditeur');
select ok(not has_table_privilege('anon','public.dating_profiles','SELECT'),'aucun catalogue anonyme des rencontres');

select has_function('public','dating_my_eligibility',array[]::text[],'RPC admissibilité présente');
select has_function('public','dating_save_profile',array['jsonb'],'RPC sauvegarde profil présente');
select has_function('public','dating_recommendations',array['integer'],'RPC recommandations présente');
select has_function('public','dating_request_introduction',array['uuid'],'RPC demande présentation présente');
select has_function('public','dating_respond_introduction',array['uuid','boolean'],'RPC réponse présentation présente');
select has_function('public','dating_photo_reveal_status',array['uuid'],'RPC état photo présente');
select has_function('public','dating_request_photo_reveal',array['uuid'],'RPC consentement photo présente');
select has_function('public','dating_conversation',array['uuid'],'RPC conversation aveugle présente');
select has_function('public','dating_send_message',array['uuid','text'],'RPC envoi chat Rencontres présente');
select has_function('public','dating_report_message',array['uuid','text'],'RPC signalement chat Rencontres présente');

select ok(position("sinjira_age_band(p_user_id) = 'adult'" in replace(pg_get_functiondef(p.oid),E'\n',' '))>0,'admissibilité réutilise la source âge canonique')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_is_eligible';

select ok(position('Célibataire' in pg_get_functiondef(p.oid))>0 and position('Divorcé(e)' in pg_get_functiondef(p.oid))>0 and position('Veuf / veuve' in pg_get_functiondef(p.oid))>0,'statuts admissibles explicites')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_allowed_relationship_status';

select ok(position('source_purged_at is null' in lower(pg_get_functiondef(p.oid)))>0,'questionnaire purgé jamais réutilisé')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_latest_payload';

select ok(position('''recommendation_token''' in lower(pg_get_functiondef(p.oid)))>0
  and position('''user_id''' in lower(pg_get_functiondef(p.oid)))=0
  and position('''pseudo''' in lower(pg_get_functiondef(p.oid)))=0
  and position('''avatar_path''' in lower(pg_get_functiondef(p.oid)))=0,
  'sortie recommandations = jeton opaque sans identité communautaire')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='dating_recommendations';

select ok(position('dating_recommendation_tokens' in lower(pg_get_functiondef(p.oid)))>0
  and position('viewer_user_id=uid' in replace(lower(pg_get_functiondef(p.oid)),' ',''))>0
  and position('expires_at>now()' in replace(lower(pg_get_functiondef(p.oid)),' ',''))>0,
  'demande de présentation consomme un jeton appartenant au compte et non expiré')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='dating_request_introduction';

select ok(position('''other_user_id'',null' in replace(lower(pg_get_functiondef(p.oid)),' ',''))>0
  and position('''other_pseudo'',''membrecompatible''' in replace(lower(pg_get_functiondef(p.oid)),' ',''))>0,
  'liste des présentations garde identité et pseudo anonymes')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='dating_my_introductions';

select ok(position('''mine''' in lower(pg_get_functiondef(p.oid)))>0
  and position('''body''' in lower(pg_get_functiondef(p.oid)))>0
  and position('''sender_user_id''' in lower(pg_get_functiondef(p.oid)))=0
  and position('''recipient_user_id''' in lower(pg_get_functiondef(p.oid)))=0,
  'conversation retourne mine/body sans identifiant adverse')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='dating_conversation';

select ok(position('from public.dating_messages' in lower(pg_get_functiondef(p.oid)))>0
  and position('sent_n >= 10' in lower(pg_get_functiondef(p.oid)))>0
  and position('received_n >= 10' in lower(pg_get_functiondef(p.oid)))>0
  and position('mine and theirs' in lower(pg_get_functiondef(p.oid)))>0,
  'révélation identité/photo compte uniquement le chat Rencontres et exige 10+10 + double consentement')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='private' and p.proname='dating_photo_status';

select ok(position('dating_rate_limit' in lower(pg_get_functiondef(p.oid)))>0
  and position("interval '2 seconds'" in lower(pg_get_functiondef(p.oid)))>0
  and position("interval '1 hour'" in lower(pg_get_functiondef(p.oid)))>0,
  'chat Rencontres possède un anti-spam serveur')
from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='dating_send_message';

select is((select count(*) from pg_trigger where tgrelid='public.private_profiles'::regclass and tgname='dating_private_profile_guard' and not tgisinternal),1::bigint,'changement de statut relationnel coupe le profil');
select is((select count(*) from pg_trigger where tgrelid='public.social_blocks'::regclass and tgname='dating_social_block_guard' and not tgisinternal),1::bigint,'blocage communautaire ferme la présentation');

select * from finish();
rollback;

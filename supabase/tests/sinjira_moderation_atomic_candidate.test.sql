\set ON_ERROR_STOP on
-- Fictif uniquement. Prérequis : fixture + candidat déjà chargés dans une
-- base PostgreSQL temporaire, jamais sur une base Supabase distante.
select public.fixture_assert_true(
 not has_function_privilege('anon','public.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'anon ne doit pas pouvoir déclencher une sanction');
select public.fixture_assert_true(
 not has_function_privilege('authenticated','public.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'authenticated ne doit pas pouvoir déclencher une sanction');
select public.fixture_assert_true(
 has_function_privilege('service_role','public.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'seul le rôle serveur peut déclencher une sanction');
select public.fixture_assert_true(
 not has_function_privilege('anon','public.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE')
 and not has_function_privilege('authenticated','public.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE')
 and has_function_privilege('service_role','public.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE'),
 'revue des appels réservée au rôle serveur');
select public.fixture_assert_true(
 not has_table_privilege('service_role','private.moderation_decisions','INSERT'),
 'pas de droit INSERT direct sur les décisions privées');


-- Le schéma public n'ouvre pas les RPC : seul service_role peut exécuter.
select public.fixture_assert_true(
 not has_function_privilege('anon',
  'public.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE')
 and not has_function_privilege('authenticated',
  'public.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE')
 and has_function_privilege('service_role',
  'public.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'RPC publique sanction : accès réservé au service');
select public.fixture_assert_true(
 not has_function_privilege('anon',
  'public.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE')
 and not has_function_privilege('authenticated',
  'public.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE')
 and has_function_privilege('service_role',
  'public.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE'),
 'RPC publique appel : accès réservé au service');

select public.fixture_assert_true(
  not has_function_privilege('anon',
    'public.sinjira_admin_appeals_overview(uuid,integer)','EXECUTE')
  and not has_function_privilege('authenticated',
    'public.sinjira_admin_appeals_overview(uuid,integer)','EXECUTE')
  and has_function_privilege('service_role',
    'public.sinjira_admin_appeals_overview(uuid,integer)','EXECUTE'),
  'la liste privée des appels doit être réservée au rôle serveur');
select public.fixture_assert_true(
  not has_table_privilege('service_role','private.moderation_appeals','SELECT'),
  'la RPC de consultation ne doit pas ouvrir SELECT aux tables privées');

-- Même si un client authentifié falsifie son JWT SQL, le rôle SQL
-- authenticated doit être refusé AVANT le code SECURITY DEFINER.
select set_config('request.jwt.claims','{"role":"service_role"}',false);
set role authenticated;
do $refuse$
begin
  begin
    perform public.sinjira_admin_moderate_atomic(
      'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
      'dddddddd-dddd-4ddd-dddd-ddddddddddde','resolve_report');
    raise exception 'EXPECTED_SQL_PERMISSION_DENIAL';
  exception when insufficient_privilege then null;
  end;
end;
$refuse$;
reset role;

-- La session simule le JWT du SERVICE et l'identité de l'admin est une
-- variable signée par Edge après vérification AAL2, jamais celle du client.
select set_config('request.jwt.claims','{"role":"service_role"}',false);
set role service_role;

-- Un rapport valide déclenche décision, suspension, clôture et notification.
select public.sinjira_admin_moderate_atomic(
 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
 'dddddddd-dddd-4ddd-dddd-dddddddddddd',
 'suspend_social','Règles communautaires de sécurité',
 'Suspension temporaire décidée après une révision humaine indépendante.',
 'standard',7
);

-- Test générique des erreurs attendues. Toutes les exceptions sont récupérées
-- dans un bloc PL/pgSQL pour confirmer que la base conserve son intégrité.
do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'dddddddd-dddd-4ddd-dddd-dddddddddddd',
     'suspend_social','Règles communautaires de sécurité',
     'Nouvelle suspension qui doit être refusée après traitement.','standard',7);
 exception when others then
   if sqlerrm<>'REPORT_NOT_OPEN' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_REPORT_NOT_OPEN'; end if;
end $$;

do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb',
     'dddddddd-dddd-4ddd-dddd-ddddddddddde',
     'hide_content','Règles communautaires de sécurité',
     'La décision doit être refusée avec un admin inconnu.','standard',null);
 exception when others then
   if sqlerrm<>'ADMIN_REQUIRED' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_ADMIN_REQUIRED'; end if;
end $$;

do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'dddddddd-dddd-4ddd-dddd-ddddddddddd0',
     'hide_content','Règles communautaires de sécurité',
     'Un post supprimé ne permet pas une sanction sans cible.','standard',null);
 exception when others then
   if sqlerrm<>'TARGET_USER_NOT_FOUND' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_TARGET_USER_NOT_FOUND'; end if;
end $$;

do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'dddddddd-dddd-4ddd-dddd-ddddddddddde',
     'suspend_social','Règles communautaires de sécurité',
     'Les durées supérieures à la limite doivent être rejetées.','standard',366);
 exception when others then
   if sqlerrm<>'INVALID_SUSPENSION_DURATION' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_INVALID_SUSPENSION_DURATION'; end if;
end $$;

-- Une notification en erreur fait tomber l'INSERT de décision et la
-- clôture de rapport dans la même transaction PostgreSQL.
do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'dddddddd-dddd-4ddd-dddd-ddddddddddd2',
     'hide_content','Règles communautaires de sécurité',
     'FORCE_ROLLBACK : cette notification échoue pour vérifier le rollback.','standard',null);
 exception when others then
   if sqlerrm<>'FIXTURE_FORCED_FAILURE' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_FULL_ROLLBACK'; end if;
end $$;

-- Deuxième rapport visant une personne déjà suspendue : pas d'écrasement
-- d'une suspension active par une décision provenant d'un autre rapport.
do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'dddddddd-dddd-4ddd-dddd-ddddddddddde',
     'suspend_social','Règles communautaires de sécurité',
     'Une nouvelle suspension ne doit pas écraser la suspension active.','standard',7);
 exception when others then
   if sqlerrm<>'SUSPENSION_ALREADY_ACTIVE' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_SUSPENSION_ALREADY_ACTIVE'; end if;
end $$;

-- Un rapport clos sans sanction reste possible et ne fabrique aucun lien
-- avec une décision, une suspension ni un appel.
select public.sinjira_admin_moderate_atomic(
 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
 'dddddddd-dddd-4ddd-dddd-ddddddddddd1',
 'resolve_report',null,null,null,null);

reset role;

select public.fixture_assert_true(
 (select count(*) from private.moderation_decisions)=1,
 'exactement une décision malgré doublons et erreurs simulées');
select public.fixture_assert_true(
 (select count(*) from public.social_suspensions)=1,
 'exactement une suspension valide');
select public.fixture_assert_true(
 (select count(*) from public.user_notifications)=1,
 'exactement une notification valide');
select public.fixture_assert_true(
 (select status='open' from public.social_reports where id='dddddddd-dddd-4ddd-dddd-ddddddddddd2'),
 'la notification en erreur annule la clôture du rapport');
select public.fixture_assert_true(
 not exists(select 1 from private.moderation_decisions where report_id='dddddddd-dddd-4ddd-dddd-ddddddddddd2'),
 'la notification en erreur annule l insertion de décision');
select public.fixture_assert_true(
 (select status='resolved' from public.social_reports where id='dddddddd-dddd-4ddd-dddd-ddddddddddd1'),
 'un rapport simple a pu être résolu');
select public.fixture_assert_true(
 (select count(*) from private.moderation_decisions where report_id='dddddddd-dddd-4ddd-dddd-ddddddddddd1')=0,
 'une résolution simple ne doit pas créer de sanction');

-- Appel fictif du seul compte suspendu.
insert into private.moderation_appeals(id,decision_id,appellant_user_id,appeal_text)
select 'ffffffff-ffff-4fff-ffff-ffffffffffff',d.id,'bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb',
'Je sollicite une révision humaine, sans frais, de la sanction.'
from private.moderation_decisions d limit 1;

set role service_role;
select public.fixture_assert_true(
 (public.sinjira_admin_appeals_overview(
  'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',300)->>'pending_count')::integer=1,
 'le tableau admin retourne le vrai nombre des appels en attente');
select public.fixture_assert_true(
 jsonb_array_length(public.sinjira_admin_appeals_overview(
  'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',300)->'appeals')=1,
 'le tableau admin contient la décision de l appel');
select public.fixture_assert_true(
 public.sinjira_admin_appeals_overview(
  'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',300)->'appeals'->0->'decision'->>'action'='suspend_social',
 'la décision est jointe en lecture privée et sans accès REST aux tables');
select public.sinjira_admin_review_appeal_atomic(
 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
 'ffffffff-ffff-4fff-ffff-ffffffffffff',
 'reversed','L’appel a été accepté après réexamen humain et correction de la décision initiale.');

do $$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_review_appeal_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'ffffffff-ffff-4fff-ffff-ffffffffffff',
     'reversed','Un appel déjà tranché ne peut être renversé une deuxième fois.');
 exception when others then
   if sqlerrm<>'APPEAL_NOT_PENDING' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_APPEAL_NOT_PENDING'; end if;
end $$;
reset role;

select public.fixture_assert_true(
 (select status='reversed' from private.moderation_decisions limit 1),
 'décision revue et renversée');
select public.fixture_assert_true(
 (select status='reversed' from private.moderation_appeals limit 1),
 'appel renversé dans la même transaction');
select public.fixture_assert_true(
 (select count(*) from public.social_suspensions)=0,
 'suppression seulement de la suspension issue de cette décision');
select public.fixture_assert_true(
 (select count(*) from public.user_notifications)=2,
 'une notification initiale et une notification après appel');


set role service_role;
select public.fixture_assert_true(
 (public.sinjira_admin_appeals_overview(
  'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',300)->>'pending_count')::integer=0,
 'un appel traité ne réapparaît pas dans les affaires en attente');
reset role;

-- Une seconde suspension sert à vérifier l'atomicité du RENVERSEMENT :
-- faire échouer la notification DOIT rétablir décision, appel et suspension.
set role service_role;
select public.sinjira_admin_moderate_atomic(
 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
 'dddddddd-dddd-4ddd-dddd-ddddddddddde',
 'suspend_social','Règles communautaires de sécurité',
 'Une seconde sanction fictive prépare une révision avec échec forcé.','standard',7);
reset role;

insert into private.moderation_appeals(id,decision_id,appellant_user_id,appeal_text)
select 'ffffffff-ffff-4fff-ffff-fffffffffff0',d.id,'bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb',
'Une autre demande de révision humaine de la seconde suspension.'
from private.moderation_decisions d
where d.report_id='dddddddd-dddd-4ddd-dddd-ddddddddddde';

set role service_role;
do $qa$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_review_appeal_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'ffffffff-ffff-4fff-ffff-fffffffffff0',
     'reversed','FORCE_ROLLBACK — un échec de notification ne peut renverser une suspension à moitié.');
 exception when others then
   if sqlerrm<>'FIXTURE_FORCED_FAILURE' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_APPEAL_ROLLBACK'; end if;
end $qa$;

do $qa$
declare v_failed boolean:=false;
begin
 begin
   perform public.sinjira_admin_moderate_atomic(
     'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
     'dddddddd-dddd-4ddd-dddd-dddddddddddf',
     null,'Règles communautaires de sécurité',
     'Une action SQL nulle doit être refusée sans effet.','standard',null);
 exception when others then
   if sqlerrm<>'INVALID_MODERATION_INPUT' then raise; end if;
   v_failed:=true;
 end;
 if not v_failed then raise exception 'EXPECTED_NULL_ACTION_REJECTION'; end if;
end $qa$;
reset role;

select public.fixture_assert_true(
 (select status='active' from private.moderation_decisions
  where report_id='dddddddd-dddd-4ddd-dddd-ddddddddddde'),
 'rollback appel : la décision originale doit rester active');
select public.fixture_assert_true(
 (select status='pending' from private.moderation_appeals
  where id='ffffffff-ffff-4fff-ffff-fffffffffff0'),
 'rollback appel : la révision doit rester en attente');
select public.fixture_assert_true(
 (select count(*) from public.social_suspensions)=1,
 'rollback appel : la suspension antérieure est conservée');
select public.fixture_assert_true(
 (select count(*) from public.user_notifications)=3,
 'rollback appel : aucune notification résiduelle après échec');
select public.fixture_assert_true(
 (select status='open' from public.social_reports
  where id='dddddddd-dddd-4ddd-dddd-dddddddddddf'),
 'une action SQL nulle ne ferme pas le rapport');


-- Régression d'une identité Rencontres falsifiée dans le JSON d'un
-- signalement social public : le snapshot n'est PAS une preuve SQL.
-- Le profil ciblé appartient ici à un AUTRE utilisateur (admin fictif).
insert into public.dating_profiles(id,user_id) values(
 '99999999-9999-4999-9999-999999999998',
 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa');
update public.social_reports
set snapshot='{"source":"dating","dating_profile_id":"99999999-9999-4999-9999-999999999998"}'::jsonb
where id='dddddddd-dddd-4ddd-dddd-ddddddddddd3';

set role service_role;
do $spoof$
declare v_rejected boolean:=false;
begin
  begin
    perform public.sinjira_admin_moderate_atomic(
      'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
      'dddddddd-dddd-4ddd-dddd-ddddddddddd3',
      'suspend_social','Règles communautaires de sécurité',
      'Un signalement social ne prouve pas la provenance d un profil Rencontres.',
      'standard',7);
  exception when others then
    if sqlerrm<>'UNVERIFIED_DATING_PROVENANCE' then raise; end if;
    v_rejected:=true;
  end;
  if not v_rejected then raise exception 'EXPECTED_DATING_PROVENANCE_DENIAL'; end if;
end;
$spoof$;
reset role;

select public.fixture_assert_true(
 not exists(select 1 from private.moderation_decisions
            where report_id='dddddddd-dddd-4ddd-dddd-ddddddddddd3'),
 'Un snapshot Rencontres forgé ne crée aucune décision contre un autre compte');
select public.fixture_assert_true(
 (select status='open' from public.social_reports
  where id='dddddddd-dddd-4ddd-dddd-ddddddddddd3'),
 'Un snapshot forgé ne clôture pas le signalement');
select public.fixture_assert_true(
 not exists(select 1 from public.social_suspensions
            where user_id='aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa'),
 'Un faux ID de profil ne peut suspendre un tiers');

-- Revenir à un rapport social canonique pour le test de concurrence à 2 sessions.
update public.social_reports
set snapshot='{}'::jsonb
where id='dddddddd-dddd-4ddd-dddd-ddddddddddd3';

select 'PASS: base temporaire — droits minimaux, sanction atomique, rollback forcé, appels et réexamen.' as result;

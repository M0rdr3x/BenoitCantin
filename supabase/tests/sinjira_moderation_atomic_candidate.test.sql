\set ON_ERROR_STOP on
-- Fictif uniquement. Prérequis : fixture + candidat déjà chargés dans une
-- base PostgreSQL temporaire, jamais sur une base Supabase distante.
select public.fixture_assert_true(
 not has_function_privilege('anon','private.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'anon ne doit pas pouvoir déclencher une sanction');
select public.fixture_assert_true(
 not has_function_privilege('authenticated','private.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'authenticated ne doit pas pouvoir déclencher une sanction');
select public.fixture_assert_true(
 has_function_privilege('service_role','private.sinjira_admin_moderate_atomic(uuid,uuid,text,text,text,text,integer)','EXECUTE'),
 'seul le rôle serveur peut déclencher une sanction');
select public.fixture_assert_true(
 not has_function_privilege('anon','private.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE')
 and not has_function_privilege('authenticated','private.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE')
 and has_function_privilege('service_role','private.sinjira_admin_review_appeal_atomic(uuid,uuid,text,text)','EXECUTE'),
 'revue des appels réservée au rôle serveur');
select public.fixture_assert_true(
 not has_table_privilege('service_role','private.moderation_decisions','INSERT'),
 'pas de droit INSERT direct sur les décisions privées');

-- La session simule le JWT du SERVICE et l'identité de l'admin est une
-- variable signée par Edge après vérification AAL2, jamais celle du client.
select set_config('request.jwt.claims','{"role":"service_role"}',false);
set role service_role;

-- Un rapport valide déclenche décision, suspension, clôture et notification.
select private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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
select private.sinjira_admin_moderate_atomic(
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
select private.sinjira_admin_review_appeal_atomic(
 'aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaaa',
 'ffffffff-ffff-4fff-ffff-ffffffffffff',
 'reversed','L’appel a été accepté après réexamen humain et correction de la décision initiale.');

do $$
declare v_failed boolean:=false;
begin
 begin
   perform private.sinjira_admin_review_appeal_atomic(
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


-- Une seconde suspension sert à vérifier l'atomicité du RENVERSEMENT :
-- faire échouer la notification DOIT rétablir décision, appel et suspension.
set role service_role;
select private.sinjira_admin_moderate_atomic(
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
   perform private.sinjira_admin_review_appeal_atomic(
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
   perform private.sinjira_admin_moderate_atomic(
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

select 'PASS: base temporaire — droits minimaux, sanction atomique, rollback forcé, appels et réexamen.' as result;

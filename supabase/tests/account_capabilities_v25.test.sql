begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(25);

select ok(to_regprocedure('public.sinjira_my_account_capabilities()') is not null,'RPC self-only des capacités existe');
select ok(to_regprocedure('public.sinjira_my_account_capabilities(uuid)') is null,'aucun RPC capacités avec UUID arbitraire');
select ok(not has_function_privilege('anon','public.sinjira_my_account_capabilities()','EXECUTE'),'anon ne peut pas sonder les capacités');
select ok(has_function_privilege('authenticated','public.sinjira_my_account_capabilities()','EXECUTE'),'authenticated peut lire ses propres capacités');

select set_config('request.jwt.claim.sub','a9000000-0000-4000-8000-000000000099',true);
select is(public.sinjira_my_account_capabilities()->>'account_mode','restricted','un compte sans profil de sécurité vérifié reste restricted');
select ok(not (public.sinjira_my_account_capabilities()->>'native_general_hubs')::boolean,'restricted ne peut pas ouvrir les hubs natifs généraux');
select is(public.sinjira_my_account_capabilities()->>'library_mode','none','restricted ne reçoit aucune bibliothèque');
select ok(not (public.sinjira_my_account_capabilities()->>'general_community')::boolean,'restricted ne peut pas ouvrir la communauté générale');

insert into auth.users(id,email,raw_user_meta_data)
values(
  'a1000000-0000-4000-8000-000000000001',
  'capabilities-adult@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '35 years')::date::text,
    'date_of_birth',(current_date-interval '35 years')::date::text,
    'gender','Homme','sex','male','pseudo','Adulte capacités','display_name','Adulte capacités','residence_country','Canada'
  )
);
select is(public.sinjira_age_band('a1000000-0000-4000-8000-000000000001'),'adult','compte adulte de test');

select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000001',true);
select is(public.sinjira_my_account_capabilities()->>'account_mode','standard','adulte en mode standard');
select ok((public.sinjira_my_account_capabilities()->>'native_general_hubs')::boolean,'adulte peut utiliser les hubs natifs généraux');
select is(public.sinjira_my_account_capabilities()->>'library_mode','full','adulte garde la bibliothèque complète');
select ok((public.sinjira_my_account_capabilities()->>'dating')::boolean,'Rencontres reste disponible à adulte');

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('a1000000-0000-4000-8000-000000000001','YOUTH-CAPABI0001',now()+interval '1 day');

insert into auth.users(id,email,raw_user_meta_data)
values(
  'a2000000-0000-4000-8000-000000000011',
  'capabilities-child@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '11 years')::date::text,
    'date_of_birth',(current_date-interval '11 years')::date::text,
    'gender','Femme','sex','female','pseudo','Enfant capacités','display_name','Enfant capacités','residence_country','Canada',
    'guardian_code','YOUTH-CAPABI0001'
  )
);
select is(public.sinjira_age_band('a2000000-0000-4000-8000-000000000011'),'child','compte enfant de test');

select set_config('request.jwt.claim.sub','a2000000-0000-4000-8000-000000000011',true);
select is(public.sinjira_my_account_capabilities()->>'account_mode','child','11–12 reçoit le mode child');
select ok((public.sinjira_my_account_capabilities()->>'child_11_12')::boolean,'capacité child_11_12 vraie');
select ok(not (public.sinjira_my_account_capabilities()->>'native_general_hubs')::boolean,'hubs natifs généraux fermés à 11–12');
select is(public.sinjira_my_account_capabilities()->>'library_mode','reviewed_11_12','bibliothèque bornée au contenu revu');
select ok(not (public.sinjira_my_account_capabilities()->>'general_community')::boolean,'communauté générale fermée à 11–12');
select ok(not (public.sinjira_my_account_capabilities()->>'dating')::boolean,'Rencontres fermée à 11–12');
select ok((public.sinjira_my_account_capabilities()->>'junior_community_eligible')::boolean,'Communauté Junior éligible à 11–12');

update public.guardian_links
set status='revoked',revoked_at=now()
where minor_user_id='a2000000-0000-4000-8000-000000000011'
  and guardian_user_id='a1000000-0000-4000-8000-000000000001';

select is(public.sinjira_age_band('a2000000-0000-4000-8000-000000000011'),'child_pending','après révocation parentale un 11–12 devient child_pending');
select is(public.sinjira_my_account_capabilities()->>'account_mode','restricted','child_pending devient immédiatement restricted');
select is(public.sinjira_my_account_capabilities()->>'library_mode','none','child_pending perd immédiatement la Bibliothèque Junior');
select ok(not (public.sinjira_my_account_capabilities()->>'junior_community_eligible')::boolean,'child_pending perd immédiatement l éligibilité Communauté Junior');

select * from finish();
rollback;

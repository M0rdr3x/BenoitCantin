begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(34);

select ok(to_regprocedure('public.enforce_sinjira_account_safety_age()') is not null,'garde serveur de date de naissance existe');
select ok(to_regprocedure('public.handle_new_sinjira_user()') is not null,'pont de création de compte existe');
select ok(to_regprocedure('public.sinjira_age_band(uuid)') is not null,'classification d âge existe');
select ok(to_regprocedure('public.sinjira_parent_can_supervise(uuid,uuid)') is not null,'contrôle de supervision existe');
select ok(not has_function_privilege('authenticated','public.sinjira_age_band(uuid)','EXECUTE'),'authenticated ne peut pas sonder la bande âge d un UUID arbitraire');
select ok(has_function_privilege('authenticated','public.sinjira_my_age_band()','EXECUTE'),'authenticated peut lire uniquement sa propre bande âge');
select ok(has_function_privilege('anon','public.sinjira_my_age_band()','EXECUTE'),'anon peut évaluer uniquement sa propre bande self-only pour les RLS publiques');
select ok(not has_function_privilege('authenticated','public.sinjira_parent_can_supervise(uuid,uuid)','EXECUTE'),'authenticated ne peut pas sonder une relation parent/enfant arbitraire');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '10000000-0000-4000-8000-000000000001',
  'guardian-child11@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '35 years')::date::text,
    'date_of_birth',(current_date-interval '35 years')::date::text,
    'gender','Homme','sex','male','pseudo','Parent test','display_name','Parent test','residence_country','Canada'
  )
);

select is(public.sinjira_age_band('10000000-0000-4000-8000-000000000001'),'adult','le parent de test est classé adulte');

-- Émettre un code parental est un geste sensible : AAL1 doit échouer même lorsque
-- la politique MFA globale est permissive; AAL2 doit réussir.
update public.sinjira_security_settings
set require_phone_mfa=false
where singleton_id=1;

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','10000000-0000-4000-8000-000000000001',
    'aal','aal1'
  )::text,
  true
);

select throws_ok(
  $$ select public.create_guardian_signup_invite() $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'une session adulte AAL1 ne peut pas créer de code parental'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','10000000-0000-4000-8000-000000000001',
    'aal','aal2'
  )::text,
  true
);

select lives_ok(
  $$ select public.create_guardian_signup_invite() $$,
  'une session adulte AAL2 peut créer un code parental'
);

select ok(
  exists(
    select 1
    from public.guardian_signup_invites
    where guardian_user_id='10000000-0000-4000-8000-000000000001'
      and used_at is null
      and invite_code ~ '^YOUTH-[A-Z0-9]{10}$'
  ),
  'le code créé sous AAL2 respecte le format et reste à usage unique'
);

delete from public.guardian_signup_invites
where guardian_user_id='10000000-0000-4000-8000-000000000001'
  and used_at is null;

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('10000000-0000-4000-8000-000000000001','YOUTH-ABCD123456',now()+interval '1 day');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '20000000-0000-4000-8000-000000000011',
  'child11@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '11 years')::date::text,
    'date_of_birth',(current_date-interval '11 years')::date::text,
    'gender','Homme','sex','male','pseudo','Enfant 11','display_name','Enfant 11','residence_country','Canada',
    'guardian_code','YOUTH-ABCD123456','initial_contributor_opt_in',true,'initial_share_free_text',true
  )
);

select ok(exists(select 1 from public.profiles where user_id='20000000-0000-4000-8000-000000000011'),'le compte enfant crée son profil');
select is((select date_of_birth from public.account_safety_profiles where user_id='20000000-0000-4000-8000-000000000011'),(current_date-interval '11 years')::date,'la date de naissance exacte de 11 ans est conservée');
select ok(exists(select 1 from public.guardian_links where minor_user_id='20000000-0000-4000-8000-000000000011' and guardian_user_id='10000000-0000-4000-8000-000000000001' and status='verified'),'le lien parent enfant est créé et vérifié');
select ok(exists(select 1 from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456' and used_at is not null and minor_user_id='20000000-0000-4000-8000-000000000011'),'le code parental est consommé une seule fois par le compte enfant');
select is(public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'child','un compte ayant exactement 11 ans devient child');
select ok(public.sinjira_parent_can_supervise('10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000011'),'le parent peut superviser le compte enfant');
select ok(not public.sinjira_can_social_interact('20000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011'),'les fonctions sociales restent coupées pour la bande child');
select ok(exists(select 1 from public.research_consents where user_id='20000000-0000-4000-8000-000000000011' and participate=false and share_free_text=false),'le Programme Contributeur est neutralisé côté serveur pour 11 ans');

update public.account_safety_profiles
set date_of_birth=(current_date-interval '13 years'+interval '1 day')::date
where user_id='20000000-0000-4000-8000-000000000011';
select is(public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'child','la veille des 13 ans reste classée child');

update public.account_safety_profiles
set date_of_birth=(current_date-interval '13 years')::date
where user_id='20000000-0000-4000-8000-000000000011';
select is(public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'youth','le jour des 13 ans la classification devient youth automatiquement');
select ok(public.sinjira_parent_can_supervise('10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000011'),'le lien parental vérifié continue de permettre la supervision à 13 ans');
select ok(public.sinjira_can_social_interact('20000000-0000-4000-8000-000000000011','20000000-0000-4000-8000-000000000011'),'le contrat social jeunesse peut s appliquer automatiquement à partir de 13 ans');

update public.guardian_links
set revoked_at=now()
where minor_user_id='20000000-0000-4000-8000-000000000011'
  and guardian_user_id='10000000-0000-4000-8000-000000000001'
  and status='verified';
select is(public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'youth_pending','revoked_at seul suffit à retirer la bande supervisée même si status est encore verified');
select ok(not public.sinjira_parent_can_supervise('10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000011'),'revoked_at seul suffit à retirer la supervision parentale');

select throws_ok($$
  insert into auth.users(id,email,raw_user_meta_data)
  values(
    '30000000-0000-4000-8000-000000000010',
    'child10@example.test',
    jsonb_build_object('birth_date',(current_date-interval '10 years')::date::text,'gender','Homme','pseudo','Enfant 10','residence_country','Canada')
  )
$$,'P0001','SINJIRA_MINIMUM_AGE_11','un enfant de 10 ans est refusé');

select throws_ok($$
  insert into auth.users(id,email,raw_user_meta_data)
  values(
    '40000000-0000-4000-8000-000000000011',
    'child11-no-guardian@example.test',
    jsonb_build_object('birth_date',(current_date-interval '11 years')::date::text,'gender','Homme','pseudo','Sans parent','residence_country','Canada')
  )
$$,'P0001','GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14','un compte de 11 ans sans code parental est refusé');

select throws_ok($$
  insert into auth.users(id,email,raw_user_meta_data)
  values(
    '50000000-0000-4000-8000-000000000011',
    'child11-outside-canada@example.test',
    jsonb_build_object('birth_date',(current_date-interval '11 years')::date::text,'gender','Homme','pseudo','Hors Canada','residence_country','France','guardian_code','YOUTH-ABCD123456')
  )
$$,'P0001','YOUTH_JURISDICTION_NOT_ENABLED','un compte jeunesse hors Canada reste refusé');

-- Régression V25 : après révocation, un 11–12 ans devient child_pending.
-- L'écran Relations lui propose un nouveau code; le RPC doit réellement permettre
-- de rétablir la supervision et le trigger canonique réactive le lien.
update public.account_safety_profiles
set date_of_birth=(current_date-interval '11 years')::date
where user_id='20000000-0000-4000-8000-000000000011';

select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'child_pending',
  'un enfant de 11 ans sans lien tuteur actif devient child_pending'
);

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values(
  '10000000-0000-4000-8000-000000000001',
  'YOUTH-REDEEM1101',
  now()+interval '1 day'
);

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);

select lives_ok(
  $$ select public.redeem_guardian_signup_invite('YOUTH-REDEEM1101') $$,
  'child_pending peut consommer un nouveau code parental valide'
);

select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'child',
  'la consommation du nouveau code rétablit immédiatement la bande child'
);

select ok(
  exists(
    select 1 from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
      and status='verified'
      and revoked_at is null
  ),
  'le lien tuteur révoqué est réactivé proprement en verified non révoqué'
);

select ok(
  exists(
    select 1 from public.guardian_signup_invites
    where invite_code='YOUTH-REDEEM1101'
      and used_at is not null
      and minor_user_id='20000000-0000-4000-8000-000000000011'
  ),
  'le nouveau code est consommé une seule fois par le compte child_pending'
);

select * from finish();
rollback;

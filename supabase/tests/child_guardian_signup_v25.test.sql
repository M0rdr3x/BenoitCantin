begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(69);

select ok(to_regprocedure('public.enforce_sinjira_account_safety_age()') is not null,'garde serveur de date de naissance existe');
select ok(to_regprocedure('public.handle_new_sinjira_user()') is not null,'pont de création de compte existe');
select ok(to_regprocedure('public.sinjira_age_band(uuid)') is not null,'classification d âge existe');
select ok(to_regprocedure('public.sinjira_parent_can_supervise(uuid,uuid)') is not null,'contrôle de supervision existe');

select ok(
  position('account_safety_profiles' in lower(pg_catalog.pg_get_functiondef(
    'sinjira_v25_internal.redeem_guardian_signup_invite(text)'::regprocedure
  ))) > 0
  and position('for update' in lower(pg_catalog.pg_get_functiondef(
    'sinjira_v25_internal.redeem_guardian_signup_invite(text)'::regprocedure
  ))) > 0,
  'le rétablissement parental sérialise les consommations concurrentes pour un même compte'
);
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

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
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
      and invite_code ~ '^YOUTH-[A-Z0-9]{16}
  ),
  'le code créé sous AAL2 respecte le format et reste à usage unique'
);

delete from public.guardian_signup_invites
where guardian_user_id='10000000-0000-4000-8000-000000000001'
  and used_at is null;

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('10000000-0000-4000-8000-000000000001','YOUTH-ABCD123456',now()+interval '1 day');

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','10000000-0000-4000-8000-000000000001',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456'),
  0,
  'une session tuteur AAL1 ne peut pas relire un code parental'
);
reset role;

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','10000000-0000-4000-8000-000000000001',
    'aal','aal2'
  )::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456'),
  1,
  'une session tuteur AAL2 peut relire son propre code parental'
);
reset role;

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

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);

select ok(exists(select 1 from public.profiles where user_id='20000000-0000-4000-8000-000000000011'),'le compte enfant crée son profil');
select is((select date_of_birth from public.account_safety_profiles where user_id='20000000-0000-4000-8000-000000000011'),(current_date-interval '11 years')::date,'la date de naissance exacte de 11 ans est conservée');
select ok(exists(select 1 from public.guardian_links where minor_user_id='20000000-0000-4000-8000-000000000011' and guardian_user_id='10000000-0000-4000-8000-000000000001' and status='verified'),'le lien parent enfant est créé et vérifié');
select is(
  (select can_view_contact_metadata from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'
     and guardian_user_id='10000000-0000-4000-8000-000000000001'),
  false,
  'un nouveau lien de supervision désactive les métadonnées de contacts par défaut'
);
select ok(exists(select 1 from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456' and used_at is not null and minor_user_id='20000000-0000-4000-8000-000000000011'),'le code parental est consommé une seule fois par le compte enfant');
select ok(
  not coalesce(
    (select raw_user_meta_data ? 'guardian_code'
     from auth.users
     where id='20000000-0000-4000-8000-000000000011'),
    false
  ),
  'le code parental consommé est supprimé des métadonnées Auth de l enfant'
);
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

-- Fail-closed adversarial : revoked_at doit suffire même si le statut reste verified.
update public.guardian_links
set revoked_at=now()
where minor_user_id='20000000-0000-4000-8000-000000000011'
  and guardian_user_id='10000000-0000-4000-8000-000000000001'
  and status='verified';

select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'youth_pending',
  'revoked_at seul suffit à retirer la bande supervisée même si status est encore verified'
);
select ok(
  not public.sinjira_parent_can_supervise(
    '10000000-0000-4000-8000-000000000001',
    '20000000-0000-4000-8000-000000000011'
  ),
  'revoked_at seul suffit à retirer la supervision parentale'
);

update public.guardian_links
set revoked_at=null
where minor_user_id='20000000-0000-4000-8000-000000000011'
  and guardian_user_id='10000000-0000-4000-8000-000000000001'
  and status='verified';

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select throws_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'GUARDIAN_CONTACT_METADATA_NOT_ALLOWED',
  'le tuteur ne peut pas lire les métadonnées de contacts sans consentement explicite'
);

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select lives_ok(
  $$ select public.set_my_guardian_contact_metadata((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  ),true) $$,
  'le compte jeunesse peut autoriser explicitement ses métadonnées de contacts'
);
select is(
  (select can_view_contact_metadata from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'
     and guardian_user_id='10000000-0000-4000-8000-000000000001'),
  true,
  'l autorisation explicite du compte jeunesse est enregistrée'
);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '70000000-0000-4000-8000-000000000015',
  'youth-contact@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '15 years')::date::text,
    'date_of_birth',(current_date-interval '15 years')::date::text,
    'gender','Femme','sex','female','pseudo','Contact Jeunesse','display_name','Nom Affiché Privé','residence_country','Canada'
  )
);

insert into public.social_real_messages(
  sender_user_id,recipient_user_id,body,created_at
)
values(
  '20000000-0000-4000-8000-000000000011',
  '70000000-0000-4000-8000-000000000015',
  'message de preuve non exposé au tuteur',
  now()-interval '3 hours'
);

insert into public.characters(
  id,user_id,public_name,public_description,status,visible_to_user
)
values
(
  '81000000-0000-4000-8000-000000000011',
  '20000000-0000-4000-8000-000000000011',
  'Personnage Enfant',
  'identité personnage enfant de preuve',
  'approved',
  true
),
(
  '81000000-0000-4000-8000-000000000015',
  '70000000-0000-4000-8000-000000000015',
  'Avatar Secret',
  'identité personnage contact de preuve',
  'approved',
  true
);

insert into public.social_character_messages(
  sender_user_id,recipient_user_id,
  sender_character_id,recipient_character_id,
  body,created_at
)
values(
  '20000000-0000-4000-8000-000000000011',
  '70000000-0000-4000-8000-000000000015',
  '81000000-0000-4000-8000-000000000011',
  '81000000-0000-4000-8000-000000000015',
  'message personnage de preuve non exposé au tuteur',
  now()-interval '2 hours'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select throws_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'le tuteur AAL1 ne peut pas lire les métadonnées de contacts jeunesse'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select lives_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'le tuteur avec consentement explicite et AAL2 peut lire uniquement les métadonnées de contacts jeunesse'
);

select is(
  jsonb_array_length(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')),
  2,
  'le résumé parental sépare le contact Compte et le contact Personnage'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item ? 'user_id'
       or item ? 'display_name'
       or item ? 'last_contact_at'
       or item ? 'pseudo'
       or item ? 'networks'
  ),
  'le résumé parental ne révèle ni UUID, display_name, ancien pseudo brut ni timestamp précis'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Compte'
      and item->>'contact_label'='Contact Jeunesse'
  )
  and exists(
    select 1
    from public.social_profiles sp
    where sp.user_id='70000000-0000-4000-8000-000000000015'
      and sp.pseudo='Contact Jeunesse'
      and sp.display_name='Contact Jeunesse'
  )
  and not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'contact_label'='Nom Affiché Privé'
  ),
  'le réseau Compte conserve uniquement le pseudo public du contact'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Personnage'
      and item->>'contact_label'='Avatar Secret'
  ),
  'le réseau Personnage expose uniquement le nom public du personnage'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Personnage'
      and item->>'contact_label'='Contact Jeunesse'
  ),
  'le résumé ne recolle pas le personnage au pseudo de son compte réel'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where not (item ? 'network' and item ? 'contact_label' and item ? 'last_contact_date')
  ),
  'chaque entrée ne conserve que label public, réseau et date de dernier contact'
);
select ok(
  coalesce((
    select item->>'last_contact_date'
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Personnage'
    limit 1
  ),'') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$',
  'la dernière interaction personnage reste réduite à une date sans heure précise'
);

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select lives_ok(
  $$ select public.set_my_guardian_contact_metadata((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  ),false) $$,
  'le compte jeunesse peut retirer immédiatement la permission de métadonnées'
);
select is(
  (select can_view_contact_metadata from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'
     and guardian_user_id='10000000-0000-4000-8000-000000000001'),
  false,
  'le retrait de permission est enregistré immédiatement'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select throws_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'GUARDIAN_CONTACT_METADATA_NOT_ALLOWED',
  'après retrait le tuteur AAL2 perd immédiatement l accès aux métadonnées de contacts'
);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '10000000-0000-4000-8000-000000000099',
  'unrelated-guardian-probe@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '34 years')::date::text,
    'date_of_birth',(current_date-interval '34 years')::date::text,
    'gender','Homme','sex','male','pseudo','Adulte tiers','display_name','Adulte tiers','residence_country','Canada'
  )
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000099',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000099','aal','aal2')::text,
  true
);
select throws_ok(
  $ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $,
  'P0001',
  'GUARDIAN_LINK_UNAVAILABLE',
  'un compte tiers ne peut pas distinguer un lien de supervision existant'
);
select throws_ok(
  $ select public.revoke_guardian_link('ffffffff-ffff-4fff-8fff-ffffffffffff'::uuid) $,
  'P0001',
  'GUARDIAN_LINK_UNAVAILABLE',
  'un lien inexistant renvoie la même erreur fail-closed qu un lien tiers'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select throws_ok(
  $ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'un tuteur AAL1 ne peut pas révoquer le lien de supervision'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select lives_ok(
  $$ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $$,
  'un tuteur AAL2 peut révoquer le lien de supervision'
);
select is(public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'youth_pending','la révocation tuteur AAL2 retire la bande supervisée');
select ok(not public.sinjira_parent_can_supervise('10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000011'),'la révocation tuteur AAL2 retire la supervision parentale');

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

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select lives_ok(
  $$ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $$,
  'l enfant AAL1 peut quitter immédiatement son propre lien de supervision'
);
select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'child_pending',
  'quitter son lien remet immédiatement le compte 11 ans en child_pending'
);

-- Majorité : la supervision cesse aussi comme visibilité pour l'ancien tuteur.
update public.account_safety_profiles
set date_of_birth=(current_date-interval '18 years')::date
where user_id='20000000-0000-4000-8000-000000000011';

select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'adult',
  'le jour des 18 ans le compte devient adult'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer
   from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'),
  0,
  'à 18 ans l ancien tuteur ne peut plus lire le lien de supervision'
);
select is(
  (select count(*)::integer
   from public.guardian_signup_invites
   where minor_user_id='20000000-0000-4000-8000-000000000011'),
  0,
  'à 18 ans l ancien tuteur ne peut plus relire les invitations parentales consommées'
);
reset role;

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer
   from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'),
  1,
  'la personne devenue adulte conserve l accès à son propre historique de supervision'
);
reset role;

insert into auth.users(id,email,raw_user_meta_data)
values(
  '60000000-0000-4000-8000-000000000099',
  'guardian-link-outsider@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '30 years')::date::text,
    'date_of_birth',(current_date-interval '30 years')::date::text,
    'gender','Femme','sex','female','pseudo','Tiers test','display_name','Tiers test','residence_country','Canada'
  )
);

select set_config('request.jwt.claim.sub','60000000-0000-4000-8000-000000000099',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','60000000-0000-4000-8000-000000000099','aal','aal2')::text,
  true
);
select ok(
  not public.sinjira_can_read_guardian_link((
    select id
    from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
    limit 1
  )),
  'un tiers ne peut pas utiliser le helper pour sonder un lien qui ne le concerne pas'
);

select ok(
  position(
    $needle$values(new.id,'memorialize','peaceful',false,false)$needle$
    in lower(pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))
  ) > 0,
  'l inscription ne préactive jamais la publication mémorielle publique'
);

select ok(
  position(
    $needle$values(new.id,dob,sx,false,false,false,'not_specified','active')$needle$
    in lower(pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))
  ) > 0,
  'l inscription ne préactive jamais les souhaits anniversaire ni les usages privés optionnels'
);

select * from finish();
rollback;

  ),
  'le code créé sous AAL2 respecte le format et reste à usage unique'
);

delete from public.guardian_signup_invites
where guardian_user_id='10000000-0000-4000-8000-000000000001'
  and used_at is null;

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('10000000-0000-4000-8000-000000000001','YOUTH-ABCD123456',now()+interval '1 day');

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','10000000-0000-4000-8000-000000000001',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456'),
  0,
  'une session tuteur AAL1 ne peut pas relire un code parental'
);
reset role;

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','10000000-0000-4000-8000-000000000001',
    'aal','aal2'
  )::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456'),
  1,
  'une session tuteur AAL2 peut relire son propre code parental'
);
reset role;

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

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);

select ok(exists(select 1 from public.profiles where user_id='20000000-0000-4000-8000-000000000011'),'le compte enfant crée son profil');
select is((select date_of_birth from public.account_safety_profiles where user_id='20000000-0000-4000-8000-000000000011'),(current_date-interval '11 years')::date,'la date de naissance exacte de 11 ans est conservée');
select ok(exists(select 1 from public.guardian_links where minor_user_id='20000000-0000-4000-8000-000000000011' and guardian_user_id='10000000-0000-4000-8000-000000000001' and status='verified'),'le lien parent enfant est créé et vérifié');
select is(
  (select can_view_contact_metadata from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'
     and guardian_user_id='10000000-0000-4000-8000-000000000001'),
  false,
  'un nouveau lien de supervision désactive les métadonnées de contacts par défaut'
);
select ok(exists(select 1 from public.guardian_signup_invites where invite_code='YOUTH-ABCD123456' and used_at is not null and minor_user_id='20000000-0000-4000-8000-000000000011'),'le code parental est consommé une seule fois par le compte enfant');
select ok(
  not coalesce(
    (select raw_user_meta_data ? 'guardian_code'
     from auth.users
     where id='20000000-0000-4000-8000-000000000011'),
    false
  ),
  'le code parental consommé est supprimé des métadonnées Auth de l enfant'
);
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

-- Fail-closed adversarial : revoked_at doit suffire même si le statut reste verified.
update public.guardian_links
set revoked_at=now()
where minor_user_id='20000000-0000-4000-8000-000000000011'
  and guardian_user_id='10000000-0000-4000-8000-000000000001'
  and status='verified';

select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'youth_pending',
  'revoked_at seul suffit à retirer la bande supervisée même si status est encore verified'
);
select ok(
  not public.sinjira_parent_can_supervise(
    '10000000-0000-4000-8000-000000000001',
    '20000000-0000-4000-8000-000000000011'
  ),
  'revoked_at seul suffit à retirer la supervision parentale'
);

update public.guardian_links
set revoked_at=null
where minor_user_id='20000000-0000-4000-8000-000000000011'
  and guardian_user_id='10000000-0000-4000-8000-000000000001'
  and status='verified';

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select throws_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'GUARDIAN_CONTACT_METADATA_NOT_ALLOWED',
  'le tuteur ne peut pas lire les métadonnées de contacts sans consentement explicite'
);

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select lives_ok(
  $$ select public.set_my_guardian_contact_metadata((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  ),true) $$,
  'le compte jeunesse peut autoriser explicitement ses métadonnées de contacts'
);
select is(
  (select can_view_contact_metadata from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'
     and guardian_user_id='10000000-0000-4000-8000-000000000001'),
  true,
  'l autorisation explicite du compte jeunesse est enregistrée'
);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '70000000-0000-4000-8000-000000000015',
  'youth-contact@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '15 years')::date::text,
    'date_of_birth',(current_date-interval '15 years')::date::text,
    'gender','Femme','sex','female','pseudo','Contact Jeunesse','display_name','Nom Affiché Privé','residence_country','Canada'
  )
);

insert into public.social_real_messages(
  sender_user_id,recipient_user_id,body,created_at
)
values(
  '20000000-0000-4000-8000-000000000011',
  '70000000-0000-4000-8000-000000000015',
  'message de preuve non exposé au tuteur',
  now()-interval '3 hours'
);

insert into public.characters(
  id,user_id,public_name,public_description,status,visible_to_user
)
values
(
  '81000000-0000-4000-8000-000000000011',
  '20000000-0000-4000-8000-000000000011',
  'Personnage Enfant',
  'identité personnage enfant de preuve',
  'approved',
  true
),
(
  '81000000-0000-4000-8000-000000000015',
  '70000000-0000-4000-8000-000000000015',
  'Avatar Secret',
  'identité personnage contact de preuve',
  'approved',
  true
);

insert into public.social_character_messages(
  sender_user_id,recipient_user_id,
  sender_character_id,recipient_character_id,
  body,created_at
)
values(
  '20000000-0000-4000-8000-000000000011',
  '70000000-0000-4000-8000-000000000015',
  '81000000-0000-4000-8000-000000000011',
  '81000000-0000-4000-8000-000000000015',
  'message personnage de preuve non exposé au tuteur',
  now()-interval '2 hours'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select throws_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'le tuteur AAL1 ne peut pas lire les métadonnées de contacts jeunesse'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select lives_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'le tuteur avec consentement explicite et AAL2 peut lire uniquement les métadonnées de contacts jeunesse'
);

select is(
  jsonb_array_length(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')),
  2,
  'le résumé parental sépare le contact Compte et le contact Personnage'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item ? 'user_id'
       or item ? 'display_name'
       or item ? 'last_contact_at'
       or item ? 'pseudo'
       or item ? 'networks'
  ),
  'le résumé parental ne révèle ni UUID, display_name, ancien pseudo brut ni timestamp précis'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Compte'
      and item->>'contact_label'='Contact Jeunesse'
  )
  and exists(
    select 1
    from public.social_profiles sp
    where sp.user_id='70000000-0000-4000-8000-000000000015'
      and sp.pseudo='Contact Jeunesse'
      and sp.display_name='Contact Jeunesse'
  )
  and not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'contact_label'='Nom Affiché Privé'
  ),
  'le réseau Compte conserve uniquement le pseudo public du contact'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Personnage'
      and item->>'contact_label'='Avatar Secret'
  ),
  'le réseau Personnage expose uniquement le nom public du personnage'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Personnage'
      and item->>'contact_label'='Contact Jeunesse'
  ),
  'le résumé ne recolle pas le personnage au pseudo de son compte réel'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where not (item ? 'network' and item ? 'contact_label' and item ? 'last_contact_date')
  ),
  'chaque entrée ne conserve que label public, réseau et date de dernier contact'
);
select ok(
  coalesce((
    select item->>'last_contact_date'
    from jsonb_array_elements(public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011')) item
    where item->>'network'='Personnage'
    limit 1
  ),'') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$',
  'la dernière interaction personnage reste réduite à une date sans heure précise'
);

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select lives_ok(
  $$ select public.set_my_guardian_contact_metadata((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  ),false) $$,
  'le compte jeunesse peut retirer immédiatement la permission de métadonnées'
);
select is(
  (select can_view_contact_metadata from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'
     and guardian_user_id='10000000-0000-4000-8000-000000000001'),
  false,
  'le retrait de permission est enregistré immédiatement'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select throws_ok(
  $$ select public.get_guardian_youth_contacts('20000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'GUARDIAN_CONTACT_METADATA_NOT_ALLOWED',
  'après retrait le tuteur AAL2 perd immédiatement l accès aux métadonnées de contacts'
);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '10000000-0000-4000-8000-000000000099',
  'unrelated-guardian-probe@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '34 years')::date::text,
    'date_of_birth',(current_date-interval '34 years')::date::text,
    'gender','Homme','sex','male','pseudo','Adulte tiers','display_name','Adulte tiers','residence_country','Canada'
  )
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000099',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000099','aal','aal2')::text,
  true
);
select throws_ok(
  $ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $,
  'P0001',
  'GUARDIAN_LINK_UNAVAILABLE',
  'un compte tiers ne peut pas distinguer un lien de supervision existant'
);
select throws_ok(
  $ select public.revoke_guardian_link('ffffffff-ffff-4fff-8fff-ffffffffffff'::uuid) $,
  'P0001',
  'GUARDIAN_LINK_UNAVAILABLE',
  'un lien inexistant renvoie la même erreur fail-closed qu un lien tiers'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select throws_ok(
  $ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'un tuteur AAL1 ne peut pas révoquer le lien de supervision'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select lives_ok(
  $$ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $$,
  'un tuteur AAL2 peut révoquer le lien de supervision'
);
select is(public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),'youth_pending','la révocation tuteur AAL2 retire la bande supervisée');
select ok(not public.sinjira_parent_can_supervise('10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000011'),'la révocation tuteur AAL2 retire la supervision parentale');

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

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select lives_ok(
  $$ select public.revoke_guardian_link((
    select id from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
      and guardian_user_id='10000000-0000-4000-8000-000000000001'
  )) $$,
  'l enfant AAL1 peut quitter immédiatement son propre lien de supervision'
);
select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'child_pending',
  'quitter son lien remet immédiatement le compte 11 ans en child_pending'
);

-- Majorité : la supervision cesse aussi comme visibilité pour l'ancien tuteur.
update public.account_safety_profiles
set date_of_birth=(current_date-interval '18 years')::date
where user_id='20000000-0000-4000-8000-000000000011';

select is(
  public.sinjira_age_band('20000000-0000-4000-8000-000000000011'),
  'adult',
  'le jour des 18 ans le compte devient adult'
);

select set_config('request.jwt.claim.sub','10000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','10000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer
   from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'),
  0,
  'à 18 ans l ancien tuteur ne peut plus lire le lien de supervision'
);
select is(
  (select count(*)::integer
   from public.guardian_signup_invites
   where minor_user_id='20000000-0000-4000-8000-000000000011'),
  0,
  'à 18 ans l ancien tuteur ne peut plus relire les invitations parentales consommées'
);
reset role;

select set_config('request.jwt.claim.sub','20000000-0000-4000-8000-000000000011',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','20000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer
   from public.guardian_links
   where minor_user_id='20000000-0000-4000-8000-000000000011'),
  1,
  'la personne devenue adulte conserve l accès à son propre historique de supervision'
);
reset role;

insert into auth.users(id,email,raw_user_meta_data)
values(
  '60000000-0000-4000-8000-000000000099',
  'guardian-link-outsider@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '30 years')::date::text,
    'date_of_birth',(current_date-interval '30 years')::date::text,
    'gender','Femme','sex','female','pseudo','Tiers test','display_name','Tiers test','residence_country','Canada'
  )
);

select set_config('request.jwt.claim.sub','60000000-0000-4000-8000-000000000099',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','60000000-0000-4000-8000-000000000099','aal','aal2')::text,
  true
);
select ok(
  not public.sinjira_can_read_guardian_link((
    select id
    from public.guardian_links
    where minor_user_id='20000000-0000-4000-8000-000000000011'
    limit 1
  )),
  'un tiers ne peut pas utiliser le helper pour sonder un lien qui ne le concerne pas'
);

select ok(
  position(
    $needle$values(new.id,'memorialize','peaceful',false,false)$needle$
    in lower(pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))
  ) > 0,
  'l inscription ne préactive jamais la publication mémorielle publique'
);

select ok(
  position(
    $needle$values(new.id,dob,sx,false,false,false,'not_specified','active')$needle$
    in lower(pg_get_functiondef('public.handle_new_sinjira_user()'::regprocedure))
  ) > 0,
  'l inscription ne préactive jamais les souhaits anniversaire ni les usages privés optionnels'
);

select * from finish();
rollback;

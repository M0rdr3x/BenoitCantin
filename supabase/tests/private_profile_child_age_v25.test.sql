begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(13);

select ok(
  position(
    'SINJIRA_MINIMUM_AGE_11'
    in pg_get_functiondef(
      'sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure
    )
  )>0,
  'le coffre privé applique le minimum actuel de 11 ans'
);

select ok(
  position(
    'SINJIRA_MINIMUM_AGE_13'
    in pg_get_functiondef(
      'sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure
    )
  )=0,
  'l ancienne limite effective de 13 ans n est plus active'
);

select ok(
  position(
    'revoked_at is null'
    in lower(pg_get_functiondef(
      'sinjira_profile_internal.private_profile_save(date,text,text[],text,text,text,text,text,text,text,date,text)'::regprocedure
    ))
  )>0,
  'la supervision exigée avant 14 ans exclut un lien révoqué'
);

update public.sinjira_security_settings
set require_phone_mfa=false
where singleton_id=1;

insert into auth.users(id,email,raw_user_meta_data)
values
(
  'd1000000-0000-4000-8000-000000000001',
  'profile-guardian@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '40 years')::date::text,
    'date_of_birth',(current_date-interval '40 years')::date::text,
    'gender','Homme','sex','male',
    'pseudo','Tuteur Profil',
    'display_name','Tuteur Profil',
    'residence_country','Canada'
  )
),
(
  'd2000000-0000-4000-8000-000000000002',
  'profile-child-active@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '20 years')::date::text,
    'date_of_birth',(current_date-interval '20 years')::date::text,
    'gender','Femme','sex','female',
    'pseudo','Enfant Profil Actif',
    'display_name','Enfant Profil Actif',
    'residence_country','Canada'
  )
),
(
  'd3000000-0000-4000-8000-000000000003',
  'profile-child-no-guardian@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '20 years')::date::text,
    'date_of_birth',(current_date-interval '20 years')::date::text,
    'gender','Homme','sex','male',
    'pseudo','Enfant Profil Sans Tuteur',
    'display_name','Enfant Profil Sans Tuteur',
    'residence_country','Canada'
  )
);

update public.account_safety_profiles
set date_of_birth=(current_date-interval '11 years')::date
where user_id in (
  'd2000000-0000-4000-8000-000000000002',
  'd3000000-0000-4000-8000-000000000003'
);

insert into public.guardian_links(
  minor_user_id,guardian_user_id,status,guardian_role,consented_at,revoked_at
)
values(
  'd2000000-0000-4000-8000-000000000002',
  'd1000000-0000-4000-8000-000000000001',
  'verified',
  'parent',
  now(),
  null
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','d2000000-0000-4000-8000-000000000002',
    'role','authenticated',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;

select lives_ok(
  $$ select public.private_profile_save(
    (current_date-interval '11 years')::date,
    'prefer_not_to_say',
    array['Français'],
    'Montréal',
    'Québec',
    'Canada',
    null,
    null,
    null,
    'not_set',
    null,
    null
  ) $$,
  'un enfant de 11 ans avec tuteur actif peut enregistrer son coffre privé'
);

select lives_ok(
  $read$ select public.private_profile_get() $read$,
  'un enfant de 11 ans avec tuteur actif peut relire son coffre privé'
);

select throws_ok(
  $age_review$ select public.private_profile_save(
    (current_date-interval '18 years')::date,
    'prefer_not_to_say',
    array['Français'],
    'Montréal',
    'Québec',
    'Canada',
    null,
    null,
    null,
    'not_set',
    null,
    null
  ) $age_review$,
  'P0001',
  'BIRTH_DATE_PROTECTION_BOUNDARY_REQUIRES_REVIEW',
  'un compte mineur ne peut pas se vieillir lui-même pour sortir des protections Junior'
);

reset role;

select is(
  (
    select date_of_birth
    from public.account_safety_profiles
    where user_id='d2000000-0000-4000-8000-000000000002'
  ),
  (current_date-interval '11 years')::date,
  'la tentative de vieillissement ne modifie pas la date de sécurité canonique'
);

select is(
  (
    select birth_date
    from public.private_profiles
    where user_id='d2000000-0000-4000-8000-000000000002'
  ),
  (current_date-interval '11 years')::date,
  'la date de naissance de 11 ans est conservée dans le coffre privé'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','d3000000-0000-4000-8000-000000000003',
    'role','authenticated',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;

select throws_ok(
  $$ select public.private_profile_save(
    (current_date-interval '11 years')::date,
    'prefer_not_to_say',
    array['Français'],
    null,
    null,
    'Canada',
    null,
    null,
    null,
    'not_set',
    null,
    null
  ) $$,
  'P0001',
  'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14',
  'un enfant de 11 ans sans tuteur actif ne peut pas enregistrer son coffre'
);

select throws_ok(
  $read$ select public.private_profile_get() $read$,
  'P0001',
  'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14',
  'un enfant de 11 ans sans tuteur actif ne peut pas relire son coffre'
);

select throws_ok(
  $$ select public.private_profile_save(
    (current_date-interval '10 years')::date,
    'prefer_not_to_say',
    array['Français'],
    null,
    null,
    'Canada',
    null,
    null,
    null,
    'not_set',
    null,
    null
  ) $$,
  'P0001',
  'SINJIRA_MINIMUM_AGE_11',
  'un compte sous 11 ans reste refusé'
);

reset role;

insert into public.guardian_links(
  minor_user_id,guardian_user_id,status,guardian_role,consented_at,revoked_at
)
values(
  'd3000000-0000-4000-8000-000000000003',
  'd1000000-0000-4000-8000-000000000001',
  'verified',
  'parent',
  now(),
  now()
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','d3000000-0000-4000-8000-000000000003',
    'role','authenticated',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;

select throws_ok(
  $$ select public.private_profile_save(
    (current_date-interval '11 years')::date,
    'prefer_not_to_say',
    array['Français'],
    null,
    null,
    'Canada',
    null,
    null,
    null,
    'not_set',
    null,
    null
  ) $$,
  'P0001',
  'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14',
  'un lien tuteur révoqué ne satisfait jamais la supervision'
);

select throws_ok(
  $read$ select public.private_profile_get() $read$,
  'P0001',
  'GUARDIAN_AUTHORIZATION_REQUIRED_UNDER_14',
  'un lien tuteur révoqué bloque aussi la lecture du coffre'
);

reset role;

select * from finish();
rollback;

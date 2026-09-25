begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(26);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '75000000-0000-4000-8000-000000000001',
  'junior-revocation-guardian-a@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '38 years')::date::text,
    'date_of_birth',(current_date-interval '38 years')::date::text,
    'gender','Homme','sex','male','pseudo','Tuteur A','display_name','Tuteur A','residence_country','Canada'
  )
);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '75000000-0000-4000-8000-000000000002',
  'junior-revocation-guardian-b@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '41 years')::date::text,
    'date_of_birth',(current_date-interval '41 years')::date::text,
    'gender','Femme','sex','female','pseudo','Tuteur B','display_name','Tuteur B','residence_country','Canada'
  )
);

select is(public.sinjira_age_band('75000000-0000-4000-8000-000000000001'),'adult','tuteur A adulte');
select is(public.sinjira_age_band('75000000-0000-4000-8000-000000000002'),'adult','tuteur B adulte');

select ok(
  position(
    'frompublic.guardian_linksgwhereg.guardian_user_id=uidandg.minor_user_id=p_child_user_idandg.status=''verified''andg.revoked_atisnullforupdate'
    in regexp_replace(
      lower(pg_catalog.pg_get_functiondef(
        'sinjira_v25_internal.guardian_set_junior_community(uuid,boolean)'::regprocedure
      )),
      '[[:space:]]+', '', 'g'
    )
  ) > 0,
  'activation Junior sérialise le lien tuteur avant le consentement'
);

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('75000000-0000-4000-8000-000000000001','YOUTH-REVOKE0001',now()+interval '1 day');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '75000000-0000-4000-8000-000000000011',
  'junior-revocation-child@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '11 years')::date::text,
    'date_of_birth',(current_date-interval '11 years')::date::text,
    'gender','Homme','sex','male','pseudo','Enfant Test','display_name','Enfant Test','residence_country','Canada',
    'guardian_code','YOUTH-REVOKE0001'
  )
);

select is(public.sinjira_age_band('75000000-0000-4000-8000-000000000011'),'child','enfant initialement child via tuteur A');

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select throws_ok(
  $$ select public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true) $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'tuteur AAL1 ne peut pas activer la Communauté Junior'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select is(
  (public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,
  true,
  'tuteur A active Junior sous AAL2 avant révocation'
);

insert into public.junior_community_posts(author_user_id,body,created_at)
values(
  '75000000-0000-4000-8000-000000000011',
  'activité Junior de preuve non visible au tuteur',
  now()-interval '2 hours'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select throws_ok(
  $$ select public.junior_guardian_summary('75000000-0000-4000-8000-000000000011') $$,
  'P0001',
  'MFA_AAL2_REQUIRED',
  'tuteur AAL1 ne peut pas lire le résumé d activité Junior'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select ok(
  not (public.junior_guardian_summary('75000000-0000-4000-8000-000000000011') ? 'last_activity_at')
  and public.junior_guardian_summary('75000000-0000-4000-8000-000000000011') ? 'last_activity_date',
  'le résumé Junior ne révèle plus l heure précise de dernière activité'
);
select ok(
  coalesce(
    public.junior_guardian_summary('75000000-0000-4000-8000-000000000011')->>'last_activity_date',
    ''
  ) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$',
  'le résumé Junior réduit la dernière activité à une date'
);
select is(
  (public.junior_guardian_summary('75000000-0000-4000-8000-000000000011')->>'posts')::integer,
  1,
  'le résumé AAL2 conserve seulement le compte utile des publications'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000011',true);
select ok(public.sinjira_junior_community_enabled(),'Junior est actif tant que le lien A est valide');

insert into public.guardian_links(
  minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at
)
values(
  '75000000-0000-4000-8000-000000000011',
  '75000000-0000-4000-8000-000000000002',
  'verified','parent',true,now()
);

update public.guardian_links
set revoked_at=now()
where minor_user_id='75000000-0000-4000-8000-000000000011'
  and guardian_user_id='75000000-0000-4000-8000-000000000001';

select ok(
  exists(
    select 1
    from public.junior_community_guardian_consents
    where minor_user_id='75000000-0000-4000-8000-000000000011'
      and guardian_user_id='75000000-0000-4000-8000-000000000001'
      and revoked_at is not null
  ),
  'révoquer le lien A révoque durablement son consentement Junior'
);

select is(
  public.sinjira_age_band('75000000-0000-4000-8000-000000000011'),
  'child',
  'le tuteur B valide maintient la bande child après révocation de A'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000011',true);
select ok(
  not public.sinjira_junior_community_enabled(),
  'le consentement Junior de A ne survit pas à la révocation de son lien même si B reste valide'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);
select ok(
  position('75000000-0000-4000-8000-000000000011' in public.guardian_junior_community_children()::text)=0,
  'le tuteur A révoqué ne voit plus l enfant dans sa liste Junior'
);

select throws_ok(
  $$select public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)$$,
  'P0001',
  'GUARDIAN_ACCESS_REQUIRED',
  'le tuteur A révoqué ne peut pas réactiver Junior'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000002',true);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.guardian_junior_community_children()) item
    where item->>'minor_user_id'='75000000-0000-4000-8000-000000000011'
      and (item->>'enabled')::boolean=false
  ),
  'le tuteur B valide voit l enfant sans hériter du consentement Junior de A'
);

select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.guardian_junior_community_children()) item
    where item ? 'junior_alias'
  ),
  'la liste tuteur ne révèle jamais le pseudonyme Junior de l enfant'
);

-- Révoquer aussi B fait passer l'enfant en child_pending.
update public.guardian_links
set revoked_at=now()
where minor_user_id='75000000-0000-4000-8000-000000000011'
  and guardian_user_id='75000000-0000-4000-8000-000000000002';

select is(
  public.sinjira_age_band('75000000-0000-4000-8000-000000000011'),
  'child_pending',
  'sans lien tuteur actif le compte 11 ans devient child_pending'
);

-- Un nouveau code de A rétablit la supervision, mais ne doit pas réactiver l'ancien consentement Junior.
insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('75000000-0000-4000-8000-000000000001','YOUTH-RECONSENT1',now()+interval '1 day');

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000011',true);
select lives_ok(
  $$ select public.redeem_guardian_signup_invite('YOUTH-RECONSENT1') $$,
  'child_pending peut rétablir la supervision avec un nouveau code de A'
);

select is(
  public.sinjira_age_band('75000000-0000-4000-8000-000000000011'),
  'child',
  'le nouveau code rétablit la bande child'
);

select ok(
  not public.sinjira_junior_community_enabled(),
  'l ancien consentement Junior de A reste révoqué après rétablissement de supervision'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select is(
  (public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,
  true,
  'une nouvelle activation Junior explicite est nécessaire après rétablissement de supervision'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000011',true);
select ok(
  public.sinjira_junior_community_enabled(),
  'Junior ne redevient actif qu après la nouvelle activation explicite de A'
);

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000001','aal','aal1')::text,
  true
);
select is(
  (public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',false)->>'enabled')::boolean,
  false,
  'tuteur AAL1 peut toujours désactiver Junior en voie fail-safe'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','75000000-0000-4000-8000-000000000011','aal','aal1')::text,
  true
);
select ok(
  not public.sinjira_junior_community_enabled(),
  'la désactivation AAL1 coupe immédiatement Junior pour l enfant'
);

select * from finish();
rollback;

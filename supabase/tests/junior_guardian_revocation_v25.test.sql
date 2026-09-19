begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(17);

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

select set_config('request.jwt.claim.sub','75000000-0000-4000-8000-000000000001',true);
select is(
  (public.guardian_set_junior_community('75000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,
  true,
  'tuteur A active Junior avant révocation'
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
  $ select public.redeem_guardian_signup_invite('YOUTH-RECONSENT1') $,
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

select * from finish();
rollback;

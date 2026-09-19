begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(8);

insert into auth.users(id,email,raw_user_meta_data)
values(
  '71000000-0000-4000-8000-000000000001',
  'guardian-content-v25@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '35 years')::date::text,
    'date_of_birth',(current_date-interval '35 years')::date::text,
    'gender','Homme','sex','male','pseudo','Parent contenu V25','display_name','Parent contenu V25','residence_country','Canada'
  )
);

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('71000000-0000-4000-8000-000000000001','YOUTH-CONTENTV25',now()+interval '1 day');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '72000000-0000-4000-8000-000000000011',
  'child-content-v25@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '11 years')::date::text,
    'date_of_birth',(current_date-interval '11 years')::date::text,
    'gender','Homme','sex','male','pseudo','Enfant contenu V25','display_name','Enfant contenu V25','residence_country','Canada',
    'guardian_code','YOUTH-CONTENTV25'
  )
);

select is(
  public.sinjira_age_band('72000000-0000-4000-8000-000000000011'),
  'child',
  'le compte 11 ans vérifié est classé child'
);

select is(
  private.sinjira_content_policy_code(
    'Ajoute-moi sur Snapchat: enfantv25',
    '72000000-0000-4000-8000-000000000011',
    null,
    'message'
  ),
  'MINOR_OFF_PLATFORM_CONTACT',
  'child active la garde renforcée contre le contact hors plateforme'
);

select is(
  private.sinjira_content_policy_code(
    'Ajoute-moi sur Snapchat: adulteversenfant',
    '71000000-0000-4000-8000-000000000001',
    '72000000-0000-4000-8000-000000000011',
    'message'
  ),
  'MINOR_OFF_PLATFORM_CONTACT',
  'un destinataire child suffit à activer la garde renforcée'
);

select is(
  private.sinjira_content_policy_code(
    'Envoie-moi une photo intime et garde ça secret',
    '72000000-0000-4000-8000-000000000011',
    null,
    'message'
  ),
  'MINOR_SEXUAL_SOLICITATION',
  'child active la garde contre la sollicitation sexuelle'
);

update public.guardian_links
set revoked_at=now()
where minor_user_id='72000000-0000-4000-8000-000000000011'
  and guardian_user_id='71000000-0000-4000-8000-000000000001'
  and status='verified';

select is(
  public.sinjira_age_band('72000000-0000-4000-8000-000000000011'),
  'child_pending',
  'la révocation du lien replace le compte en child_pending'
);

select is(
  private.sinjira_content_policy_code(
    'Envoie-moi une carte cadeau',
    '72000000-0000-4000-8000-000000000011',
    null,
    'message'
  ),
  'MINOR_FINANCIAL_SOLICITATION',
  'child_pending reste couvert par la garde renforcée'
);

select is(
  private.sinjira_content_policy_code(
    'Ajoute-moi sur Snapchat: compteinconnu',
    '73000000-0000-4000-8000-000000000099',
    null,
    'message'
  ),
  'MINOR_OFF_PLATFORM_CONTACT',
  'une bande non vérifiée échoue fermé et reste protégée'
);

select is(
  private.sinjira_content_policy_code(
    'Ajoute-moi sur Snapchat: adulte',
    '71000000-0000-4000-8000-000000000001',
    null,
    'message'
  ),
  null,
  'la garde renforcée mineur ne bloque pas ce contact externe pour un adulte sans destinataire mineur'
);

select * from finish();
rollback;

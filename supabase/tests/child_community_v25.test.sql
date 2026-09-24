begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(59);

select ok(to_regprocedure('private.sinjira_junior_community_enabled(uuid)') is not null,'garde privée d activation Junior existe');
select ok(to_regprocedure('public.junior_community_feed(integer)') is not null,'RPC fil Junior existe');
select ok(to_regprocedure('public.guardian_set_junior_community(uuid,boolean)') is not null,'RPC parent activation Junior existe');
select ok(to_regprocedure('public.sinjira_junior_community_enabled()') is not null,'RPC état Junior self-only existe');
select ok(to_regprocedure('public.sinjira_junior_community_enabled(uuid)') is null,'aucun RPC public ne permet de sonder l activation Junior par UUID');
select ok(to_regprocedure('public.has_accepted_junior_community_rules()') is not null,'RPC règles Junior self-only existe');
select ok(to_regprocedure('public.has_accepted_junior_community_rules(uuid)') is null,'aucun RPC public ne permet de sonder les règles Junior par UUID');
select ok(to_regprocedure('public.sinjira_is_junior(uuid)') is null,'aucun RPC public ne permet de sonder la bande Junior par UUID');
select ok(
  not (select prosecdef from pg_proc where oid='public.sinjira_my_age_band()'::regprocedure)
  and (select prosecdef from pg_proc where oid='sinjira_v25_internal.sinjira_my_age_band()'::regprocedure),
  'wrapper public de bande self-only reste SECURITY INVOKER et son implémentation interne SECURITY DEFINER'
);
select ok(has_function_privilege('authenticated','public.sinjira_my_age_band()','EXECUTE'),'authenticated conserve le wrapper de bande self-only');
select ok(has_function_privilege('anon','public.sinjira_my_age_band()','EXECUTE'),'anon conserve le wrapper self-only requis par les RLS publiques');
select ok(not has_function_privilege('authenticated','private.sinjira_is_junior(uuid)','EXECUTE'),'auth: aucun EXECUTE sur le helper privé de bande Junior');
select ok(not has_function_privilege('authenticated','private.sinjira_junior_community_enabled(uuid)','EXECUTE'),'auth: aucun EXECUTE sur le helper privé d activation Junior');
select ok(not has_function_privilege('authenticated','private.has_accepted_junior_community_rules(uuid)','EXECUTE'),'auth: aucun EXECUTE sur le helper privé de règles Junior');

select ok(not has_table_privilege('authenticated','public.junior_community_posts','SELECT'),'auth: aucun SELECT direct sur publications Junior');
select ok(not has_table_privilege('authenticated','public.junior_community_posts','INSERT'),'auth: aucun INSERT direct sur publications Junior');
select ok(not has_table_privilege('authenticated','public.junior_community_comments','SELECT'),'auth: aucun SELECT direct sur commentaires Junior');
select ok(not has_table_privilege('authenticated','public.junior_community_comments','INSERT'),'auth: aucun INSERT direct sur commentaires Junior');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '71000000-0000-4000-8000-000000000001',
  'guardian-junior@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '36 years')::date::text,
    'date_of_birth',(current_date-interval '36 years')::date::text,
    'gender','Homme','sex','male','pseudo','Parent Junior','display_name','Parent Junior','residence_country','Canada'
  )
);
select is(public.sinjira_age_band('71000000-0000-4000-8000-000000000001'),'adult','le parent Junior est adulte');

insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('71000000-0000-4000-8000-000000000001','YOUTH-JUNIOR0001',now()+interval '1 day');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '72000000-0000-4000-8000-000000000011',
  'child-junior-11@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '11 years')::date::text,
    'date_of_birth',(current_date-interval '11 years')::date::text,
    'gender','Homme','sex','male','pseudo','Nom Réel Enfant Un','display_name','Nom Réel Enfant Un','residence_country','Canada',
    'guardian_code','YOUTH-JUNIOR0001'
  )
);

-- Le contrat n'autorise qu'un seul code parental ouvert par tuteur.
-- Le premier code est consommé à la création du premier enfant avant d'en créer un second.
insert into public.guardian_signup_invites(guardian_user_id,invite_code,expires_at)
values('71000000-0000-4000-8000-000000000001','YOUTH-JUNIOR0002',now()+interval '1 day');

insert into auth.users(id,email,raw_user_meta_data)
values(
  '73000000-0000-4000-8000-000000000012',
  'child-junior-12@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '12 years')::date::text,
    'date_of_birth',(current_date-interval '12 years')::date::text,
    'gender','Femme','sex','female','pseudo','Nom Réel Enfant Deux','display_name','Nom Réel Enfant Deux','residence_country','Canada',
    'guardian_code','YOUTH-JUNIOR0002'
  )
);

select is(public.sinjira_age_band('72000000-0000-4000-8000-000000000011'),'child','11 ans est dans la bande child');
select is(public.sinjira_age_band('73000000-0000-4000-8000-000000000012'),'child','12 ans est dans la bande child');

select set_config('request.jwt.claim.sub','71000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','71000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select is(
  (public.guardian_set_junior_community('72000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,
  true,
  'le parent active explicitement la Communauté Junior pour le premier enfant'
);
select is(
  (public.guardian_set_junior_community('73000000-0000-4000-8000-000000000012',true)->>'enabled')::boolean,
  true,
  'le parent active explicitement la Communauté Junior pour le second enfant'
);
select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(public.sinjira_junior_community_enabled(),'l accès Junior self-only est actif après consentement parental');

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok((public.junior_community_accept_rules()->>'ok')::boolean,'le premier enfant accepte les règles Junior');

select set_config('request.jwt.claim.sub','73000000-0000-4000-8000-000000000012',true);
select ok((public.junior_community_accept_rules()->>'ok')::boolean,'le second enfant accepte les règles Junior');

create temporary table junior_test_ids(name text primary key,id uuid);

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
insert into junior_test_ids(name,id)
select 'post1',(public.junior_community_create_post('J aime explorer les histoires de SINJIRA')->>'id')::uuid;
select ok((select id is not null from junior_test_ids where name='post1'),'le premier enfant crée une publication Junior');

select set_config('request.jwt.claim.sub','73000000-0000-4000-8000-000000000012',true);
select ok(public.junior_community_feed(30)::text like '%J aime explorer les histoires de SINJIRA%','le second enfant voit la publication du premier');
select ok(position('Nom Réel Enfant Un' in public.junior_community_feed(30)::text)=0,'le vrai pseudo/profil du premier enfant n est pas exposé');
select ok(position('72000000-0000-4000-8000-000000000011' in public.junior_community_feed(30)::text)=0,'l UUID auteur n est pas exposé au fil Junior');

insert into private.moderation_decisions(
  subject_user_id,network,target_type,target_id,action,policy_rule,statement_of_reasons,urgency
)
values(
  '72000000-0000-4000-8000-000000000011',
  'real',
  'post',
  (select id from junior_test_ids where name='post1'),
  'hide_content',
  'Règles Communauté Junior',
  'Test automatique : masquage humain réversible d une publication Junior signalée.',
  'standard'
);
select ok(position('J aime explorer les histoires de SINJIRA' in public.junior_community_feed(30)::text)=0,'une décision humaine hide_content masque la publication Junior');
update private.moderation_decisions
set status='reversed',reversed_at=now(),reversal_reason='Test automatique : décision renversée après révision humaine.'
where target_id=(select id from junior_test_ids where name='post1')
  and network='real' and target_type='post' and action='hide_content';
select ok(public.junior_community_feed(30)::text like '%J aime explorer les histoires de SINJIRA%','une décision renversée rend la publication Junior visible à nouveau');

insert into junior_test_ids(name,id)
select 'comment1',(public.junior_community_create_comment((select id from junior_test_ids where name='post1'),'Moi aussi, surtout les jeux!')->>'id')::uuid;
select ok((select id is not null from junior_test_ids where name='comment1'),'le second enfant peut commenter dans le fil Junior');

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(public.junior_community_feed(30)::text like '%Moi aussi, surtout les jeux!%','le commentaire Junior apparaît dans le fil');

select set_config('request.jwt.claim.sub','73000000-0000-4000-8000-000000000012',true);
insert into junior_test_ids(name,id)
select 'post-revoked-author',(public.junior_community_create_post('Publication à masquer si son auteur perd Junior')->>'id')::uuid;
select ok(
  (select id is not null from junior_test_ids where name='post-revoked-author'),
  'le second enfant crée une publication utilisée pour prouver la révocation auteur'
);

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(
  public.junior_community_feed(30)::text like '%Publication à masquer si son auteur perd Junior%',
  'la publication du second enfant est visible avant révocation de son accès Junior'
);

select set_config('request.jwt.claim.sub','71000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','71000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select is(
  (public.guardian_set_junior_community('73000000-0000-4000-8000-000000000012',false)->>'enabled')::boolean,
  false,
  'le parent retire l accès Junior de l auteur du commentaire'
);

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(
  position('Moi aussi, surtout les jeux!' in public.junior_community_feed(30)::text)=0,
  'le commentaire disparaît du fil dès que son auteur perd l accès Junior'
);
select ok(
  position('Publication à masquer si son auteur perd Junior' in public.junior_community_feed(30)::text)=0,
  'la publication disparaît du fil dès que son auteur perd l accès Junior'
);

select set_config('request.jwt.claim.sub','71000000-0000-4000-8000-000000000001',true);
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','71000000-0000-4000-8000-000000000001','aal','aal2')::text,
  true
);
select is(
  (public.guardian_set_junior_community('73000000-0000-4000-8000-000000000012',true)->>'enabled')::boolean,
  true,
  'le parent réactive explicitement l accès Junior de l auteur du commentaire'
);

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(
  public.junior_community_feed(30)::text like '%Moi aussi, surtout les jeux!%',
  'le commentaire redevient visible après réactivation explicite du même enfant'
);
select ok(
  public.junior_community_feed(30)::text like '%Publication à masquer si son auteur perd Junior%',
  'la publication redevient visible après réactivation explicite du même enfant'
);

select throws_ok(
  $$select public.junior_community_create_post('Ajoute-moi sur https://example.com')$$,
  'P0001',
  'SINJIRA_JUNIOR_EXTERNAL_CONTACT_FORBIDDEN',
  'un lien externe est refusé côté serveur'
);

select set_config('request.jwt.claim.sub','71000000-0000-4000-8000-000000000001',true);
select throws_ok(
  $$select public.junior_community_feed(30)$$,
  'P0001',
  'JUNIOR_COMMUNITY_11_12_ONLY',
  'un adulte ne peut pas lire le fil Junior'
);

select ok(
  not public.sinjira_can_social_interact(
    '72000000-0000-4000-8000-000000000011',
    '73000000-0000-4000-8000-000000000012'
  ),
  'la messagerie et les réseaux sociaux historiques restent fermés entre comptes child'
);

select is(
  (public.junior_guardian_summary('72000000-0000-4000-8000-000000000011')->>'content_visible_to_guardian')::boolean,
  false,
  'le résumé parent ne donne pas accès au contenu'
);

select is(
  (public.junior_guardian_summary('72000000-0000-4000-8000-000000000011')->>'private_messages_available')::boolean,
  false,
  'le résumé confirme qu aucune messagerie privée Junior n existe'
);

select set_config('request.jwt.claim.sub','73000000-0000-4000-8000-000000000012',true);
insert into junior_test_ids(name,id)
select 'post2',(public.junior_community_create_post('Une publication du deuxième enfant')->>'id')::uuid;
select ok((select id is not null from junior_test_ids where name='post2'),'le second enfant peut publier dans la même cohorte Junior');

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(
  (public.junior_community_report_content('post',(select id from junior_test_ids where name='post2'),'harassment','Test de signalement Junior',true)->>'blocked')::boolean,
  'le signalement Junior peut masquer immédiatement l auteur'
);
select ok(
  exists(
    select 1 from public.social_reports
    where reporter_user_id='72000000-0000-4000-8000-000000000011'
      and target_id=(select id from junior_test_ids where name='post2')
      and snapshot->>'source'='junior_community'
  ),
  'le signalement Junior rejoint le système de modération avec une source explicite'
);
select ok(
  position('Une publication du deuxième enfant' in public.junior_community_feed(30)::text)=0,
  'le contenu de la personne bloquée disparaît du fil'
);

select set_config('request.jwt.claim.sub','71000000-0000-4000-8000-000000000001',true);
select is(
  (public.guardian_set_junior_community('72000000-0000-4000-8000-000000000011',false)->>'enabled')::boolean,
  false,
  'le parent peut révoquer immédiatement la Communauté Junior'
);

select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(not public.sinjira_junior_community_enabled(),'la révocation parentale désactive immédiatement l état self-only');
select throws_ok(
  $revocation$select public.junior_community_feed(30)$revocation$,
  'P0001',
  'JUNIOR_GUARDIAN_CONSENT_REQUIRED',
  'après révocation le fil Junior est immédiatement refusé côté serveur'
);

select set_config('request.jwt.claim.sub','71000000-0000-4000-8000-000000000001',true);
select is(
  (public.guardian_set_junior_community('72000000-0000-4000-8000-000000000011',true)->>'enabled')::boolean,
  true,
  'le parent peut réactiver la Communauté Junior'
);
select set_config('request.jwt.claim.sub','72000000-0000-4000-8000-000000000011',true);
select ok(
  public.sinjira_junior_community_enabled() and public.has_accepted_junior_community_rules(),
  'la réactivation restaure l accès sans redemander des règles dont la version n a pas changé'
);

update public.account_safety_profiles
set date_of_birth=(current_date-interval '13 years')::date
where user_id='72000000-0000-4000-8000-000000000011';

select is(public.sinjira_age_band('72000000-0000-4000-8000-000000000011'),'youth','à 13 ans le compte quitte automatiquement la bande Junior');
select ok(not public.sinjira_junior_community_enabled(),'l activation Junior self-only devient automatiquement inactive à 13 ans');
select throws_ok(
  $$select public.junior_community_feed(30)$$,
  'P0001',
  'JUNIOR_COMMUNITY_11_12_ONLY',
  'à 13 ans le fil Junior n est plus accessible'
);

select * from finish();
rollback;

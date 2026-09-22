begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(38);

insert into auth.users(id,email,raw_user_meta_data)
values
(
  'f1000000-0000-4000-8000-000000000001',
  'catalog-family-youth@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '15 years')::date::text,
    'date_of_birth',(current_date-interval '15 years')::date::text,
    'gender','Autre','sex','other','pseudo','Famille jeunesse test',
    'display_name','Famille jeunesse test','residence_country','Canada'
  )
),
(
  'f2000000-0000-4000-8000-000000000002',
  'catalog-standard-member@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '30 years')::date::text,
    'date_of_birth',(current_date-interval '30 years')::date::text,
    'gender','Autre','sex','other','pseudo','Membre standard test',
    'display_name','Membre standard test','residence_country','Canada'
  )
),
(
  'f3000000-0000-4000-8000-000000000003',
  'catalog-family-child@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '15 years')::date::text,
    'date_of_birth',(current_date-interval '15 years')::date::text,
    'gender','Autre','sex','other','pseudo','Famille enfant test',
    'display_name','Famille enfant test','residence_country','Canada'
  )
),
(
  'f4000000-0000-4000-8000-000000000004',
  'catalog-guardian@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '40 years')::date::text,
    'date_of_birth',(current_date-interval '40 years')::date::text,
    'gender','Autre','sex','other','pseudo','Tuteur test',
    'display_name','Tuteur test','residence_country','Canada'
  )
);

update public.account_safety_profiles
set date_of_birth=(current_date-interval '12 years')::date,
    updated_at=now()
where user_id='f3000000-0000-4000-8000-000000000003';

insert into public.guardian_links(
  minor_user_id,guardian_user_id,status,guardian_role,can_view_contact_metadata,consented_at
)
values(
  'f3000000-0000-4000-8000-000000000003',
  'f4000000-0000-4000-8000-000000000004',
  'verified','parent',false,now()
);

insert into public.projects(
  id,slug,name,type,status,visibility,description,cover_url,public_path,play_path,
  allow_tester_requests,sort_order,child_access_status
)
values(
  'f8000000-0000-4000-8000-000000000008',
  'family-private-game',
  'Jeu privé famille',
  'game',
  'draft',
  'restricted',
  'Description interne non classée pour 11–12 ans',
  null,
  '/famille/projet-prive',
  '/famille/jeu-prive',
  false,
  999,
  'unreviewed'
);

insert into public.sinjira_novels(
  id,slug,title,subtitle,description,status,public_path,demo_path,comments_enabled,sort_order
)
values(
  'f7000000-0000-4000-8000-000000000007',
  'family-private-novel',
  'Roman privé famille',
  'Preuve famille',
  'Description interne non classée pour 11–12 ans',
  'draft',
  '/famille/roman-prive',
  '/famille/demo-prive',
  false,
  999
);

insert into public.products(id,slug,name,product_type,active)
values(
  'f6000000-0000-4000-8000-000000000006',
  'family-private-novel-product',
  'Produit privé famille',
  'novel',
  false
);

insert into private.sinjira_private_novel_assets(
  novel_id,product_slug,delivery_mode,storage_bucket,storage_path,download_name,total_pages,enabled
)
values(
  'f7000000-0000-4000-8000-000000000007',
  'family-private-novel-product',
  'storage',
  'private-test',
  'family/private-novel.pdf',
  'family-private-novel.pdf',
  321,
  true
);

select ok(
  to_regclass('private.sinjira_catalog_family_members') is not null,
  'le registre familial privé existe'
);
select is(
  (select count(*)::integer
   from information_schema.columns
   where table_schema='private'
     and table_name='sinjira_catalog_family_members'
     and column_name='email'),
  0,
  'aucun courriel n est stocké dans le registre familial'
);
select is(
  (select count(*)::integer
   from information_schema.columns
   where table_schema='private'
     and table_name='sinjira_catalog_family_members'
     and column_name='label'),
  0,
  'aucun libellé nominatif n est stocké dans le registre familial'
);
select ok(
  not has_table_privilege('authenticated','private.sinjira_catalog_family_members','SELECT'),
  'authenticated ne peut pas lire le registre familial privé'
);
select ok(
  not has_function_privilege(
    'authenticated',
    'public.set_sinjira_catalog_family_access_by_email(text,boolean)',
    'EXECUTE'
  ),
  'le navigateur ne peut pas provisionner un accès familial'
);
select ok(
  has_function_privilege(
    'service_role',
    'public.set_sinjira_catalog_family_access_by_email(text,boolean)',
    'EXECUTE'
  ),
  'service_role peut provisionner un accès familial'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('role','service_role','aal','aal2')::text,
  true
);
set local role service_role;

select lives_ok(
  $ select public.set_sinjira_catalog_family_access_by_email(
    'catalog-family-youth@example.test',true
  ) $,
  'service_role peut associer un compte familial par courriel sans conserver le courriel'
);
select lives_ok(
  $ select public.set_sinjira_catalog_family_access_by_email(
    'catalog-family-child@example.test',true
  ) $,
  'service_role peut associer un second compte familial'
);

reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f1000000-0000-4000-8000-000000000001',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;

select ok(
  public.is_sinjira_catalog_family_member('f1000000-0000-4000-8000-000000000001'),
  'le compte familial courant est reconnu'
);
select ok(
  public.sinjira_has_full_catalog_access('f1000000-0000-4000-8000-000000000001'),
  'le compte familial courant possède le catalogue complet'
);
select is(
  public.sinjira_my_catalog_access_mode(),
  'family',
  'le mode self-only distingue famille du propriétaire et du membre'
);
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  1,
  'un compte familial youth/adult voit les projets internes'
);
select is(
  (select count(*)::integer from public.sinjira_novels where slug='family-private-novel'),
  1,
  'un compte familial youth/adult voit les romans brouillons'
);
select is(
  (select count(*)::integer from public.products where slug='family-private-novel-product'),
  1,
  'un compte familial youth/adult voit les produits internes'
);
select is(
  sinjira_catalog_internal.project_access_rank(
    'f8000000-0000-4000-8000-000000000008',
    'f1000000-0000-4000-8000-000000000001'
  ),
  90,
  'le compte familial standard obtient un rang catalogue sans faux project_access'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-private-game'
      and (item->>'content_available')::boolean
  ),
  'le catalogue projet self-only contient la création privée pour un compte familial standard'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
      and (item->>'full_access')::boolean
      and item->>'access_source'='family'
  ),
  'le catalogue roman familial standard donne l intégrale configurée sans entitlement'
);
select ok(
  public.has_sinjira_product(
    'family-private-novel-product',
    'f1000000-0000-4000-8000-000000000001'
  ),
  'un compte familial youth/adult satisfait le droit produit sans faux entitlement'
);
select ok(
  not public.has_sinjira_product(
    'family-product-does-not-exist',
    'f1000000-0000-4000-8000-000000000001'
  ),
  'un compte familial ne valide jamais un slug produit inexistant'
);

reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f2000000-0000-4000-8000-000000000002',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;

select ok(
  not public.sinjira_has_full_catalog_access('f2000000-0000-4000-8000-000000000002'),
  'un membre standard ne reçoit pas le catalogue familial'
);
select is(
  public.sinjira_my_catalog_access_mode(),
  'member',
  'un membre standard reste en mode membre'
);
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  0,
  'un membre standard ne voit pas le projet interne'
);
select is(
  (select count(*)::integer from public.sinjira_novels where slug='family-private-novel'),
  0,
  'un membre standard ne voit pas le roman brouillon'
);
select is(
  (select count(*)::integer from public.products where slug='family-private-novel-product'),
  0,
  'un membre standard ne voit pas le produit interne sans achat ni droit'
);
select throws_ok(
  $$ select public.sinjira_my_project_catalog() $$,
  '42501',
  'CATALOG_ACCESS_REQUIRED',
  'un membre standard ne peut pas appeler le catalogue projet familial'
);
select is(
  (
    select count(*)::integer
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
  ),
  0,
  'un membre standard ne reçoit pas le roman brouillon via le RPC self-only'
);
select ok(
  not public.has_sinjira_product(
    'family-private-novel-product',
    'f2000000-0000-4000-8000-000000000002'
  ),
  'un membre standard sans achat ni entitlement ne satisfait pas le droit produit'
);

reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f3000000-0000-4000-8000-000000000003',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;

select is(
  public.sinjira_age_band('f3000000-0000-4000-8000-000000000003'),
  'child',
  'le compte familial de preuve est bien classé 11–12 ans'
);
select ok(
  public.is_sinjira_catalog_family_member('f3000000-0000-4000-8000-000000000003'),
  'le compte familial 11–12 reste reconnu comme famille'
);
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  0,
  'le rôle familial ne contourne pas la RLS child pour un projet privé non classé'
);
select is(
  sinjira_catalog_internal.project_access_rank(
    'f8000000-0000-4000-8000-000000000008',
    'f3000000-0000-4000-8000-000000000003'
  ),
  0,
  'le rang familial complet n est jamais accordé à 11–12 ans'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-private-game'
  ),
  'le compte familial 11–12 voit néanmoins la fiche de catalogue de la création'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-private-game'
      and (item->>'content_available')::boolean=false
      and item->>'play_path' is null
      and item->>'public_path' is null
      and item->>'description' like '%Contenu protégé%'
  ),
  'la fiche 11–12 non classée est minimisée et sans chemin ouvrable'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
  ),
  'le compte familial 11–12 voit la fiche du roman privé'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
      and (item->>'full_access')::boolean=false
      and item->>'access_source'='family_catalog'
  ),
  'la fiche roman familiale 11–12 ne donne jamais l intégrale privée'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
      and item->>'demo_path' is null
      and item->>'public_path' is null
      and item->>'total_pages' is null
  ),
  'le catalogue roman 11–12 masque les chemins de lecture et la taille de l intégrale'
);
select is(
  (select count(*)::integer from public.products where slug='family-private-novel-product'),
  0,
  'le rôle familial 11–12 ne contourne pas la frontière commerce produit'
);
select ok(
  not public.has_sinjira_product(
    'family-private-novel-product',
    'f3000000-0000-4000-8000-000000000003'
  ),
  'un compte familial 11–12 ne satisfait pas le droit produit non classé'
);

reset role;

select * from finish();
rollback;

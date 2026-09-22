begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(90);

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
values
(
  'f8000000-0000-4000-8000-000000000008',
  'family-private-game',
  'Jeu privé famille',
  'game',
  'active',
  'public',
  'Description publique de catalogue, accès jouable réservé au droit produit.',
  null,
  '/famille/projet-prive',
  '/famille/jeu-prive',
  false,
  999,
  'unreviewed'
),
(
  'f8000000-0000-4000-8000-000000000009',
  'family-free-account-project',
  'Création gratuite avec compte',
  'experience',
  'active',
  'account',
  'Contenu gratuit inclus avec un compte SINJIRA.',
  null,
  '/gratuit/creation-compte',
  null,
  false,
  998,
  'approved_11_12'
);

insert into public.extensions(
  id,project_id,title,description,status,is_public
)
values(
  'fd000000-0000-4000-8000-00000000000d',
  'f8000000-0000-4000-8000-000000000008',
  'Extension interne famille',
  'Extension SINJIRA non publiée.',
  'design',
  false
);

insert into public.sinjira_novels(
  id,slug,title,subtitle,description,status,cover_url,public_path,demo_path,comments_enabled,sort_order
)
values(
  'f7000000-0000-4000-8000-000000000007',
  'family-private-novel',
  'Roman privé famille',
  'Preuve famille',
  'Description interne non classée pour 11–12 ans',
  'draft',
  '/famille/couverture-roman-non-classee.webp',
  '/famille/roman-prive',
  '/famille/demo-prive',
  false,
  999
);

insert into public.products(id,slug,name,product_type,active)
values
(
  'f6000000-0000-4000-8000-000000000006',
  'family-private-novel-product',
  'Produit privé famille',
  'novel',
  false
),
(
  'fe000000-0000-4000-8000-00000000000e',
  'family-private-extension-product',
  'Extension privée achetable',
  'extension',
  false
);

update public.projects
set product_slug='family-private-novel-product'
where id='f8000000-0000-4000-8000-000000000008';

insert into public.projects(
  id,slug,name,type,status,visibility,description,cover_url,public_path,play_path,
  allow_tester_requests,sort_order,child_access_status,product_slug
)
values(
  'fb100000-0000-4000-8000-000000000011',
  'family-paid-draft-project',
  'Projet payant brouillon',
  'game',
  'draft',
  'account',
  'Brouillon interne qui ne doit pas être révélé par un achat.',
  null,
  '/famille/brouillon-payant',
  '/famille/brouillon-payant/jouer',
  false,
  996,
  'unreviewed',
  'family-private-novel-product'
);

insert into public.documents(
  id,project_id,title,description,document_type,version,status,access_level,
  external_url,sort_order,child_access_status
)
values(
  'fb200000-0000-4000-8000-000000000012',
  'fb100000-0000-4000-8000-000000000011',
  'Document brouillon payant',
  'Document approuvé mais parent encore en brouillon.',
  'document',
  '1.0',
  'approved',
  'account',
  '/famille/brouillon-payant/document.pdf',
  996,
  'blocked_11_12'
);

insert into public.projects(
  id,slug,name,type,status,visibility,description,cover_url,public_path,play_path,
  allow_tester_requests,sort_order,child_access_status,product_slug
)
values(
  'f9000000-0000-4000-8000-000000000009',
  'family-paid-child-reviewed',
  'Projet payant approuvé 11–12',
  'game',
  'active',
  'account',
  'Projet payant de preuve: approbation humaine et accès explicite ne suffisent pas à 11–12 ans.',
  null,
  '/famille/payant-enfant',
  '/famille/payant-enfant/jouer',
  false,
  997,
  'approved_11_12',
  'family-private-novel-product'
);

insert into public.documents(
  id,project_id,title,description,document_type,version,status,access_level,
  external_url,sort_order,child_access_status
)
values(
  'fa000000-0000-4000-8000-00000000000a',
  'f9000000-0000-4000-8000-000000000009',
  'Document payant approuvé 11–12',
  'Document de preuve qui doit rester fermé.',
  'document',
  '1.0',
  'approved',
  'account',
  '/famille/payant-enfant/document.pdf',
  997,
  'approved_11_12'
);

insert into public.project_access(user_id,project_id,access_level,granted_by,source)
values(
  'f3000000-0000-4000-8000-000000000003',
  'f9000000-0000-4000-8000-000000000009',
  'player',
  'f4000000-0000-4000-8000-000000000004',
  'migration'
);

insert into public.extensions(
  id,project_id,title,description,status,is_public,product_slug
)
values(
  'fc100000-0000-4000-8000-000000000011',
  'f8000000-0000-4000-8000-000000000008',
  'Extension produit en conception',
  'Extension liée au produit mais encore interne.',
  'design',
  false,
  'family-private-extension-product'
);

insert into public.extensions(
  id,project_id,title,description,status,is_public,product_slug
)
values(
  'ff000000-0000-4000-8000-00000000000f',
  'f8000000-0000-4000-8000-000000000008',
  'Extension privée achetable',
  'Extension SINJIRA privée liée à un produit réel.',
  'released',
  false,
  'family-private-extension-product'
);

insert into public.extensions(
  id,project_id,title,description,status,is_public,product_slug
)
values(
  'fc200000-0000-4000-8000-000000000012',
  'fb100000-0000-4000-8000-000000000011',
  'Extension publiée d un projet brouillon',
  'Même publiée, cette extension ne doit pas révéler son projet parent encore brouillon.',
  'released',
  true,
  'family-private-extension-product'
);

insert into public.orders(id,user_id,order_number,status,currency,total_cents)
values(
  'fb000000-0000-4000-8000-00000000000b',
  'f2000000-0000-4000-8000-000000000002',
  'TEST-FAMILY-PENDING-EXT-001',
  'pending','CAD',900
);
insert into public.order_items(order_id,product_id,quantity,unit_price_cents)
values(
  'fb000000-0000-4000-8000-00000000000b',
  'fe000000-0000-4000-8000-00000000000e',
  1,900
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

set local role anon;
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  0,
  'anon ne reçoit pas la ligne complète d un projet public lié à un produit'
);
select is(
  (select count(*)::integer from public.extensions where id='fc200000-0000-4000-8000-000000000012'),
  0,
  'anon ne voit pas une extension publiée dont le projet parent est encore brouillon'
);
reset role;

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
  not has_function_privilege('authenticated','public.sinjira_age_band(uuid)','EXECUTE'),
  'authenticated ne peut toujours pas sonder la bande âge d un UUID arbitraire'
);
select ok(
  has_function_privilege('authenticated','public.sinjira_my_age_band()','EXECUTE'),
  'authenticated conserve uniquement le helper âge self-only du compte courant'
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

select is(
  (
    select count(*)::integer
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public'
      and p.proname in (
        'is_sinjira_catalog_family_member',
        'sinjira_has_full_catalog_access',
        'sinjira_my_catalog_access_mode',
        'set_sinjira_catalog_family_access_by_email',
        'sinjira_my_project_catalog',
        'sinjira_my_extension_catalog',
        'sinjira_my_novel_catalog'
      )
      and p.prosecdef
  ),
  0,
  'les RPC publics famille restent SECURITY INVOKER'
);
select is(
  (
    select count(*)::integer
    from pg_proc p
    join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='sinjira_v25_internal'
      and p.proname in (
        'is_sinjira_catalog_family_member',
        'sinjira_has_full_catalog_access',
        'sinjira_my_catalog_access_mode',
        'set_sinjira_catalog_family_access_by_email',
        'sinjira_my_project_catalog',
        'sinjira_my_extension_catalog',
        'sinjira_my_novel_catalog'
      )
      and p.prosecdef
  ),
  7,
  'les sept implémentations privilégiées famille restent hors du schéma public'
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
  'un compte familial youth/adult voit aussi les projets publics liés à un produit'
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
select is(
  (select count(*)::integer from public.extensions where id='fd000000-0000-4000-8000-00000000000d'),
  1,
  'un compte familial youth/adult voit une extension interne du catalogue créateur'
);
select is(
  (select count(*)::integer from public.extensions where id='fc100000-0000-4000-8000-000000000011'),
  1,
  'la famille adult/youth voit aussi une extension produit encore en conception'
);
select is(
  (select count(*)::integer from public.extensions where id='fc200000-0000-4000-8000-000000000012'),
  1,
  'la famille adult/youth conserve la visibilité catalogue sur une extension de projet brouillon'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='fd000000-0000-4000-8000-00000000000d'
      and item->>'title'='Extension interne famille'
      and (item->>'content_available')::boolean
  ),
  'le catalogue extension self-only donne les métadonnées complètes à la famille 13+'
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

select is(
  jsonb_array_length(public.sinjira_my_product_rights()),
  0,
  'le catalogue famille ne fabrique aucun droit produit commercial'
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
  'un membre standard sans droit ne reçoit pas la ligne complète du projet public payant'
);
select is(
  (select count(*)::integer from public.projects where slug='family-free-account-project'),
  1,
  'un membre standard voit le contenu gratuit inclus avec son compte'
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
select is(
  (select count(*)::integer from public.extensions where id='fd000000-0000-4000-8000-00000000000d'),
  0,
  'un membre standard ne voit pas une extension interne non publique'
);
select is(
  (select count(*)::integer from public.extensions where id='fc200000-0000-4000-8000-000000000012'),
  0,
  'un membre standard ne voit pas une extension publique si le projet parent est brouillon'
);
select is(
  (
    select count(*)::integer
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='fd000000-0000-4000-8000-00000000000d'
  ),
  0,
  'le catalogue extension self-only ne révèle pas l extension interne au membre standard'
);
select is(
  (select count(*)::integer from public.extensions where id='ff000000-0000-4000-8000-00000000000f'),
  0,
  'une commande pending ne rend pas l extension privée visible au membre standard'
);
select is(
  (
    select count(*)::integer
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='ff000000-0000-4000-8000-00000000000f'
  ),
  0,
  'le RPC extension refuse une extension liée seulement à une commande pending'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-free-account-project'
      and item->>'access_source'='free'
  )
  and not exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-private-game'
  ),
  'le catalogue projet standard contient le gratuit mais masque le projet payant non acheté'
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

select is(
  jsonb_array_length(public.sinjira_my_product_rights()),
  0,
  'une commande pending n apparaît pas dans les droits produit du compte'
);

reset role;

insert into public.orders(id,user_id,order_number,status,currency,total_cents)
values(
  'fc000000-0000-4000-8000-00000000000c',
  'f2000000-0000-4000-8000-000000000002',
  'TEST-FAMILY-PAID-NOVEL-001',
  'paid','CAD',3200
);
insert into public.order_items(order_id,product_id,quantity,unit_price_cents)
values
(
  'fc000000-0000-4000-8000-00000000000c',
  'f6000000-0000-4000-8000-000000000006',
  1,3200
),
(
  'fc000000-0000-4000-8000-00000000000c',
  'fe000000-0000-4000-8000-00000000000e',
  1,900
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f2000000-0000-4000-8000-000000000002',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;

select is(
  (select count(*)::integer from public.products where slug='family-private-novel-product'),
  1,
  'une commande paid rend le produit acheté visible au membre standard'
);
select ok(
  public.has_sinjira_product(
    'family-private-novel-product',
    'f2000000-0000-4000-8000-000000000002'
  ),
  'une commande paid satisfait le droit produit sans entitlement artificiel'
);

select is(
  jsonb_array_length(public.sinjira_my_product_rights()),
  2,
  'les deux produits d une commande paid apparaissent dans les droits effectifs du compte'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_product_rights()) item
    where item->>'slug'='family-private-novel-product'
      and item->>'source'='paid_order'
  )
  and exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_product_rights()) item
    where item->>'slug'='family-private-extension-product'
      and item->>'source'='paid_order'
  ),
  'les droits issus d une commande paid sont identifiés sans exposer la commande'
);
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  1,
  'une commande paid rend le projet privé lié au produit visible au membre standard'
);
select is(
  (select count(*)::integer from public.projects where slug='family-paid-draft-project'),
  0,
  'un achat paid ne révèle jamais un projet encore en brouillon'
);
select is(
  (select count(*)::integer from public.documents where id='fb200000-0000-4000-8000-000000000012'),
  0,
  'un achat paid ne révèle pas le document approuvé d un projet encore en brouillon'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-private-game'
      and item->>'access_source'='product'
      and (item->>'content_available')::boolean
  ),
  'le catalogue projet reconnaît le projet acheté sans entitlement artificiel'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
      and (item->>'full_access')::boolean
      and item->>'access_source'='product'
  ),
  'un roman privé acheté par commande paid devient disponible dans le catalogue sans entitlement'
);
select is(
  (select count(*)::integer from public.extensions where id='fc100000-0000-4000-8000-000000000011'),
  0,
  'un achat ne révèle pas une extension encore en conception'
);
select is(
  (select count(*)::integer from public.extensions where id='fc200000-0000-4000-8000-000000000012'),
  0,
  'un achat paid ne révèle pas une extension publiée si son projet parent reste brouillon'
);
select is(
  (
    select count(*)::integer
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='fc200000-0000-4000-8000-000000000012'
  ),
  0,
  'le catalogue membre masque une extension achetée dont le projet parent est brouillon'
);
select is(
  (
    select count(*)::integer
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='fc100000-0000-4000-8000-000000000011'
  ),
  0,
  'le catalogue membre masque aussi l extension produit encore en conception'
);
select is(
  (select count(*)::integer from public.extensions where id='ff000000-0000-4000-8000-00000000000f'),
  1,
  'une commande paid rend l extension privée achetée visible au membre standard'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='ff000000-0000-4000-8000-00000000000f'
      and item->>'access_source'='product'
      and (item->>'content_available')::boolean
  ),
  'le catalogue extension reconnaît une commande paid sans entitlement artificiel'
);

reset role;

insert into public.project_access(user_id,project_id,access_level,granted_by,source)
values(
  'f2000000-0000-4000-8000-000000000002',
  'fb100000-0000-4000-8000-000000000011',
  'player',
  'f4000000-0000-4000-8000-000000000004',
  'migration'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f2000000-0000-4000-8000-000000000002',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;
select is(
  (select count(*)::integer from public.projects where slug='family-paid-draft-project'),
  1,
  'un accès player explicite peut ouvrir le projet brouillon sans dépendre de l achat'
);
select is(
  (select count(*)::integer from public.documents where id='fb200000-0000-4000-8000-000000000012'),
  1,
  'un accès player explicite conserve l accès au document du brouillon'
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
  sinjira_catalog_internal.project_access_rank(
    'f9000000-0000-4000-8000-000000000009',
    'f3000000-0000-4000-8000-000000000003'
  ),
  20,
  'un accès player explicite reste un rang technique et ne devient pas un droit produit enfant'
);
select is(
  (select count(*)::integer from public.projects where slug='family-paid-child-reviewed'),
  0,
  'un compte 11–12 ne lit pas un projet payant même approuvé et avec project_access player'
);
select ok(
  not public.sinjira_child_project_available('f9000000-0000-4000-8000-000000000009'),
  'le helper 11–12 refuse aussi le projet payant approuvé avec accès explicite'
);
select is(
  (select count(*)::integer from public.documents where id='fa000000-0000-4000-8000-00000000000a'),
  0,
  'un compte 11–12 ne lit pas le document d un projet payant malgré un rang player'
);
select ok(
  not public.sinjira_child_document_available('fa000000-0000-4000-8000-00000000000a'),
  'le helper document 11–12 refuse le contenu payant malgré double approbation et accès player'
);
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  0,
  'le rôle familial ne contourne pas la RLS child pour un projet privé non classé'
);
select is(
  (select count(*)::integer from public.extensions where id='fd000000-0000-4000-8000-00000000000d'),
  0,
  'le compte familial 11–12 ne reçoit pas une extension interne non classée'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='fd000000-0000-4000-8000-00000000000d'
      and item->>'title'='Extension SINJIRA™ protégée'
      and item->>'status'='protected'
      and (item->>'content_available')::boolean=false
  ),
  'le compte familial 11–12 voit une fiche extension minimisée sans contenu ouvrable'
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
      and item->>'cover_url' is null
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
      and item->>'cover_url' is null
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

insert into public.orders(id,user_id,order_number,status,currency,total_cents)
values(
  'fd100000-0000-4000-8000-000000000013',
  'f3000000-0000-4000-8000-000000000003',
  'TEST-CHILD-PAID-PRODUCT-001',
  'paid','CAD',900
);
insert into public.order_items(order_id,product_id,quantity,unit_price_cents)
values(
  'fd100000-0000-4000-8000-000000000013',
  'fe000000-0000-4000-8000-00000000000e',
  1,900
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f3000000-0000-4000-8000-000000000003',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;

select ok(
  public.has_sinjira_product(
    'family-private-extension-product',
    'f3000000-0000-4000-8000-000000000003'
  ),
  'une commande paid enfant reste un droit comptable réel'
);
select is(
  (select count(*)::integer from public.products where slug='family-private-extension-product'),
  0,
  'une commande paid enfant ne révèle pas les métadonnées du produit à 11–12'
);

reset role;

insert into public.user_entitlements(user_id,product_id,source)
values
(
  'f3000000-0000-4000-8000-000000000003',
  'f6000000-0000-4000-8000-000000000006',
  'physical_activation'
),
(
  'f3000000-0000-4000-8000-000000000003',
  'fe000000-0000-4000-8000-00000000000e',
  'physical_activation'
)
on conflict (user_id,product_id) do nothing;

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','f3000000-0000-4000-8000-000000000003',
    'role','authenticated','aal','aal1'
  )::text,
  true
);
set local role authenticated;

select ok(
  public.has_sinjira_product(
    'family-private-novel-product',
    'f3000000-0000-4000-8000-000000000003'
  ),
  'un droit produit réel peut exister comptablement pour un compte 11–12'
);
select is(
  (select count(*)::integer from public.products where slug='family-private-novel-product'),
  0,
  'un entitlement enfant ne révèle pas les métadonnées du produit à 11–12'
);

select is(
  jsonb_array_length(public.sinjira_my_product_rights()),
  0,
  'les droits commerciaux restent masqués côté navigateur à 11–12 malgré des entitlements réels'
);
select is(
  (select count(*)::integer from public.projects where slug='family-private-game'),
  0,
  'un droit produit réel ne rouvre pas la ligne projet au compte 11–12'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_project_catalog()) item
    where item->>'slug'='family-private-game'
      and (item->>'content_available')::boolean=false
      and item->>'play_path' is null
  ),
  'le catalogue familial garde le projet acheté non ouvrable à 11–12'
);
select is(
  (select count(*)::integer from public.extensions where id='ff000000-0000-4000-8000-00000000000f'),
  0,
  'un droit produit réel ne rouvre pas l extension privée au compte 11–12'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_extension_catalog()) item
    where item->>'id'='ff000000-0000-4000-8000-00000000000f'
      and (item->>'content_available')::boolean=false
      and item->>'status'='protected'
  ),
  'le catalogue familial garde l extension achetée minimisée à 11–12'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='family-private-novel'
      and (item->>'full_access')::boolean=false
      and item->>'demo_path' is null
      and item->>'public_path' is null
  ),
  'le droit produit réel ne donne jamais l intégrale du roman au compte 11–12'
);

reset role;

select * from finish();
rollback;

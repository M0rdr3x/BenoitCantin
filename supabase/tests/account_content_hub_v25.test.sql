begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(52);

insert into auth.users(id,email,raw_user_meta_data)
values
(
  'b1000000-0000-4000-8000-000000000001',
  'creator-test@example.test',
  jsonb_build_object('birth_date',(current_date-interval '40 years')::date::text,'date_of_birth',(current_date-interval '40 years')::date::text,'gender','Homme','sex','male','pseudo','Créateur test','display_name','Créateur test','residence_country','Canada')
),
(
  'b2000000-0000-4000-8000-000000000002',
  'content-hub-member@example.test',
  jsonb_build_object('birth_date',(current_date-interval '30 years')::date::text,'date_of_birth',(current_date-interval '30 years')::date::text,'gender','Femme','sex','female','pseudo','Membre test','display_name','Membre test','residence_country','Canada')
);

update public.profiles
set pseudo='Pseudo public test',
    display_name='Nom privé à ne jamais exposer'
where user_id='b2000000-0000-4000-8000-000000000002';

select ok(
  exists(
    select 1
    from public.social_profiles
    where user_id='b2000000-0000-4000-8000-000000000002'
      and pseudo='Pseudo public test'
      and display_name='Pseudo public test'
      and display_name<>'Nom privé à ne jamais exposer'
  ),
  'le profil social ne reçoit jamais le nom affiché privé du compte'
);

insert into public.internal_admin_users(user_id,role)
values('b1000000-0000-4000-8000-000000000001','owner')
on conflict(user_id) do update set role='owner';

insert into public.projects(
  id,slug,name,type,status,visibility,description,allow_tester_requests,sort_order
)
values(
  'b8000000-0000-4000-8000-000000000008',
  'content-hub-owner-private-project',
  'Projet interne créateur',
  'game',
  'draft',
  'restricted',
  'Projet interne de preuve owner-only',
  false,
  998
);

select ok(
  exists(
    select 1
    from pg_policies
    where schemaname='public'
      and tablename='projects'
      and policyname='projects_owner_catalog_read_v25'
      and qual ilike '%is_sinjira_owner%'
  ),
  'la policy projets owner-only V25 existe'
);

select ok(has_table_privilege('authenticated','public.projects','SELECT'),'authenticated peut lire projects sous RLS');
select ok(has_table_privilege('anon','public.projects','SELECT'),'anon peut lire les projets publics sous RLS');
select ok(not has_table_privilege('authenticated','public.projects','INSERT'),'authenticated ne peut pas créer un projet directement');
select ok(has_table_privilege('authenticated','public.project_access','SELECT'),'authenticated peut relire son project_access sous RLS');
select ok(not has_table_privilege('authenticated','public.project_access','INSERT'),'authenticated ne peut pas s auto-attribuer project_access par INSERT');
select ok(not has_table_privilege('anon','public.project_access','SELECT'),'anon ne peut pas lire project_access');
select ok(has_table_privilege('authenticated','public.access_requests','SELECT'),'authenticated peut relire ses demandes sous RLS');
select ok(has_table_privilege('authenticated','public.access_requests','INSERT'),'authenticated peut créer une demande sous RLS');
select ok(not has_table_privilege('authenticated','public.access_requests','UPDATE'),'authenticated ne peut pas décider une demande directement');
select ok(not has_table_privilege('authenticated','public.access_requests','DELETE'),'authenticated ne peut pas supprimer arbitrairement une demande');
select ok(has_table_privilege('authenticated','public.documents','SELECT'),'authenticated peut lire les documents autorisés sous RLS');
select ok(has_table_privilege('anon','public.documents','SELECT'),'anon peut lire uniquement les documents publics autorisés par RLS');
select ok(has_table_privilege('authenticated','public.playtests','SELECT'),'authenticated peut lire les playtests autorisés sous RLS');
select ok(has_table_privilege('authenticated','public.playtest_participants','SELECT'),'authenticated peut relire ses candidatures playtest');
select ok(has_table_privilege('authenticated','public.playtest_participants','INSERT'),'authenticated peut candidater à un playtest');
select ok(not has_table_privilege('authenticated','public.playtest_participants','UPDATE'),'authenticated ne peut pas approuver une candidature directement');
select ok(not has_table_privilege('authenticated','public.playtest_participants','DELETE'),'authenticated ne peut pas supprimer arbitrairement une candidature');

select ok(
  exists(
    select 1
    from pg_policies
    where schemaname='public'
      and tablename='access_requests'
      and policyname='requests own insert'
      and lower(coalesce(with_check,'')) like '%auth.uid%'
      and lower(coalesce(with_check,'')) like '%user_id%'
      and lower(coalesce(with_check,'')) like '%sinjira_my_age_band%'
      and lower(coalesce(with_check,'')) like '%adult%'
      and lower(coalesce(with_check,'')) like '%youth%'
      and lower(coalesce(with_check,'')) like '%pending%'
  ),
  'INSERT access_requests reste self-only, adulte/youth et pending'
);
select ok(
  exists(
    select 1
    from pg_policies
    where schemaname='public'
      and tablename='playtest_participants'
      and policyname='participants own apply'
      and lower(coalesce(with_check,'')) like '%auth.uid%'
      and lower(coalesce(with_check,'')) like '%user_id%'
      and lower(coalesce(with_check,'')) like '%sinjira_my_age_band%'
      and lower(coalesce(with_check,'')) like '%adult%'
      and lower(coalesce(with_check,'')) like '%youth%'
      and lower(coalesce(with_check,'')) like '%applied%'
  ),
  'INSERT playtest_participants reste self-only, adulte/youth et applied'
);

select ok(has_table_privilege('authenticated','public.extensions','SELECT'),'authenticated peut lire les extensions publiées sous RLS');
select ok(has_table_privilege('anon','public.extensions','SELECT'),'anon peut lire les extensions publiques sous RLS');

select ok(to_regnamespace('sinjira_catalog_internal') is not null,'schéma interne catalogue existe');
select ok(
  exists(
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='public' and p.proname='project_access_rank' and not p.prosecdef
  ),
  'project_access_rank public est un wrapper SECURITY INVOKER'
);
select ok(not has_function_privilege('authenticated','public.project_access_rank(uuid,uuid)','EXECUTE'),'authenticated ne peut pas sonder directement le rang projet');
select ok(not has_function_privilege('anon','public.project_access_rank(uuid,uuid)','EXECUTE'),'anon ne peut pas sonder directement le rang projet');
select ok(has_function_privilege('service_role','public.project_access_rank(uuid,uuid)','EXECUTE'),'service_role conserve le wrapper public du rang projet');
select ok(
  exists(
    select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='sinjira_catalog_internal' and p.proname='project_access_rank' and p.prosecdef
  ),
  'implémentation project_access_rank privilégiée déplacée hors public'
);
select ok(has_function_privilege('authenticated','sinjira_catalog_internal.project_access_rank(uuid,uuid)','EXECUTE'),'authenticated peut évaluer le helper interne via RLS');
select ok(has_function_privilege('anon','sinjira_catalog_internal.project_access_rank(uuid,uuid)','EXECUTE'),'anon peut évaluer le helper interne via RLS public');
select is(
  (
    select count(*)::integer
    from pg_policies
    where schemaname='public'
      and tablename in ('projects','documents')
      and lower(coalesce(qual,'')) like '%sinjira_catalog_internal.project_access_rank%'
  ),
  2,
  'les policies projects/documents conservent l OID du helper déplacé'
);

insert into public.sinjira_novels(id,slug,title,status,sort_order)
values('b3000000-0000-4000-8000-000000000003','content-hub-draft','Roman privé créateur','draft',999);

insert into public.products(id,slug,name,product_type,active)
values
('b4000000-0000-4000-8000-000000000004','content-entitled','Produit attribué','novel',false),
('b5000000-0000-4000-8000-000000000005','content-ordered','Produit acheté','game',false),
('b6000000-0000-4000-8000-000000000006','content-private','Produit privé créateur','digital',false),
('ba000000-0000-4000-8000-00000000000a','content-pending','Produit commande non payée','digital',false);

insert into public.user_entitlements(user_id,product_id,source)
values('b2000000-0000-4000-8000-000000000002','b4000000-0000-4000-8000-000000000004','test');

insert into public.orders(id,user_id,order_number,status,currency,total_cents)
values
('b7000000-0000-4000-8000-000000000007','b2000000-0000-4000-8000-000000000002','TEST-CONTENT-HUB-001','paid','CAD',2500),
('bb000000-0000-4000-8000-00000000000b','b2000000-0000-4000-8000-000000000002','TEST-CONTENT-HUB-PENDING','pending','CAD',1800);

insert into public.order_items(order_id,product_id,quantity,unit_price_cents)
values
('b7000000-0000-4000-8000-000000000007','b5000000-0000-4000-8000-000000000005',1,2500),
('bb000000-0000-4000-8000-00000000000b','ba000000-0000-4000-8000-00000000000a',1,1800);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','b2000000-0000-4000-8000-000000000002','role','authenticated','aal','aal1')::text,
  true
);
set local role authenticated;

select is(
  sinjira_catalog_internal.project_access_rank(
    'b8000000-0000-4000-8000-000000000008',
    'b1000000-0000-4000-8000-000000000001'
  ),
  0,
  'un membre ne peut pas sonder le rang projet d’un autre compte'
);

select ok(
  not public.is_sinjira_owner('b2000000-0000-4000-8000-000000000002'),
  'un membre standard n est pas traité comme créateur'
);
select is(
  (select count(*)::integer from public.sinjira_novels where slug='content-hub-draft'),
  0,
  'un membre ne voit pas un roman brouillon créateur'
);
select is(
  (select count(*)::integer from public.projects where slug='content-hub-owner-private-project'),
  0,
  'un membre ne voit pas un projet interne créateur'
);
select is(
  (select count(*)::integer from public.products where slug='content-entitled'),
  1,
  'un membre voit encore un produit inactif lié à son entitlement'
);
select is(
  (select count(*)::integer from public.products where slug='content-ordered'),
  1,
  'un membre voit encore un produit inactif présent dans sa propre commande'
);
select is(
  (select count(*)::integer from public.products where slug='content-private'),
  0,
  'un membre ne voit pas un produit inactif sans droit ni achat'
);
select is(
  (select count(*)::integer from public.products where slug='content-pending'),
  0,
  'une commande pending ne rend pas le produit privé visible comme achat'
);
select ok(
  public.has_sinjira_product(
    'content-entitled',
    'b2000000-0000-4000-8000-000000000002'
  ),
  'un entitlement réel conserve le droit produit même si le produit devient inactif'
);
select ok(
  public.has_sinjira_product(
    'content-ordered',
    'b2000000-0000-4000-8000-000000000002'
  ),
  'une commande paid conserve le droit produit même si le produit devient inactif'
);
select ok(
  not public.has_sinjira_product(
    'content-pending',
    'b2000000-0000-4000-8000-000000000002'
  ),
  'une commande pending ne satisfait jamais le droit produit'
);

reset role;

select ok(
  has_function_privilege(
    'service_role',
    'sinjira_catalog_internal.project_access_rank(uuid,uuid)',
    'EXECUTE'
  ),
  'service_role conserve EXECUTE sur le helper interne de rang projet'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','b2000000-0000-4000-8000-000000000002','role','service_role','aal','aal2')::text,
  true
);
set local role service_role;
select is(
  sinjira_catalog_internal.project_access_rank(
    'b8000000-0000-4000-8000-000000000008',
    'b1000000-0000-4000-8000-000000000001'
  ),
  100,
  'service_role peut encore calculer le rang d’un UUID explicite différent du compte JWT'
);
reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','b1000000-0000-4000-8000-000000000001','role','authenticated','aal','aal1')::text,
  true
);
set local role authenticated;

select is(
  sinjira_catalog_internal.project_access_rank(
    'b8000000-0000-4000-8000-000000000008',
    'b1000000-0000-4000-8000-000000000001'
  ),
  100,
  'le compte courant conserve son propre rang admin via le helper interne'
);

select ok(
  public.is_sinjira_owner('b1000000-0000-4000-8000-000000000001'),
  'le compte propriétaire est reconnu comme créateur'
);
select is(
  (select count(*)::integer from public.sinjira_novels where slug='content-hub-draft'),
  1,
  'le créateur voit son roman brouillon'
);
select is(
  (select count(*)::integer from public.projects where slug='content-hub-owner-private-project'),
  1,
  'le créateur voit son projet interne sans faux achat'
);
select is(
  (select count(*)::integer from public.products where slug='content-private'),
  1,
  'le créateur voit les produits internes inactifs sans créer un achat'
);
select is(
  jsonb_array_length(public.sinjira_my_product_rights()),
  0,
  'le catalogue complet du créateur ne fabrique aucun droit produit commercial'
);

reset role;

select ok(
  exists(
    select 1
    from public.sinjira_novels
    where slug='le-sang-du-sauveur'
      and public_path='/projets/sinjira/romans/le-sang-du-sauveur/index.html'
  ),
  'Le Sang du Sauveur est présent dans le catalogue roman canonique'
);

select * from finish();
rollback;

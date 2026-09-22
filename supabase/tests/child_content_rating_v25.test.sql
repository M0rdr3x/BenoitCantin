begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(26);

select has_column('public','projects','child_access_status','projects possède le classement 11–12');
select has_column('public','projects','child_access_reviewed_by','projects conserve le réviseur humain');
select has_column('public','documents','child_access_status','documents possède le classement 11–12');
select has_column('public','documents','child_access_reviewed_by','documents conserve le réviseur humain');
select ok(to_regprocedure('public.sinjira_child_project_available(uuid)') is not null,'helper disponibilité projet 11–12 existe');
select ok(to_regprocedure('public.sinjira_child_document_available(uuid)') is not null,'helper disponibilité document 11–12 existe');

insert into public.projects(id,slug,name,type,status,visibility,description,allow_tester_requests,sort_order)
values
('91000000-0000-4000-8000-000000000001','child-rating-unreviewed','Non révisé','game','active','account','test',false,901),
('91000000-0000-4000-8000-000000000002','child-rating-approved','Approuvé','game','active','account','test',false,902),
('91000000-0000-4000-8000-000000000003','child-rating-restricted','Restreint','game','active','restricted','test',false,903),
('91000000-0000-4000-8000-000000000004','child-rating-draft','Brouillon','game','draft','account','test',false,904);

select is((select child_access_status from public.projects where id='91000000-0000-4000-8000-000000000001'),'unreviewed','un projet existant/nouveau reste fermé par défaut');
select ok(not public.sinjira_child_project_available('91000000-0000-4000-8000-000000000001'),'un projet non révisé est indisponible 11–12');

update public.projects set child_access_status='approved_11_12' where id in (
'91000000-0000-4000-8000-000000000002','91000000-0000-4000-8000-000000000003','91000000-0000-4000-8000-000000000004');

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','93000000-0000-4000-8000-000000000001','role','authenticated','aal','aal1')::text,
  true
);
set local role authenticated;
select ok(public.sinjira_child_project_available('91000000-0000-4000-8000-000000000002'),'un projet account actif explicitement approuvé devient disponible');
reset role;

select set_config('request.jwt.claims',jsonb_build_object('role','anon')::text,true);
set local role anon;
select ok(
  not public.sinjira_child_project_available('91000000-0000-4000-8000-000000000002'),
  'anon ne peut pas sonder un projet account approuvé 11–12 par UUID'
);
reset role;
select ok(not public.sinjira_child_project_available('91000000-0000-4000-8000-000000000003'),'un projet restricted ne devient pas Junior par simple classement');
select ok(not public.sinjira_child_project_available('91000000-0000-4000-8000-000000000004'),'un brouillon approuvé reste indisponible');

insert into public.documents(id,project_id,title,description,document_type,version,status,access_level,external_url,sort_order)
values
('92000000-0000-4000-8000-000000000001','91000000-0000-4000-8000-000000000002','Document non révisé','test','document','1.0','approved','account','/test-child-unreviewed.pdf',901),
('92000000-0000-4000-8000-000000000002','91000000-0000-4000-8000-000000000002','Document approuvé','test','document','1.0','approved','account','/test-child-approved.pdf',902);

insert into public.products(id,slug,name,product_type,active)
values(
  '94000000-0000-4000-8000-000000000001',
  'child-rating-paid-product',
  'Produit payant test 11–12',
  'game',
  true
);
insert into public.projects(
  id,slug,name,type,status,visibility,description,allow_tester_requests,sort_order,
  child_access_status,product_slug
)
values(
  '91000000-0000-4000-8000-000000000005',
  'child-rating-paid-approved',
  'Payant approuvé 11–12',
  'game',
  'active',
  'account',
  'test payant',
  false,
  905,
  'approved_11_12',
  'child-rating-paid-product'
);
insert into public.documents(
  id,project_id,title,description,document_type,version,status,access_level,
  external_url,sort_order,child_access_status
)
values(
  '92000000-0000-4000-8000-000000000003',
  '91000000-0000-4000-8000-000000000005',
  'Document payant approuvé',
  'test',
  'document',
  '1.0',
  'approved',
  'account',
  '/test-child-paid-approved.pdf',
  903,
  'approved_11_12'
);

select is((select child_access_status from public.documents where id='92000000-0000-4000-8000-000000000001'),'unreviewed','un document reste fermé par défaut');
select ok(not public.sinjira_child_document_available('92000000-0000-4000-8000-000000000001'),'un document non révisé est indisponible 11–12');
update public.documents set child_access_status='approved_11_12' where id='92000000-0000-4000-8000-000000000002';
select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','93000000-0000-4000-8000-000000000001','role','authenticated','aal','aal1')::text,
  true
);
set local role authenticated;
select ok(public.sinjira_child_document_available('92000000-0000-4000-8000-000000000002'),'document + projet doublement approuvés deviennent disponibles');
select ok(
  not public.sinjira_child_project_available('91000000-0000-4000-8000-000000000005'),
  'un projet payant reste indisponible 11–12 même avec approbation humaine'
);
select ok(
  not public.sinjira_child_document_available('92000000-0000-4000-8000-000000000003'),
  'un document d un projet payant reste indisponible 11–12 même doublement approuvé'
);
reset role;

select set_config('request.jwt.claims',jsonb_build_object('role','anon')::text,true);
set local role anon;
select ok(
  not public.sinjira_child_document_available('92000000-0000-4000-8000-000000000002'),
  'anon ne peut pas sonder un document account approuvé 11–12 par UUID'
);
reset role;
update public.projects set child_access_status='blocked_11_12' where id='91000000-0000-4000-8000-000000000002';
select ok(not public.sinjira_child_document_available('92000000-0000-4000-8000-000000000002'),'bloquer ensuite le projet referme immédiatement le document');

select is(
  (
    select string_agg(policyname, ', ' order by policyname)
    from pg_policies
    where schemaname='public'
      and tablename='projects'
      and cmd='SELECT'
  ),
  'projects readable when accessible, projects_family_catalog_read_v25, projects_owner_catalog_read_v25, projects_purchased_read_v25'::text,
  'une seule politique générale projets reste active; les exceptions owner, famille et achat V25 restent explicitement bornées'
);
select is(
  (select count(*) from pg_policies where schemaname='public' and tablename='documents' and cmd='SELECT'),
  1::bigint,
  'une seule politique SELECT documents reste active pour éviter un OR permissif'
);
select ok((select qual ilike '%sinjira_my_age_band%' and qual ilike '%adult%' and qual ilike '%youth%' and qual ilike '%child%' from pg_policies where schemaname='public' and tablename='projects' and policyname='projects readable when accessible'),'RLS projets sépare standard, child et bandes restreintes');
select ok((select qual ilike '%sinjira_my_age_band%' and qual ilike '%adult%' and qual ilike '%youth%' and qual ilike '%child%' from pg_policies where schemaname='public' and tablename='documents' and policyname='approved documents visible by access'),'RLS documents sépare standard, child et bandes restreintes');
select ok((select qual ilike '%child_access_status%' from pg_policies where schemaname='public' and tablename='projects' and policyname='projects readable when accessible'),'RLS projets contient le classement 11–12');
select ok((
  select qual ilike '%sinjira_my_age_band%'
     and qual ilike '%adult%'
     and qual ilike '%youth%'
     and qual not ilike '%child%'
     and qual ilike '%has_sinjira_product%'
  from pg_policies
  where schemaname='public'
    and tablename='projects'
    and policyname='projects_purchased_read_v25'
),'la policy projet acheté reste interdite aux comptes 11–12 et exige un droit produit réel');
select ok((select qual ilike '%sinjira_child_document_available%' from pg_policies where schemaname='public' and tablename='documents' and policyname='approved documents visible by access'),'RLS documents impose la double approbation');

select * from finish();
rollback;

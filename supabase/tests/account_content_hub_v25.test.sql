begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(12);

insert into auth.users(id,email,raw_user_meta_data)
values
(
  'b1000000-0000-4000-8000-000000000001',
  'kingtyrano@gmail.com',
  jsonb_build_object('birth_date',(current_date-interval '40 years')::date::text,'date_of_birth',(current_date-interval '40 years')::date::text,'gender','Homme','sex','male','pseudo','Créateur test','display_name','Créateur test','residence_country','Canada')
),
(
  'b2000000-0000-4000-8000-000000000002',
  'content-hub-member@example.test',
  jsonb_build_object('birth_date',(current_date-interval '30 years')::date::text,'date_of_birth',(current_date-interval '30 years')::date::text,'gender','Femme','sex','female','pseudo','Membre test','display_name','Membre test','residence_country','Canada')
);

insert into public.internal_admin_users(user_id,role)
values('b1000000-0000-4000-8000-000000000001','owner')
on conflict(user_id) do update set role='owner';

insert into public.projects(
  id,slug,name,type,status,visibility,sort_order,allow_tester_requests
)
values(
  'b8000000-0000-4000-8000-000000000008',
  'content-hub-owner-private-project',
  'Projet interne créateur',
  'game',
  'draft',
  'restricted',
  998,
  false
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

insert into public.sinjira_novels(id,slug,title,status,sort_order)
values('b3000000-0000-4000-8000-000000000003','content-hub-draft','Roman privé créateur','draft',999);

insert into public.products(id,slug,name,product_type,active)
values
('b4000000-0000-4000-8000-000000000004','content-entitled','Produit attribué','novel',false),
('b5000000-0000-4000-8000-000000000005','content-ordered','Produit acheté','game',false),
('b6000000-0000-4000-8000-000000000006','content-private','Produit privé créateur','digital',false);

insert into public.user_entitlements(user_id,product_id,source)
values('b2000000-0000-4000-8000-000000000002','b4000000-0000-4000-8000-000000000004','test');

insert into public.orders(id,user_id,order_number,status,currency,total_cents)
values('b7000000-0000-4000-8000-000000000007','b2000000-0000-4000-8000-000000000002','TEST-CONTENT-HUB-001','paid','CAD',2500);

insert into public.order_items(order_id,product_id,quantity,unit_price_cents)
values('b7000000-0000-4000-8000-000000000007','b5000000-0000-4000-8000-000000000005',1,2500);

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','b2000000-0000-4000-8000-000000000002','role','authenticated','aal','aal1')::text,
  true
);
set local role authenticated;

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

reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object('sub','b1000000-0000-4000-8000-000000000001','role','authenticated','aal','aal1')::text,
  true
);
set local role authenticated;

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

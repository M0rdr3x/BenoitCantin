begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,extensions;

select plan(13);

select ok(
  to_regprocedure('public.sinjira_my_novel_catalog()') is not null,
  'le catalogue roman self-only existe'
);
select ok(
  not has_function_privilege('anon','public.sinjira_my_novel_catalog()','EXECUTE'),
  'anon ne peut pas lire le catalogue privé du compte'
);
select ok(
  has_function_privilege('authenticated','public.sinjira_my_novel_catalog()','EXECUTE'),
  'authenticated peut lire son propre catalogue roman'
);
select ok(
  not has_function_privilege('authenticated','public.sinjira_private_novel_asset_for_delivery(text)','EXECUTE'),
  'le navigateur membre ne peut pas lire les métadonnées de livraison privée'
);
select ok(
  exists(
    select 1
    from pg_class c
    join pg_namespace n on n.oid=c.relnamespace
    where n.nspname='private'
      and c.relname='sinjira_private_novel_assets'
      and c.relrowsecurity=true
  ),
  'RLS est activée sur le registre privé des actifs romans'
);

select ok(
  not has_table_privilege('authenticated','private.sinjira_private_novel_assets','SELECT'),
  'la table des actifs privés reste invisible au navigateur'
);

insert into auth.users(id,email,raw_user_meta_data)
values
(
  'c1000000-0000-4000-8000-000000000001',
  'kingtyrano@gmail.com',
  jsonb_build_object(
    'birth_date',(current_date-interval '42 years')::date::text,
    'date_of_birth',(current_date-interval '42 years')::date::text,
    'gender','Homme','sex','male',
    'pseudo','Créateur Roman',
    'display_name','Créateur Roman',
    'residence_country','Canada'
  )
),
(
  'c2000000-0000-4000-8000-000000000002',
  'private-novel-member@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '30 years')::date::text,
    'date_of_birth',(current_date-interval '30 years')::date::text,
    'gender','Femme','sex','female',
    'pseudo','Membre Roman',
    'display_name','Membre Roman',
    'residence_country','Canada'
  )
),
(
  'c3000000-0000-4000-8000-000000000003',
  'private-novel-restricted@example.test',
  jsonb_build_object(
    'birth_date',(current_date-interval '30 years')::date::text,
    'date_of_birth',(current_date-interval '30 years')::date::text,
    'gender','Homme','sex','male',
    'pseudo','Compte non vérifié',
    'display_name','Compte non vérifié',
    'residence_country','Canada'
  )
);

delete from public.account_safety_profiles
where user_id='c3000000-0000-4000-8000-000000000003';

-- Le catalogue créateur dépend de l'autorité canonique is_sinjira_owner :
-- l'identité propriétaire canonique autorise l'attribution du rôle owner, puis le catalogue dépend du rôle serveur + RLS self-only.
insert into public.internal_admin_users(user_id,role)
values('c1000000-0000-4000-8000-000000000001','owner')
on conflict(user_id) do update set role=excluded.role;

insert into public.sinjira_novels(
  id,slug,title,status,sort_order,comments_enabled
)
values
(
  'c4000000-0000-4000-8000-000000000004',
  'private-novel-announced',
  'Roman annoncé privé',
  'announced',
  901,
  false
),
(
  'c5000000-0000-4000-8000-000000000005',
  'private-novel-draft',
  'Roman brouillon créateur',
  'draft',
  902,
  false
);

insert into public.products(id,slug,name,product_type,active)
values(
  'c6000000-0000-4000-8000-000000000006',
  'private-novel-product',
  'Roman privé de test',
  'novel',
  false
);

insert into private.sinjira_private_novel_assets(
  novel_id,product_slug,delivery_mode,storage_bucket,storage_path,
  download_name,total_pages,enabled
)
values
(
  'c4000000-0000-4000-8000-000000000004',
  'private-novel-product',
  'storage',
  'private-books',
  'tests/private-novel-announced.pdf',
  'Roman_prive_test.pdf',
  321,
  true
),
(
  'c5000000-0000-4000-8000-000000000005',
  null,
  'storage',
  'private-books',
  'tests/private-novel-draft.pdf',
  'Roman_brouillon_createur.pdf',
  654,
  true
);

insert into public.user_entitlements(user_id,product_id,source)
values(
  'c2000000-0000-4000-8000-000000000002',
  'c6000000-0000-4000-8000-000000000006',
  'test'
);

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','c2000000-0000-4000-8000-000000000002',
    'role','authenticated',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;

select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='private-novel-announced'
  ),
  'un membre voit le roman annoncé'
);
select ok(
  not exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='private-novel-draft'
  ),
  'un membre ne voit pas le brouillon créateur'
);
select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='private-novel-announced'
      and (item->>'full_access')::boolean=true
      and item->>'access_source'='product'
      and (item->>'total_pages')::integer=321
  ),
  'un entitlement donne accès intégral au roman privé configuré'
);
select ok(
  position('storage_bucket' in public.sinjira_my_novel_catalog()::text)=0
  and position('storage_path' in public.sinjira_my_novel_catalog()::text)=0
  and position('private-books' in public.sinjira_my_novel_catalog()::text)=0,
  'le catalogue navigateur ne révèle aucun chemin de stockage privé'
);

reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','c1000000-0000-4000-8000-000000000001',
    'role','authenticated',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;

select ok(
  exists(
    select 1
    from jsonb_array_elements(public.sinjira_my_novel_catalog()) item
    where item->>'slug'='private-novel-draft'
      and (item->>'creator_mode')::boolean=true
      and (item->>'full_access')::boolean=true
      and item->>'access_source'='owner'
  ),
  'le créateur voit le brouillon et son intégrale privée configurée'
);

reset role;

select set_config(
  'request.jwt.claims',
  jsonb_build_object(
    'sub','c3000000-0000-4000-8000-000000000003',
    'role','authenticated',
    'aal','aal1'
  )::text,
  true
);
set local role authenticated;

select is(
  public.sinjira_my_novel_catalog(),
  '[]'::jsonb,
  'un compte non vérifié ne reçoit aucun catalogue roman privé'
);

reset role;

select ok(
  exists(
    select 1
    from private.sinjira_private_novel_assets a
    join public.sinjira_novels n on n.id=a.novel_id
    where n.slug='la-cendre-du-jugement'
      and a.delivery_mode='legacy_env'
      and a.enabled=false
      and a.total_pages=1066
  ),
  'le Livre I reste enregistré mais désactivé tant que le stockage privé n est pas configuré'
);

select * from finish();
rollback;

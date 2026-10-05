begin;
create extension if not exists pgtap with schema extensions;
set local search_path=public,private,storage,extensions;

select plan(13);

select ok(
  to_regprocedure('public.sinjira_private_novel_release_status(text)') is not null,
  'la lecture de readiness privée existe'
);
select ok(
  to_regprocedure('public.sinjira_record_private_novel_integrity(text,text,bigint)') is not null,
  'la preuve d intégrité privée existe'
);
select ok(
  to_regprocedure('public.sinjira_set_private_novel_delivery(text,boolean)') is not null,
  'la bascule explicite de diffusion privée existe'
);

select ok(
  not has_function_privilege('authenticated','public.sinjira_private_novel_release_status(text)','EXECUTE'),
  'authenticated ne peut pas lire la readiness privée'
);
select ok(
  not has_function_privilege('authenticated','public.sinjira_record_private_novel_integrity(text,text,bigint)','EXECUTE'),
  'authenticated ne peut pas enregistrer une preuve d intégrité'
);
select ok(
  not has_function_privilege('authenticated','public.sinjira_set_private_novel_delivery(text,boolean)','EXECUTE'),
  'authenticated ne peut pas activer la diffusion privée'
);

select ok(
  exists(
    select 1
    from private.sinjira_private_novel_assets a
    join public.sinjira_novels n on n.id=a.novel_id
    where n.slug='la-cendre-du-jugement'
      and a.source_sha256='9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8'
      and a.source_size_bytes=7325502
      and a.source_mime_type='application/pdf'
      and a.source_received_on=date '2026-10-05'
      and a.total_pages=1027
  ),
  'le maître Livre I attendu est ancré sans publication'
);

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values(
  'sinjira-private-novels-test',
  'sinjira-private-novels-test',
  false,
  10485760,
  array['application/pdf']::text[]
)
on conflict(id) do update
set public=false,
    file_size_limit=excluded.file_size_limit,
    allowed_mime_types=excluded.allowed_mime_types;

insert into storage.objects(bucket_id,name,metadata)
values(
  'sinjira-private-novels-test',
  'release-tests/livre-i.pdf',
  jsonb_build_object('size',7325502,'mimetype','application/pdf')
)
on conflict(bucket_id,name) do update
set metadata=excluded.metadata;

update private.sinjira_private_novel_assets a
set delivery_mode='storage',
    storage_bucket='sinjira-private-novels-test',
    storage_path='release-tests/livre-i.pdf',
    enabled=false,
    integrity_verified_sha256=null,
    integrity_verified_size_bytes=null,
    integrity_verified_at=null,
    delivery_enabled_at=null,
    delivery_disabled_at=null
from public.sinjira_novels n
where a.novel_id=n.id
  and n.slug='la-cendre-du-jugement';

select set_config(
  'request.jwt.claims',
  jsonb_build_object('role','service_role','aal','aal2')::text,
  true
);
set local role service_role;

select ok(
  (public.sinjira_private_novel_release_status('la-cendre-du-jugement')->>'source_ready')::boolean
  and (public.sinjira_private_novel_release_status('la-cendre-du-jugement')->>'bucket_private')::boolean
  and (public.sinjira_private_novel_release_status('la-cendre-du-jugement')->>'object_exists')::boolean,
  'la readiness voit le maître, le bucket privé et l objet'
);

select ok(
  not (public.sinjira_private_novel_release_status('la-cendre-du-jugement')->>'can_enable')::boolean,
  'la diffusion reste bloquée avant preuve d intégrité'
);

select ok(
  (
    public.sinjira_record_private_novel_integrity(
      'la-cendre-du-jugement',
      '9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8',
      7325502
    )->>'can_enable'
  )::boolean,
  'la preuve exacte rend le roman éligible à une décision humaine'
);

select ok(
  (
    public.sinjira_set_private_novel_delivery(
      'la-cendre-du-jugement',
      true
    )->>'enabled'
  )::boolean,
  'l activation explicite fonctionne seulement après readiness complète'
);

select ok(
  not (
    public.sinjira_set_private_novel_delivery(
      'la-cendre-du-jugement',
      false
    )->>'enabled'
  )::boolean,
  'la désactivation fail-safe reste immédiatement disponible'
);

reset role;

update storage.buckets
set public=true
where id='sinjira-private-novels-test';

select set_config(
  'request.jwt.claims',
  jsonb_build_object('role','service_role','aal','aal2')::text,
  true
);
set local role service_role;

select ok(
  not (public.sinjira_private_novel_release_status('la-cendre-du-jugement')->>'can_enable')::boolean,
  'un bucket public invalide immédiatement la readiness de diffusion privée'
);

select * from finish();
rollback;

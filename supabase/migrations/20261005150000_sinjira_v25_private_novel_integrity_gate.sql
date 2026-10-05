-- SINJIRA™ V25 — garde d’intégrité et activation explicite des romans privés.
-- Forward-only. Cette migration N’ACTIVE aucun roman et N’AJOUTE aucun PDF au stockage.
-- Elle sépare strictement : source attendue -> objet privé présent -> intégrité enregistrée
-- -> décision humaine explicite -> diffusion signée.
--
-- Principe : L’HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.

begin;

alter table private.sinjira_private_novel_assets
  add column if not exists source_sha256 text,
  add column if not exists source_size_bytes bigint,
  add column if not exists source_mime_type text,
  add column if not exists source_received_on date,
  add column if not exists integrity_verified_sha256 text,
  add column if not exists integrity_verified_size_bytes bigint,
  add column if not exists integrity_verified_at timestamptz,
  add column if not exists delivery_enabled_at timestamptz,
  add column if not exists delivery_disabled_at timestamptz;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname='sinjira_private_novel_assets_source_sha256_check'
      and conrelid='private.sinjira_private_novel_assets'::regclass
  ) then
    alter table private.sinjira_private_novel_assets
      add constraint sinjira_private_novel_assets_source_sha256_check
      check(source_sha256 is null or source_sha256 ~ '^[0-9a-f]{64}$');
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname='sinjira_private_novel_assets_source_size_check'
      and conrelid='private.sinjira_private_novel_assets'::regclass
  ) then
    alter table private.sinjira_private_novel_assets
      add constraint sinjira_private_novel_assets_source_size_check
      check(source_size_bytes is null or source_size_bytes > 0);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname='sinjira_private_novel_assets_verified_sha256_check'
      and conrelid='private.sinjira_private_novel_assets'::regclass
  ) then
    alter table private.sinjira_private_novel_assets
      add constraint sinjira_private_novel_assets_verified_sha256_check
      check(integrity_verified_sha256 is null or integrity_verified_sha256 ~ '^[0-9a-f]{64}$');
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname='sinjira_private_novel_assets_verified_size_check'
      and conrelid='private.sinjira_private_novel_assets'::regclass
  ) then
    alter table private.sinjira_private_novel_assets
      add constraint sinjira_private_novel_assets_verified_size_check
      check(integrity_verified_size_bytes is null or integrity_verified_size_bytes > 0);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname='sinjira_private_novel_assets_source_mime_check'
      and conrelid='private.sinjira_private_novel_assets'::regclass
  ) then
    alter table private.sinjira_private_novel_assets
      add constraint sinjira_private_novel_assets_source_mime_check
      check(source_mime_type is null or source_mime_type in ('application/pdf'));
  end if;
end $$;

-- Rebaseline du maître reçu le 5 octobre 2026.
-- Aucune configuration de bucket/path et aucune activation ne sont faites ici.
update private.sinjira_private_novel_assets a
set source_sha256='9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8',
    source_size_bytes=7325502,
    source_mime_type='application/pdf',
    source_received_on=date '2026-10-05',
    total_pages=1027,
    updated_at=now()
from public.sinjira_novels n
where a.novel_id=n.id
  and n.slug='la-cendre-du-jugement';

create or replace function public.sinjira_private_novel_release_status(p_novel_slug text)
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,storage
as $$
declare
  item record;
  object_size bigint;
  object_mime text;
  object_exists boolean:=false;
  bucket_private boolean:=false;
  source_ready boolean:=false;
  object_shape_ok boolean:=false;
  integrity_ok boolean:=false;
  can_enable boolean:=false;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;

  select
    n.slug,
    a.delivery_mode,
    a.storage_bucket,
    a.storage_path,
    a.enabled,
    a.total_pages,
    a.source_sha256,
    a.source_size_bytes,
    a.source_mime_type,
    a.source_received_on,
    a.integrity_verified_sha256,
    a.integrity_verified_size_bytes,
    a.integrity_verified_at,
    a.delivery_enabled_at,
    a.delivery_disabled_at
  into item
  from public.sinjira_novels n
  join private.sinjira_private_novel_assets a on a.novel_id=n.id
  where n.slug=trim(coalesce(p_novel_slug,''));

  if item.slug is null then
    raise exception 'NOVEL_PRIVATE_ASSET_NOT_FOUND';
  end if;

  source_ready :=
    item.source_sha256 is not null
    and item.source_size_bytes is not null
    and item.source_mime_type='application/pdf'
    and item.source_received_on is not null;

  if nullif(trim(coalesce(item.storage_bucket,'')),'') is not null
     and nullif(trim(coalesce(item.storage_path,'')),'') is not null then

    select (b.public is false)
    into bucket_private
    from storage.buckets b
    where b.id=item.storage_bucket;

    select
      true,
      case
        when coalesce(o.metadata->>'size','') ~ '^[0-9]+$'
          then (o.metadata->>'size')::bigint
        else null
      end,
      lower(coalesce(o.metadata->>'mimetype',''))
    into object_exists,object_size,object_mime
    from storage.objects o
    where o.bucket_id=item.storage_bucket
      and o.name=item.storage_path
    limit 1;
  end if;

  object_shape_ok :=
    bucket_private is true
    and object_exists is true
    and object_size=item.source_size_bytes
    and object_mime=item.source_mime_type;

  integrity_ok :=
    item.integrity_verified_at is not null
    and item.integrity_verified_sha256=item.source_sha256
    and item.integrity_verified_size_bytes=item.source_size_bytes;

  can_enable :=
    item.delivery_mode='storage'
    and source_ready
    and object_shape_ok
    and integrity_ok;

  return jsonb_build_object(
    'novel_slug',item.slug,
    'enabled',item.enabled,
    'delivery_mode',item.delivery_mode,
    'storage_configured',
      nullif(trim(coalesce(item.storage_bucket,'')),'') is not null
      and nullif(trim(coalesce(item.storage_path,'')),'') is not null,
    'bucket_private',coalesce(bucket_private,false),
    'object_exists',coalesce(object_exists,false),
    'object_size_bytes',object_size,
    'object_mime_type',nullif(object_mime,''),
    'source_ready',source_ready,
    'expected_size_bytes',item.source_size_bytes,
    'expected_sha256',item.source_sha256,
    'integrity_verified',integrity_ok,
    'integrity_verified_at',item.integrity_verified_at,
    'can_enable',can_enable,
    'delivery_enabled_at',item.delivery_enabled_at,
    'delivery_disabled_at',item.delivery_disabled_at
  );
end;
$$;

revoke all on function public.sinjira_private_novel_release_status(text)
from public,anon,authenticated;
grant execute on function public.sinjira_private_novel_release_status(text)
to service_role;

create or replace function public.sinjira_record_private_novel_integrity(
  p_novel_slug text,
  p_sha256 text,
  p_size_bytes bigint
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private,storage
as $$
declare
  item record;
  object_size bigint;
  object_mime text;
  bucket_private boolean:=false;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;

  select
    n.id as novel_id,
    n.slug,
    a.storage_bucket,
    a.storage_path,
    a.source_sha256,
    a.source_size_bytes,
    a.source_mime_type
  into item
  from public.sinjira_novels n
  join private.sinjira_private_novel_assets a on a.novel_id=n.id
  where n.slug=trim(coalesce(p_novel_slug,''))
  for update of a;

  if item.novel_id is null then
    raise exception 'NOVEL_PRIVATE_ASSET_NOT_FOUND';
  end if;

  if lower(trim(coalesce(p_sha256,''))) is distinct from item.source_sha256
     or p_size_bytes is distinct from item.source_size_bytes then
    raise exception 'NOVEL_INTEGRITY_MISMATCH';
  end if;

  if nullif(trim(coalesce(item.storage_bucket,'')),'') is null
     or nullif(trim(coalesce(item.storage_path,'')),'') is null then
    raise exception 'NOVEL_PRIVATE_STORAGE_NOT_CONFIGURED';
  end if;

  select (b.public is false)
  into bucket_private
  from storage.buckets b
  where b.id=item.storage_bucket;

  if bucket_private is not true then
    raise exception 'NOVEL_PRIVATE_BUCKET_REQUIRED';
  end if;

  select
    case
      when coalesce(o.metadata->>'size','') ~ '^[0-9]+$'
        then (o.metadata->>'size')::bigint
      else null
    end,
    lower(coalesce(o.metadata->>'mimetype',''))
  into object_size,object_mime
  from storage.objects o
  where o.bucket_id=item.storage_bucket
    and o.name=item.storage_path
  limit 1;

  if object_size is null then
    raise exception 'NOVEL_PRIVATE_OBJECT_NOT_FOUND';
  end if;
  if object_size is distinct from item.source_size_bytes then
    raise exception 'NOVEL_PRIVATE_OBJECT_SIZE_MISMATCH';
  end if;
  if object_mime is distinct from item.source_mime_type then
    raise exception 'NOVEL_PRIVATE_OBJECT_MIME_MISMATCH';
  end if;

  update private.sinjira_private_novel_assets
  set integrity_verified_sha256=item.source_sha256,
      integrity_verified_size_bytes=item.source_size_bytes,
      integrity_verified_at=now(),
      updated_at=now()
  where novel_id=item.novel_id;

  return public.sinjira_private_novel_release_status(item.slug);
end;
$$;

revoke all on function public.sinjira_record_private_novel_integrity(text,text,bigint)
from public,anon,authenticated;
grant execute on function public.sinjira_record_private_novel_integrity(text,text,bigint)
to service_role;

create or replace function public.sinjira_set_private_novel_delivery(
  p_novel_slug text,
  p_enabled boolean
)
returns jsonb
language plpgsql
security definer
set search_path=pg_catalog,public,private
as $$
declare
  novel_id_value uuid;
  status jsonb;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;

  select n.id
  into novel_id_value
  from public.sinjira_novels n
  where n.slug=trim(coalesce(p_novel_slug,''));

  if novel_id_value is null then
    raise exception 'NOVEL_PRIVATE_ASSET_NOT_FOUND';
  end if;

  if p_enabled is false then
    update private.sinjira_private_novel_assets
    set enabled=false,
        delivery_disabled_at=now(),
        updated_at=now()
    where novel_id=novel_id_value;
    return public.sinjira_private_novel_release_status(p_novel_slug);
  end if;

  status:=public.sinjira_private_novel_release_status(p_novel_slug);
  if coalesce((status->>'can_enable')::boolean,false) is not true then
    raise exception 'NOVEL_PRIVATE_RELEASE_NOT_READY';
  end if;

  update private.sinjira_private_novel_assets
  set enabled=true,
      delivery_enabled_at=now(),
      delivery_disabled_at=null,
      updated_at=now()
  where novel_id=novel_id_value;

  return public.sinjira_private_novel_release_status(p_novel_slug);
end;
$$;

revoke all on function public.sinjira_set_private_novel_delivery(text,boolean)
from public,anon,authenticated;
grant execute on function public.sinjira_set_private_novel_delivery(text,boolean)
to service_role;

comment on function public.sinjira_private_novel_release_status(text) is
  'V25: état de préparation d un roman privé réservé au service_role. Ne décide jamais seul de publier.';
comment on function public.sinjira_record_private_novel_integrity(text,text,bigint) is
  'V25: enregistre une preuve d intégrité externe uniquement si l objet Storage privé et sa forme correspondent au maître attendu.';
comment on function public.sinjira_set_private_novel_delivery(text,boolean) is
  'V25: activation/désactivation service_role; activation refusée sans stockage privé, objet conforme et intégrité préalablement vérifiée.';

commit;

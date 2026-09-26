-- SINJIRA™ V25 — registre privé générique des romans intégraux.
-- Les chemins de stockage ne sont jamais exposés au navigateur.
-- Le catalogue self-only ne retourne que métadonnées et état d'accès.

create table if not exists private.sinjira_private_novel_assets(
  novel_id uuid primary key references public.sinjira_novels(id) on delete cascade,
  product_slug text,
  delivery_mode text not null default 'storage',
  storage_bucket text,
  storage_path text,
  download_name text,
  total_pages integer,
  enabled boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint sinjira_private_novel_assets_delivery_mode_check
    check(delivery_mode in ('legacy_env','storage')),
  constraint sinjira_private_novel_assets_total_pages_check
    check(total_pages is null or total_pages>0),
  constraint sinjira_private_novel_assets_storage_shape_check
    check(
      delivery_mode='legacy_env'
      or (
        nullif(trim(coalesce(storage_bucket,'')),'') is not null
        and nullif(trim(coalesce(storage_path,'')),'') is not null
        and storage_path not like '/%'
        and storage_path not like '%://%'
      )
    )
);

-- Défense en profondeur dès la création : même si le schéma privé devenait
-- accidentellement atteignable, aucune policy membre n'autorise la lecture.
alter table private.sinjira_private_novel_assets
  enable row level security;

revoke all on table private.sinjira_private_novel_assets from public,anon,authenticated;
grant select,insert,update,delete on table private.sinjira_private_novel_assets to service_role;

insert into private.sinjira_private_novel_assets(
  novel_id,product_slug,delivery_mode,download_name,total_pages,enabled
)
select n.id,
       'sinjira-livre-01-la-cendre-du-jugement',
       'legacy_env',
       'SINJIRA_Livre_01_La_Cendre_du_Jugement.pdf',
       1066,
       false
from public.sinjira_novels n
where n.slug='la-cendre-du-jugement'
on conflict(novel_id) do nothing;

create or replace function public.sinjira_my_novel_catalog()
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private,auth
as $$
declare
  uid uuid:=auth.uid();
  band text;
  owner_mode boolean:=false;
  result jsonb;
begin
  if uid is null then raise exception 'AUTH_REQUIRED'; end if;

  band:=public.sinjira_age_band(uid);
  if band not in ('adult','youth') then
    return '[]'::jsonb;
  end if;

  select public.is_sinjira_owner(uid)
  into owner_mode;

  with catalogue as (
    select
      n.id,n.slug,n.title,n.subtitle,n.description,n.status,n.cover_url,
      n.public_path,n.demo_path,n.sort_order,
      a.product_slug,
      coalesce(a.enabled,false) as private_asset_configured,
      a.total_pages,
      exists(
        select 1
        from public.products p
        join public.user_entitlements ue
          on ue.product_id=p.id
         and ue.user_id=uid
        where p.slug=a.product_slug
      ) as entitled
    from public.sinjira_novels n
    left join private.sinjira_private_novel_assets a on a.novel_id=n.id
    where owner_mode
       or n.status in ('announced','published')
       or exists(
         select 1
         from public.products p
         join public.user_entitlements ue
           on ue.product_id=p.id
          and ue.user_id=uid
         where p.slug=a.product_slug
       )
  )
  select coalesce(
    jsonb_agg(
      jsonb_build_object(
        'id',id,
        'slug',slug,
        'title',title,
        'subtitle',subtitle,
        'description',description,
        'status',status,
        'cover_url',cover_url,
        'public_path',public_path,
        'demo_path',demo_path,
        'sort_order',sort_order,
        'creator_mode',owner_mode,
        'full_access',private_asset_configured and (owner_mode or entitled),
        'private_asset_configured',private_asset_configured,
        'total_pages',total_pages,
        'access_source',case
          when private_asset_configured and owner_mode then 'owner'
          when private_asset_configured and entitled then 'entitlement'
          else 'catalogue'
        end
      )
      order by sort_order,title
    ),
    '[]'::jsonb
  ) into result
  from catalogue;

  return result;
end;
$$;

revoke all on function public.sinjira_my_novel_catalog() from public,anon;
grant execute on function public.sinjira_my_novel_catalog() to authenticated;

create or replace function public.sinjira_private_novel_asset_for_delivery(p_novel_slug text)
returns jsonb
language plpgsql
stable
security definer
set search_path=pg_catalog,public,private
as $$
declare
  item jsonb;
begin
  if coalesce(auth.jwt()->>'role','')<>'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;

  select jsonb_build_object(
    'novel_id',n.id,
    'novel_slug',n.slug,
    'title',n.title,
    'product_slug',a.product_slug,
    'delivery_mode',a.delivery_mode,
    'storage_bucket',a.storage_bucket,
    'storage_path',a.storage_path,
    'download_name',a.download_name,
    'total_pages',a.total_pages,
    'enabled',a.enabled
  )
  into item
  from public.sinjira_novels n
  join private.sinjira_private_novel_assets a on a.novel_id=n.id
  where n.slug=trim(coalesce(p_novel_slug,''));

  if item is null then raise exception 'NOVEL_PRIVATE_ASSET_NOT_FOUND'; end if;
  return item;
end;
$$;

revoke all on function public.sinjira_private_novel_asset_for_delivery(text)
from public,anon,authenticated;
grant execute on function public.sinjira_private_novel_asset_for_delivery(text)
to service_role;

comment on function public.sinjira_my_novel_catalog() is
  'V25: catalogue roman self-only; owner voit tout, membre voit catalogue/entitlements; aucun chemin de stockage privé n est retourné. Un actif privé reste désactivé jusqu à activation explicite.';
comment on function public.sinjira_private_novel_asset_for_delivery(text) is
  'V25: métadonnées de livraison privée réservées au service_role; jamais appelables par un navigateur membre.';

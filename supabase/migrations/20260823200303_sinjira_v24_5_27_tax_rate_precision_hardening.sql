alter table public.preorder_tax_estimate_profiles
  alter column paper_rate_basis_points type numeric(10,3) using paper_rate_basis_points::numeric,
  alter column digital_rate_basis_points type numeric(10,3) using digital_rate_basis_points::numeric,
  alter column shipping_rate_basis_points type numeric(10,3) using shipping_rate_basis_points::numeric;

comment on column public.preorder_tax_estimate_profiles.paper_rate_basis_points is 'Points de base décimaux du taux papier indicatif; 100 points de base = 1 %. Précision suffisante pour 14,975 % sans arrondi imposé.';
comment on column public.preorder_tax_estimate_profiles.digital_rate_basis_points is 'Points de base décimaux du taux numérique indicatif; 100 points de base = 1 %.';
comment on column public.preorder_tax_estimate_profiles.shipping_rate_basis_points is 'Points de base décimaux du taux indicatif applicable à la livraison, si vérifié pour la zone.';

drop function if exists public.admin_preorder_tax_profile_save(text,text,text,text,text,integer,integer,integer,text,date,text,boolean);
drop function if exists preorder_tax_internal.admin_preorder_tax_profile_save(text,text,text,text,text,integer,integer,integer,text,date,text,boolean);

create or replace function preorder_tax_internal.admin_preorder_tax_profile_save(
  p_product_slug text,
  p_tax_code text,
  p_label text,
  p_country_code text default null,
  p_subdivision_code text default null,
  p_paper_rate_basis_points numeric default null,
  p_digital_rate_basis_points numeric default null,
  p_shipping_rate_basis_points numeric default null,
  p_source_reference text default null,
  p_effective_on date default null,
  p_estimate_note text default null,
  p_active boolean default true
)
returns uuid
language plpgsql
security definer
set search_path=''
as $$
declare
  v_admin uuid := auth.uid();
  v_product_id uuid;
  v_id uuid;
  v_code text := lower(btrim(coalesce(p_tax_code,'')));
begin
  perform private.require_sinjira_admin_aal2();
  select id into v_product_id from public.products where slug=p_product_slug and active=true limit 1;
  if v_product_id is null then raise exception using errcode='22023',message='PREORDER_PRODUCT_NOT_FOUND'; end if;
  if v_code !~ '^[a-z0-9][a-z0-9_-]{1,39}$' then raise exception using errcode='22023',message='INVALID_TAX_CODE'; end if;
  if nullif(btrim(coalesce(p_label,'')),'') is null then raise exception using errcode='22023',message='TAX_LABEL_REQUIRED'; end if;
  if p_country_code is not null and upper(btrim(p_country_code)) !~ '^[A-Z]{2}$' then raise exception using errcode='22023',message='INVALID_COUNTRY_CODE'; end if;
  if coalesce(p_paper_rate_basis_points,0) < 0 or coalesce(p_paper_rate_basis_points,0) > 10000
     or coalesce(p_digital_rate_basis_points,0) < 0 or coalesce(p_digital_rate_basis_points,0) > 10000
     or coalesce(p_shipping_rate_basis_points,0) < 0 or coalesce(p_shipping_rate_basis_points,0) > 10000 then
    raise exception using errcode='22023',message='INVALID_TAX_RATE';
  end if;

  insert into public.preorder_tax_estimate_profiles(
    product_id,tax_code,label,country_code,subdivision_code,paper_rate_basis_points,digital_rate_basis_points,
    shipping_rate_basis_points,source_reference,effective_on,estimate_note,active,published_at,created_by,updated_by
  ) values (
    v_product_id,v_code,btrim(p_label),nullif(upper(btrim(coalesce(p_country_code,''))),''),
    nullif(upper(btrim(coalesce(p_subdivision_code,''))),''),p_paper_rate_basis_points,p_digital_rate_basis_points,
    p_shipping_rate_basis_points,nullif(btrim(coalesce(p_source_reference,'')),''),p_effective_on,
    nullif(btrim(coalesce(p_estimate_note,'')),''),coalesce(p_active,true),null,v_admin,v_admin
  )
  on conflict(product_id,tax_code) do update set
    label=excluded.label,country_code=excluded.country_code,subdivision_code=excluded.subdivision_code,
    paper_rate_basis_points=excluded.paper_rate_basis_points,digital_rate_basis_points=excluded.digital_rate_basis_points,
    shipping_rate_basis_points=excluded.shipping_rate_basis_points,source_reference=excluded.source_reference,
    effective_on=excluded.effective_on,estimate_note=excluded.estimate_note,active=excluded.active,
    published_at=null,updated_by=v_admin,updated_at=now()
  returning id into v_id;
  return v_id;
end;
$$;

revoke all on function preorder_tax_internal.admin_preorder_tax_profile_save(text,text,text,text,text,numeric,numeric,numeric,text,date,text,boolean) from public,anon;
grant execute on function preorder_tax_internal.admin_preorder_tax_profile_save(text,text,text,text,text,numeric,numeric,numeric,text,date,text,boolean) to authenticated,service_role;

create or replace function public.admin_preorder_tax_profile_save(
  p_product_slug text,
  p_tax_code text,
  p_label text,
  p_country_code text default null,
  p_subdivision_code text default null,
  p_paper_rate_basis_points numeric default null,
  p_digital_rate_basis_points numeric default null,
  p_shipping_rate_basis_points numeric default null,
  p_source_reference text default null,
  p_effective_on date default null,
  p_estimate_note text default null,
  p_active boolean default true
)
returns uuid language sql security invoker set search_path=''
as $$select preorder_tax_internal.admin_preorder_tax_profile_save($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)$$;

revoke all on function public.admin_preorder_tax_profile_save(text,text,text,text,text,numeric,numeric,numeric,text,date,text,boolean) from public,anon;
grant execute on function public.admin_preorder_tax_profile_save(text,text,text,text,text,numeric,numeric,numeric,text,date,text,boolean) to authenticated,service_role;

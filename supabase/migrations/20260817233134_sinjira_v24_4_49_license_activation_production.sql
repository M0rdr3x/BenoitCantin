-- SINJIRA V24.4.49 — activation physique ciblée en production.
-- Ce correctif active uniquement le sous-système de codes de licence déjà utilisé
-- par les Edge Functions admin-license-codes et redeem-license-code.

create table if not exists public.license_batches (
  id uuid primary key default gen_random_uuid(),
  product_slug text not null,
  batch_code text not null unique,
  quantity integer not null check (quantity > 0),
  status text not null default 'active' check (status in ('active','revoked','exhausted')),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.activation_codes (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references public.license_batches(id) on delete cascade,
  code_hash text not null unique,
  product_slug text not null,
  status text not null default 'unused' check (status in ('unused','redeemed','revoked')),
  redeemed_by uuid references auth.users(id) on delete set null,
  redeemed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists activation_codes_batch_idx
  on public.activation_codes(batch_id,status);

create table if not exists public.license_redemptions (
  id uuid primary key default gen_random_uuid(),
  activation_code_id uuid not null unique references public.activation_codes(id) on delete restrict,
  user_id uuid not null references auth.users(id) on delete cascade,
  product_slug text not null,
  redeemed_at timestamptz not null default now()
);

create index if not exists license_redemptions_user_idx
  on public.license_redemptions(user_id,redeemed_at desc);

alter table public.license_batches enable row level security;
alter table public.activation_codes enable row level security;
alter table public.license_redemptions enable row level security;

-- Ces tables ne sont jamais lues ou écrites directement depuis le navigateur.
revoke all on public.license_batches from public,anon,authenticated;
revoke all on public.activation_codes from public,anon,authenticated;
revoke all on public.license_redemptions from public,anon,authenticated;

grant all on public.license_batches to service_role;
grant all on public.activation_codes to service_role;
grant all on public.license_redemptions to service_role;

create or replace function public.redeem_sinjira_activation(p_code_hash text,p_user_id uuid)
returns table(product_slug text, product_id uuid)
language plpgsql
security definer
set search_path=public
as $$
declare
  c public.activation_codes%rowtype;
  p public.products%rowtype;
begin
  if p_user_id is null or nullif(trim(p_code_hash),'') is null then
    raise exception 'CODE_INVALID_OR_USED';
  end if;

  select * into c
  from public.activation_codes
  where code_hash=p_code_hash
  for update;

  if c.id is null or c.status <> 'unused' then
    raise exception 'CODE_INVALID_OR_USED';
  end if;

  select * into p
  from public.products
  where slug=c.product_slug and active=true;

  if p.id is null then
    raise exception 'PRODUCT_NOT_ACTIVE';
  end if;

  update public.activation_codes
  set status='redeemed',redeemed_by=p_user_id,redeemed_at=now()
  where id=c.id;

  insert into public.license_redemptions(activation_code_id,user_id,product_slug)
  values(c.id,p_user_id,c.product_slug);

  insert into public.user_entitlements(user_id,product_id,source)
  values(p_user_id,p.id,'physical_activation')
  on conflict (user_id,product_id) do nothing;

  return query select c.product_slug,p.id;
end;
$$;

revoke all on function public.redeem_sinjira_activation(text,uuid) from public,anon,authenticated;
grant execute on function public.redeem_sinjira_activation(text,uuid) to service_role;

create or replace function public.sinjira_license_health()
returns jsonb
language sql
stable
security invoker
set search_path=public
as $$
  select jsonb_build_object(
    'ok',
      to_regclass('public.license_batches') is not null and
      to_regclass('public.activation_codes') is not null and
      to_regclass('public.license_redemptions') is not null and
      to_regprocedure('public.redeem_sinjira_activation(text,uuid)') is not null and
      exists(select 1 from public.products where slug='fracture-du-reseau-mere' and active=true),
    'tables',jsonb_build_object(
      'license_batches',to_regclass('public.license_batches') is not null,
      'activation_codes',to_regclass('public.activation_codes') is not null,
      'license_redemptions',to_regclass('public.license_redemptions') is not null
    ),
    'redeem_rpc',to_regprocedure('public.redeem_sinjira_activation(text,uuid)') is not null,
    'fracture_product_active',exists(select 1 from public.products where slug='fracture-du-reseau-mere' and active=true),
    'version','24.4.49'
  );
$$;

revoke all on function public.sinjira_license_health() from public,anon,authenticated;
grant execute on function public.sinjira_license_health() to service_role;

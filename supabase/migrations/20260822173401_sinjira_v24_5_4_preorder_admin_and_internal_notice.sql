create table if not exists public.preorder_sales_announcements (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  campaign_key text not null default 'sales_opening' check (campaign_key ~ '^[a-z0-9_]{3,64}$'),
  title text not null check (char_length(title) between 1 and 160),
  body text not null default '' check (char_length(body) <= 1000),
  action_path text not null default '/compte/mes-achats.html#precommandes' check (action_path ~ '^/[A-Za-z0-9_./#?=&%-]{1,299}$'),
  sales_open_at timestamptz,
  public_price_text text check (public_price_text is null or char_length(public_price_text) <= 120),
  edition_note text not null default '' check (char_length(edition_note) <= 600),
  status text not null default 'draft' check (status in ('draft','ready','sent','cancelled')),
  external_delivery_enabled boolean not null default false check (external_delivery_enabled = false),
  payment_activation_allowed boolean not null default false check (payment_activation_allowed = false),
  created_by uuid not null references auth.users(id) on delete restrict,
  updated_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  ready_at timestamptz,
  sent_at timestamptz,
  recipient_count integer not null default 0 check (recipient_count >= 0),
  constraint preorder_sales_announcements_product_campaign_key unique (product_id, campaign_key)
);

comment on table public.preorder_sales_announcements is
  'V24.5.4: brouillons et campagnes de notification interne des précommandes. Aucun transport externe ni activation de paiement.';
comment on column public.preorder_sales_announcements.external_delivery_enabled is
  'Verrouillé à false: aucun courriel, SMS ou fournisseur externe n est activé par ce module.';
comment on column public.preorder_sales_announcements.payment_activation_allowed is
  'Verrouillé à false: une campagne de précommande ne peut jamais ouvrir un checkout ou autoriser un débit.';

create index if not exists preorder_sales_announcements_product_status_idx
  on public.preorder_sales_announcements(product_id, status, updated_at desc);
create index if not exists preorder_sales_announcements_created_by_idx
  on public.preorder_sales_announcements(created_by, created_at desc);
create index if not exists preorder_sales_announcements_updated_by_idx
  on public.preorder_sales_announcements(updated_by, updated_at desc);

alter table public.preorder_sales_announcements enable row level security;
revoke all on table public.preorder_sales_announcements from public, anon, authenticated;

create or replace function public.admin_preorder_overview(p_product_slug text)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_product_id uuid;
  v_product_name text;
  v_summary jsonb;
  v_announcement jsonb;
begin
  v_admin := private.require_sinjira_admin_aal2();

  select p.id, p.name into v_product_id, v_product_name
  from public.products p
  where p.slug = p_product_slug
  limit 1;

  if v_product_id is null then
    raise exception using errcode='22023', message='UNKNOWN_PRODUCT';
  end if;

  select jsonb_build_object(
    'reserved_accounts', count(*) filter (where pp.status='reserved'),
    'cancelled_accounts', count(*) filter (where pp.status='cancelled'),
    'reserved_units', coalesce(sum(pp.quantity) filter (where pp.status='reserved'),0),
    'notify_opt_in', count(*) filter (where pp.status='reserved' and pp.contact_when_sales_open),
    'paper_accounts', count(*) filter (where pp.status='reserved' and pp.preferred_format='paper'),
    'digital_accounts', count(*) filter (where pp.status='reserved' and pp.preferred_format='digital'),
    'both_accounts', count(*) filter (where pp.status='reserved' and pp.preferred_format='both'),
    'undecided_accounts', count(*) filter (where pp.status='reserved' and pp.preferred_format='undecided'),
    'paper_units', coalesce(sum(pp.quantity) filter (where pp.status='reserved' and pp.preferred_format='paper'),0),
    'digital_units', coalesce(sum(pp.quantity) filter (where pp.status='reserved' and pp.preferred_format='digital'),0),
    'both_units', coalesce(sum(pp.quantity) filter (where pp.status='reserved' and pp.preferred_format='both'),0),
    'undecided_units', coalesce(sum(pp.quantity) filter (where pp.status='reserved' and pp.preferred_format='undecided'),0)
  ) into v_summary
  from public.product_preorders pp
  where pp.product_id = v_product_id;

  select jsonb_build_object(
    'id', a.id,
    'campaign_key', a.campaign_key,
    'title', a.title,
    'body', a.body,
    'action_path', a.action_path,
    'sales_open_at', a.sales_open_at,
    'public_price_text', a.public_price_text,
    'edition_note', a.edition_note,
    'status', a.status,
    'external_delivery_enabled', a.external_delivery_enabled,
    'payment_activation_allowed', a.payment_activation_allowed,
    'updated_at', a.updated_at,
    'ready_at', a.ready_at,
    'sent_at', a.sent_at,
    'recipient_count', a.recipient_count
  ) into v_announcement
  from public.preorder_sales_announcements a
  where a.product_id=v_product_id and a.campaign_key='sales_opening';

  return jsonb_build_object(
    'product', jsonb_build_object('slug',p_product_slug,'name',v_product_name),
    'summary', coalesce(v_summary,'{}'::jsonb),
    'announcement', v_announcement,
    'financial_contract', jsonb_build_object(
      'payment_enabled',false,
      'external_delivery_enabled',false,
      'automatic_conversion_to_order',false
    )
  );
end;
$$;

create or replace function public.admin_preorder_list(
  p_product_slug text,
  p_status text default null,
  p_format text default null,
  p_limit integer default 100,
  p_offset integer default 0
)
returns table(
  preorder_id uuid,
  user_label text,
  quantity integer,
  preferred_format text,
  status text,
  contact_when_sales_open boolean,
  created_at timestamptz,
  updated_at timestamptz,
  cancelled_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
begin
  v_admin := private.require_sinjira_admin_aal2();
  if p_status is not null and p_status not in ('reserved','cancelled') then
    raise exception using errcode='22023', message='INVALID_STATUS_FILTER';
  end if;
  if p_format is not null and p_format not in ('digital','paper','both','undecided') then
    raise exception using errcode='22023', message='INVALID_FORMAT_FILTER';
  end if;
  if coalesce(p_limit,0) < 1 or p_limit > 250 or coalesce(p_offset,0) < 0 then
    raise exception using errcode='22023', message='INVALID_PAGINATION';
  end if;

  return query
  select
    pp.id,
    coalesce(nullif(pr.pseudo,''),nullif(pr.display_name,''),'Compte SINJIRA')::text,
    pp.quantity::integer,
    pp.preferred_format,
    pp.status,
    pp.contact_when_sales_open,
    pp.created_at,
    pp.updated_at,
    pp.cancelled_at
  from public.product_preorders pp
  join public.products p on p.id=pp.product_id
  left join public.profiles pr on pr.user_id=pp.user_id
  where p.slug=p_product_slug
    and (p_status is null or pp.status=p_status)
    and (p_format is null or pp.preferred_format=p_format)
  order by pp.updated_at desc
  limit p_limit offset p_offset;
end;
$$;

create or replace function public.admin_preorder_save_announcement_draft(
  p_product_slug text,
  p_title text,
  p_body text,
  p_action_path text default '/compte/mes-achats.html#precommandes',
  p_sales_open_at timestamptz default null,
  p_public_price_text text default null,
  p_edition_note text default ''
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_product_id uuid;
  v_id uuid;
  v_status text;
begin
  v_admin := private.require_sinjira_admin_aal2();
  select id into v_product_id from public.products where slug=p_product_slug limit 1;
  if v_product_id is null then raise exception using errcode='22023', message='UNKNOWN_PRODUCT'; end if;
  if btrim(coalesce(p_title,''))='' or char_length(p_title)>160 then raise exception using errcode='22023', message='INVALID_TITLE'; end if;
  if char_length(coalesce(p_body,''))>1000 then raise exception using errcode='22023', message='INVALID_BODY'; end if;
  if p_action_path is null or p_action_path !~ '^/[A-Za-z0-9_./#?=&%-]{1,299}$' then raise exception using errcode='22023', message='INVALID_ACTION_PATH'; end if;
  if p_public_price_text is not null and char_length(p_public_price_text)>120 then raise exception using errcode='22023', message='INVALID_PRICE_TEXT'; end if;
  if char_length(coalesce(p_edition_note,''))>600 then raise exception using errcode='22023', message='INVALID_EDITION_NOTE'; end if;

  select status into v_status from public.preorder_sales_announcements where product_id=v_product_id and campaign_key='sales_opening';
  if v_status='sent' then raise exception using errcode='55000', message='ANNOUNCEMENT_ALREADY_SENT'; end if;

  insert into public.preorder_sales_announcements(
    product_id,campaign_key,title,body,action_path,sales_open_at,public_price_text,edition_note,
    status,external_delivery_enabled,payment_activation_allowed,created_by,updated_by,ready_at,sent_at,recipient_count
  ) values (
    v_product_id,'sales_opening',btrim(p_title),coalesce(p_body,''),p_action_path,p_sales_open_at,
    nullif(btrim(coalesce(p_public_price_text,'')),''),coalesce(p_edition_note,''),
    'draft',false,false,v_admin,v_admin,null,null,0
  )
  on conflict(product_id,campaign_key) do update set
    title=excluded.title,
    body=excluded.body,
    action_path=excluded.action_path,
    sales_open_at=excluded.sales_open_at,
    public_price_text=excluded.public_price_text,
    edition_note=excluded.edition_note,
    status='draft',
    external_delivery_enabled=false,
    payment_activation_allowed=false,
    updated_by=v_admin,
    updated_at=now(),
    ready_at=null,
    sent_at=null,
    recipient_count=0
  returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.admin_preorder_mark_announcement_ready(p_product_slug text)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_count integer;
begin
  v_admin := private.require_sinjira_admin_aal2();
  update public.preorder_sales_announcements a
  set status='ready', ready_at=now(), updated_at=now(), updated_by=v_admin,
      external_delivery_enabled=false, payment_activation_allowed=false
  from public.products p
  where a.product_id=p.id and p.slug=p_product_slug and a.campaign_key='sales_opening' and a.status='draft'
    and btrim(a.title)<>'' and btrim(a.body)<>'';
  get diagnostics v_count=row_count;
  return v_count=1;
end;
$$;

create or replace function public.admin_preorder_send_internal_announcement(p_product_slug text)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_admin uuid;
  v_announcement public.preorder_sales_announcements%rowtype;
  v_product_id uuid;
  v_count integer:=0;
begin
  v_admin := private.require_sinjira_admin_aal2();
  select p.id into v_product_id from public.products p where p.slug=p_product_slug limit 1;
  if v_product_id is null then raise exception using errcode='22023', message='UNKNOWN_PRODUCT'; end if;

  select * into v_announcement
  from public.preorder_sales_announcements a
  where a.product_id=v_product_id and a.campaign_key='sales_opening'
  for update;

  if v_announcement.id is null then raise exception using errcode='55000', message='ANNOUNCEMENT_NOT_FOUND'; end if;
  if v_announcement.status<>'ready' then raise exception using errcode='55000', message='ANNOUNCEMENT_NOT_READY'; end if;
  if v_announcement.external_delivery_enabled or v_announcement.payment_activation_allowed then
    raise exception using errcode='55000', message='PAID_OR_EXTERNAL_DELIVERY_FORBIDDEN';
  end if;

  insert into public.user_notifications(
    user_id,notification_type,title,body,related_entity_type,related_entity_id,action_path
  )
  select
    pp.user_id,
    'preorder_sales_opening',
    v_announcement.title,
    v_announcement.body,
    'preorder_sales_announcement',
    v_announcement.id,
    v_announcement.action_path
  from public.product_preorders pp
  where pp.product_id=v_product_id
    and pp.status='reserved'
    and pp.contact_when_sales_open=true;

  get diagnostics v_count=row_count;

  update public.preorder_sales_announcements
  set status='sent', sent_at=now(), updated_at=now(), updated_by=v_admin,
      recipient_count=v_count, external_delivery_enabled=false, payment_activation_allowed=false
  where id=v_announcement.id;

  return v_count;
end;
$$;

revoke all on function public.admin_preorder_overview(text) from public,anon,authenticated;
revoke all on function public.admin_preorder_list(text,text,text,integer,integer) from public,anon,authenticated;
revoke all on function public.admin_preorder_save_announcement_draft(text,text,text,text,timestamptz,text,text) from public,anon,authenticated;
revoke all on function public.admin_preorder_mark_announcement_ready(text) from public,anon,authenticated;
revoke all on function public.admin_preorder_send_internal_announcement(text) from public,anon,authenticated;

grant execute on function public.admin_preorder_overview(text) to authenticated;
grant execute on function public.admin_preorder_list(text,text,text,integer,integer) to authenticated;
grant execute on function public.admin_preorder_save_announcement_draft(text,text,text,text,timestamptz,text,text) to authenticated;
grant execute on function public.admin_preorder_mark_announcement_ready(text) to authenticated;
grant execute on function public.admin_preorder_send_internal_announcement(text) to authenticated;

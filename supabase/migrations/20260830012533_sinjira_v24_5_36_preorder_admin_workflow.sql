create table if not exists private.preorder_admin_workflow (
  preorder_id uuid primary key references public.product_preorders(id) on delete cascade,
  workflow_state text not null default 'pending' check (workflow_state in ('pending','ready_for_future_contact','completed')),
  updated_at timestamptz not null default now(),
  updated_by uuid null references auth.users(id) on delete set null
);

alter table private.preorder_admin_workflow enable row level security;
revoke all on table private.preorder_admin_workflow from public, anon, authenticated;
grant select, insert, update, delete on table private.preorder_admin_workflow to service_role;

create index if not exists preorder_admin_workflow_state_updated_idx
  on private.preorder_admin_workflow(workflow_state, updated_at desc);
create index if not exists preorder_admin_workflow_updated_by_idx
  on private.preorder_admin_workflow(updated_by);

create or replace function preorder_admin_internal.admin_preorder_workflow_by_reference(p_reservation_reference text)
returns table(
  reservation_reference text,
  workflow_state text,
  workflow_updated_at timestamptz
)
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_admin uuid;
  v_reference text;
begin
  v_admin := private.require_sinjira_admin_aal2();
  v_reference := upper(btrim(coalesce(p_reservation_reference,'')));
  if v_reference !~ '^PR-[0-9A-F]{16}$' then
    raise exception using errcode='22023', message='INVALID_RESERVATION_REFERENCE';
  end if;

  return query
  select pp.reservation_reference,
         coalesce(w.workflow_state,'pending')::text,
         w.updated_at
  from public.product_preorders pp
  left join private.preorder_admin_workflow w on w.preorder_id=pp.id
  where pp.reservation_reference=v_reference
  limit 1;
end;
$$;

create or replace function preorder_admin_internal.admin_preorder_set_workflow_state(
  p_reservation_reference text,
  p_workflow_state text
)
returns table(
  reservation_reference text,
  workflow_state text,
  workflow_updated_at timestamptz
)
language plpgsql
security definer
set search_path=''
as $$
declare
  v_admin uuid;
  v_reference text;
  v_state text;
  v_preorder_id uuid;
begin
  v_admin := private.require_sinjira_admin_aal2();
  v_reference := upper(btrim(coalesce(p_reservation_reference,'')));
  v_state := lower(btrim(coalesce(p_workflow_state,'')));

  if v_reference !~ '^PR-[0-9A-F]{16}$' then
    raise exception using errcode='22023', message='INVALID_RESERVATION_REFERENCE';
  end if;
  if v_state not in ('pending','ready_for_future_contact','completed') then
    raise exception using errcode='22023', message='INVALID_WORKFLOW_STATE';
  end if;

  select pp.id into v_preorder_id
  from public.product_preorders pp
  where pp.reservation_reference=v_reference
  limit 1;

  if v_preorder_id is null then
    raise exception using errcode='P0002', message='PREORDER_NOT_FOUND';
  end if;

  insert into private.preorder_admin_workflow(preorder_id,workflow_state,updated_at,updated_by)
  values(v_preorder_id,v_state,now(),v_admin)
  on conflict(preorder_id) do update
    set workflow_state=excluded.workflow_state,
        updated_at=excluded.updated_at,
        updated_by=excluded.updated_by;

  return query
  select v_reference, w.workflow_state, w.updated_at
  from private.preorder_admin_workflow w
  where w.preorder_id=v_preorder_id;
end;
$$;

create or replace function preorder_admin_internal.admin_preorder_workflow_queue(
  p_workflow_state text default null,
  p_limit integer default 100
)
returns table(
  reservation_reference text,
  user_label text,
  product_name text,
  quantity integer,
  preferred_format text,
  preorder_status text,
  fulfillment_preference text,
  workflow_state text,
  workflow_updated_at timestamptz
)
language plpgsql
stable
security definer
set search_path=''
as $$
declare
  v_admin uuid;
  v_state text;
  v_limit integer;
begin
  v_admin := private.require_sinjira_admin_aal2();
  v_state := nullif(lower(btrim(coalesce(p_workflow_state,''))), '');
  if v_state is not null and v_state not in ('pending','ready_for_future_contact','completed') then
    raise exception using errcode='22023', message='INVALID_WORKFLOW_STATE';
  end if;
  v_limit := greatest(1,least(coalesce(p_limit,100),200));

  return query
  select
    pp.reservation_reference,
    coalesce(nullif(pr.pseudo,''),nullif(pr.display_name,''),'Compte SINJIRA')::text,
    p.name::text,
    pp.quantity::integer,
    pp.preferred_format,
    pp.status,
    pp.fulfillment_preference,
    coalesce(w.workflow_state,'pending')::text,
    w.updated_at
  from public.product_preorders pp
  join public.products p on p.id=pp.product_id
  left join public.profiles pr on pr.user_id=pp.user_id
  left join private.preorder_admin_workflow w on w.preorder_id=pp.id
  where v_state is null or coalesce(w.workflow_state,'pending')=v_state
  order by coalesce(w.updated_at,pp.created_at) asc
  limit v_limit;
end;
$$;

create or replace function public.admin_preorder_workflow_by_reference(p_reservation_reference text)
returns table(reservation_reference text, workflow_state text, workflow_updated_at timestamptz)
language sql
stable
security invoker
set search_path=''
as $$ select * from preorder_admin_internal.admin_preorder_workflow_by_reference($1) $$;

create or replace function public.admin_preorder_set_workflow_state(p_reservation_reference text,p_workflow_state text)
returns table(reservation_reference text, workflow_state text, workflow_updated_at timestamptz)
language sql
security invoker
set search_path=''
as $$ select * from preorder_admin_internal.admin_preorder_set_workflow_state($1,$2) $$;

create or replace function public.admin_preorder_workflow_queue(p_workflow_state text default null,p_limit integer default 100)
returns table(reservation_reference text,user_label text,product_name text,quantity integer,preferred_format text,preorder_status text,fulfillment_preference text,workflow_state text,workflow_updated_at timestamptz)
language sql
stable
security invoker
set search_path=''
as $$ select * from preorder_admin_internal.admin_preorder_workflow_queue($1,$2) $$;

revoke all on function public.admin_preorder_workflow_by_reference(text) from public, anon;
revoke all on function public.admin_preorder_set_workflow_state(text,text) from public, anon;
revoke all on function public.admin_preorder_workflow_queue(text,integer) from public, anon;
grant execute on function public.admin_preorder_workflow_by_reference(text) to authenticated, service_role;
grant execute on function public.admin_preorder_set_workflow_state(text,text) to authenticated, service_role;
grant execute on function public.admin_preorder_workflow_queue(text,integer) to authenticated, service_role;

revoke all on function preorder_admin_internal.admin_preorder_workflow_by_reference(text) from public, anon;
revoke all on function preorder_admin_internal.admin_preorder_set_workflow_state(text,text) from public, anon;
revoke all on function preorder_admin_internal.admin_preorder_workflow_queue(text,integer) from public, anon;
grant execute on function preorder_admin_internal.admin_preorder_workflow_by_reference(text) to authenticated, service_role;
grant execute on function preorder_admin_internal.admin_preorder_set_workflow_state(text,text) to authenticated, service_role;
grant execute on function preorder_admin_internal.admin_preorder_workflow_queue(text,integer) to authenticated, service_role;
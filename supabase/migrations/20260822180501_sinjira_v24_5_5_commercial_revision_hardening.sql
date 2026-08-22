create or replace function public.preorder_commercial_plan_server_fields()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at := now();
  new.sales_enabled := false;
  new.checkout_enabled := false;
  new.payment_enabled := false;
  new.external_fulfillment_enabled := false;
  new.auto_conversion_allowed := false;

  if tg_op = 'UPDATE' then
    new.product_id := old.product_id;
    new.revision := old.revision;
    new.created_by := old.created_by;
    new.created_at := old.created_at;

    if old.status = 'published' then
      if new.status is distinct from 'superseded'
         or (to_jsonb(new) - array['status','superseded_at','updated_by','updated_at']::text[])
            is distinct from
            (to_jsonb(old) - array['status','superseded_at','updated_by','updated_at']::text[]) then
        raise exception using errcode = '22023', message = 'COMMERCIAL_PLAN_IMMUTABLE';
      end if;
    elsif old.status in ('superseded','cancelled') then
      if (to_jsonb(new) - array['updated_at']::text[])
         is distinct from
         (to_jsonb(old) - array['updated_at']::text[]) then
        raise exception using errcode = '22023', message = 'COMMERCIAL_PLAN_IMMUTABLE';
      end if;
    end if;
  end if;

  return new;
end;
$$;

revoke all on function public.preorder_commercial_plan_server_fields() from public, anon, authenticated;

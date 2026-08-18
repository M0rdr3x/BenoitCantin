do $$
declare
  v_definition text;
  v_old constant text := 'SINJIRA — Livre II (titre à confirmer)';
  v_new constant text := 'SINJIRA — Livre II : Le Sang du Sauveur';
begin
  select pg_get_functiondef('public.ensure_sinjira_owner_character()'::regprocedure)
    into v_definition;

  if position(v_old in v_definition) > 0 then
    execute replace(v_definition, v_old, v_new);
  elsif position(v_new in v_definition) = 0 then
    raise exception 'ensure_sinjira_owner_character(): Book II title marker not found';
  end if;
end
$$;

with owner_account as (
  select id
  from auth.users
  where lower(coalesce(email, '')) = 'kingtyrano@gmail.com'
  limit 1
)
update public.characters c
set
  novel_note = case
    when c.novel_note = 'SINJIRA — Livre II (titre à confirmer)'
      then 'SINJIRA — Livre II : Le Sang du Sauveur'
    else c.novel_note
  end,
  bible = case
    when coalesce(c.bible->>'placement', '') = 'SINJIRA — Livre II (titre à confirmer)'
      then jsonb_set(
        coalesce(c.bible, '{}'::jsonb),
        '{placement}',
        to_jsonb('SINJIRA — Livre II : Le Sang du Sauveur'::text),
        true
      )
    else c.bible
  end,
  updated_at = now()
from owner_account o
where c.user_id = o.id
  and lower(coalesce(c.public_name, '')) = 'abysstime'
  and (
    c.novel_note = 'SINJIRA — Livre II (titre à confirmer)'
    or coalesce(c.bible->>'placement', '') = 'SINJIRA — Livre II (titre à confirmer)'
  );

create or replace function public.sinjira_owner_book2_title_health()
returns jsonb
language plpgsql
stable
security definer
set search_path = public, auth
as $$
declare
  v_owner uuid;
  v_stale_rows integer := 0;
  v_definition text;
begin
  select id into v_owner
  from auth.users
  where lower(coalesce(email, '')) = 'kingtyrano@gmail.com'
  limit 1;

  select count(*) into v_stale_rows
  from public.characters c
  where c.user_id = v_owner
    and lower(coalesce(c.public_name, '')) = 'abysstime'
    and (
      c.novel_note = 'SINJIRA — Livre II (titre à confirmer)'
      or coalesce(c.bible->>'placement', '') = 'SINJIRA — Livre II (titre à confirmer)'
    );

  select pg_get_functiondef('public.ensure_sinjira_owner_character()'::regprocedure)
    into v_definition;

  return jsonb_build_object(
    'ok',
      v_owner is not null
      and v_stale_rows = 0
      and position('SINJIRA — Livre II (titre à confirmer)' in v_definition) = 0
      and position('SINJIRA — Livre II : Le Sang du Sauveur' in v_definition) > 0,
    'version', '24.4.58',
    'owner_found', v_owner is not null,
    'stale_rows', v_stale_rows,
    'repair_function_official_title',
      position('SINJIRA — Livre II : Le Sang du Sauveur' in v_definition) > 0
  );
end;
$$;

revoke all on function public.sinjira_owner_book2_title_health() from public, anon, authenticated;
grant execute on function public.sinjira_owner_book2_title_health() to service_role;

comment on function public.sinjira_owner_book2_title_health() is
  'SINJIRA V24.4.58 — verifies AbyssTime and owner repair use the official Book II title.';

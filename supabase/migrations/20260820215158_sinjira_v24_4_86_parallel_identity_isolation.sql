create table if not exists private.parallel_identities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source_character_id uuid not null references public.characters(id) on delete cascade,
  public_name text not null check (char_length(btrim(public_name)) between 2 and 80),
  public_bio text null check (public_bio is null or char_length(public_bio) <= 600),
  status text not null default 'active' check (status in ('active','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id)
);

alter table private.parallel_identities enable row level security;
revoke all on table private.parallel_identities from anon, authenticated;

create index if not exists parallel_identities_character_idx
  on private.parallel_identities(source_character_id);

create or replace function public.parallel_my_identity()
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_character uuid;
  v_identity private.parallel_identities%rowtype;
begin
  if v_user is null then
    raise exception 'AUTH_REQUIRED';
  end if;

  select c.id into v_character
  from public.characters c
  where c.user_id = v_user
    and c.status <> 'archived'
    and c.visible_to_user = true
  order by c.updated_at desc
  limit 1;

  if v_character is null then
    return jsonb_build_object('ok', false, 'code', 'PARALLEL_CHARACTER_NOT_READY');
  end if;

  insert into private.parallel_identities(user_id, source_character_id, public_name)
  select v_user, v_character, coalesce(nullif(btrim(c.public_name),''), 'Identité parallèle')
  from public.characters c
  where c.id = v_character
  on conflict(user_id) do update
    set source_character_id = excluded.source_character_id,
        updated_at = case
          when private.parallel_identities.source_character_id is distinct from excluded.source_character_id then now()
          else private.parallel_identities.updated_at
        end
  returning * into v_identity;

  return jsonb_build_object(
    'ok', true,
    'identity_id', v_identity.id,
    'public_name', v_identity.public_name,
    'public_bio', v_identity.public_bio,
    'status', v_identity.status
  );
end;
$$;

revoke all on function public.parallel_my_identity() from public, anon;
grant execute on function public.parallel_my_identity() to authenticated;

create or replace function public.parallel_set_my_identity(p_public_name text, p_public_bio text default null)
returns jsonb
language plpgsql
security definer
set search_path = public, private, auth
as $$
declare
  v_user uuid := auth.uid();
  v_name text := btrim(coalesce(p_public_name,''));
  v_bio text := nullif(btrim(coalesce(p_public_bio,'')), '');
  v_current jsonb;
begin
  if v_user is null then
    raise exception 'AUTH_REQUIRED';
  end if;
  if char_length(v_name) < 2 or char_length(v_name) > 80 then
    raise exception 'PARALLEL_NAME_LENGTH';
  end if;
  if v_bio is not null and char_length(v_bio) > 600 then
    raise exception 'PARALLEL_BIO_LENGTH';
  end if;
  if not public.sinjira_content_allowed(v_user, v_name) then
    raise exception 'PARALLEL_NAME_NOT_ALLOWED';
  end if;
  if v_bio is not null and not public.sinjira_content_allowed(v_user, v_bio) then
    raise exception 'PARALLEL_BIO_NOT_ALLOWED';
  end if;

  v_current := public.parallel_my_identity();
  if coalesce((v_current->>'ok')::boolean, false) is not true then
    return v_current;
  end if;

  update private.parallel_identities
  set public_name = v_name,
      public_bio = v_bio,
      updated_at = now()
  where user_id = v_user
  returning jsonb_build_object(
    'ok', true,
    'identity_id', id,
    'public_name', public_name,
    'public_bio', public_bio,
    'status', status
  ) into v_current;

  return v_current;
end;
$$;

revoke all on function public.parallel_set_my_identity(text,text) from public, anon;
grant execute on function public.parallel_set_my_identity(text,text) to authenticated;

insert into private.parallel_identities(user_id, source_character_id, public_name, public_bio)
select u.id,
       c.id,
       'Seth Tremblay',
       'Identité narrative du Monde parallèle SINJIRA™. Distincte du compte, du Registre et des personnages des romans.'
from auth.users u
cross join lateral (
  select c2.id
  from public.characters c2
  where c2.user_id = u.id
    and c2.status <> 'archived'
    and c2.visible_to_user = true
  order by c2.updated_at desc
  limit 1
) c
where lower(coalesce(u.email,'')) = 'kingtyrano@gmail.com'
on conflict(user_id) do update
set source_character_id = excluded.source_character_id,
    public_name = 'Seth Tremblay',
    public_bio = excluded.public_bio,
    status = 'active',
    updated_at = now();

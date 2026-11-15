-- P0 SINJIRA : rotation transactionnelle des liens Histoire de vie.
-- Migration future : aucune modification de l'historique appliqué.
-- Le rôle serveur a déjà authentifié l'administrateur MFA AAL2 dans l'Edge.
create or replace function public.service_life_story_rotate_delivery_links(
  p_export_id uuid,
  p_token_hashes jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_export public.life_story_exports%rowtype;
  v_count integer;
  v_expires_at timestamptz;
  v_inserted integer;
begin
  if coalesce(auth.jwt()->>'role','') <> 'service_role' then
    raise exception 'SERVICE_ROLE_REQUIRED';
  end if;
  if p_export_id is null or pg_catalog.jsonb_typeof(p_token_hashes) <> 'array' then
    raise exception 'INVALID_DELIVERY_LINKS';
  end if;
  v_count := pg_catalog.jsonb_array_length(p_token_hashes);
  if v_count < 1 or v_count > 128 then
    raise exception 'INVALID_DELIVERY_LINKS';
  end if;
  if exists (
    select 1
    from pg_catalog.jsonb_array_elements(p_token_hashes) as hash(value)
    where pg_catalog.jsonb_typeof(hash.value) <> 'string'
       or hash.value #>> '{}' !~ '^[a-f0-9]{64}$'
  ) then
    raise exception 'INVALID_DELIVERY_LINKS';
  end if;

  -- FOR UPDATE sérialise les rotations concurrentes d'un même export.
  select e.* into v_export
  from public.life_story_exports as e
  where e.id = p_export_id
  for update;
  if not found or v_export.status <> 'generated'
      or v_export.storage_bucket <> 'sinjira-life-story-exports'
      or coalesce(v_export.storage_path, '') = ''
      or v_export.source_boundary <> 'life_story_only'
      or v_export.registry_access_prohibited is distinct from true then
    raise exception 'EXPORT_NOT_GENERATED';
  end if;
  if pg_catalog.jsonb_typeof(v_export.recipients_snapshot) <> 'array'
      or pg_catalog.jsonb_array_length(v_export.recipients_snapshot) <> v_count then
    raise exception 'RECIPIENT_SNAPSHOT_MISMATCH';
  end if;
  v_expires_at := pg_catalog.clock_timestamp() + interval '30 days';

  -- DELETE + INSERT partagent une transaction : toute erreur rollback
  -- la suppression et conserve les liens précédents. Jamais de token brut.
  delete from public.life_story_delivery_links as l
  where l.export_id = p_export_id;

  insert into public.life_story_delivery_links
    (export_id, recipient_index, recipient_label, token_hash, expires_at, max_downloads)
  select
    p_export_id,
    (h.ordinality - 1)::integer,
    coalesce(
      nullif(
        pg_catalog.left(
          pg_catalog.btrim(
            v_export.recipients_snapshot -> (h.ordinality - 1)::integer ->> 'recipient_label'
          ), 160
        ), ''
      ),
      'Destinataire ' || h.ordinality::text
    ),
    h.token_hash,
    v_expires_at,
    3
  from pg_catalog.jsonb_array_elements_text(p_token_hashes)
    with ordinality as h(token_hash, ordinality)
  order by h.ordinality;
  get diagnostics v_inserted = row_count;
  if v_inserted <> v_count then
    raise exception 'DELIVERY_LINK_ROTATION_FAILED';
  end if;

  return pg_catalog.jsonb_build_object(
    'link_count', v_inserted,
    'expires_at', v_expires_at
  );
end;
$function$;

revoke all on function public.service_life_story_rotate_delivery_links(uuid,jsonb)
  from public, anon, authenticated;
grant execute on function public.service_life_story_rotate_delivery_links(uuid,jsonb)
  to service_role;
comment on function public.service_life_story_rotate_delivery_links(uuid,jsonb) is
  'Rotation sérialisée et transactionnelle des jetons de remise; service_role uniquement, aucune clé de lien en clair dans SQL.';

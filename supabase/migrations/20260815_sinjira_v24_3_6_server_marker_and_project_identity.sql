-- SINJIRA™ V24.3.6 — marqueur de synchronisation serveur + identité de projet
-- À appliquer APRÈS :
--   20260814_sinjira_v24_foundation.sql
--   20260815_sinjira_v24_1_owner_and_live_fixes.sql
--   20260815_sinjira_v24_3_1_owner_repair_and_fracture_access.sql
--
-- Le « slug » reste un identifiant TECHNIQUE interne pour les URLs et les RPC.
-- L'identifiant lisible montré dans l'administration est le nom officiel du projet.

create or replace function public.get_sinjira_server_version()
returns text
language sql
stable
security definer
set search_path=public
as $$
  select '24.3.6'::text;
$$;
revoke all on function public.get_sinjira_server_version() from public,anon;
grant execute on function public.get_sinjira_server_version() to authenticated,service_role;

-- Identité officielle demandée : « Fracture du Réseau-Mère ».
-- Le slug technique fracture-du-reseau-mere reste inchangé afin de ne casser
-- ni les URLs, ni les licences, ni les parties existantes.
do $$
begin
  if to_regclass('public.projects') is not null then
    update public.projects
    set name='Fracture du Réseau-Mère', updated_at=now()
    where slug='fracture-du-reseau-mere'
      and name is distinct from 'Fracture du Réseau-Mère';
  end if;

  if to_regclass('public.products') is not null then
    update public.products
    set name='Fracture du Réseau-Mère — accès en ligne'
    where slug='fracture-du-reseau-mere'
      and name is distinct from 'Fracture du Réseau-Mère — accès en ligne';
  end if;
end $$;

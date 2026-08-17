-- SINJIRA™ V24.4.44 — restaure l'API self-only de cohorte après la réparation propriétaire.
-- Les membres utilisent sinjira_my_age_band(); la variante paramétrée reste interne.

revoke execute on function public.sinjira_age_band(uuid) from public, anon, authenticated;
grant execute on function public.sinjira_age_band(uuid) to service_role;

grant execute on function public.sinjira_my_age_band() to authenticated, service_role;

-- SINJIRA™ V24.4.12 — retrait de la surface RPC parentale historique.
-- Les fonctions restent physiquement présentes pour compatibilité/rollback, mais ne sont plus
-- appelables directement par le navigateur. L'API V24 active est get_guardian_youth_contacts().

revoke execute on function public.guardian_minor_contact_log(uuid) from authenticated;
revoke execute on function public.guardian_minor_contact_summary(uuid) from authenticated;
revoke execute on function public.sinjira_guardian_can_monitor(uuid,uuid) from authenticated;
revoke execute on function public.sinjira_social_compatible(uuid,uuid) from authenticated;

-- Helpers internes : appelés uniquement à l'intérieur de fonctions SECURITY DEFINER.
revoke execute on function public.sinjira_parent_can_supervise(uuid,uuid) from authenticated;
revoke execute on function public.sinjira_phone_factor_verified(uuid) from authenticated;

grant execute on function public.guardian_minor_contact_log(uuid) to service_role;
grant execute on function public.guardian_minor_contact_summary(uuid) to service_role;
grant execute on function public.sinjira_guardian_can_monitor(uuid,uuid) to service_role;
grant execute on function public.sinjira_social_compatible(uuid,uuid) to service_role;
grant execute on function public.sinjira_parent_can_supervise(uuid,uuid) to service_role;
grant execute on function public.sinjira_phone_factor_verified(uuid) to service_role;

comment on function public.guardian_minor_contact_log(uuid) is
  'API V22 historique retirée de la surface client en V24.4.12. Utiliser get_guardian_youth_contacts().';
comment on function public.guardian_minor_contact_summary(uuid) is
  'API V22 historique retirée de la surface client en V24.4.12. Utiliser get_guardian_youth_contacts().';
comment on function public.sinjira_guardian_can_monitor(uuid,uuid) is
  'Helper V22 historique non exposé aux clients depuis V24.4.12.';
comment on function public.sinjira_social_compatible(uuid,uuid) is
  'Alias historique non exposé aux clients depuis V24.4.12. La règle canonique est sinjira_can_social_interact().';
comment on function public.sinjira_parent_can_supervise(uuid,uuid) is
  'Helper interne de get_guardian_youth_contacts(); non exposé directement aux clients.';
comment on function public.sinjira_phone_factor_verified(uuid) is
  'Helper interne MFA; non exposé directement aux clients.';

-- SINJIRA™ V24.4.12 — retrait de la surface RPC parentale historique.
-- Les fonctions restent physiquement présentes pour compatibilité/rollback, mais ne sont plus
-- appelables directement par le navigateur. L'API V24 active est get_guardian_youth_contacts().
--
-- V24.4.21 reconstruction à froid : certaines installations historiques ne matérialisaient
-- pas encore toutes ces RPC au moment de cette migration. Les ACL sont donc appliquées
-- seulement lorsque la signature existe déjà; les migrations ultérieures recréent les
-- fonctions actives avec leurs ACL canoniques.

do $$
declare
  sig text;
begin
  foreach sig in array array[
    'public.guardian_minor_contact_log(uuid)',
    'public.guardian_minor_contact_summary(uuid)',
    'public.sinjira_guardian_can_monitor(uuid,uuid)',
    'public.sinjira_social_compatible(uuid,uuid)',
    'public.sinjira_parent_can_supervise(uuid,uuid)',
    'public.sinjira_phone_factor_verified(uuid)'
  ] loop
    if to_regprocedure(sig) is not null then
      execute format('revoke execute on function %s from authenticated', sig);
      execute format('grant execute on function %s to service_role', sig);
    end if;
  end loop;
end $$;

do $$ begin
  if to_regprocedure('public.guardian_minor_contact_log(uuid)') is not null then
    comment on function public.guardian_minor_contact_log(uuid) is
      'API V22 historique retirée de la surface client en V24.4.12. Utiliser get_guardian_youth_contacts().';
  end if;
  if to_regprocedure('public.guardian_minor_contact_summary(uuid)') is not null then
    comment on function public.guardian_minor_contact_summary(uuid) is
      'API V22 historique retirée de la surface client en V24.4.12. Utiliser get_guardian_youth_contacts().';
  end if;
  if to_regprocedure('public.sinjira_guardian_can_monitor(uuid,uuid)') is not null then
    comment on function public.sinjira_guardian_can_monitor(uuid,uuid) is
      'Helper V22 historique non exposé aux clients depuis V24.4.12.';
  end if;
  if to_regprocedure('public.sinjira_social_compatible(uuid,uuid)') is not null then
    comment on function public.sinjira_social_compatible(uuid,uuid) is
      'Alias historique non exposé aux clients depuis V24.4.12. La règle canonique est sinjira_can_social_interact().';
  end if;
  if to_regprocedure('public.sinjira_parent_can_supervise(uuid,uuid)') is not null then
    comment on function public.sinjira_parent_can_supervise(uuid,uuid) is
      'Helper interne de get_guardian_youth_contacts(); non exposé directement aux clients.';
  end if;
  if to_regprocedure('public.sinjira_phone_factor_verified(uuid)') is not null then
    comment on function public.sinjira_phone_factor_verified(uuid) is
      'Helper interne MFA; non exposé directement aux clients.';
  end if;
end $$;

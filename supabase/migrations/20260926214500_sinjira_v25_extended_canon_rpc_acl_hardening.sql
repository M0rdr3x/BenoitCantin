-- SINJIRA V25 — ACL des RPC Canon étendu réservées au serveur
-- Forward-only : l'administration web passe déjà par admin-sinjira-v18,
-- qui authentifie JWT + admin + AAL2 puis utilise le client service_role.
-- Le navigateur authenticated n'a donc aucune raison d'exécuter directement
-- ces SECURITY DEFINER publics.

revoke all on function public.admin_sinjira_story_continuity_check(uuid)
from public,anon,authenticated;
grant execute on function public.admin_sinjira_story_continuity_check(uuid)
to service_role;

revoke all on function public.admin_sinjira_promote_extended_story(uuid)
from public,anon,authenticated;
grant execute on function public.admin_sinjira_promote_extended_story(uuid)
to service_role;

revoke all on function public.admin_sinjira_publish_extended_story(uuid,text)
from public,anon,authenticated;
grant execute on function public.admin_sinjira_publish_extended_story(uuid,text)
to service_role;

revoke all on function public.admin_sinjira_unpublish_extended_story(uuid)
from public,anon,authenticated;
grant execute on function public.admin_sinjira_unpublish_extended_story(uuid)
to service_role;

revoke all on function public.admin_sinjira_migrate_canon_source_references(uuid,uuid)
from public,anon,authenticated;
grant execute on function public.admin_sinjira_migrate_canon_source_references(uuid,uuid)
to service_role;

revoke all on function public.admin_sinjira_story_validation_check(uuid)
from public,anon,authenticated;
grant execute on function public.admin_sinjira_story_validation_check(uuid)
to service_role;

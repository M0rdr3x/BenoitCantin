-- SINJIRA™ V24.4.12 — réduire les privilèges des helpers qui peuvent s'appuyer sur RLS.

-- 1) Acceptation des règles : la table est RLS propriétaire, aucun besoin de DEFINER.
alter function public.has_accepted_community_rules(uuid) security invoker;
revoke all on table public.community_rule_acceptances from anon;
revoke truncate,references,trigger on table public.community_rule_acceptances from authenticated;
grant select,insert,update,delete on table public.community_rule_acceptances to authenticated;

-- 2) Catalogue produit : lecture active seulement. Écritures réservées au serveur.
revoke all on table public.products from anon;
revoke insert,update,delete,truncate,references,trigger on table public.products from authenticated;
grant select on table public.products to authenticated;

-- 3) Entitlements : un membre ne lit que ses propres lignes via RLS.
revoke all on table public.user_entitlements from anon;
revoke insert,update,delete,truncate,references,trigger on table public.user_entitlements from authenticated;
grant select on table public.user_entitlements to authenticated;

-- La fonction garde son contrôle anti-énumération, mais laisse désormais RLS contrôler
-- la lecture des entitlements lorsqu'elle est appelée directement par un membre.
alter function public.has_sinjira_product(text,uuid) security invoker;

-- Les capacités du compte ne lisent aucune table directement : elles délèguent
-- l'identification propriétaire à is_sinjira_owner(auth.uid()).
alter function public.get_sinjira_account_capabilities() security invoker;

comment on function public.has_accepted_community_rules(uuid) is
  'SECURITY INVOKER : vérifie l’acceptation des règles via la RLS propriétaire du compte.';
comment on function public.has_sinjira_product(text,uuid) is
  'SECURITY INVOKER : RLS entitlements + garde anti-énumération; le propriétaire reste reconnu via is_sinjira_owner().';
comment on function public.get_sinjira_account_capabilities() is
  'SECURITY INVOKER : assemble les capacités du compte courant; l’identité propriétaire est vérifiée par is_sinjira_owner().';

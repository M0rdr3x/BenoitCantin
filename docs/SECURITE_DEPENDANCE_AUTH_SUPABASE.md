# Sécurité de la dépendance navigateur Supabase

## Risque initial

Le module d'authentification `assets/js/sinjira-supabase.js` importait
`@supabase/supabase-js@2/+esm` depuis jsDelivr. Cette URL résout une
**version majeure flottante**, permettant une mise à niveau 2.x sans revue
du dépôt ni test d'intégration. Elle est exécutée par les parcours de
session, connexion, renouvellement et accès aux données privées SINJIRA.

Cette exposition est un **risque de chaîne d'approvisionnement**, pas une
preuve de compromission du fournisseur CDN.

## Correction initiale

Le module importe désormais une version exacte :
`https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/+esm`.

- Version 2.119.0 vérifiée auprès de l'historique public du projet
  (release du **4 novembre 2026**).
- Résolution HTTPS vérifiée en lecture seule sur jsDelivr le
  **7 novembre 2026** : la réponse annonce explicitement
  `/npm/@supabase/supabase-js@2.119.0/dist/index.mjs`.
  Les premiers imports `@supabase/*` observés sont également
  versionnés, sans preuve d'intégrité cryptographique de tout le graphe.
- `scripts/validate_browser_supabase_supply_chain.py` refuse les versions
  flottantes `@2`, `@latest`, `@^2`, les versions partielles,
  les versions imprévues, HTTP clair et les hôtes CDN alternatifs pour
  le SDK dans les scripts et pages parcourus.
- Le workflow CI `Sécurité — intégrité des workflows GitHub Actions`
  lance ce garde sur les changements de scripts et pages pertinents.

## Limites et validation avant publication

**Épingler une version n'est pas une preuve d'intégrité du CDN.** jsDelivr
produit dynamiquement les fichiers `+esm` et avertit de ne pas appliquer
une empreinte SRI calculée une fois à ces sorties. La solution cible pour
les parcours d'authentification est un **bundle local**, produit à partir
d'un lockfile approuvé, d'un inventaire de dépendances, d'un hash
d'artefact et de tests de compatibilité avant livraison.

Pour autoriser la mise en ligne de cette modification, tester dans un
navigateur réel les parcours SINJIRA suivants en environnement adapté :
connexion, déconnexion, expiration et rafraîchissement de session,
mot de passe oublié/réinitialisé, MFA, appels Edge et accès privés RLS.
Aucun jeton de compte réel ne doit être capturé ou publié dans les
journaux de CI. Vérifier après déploiement le module effectivement servi.

Ne jamais mettre dans le navigateur `service_role`, les secrets de
fonction Edge ou une clé de base privilégiée. La sécurité des opérations
reste imposée côté serveur par Auth, RLS, contrôles de rôle et sessions.
Le contrôle CDN ne remplace pas les blocages GitHub de publication
et de protection de branche (#450 et #135).

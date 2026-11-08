# Sécurité — surveillance de la frontière de publication publique

Le site `www.benoitcantin.com` doit servir uniquement les pages et médias
explicitement approuvés. La présence des sources GitHub dans un dépôt public
ne justifie **pas** leur copie dans l'artefact d'hébergement.

## Contrôle automatisé

- `scripts/check_live_public_security_boundary.py --self-test` :
  validation **sans réseau**, y compris 200/206, redirections, 429, 5xx,
  absent/timeout, et disparition de pages légitimes.
- `scripts/check_live_public_security_boundary.py --live` :
  **16 GET non authentifiés et non intrusifs** sur une unique origine HTTPS,
  `www.benoitcantin.com`. L'outil ne lit ni n'imprime les corps HTTP,
  ne suit aucune redirection et ne lit aucune donnée de compte.
- `.github/workflows/live-public-security-boundary.yml` :
  auto-test sur les PR pertinentes et la branche principale, contrôle
  réel **quotidien** et déclenchement manuel, permissions GitHub minimales,
  actions épinglées à leur SHA. Toute réponse 200 sur un des 12 chemins
  techniques fait échouer le job. Un 3xx, 429 ou 5xx n'est **pas** confondu
  avec un refus d'accès : l'état est à diagnostiquer.
- Réponses normales pour un chemin technique : HTTP 403, 404 ou 410.
  La page d'accueil, security.txt, SINJIRA et Projet NOVA doivent répondre
  HTTP 200.

## Réception initiale du 7 novembre 2026

Vérifications **publiques en lecture seule** : `/supabase/config.toml`,
`/tests/e2e/test_public_site.py` et `/mobile-native/App.tsx` retournent
toutes HTTP 404. `/.well-known/security.txt` et la page d'accueil
sont servies. Ce relevé est borné à ces chemins et à cet instant :
il **ne prouve pas** l'inaccessibilité de toutes les sources du dépôt.

## Opérations en cas d'alerte

1. Conserver le numéro du run, la date et le **code HTTP**, sans publier
   de corps techniques, de valeurs d'environnement ni de secrets.
2. Comparer l'artefact GitHub Pages réellement déployé à l'artefact isolé
   `_site`, vérifier `.nojekyll` et la configuration Pages.
3. Si une route technique est exposée, restaurer le confinement, vérifier
   l'absence de secrets publiés et faire tourner les identifiants touchés
   **seulement si** un secret réel était présent et exposé.
4. Après toute correction, exécuter manuellement le job `--live`, puis
   documenter la clôture dans l'issue de publication #450.

**Limites :** surveillance d'une liste représentative, pas un pentest,
pas une analyse exhaustive des fichiers, des API, des sous-domaines,
des dépendances npm ni des en-têtes HTTP. La bascule vers l'artefact public
isolé et l'activation de la protection serveur de `main` restent suivies
dans les issues #450 et #135. Le moniteur ne peut pas remplacer ces
configurations administrateur.

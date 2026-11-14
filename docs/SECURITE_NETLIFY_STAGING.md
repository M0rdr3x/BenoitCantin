# SINJIRA — Préconditions de sécurité du staging Netlify

**Statut : NO-GO jusqu'à la configuration GitHub par un administrateur.**
Ce document accompagne le contrôle fail-closed du workflow
`.github/workflows/deploy-netlify-staging.yml` et ne prouve pas que
les protections du serveur GitHub sont actuellement activées.

## Risque vérifié

Le 12 novembre 2026, l'API GitHub signalait `protected: false` pour
`main` et `a1/web-release-transparency`. La vérification côté workflow,
via `GITHUB_REF_PROTECTED`, refuse donc le staging tant qu'une protection
ou un ruleset ne protège pas la branche effectivement exécutée.

Attention : le simple indicateur `GITHUB_REF_PROTECTED=true` **ne prouve
pas** qu'une révision par un tiers, des checks obligatoires ou une interdiction
de contournement sont configurés. Un utilisateur pouvant réécrire librement
le fichier workflow sur une branche non protégée pourrait retirer son garde.
**La règle serveur est la frontière de sécurité décisive.**

## Actions obligatoires de l'administrateur GitHub

1. Dans **Settings > Rules > Rulesets**, activer un ruleset de branche
   ciblant `a1/web-release-transparency` : refuser les pushes directs,
   exiger une PR avec revue indépendante et des contrôles CI requis,
   bloquer les force-pushes et la suppression, limiter les exceptions.
   Appliquer une gouvernance équivalente à `main`.
2. Dans **Settings > Environments**, créer/configurer
   `netlify-staging` : approbateur requis distinct de l'initiateur,
   activer **Prevent self-review**, limiter les branches de déploiement
   à `a1/web-release-transparency` et désactiver les contournements
   administrateur là où disponible.
3. Migrer `NETLIFY_AUTH_TOKEN` et `NETLIFY_SITE_ID` vers les secrets
   de cet environnement après revue. S'assurer que les anciennes valeurs
   conservées au niveau dépôt ne confèrent pas des droits inutiles.
   Limiter le jeton à un site et des droits de staging lorsque Netlify
   permet cette restriction. Révoquer les jetons non nécessaires.
4. Examiner la **chaîne d'approvisionnement npm Netlify** :
   le workflow installe `netlify-cli@27.10.2` dans un répertoire temporaire
   **avant toute étape recevant les identifiants**. Il passe
   `--ignore-scripts` et neutralise les fichiers npmrc utilisateur/global,
   puis vérifie la version du paquet avant utilisation. Les deux étapes
   avec secrets invoquent le binaire local et définissent
   `NPM_CONFIG_OFFLINE=true`, sans `npx` ni `npm install`.
   **Risque restant :** les dépendances transitives ne sont pas encore
   figées par un `package-lock.json` avec empreintes d'intégrité revues,
   et le binaire installé s'exécute toujours avec un jeton lors du déploiement.
   Pour une chaîne reproductible, fournir un lockfile authentique généré
   depuis le registre officiel, revu indépendamment, puis remplacer
   l'installation dynamique par `npm ci --ignore-scripts`.
   Ne pas fabriquer d'empreintes ni assimiler ce correctif à une
   attestation complète des dépendances.
5. Faire relire la PR, valider la CI du commit exact et tester en
   staging avec des données fictives. Ne lancer aucune promotion live
   par déduction d'un test réussi.

## Invariants du workflow versionné

- Une seule branche acceptée : `refs/heads/a1/web-release-transparency`.
- Refus explicite avant checkout si `GITHUB_REF_PROTECTED` est absent
  ou différent de `true`.
- Job lié à l'environnement `netlify-staging`.
- Credentials uniquement injectés dans les trois étapes autorisées;
  **jamais dans la ligne de commande CLI ni les résumés GitHub**.
- Installation npm unique, avec scripts d'installation désactivés et sans
  secrets; exécution du binaire local seulement après installation,
  hors gestionnaire de paquets, avec npm configuré hors ligne.
- Avant toute activation réelle du staging : essai en environnement isolé
  pour confirmer que la CLI fonctionne sans scripts d'installation,
  audit de dépendances npm/lockfile, révision de la configuration serveur.
- Deux déploiements de préproduction, aucun `--prod`, SHA de source
  explicitement vérifié, preuves HTTP des deux candidats.

Le validateur `scripts/validate_netlify_staging_secret_scope.py` et
son workflow de CI protègent ces invariants **du code versionné**.
Ils ne peuvent pas activer eux-mêmes une protection de branche,
une règle de revue de l'environnement, ou garantir l'intégrité du
registre npm et des dépendances transitives.

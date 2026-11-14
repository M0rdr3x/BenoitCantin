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
4. **Vérifier la chaîne d'approvisionnement npm Netlify verrouillée** :
   - Le manifeste `tools/netlify-cli/package.json` fixe uniquement `netlify-cli@27.19.0`.
   - `tools/netlify-cli/package-lock.json` (lockfile npm v3) a été produit
     par GitHub Actions **sans secret** depuis le registre npm officiel.
     Il fige **1 015 dépendances** avec des URL HTTPS de ce registre et des
     empreintes d'intégrité SRI SHA-512.
   - Le SHA-256 de ce lockfile est
     `6a21a830c8f3adc799db04bfca9a8c09ea6d864b6903e4f333c7abfdd9535bd4`.
     `scripts/validate_netlify_cli_lock.py` vérifie l'empreinte globale,
     le registre autorisé, les SRI, les versions et des mutations adversariales.
   - Avant toute exposition des secrets, le workflow valide ce contrat,
     copie manifest/lockfile dans le répertoire temporaire, puis exécute
     `npm ci --ignore-scripts --no-audit --no-fund` avec des configurations
     npm vides et distinctes. Le binaire local est soumis à un test
     `--version`. Pendant les deux déploiements, aucun `npx` ni
     `npm install` n'est exécuté et npm est configuré hors ligne.
   - **Risque restant :** un lockfile authentique et contrôlé empêche
     les variations non autorisées du graphe, mais ne prouve pas qu'un paquet
     d'origine est exempt de code malveillant. La revue des éditeurs et
     dépendances, l'analyse des vulnérabilités publiées et la limitation
     des jetons restent requises.
   - **Audit des vulnérabilités (14 novembre 2026)** : la version précédente
     `netlify-cli@27.10.2` comptait 2 avis élevés, 15 modérés et 2 faibles
     selon npm audit. La mise à jour `27.19.0` a **éliminé les deux avis
     élevés** : 0 critique, 0 élevé, mais **16 modérés et 2 faibles**
     restent à analyser. Ce résultat décrit uniquement le graphe npm et
     ne prouve pas une absence de risque en exécution.
   - Le 14 novembre 2026, `npm audit fix --package-lock-only`, exécuté
     **sans scripts et sans secrets** sur une copie isolée du verrouillage
     `27.19.0`, n'a **corrigé aucune vulnérabilité supplémentaire** :
     16 modérées et 2 faibles subsistent, avec un SHA-256 identique.
     Des conseils de npm suggèrent pour plusieurs chemins une régression
     vers `netlify-cli@2.23.0` avec rupture de version majeure : cette
     rétrogradation n'a pas été appliquée, car ses effets sur la compatibilité
     et la sécurité ne sont pas établis. Examiner manuellement les avis
     ou migrer vers un outillage moins exposé après tests indépendants.
   - La CI et le staging exécutent `npm audit --json --omit=dev` avec
     `scripts/validate_netlify_cli_audit.py`. **Tout avis élevé ou
     critique, toute absence de rapport valide ou toute erreur d'audit
     bloque** le job avant injection des identifiants Netlify. Le scan
     GitHub Actions est également programmé chaque lundi.
   - `.github/dependabot.yml` couvre maintenant `/tools/netlify-cli`
     par des PR hebdomadaires sans fusion automatique. Les nouvelles
     versions doivent être revues, puis la valeur attendue du SHA-256,
     le nombre de paquets et l'empreinte SRI de la CLI doivent être
     réexaminés avant la mise à jour du garde verrouillé.
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
- Audit des avis de sécurité npm exécuté dans une étape sans secrets,
  après npm ci et avant leur injection ; blocage des niveaux élevé/critique.
- Installation npm ci reproductible, scripts désactivés, manifest et lockfile
  validés avec 1 015 SRI; exécution du binaire local après installation,
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

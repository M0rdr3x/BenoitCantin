# GitHub Pages — bascule contrôlée et procédure de repli

**Statut : préparation uniquement. NE PAS PUBLIER depuis cette PR.**  
Référence de sécurité : issue [#450](https://github.com/M0rdr3x/BenoitCantin/issues/450), correctif [#458](https://github.com/M0rdr3x/BenoitCantin/pull/458).

## 1. État réel, prouvé

Le dernier build automatique observé sur le code public courant est le run
[37978201065](https://github.com/M0rdr3x/BenoitCantin/actions/runs/37978201065),
pour `main` à `790b1424b20e98ef31ec6597e98c5c8f6b4aa23d`.

Son job `build` exécute **`actions/upload-pages-artifact@v3` avec `path: .`** :
la racine technique du dépôt est donc empaquetée. La présence d'exclusions
`_config.yml` ne suffit pas tant que cette source de publication reste active.
La preuve que Jekyll sait construire un artefact sûr (run
[37983554606](https://github.com/M0rdr3x/BenoitCantin/actions/runs/37983554606))
concerne **un autre pipeline sans déploiement**.

L'intégration GitHub de ce projet n'offre pas la lecture/modification des
paramètres administratifs `Settings > Pages`. L'opérateur du dépôt doit
certifier la source réelle avant de déclencher la mise en ligne.

## 2. Portes préalables (aucune fusion / publication tant qu'elles ne sont pas vertes)

- Revoir les diff de #458, en particulier la suppression de `.nojekyll`,
  `_config.yml`, l'auditeur `scripts/audit_pages_jekyll.py`, la
  liste bornée des documents Nova déjà publics et le workflow manuel
  `.github/workflows/deploy-pages-controlled.yml`.
- Examiner toutes les validations PR, dont la compilation Jekyll réelle,
  les autotests et la vérification de la sortie `_site`.
- Conserver une référence immuable du **dernier état PUBLIC sûr**, une copie du
  `CNAME` et un journal des contrôles; le `main` actuel publiant la racine
  ne doit **jamais** être considéré comme image de rollback sûre.
- Vérifier `https://www.benoitcantin.com/`, Projet Nova, SINJIRA, le compte,
  les redirections HTTPS et les tests de navigation avant la bascule.
- Faire valider le créneau de changement avec le responsable du site. La PR
  reste draft avant cette décision.

## 3. Corriger la véritable source Pages (action administrateur explicite)

1. Dans GitHub, ouvrir **BenoitCantin > Settings > Pages > Build and deployment**.
2. Identifier `Source` et son mode actuel : `Deploy from a branch` ou
   `GitHub Actions`. Ne pas supposer qu'une simple `_config.yml` corrige
   le mode automatique (la preuve actuelle est `upload-pages-artifact path: .`).
3. Après validation du plan, choisir **GitHub Actions**, pas `Deploy from a branch`.
   Vérifier les éventuels workflows de publication concurrents; la nouvelle
   publication doit avoir **une seule source active**.
4. Confirmer le domaine personnalisé, le HTTPS, le `CNAME` et le rôle
   `github-pages` dans les environnements GitHub. Utiliser une approbation
   d'environnement lorsque possible.
5. **Seulement après ces vérifications**, fusionner #458 dans `main`
   par une PR contrôlée, sans fusionner #449.

Si GitHub Pages continue d'exécuter un workflow dynamique qui téléverse `path: .`,
**arrêter**. Corriger la source d'abord.

## 4. Essai sans publication

Dans `Actions > Pages — déploiement isolé explicitement approuvé > Run workflow` :
- branche **main**;
- `mode=DRY_RUN`;
- `confirm_actions_source=NOT_CONFIRMED`;
- `expected_sha` = SHA **complet** du `main` revu juste avant le run.

Le workflow doit : checkout du SHA, tests, compilation Jekyll, audit sans
fichiers techniques, puis **upload uniquement de `_site` dans les
artefacts Actions**. Le job `deploy` doit être marqué *skipped*.
Un dry-run n'est ni un déploiement ni une preuve de réponses HTTP.

Si les checks échouent, réparer sur PR et recommencer; ne jamais remplacer
`path: _site` par `path: .`.

## 5. Publication explicitement approuvée

Après revérification de la source `GitHub Actions`, du SHA `main` et des
résultats dry-run, lancer **manuellement** :
- `mode=PUBLISH`;
- `confirm_actions_source=ACTIONS_ONLY`;
- `expected_sha` = SHA complet exact, inchangé, de `main`.

**Double attestation automatique du commit approuvé :** avant de construire
en mode `PUBLISH`, puis **juste avant `actions/deploy-pages`, après l'approbation
de l'environnement `github-pages`**, le script
`scripts/attest_pages_production.py` lit deux endpoints GitHub en lecture
seule : paramètres Pages et référence `refs/heads/main`. Il exige
`build_type=workflow`, `cname=www.benoitcantin.com`,
`https_enforced=true` et surtout que le **SHA actuel de `main` soit
strictement le SHA approuvé**. Une modification de la branche entre
l'approbation et le déploiement annule l'exécution. Les erreurs API et
réponses malformées sont bloquantes. Les attestations possèdent des autotests
sans accès réseau. Le consentement manuel ne remplace jamais la preuve
automatique.

Le job `deploy`, protégé par son environnement `github-pages`, appelle
`actions/deploy-pages`. Il publie seulement l'artefact testé de `_site`.
Le job final exécute **`python3 scripts/verify_pages_live.py --check`** :
HTTPS, 8 chemins publics en 200 (types MIME HTML/JS/XML/TXT compris) et 12 chemins techniques en **404/410 strict**.

Les probes contrôlent notamment :
`/supabase/config.toml`, `/tests/e2e/test_public_site.py`,
`/mobile-native/App.tsx`, `/scripts/validate_site.py`,
`/.github/workflows/validate-site.yml` et `/_config.yml`.

Le succès du déploiement GitHub n'est **pas** le succès du contrôle HTTP :
inscrire les deux états dans l'issue #450 et tester aussi manuellement les
parcours authentifiés, la PWA/cache, les navigations et les redirections.

## 6. Annulation et retour arrière

- Si le **dry-run échoue**, ne publier **rien**; la production reste inchangée.
- Si le **déploiement ou le contrôle HTTP échoue**, ne pas relancer le vieux
  workflow dynamique `path: .` : cela réexposerait les sources.
- Conserver le contrôle du domaine sur la source GitHub Actions; restaurer
  **une version antérieure déjà confinée et validée**, pas l'ancien `main`
  exposé. Si un correctif nécessite un revert, le faire dans une nouvelle PR,
  repasser tous les tests et publier seulement le nouveau SHA approuvé.
- En cas d'incident grave, suivre la procédure de sécurité et documenter les
  URL, codes HTTP, horodatages, SHA, runs et mesures correctrices sans partager
  de secrets ni données personnelles.

## 7. Frontière avec la refonte #449

Ce confinement est un **correctif transitoire**. Il n'apporte pas les entêtes
`_headers` ni les redirections `_redirects` de Netlify, et ne valide pas les
services externes. Le projet #449 doit rester en brouillon jusqu'à ce que
l'hébergement réellement publié, les accès privés, les tests de domaines,
les garanties HTTP et les validations finales soient prouvés.

**Aucune étape de ce document n'a été exécutée en production automatiquement.**

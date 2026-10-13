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
fichiers techniques, création et validation du reçu SHA/run de test.
**Aucun artefact Pages n'est téléversé en mode DRY_RUN** : l'étape
`actions/upload-pages-artifact` et le job `deploy` doivent être marqués
*skipped*. Un dry-run n'est ni un déploiement ni une preuve de réponses HTTP.
Le téléversement de `_site` est réservé à `mode=PUBLISH` lorsque
`confirm_actions_source=ACTIONS_ONLY` et les audits ont réussi.

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
HTTPS, **12 chemins publics en 200** (HTML, JS, XML, TXT, JSON Boussole, PDF démo et image WebP avec MIME attendus) et **13 chemins techniques en 404/410 strict**, dont le contrat de livraison privée du Livre I.

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

## 7. Documents publics approuvés et éditions intégrales

Le dépôt `main` du 10 octobre 2026 contient **20 PDF** relevant de trois
ensembles : documents citoyens de Projet Nova, documents gratuits SINJIRA
(démo et questionnaires), et feuilles publiques du jeu Fracture du Réseau
Mère. Leur liste **exacte** est gelée dans
`scripts/audit_public_documents.py` ; chaque fichier doit être présent
dans l'inventaire de source **et dans l'artefact de publication**, avec des
octets identiques (SHA-256). Un nouveau PDF ou une édition payante non
approuvée provoque un échec avant le déploiement, qu'il soit présent dans
le dépôt ou dans le build. Les formats de livre électronique et archives
(`.epub`, `.mobi`, `.azw3`, `.zip`, `.docx`, etc.) sont interdits tant
qu'ils n'ont pas fait l'objet d'une politique de publication distincte.

Le contrat technique `projets/sinjira/codex/livre-i-delivery-contract.json`
reste dans le dépôt source de développement, mais est **explicitement exclu**
de l'artefact Jekyll et refusé par l'auditeur. Le manifeste public
`projets/sinjira/romans/livre-1-release.json` n'est pas modifié.

**Aucune édition intégrale SINJIRA ne peut être hébergée statiquement** sur
GitHub Pages. Les ventes et les accès authentifiés devront reposer sur
un stockage privé, des droits serveur et un lien de livraison temporaire,
avec vérification indépendante. L'ajout légitime d'un nouveau document
gratuit exige une modification délibérée de l'allowlist et une revue CI.
Cet inventaire ne révèle aucune information confidentielle de l'utilisateur.

## 8. Registre des données JSON publiques

L'inventaire réalisé sur le `main` exact du 10 octobre 2026 dénombre **78
fichiers JSON** : 50 documents actuellement destinés à l'artefact statique
(données de la Boussole électorale, publications/versions Nova, manifestes
publics) et 28 fichiers de développement exclus (rapports techniques racine,
configuration mobile native et contrat privé SINJIRA).

Le registre `scripts/audit_public_json.py` verrouille ces deux ensembles :
un JSON public doit exister dans le dépôt et dans `_site`, identique octet pour
octet après compilation (SHA-256). Les 28 JSON techniques doivent être présents
dans les exclusions Jekyll et absents de `_site`. Un JSON inconnu, y compris
un document ajouté sous `projets/projet-nova/data/`, bloque la publication
tant que son niveau d'accès n'est pas examiné. Les JSON futurs de
`.well-known/` nécessaires à une publication atomique devront être ajoutés
**expressément** au registre avec un contrôle du format de provenance.

Ce verrou est conservateur : il ne change pas les données électorales ni leur
contenu politique, ne modifie pas les interfaces, et ne fusionne pas #449.
Il ne garantit pas que les 50 JSON sont exempts de toute donnée à caractère
personnel : leur contenu nécessite une revue documentaire séparée avant la
bascule de l'hébergement.

## 9. Modèles CSV publics de Projet Nova

Le dépôt `main` recensé le 10 octobre 2026 contient **57 CSV** : deux
modèles de données Nova et 55 modèles de registres des versions officielles
V316 à V322. Ils sont des modèles de publication, et non des exports de
membres du site. `scripts/audit_public_csv.py` fixe leur liste exacte et
compare les octets SHA-256 entre source et `_site`.

Tout ajout de CSV sous `projets/projet-nova/data/`, `official/` ou dans
une autre zone publiable est bloqué sans revue explicite. Un export réel
d'utilisateurs ou de participants ne doit jamais être versé dans le dépôt
public ni servi par un hébergeur statique. Des tests négatifs détectent la
disparition, la transformation et l'inclusion d'un fichier non approuvé.

## 10. Contrat intégral de la surface publique (614 chemins)

La photographie prise sur le `main` du 10 octobre 2026, après application
des exclusions Jekyll explicites, compte **614 fichiers publiables** :
pages HTML, styles, modules JS, images, icônes, manifestes, documents et
données publiques. Le registre `scripts/pages_public_inventory.txt`
donne chaque chemin source exact et
`scripts/pages_generated_inventory.txt` autorise séparément les **31
fichiers produits exclusivement par Jekyll** (notamment les pages HTML
issues des références Markdown officielles et `assets/css/style.css`).
Le vérificateur `scripts/audit_public_surface.py` compare les **614
sources attendues et les 31 sorties générées** avec le contenu exact de
`_site`. Pour les 614 fichiers provenant directement des sources, il
exige des octets identiques SHA-256 ; les 31 sorties générées sont limitées
à une liste exacte de chemins et ne peuvent ni disparaître ni s'étendre
sans mise à jour approuvée de l'inventaire.

Cette vérification globale couvre aussi les formats non inclus dans les
audits spécialisés (par exemple nouvelles images, fichiers sans extension,
modules `.mjs`, XML ou CSV avec une extension inhabituelle). L'ajout d'un
fichier public légitime demande la mise à jour *explicite* de son chemin
dans l'inventaire et la revue de la PR. Les fichiers techniques dans
`scripts/`, `supabase/`, `tests/` ou `.github/` ne font pas partie de
cette surface. Ce contrat est une **garde de publication**, pas une
affirmation que tous les documents existants ont été audités
sémantiquement pour la confidentialité.

L'inventaire global ne remplace pas les contrôles indépendants de
confidentialité, les preuves HTTPS ni l'absence de fichiers sensibles sur
l'hébergement réellement en service. Le vrai déploiement reste bloqué
tant que le mode administrateur GitHub Pages n'est pas corrigé.

## 11. Contrôle des secrets à la sortie et préservation de .well-known

Le contrôle `scripts/audit_pages_secrets.py` examine **les ressources textuelles
réelles du build `_site`**, y compris les pages HTML générées par Jekyll,
avant l'étape `upload-pages-artifact`. Il réutilise les motifs de clés
critiques déjà vérifiés par `scripts/validate_no_committed_secrets.py`
(Supabase secret, jetons GitHub, clés privées, Stripe live et mots de passe
configurés). Un fichier texte illisible ou trop volumineux fait échouer la
publication au lieu d'être silencieusement ignoré. Les journaux indiquent
seulement le chemin, la ligne et le **type** de secret, jamais la valeur.

Le workflow autorise désormais explicitement
`include-hidden-files: 'true'` dans l'upload Pages afin de ne pas
perdre les fichiers de preuve approuvés du dossier `.well-known` lorsque
celui-ci sera utilisé.

**Compatibilité vérifiée du fournisseur :** l'ancien commit épinglé
`actions/upload-pages-artifact@56afc609` (février 2024) ne déclarait
**pas** cet input ; il l'aurait ignoré silencieusement. L'action est
désormais épinglée au commit GitHub
[`98ef48e41587a300b82de4cf298aa98b57b2faae`](https://github.com/actions/upload-pages-artifact/commit/98ef48e41587a300b82de4cf298aa98b57b2faae)
(juin 2026), dont `action.yml` déclare ce paramètre et conditionne
explicitement l'exclusion des chemins cachés à sa valeur. Le garde
`scripts/validate_pages_workflows.py` interdit le retour à la version
2024, détecte la perte du paramètre et protège le SHA complet épinglé.
Cette vérification documentaire porte sur le code de l'action upstream;
la preuve de tar effectivement déployé demeure à faire lors du PUBLISH
réel, puis par le reçu HTTPS. Cette permission est sûre **uniquement** parce que
l'audit Jekyll, le registre exact des 645 chemins publics et le rejet des
fichiers cachés imprévus s'exécutent **avant** l'envoi. Toute introduction
future d'un nouveau chemin sous `.well-known` exige une revue du registre.

Le contrôle des secrets reconnaît les motifs connus : il ne constitue ni
une garantie générale d'absence de données personnelles, ni une analyse
juridique des documents et des PDF. Ces revues demeurent distinctes.

## 12. Reçu de publication vérifié sur le domaine réel

La vérification HTTP des routes, du HTTPS et des refus techniques ne suffit
pas à prouver qu'un site sous un autre CDN sert **le même artefact** que le
déploiement GitHub Pages nouvellement approuvé. Désormais, après le build
et **avant** les audits finaux, `scripts/pages_release_proof.py` crée
`_site/.well-known/sinjira-pages-release.json` avec uniquement :
`repository`, `revision` (SHA du commit approuvé), `run_id` et une
version de contrat. Ce marqueur ne contient aucun identifiant de membre,
secret, droit d'accès ou donnée personnelle.

Le workflow manuel exige que ce **646e fichier dynamique** corresponde
exactement au SHA et au run courants. Les contrôles JSON, inventaire intégral
et anti-secrets permettent **seulement** ce chemin supplémentaire lorsque
le marqueur validé est présent; les 645 chemins historiques restent figés.

Après le déploiement, `scripts/verify_pages_live.py --check` reçoit le
SHA et le run attendus, télécharge en GET HTTPS le reçu depuis
`https://www.benoitcantin.com/.well-known/sinjira-pages-release.json`
(sans suivre de redirection), puis compare **les octets exacts**, le statut
HTTP 200 et le type MIME JSON. Le test échoue si le domaine sert une ancienne
version ou un hébergeur différent, même si les autres routes répondent 200.

**Propagation CDN bornée :** après un PUBLISH approuvé, le validateur
peut interroger uniquement ce reçu jusqu'à **13 fois à 10 secondes
d'intervalle** (soit au maximum 120 secondes de pause, hors durées
des requêtes). Il ne suit aucune redirection, rejette immédiatement un
MIME non JSON et n'accepte que les octets exacts du SHA/run. Si le reçu
n'est jamais présent et correct, le job échoue, sans déclarer le
déploiement réussi. Dès sa réception, **les 12 routes publiques et les
13 routes techniques sont retestées** en HTTP strict; un succès du reçu
ne contourne donc jamais les vérifications de non-divulgation.

La CI de la PR simule l'arrivée tardive du reçu, un SHA obsolète,
un MIME incorrect et une redirection **sans déploiement**. Une preuve HTTP
réelle n'existe qu'après PUBLISH et contrôle réussi sur le domaine.

## 13. Intégrité CDN réelle des fichiers statiques critiques

Le reçu de publication `.well-known/sinjira-pages-release.json` prouve
le SHA/run **annoncé** par l'hébergement. Il ne prouve pas à lui seul qu'un
CDN sert déjà chaque fichier de cette version. Pour éviter un faux succès
avec un reçu neuf mais un `sw.js` ou une Boussole obsolète, le dernier job
`verify-live` exécute désormais
`scripts/verify_pages_integrity.py --check --expected-sha "$GITHUB_SHA"`
**après** la vérification du reçu et des routes.

Ce contrôle lit les huit fichiers sources au **checkout exact** de la
révision approuvée, mais vérifie d'abord chacun de ces fichiers contre
le blob stocké dans l'objet Git de ce commit (`git show SHA:chemin`).
Un `git rev-parse HEAD` correct n'est pas suffisant si le répertoire de
travail a été modifié après le checkout. Toute différence source/blob,
absence ou substitution fait échouer la preuve **avant la première requête
réseau**. Les autotests créent un dépôt Git éphémère, commettent les huit
ressources, puis vérifient qu'une modification et une suppression
postérieures au commit sont rejetées.

Le contrôle calcule ensuite leurs empreintes SHA-256 et effectue des
requêtes HTTPS GET en lecture seule sur leur chemin réel. Il exige :
HTTP 200 sans redirection, MIME conforme, absence de compression inattendue,
réponse limitée à 4 Mio et SHA-256 des **octets servis** identique aux sources.

Les huit fichiers vérifiés sont : le service worker `sw.js`, le manifeste
`manifest.webmanifest`, les styles `assets/css/site.css`, le script
`assets/js/site.js`, les deux JSON de la Boussole électorale,
la démo PDF du Livre I et le logo Nova WebP.

Chaque ressource peut être contrôlée jusqu'à quatre fois à huit secondes
d'intervalle pour une propagation CDN bornée. Une version persistante
obsolète est rejetée, un changement de MIME, une redirection et une
réponse trop volumineuse sont refusés immédiatement. Les autotests
simulent notamment un service worker périmé malgré un reçu valide,
un JSON politique ancien, des ressources actualisées tardivement et
une discordance du SHA du checkout. Le contrôle ne modifie jamais le site.

Cette preuve protège ces huit ressources critiques sans prétendre auditer
les octets des autres routes HTML générées, les réponses dynamiques
des comptes ou le fonctionnement réel du cache sur un appareil. La
revue navigateur et les contrôles de droits restent obligatoires.

## 14. Isolation du cache PWA et des données privées

Le service worker `sw.js` est audité avec le **vrai code JavaScript exécuté**
dans Node 22 par `scripts/test_pwa_cache_security.cjs` dans la CI de la PR.
Un contrôle statique indépendant, `scripts/audit_pwa_precache.py`,
lit la liste `CORE` du véritable service worker et exige que ses **46
routes de préchargement** existent comme fichiers concrets dans la source
et après compilation Jekyll (les chemins terminés par `/` doivent
fournir leur `index.html`). Il interdit également les doublons, chemins
privés, URL non canoniques et ajouts non explicitement révisés. Ce contrôle
s'exécute dans la CI PR et dans le workflow de publication manuelle avant
l'upload : un seul fichier manquant empêche le déploiement et évite un
service worker impossible à installer malgré un build Jekyll réussi.
La version du cache a été augmentée pour que les caches obsolètes soient
éliminés à l'activation du nouveau service worker, sans supprimer ceux
d'autres applications du même domaine.

Seuls les chemins explicitement préapprouvés dans `CORE` peuvent être
enregistrés dans le cache PWA. La précharge utilise `credentials: omit`,
refuse les chemins privés, les redirections ainsi que les réponses comportant
`Cache-Control: no-store/private`, `Set-Cookie` ou
`Vary: Cookie/Authorization`. Les requêtes avec identifiants, en-têtes
d'authentification ou paramètres d'URL ne sont pas mémorisées.
Les navigations vers les pages publiques restent accessibles au serveur avec
leur session normale, mais **leurs réponses ne sont jamais ajoutées au
cache**, puisqu'une page pourrait être personnalisée. Le mode hors ligne
réutilise exclusivement la version anonyme préchargée, **strictement à
partir du cache public de cette version du service worker**. Aucun
`caches.match()` global n'est utilisé : l'API globale pourrait sinon
retrouver des réponses de caches appartenant à d'autres applications,
ou d'anciennes versions du site sur la même origine. Les scripts,
styles et images figurant dans la liste approuvée sont récupérés avec
`credentials: omit` avant toute mise en cache.

Les tests Node simulent expressément une réponse privée dans un cache
tiers : même hors ligne, le service worker ne doit jamais la lire ou
la servir. Une ressource absente du cache public courant reste absente,
plutôt que d'être remplacée par une ancienne copie de source inconnue.

Les chemins `/app`, `/compte`, `/admin`, `/Admin`,
`/histoire-de-vie`, `/supabase`, `/api`, `/auth`, `/rest`,
`/storage`, `/functions`, `/edge`, le contrat technique du Livre I,
et surtout les preuves `/.well-known` utilisent uniquement le réseau,
avec `cache: no-store` et **sans fallback de cache**. Une preuve de version
obsolète ne peut donc pas être renvoyée par l'ancien cache PWA.

**Compromis assumé :** certaines ressources non essentielles à la liste
`CORE` ne seront plus accessibles hors ligne. Les contenus publics ne sont
pas retirés du site en ligne; le cache n'est pas un mécanisme de
contrôle d'accès serveur. Les droits SINJIRA doivent toujours être appliqués
côté serveur. Vérifier manuellement en navigateur la PWA après le
déploiement approuvé, y compris une mise à jour depuis une ancienne version.

## 15. Frontière avec la refonte #449

Ce confinement est un **correctif transitoire**. Il n'apporte pas les entêtes
`_headers` ni les redirections `_redirects` de Netlify, et ne valide pas les
services externes. Le projet #449 doit rester en brouillon jusqu'à ce que
l'hébergement réellement publié, les accès privés, les tests de domaines,
les garanties HTTP et les validations finales soient prouvés.

**Aucune étape de ce document n'a été exécutée en production automatiquement.**

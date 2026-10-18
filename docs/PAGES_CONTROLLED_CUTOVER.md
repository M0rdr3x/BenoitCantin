# GitHub Pages — bascule contrôlée et procédure de repli

**Statut : préparation uniquement. NE PAS PUBLIER depuis cette PR.**  
Référence de sécurité : issue [#450](https://github.com/M0rdr3x/BenoitCantin/issues/450), intégration actuelle [#639](https://github.com/M0rdr3x/BenoitCantin/pull/639) (DRAFT), réunissant les travaux de [#458](https://github.com/M0rdr3x/BenoitCantin/pull/458) et [#637](https://github.com/M0rdr3x/BenoitCantin/pull/637).

## 1. État réel, prouvé

**Dernier diagnostic validé : 15 octobre 2026 UTC** (soir du 14 octobre
au Québec), [workflow de pré-bascule #38664343729](https://github.com/M0rdr3x/BenoitCantin/actions/runs/38664343729).
La source GitHub Pages demeure **`build_type=legacy`** alors que le
domaine `www.benoitcantin.com` et HTTPS sont configurés.

Le rapport HEAD **et**, pour la première fois, un diagnostic indépendant
de **statuts GET sans lecture des corps** montrent les mêmes résultats :
**9 routes techniques en HTTP 200 sur 14**, les **5 autres en HTTP 404**.
Les neuf URL concernées sont `/supabase/config.toml`,
`/tests/e2e/test_public_site.py`, `/mobile-native/App.tsx`,
`/scripts/validate_site.py`, `/assets/icons/README.md`,
`/projets/projet-nova/netlify.toml`,
`/projets/projet-nova/UPLOAD_GITHUB.md`,
`/projets/projet-nova/SECURITY.md` et
`/projets/sinjira/codex/livre-i-delivery-contract.json`.

**Qualification de sécurité :** ces codes GET 200 prouvent que les chemins
répondent sur le site public, **pas le contenu exact des réponses ni la
présence de secrets**. Le script ferme chaque réponse sans lire son
corps, ne suit pas les redirections, n'enregistre pas de fichiers et
n'utilise aucun jeton d'utilisateur. La source `legacy` doit être
corrigée par l'administrateur avant toute fusion ou publication. Les
preuves GET 404/410, le reçu SHA/run et les hachages CDN après la
bascule demeurent indispensables.

La preuve historique de la publication de la racine est le
[run #37978201065](https://github.com/M0rdr3x/BenoitCantin/actions/runs/37978201065),
où `actions/upload-pages-artifact@v3` recevait **`path: .`**.
Les exclusions Jekyll ne corrigent pas ce flux en mode `legacy`.

L'actuel `main` est `9ed5f70cbe7022f25a679346a1288701f3b09067`
(hotfix visuel Boussole #642). La CI PR peut **lire** la source Pages
en lecture seule, mais l'intégration GitHub de cette conversation ne
peut **pas modifier** son réglage administrateur. Le propriétaire doit
le faire explicitement avant toute promotion.

**Nouvelle porte CI pour les PR prêtes à la revue :** le workflow
`.github/workflows/pages-cutover-preflight.yml` conserve le rapport
informatif sur les PR en brouillon, mais active un second job
`pages-source-promotion-gate` lorsqu'une PR est marquée prête pour revue.
Cette porte exige `build_type=workflow`, le CNAME officiel et HTTPS
activé; API inaccessible ou mode `legacy` entraînent une erreur
bloquante du job.
Le job de promotion déclare aussi `needs: pages-preflight` : il attend
la fin réussie des autotests et des rapports Source, HEAD et GET
(lecture seule). Si le diagnostic échoue ou n'est pas exécuté, la
garde de promotion ne peut pas réussir. Cela ne signifie **pas** que
les 14 chemins techniques sont déjà confinés : leurs statuts restent
un signal informatif jusqu'à la publication contrôlée, puis les
contrôles HTTP et CDN stricts deviennent bloquants. La CI de diagnostic s'exécute sur **toutes les PR** (aucun filtre
`paths`) afin que son résultat ne reste pas indéfiniment en attente
lorsqu'il devient obligatoire. **Cette porte ne peut pas empêcher à
elle seule une fusion si les vérifications obligatoires de branche
ne sont pas configurées.** L'administrateur doit inclure ce job dans les règles
de protection de `main` et conserver l'approbation manuelle de PUBLISH.

## 2. Portes préalables (aucune fusion / publication tant qu'elles ne sont pas vertes)

- Revoir l'intégration finale **#639** (incluant les changements #458
  et #637), en particulier la suppression de `.nojekyll`,
  `_config.yml`, le garde `scripts/audit_pages_jekyll.py`, le
  manifeste des 618 sources autorisées et le workflow manuel
  `.github/workflows/deploy-pages-controlled.yml`.
- Examiner toutes les validations PR, dont la compilation Jekyll réelle,
  les autotests et la vérification de la sortie `_site`.
- Examiner ensemble les deux relevés **HEAD / GET statut uniquement** de
  `.github/workflows/pages-cutover-preflight.yml` : le GET ne lit pas
  de corps technique et complète, sans remplacer, le contrôle HTTP
  strict post-publication, l'attestation du SHA et les hachages CDN.
- Conserver une référence immuable du **dernier état PUBLIC sûr**, une copie du
  `CNAME` et un journal des contrôles; le `main` actuel publiant la racine
  ne doit **jamais** être considéré comme image de rollback sûre.
- Vérifier `https://www.benoitcantin.com/`, Projet Nova, SINJIRA, le compte,
  les redirections HTTPS et les tests de navigation avant la bascule.
- Faire valider le créneau de changement avec le responsable du site. La PR
  reste draft avant cette décision.

### Couverture universelle de la preuve Jekyll (17 octobre 2026)

L'ancien workflow `.github/workflows/audit-pages-jekyll.yml` appliquait
une liste `pull_request.paths` partielle : une modification légitime de
bannière, d'une nouvelle page, d'un document autorisé ou d'une ressource
absente de cette liste pouvait **ne pas déclencher** le contrôle Jekyll.
La réussite de tests précédents ne prouvait donc pas que chaque nouvelle
PR avait été compilée et inspectée.

Désormais, l'audit Jekyll est exécuté sur **toute PR vers `main`**,
sans `paths` ni `paths-ignore`, qu'elle modifie du contenu, des images
ou l'infrastructure. La fonction `validate_jekyll_ci` de
`scripts/validate_pages_workflows.py` interdit la réintroduction de
filtres, de jobs ignorés, de publication d'artefact, de droits d'écriture
ou de retrait de la compilation et des audits. Ses **17 mutations
négatives** protègent ce contrat, y compris le nom stable du job
`Construire puis auditer Pages sans déployer` utilisé comme required check; les audits des sources et secrets
doivent avoir lieu avant **et** après l'ajout du reçu SHA/run.

**Limite :** le code de contrôle CI n'est pas une règle de protection
effective de `main`. L'administrateur doit toujours activer les required
checks GitHub avant toute fusion : **`Construire puis auditer Pages sans
déployer`** et **`Garde de promotion — Source Pages conforme exigée`**.
Le premier est désormais déclenché sur toute PR; le second s'exécute
quand une PR n'est plus en brouillon. Le statut DRAFT, l'absence de PUBLISH
et le blocage de sécurité #450 restent inchangés.

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
5. **Seulement après ces vérifications**, faire approuver la PR **#639**
   (qui intègre déjà #458 et #637), puis fusionner **#639 seulement**
   sur `main`. Ne pas fusionner séparément #458, #637 ou #449.
   Relever le SHA exact du nouveau `main` pour le DRY_RUN.

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
HTTPS, **21 chemins publics en 200** (accueil, catalogues SINJIRA,
pages Nova, JS, XML, TXT, JSON Boussole, PDF démo et bannières WebP
avec MIME attendus) et **14 chemins techniques en 404/410 strict**,
dont le contrat de livraison privée du Livre I et le script historique
Netlify `/scripts/build_netlify_public.py`. Le contrôle bloquant
post-PUBLISH et la surveillance quotidienne partagent désormais
**les deux mêmes inventaires : 21 routes publiques et 14 chemins
techniques interdits**, afin de prévenir tout écart. La surveillance
quotidienne (workflow `.github/workflows/publication-boundary-watch.yml`)
vérifie les **35 URL canoniques** par des requêtes GET en lecture seule :
HTTP 200 direct et type MIME correct pour les 21 pages/ressources publiques,
404/410 strict pour les 14 chemins techniques. Les redirections, y compris
un HTTP 200 muni d'un en-tête `Location`, sont rejetées sur les routes
publiques. Les vérifications sont faites **sans lire aucun corps technique
ni aucun document public**, uniquement par les statuts et en-têtes.

**Protection contre la neutralisation du workflow :** le contrat
`scripts/validate_publication_watch_workflow.py` vérifie les événements
`push` et `pull_request` sur `main`, la planification quotidienne
`17 11 * * *` (UTC), la possibilité de déclencher manuellement,
la dépendance du job `live` aux autotests et les seules permissions
`contents: read`. Les sondes live doivent être réellement exécutées
avec `--live` uniquement sur `schedule` ou `workflow_dispatch`,
sans erreur ignorée, publication d'artefact, jeton persistant ou étape
facultative. Son autotest injecte **20 mutations dangereuses** et
vérifie qu'elles échouent. Ce contrat est lancé dans la CI de
surveillance, l'audit Jekyll de la PR et le DRY_RUN/PUBLISH contrôlé.

Le garde-fou protège le **code du futur workflow**, pas la configuration
GitHub Pages : un résultat CI vert ne garantit pas qu'une cadence ait
déjà été exécutée sur `main`, ni que la production soit confinée.

Cette surveillance reste distincte de la **preuve post-PUBLISH** :
elle n'effectue ni déploiement ni comparaison d'octets des 22 ressources
critiques, ne remplace pas l'approbation du SHA et ne teste pas les parcours
authentifiés. Une réussite des tests en PR n'atteste jamais la production.

Les probes contrôlent notamment :
`/supabase/config.toml`, `/tests/e2e/test_public_site.py`,
`/mobile-native/App.tsx`, `/scripts/validate_site.py`,
`/.github/workflows/validate-site.yml` et `/_config.yml`.

Chaque route publique canonique doit répondre **directement** HTTP 200 et
avec son type MIME prévu. Une redirection HTTP 301/302/303/307/308, même
vers l'accueil officiel ou vers une autre URL du même domaine, est refusée :
elle ne prouve pas que la route demandée fonctionne. Les **21 routes
publiques** sont protégées par des autotests de redirection trompeuse.

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

## 10. Contrat intégral de la surface publique (622 chemins)

La photographie prise sur le `main` du 10 octobre 2026, après application
des exclusions Jekyll explicites, compte **618 fichiers publiables** :
pages HTML, styles, modules JS, images, icônes, manifestes, documents et
données publiques. Le registre `scripts/pages_public_inventory.txt`
donne chaque chemin source exact et
`scripts/pages_generated_inventory.txt` autorise séparément les **31
fichiers produits exclusivement par Jekyll** (notamment les pages HTML
issues des références Markdown officielles et `assets/css/style.css`).
Le vérificateur `scripts/audit_public_surface.py` compare les **618
sources attendues et les 31 sorties générées** avec le contenu exact de
`_site`. Pour les 618 fichiers provenant directement des sources, il
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
La CI et le futur workflow de PUBLISH exécutent également
`scripts/verify_pages_tar_archive.py` **après l'ajout du reçu et après
tous les audits, mais avant l'upload**.
**Liens symboliques (contrôle fail-closed)** : GNU tar utilise
`--dereference` et pourrait donc copier dans un artefact public le contenu
d'un fichier privé ciblé par un lien portant un nom public. L'audit
`scripts/audit_public_surface.py` refuse désormais explicitement tous
les liens symboliques de **fichiers ou de répertoires**, dans les sources
et le résultat `_site` (même si un chemin source est autrement exclu de
Jekyll). Les fichiers cibles des liens ne comptent jamais comme ressources
approuvées. Les autotests créent des liens vers `scripts/internal.py`,
un répertoire privé ainsi qu'un lien brisé, et exigent leur rejet. L'état
Git au moment de l'introduction du contrôle était sans liens symboliques
suivis; le changement renforce la sécurité sans supprimer une ressource
existante.
 Ce contrôle crée une archive TAR
locale avec les options Linux de l'action épinglée, sans envoyer aucun
artefact, puis compare tous ses fichiers octet pour octet avec `_site`
et exige explicitement le reçu caché `.well-known`. Il refuse une
archive privée de ce répertoire, une ancienne copie du site ou un octet
modifié. Ses autotests simulent les anciennes exclusions des fichiers
cachés et des altérations postérieures à la création du TAR.

Cette vérification vérifie la forme attendue de l'archive avant upload;
elle ne prétend pas avoir observé le TAR effectivement téléversé par
GitHub Pages. La preuve de tar effectivement déployé demeure à faire
lors du PUBLISH réel, puis par le reçu HTTPS et les contrôles du CDN. Cette permission est sûre **uniquement** parce que
l'audit Jekyll, le registre exact des 649 chemins publics et le rejet des
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

Le workflow manuel exige que ce **650e fichier (dynamique)** corresponde
exactement au SHA et au run courants. Les contrôles JSON, inventaire intégral
et anti-secrets permettent **seulement** ce chemin supplémentaire lorsque
le marqueur validé est présent; les **649 fichiers statiques approuvés**
(618 sources + 31 générés) restent figés.

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
déploiement réussi. Dès sa réception, **les 21 routes publiques et les
14 routes techniques sont retestées** en HTTP strict; un succès du reçu
ne contourne donc jamais les vérifications de non-divulgation.

La CI de la PR simule l'arrivée tardive du reçu, un SHA obsolète,
un MIME incorrect et une redirection **sans déploiement**. Une preuve HTTP
réelle n'existe qu'après PUBLISH et contrôle réussi sur le domaine.

## 13. Intégrité CDN réelle des fichiers statiques critiques

Le reçu de publication `.well-known/sinjira-pages-release.json` prouve
l'identité SHA/run annoncée par l'hébergement, mais pas la fraîcheur de
toutes les ressources servies par un cache CDN. Le job `verify-live`
exécute donc `scripts/verify_pages_integrity.py --check --expected-sha "$GITHUB_SHA"`
**après** l'attestation du reçu et des routes.

Ce contrôle couvre **22 ressources critiques** dans quatre familles :

- Infrastructures : `index.html` (accueil réellement publié),
  `sw.js`, `manifest.webmanifest`,
  `assets/css/site.css`, `assets/js/site.js`.
- Projet Nova : les deux JSON de la Boussole électorale,
  `assets/media/nova-logo.webp`, l'icône compacte de l'accueil
  `assets/media/nova-boussole-electorale.webp`, l'illustration
  haute résolution `assets/media/nova-boussole-electorale-v2.webp`
  et la page `projets/projet-nova/boussole-electorale.html`.
- SINJIRA : démo PDF du Livre I, trois bannières WebP, les pages
  `projets/sinjira/index.html`, `romans/index.html`,
  `jeux/index.html`, `logiciels/index.html`, la feuille de style
  `projets/sinjira/sinjira.css` et `compte/bibliotheque.html`.
- Découverte du site : `sitemap.xml`.

Chaque source du checkout approuvé est préalablement comparée à son
**blob dans l'objet Git** (`git show SHA:chemin`) pour refuser une
altération du répertoire de travail, y compris lorsque `HEAD` reste
identique. Ensuite, pour chaque chemin exact sur le domaine officiel,
la preuve exige HTTP 200 sans redirection, MIME conforme, absence de
compression imprévue, réponse limitée à 4 Mio et SHA-256 identique.

Au plus quatre GET par chemin sont tentés, avec trois intervalles de
huit secondes en cas de propagation tardive du CDN. Les **22 chemins
partagent un budget monotone unique de sept minutes** : si le budget
expire, la vérification échoue explicitement, sans assimiler les
ressources restantes à des succès. Le job complet `verify-live` dispose
de **20 minutes**, couvrant également la confirmation du reçu et les
routes privées. Les appels réseau ont leur propre timeout de 12 secondes.
Les autotests
refusent un service worker obsolète, des JSON politiques périmés,
chacune des pages SINJIRA obsolètes, un sitemap ou CSS ancien, des
redirections, des réponses trompeuses et la divergence entre worktree
et commit. Aucun de ces tests n'émet de requête d'écriture.

Cette preuve porte sur les **22 ressources énumérées seulement**.
L'exactitude des autres routes, les réponses dynamiques des comptes
et le cache réel sur appareil exigent toujours la revue fonctionnelle
et les tests de permissions. Le passage Pages vers GitHub Actions
et l'approbation explicite du propriétaire restent obligatoires.

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

## 15. Validation des commandes réellement exécutables

Le contrôle `scripts/validate_pages_workflows.py` ne vérifie plus
uniquement la **présence textuelle** de noms d'audits dans le workflow.
Un commentaire YAML ou shell, ou une ligne `echo python3 ...`, pouvait
autrefois conserver la chaîne attendue alors que l'audit ne s'exécutait
plus. Le validateur extrait désormais les **commandes Python exécutables**
des étapes `run`, exige les neuf contrôles finaux dans le job
`artifact` et leur ordre **compilation Jekyll → reçu SHA/run →
audits → upload conditionnel**. Il exige aussi les attestations Pages
réellement exécutées dans les deux jobs appropriés, puis les contrôles
HTTP et CDN effectivement exécutés dans `verify-live`.

Le même validateur limite explicitement les jobs à
`artifact`, `deploy` et `verify-live`, dans cet ordre, et rejette
une deuxième définition YAML de `deploy` ou un job supplémentaire de
publication. Les autotests mutent volontairement les commandes en
commentaires, en simples affichages et dupliquent des jobs; **toute
mutation doit faire échouer la validation**. Cette protection ne remplace
pas la revue manuelle du code Bash ou la mise en production contrôlée,
mais rend les garde-fous moins faciles à désactiver accidentellement.

## 16. Frontière avec la refonte #449

Ce confinement est un **correctif transitoire**. Il n'apporte pas les entêtes
`_headers` ni les redirections `_redirects` de Netlify, et ne valide pas les
services externes. Le projet #449 doit rester en brouillon jusqu'à ce que
l'hébergement réellement publié, les accès privés, les tests de domaines,
les garanties HTTP et les validations finales soient prouvés.

**Aucune étape de ce document n'a été exécutée en production automatiquement.**


## Convergence SINJIRA — catalogues du 13 octobre 2026

Cette intégration fermée reprend la page Logiciels et les trois visuels WebP de la PR #637.
Inventaire explicite : 618 sources + 31 sorties Jekyll = 649 statiques ; reçu SHA/run dynamique lors d'une publication approuvée = 650 sorties.
Contrôles supplémentaires : pages Romans, Jeux, Logiciels, trois images WebP et comparaison CDN du contenu au SHA approuvé.
Ces nombres ne prouvent pas une publication ; voir la CI du commit combiné. Aucune publication avant bascule GitHub Actions et approbation explicite.


## 17. Contrôle final du graphe de navigation des catalogues

Le contrôle `scripts/validate_sinjira_public_links.py` fait désormais partie
des **audit(s) exécutables avant upload** dans
`.github/workflows/deploy-pages-controlled.yml`. Ses autotests refusent
notamment des liens vers `scripts/`, `supabase/`, des ressources absentes
du manifeste public et un détournement HTML `<base>`.

La CI Jekyll sans publication l'exécute également avant de compiler.
Le garde indépendant `scripts/validate_pages_workflows.py` impose que
`--check` soit une vraie commande **dans le job artifact, au sein des audits
finaux entre la compilation et l'upload conditionnel** ; un `echo` ou
une omission fait échouer les tests négatifs. Ce mécanisme empêche qu'une
PR réussie soit considérée comme une autorisation implicite de publier.
Le réglage administratif GitHub Pages, la preuve HTTPS et l'approbation
humaine du SHA final restent indispensables.


## Diagnostic automatique du réglage administrateur (sans déploiement)

La CI dédiée `.github/workflows/pages-cutover-preflight.yml`
interroge **en lecture seule** l'API de configuration Pages depuis
la PR, avec la permission minimale `pages: read`. Le script
`scripts/report_pages_cutover_status.py` vérifie `build_type`,
le `cname` et `https_enforced` sans jamais afficher de jeton ni
modifier la configuration. Il consigne une synthèse explicite dans
le résumé du job :

- **BLOQUÉ** : source `legacy` (branche), CNAME divergent ou HTTPS
  non attesté; corriger `Settings > Pages`.
- **INCONNU** : Pages inaccessible au jeton de la PR, API malformée,
  ou source non reconnue; faire vérifier les paramètres par le propriétaire.
- **SOURCE_CONFORME** : les seuls prérequis administratifs de source,
  domaine et HTTPS sont observés comme conformes. Cela ne prouve pas
  le confinement HTTP en ligne ni la fin de l'incident #450.

**Attention :** le job `pages-preflight` reste **informatif** et
retourne `success` même si le diagnostic est BLOQUÉ ou INCONNU.
En revanche, le job `pages-source-promotion-gate` de ce même workflow
s'exécute lorsqu'une PR est **prête pour revue** et échoue fermé si
`build_type` n'est pas `workflow`, si CNAME/HTTPS sont incorrects
ou si l'API ne peut être vérifiée. Pour empêcher la fusion malgré cet
échec, l'administrateur doit aussi rendre ce job **required** dans
la protection de la branche `main`. Le nouveau contrat
`scripts/validate_pages_promotion_gate.py` teste les régressions de
filtrage des PR, de neutralisation d'erreur, de suppression du job,
de permissions en écriture et de **détachement/contournement du job de
diagnostic**. Il rejette les étapes HEAD/GET supprimées ou sautées,
ainsi que les erreurs de diagnostic masquées. Même avec ce garde, seul
un changement administratif réel de Source et les preuves post-PUBLISH
peuvent clôturer l'incident #450.
Le workflow `deploy-pages-controlled.yml` reste **strictement bloquant** et
vérifie de nouveau `build_type=workflow` au SHA exact avant PUBLISH
et juste avant le déploiement. Aucun lancement de l'outil de publication,
aucune fusion et aucun changement de paramètre n'est fait par ce
diagnostic. Un workflow de diagnostic ajouté sur une branche ne
constitue pas une preuve de publication réelle.


## Contrôle de cohérence entre accueil et page Boussole

Depuis la correction visuelle #642, l'accueil et la page de la Boussole
utilisent **deux fichiers distincts** : un WebP compact pour le portail,
et la version originale 360 × 360 pour l'outil civique. Le contrôle CDN
après PUBLISH vérifie désormais **22 ressources** au SHA exact approuvé,
incluant `index.html`, la page `boussole-electorale.html`, ainsi que
les deux WebP. Un résultat CDN portant sur l'icône seule ne suffit pas
à certifier la fraîcheur du parcours complet.

Les autotests simulent une ancienne version de chaque ressource
ajoutée et exigent le rejet avant conclusion. La fenêtre globale de
sept minutes est conservée, avec réponse explicite `budget épuisé`
si tous les fichiers n'ont pas été réellement contrôlés.


## Constat HTTP anonymisé avant changement administratif

Le même workflow `pages-cutover-preflight.yml` exécute les
diagnostics **HEAD et GET (statuts uniquement)** sur les **14 chemins
techniques exacts** de `www.benoitcantin.com`. Le diagnostic GET
n'effectue aucune lecture du corps des fichiers, n'enregistre
aucun contenu technique, n'envoie aucun jeton privé et refuse les
redirections. Les deux méthodes ont confirmé 9 réponses HTTP 200
sur 14 chemins (5 réponses HTTP 404), sans prouver la présence de
secrets. Preuve : [prévol #38664569897](https://github.com/M0rdr3x/BenoitCantin/actions/runs/38664569897).

Le rapport distingue : **EXPOSÉ** (HTTP 200/206 sur une source
technique), **NON_CONFORME** (HTTP différent de 404/410 et sans
signification de refus valide, par exemple 301/403/500),
**INCONNU** (réseau indisponible, HEAD 405/501 ou inventaire
incomplet) et **REFUS_HEAD_OBSERVÉ** (14 réponses HEAD 404/410).
Une réponse HEAD 404 **ne prouve pas** une réponse GET 404, l'absence
de divulgation antérieure ni la publication au SHA approuvé.

Ce rapport est **non bloquant pour la CI PR**, pour rendre les risques
visibles même avant la bascule administrateur. Le résultat vert
de ce workflow signifie seulement que la mesure est enregistrée.
Un déploiement réel reste soumis à `attest_pages_production.py`
(contrôle bloquant de `build_type=workflow`, CNAME, HTTPS et SHA
de `main`), puis aux vérifications GET strictes, à la preuve SHA/run
et aux octets CDN après PUBLISH approuvé.

# Projet Nova — P51B : consolidation des contrôles P50Y, P50Z et P51A

**17 octobre 2026 · Candidat unique en revue · Aucun GO de fusion ou de publication**

## 1. Problème résolu pour la revue de code

Les trois corrections étaient réparties sur des PR **imbriquées** :

- [PR667 — P50Y](https://github.com/M0rdr3x/BenoitCantin/pull/667) : trois essais administratifs de refus de fusion, **non exécutés**;
- [PR668 — P50Z](https://github.com/M0rdr3x/BenoitCantin/pull/668), basée sur PR667 : identité, dépôt cible, branches et fichiers des PR témoins;
- [PR670 — P51A](https://github.com/M0rdr3x/BenoitCantin/pull/670), basée sur PR668 : revues réellement soumises et checks au SHA actuel pour étayer le motif du blocage.

Les comparateurs [PR669](https://github.com/M0rdr3x/BenoitCantin/pull/669) et [PR671](https://github.com/M0rdr3x/BenoitCantin/pull/671) ont chacun réussi leurs validations adversariales sur des **SHA figés**. Ces preuves établissent le comportement des sources examinées, mais les PR parentales n'ont pas été fusionnées.

**P51B regroupe l'état de code de PR670, lequel contient les trois couches de correction depuis leur origine, dans une unique branche candidate ciblant `main`.** Les PR historiques restent ouvertes, en brouillon et non fusionnées; aucune demande de merger les trois parents n'est implicitement faite.

## 2. Défaut complémentaire observé et traité

Dans le validateur P51A, la présence d'une revue au statut GitHub `DISMISSED` sur un ancien commit était comptée comme une ancienne approbation. Or `DISMISSED` n'identifie pas à elle seule si l'avis initial était `APPROVED` ou `CHANGES_REQUESTED`. P51B adopte une interprétation **conservatrice** : seule une trace explicitement `APPROVED` sur un ancien SHA alimente le compteur d'approbations historiques.

**Limite prévisible** : si GitHub ne restitue plus que `DISMISSED` pour une approbation réellement invalidée, l'outil classe la preuve de l'essai « approbation périmée » **comme insuffisante**. L'administrateur doit alors examiner la chronologie GitHub, son journal de preuve et les règles de branche au lieu de surinterpréter un statut ambigu. Un faux négatif documentaire est préférable à une fausse preuve de protection.

Trois tests de régression supplémentaires vérifient qu'une revue `DISMISSED` n'est jamais automatiquement une approbation, que l'essai périmé reste bloqué sans preuve historique et qu'une revue `CHANGES_REQUESTED` postérieure ne compte pas comme une approbation toujours actuelle.

## 3. Un seul périmètre à soumettre pour la décision humaine

Le candidat P51B contient :
- validateur P50Y à jour : contrôle du protocole, identité et périmètre des canaris, revues GitHub et checks effectivement émis;
- **113 tests unitaires** (25 P50Y + 12 P50Z + 15 P51A + 3 P51B + 14 P51C + 15 P51D + 15 P51E + 14 P51F), sur l'intégration des trois couches;
- le procès-verbal JSON volontairement vide et marqué `NO_GO`;
- le protocole opératoire P50Y actualisé;
- un workflow de validation P51B read-only avec tests comptés et contrôle `NO_GO_AUTOMATIQUE`. P51C ajoute une vérification stricte des fichiers **ajoutés** (statut `added`, extension `.txt`, chemin direct sous le dossier de canaris, aucun renommage ou ancien chemin), et exige que l'URL `preuve_url` désigne **la PR témoin correspondante**, pas une autre PR ni une exécution Actions arbitraire. Ces règles ne prouvent toujours pas la cause du blocage sans la recette de l'administrateur.

Les précédentes validations historiques restent consultables :
- [P50Y — 25 tests](https://github.com/M0rdr3x/BenoitCantin/actions/runs/39003702906);
- [P50Z — 25/37 tests, 9 erreurs corrigées sur fixtures](https://github.com/M0rdr3x/BenoitCantin/actions/runs/39005324106);
- [P51A — 37/52 tests, 6 motifs rejetés sur fixtures](https://github.com/M0rdr3x/BenoitCantin/actions/runs/39007363372).

Une preuve indépendante d'une version antérieure n'est **pas** une approbation de P51B. La CI propre à P51B doit réussir sur **son propre HEAD**, puis un réviseur habilité doit examiner le diff complet.

## 3 bis. Renforcement P51D : la protection serveur doit aussi être observable

L'ancien mode `--live` vérifiait les trois PR témoins déclarées, mais **ne relevait pas la protection effectivement installée sur `main`**. Un procès-verbal apparemment complet aurait donc pu être présenté avec une branche non protégée ou un état devenu obsolète.

Le correctif P51D ajoute `--observer-serveur` et impose aussi l'observation des API GitHub lors de `--live`. Les requêtes sont **exclusivement en lecture seule** :

- `GET /branches/main` pour l'indicateur `protected` et le SHA réel, qui doit correspondre à la référence du dossier;
- `GET /rulesets?includes_parents=true` et détails des règles **actives** pour confirmer les obligations de PR, approbations et checks, sans faire passer un modèle désactivé pour une configuration réelle;
- `GET /rules/branches/main` pour vérifier que les quatre familles de règles attendues s'appliquent effectivement;
- liste des `bypass_actors` : **information absente ou non lisible = obstacle**, et toute exception explicite doit être examinée.

L'outil ne déclare les *préconditions techniques visibles* que si ces éléments sont cohérents et si les trois contrôles universels sont réellement exigés de GitHub Actions (app `15368`). Cela ne prouve toujours **pas** que GitHub refuse la fusion pour la bonne cause : l'administrateur doit inspecter les trois essais réels de P50Y et ses permissions effectives.

Le workflow consolidé exécute désormais **84 tests** et joint un relevé serveur non nominatif au procès-verbal des trois essais encore non exécutés. Une erreur 403, une liste tronquée, une règle inactive ou un changement de SHA mène à un état bloquant. **`NO_GO_AUTOMATIQUE`, aucune permission d'écriture, aucune publication.**

## 3 ter. P51E — provenance réelle des règles et cohérence de la lecture

Le contrôle P51D vérifiait la présence de quatre catégories de règles effectives, sans s'assurer que leur **`ruleset_id`** correspondait au ruleset actif considéré conforme. Une combinaison de règles provenant de sources différentes pouvait donner un relevé artificiellement favorable. L'API GitHub fournit pourtant un `ruleset_id` associé aux règles effectivement appliquées à une branche.

P51E corrige ce point : identifiants uniques et concordants entre **la liste des rulesets actifs et leurs détails**, rattachement des quatre règles effectives **au même identifiant**, et contrôle des paramètres réellement applicables aux approbations et aux trois checks universels. Une exception de contournement masquée ou présente sur **un autre ruleset actif** constitue également un obstacle, et non une absence présumée d'exception.

Le mode `--live` vérifie maintenant, avant de conclure, que la PR témoin n'a pas changé de SHA, de base ou de nombre de fichiers **entre la première et la dernière lecture GitHub**. Les mesures recueillies pendant un changement de commit sont rejetées plutôt que mélangées.

Les **15 tests supplémentaires** portent la suite à **99**. L'état `PRECONDITIONS_TECHNIQUES_VISIBLES` reste uniquement un constat de configuration partielle : il ne peut jamais certifier une véritable recette, l'indépendance du responsable, une fusion ou une publication.

Référence API : [GitHub — règles effectives d'une branche](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch). **Aucune action administrative n'est exécutée.**

## 3 quater. P51F — diff GitHub du marqueur d'essai vérifié

Le validateur P51E contrôlait uniquement les noms, statuts et chemins des fichiers ajoutés, laissant la possibilité de déposer du contenu arbitraire dans un `.txt` prétendument inoffensif. P51F impose désormais un **patch textuel complet et minimal**, contenant seulement `P50Y-CANARI:<scénario>`, ou cette ligne suivie de `NONCE:<8 caractères hexadécimaux>`. Il vérifie `additions`, `deletions`, `changes`, les lignes du diff, le dossier autorisé et l'absence de renommage. Un patch binaire, tronqué, très long ou comportant du contenu additionnel reste **bloquant**.

Le rapport produit uniquement un booléen `canary_files_safe` ; le contenu du diff n'est **pas conservé dans les artefacts**. Cette mesure limite les risques de dépôt d'informations personnelles ou de scripts dans les PR témoins futures, sans effectuer les trois essais administratifs ni changer leur décision `NO_GO`. **14 tests ajoutés, suite totale : 113.**

## 4. Critères de réception et prérequis non automatisables

1. Conserver `main` au SHA relevé ou **réévaluer si `main` évolue**; ne jamais assimiler une CI verte à une protection imposée.
2. Solliciter une revue indépendante par un mainteneur réellement habilité **sur la PR consolidée et son HEAD définitif**; ne pas inventer de reviewer.
3. Avant tout déploiement, un administrateur doit protéger `main`, vérifier les règles effectives et les exceptions (`bypass`), confirmer une personne autorisée à approuver et exécuter les **trois essais réels sans fusion**.
4. Ne pas modifier le site, ouvrir de collecte, générer des signatures ni accéder à des documents privés au nom d'un essai; ne jamais utiliser [PR640](https://github.com/M0rdr3x/BenoitCantin/pull/640) comme PR témoin ni la fusionner.
5. Les revues de sécurité du scanner [PR657](https://github.com/M0rdr3x/BenoitCantin/pull/657) et d'identité/statuts [PR638](https://github.com/M0rdr3x/BenoitCantin/pull/638) restent une autre dépendance. Les statuts ne sont pas adoptés et l'existence juridique d'un parti n'est pas affirmée.

Dépendances maintenues : [#135 — protection `main`](https://github.com/M0rdr3x/BenoitCantin/issues/135) et [#662 — vrais réviseurs](https://github.com/M0rdr3x/BenoitCantin/issues/662).

**Décision : NO_GO. Ce document établit un candidat complet à faire examiner, pas un passage en production.**

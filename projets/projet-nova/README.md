# Projet Nova — site public sur benoitcantin.com

**URL publique :** https://www.benoitcantin.com/projets/projet-nova/

**Statut :** projet politique et institutionnel en développement — références publiques candidates, non adoptées.

Projet Nova est une démarche politique citoyenne québécoise en construction. Le site distingue les propositions politiques, les textes de référence candidats, les archives, les validations en cours et toute éventuelle activation future.

## Sources publiques prioritaires
- `official/reference/corpus.md` : architecture institutionnelle et corpus maître public;
- `official/reference/statuts.md` : statuts et gouvernance candidats du Parti Nova;
- `official/reference/programme.md` : programme public actuel;
- `data/sources.json` : manifeste des références et empreintes SHA-256;
- `document.html` : lecteur public permanent de ces références.

## Règles de publication
- La page `programme.html` et le Programme public permanent présentent les orientations politiques actuelles.
- `registre-conformite.html` indique les correctifs réalisés et les validations externes restantes.
- Les anciens PDF sont classés comme archives lorsqu’ils ne représentent plus la position courante.
- Aucun don, prêt, contribution politique ou adhésion officielle à un parti autorisé n’est recueilli sur ce site.
- Le formulaire externe de participation demeure suspendu tant que sa gouvernance des renseignements personnels n’est pas validée.

## Contrôle documentaire
Tout texte appelé à devenir officiel doit avoir un identifiant, une date, un statut, une autorité d’adoption, un journal de changements et une empreinte d’intégrité. Une page Web, une FAQ ou une brochure ne crée jamais une norme absente de la source adoptée.

## Études complémentaires Nova–Sinjira (3 novembre 2026)

Projet Nova demeure le **seul projet politique en activité** dans cette arborescence; SCQ est une référence historique, non une position en vigueur. **SINJIRA™** est un univers narratif distinct qui inspire certains principes de dignité, de preuve et de protection sans surveillance dans les études Nova.

L'architecture de travail `architecture-nova-sinjira.md` et sa page `architecture-nova-sinjira.html` sont accompagnées d'une page de mise en œuvre `mise-en-oeuvre-nova-sinjira.html` et de quatre dossiers candidats dans `official/working/` : plan d'exécution (IMP-001), protocole de santé RAMQ (SAN-001), cahier des charges des prestations (CON-001) et registre des arbitrages (DEC-001).

**Ces fichiers ne sont pas des sources officielles candidates du manifeste `data/sources.json`** : ils sont publiés pour discussion et examen externe. Leur publication ne déclenche aucune expérimentation, obligation, financement, changement de propriétaire ou modification constitutionnelle. Avant de les intégrer dans `official/reference/`, il faudrait une décision formelle, une nouvelle version datée, une validation pertinente et l'actualisation de l'empreinte SHA-256 du manifeste.

## Registre financier sectoriel (3 novembre 2026)

Le nouveau dossier `official/working/modele-financier-services-nova-sinjira-v1.md` documente la méthode de comparaison du coût public, du coût réel de production et du coût social partiel.

Les fichiers `data/reperes-financiers-nova-sinjira-2026.json` et `data/registre-donnees-services-nova-sinjira.json` séparent les repères budgétaires publics des **14 fiches de besoins en données**, dont les montants non vérifiés sont laissés à `null`.

Le site propose `comparateur-couts-services.html` (saisie locale sans tarifs par défaut) et `registre-donnees-nova-sinjira.html` (état de la donnée et références potentielles). Calcul : `assets/comparateur-financier-core.mjs` et `assets/comparateur-financier-ui.mjs`. Tests : `tests/comparateur-financier.test.mjs`, `tests/registre-donnees.test.mjs`. Commande depuis la racine du dépôt : `node --test projets/projet-nova/tests/*.test.mjs`.

Ces études **ne sont ni une simulation officielle du budget, ni des économies réalisées, ni des règlements adoptés**. Aucun de ces nouveaux fichiers n'est inclus au manifeste des quatre références candidates `data/sources.json`. Toute incorporation éventuelle requiert validation, versionnement, nouvelle empreinte et autorité de décision identifiée.

## Validation externe requise
Le caractère « document de référence » ne remplace jamais les validations juridique, financière, électorale, cybersécurité ou accessibilité requises.

## Traçabilité
Les anciennes versions retirées du site actif restent conservées dans l’historique Git. Elles servent à retracer l’évolution du projet, mais ne sont pas des sources publiques prioritaires.

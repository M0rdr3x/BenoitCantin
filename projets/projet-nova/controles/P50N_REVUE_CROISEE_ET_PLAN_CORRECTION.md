# Projet Nova — P50N : revue croisée de versions et ordonnance de correction

**Date : 14 octobre 2026.** **Statut : NO_GO — examen technique préliminaire, sans revue humaine formelle ni autorisation.**

## 1. Décision de cadrage

Les jalons P50F–P50M ont documenté les conditions de publication. P50N ne réédite pas ces matrices : il **vérifie matériellement** que les corrections de communication déjà proposées dans les PR 636 et 638 se retrouvent dans la branche de validation 640, que leurs périmètres ne se recouvrent pas et que le manifeste documentaire de la PR 638 est cohérent.

**PR 640 : branche de validation uniquement. NE PAS FUSIONNER.** Les corrections destinées à une éventuelle publication sont exclusivement les PR 636 et 638, après leur revue et autorisation propres.

## 2. Sources et empreintes vérifiées par consultation du connecteur GitHub

### Références des arbres
- `main` : `9ed5f70cbe7022f25a679346a1288701f3b09067`
- PR 636 : `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb` — 5 fichiers
- PR 638 : `e027b0ca130fe91b00e52d9e9fe2f1b301f4b47e` — 9 fichiers
- PR 640 : `332afe7d9d73390feb41b0deb588692f3c73d48d` — 14 fichiers

**Observation matérielle** : aucun chemin de fichier modifié ne se retrouve à la fois dans le diff des PR 636 et 638; la liste des 14 chemins de la PR 640 correspond à leur union. Cela ne prouve ni la faisabilité d'une fusion ultérieure sans conflit avec de nouveaux commits ni l'absence de toute interdépendance comportementale.

### Concordance des trois pages

| Page | `main` | Correction proposée | PR 640 | Constat |
| --- | --- | --- | --- | --- |
| `participer.html` | `832a73caf4d1a7490523422c9d677974df0bc8f0` | PR636 `ef037f1ef6257c676573a80afae060b4e965bb25` | **Même blob** `ef037f1...` | Ancien message de formulaire de préadhésion supprimé dans la proposition |
| `avis-legal.html` | `4f35dba55c01f744fad9247354e77cd51c9d7a3c` | PR636 `602dc790de1416a3bc3806f6a0d328a489925752` | **Même blob** `602dc...` | Ancien énoncé affirmant l'usage de formulaires remplacé |
| `code-conduite.html` | `155e5aae78ef7220ba3de39483248dfd98052faf` | PR638 `34a00ecae9592846d6578b74e03796a768b2450f` | **Même blob** `34a00...` | Ancienne dénomination institutionnelle corrigée |

Les blobs de `participer.html` et `avis-legal.html` sont **inchangés** dans la PR 638 relativement à `main`; le blob de `code-conduite.html` est **inchangé** dans la PR 636. Ce résultat isole proprement les deux responsabilités éditoriales.

**Limite de périmètre** : la cohérence des trois blobs et des 14 chemins ne vaut ni revue des dépendances complètes (scripts, navigation, autres pages) ni test de production.

## 3. Deux risques éditoriaux actuellement visibles

### E01 — participation
La branche `main` contient encore l'annonce d'un « formulaire intégré de soutien et de préadhésion » sur la page `participer.html`, alors que `recrutement.html` annonce une participation volontaire par courriel et la suspension des formulaires externes.

**Mesure proposée** : revue technique et juridique de la PR 636, avec attention au titre, métadonnées et liens de l'ancien PDF; vérifier que la version corrigée ne présente pas d'adhésion officielle.

### E02 — avis légal et identité
Sur `main`, `avis-legal.html` comporte toujours une déclaration sur l'utilisation des formulaires, et `code-conduite.html` emploie une gouvernance au nom d'un parti futur comme si la structure pouvait être en fonction.

**Mesure proposée** : revue de la PR 636 pour l'avis légal et de la PR 638 pour l'identité, les métadonnées sociales et les statuts non adoptés. Conserver la mention explicite du caractère préparatoire.

## 4. Troisième contrôle objectif : manifeste documentaire

La PR 638 modifie `official/reference/statuts.md` **et** sa valeur `sha256` dans `data/sources.json`. Avant toute fusion éventuelle, il faut vérifier cryptographiquement que le SHA-256 des octets réels du document est égal à celui déclaré dans le manifeste. La branche 640 doit présenter la même concordance.

**Nouveau contrôle P50N** : un script Python lit *quatre arbres locaux* et vérifie à la fois les blobs Git exacts, les trois corrections éditoriales, les surfaces HTML de collecte/paiement, l'indépendance des corrections et le digest du document `statuts.md`. Il ne contacte aucun site ni ne transmet de données. Une GitHub Action lit quatre SHA figés avec des droits en **lecture seule**. **Aucune publication ni fusion n'est incluse.**

## 5. Vérifications humaines non réalisées

Lors du relevé P50N, le connecteur GitHub indique **0 revue formelle** pour chacune des PR 636, 638 et 652. Les autres statuts devront également être relus avant décision. Les comptes ayant accès au dépôt ne sont pas réputés posséder un mandat de décision politique ou juridique.

Il manque donc, à obtenir **hors dépôt** et auprès d'acteurs habilités :
- contrôle rédactionnel et technique indépendant de PR 636 (cinq fichiers);
- contrôle rédactionnel et technique indépendant de PR 638 (neuf fichiers, manifeste inclus);
- qualification juridique du porteur et des annonces du site;
- examen des flux réels du contact courriel, confidentialité et sous-traitants;
- habilitation de la personne autorisant et exécutant une modification publique;
- sauvegarde opérationnelle, procédure de retour arrière et critères d'incident.

Le travail automatisé et la présente note **ne remplacent aucun de ces contrôles**.

## 6. Ordonnance de traitement — actions réellement exécutables

**A0 — Sans changement public** : figer les SHA et consigner ces constats. Si un SHA a changé, interrompre et reprendre l'analyse : la concordance passée devient historique.

**A1 — Revue autonome PR 636** : inspecter précisément les corrections `participer.html` et `avis-legal.html`, les liens et les tests; enregistrer les demandes de modification et un avis humain signé ou traçable.

**A2 — Revue autonome PR 638** : vérifier la nouvelle identité de la page de conduite, les projets de statuts, le manifeste SHA-256 et le scanner des appellations; vérifier la cohérence des mentions « future » et « non adoptées ».

**A3 — Préparation de l'intégration** : après résolution des avis, vérifier les nouvelles bases, les conflits, la CI, le plan de rollback. La PR 640 demeure **non fusionnable**, même si ses tests réussissent. L'ordre des fusions éventuelles des PR 636/638 doit être déterminé par le mainteneur habilité selon les SHA alors en vigueur.

**A4 — Décision séparée** : le décideur dûment habilité précise le périmètre, les SHA, le responsable technique et les conditions de mise en ligne. Tant que le dossier reste incomplet : **NO_GO**.

**A5 — Recette après action autorisée seulement** : observer les URL réelles `participer`, `avis-legal`, `code-conduite`, `recrutement`, `contact`, `confidentialite`, les réponses HTTP brutes, redirections, cache, scripts, liens, formulaires, paiements et textes affichés; faire signer la clôture indépendante.

## 7. Blocages maintenus et hiérarchie de décision

Les PR 645–652 constituent des dossiers de contrôle en brouillon; leur présence ne confère pas de pouvoir nouveau, et leur fusion ne doit pas masquer la correction éditoriale des PR 636/638. La base maîtresse V3.40 et les portes institutionnelles précédemment consignées demeurent inchangées. Aucune contribution, adhésion, collecte de signatures, paiement ou nouveau formulaire n'est autorisé ici.

**NO_GO = aucune publication automatique ni fusion non autorisée.**
**La compatibilité technique = une condition utile, jamais une autorisation.**
**PR 640 = ne pas fusionner.**

## 8. Résultat et suite recommandée

P50N fournit une preuve de **reproductibilité technique**, puis recentre la progression sur deux revues humaines et une décision clairement habilitée, plutôt que sur l'accumulation de nouveaux registres. Si la compatibilité passe, la prochaine étape utile sera **P50O : réception des deux avis indépendants sur PR 636/638 et constitution d'un plan de publication signé**, seulement si des titulaires réels peuvent produire ces éléments.

*Aucune observation HTTP de production, aucune revue humaine et aucune validation légale individuelle n'est présentée comme ayant eu lieu dans cette note.*

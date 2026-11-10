# Projet Nova — P50P : preuve d'exécution du correctif PR 655

**Date d'ouverture : 15 octobre 2026 · Jalon technique préparatoire · NO_GO publication**

## 1. Objectif vérifiable

Ce jalon doit répondre à la lacune identifiée à P50O : les **26 tests ajoutés à la PR 655** sont-ils réellement exécutés sur le bon code et ses cinq pages, et les **8 contre-exemples** que ne détectait pas le validateur original de la PR 636 sont-ils maintenant tous reconnus ?

La preuve attendue est un **workflow GitHub Actions de lecture seule** lancé par cette PR, avec journaux inspectables, incluant la suite unitaire du correctif, le contrôle des cinq pages réelles de la branche candidate, une comparaison du diagnostiqueur P50O sur les deux validateurs et la vérification des empreintes de fichiers.

Une preuve de bon fonctionnement du validateur **n'est pas** une preuve de conformité de la messagerie, de retrait des anciennes URL, de sécurité du site déployé, d'autorisation électorale, de compétence juridique, de revue humaine ou de publication réussie.

## 2. Objets examinés — commits exacts

| Objet | SHA Git utilisé | Rôle |
| --- | --- | --- |
| `main` relevé avant l'intervention | `9ed5f70cbe7022f25a679346a1288701f3b09067` | Constat du dépôt, non modifié |
| PR 636, validateur original | `6cd38faf1124a9bcbb2be1beaa12bcd14a85f9fb` | Comparaison avant correction |
| PR 655, validateur corrigé et cinq pages | `8541f761be8dbabda0c3f024f8969562ab816bc7` | Référence exacte des nouveaux tests |
| PR 654, diagnostiqueur P50O | `baf7674b5b81ceb5dd074bcf4c1dd732c1ea15ad` | Onze contre-exemples reproductibles |
| PR 640, intégration purement expérimentale | `332afe7d9d73390feb41b0deb588692f3c73d48d` | **NE PAS FUSIONNER** |

**La PR 655 ne vise pas `main` :** sa base est la branche de la PR 636 `review/p49q-coherence-participation-2026-10-11`. La présente PR P50P n'édite pas ces branches et ne fusionne aucune d'elles.

## 3. Contrôles effectivement programmés dans la CI P50P

| Étape | Critère d'acceptation du contrôle |
| --- | --- |
| T01 | Le validateur PR 655 compile sous Python 3.11 |
| T02 | La suite de **26 tests** est exécutée sur les octets du SHA `8541f761...`, sans copie remplacée |
| T03 | `validate_nova_publication_p50b.py` refuse les cinq pages si un mécanisme interdit y est trouvé, et réussit seulement si son contrôle source est cohérent |
| T04 | Le diagnostiqueur P50O retrouve **8 angles morts** dans la version originale du validateur PR 636 |
| T05 | Le même diagnostiqueur mesure **0 angle mort sur les 11 sondes** dans la version PR 655 |
| T06 | Les cinq empreintes de *blobs Git* contrôlées correspondent exactement aux pages candidates |
| T07 | Toutes les sorties de diagnostic déclarent `NO_GO_AUTOMATIQUE` |
| T08 | Aucun changement de `main`, aucune action de déploiement, aucune collecte de données |

**Attention :** un workflow au vert confirme uniquement T01–T07 sur les versions figées. T08 exige la lecture des statuts GitHub en fin de jalon; le workflow ne certifie pas les opérations externes ou la production. Un contrôle échoué appelle un correctif ciblé avec nouveau SHA et nouvelle vérification, jamais une dérogation automatique.

## 4. Questions ouvertes, même en cas de tests réussis

- **Couverture :** cette solution est un scanner statique de cinq pages, pas un audit des scripts externes exécutés, des redirections serveur, des CSP, de la collecte en production ou de tous les fournisseurs possibles.
- **Comportement réel :** aucune réponse HTTP live, interaction avec un fournisseur ou contenu de la boîte courriel n'a été inspecté par ce jalon.
- **Provenance :** une branche maintenue sous GitHub peut évoluer; toute modification au SHA réactive la nécessité d'une nouvelle comparaison.
- **Mandats :** ni l'assistant, ni le workflow, ni la possession d'un accès GitHub ne représentent automatiquement le responsable habilité du projet.
- **PR 638 :** sa validation autonome de l'identité Projet Nova et du document de statuts demeure exigée; P50P ne constitue pas son approbation.
- **Documents publics :** les anciennes déclarations sur `main` restent présentes tant qu'aucune correction n'a été autorisée et diffusée.

## 5. Ordonnance réelle de correction et de décision

1. Vérifier les journaux de la CI **P50P** et les résultats des 26 tests, du contrôle des cinq pages et du diagnostic 8 → 0.
2. Si erreur : corriger la branche PR 655 **par nouvelle PR ou par intervention approuvée** puis répéter les tests au nouveau SHA, sans mettre à jour silencieusement un rapport signé.
3. Si les tests réussissent : présenter la PR 655 à un mainteneur et à un réviseur indépendants compétents; après leur décision, envisager seulement l'intégration **dans la PR 636**, jamais dans `main` par cet acte.
4. Faire examiner séparément les textes de la PR 636, le statut juridique du projet, les conditions de confidentialité du contact courriel, la PR 638, les statuts proposés, les délais et la sécurité.
5. Confirmer le rôle du décideur et de l'opérateur de publication, la sauvegarde et le retour arrière effectifs, avec preuves conservées hors dépôt.
6. Décider expressément si les PR de correction peuvent avancer, sur des SHA précis. La réussite CI n'est jamais un vote, un avis légal ni une habilitation.
7. **Après seulement** une publication effectivement autorisée : vérifier HTTP/HTTPS, caches, liens, CTA, formulaires, paiements et redirections; consigner ensuite B12/B14 avec un réviseur indépendant.
8. **PR 640 — NE PAS FUSIONNER.** Ne pas réactiver les formulaires, dons, signatures, adhésions ou services de réception par cet exercice.

## 6. Statuts institutionnels préservés

Projet Nova est l'identité active; « Parti Nova » demeure une dénomination future conditionnelle. La base maître V3.40 est inchangée. P2-C0-49 EN_COURS; W0 NON_CLOTUREE; W1 NO_GO; W2–W4 NON_AUTORISEES; E26 0/20; pouvoirs 0/14; pièces financières 0/16; quatorze portes financières bloquantes : aucune levée.

**Décision P50P : NO_GO publication**, quel que soit le résultat technique. Une revue indépendante, une décision expresse et la recette de production restent à accomplir.

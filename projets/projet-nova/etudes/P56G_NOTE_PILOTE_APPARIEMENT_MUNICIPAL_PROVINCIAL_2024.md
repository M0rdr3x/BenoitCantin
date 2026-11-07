# Projet Nova — P56G : premier dossier pilote provincial-municipal réel, sans fausse concordance

**7 novembre 2026 — Étude candidate NON ADOPTÉE, NON CERTIFIÉE.** Le baromètre P55N reste à **53 %**, fourchette prudente de 45 à 60 %. Le cadre fiscal Nova n'a aucun taux définitivement adopté; P52B conserve 600 montants budgétaires inconnus, P52D 720 incidences inconnues. La décision demeure **NO_GO_AUTOMATIQUE**.

## 1. Pourquoi P56G change réellement la qualité des dossiers

P56D a démontré des mécanismes de consolidation sur 12 **flux fictifs**. P56E a intégré les enveloppes **prévues** pour quatre programmes en année civile 2027. P56F a consigné un agrégat **historique 2023** de transferts municipaux, non directement comparable aux quatre prévisions 2027.

**P56G sélectionne pour la première fois un même organisme municipal identifiable, avec son rapport financier consolidé et deux documents ministériels détaillant des programmes de transferts.** Le choix est celui d'un **cas pilote méthodologique**, sans extrapolation aux autres municipalités ni affirmation d'une contrepartie comptable déjà prouvée.

Municipalité pilote : **Ville d'Alma (code MAMH 93042)**, année municipale terminée le **31 décembre 2024**. Aucune donnée privée de contribuable ou salarié n'est utilisée.

## 2. Pièce primaire municipale : comptes consolidés 2024

- [Rapport financier 2024 et autres documents — Ville d'Alma, code 93042](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-93042.pdf), état consolidé des résultats **S7**; attestation du trésorier datée du 12 mai 2025; rapport contenant un avis d'auditeur sur les comptes de la municipalité.
- [Communiqué municipal du 12 mai 2025](https://www.ville.alma.qc.ca/rapport-financier-2024/) corroborant l'existence des comptes et l'ordre de grandeur des compensations.

Les rubriques consolidées de 2024 du rapport municipal sont :

| Rubrique municipale 2024 | Montant observé (CAD) | Nature |
|---|---:|---|
| Compensations tenant lieu de taxes | **5 514 445 $** | Recette consolidée municipale, toutes origines pertinentes de cette rubrique |
| Transferts | **5 578 416 $** | Recette consolidée municipale, plusieurs programmes et contreparties |
| **Total des revenus consolidés** | **93 994 134 $** | Résultat comptable municipal |
| **Total des charges consolidées** | **89 364 728 $** | Résultat comptable municipal |
| **Excédent comptable consolidé** | **4 629 406 $** | 93 994 134 − 89 364 728 |

Le communiqué de la Ville mentionne un **excédent de fonctionnement à des fins fiscales** d'un autre ordre de grandeur; il ne faut pas l'assimiler au résultat comptable consolidé ci-dessus. Les transferts municipaux ne constituent pas les seules recettes municipales et le résultat comptable n'est pas une réserve entièrement disponible.

## 3. Deux pièces ministérielles à rapprocher, mais pas encore rapprochées

- [Liste MAMH des engagements financiers — juillet 2024](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_juillet_2024.pdf), **programme 40350**, ligne **1193**, Ville d'Alma, **3 320 039 $** au titre des compensations tenant lieu de taxes pour les immeubles du réseau de la santé, des services sociaux et de l'éducation.
- [Liste MAMH des engagements financiers — avril 2024](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_avril_2024.pdf), **programme 40561**, ligne **746**, Ville d'Alma, **1 665 580 $** de partage de la croissance d'un point de TVQ.

Ces documents présentent des montants sous le libellé **« versement »** au sein de listes d'engagements financiers de **l'exercice provincial 2024-2025**. **Le libellé ne prouve pas à lui seul l'encaissement à une date précise ni sa constatation dans l'exercice civil 2024 de la municipalité.**

| Hypothèse de mise en relation | Pièce provinciale | Poste municipal possible | État |
|---|---:|---:|---|
| H01 : compensations réseau santé-éducation | 3 320 039 $ (40350) | 5 514 445 $ (toutes compensations) | **Non apparié** : sous-catégorie, dates et montant différents |
| H02 : part de croissance TVQ | 1 665 580 $ (40561) | 5 578 416 $ (tous transferts) | **Non apparié** : programme particulier, dates et montant différents |

Aucun des deux « écarts arithmétiques » apparents ne peut être désigné comme **manque à gagner**, comme **dépense non justifiée** ou comme **économie Nova**. Les mêmes montants peuvent être reconnus dans un exercice civil différent, ou ventilés dans une autre composante selon les conventions. Des corrections ou ajustements peuvent aussi exister.

## 4. Preuves encore à obtenir pour une véritable écriture réciproque

| Pièce | Justificatif nécessaire | État |
|---|---|---|
| G01 | Ventilation de la rubrique municipale « compensations » par organisme payeur et programme | **Non obtenu** |
| G02 | Bordereau de versement daté du programme 40350 et compte provincial correspondant | **Non obtenu** |
| G03 | Ventilation municipale des transferts incluant le programme 40561 et l'année de constatation | **Non obtenu** |
| G04 | Pièces comptables provinciales et municipales attestant la même transaction et son exercice | **Non obtenu** |
| G05 | Revue d'un comptable municipal indépendant, avec réserves et correction des écarts | **Non obtenu** |

Le rapport financier municipal est publiquement disponible, mais l'outil de consultation PDF a retourné une **erreur de cache lors des demandes de captures visuelles** et le fichier binaire original n'a pas pu être téléchargé indépendamment. Les montants sont donc relevés dans l'extraction officielle indexée et soutenus par les pages municipales accessibles, **sans prétendre qu'une comparaison visuelle du même binaire ou une empreinte SHA-256 a été effectuée**. Ce contrôle reste explicitement ouvert.

## 5. Contrôles techniques et statut

Le registre `P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json` sépare quatre lignes publiques (deux municipales, deux provinciales), deux liens de rapprochement **non confirmés**, cinq pièces obligatoires encore absentes et les exercices incomparables.

Le programme `scripts/verifier_pont_provincial_municipal_nova_p56g.py` vérifie les références, les montants exacts en dollars, les catégories, les codes 40350/40561, l'identité de l'organisme, l'addition du résultat comptable, les dates, les écarts de périmètre et l'absence de GO automatique. La suite de tests rejette toute création fictive d'une date de paiement, d'un montant rapproché, d'une preuve d'audit Nova ou d'une économie.

Commande depuis la racine du dépôt :

```bash
python scripts/verifier_pont_provincial_municipal_nova_p56g.py \
  --dossier projets/projet-nova/etudes/P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json
```

Le mode `--exiger-appariement-certifie` refuse la certification (code 3); tout fichier de sortie existant est protégé. **Zéro ligne provinciale-municipale est appariée avec preuves**. C'est un résultat de contrôle, non l'affirmation qu'aucun transfert n'a réellement été versé.

## 6. Suite prioritaire P56H

P56H doit chercher la ventilation exacte de la rubrique des compensations et des transferts municipaux **pour 2024**, ainsi que les dates de versement des programmes provinciaux, puis produire une première écriture réellement appariée. À défaut de source suffisamment précise, conserver le statut « non apparié ». Compléter ensuite le modèle fiscal et les protections de services avec des données 2027–2036 sourcées, plutôt que d'extrapoler une municipalité à tout le Québec.

Le score P55N **reste 53 %** : cette étape améliore la traçabilité documentaire, mais ne valide aucun budget décennal, montant municipal réel payable par Nova, avantage fiscal ou financement de la transition souveraine. **Aucun changement public, aucune fusion de PR, aucun taux fiscal adopté et aucune modification de SINJIRA.**

# Projet Nova — P56H : rapprochement numérique de deux programmes provinciaux et des annexes municipales 2024

**7 novembre 2026 — étude candidate, non adoptée, non certifiée. Décision : NO_GO_AUTOMATIQUE.**  
**Maturité estimée P55N : 53 % (fourchette 45–60 %), inchangée.** La validation technique ne démontre pas la faisabilité d'une réforme fiscale.

## 1. Ce qui change par rapport au jalon P56G

P56G avait identifié des montants dans les comptes consolidés de la Ville d'Alma et deux montants du ministère des Affaires municipales et de l'Habitation, sans répartition suffisante. Le présent P56H exploite désormais l'**analyse des revenus consolidés, annexe S27**, du [rapport financier municipal 2024, Ville d'Alma, MAMH code 93042](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-93042.pdf).

**Qualification de preuve essentielle :** l'annexe S27 est explicitement intitulée « Non audité ». Même si le rapport financier contient des états financiers consolidés audités, **il ne faut pas attribuer automatiquement l'opinion d'audit à toutes les pages complémentaires S27**. Les PDF consultés ont fourni du texte indexé détaillé; les tentatives de captures visuelles ont échoué en raison d'une erreur de cache. Aucune copie binaire canonique ni empreinte SHA-256 n'est enregistrée dans ce jalon. Les contrôles documentaires ont donc cette réserve explicite.

Les données ministérielles proviennent de deux publications distinctes. Le **programme 40350** figure dans la [liste des engagements de juillet 2024, PDF index 55, ligne 1193](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_juillet_2024.pdf). Le **programme 40561** figure dans la [liste d'avril 2024, PDF index 49, ligne 746](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_avril_2024.pdf). Ces listes désignent des « versements » dans le cadre de **l'exercice provincial 2024-2025**, sans constituer la preuve de la date d'encaissement dans l'année civile municipale 2024.

## 2. Correspondance numérique exacte : programme 40350

L'annexe S27, **page imprimée 47, lignes 31–33**, énumère les recettes municipales réalisées en 2024 au titre des immeubles des réseaux :

| Sous-catégorie municipalité, 2024 | Montant CAD |
|---|---:|
| Santé et services sociaux, ligne 31 | 1 163 325 $ |
| Cégeps et universités, ligne 32 | 576 300 $ |
| Écoles primaires et secondaires, ligne 33 | 1 580 414 $ |
| **Somme des trois lignes** | **3 320 039 $** |
| MAMH, **programme 40350**, ligne 1193, « versement » 2024-2025 | **3 320 039 $** |
| **Différence numérique** | **0 $** |

La somme des trois sous-catégories est **arithmétiquement identique** au montant ministériel publié. Cela renforce la plausibilité d'une correspondance de programme et permet de cibler une vérification précise. Cela **ne prouve toujours pas** : la date de paiement, l'écriture comptable provinciale, le revenu municipal constaté pour la même transaction, un éventuel ajustement ou la concordance des exercices.

Ne pas ajouter **3 320 039 $** aux **5 514 445 $** de compensations tenant lieu de taxes de la Ville : les trois rubriques S27 sont **déjà comprises dans cette catégorie municipale plus large**.

## 3. Proximité sans concordance exacte : programme 40561

L'annexe S27, **page imprimée 52, ligne 136**, donne pour l'année civile 2024 le partage de la croissance d'un point de TVQ à Alma :

| Comparaison de programme 40561 | Montant CAD |
|---|---:|
| Municipalité, annexe S27 ligne 136 | 1 665 578 $ |
| MAMH, liste d'avril 2024, ligne 746 | 1 665 580 $ |
| **Écart municipal moins provincial** | **−2 $** |

La cause de cet écart de **2 $** n'est pas prouvée. Elle peut dépendre de dates, d'une méthode de calcul, d'un ajustement ou d'un autre élément, mais **aucune de ces explications n'est retenue comme fait sans pièce justificative**.

Le montant municipal fait partie des **5 578 416 $** de transferts consolidés 2024 d'Alma; ne pas ajouter à nouveau le transfert de la TVQ à cette rubrique.

## 4. Ce qui est démontré et ce qui ne l'est pas

| Contrôle | Résultat |
|---|---|
| Deux références municipales détaillées et deux programmes provinciaux identifiés | **Oui, sources textuelles publiées** |
| Égalité arithmétique des trois rubriques au programme 40350 | **Oui, écart 0 $** |
| Montant TVQ quasi identique au programme 40561 | **Oui, écart −2 $** |
| Confirmation de la même écriture réciproque, de la date et du paiement | **Non** |
| Examen visuel réussi du binaire PDF exact + empreinte SHA-256 | **Non** |
| Avis indépendant sur les correspondances | **Non** |
| Données 2027–2036 de la réforme fiscale Nova renseignées | **Non** |
| Économie publique ou financement Nova certifié | **Non** |

Le registre `P56H_DECOMPOSITION_REVENUS_ALMA_2024_CORRESPONDANCES_PROVINCIALES.json` fixe les quatre rubriques S27, les deux lignes ministérielles, les deux comparaisons et les cinq pièces restant à obtenir. Le programme `scripts/verifier_correspondances_revenus_municipaux_nova_p56h.py` lit également le dossier **P56G existant** pour empêcher les divergences accidentelles, et retourne les deux écarts sans autoriser de changement des comptes ni des budgets décennaux.

Exécution depuis la racine du dépôt :

```bash
python scripts/verifier_correspondances_revenus_municipaux_nova_p56h.py \
  --decomposition projets/projet-nova/etudes/P56H_DECOMPOSITION_REVENUS_ALMA_2024_CORRESPONDANCES_PROVINCIALES.json \
  --pilote-p56g projets/projet-nova/etudes/P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json
```

Le mode `--exiger-appariement-certifie` échoue volontairement (code de sortie 3). Les rapports existants ne sont pas écrasés.

## 5. Travaux encore nécessaires pour un appariement et une progression du programme

1. Récupérer **les trois PDF binaires originaux**, vérifier SHA-256 et rendre visuellement les pages concernées. Documenter les éventuelles différences texte/image.
2. Obtenir les bordereaux de paiement du **40350** et du **40561**, leurs périodes, leurs ajustements et leurs bénéficiaires.
3. Vérifier, sur les journaux de comptabilité municipale et les pièces ministérielles, si les flux ont été constatés au **même exercice** et selon les **mêmes droits**. Expliquer ou justifier les 2 $.
4. Faire signer un avis de rapprochement par un comptable municipal indépendant, et préciser le périmètre de consolidation dans lequel une élimination serait admissible.
5. Étendre seulement ensuite à des municipalités représentatives et aux catégories P52B; ne pas extrapoler une seule ville à tout le Québec.

**Suivi :** 2 rapprochements **numériques documentés**, **0 appariement comptable certifié**. Le budget fiscal décennal conserve **600 valeurs inconnues**, l'étude d'incidence **720**, et le baromètre de complétude reste **53 %**. Le problème des taux fiscaux et celui du financement des services publics ne sont pas résolus. Aucune suppression de taxe, de cotisation, de transfert municipal, de droit social, d'emploi ou de service n'est déclarée possible.

**Statut : NO_GO_AUTOMATIQUE.** Aucune dépense, aucun contact externe, aucune modification de SINJIRA ou de `main`, aucune fusion de la PR et aucune activation du programme public.

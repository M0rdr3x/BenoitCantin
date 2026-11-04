# P55D — Dossier de recevabilité pour une revue indépendante (3 novembre 2026)

**Statut : inventaire et passation préparatoires, non certifiants.** P55D convertit les références documentaires P55C en une liste structurée de pièces, contrôles, responsabilités et conditions d'arrêt. Il **ne sollicite ni ne mandate** un expert, ne demande aucun devis, ne transmet aucun PDF et n'engage aucune dépense.

## Références et conditions d'entrée

Les cinq observations historiques de 2024 restent `P54E-V-001`, `P54E-M-001`, `P54O-DATE-001`, `P54E-M-002` et `P54E-M-003`. Il s'agit de **quatre dossiers indéterminés et d'une date/année probable**, et non de montants financiers. Les deux PDF publics (Ville de Québec et MAMH organisme 23027) doivent être disponibles hors Git, identiques aux versions de référence P54Q (taille + SHA-256) et relus par l'outil de reproduction historique P54Q/P55C. Les offsets NFKC ne sont **pas** des coordonnées visuelles.

Une empreinte concordante prouve uniquement l'égalité des octets avec la référence historique, **pas** l'émission institutionnelle ni la qualification professionnelle. Toute édition différente est mise en réserve; il est interdit de remplacer silencieusement les empreintes historiques.

## Huit exigences par observation — 40 positions au total

| Code | Livrable et question de vérification |
|---|---|
| `ORIGINAL_VERSIONNE` | Copie source originale, provenance, édition, droit d'accès et chaîne de conservation |
| `PAGE_VISUELLE` | Confirmation par une personne habilitée sur la page PDF |
| `EXTRACTION_ET_CONTEXTE` | Correspondance entre texte NFKC et contexte visuel |
| `QUALIFICATION_UNITE_EXERCICE` | Nature date/folio/référence/valeur, unité, exercice, signe et colonne |
| `PORTEE_JURIDIQUE_AUDIT` | Portée du R.A.V.Q. 1435 et limites du rapport d'audit spécialisé |
| `PERIMETRE_ET_CONSOLIDATION` | Réconciliation Ville–RTC–SOMHAC, opérations réciproques et éliminations |
| `CONTRE_REVUE_ET_RESERVES` | Revue contradictoire, conflits, désaccords, réserves et suspensions |
| `EMPLOIS_SERVICES_POUVOIR_ACHAT` | Effets documentés sur la continuité des services, les emplois et le pouvoir d'achat |

Le **fichier privé P55D** comporte 40 cases, chacune ayant un état de suivi strictement déclaratif : `A_COLLECTER`, `PREPARATION_DECLAREE_NON_ATTESTEE`, `RESERVE`, `INACCESSIBLE` ou `SUSPENDU`. Il est lié aux octets de la fiche P55C par SHA-256 **conservé uniquement hors Git**. Aucune catégorie « reçue authentifiée » ou « certifiée » n'existe dans le schéma.

Le statut `PREPARATION_DECLAREE_NON_ATTESTEE` requiert, pour la même observation, les huit préparations P54Z et les dix P55A et une relecture P55C déclarée avec contre-lecture distincte déclarée. Cela reste une **déclaration non vérifiée** : aucun expert n'est authentifié. Les réserves et suspensions de P54Z, P55A et P55C ne peuvent être effacées par P55D.

## Circuit humain requis pour une remise réelle

Le **responsable documentaire à désigner** devra obtenir légalement et versionner les publications, distinguer leur authenticité et les copies de travail, puis gérer les droits d'accès.

Les **lecteur et contre-lecteur à désigner** devront examiner les cinq pages/occurrences sur les PDF, classer date/folio/référence/valeur, expliquer les contradictions et signer leur propre revue suivant une procédure légitime et confidentielle. Les identités, preuves et signatures ne doivent pas être ajoutées au dépôt GitHub.

Deux projets de mandat P54H existent, mais **aucun contrat n'a été signé** : `MANDAT-COMPTABLE-2024` pour le périmètre, les comptes réciproques et les unités (CPA habilité) et `MANDAT-JURIDIQUE-2024` pour le droit municipal et le R.A.V.Q. 1435 (juriste habilité). La compétence, les ordres professionnels pertinents, les conflits d'intérêts, la confidentialité, les honoraires et les autorisations doivent être évalués par des personnes compétentes **hors logiciel**.

Le dossier peut légitimement conclure à l'absence d'écart, à l'insuffisance des pièces ou à une réserve. Il ne sert pas à fabriquer une économie.

## Utilisation locale uniquement, après réception réelle des pièces

L'environnement local doit respecter `pypdf==5.9.0` (P54Q), les fichiers privés `0600` et l'interdiction des liens symboliques. Les PDF et fiches privées doivent être **hors du dépôt**.

Créer une matrice privée après vérification des deux sources, des cinq positions et des fiches amont :

```bash
python scripts/preparer_dossier_experts_nova_p55d.py \
  --ville-pdf /hors_git/ville2024.pdf --mamh-pdf /hors_git/mamh2024.pdf \
  --declarations-p54z /hors_git/p54z.json \
  --relecture-p55a /hors_git/p55a.json \
  --fiche-p55c /hors_git/p55c.json \
  --creer-suivi-prive /hors_git/p55d.json
```

Vérifier ensuite cette fiche sans en publier les données :

```bash
python scripts/preparer_dossier_experts_nova_p55d.py \
  --ville-pdf /hors_git/ville2024.pdf --mamh-pdf /hors_git/mamh2024.pdf \
  --declarations-p54z /hors_git/p54z.json --relecture-p55a /hors_git/p55a.json \
  --fiche-p55c /hors_git/p55c.json --suivi-prive /hors_git/p55d.json \
  --bilan-public /hors_git/p55d_bilan.json
```

Un plan public **neutre** et un bilan non certifiant peuvent être produits sans aucune pièce : `python scripts/preparer_dossier_experts_nova_p55d.py --plan-public p55d_plan.json --bilan-public p55d_bilan.json`. Ces sorties ne contiennent ni chemin privé, ni empreinte de fiche, ni offset, ni jeton, ni coordonnées personnelles.

Codes de sortie : **0** pour un traitement structurel non certifiant; **2** pour une entrée ou une chaîne de preuve invalide; **4** si les versions/reproductions ne permettent pas l'ouverture des fiches; **3** pour le refus de `--exiger-transmission`.

## Verrous préservés

Quatre dossiers P54E et la date/année probable restent ouverts. Il reste 40 tâches P54N, dix blocages P54O, 96 contrôles P54B et huit contrôles P54C non attestés. Il n'y a **aucune économie certifiée** et aucune autorisation de dépense ou de transmission. Les éliminations Ville–RTC–SOMHAC ne peuvent être comptées deux fois. La continuité des emplois/services et le pouvoir d'achat doivent être protégés, et les deux régimes Québec dans le Canada / Québec souverain hypothétique sont distincts.

**NO_GO_AUTOMATIQUE — PR brouillon, aucune fusion dans `main`, aucune modification à SINJIRA.**

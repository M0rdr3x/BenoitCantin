# P54E — Dossier opérationnel de revue humaine indépendante, non certifiante

**24 octobre 2026.** Document de travail du Projet Nova lié exclusivement à P54D. Il ne déclare aucune pièce primaire obtenue, aucun avis d'expert signé et aucune économie.

## Faits d'entrée établis

Le workflow P54D a recapturé les deux publications financières officielles 2024 (Ville de Québec et MAMH). Sur la paire d'indices PDF Ville 102 / MAMH 162, **cinq occurrences numériques lexicales** sont non appariées. Le classement automatisé en a estimé **une liée probablement à une date ou une année** et a laissé **quatre indéterminées**.

Sources vérifiables :
- https://github.com/M0rdr3x/BenoitCantin/actions/runs/40120462237 (52 tests et classification réels)
- https://github.com/M0rdr3x/BenoitCantin/actions/runs/40120767469 (24 tests des observations)
- Artefact de résultats : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40120462237/artifacts/12570359704

Le rapport ciblé porte sur la ventilation des dépenses mixtes locales et d'agglomération, selon le R.A.V.Q. 1435. Il ne s'agit pas d'un audit de la réforme fiscale proposée par Nova.

## Quatre dossiers de revue

| Référence interne stable | Publication | Index de page PDF | Zone |
|---|---|---:|---|
| P54E-V-001 | Ville de Québec | 102 | Fin |
| P54E-M-001 | MAMH | 162 | Début |
| P54E-M-002 | MAMH | 162 | Fin |
| P54E-M-003 | MAMH | 162 | Fin |

Ces références désignent l'**ordre de l'observation dans le résultat P54D**, pas la position précise d'un caractère dans la page. Plusieurs occurrences étant dans la même zone « fin », les références ne permettent pas seules de les retrouver sur l'original; une personne autorisée doit consulter le document et le diagnostic privé. Les références ne sont pas des numéros d'anomalie financière.

La cinquième occurrence, dite « année/date probable », ne relève pas de ces quatre dossiers mais **n'est pas définitivement résolue**.

## Dix contrôles par dossier (40 positions)

1. Vérifier la même édition originale et l'empreinte de la copie.
2. Déterminer le folio, la page physique et les écarts de mise en page.
3. Examiner le contexte lexical, le libellé et la nature documentaire.
4. Vérifier la période et l'éventuelle colonne concernée.
5. Identifier la portée du rapport d'audit et du R.A.V.Q. 1435.
6. Examiner les unités, devises, milliers, signes et conventions de chiffres.
7. Distinguer tableau, annexe, signature, mention administrative et référence.
8. Appliquer les règles de confidentialité, droits d'accès et minimisation.
9. Documenter les contradictions et solliciter une contre-revue distincte.
10. Garantir absence de double élimination comptable, protection des travailleurs et continuité des services.

Les 40 positions commencent **NON ATTESTÉES**. Un analyste peut cocher qu'il *déclare avoir examiné* un point, sans que le programme puisse valider son expertise, son indépendance, sa signature ou sa preuve.

## Procédure pour un examinateur mandaté

Conserver les PDF, les valeurs exactes, les captures pertinentes, les noms et les pièces probantes exclusivement dans un dossier local autorisé **hors GitHub**, avec restrictions d'accès. Comparer le même exercice, les mêmes unités et le même périmètre; consigner toute contradiction plutôt que la masquer. Faire produire une contre-revue documentaire séparée et, pour toute assertion de comptabilité ou économies, obtenir ensuite un avis original signé et une analyse des grands livres.

Un modèle JSON de déclarations locales peut être préparé selon la structure suivante, avec vocabulaire fermé et sans texte libre, personnes, montants ou chemins de preuve dans le dépôt :

    {
      "schema_version": "P54E-DECLARATIONS-1",
      "source_run_p54d": 40120462237,
      "sha256_copies": {
        "ville": "<empreinte de référence P53Z>",
        "mamh": "<empreinte de référence P53Z>"
      },
      "declarations": [
        {
          "dossier_id": "P54E-V-001",
          "hypothese": "INDETERMINE",
          "statut": "EN_EXAMEN",
          "controles_declares": [],
          "pieces_hors_git_declarees": 0,
          "contradiction": "NON_EVALUE",
          "role_examen": "EXAMINATEUR_DECLARE",
          "role_relecture": "RELECTEUR_DISTINCT_DECLARE",
          "avis_independant_signe_valide": false,
          "decision_certifiante_autorisee": false
        }
      ]
    }

**Les deux empreintes doivent être celles consignées dans la configuration des captures P53Z/P54D;** les champs ci-dessus entourés de chevrons sont des emplacements descriptifs et non un fichier prêt à valider. Le lecteur ne transmet pas les fiches locales à GitHub.

## Commandes

Créer les dossiers et le bilan initial, sans réseau :

    python scripts/preparer_revue_humaine_nova_p54e.py --dossiers p54e_dossiers.json --rapport p54e_bilan.json

Contrôler une déclaration locale hors Git (exemple de chemin non réel) :

    python scripts/preparer_revue_humaine_nova_p54e.py --revue-locale /repertoire_prive/fiche.json --rapport p54e_declarations_agregees.json

Tester le refus d'un avis indépendant inventé :

    python scripts/preparer_revue_humaine_nova_p54e.py --exiger-avis-signe

Codes : 0 = structures et déclarations conformes; 2 = refus de schéma, rôle, source ou confidentialité; 3 = refus attendu de certification. Même si dix contrôles sont déclarés pour un cas, le rapport continue de présenter **zéro point attesté** et **zéro dossier clôturé**.

## Protections institutionnelles

Les **96 vérifications de comparabilité P54B** et les **8 contrôles contextuels P54C** restent non instruits. Les opérations Ville–RTC déjà consolidées et éliminées ne constituent pas des économies additionnelles. Les emplois, les conditions de travail, les services essentiels et les droits des citoyens demeurent protégés. Le Québec dans le Canada et le Québec souverain hypothétique restent des systèmes d'analyse distincts.

**NO_GO_AUTOMATIQUE** : aucune certification de poste financier, aucun montant d'économie, aucune fusion dans main et aucune modification de SINJIRA.

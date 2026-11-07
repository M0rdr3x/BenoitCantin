# P55F — Notes comptables et verrou d'interprétation des sources financières 2024

**3 novembre 2026 — constat contextuel fondé sur des ressources publiques, non certifiant.**

Ce jalon ajoute un **fait nouveau utile** au dossier : la note 3 du tableau de ventilation des dépenses mixtes de la Ville de Québec 2024 précise un **redressement de 1 825 176 $ du comparatif de l'exercice précédent**. Les dépenses de l'exercice comparatif ont été diminuées après la correction d'une erreur d'identification de dépenses mixtes. Ce montant **n'est pas** une nouvelle économie récurrente, ni une économie du Projet Nova, ni une preuve d'anomalie de 2024.

Sources consultables :
- [Rapport financier 2024 — Ville de Québec](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf), chapitre « Ventilation des dépenses mixtes », notes complémentaires, page imprimée 106 (le document PDF peut utiliser une pagination différente).
- [Rapport financier 2024 et autres — organisme 23027, MAMH](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf), tableau de ventilation des dépenses mixtes 2024, formulaire S50, avec une colonne « Éliminations ».
- [Données Québec — Rapport financier des organismes municipaux et documents connexes](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents), notice rappelant que les organismes peuvent retransmettre des documents après modification et que les utilisateurs doivent tenir compte des mises à jour.

**Précision probatoire :** les résultats ci-dessus proviennent de l'accès au texte et aux notices publiques, **pas d'une nouvelle capture octet à octet du PDF dans le dépôt**. Une lecture de contenu en ligne n'est ni une preuve d'empreinte SHA-256 courante, ni une authentification de signature, ni une expertise comptable. La récupération directe en conteneur a échoué par défaut de DNS. L'outil ne déclare donc aucune version actuelle authentifiée.

## Ce que P55F change dans l'analyse

| Question de qualification | Traitement admissible |
|---|---|
| Que signifie « dépenses mixtes » ? | Le rapport renvoie au périmètre agglomération/compétences locales et au R.A.V.Q. 1435. Il faut vérifier la portée juridique et le critère de ventilation. |
| À quoi correspond 1 825 176 $ ? | Correction du **comparatif antérieur** documentée dans les notes, **pas une économie 2024**. |
| La colonne « Éliminations » permet-elle de compter de nouveaux gains ? | Non. Les éliminations existantes ne deviennent pas un gain budgétaire nouveau simplement parce qu'on regroupe deux entités. |
| Un même nombre dans deux rapports est-il deux économies ? | Non. Il faut rapprocher les périmètres, les écritures, le statut consolidé/non consolidé et les flux réciproques. |
| Une URL retrouvée prouve-t-elle la version PDF ? | Non. Les sources peuvent être retransmises ou modifiées; la taille, le SHA et la page doivent être vérifiés sur la copie utilisée. |
| Une comparaison budget/réalisations prouve-t-elle des économies possibles ? | Non. Les transferts, reclassements, variations d'exercice ou redressements ne sont pas des gains nets, récurrents et disponibles. |

## Intégration technique

Le script `scripts/verifier_interpretation_sources_nova_p55f.py` reprend la configuration P55E et la reproduction locale des deux PDF (P54Q/P55C) **seulement si l'opérateur fournit leurs chemins**. Il expose des drapeaux de prudence fixes et une décision `NO_GO_AUTOMATIQUE`.

Exécution neutre, sans PDF :

```bash
python scripts/verifier_interpretation_sources_nova_p55f.py \
  --bilan-public p55f_bilan_neutre.json \
  --plan-public p55f_plan_neutre.json
```

Examen local (aucun appel réseau) avec les deux copies officielles **hors dépôt**, en lecture seule, avec droits `0600` et sans liens symboliques :

```bash
python scripts/verifier_interpretation_sources_nova_p55f.py \
  --ville-pdf /hors_git/ville2024.pdf \
  --mamh-pdf /hors_git/mamh2024.pdf \
  --bilan-public /hors_git/p55f_bilan.json
```

Même après reproduction technique, les quatre observations P54E et la date probable demeurent ouvertes jusqu'à qualification contradictoire. Les 40 tâches P54N, dix blocages P54O, 96 contrôles P54B et huit P54C restent non attestés. Un CPA indépendant doit traiter les unités, redressements, comptes réciproques et conditions de répétition; un juriste compétent doit traiter la portée R.A.V.Q. 1435 et les conséquences institutionnelles, selon des mandats réels qui ne sont pas signés.

Les scénarios **Québec au Canada** et **Québec souverain hypothétique** sont deux régimes distincts. Ne pas réduire les effectifs ou le niveau de services au nom d'une économie non démontrée. Protéger le pouvoir d'achat, interdire le double compte Ville–RTC–SOMHAC, ne pas contacter d'organismes ni modifier SINJIRA et ne rien fusionner dans `main`.

**P55F refuse les inférences automatiques : redressement comparatif ≠ économie; élimination ≠ gain nouveau; chiffre similaire ≠ double recette; source textuelle ≠ original authentifié.**

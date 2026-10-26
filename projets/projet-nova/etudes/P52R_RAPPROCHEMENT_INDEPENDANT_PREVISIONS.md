# Projet Nova — P52R : rapprochement primaire et réception vérifiable des documents budgétaires

**20 octobre 2026 · Version de travail non adoptée · NO_GO.**

## Ce qui est vérifié aujourd'hui

Les deux PDF du ministère des Finances du Québec sont consultables dans le navigateur : le *Discours sur le budget 2026-2027*, Tableau 3, page imprimée **27**, index PDF **29**; et le *Plan budgétaire 2026-2027*, Tableau F.2, page **F.9**, index PDF **277**. Le lecteur en ligne affiche respectivement **34** et **426** pages. Les **montants transcrits ont été revus directement sur les pages rendues** et inscrits dans P52R comme *constats de lecture des images*. Cela ne prouve **ni l'origine cryptographique de leurs octets, ni une relecture humaine indépendante**.

La récupération des octets PDF par l'environnement d'exécution a échoué (accès réseau/DNS indisponible). **Il serait faux d'annoncer un hash SHA-256 des PDF originaux, une archive obtenue ou une attestation.** Le registre P52K reste inchangé : deux originaux manquants, empreintes nulles et statut `NON_EFFECTUEE`.

### Rapprochement arithmétique des tableaux de mars 2026 (millions CAD)

| Ligne | Montant | Calcul de contrôle |
| --- | ---: | --- |
| Impôts revenus et biens | 76 050 | 50 800 + 9 412 + 14 527 + 1 311 |
| Taxes à la consommation (agrégat) | 30 008 | 26 349 + 2 097 + 830 + 574 + 158 |
| Revenus des entreprises du gouvernement | 5 853 | 2 445 + 1 557 + 1 406 + 292 + 146 + 7 |
| Droits et redevances | 6 542 | Ligne publiée |
| Revenus divers | 15 908 | Ligne publiée |
| **Revenus autonomes** | **134 361** | 76 050 + 30 008 + 5 853 + 6 542 + 15 908 |
| **Transferts fédéraux** | **32 131** | 13 907 + 9 265 + 1 392 + 7 567 |
| **Total recettes** | **166 492** | 134 361 + 32 131 |
| Dépenses de portefeuilles et dette | −170 757 | −160 489 − 10 268 |
| Solde avant provision | −4 265 | 166 492 − 170 757 |
| Solde comptable après provision | −6 265 | −4 265 − 2 000 |
| **Solde budgétaire au sens de la loi** | **−8 612** | −6 265 − 2 347 |

**Attention :** la ligne « taxes de vente » totalisant 26 349 M$ n'est pas la TVQ seule. Le service de la dette fait déjà partie du total des dépenses. La provision de 2 000 M$ et le versement au Fonds des générations de 2 347 M$ doivent être rapprochés au bon stade et non retranchés à nouveau des dépenses.

Ces chiffres sont **des prévisions budgétaires publiées en mars 2026, pas des résultats**, et ne démontrent pas le financement de la proposition à deux prélèvements. Les **32 131 M$ de transferts fédéraux** ne sauraient être reportés automatiquement dans un scénario de Québec souverain hypothétique. Aucun des 1 320 montants P52B et P52D n'est complété. F09 et l'ensemble des vingt exigences F01–F20 restent NON VALIDÉS.

## Fichiers et exécution

- `P52R_RECONCILIATION_ET_RECEPTION_ORIGINAUX.json` : figures des deux tableaux observés, limites documentaires et garde de non-adoption.
- `scripts/auditer_rapprochement_budget_nova_p52r.py` : contrôle **autonome** des 21 lignes individuelles, 8 sous-totaux, 10 postes signés, passages arithmétiques et concordance avec P52C/P52J/P52K. Refuse la falsification d'une valeur ou l'annonce fictive d'une réception.
- `scripts/tests/test_auditer_rapprochement_budget_nova_p52r.py` : tests adversariaux de falsification, sommes, signatures et modes locaux.
- `.github/workflows/validate-nova-p52r.yml` : lecture seule; aucune récupération de PDF sur Internet, aucun upload d'original ni d'empreinte d'une personne.

```bash
# Le registre actuel (sans PDF original) : sortie structurée NO_GO, code 0
python scripts/auditer_rapprochement_budget_nova_p52r.py --rapport /tmp/p52r_agrege.json
# Le mode strict refuse une attestation fictive : code 3
python scripts/auditer_rapprochement_budget_nova_p52r.py --exiger-expertise

# Seulement hors du dépôt, après téléchargement manuel licite des deux documents :
python scripts/auditer_rapprochement_budget_nova_p52r.py \
  --discours-fichier "/chemin/privé/Budget2627_Discours.pdf" \
  --plan-fichier "/chemin/privé/Budget2627_PlanBudgetaire.pdf" \
  --rapport "/chemin/privé/constat_octets_non_atteste.json"
```

Le lecteur local ouvre les octets en lecture seule, vérifie seulement un en-tête PDF et un marqueur de fin plausibles, calcule les deux SHA-256 et les tailles. Un PDF peut satisfaire ces vérifications sommaires tout en étant malformé, falsifié ou provenant d'un tiers. **Même si des empreintes sont calculées, le rapport conclut NO_GO** : il ne vérifie pas la signature du ministère, les certificats de transport, les identités, les pages PDF ni les avis d'experts.

Seul le rapport privé peut exposer les deux empreintes si les fichiers réels ont été remis. GitHub Actions n'utilise **aucun PDF**, et n'affiche que des agrégats, ni URL individuelles ni sommes détaillées. Le mode `--exiger-originaux` renvoie **3** tant que les originaux ne sont pas accessibles et plausibles; le mode `--exiger-expertise` renvoie toujours **3** faute d'attestation humaine. Code **2** en cas d'erreur; un rapport existant n'est jamais écrasé.

## Étapes humaines indispensables

1. Télécharger manuellement les documents depuis les deux URL officielles, conserver une copie licite hors GitHub, enregistrer les heures, la méthode, la chaîne de transport, les droits et les personnes autorisées.
2. Vérifier les pages, les versions et toutes les indications d'authenticité applicables avec un outil PDF fiable; exécuter ensuite P52R sur les octets sauvegardés.
3. Réaliser une seconde extraction indépendante, revoir les éventuelles versions révisées et obtenir les comptes réalisés au moment de leur publication.
4. Rapprocher le périmètre provincial avec les transferts fédéraux et les administrations locales, selon les deux hypothèses constitutionnelles.
5. Mandater un expert comptable indépendant avec justification, vérification d'indépendance, signatures, réserves et recours; l'examen final relève d'une autorité compétente.

Maintenir la PR #673 en brouillon. Protéger `main` (#135) et obtenir de vraies revues (#662) avant toute fusion. Aucun impact sur SINJIRA.

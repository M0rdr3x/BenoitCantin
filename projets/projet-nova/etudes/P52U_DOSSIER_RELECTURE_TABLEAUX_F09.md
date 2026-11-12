# Projet Nova — P52U : relecture du contenu des PDF et remise du dossier F09

**20 octobre 2026 — état non adopté, NO_GO_AUTOMATIQUE.**

## Progrès attendu

P52S et P52T ont déjà démontré la stabilité binaire des deux fichiers budgétaires reçus par HTTPS. P52J et P52R ont vérifié les montants figurant sur les pages publiques rendues du **tableau 3** (discours, PDF page index 29, imprimée p. 27) et du **tableau F.2** (plan, PDF page index 277, imprimée p. F.9).

P52U ajoute un contrôle distinct : après comparaison exacte des SHA-256 et tailles reçues en P52S, ouvrir les fichiers PDF en mémoire, vérifier les **34 et 426 pages** respectivement, puis extraire sur les pages ciblées **21 lignes détaillées de revenus, 8 sous-totaux et 10 montants signés**, soit 39 valeurs à rechercher. Les PDF ne sont pas déposés dans GitHub; le rapport ne contient que compteurs et identifiants d'anomalies.

**Limite déterminante :** retrouver un chiffre dans le texte extrait d'une page ne signifie pas qu'il est rattaché à la bonne ligne de tableau. L'extraction automatique n'est pas une analyse comptable, une validation des dépenses du Projet Nova, ni une expertise humaine. En cas d'absence d'une valeur, d'un problème d'extraction, de pages manquantes ou de dérive SHA-256, le workflow doit échouer.

## Références et statut actuel

- Discours budgétaire : https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_Discours.pdf
- Plan budgétaire : https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/documents/Budget2627_PlanBudgetaire.pdf

Ces publications concernent **les prévisions du gouvernement du Québec pour 2026-2027**, non des résultats et non un budget adopté par le Projet Nova. Il ne faut pas reporter automatiquement les **32 131 M$ de transferts fédéraux** dans le scénario souverain hypothétique. Les **1 320 montants** de P52B et P52D restent inconnus.

## Dossier prêt pour une mission d'expertise (non attribuée)

Le réviseur devra recevoir une copie licite complète archivée indépendamment, les reçus P52S/P52T, les tableaux P52J/P52R, les différences de versions et les méthodes. Il devra : refaire les montants ligne à ligne, examiner le périmètre du gouvernement et des municipalités, prévenir le double comptage, distinguer prévision et réalisation, et vérifier les hypothèses légales et financières des deux régimes. Son mandat et ses conflits d'intérêts doivent être contrôlés; son avis daté et signé, les réserves, contre-expertises et voies de contestation doivent être consignés sous contrôle d'accès hors du dépôt.

**Aucun expert n'est nommé ni mandaté, aucune signature n'est simulée.** La preuve F09 et les 19 autres demeurent NON VALIDÉES. `main` (#135) doit être protégée et une revue nommée (#662) est requise avant fusion.

## Commandes reproductibles

```bash
python scripts/valider_pages_budget_nova_p52u.py --rapport /tmp/p52u_controle_structurel.json
python scripts/valider_pages_budget_nova_p52u.py --reseau --rapport /tmp/p52u_pages_pdf.json
python scripts/valider_pages_budget_nova_p52u.py --exiger-expertise
```

En mode réseau, seule la lecture mémoire de documents publics est autorisée; pas d'archivage des PDF, de texte intégral ou de données nominatives. Le code **0** signifie seulement contrôle mécanique cohérent, le code **2** une anomalie et le code **3** l'absence de preuve humaine requise. **Aucun mode ne fournit un GO institutionnel.**

Les prochaines preuves réellement utiles requièrent des professionnels autorisés, des données effectives et des avis humains contradictoires. Ne pas modifier SINJIRA, ne pas fusionner la PR #673, ne pas annoncer les deux prélèvements comme établis.

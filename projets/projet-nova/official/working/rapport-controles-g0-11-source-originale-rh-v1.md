# NOVA-SINJ-G0-SAN-019 — Rapport d'exécution et de contrôle G0.11

**Date :** 5 novembre 2026  
**Portée :** certificat technique interne de copie reçue et de rapprochement des cellules, **non certification gouvernementale ou clinique**.

## Preuve d'acquisition dans l'environnement externe

| Élément | Valeur constatée |
| --- | --- |
| Source | Fichier XLSX gouvernemental MSSS, portrait RH 2024–2025 |
| Octets téléchargés | **139 566** |
| SHA‑256 de la copie | `8d65573b2f0bf0a935a58c75ba1b4b76050a08b902760f7a03b3cae0cdb86219` |
| Fichiers ZIP | **61**, CRC intégral confirmé |
| Feuilles de classeur | **7** |
| Feuille de données examinée | « Feuille A - 2 », `xl/worksheets/sheet4.xml` |
| Lignes avec source et cellule vérifiées | **19** : organisation 00, RSS 01–18 |
| Données de personnes au 31 mars 2025 | **344 056** — total exact de 343 252 RSS + 804 Santé Québec |
| ETC rémunérés 2024–2025 | **283 740** entiers affichés au total, depuis `B70` |
| Écart apparent sur les entiers par ligne | **2 ETC — expliqué par arrondi des valeurs originales** |

**Calcul contrôlé :** la somme des cellules brutes `B51:B69` est environ `283739,959`, et la cellule totale `B70` est également `283739,959`, avec une différence numérique inférieure à `10⁻⁸`. En arrondissant chaque ligne séparément puis en additionnant, on obtient `283738`. Le total non arrondi, arrondi une seule fois, donne `283740`.

Ce résultat règle l'incertitude **arithmétique** laissée ouverte par G0.10. Il ne transforme pas les ETC rémunérés en ETP de soins disponibles.

## Tests exécutés — preuve, non intention

- **57/57 tests Node réussis**, sur l'ensemble des suites G0.7, G0.8, G0.9, G0.10 et G0.11.
- **0 échec, 0 test ignoré** lors de l'exécution complète du 5 novembre 2026 dans un environnement externe sous **Node.js v26.12.1**.
- Script `scripts/g11-verifier-original-rh-officiel.mjs` exécuté sur les **139 566 octets reçus**, **code de sortie 0**.
- Le script a produit le statut exact **`ORIGINAL_CELLS_MATCH_REVIEW_PENDING`**, confirmant l'empreinte et les 19 lignes, sans passer G0.
- Un premier essai sur le véritable fichier avait signalé des labels manquants : le lecteur XML assimilait certaines cellules vides autofermées à une cellule non vide. Le correctif et son **test de régression** ont été enregistrés dans GitHub, puis les tests et la validation source ont été relancés avec succès.

**L'exécution a eu lieu dans un environnement distant de vérification, pas dans les GitHub Actions.** Les fichiers du dépôt sont désormais configurés pour refaire ces tests et cette validation après une acquisition volontaire, mais **aucun journal d'exécution GitHub Actions n'est confirmé**.

## Limites non levées

1. La copie du XLSX original a été récupérée en mémoire externe, **pas archivée dans le dépôt GitHub**. La SHA‑256 décrit cette copie; elle n'est pas une signature officielle du producteur.
2. La validation sémantique s'est concentrée sur les **19 lignes et trois mesures** de la feuille A - 2; il ne s'agit pas d'un audit exhaustif des sept feuilles.
3. Le contrôleur vérifie la correspondance des valeurs originales et les sommes; il ne détermine pas si l'effectif est suffisant pour offrir les soins requis.
4. Aucun dossier patient, salaire nominatif, ETC clinique de première ligne, coût complet par épisode ou rendement comparé public–privé n'est calculé ou validé.
5. La méthodologie doit encore être revue indépendamment par les institutions et spécialistes concernés avant un usage décisionnel.

## Localisation dans GitHub

- `data/preuve-binaire-rh-msss-g0-11-2024-2025.json` — empreinte, coordonnées, 19 lignes et valeurs sous-jacentes.
- `data/rapport-execution-distante-g0-11-rh-2026-11-05.json` — résumé d'exécution réelle.
- `assets/g11-rh-evidence-core.mjs` — validateur et lecteur OOXML.
- `scripts/g11-verifier-original-rh-officiel.mjs` — vérification directe de la copie locale acquise.
- `tests/g11-rh-original-cells.test.mjs` — 15 tests Node.
- `.github/workflows/nova-g07-acquisition-rh.yml` — acquisition **manuelle** et nouvelle étape G0.11.

**Décision : G0 NON FRANCHIE; aucune réforme, économie ou modification des emplois autorisée.**

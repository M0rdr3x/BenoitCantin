# Flux de développement SINJIRA™

## Objectif

Éviter les alertes GitHub rouges pendant qu’un ensemble de changements est encore incomplet, sans diminuer la qualité des validations avant fusion.

## Méthode

1. Créer une branche de travail depuis le `main` courant.
2. Ouvrir la pull request en **Draft / Brouillon**.
3. Effectuer les modifications liées sur cette branche.
4. Tant que la PR reste brouillon, les validations coûteuses de PR sont ignorées plutôt que lancées sur un état intermédiaire.
5. Lorsque la passe est cohérente, passer la PR à **Ready for review**.
6. GitHub exécute alors les validations générales, les tests Chromium/Firefox/WebKit/Lighthouse et, lorsqu’ils sont concernés, la reconstruction/ledger Supabase.
7. Fusionner seulement après les contrôles requis réussis.
8. Le push final sur `main` relance les validations de production habituelles.

## Garanties

- Les PR brouillon ne sont pas considérées comme validées : elles sont simplement en cours de préparation.
- `ready_for_review` déclenche explicitement les contrôles.
- Chaque nouveau commit sur une PR prête relance les contrôles via l’événement `synchronize`.
- Les contrôles sur `main`, les tâches planifiées et les lancements manuels restent actifs.
- Un ancien run rouge reste historique et ne décrit pas l’état du `main` actuel.

Le contrat est surveillé par `scripts/validate_ci_draft_gate.py` afin d’éviter qu’un changement futur réintroduise les alertes intermédiaires.

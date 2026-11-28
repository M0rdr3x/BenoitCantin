# Réconciliation de l'historique Supabase production

Contrôle en lecture seule, distinct de toute autorisation de déploiement.

1. Exporter uniquement les métadonnées version/nom depuis l'inventaire authentifié des migrations du projet, dans un fichier JSON local hors du dépôt. Le format est un tableau d'objets avec les champs string `version` et `name`. Ne pas inclure les instructions SQL ni les secrets.
2. Depuis un checkout du commit à examiner, exécuter `python scripts/audit_production_migration_history.py --remote-json /chemin/local/inventaire.json`.
3. Code retour 0 : métadonnées alignées sur le ledger, sans migration supplémentaire distante. Code 1 : divergence; bloquer la synchronisation générale. Code 2 : entrée invalide; aucune décision favorable.
4. Une correspondance de nom/version ne prouve pas l'équivalence du SQL ni l'état du schéma. Vérifier les définitions, les ACL, les effets réels et l'historique distant avant de proposer une réconciliation append-only contrôlée. Une migration de même nom mais de version différente ne doit pas être rejouée automatiquement.
5. Toute application exige encore le processus de revue et d'autorisation de production. Ne pas utiliser migration repair, include-all ou reset pour contourner le blocage. Ce contrôle ne modifie ni les manifestes, ni la base, ni le workflow de déploiement.

Le mode `--self-test` utilise uniquement des inventaires synthétiques. Il est exécuté par la CI de validation du ledger.

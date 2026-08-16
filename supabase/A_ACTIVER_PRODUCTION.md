# SINJIRA™ — activer la synchronisation Supabase production

Le dépôt contient maintenant un workflow manuel :

`.github/workflows/supabase-production-preflight.yml`

Projet de production verrouillé dans le workflow : `gpvivleexywljowcqkru`.

## Secrets GitHub Actions requis

Dans le dépôt GitHub : **Settings → Secrets and variables → Actions → New repository secret**.

Créer exactement :

- `SUPABASE_ACCESS_TOKEN` : Personal Access Token Supabase du propriétaire.
- `SUPABASE_DB_PASSWORD` : mot de passe PostgreSQL du projet Supabase de production.

Ne jamais mettre ces valeurs dans un fichier du dépôt, dans le JavaScript du navigateur ou dans une migration SQL.

## Premier passage recommandé

Dans **Actions → Synchroniser Supabase production → Run workflow** :

1. laisser `apply = false` ;
2. lancer le workflow ;
3. vérifier `migration list` et le résultat `db push --dry-run` ;
4. si l'historique distant est cohérent, relancer avec `apply = true`.

Avec `apply = true`, le workflow :

1. lie le projet de production ;
2. relit l'historique des migrations ;
3. exécute un dry-run ;
4. applique les migrations manquantes avec `supabase db push` ;
5. déploie les Edge Functions du dépôt ;
6. relit l'historique après déploiement.

## Après le déploiement

Ouvrir le site SINJIRA™, puis **Administration → État du système**. Le marqueur serveur attendu est `24.3.6`. Ensuite tester :

- AbyssTime / propriétaire ;
- coffre privé ;
- personnage et fiche sociale ;
- Fracture du Réseau-Mère : créer une partie puis la rejoindre ;
- licences ;
- questionnaire ;
- rapports de fin de partie.

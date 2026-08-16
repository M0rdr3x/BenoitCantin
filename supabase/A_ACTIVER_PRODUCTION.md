# SINJIRA™ — activer la synchronisation Supabase production

Le dépôt contient un workflow manuel sécurisé :

`.github/workflows/supabase-production-preflight.yml`

Projet de production verrouillé dans le workflow : `gpvivleexywljowcqkru`.

## 1. Secrets GitHub Actions requis

Dans le dépôt GitHub : **Settings → Secrets and variables → Actions → New repository secret**.

Créer exactement :

- `SUPABASE_ACCESS_TOKEN` : Personal Access Token Supabase du propriétaire.
- `SUPABASE_DB_PASSWORD` : mot de passe PostgreSQL du projet Supabase de production.

Ne jamais mettre ces valeurs dans un fichier du dépôt, dans le JavaScript du navigateur, dans une migration SQL ou dans une conversation.

## 2. Secret Supabase requis pour les licences

Les Edge Functions de codes d’activation utilisent aussi :

- `SINJIRA_LICENSE_PEPPER`

Ce secret doit être défini dans les secrets Edge Functions de Supabase. Il doit être long, aléatoire et stable. Le changer après émission de codes rendrait les anciens codes impossibles à vérifier.

## 3. Premier passage : prévisualisation uniquement

Dans **Actions → Synchroniser Supabase production → Run workflow** :

1. laisser `apply = false`;
2. lancer le workflow;
3. vérifier `migration list`;
4. vérifier le résultat de `supabase db push --dry-run`;
5. ne rien appliquer si l’historique distant ne correspond pas aux migrations attendues.

## 4. Synchronisation réelle

Si le dry-run est cohérent, relancer le même workflow avec `apply = true`.

Le workflow :

1. lie le projet de production;
2. relit l’historique des migrations;
3. exécute un dry-run;
4. applique les migrations manquantes avec `supabase db push`;
5. déploie les Edge Functions du dépôt;
6. relit l’historique après déploiement.

Les migrations Fracture Web les plus récentes doivent se terminer par :

1. `20260816_fracture_web_engine_v24_4.sql`
2. `20260816_fracture_web_engine_v24_4_1_hotfix.sql`
3. `20260816_fracture_web_engine_v24_4_2_privacy.sql`

Le marqueur serveur attendu après synchronisation est **`24.4.2`**.

## 5. Validation après déploiement

Ouvrir **Administration → État du système**. Les composants essentiels doivent être `NORMAL`. Les lignes `PROTÉGÉ` peuvent être normales lorsqu’une table est volontairement inaccessible directement au navigateur.

Tester dans cet ordre :

- AbyssTime / propriétaire;
- coffre privé;
- personnage et fiche sociale;
- licences et codes d’activation;
- questionnaire;
- **Fracture Solo** : créer une partie à 1 humain, démarrer, vérifier les deux sièges moteur et terminer une ronde;
- **Fracture Duo** : deux comptes humains, vérifier que le siège 3 est joué par le moteur;
- **Fracture multijoueur** : créer/join avec un code `FRM-XXXXXX`;
- reprise de session après actualisation/fermeture du navigateur;
- accusation finale et résultat automatique;
- rapports de fin de partie.

## Blocage actuel connu

Le dernier prévol GitHub a confirmé que `SUPABASE_ACCESS_TOKEN` et `SUPABASE_DB_PASSWORD` ne sont pas encore présents dans les GitHub Actions secrets. Tant qu’ils sont absents, le workflow s’arrête volontairement **avant toute modification de Supabase production**.

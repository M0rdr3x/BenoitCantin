# SINJIRA™ — synchronisation Supabase production

Le dépôt utilise un workflow manuel sécurisé :

`.github/workflows/supabase-production-preflight.yml`

Projet de production verrouillé : `gpvivleexywljowcqkru`.

## 1. Secrets GitHub Actions indispensables

Dans le dépôt GitHub : **Settings → Secrets and variables → Actions → New repository secret**.

Créer exactement :

- `SUPABASE_ACCESS_TOKEN` : Personal Access Token Supabase du propriétaire.
- `SUPABASE_DB_PASSWORD` : mot de passe PostgreSQL du projet Supabase de production.

Ne jamais mettre ces valeurs dans un fichier du dépôt, dans le JavaScript du navigateur, dans une migration SQL ou dans une conversation.

Le connecteur GitHub utilisé par l'assistant ne peut ni lire ni créer ces deux secrets à votre place.

## 2. Secrets Edge Functions

Le workflow V24.4.5 garantit automatiquement la présence d'un `SINJIRA_LICENSE_PEPPER` stable. S'il est absent, une valeur cryptographiquement aléatoire est créée directement dans les secrets Supabase et sa valeur n'est jamais affichée. S'il existe déjà, elle est conservée afin de ne jamais invalider les anciens codes d'activation.

Le workflow configure aussi :

- `REPORT_FROM_EMAIL=SINJIRA <no-reply@benoitcantin.com>`
- `CHARACTER_REPORT_TO_EMAIL=kingtyrano@gmail.com`
- `FRACTURE_REPORT_TO_EMAIL=kingtyrano@gmail.com`

Secrets externes facultatifs :

- `RESEND_API_KEY` : active l'envoi de rapports/courriels. Sans cette clé, les téléchargements restent disponibles mais l'envoi de courriel est désactivé.
- `OPENAI_API_KEY` : facultatif. SINJIRA™ doit continuer de fonctionner avec l'IA externe désactivée.
- variable GitHub facultative `OPENAI_CHARACTER_MODEL` : modèle à utiliser uniquement si l'IA de personnage est volontairement activée.

## 3. Migrations : format corrigé V24.4.5

Les migrations ont maintenant des timestamps Supabase **uniques sur 14 chiffres** (`YYYYMMDDHHMMSS`). Cette correction est nécessaire parce que Supabase identifie une migration par son timestamp.

Les trois migrations Fracture les plus récentes sont :

1. `20260816090000_fracture_web_engine_v24_4.sql`
2. `20260816100000_fracture_web_engine_v24_4_1_hotfix.sql`
3. `20260816110000_fracture_web_engine_v24_4_2_privacy.sql`

Le contenu SQL n'a pas été modifié lors du renommage; seul l'identifiant chronologique du fichier a été corrigé pour éviter les collisions de migration.

## 4. Premier passage : prévisualisation uniquement

Dans **Actions → Synchroniser Supabase production → Run workflow** :

1. laisser `apply = false`;
2. lancer le workflow;
3. le workflow valide d'abord la structure Supabase du dépôt;
4. il lie le projet de production;
5. il affiche `migration list`;
6. il exécute `supabase db push --dry-run`;
7. il ne modifie ni la base, ni les secrets, ni les Edge Functions.

Si l'historique distant diffère de l'historique local, **ne pas lancer `apply = true`**. Il faut d'abord réconcilier l'historique distant avec les migrations réellement déjà présentes en production. Le workflow ne fait jamais de `migration repair` automatique, afin d'éviter de marquer par erreur une migration comme appliquée.

## 5. Synchronisation réelle

Lorsque le dry-run est cohérent, relancer le workflow avec `apply = true`.

Le workflow :

1. applique les migrations manquantes;
2. crée ou conserve le secret de licence stable;
3. configure les paramètres serveur de courriel;
4. synchronise les secrets externes optionnels présents dans GitHub;
5. déploie **toutes** les Edge Functions du dépôt via l'API Supabase;
6. vérifie qu'aucune Edge Function du dépôt ne manque côté production;
7. relit l'historique des migrations;
8. refait un `db push --dry-run` final pour confirmer qu'aucune migration n'est encore en attente.

Le marqueur serveur attendu après synchronisation est **`24.4.2`**.

## 6. Compatibilité des clés serveur

Le code partagé des Edge Functions accepte maintenant en priorité les clés Supabase modernes via `SUPABASE_SECRET_KEYS`, avec repli sur la clé legacy `SUPABASE_SERVICE_ROLE_KEY`. Aucun secret serveur n'est exposé au navigateur.

## 7. Validation après déploiement

Ouvrir **Administration → État du système**. Les composants essentiels doivent être `NORMAL`. Les tables internes du moteur Fracture peuvent rester inaccessibles directement au navigateur : leur état est vérifié par `fracture_engine_health()`.

Tester dans cet ordre :

- connexion / inscription / récupération de mot de passe;
- AbyssTime / propriétaire;
- profil privé, avatar et relations;
- personnage, questionnaire et Registre;
- bibliothèque et droits d'accès;
- licences et codes d'activation;
- **Fracture Solo** : 1 humain + 2 sièges moteur;
- **Fracture Duo** : 2 humains + siège 3 moteur;
- **Fracture multijoueur** : création et entrée par code;
- reprise de session après actualisation;
- accusation finale et résultat automatique;
- téléchargement du rapport de partie;
- envoi du rapport par courriel seulement si `RESEND_API_KEY` est configuré;
- Communauté, Monde parallèle, Marché et autres modules exposés par le compte.

## Blocage qui ne peut pas être automatisé depuis le dépôt

Les deux seules informations de connexion que le dépôt ne peut pas fabriquer sont :

- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_DB_PASSWORD`

Elles doivent être ajoutées une fois dans GitHub Actions par le propriétaire. Après cela, le workflow V24.4.5 peut effectuer le prévol puis la synchronisation complète sans révéler ces valeurs.

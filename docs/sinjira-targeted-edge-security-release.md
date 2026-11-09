# SINJIRA — Promotion contrôlée de deux Edge Functions JWT

> Document opératoire de sécurité. Aucune étape de ce document ne constitue une autorisation implicite de publier en production. Voir l'issue #702 et la PR #914.

## Constat vérifié en lecture seule (8 novembre 2026)

Projet : `gpvivleexywljowcqkru`. Les fonctions `revoke-my-contributions` et `redeem-license-code` sont déployées en **version 2** avec `verify_jwt=true`. Les sources actuellement actives restent différentes des fichiers `index.ts` approuvés dans `main`.

- **Révocation :** la source active utilise `await req.text()` avant de limiter la taille et journalise des erreurs brutes. La version de `main` utilise `readLimitedUtf8Body`, un plafond de 2 048 octets et des logs à codes fixes.
- **Activation :** la source active utilise `await req.json()` sans limite préalable équivalente et journalise des erreurs brutes. La version de `main` impose le lecteur borné, 4 096 octets et des codes de 12 à 80 caractères.

Il s'agit d'écarts prouvés entre la production et le dépôt, pas d'une preuve de compromission. Les quatre fonctions publiques `verify_jwt=false` ne sont **pas** concernées par cette promotion.

## Préconditions bloquantes

1. PR #914 revue puis fusionnée vers `main` après CI entièrement verte. Le déclenchement de la PR ne déploie rien.
2. Tester les deux parcours sur un environnement de préproduction **isolé**, avec uniquement des utilisateurs, données, sessions et licences fictifs. Vérifier les erreurs 401/400/413, les accès intercomptes, la portée de révocation, l'idempotence de la licence et les journaux sans données sensibles.
3. Vérifier que GitHub `environment: production` dispose réellement des règles d'approbation attendues. Le simple champ YAML n'assure pas qu'un réviseur est configuré.
4. Mettre à disposition le secret d'environnement GitHub `SUPABASE_EDGE_DEPLOY_TOKEN` avec les permissions les plus restreintes permettant la lecture des métadonnées et le déploiement **ciblé** de fonctions. Aucun secret ne doit être ajouté au code ni aux journaux. Si ce modèle de permission n'est pas disponible, suspendre le déploiement jusqu'à une décision d'accès explicite.
5. Conserver une **copie récupérable et contrôlée** de la dernière version de fonction en production, incluant les dépendances nécessaires, et une procédure de retour arrière testée dans un environnement isolé. Ne pas supposer que l'éditeur web Supabase fournit des versions restaurables.
6. Confirmer une fenêtre d'intervention et une personne habilitée à surveiller le service immédiatement après publication. Aucun changement SQL, Auth, DNS, JWT ou service payant n'est prévu.

## Exécution — une seule fonction par intervention

Workflow : `.github/workflows/sinjira-targeted-edge-hardening-release.yml`.

1. Depuis **Actions**, sélectionner le workflow sur la branche `main`.
2. Choisir **une seule** fonction dans `function_slug` : `revoke-my-contributions` ou `redeem-license-code`.
3. Renseigner `source_commit` avec le **SHA complet de 40 caractères** du commit `main` déjà vérifié. Le workflow exige qu'il corresponde exactement au SHA du déclenchement.
4. Renseigner `confirmation` avec `DEPLOY-SINJIRA-EDGE-<nom-exact-de-la-fonction>` (sans les chevrons).
5. Vérifier que le job sans secrets passe tous les contrôles de source et de flux. Le job de production exige un lancement manuel, `refs/heads/main`, le choix autorisé et la confirmation ; GitHub doit appliquer les restrictions de l'environnement production.
6. Le prévol récupère la liste live des fonctions et refuse la publication si la cible n'est plus en version 2, si le JWT de la cible n'est plus activé ou si une cinquième fonction sans JWT est apparue.
7. Le workflow utilise **Supabase CLI v2.111.0 figée**, un projet explicite et la forme `supabase functions deploy "$FUNCTION_SLUG" --project-ref gpvivleexywljowcqkru --use-api`. Aucune option `--no-verify-jwt`, `--prune`, déploiement global ou écriture dans la base n'est autorisée.
8. Après publication, il exige une version supérieure à 2, le maintien de `verify_jwt=true`, l'absence de modification des autres métadonnées Edge et l'identité du `index.ts` déployé avec la version approuvée du dépôt.
9. Vérifier ensuite manuellement les parcours autorisés en préproduction et surveiller en production les erreurs d'authentification, de chargement et de fonction **sans lancer d'opérations de révocation ou d'activation réelles à titre de test**.

### En cas d'échec

- **Avant l'étape de déploiement :** arrêter ; aucun changement de code Supabase n'a été demandé par cette procédure.
- **Après le début du déploiement :** un job en échec **n'implique pas** que la production est inchangée. Vérifier immédiatement la version active, le statut JWT, le code et les métriques. Ne pas relancer à l'aveugle : la baseline version 2 est conçue pour empêcher un second passage involontaire.
- **Si la nouvelle version entraîne une régression :** utiliser la procédure de retour arrière approuvée et un artefact précédent récupérable, ou suspendre temporairement l'opération affectée suivant le plan d'incident. Toute restauration doit également préserver `verify_jwt=true` et être revalidée. **Il n'existe aucun rollback automatique garanti par ce workflow.**
- Déclarer un incident si des données sensibles apparaissent dans les journaux, puis appliquer la procédure de restriction d'accès et de rétention appropriée.

## Limites explicites

Les tests de CI de la PR vérifient les contrats locaux et des mutations synthétiques, **pas** la publication réelle. Les commandes de Management API et `supabase functions download` lors d'une exécution autorisée doivent encore être éprouvées en production réelle ; un échec postflight ne déclenche pas une restauration.

La branche `main` peut évoluer après la fusion : seul le SHA exact, revu et testé, doit être déclenché. La source chargée par le site peut différer du dépôt tant que chaque fonction n'a pas été promue et contrôlée.

Références fournisseurs : Supabase « Deploy to Production », « Function Configuration » et changelog « CLI v3 is local by default » (4 novembre 2026).

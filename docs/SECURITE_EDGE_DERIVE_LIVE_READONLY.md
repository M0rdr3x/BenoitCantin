# Sécurité — contrôle de dérive du code Edge réellement déployé

## Risque confirmé par lecture seule (8 novembre 2026)

Quatre fonctions Edge actives disposent de `verify_jwt=false` et
doivent donc reposer sur leurs propres contrôles d'accès :

| Fonction | Version active observée | Écart important avec GitHub `main` |
|---|---:|---|
| `get-document-url` | 2 | Lecture `req.text()` brute plutôt que lecteur HTTP en flux borné |
| `send-game-report` | 6 | Même lecture brute, correctif de délai PDF toujours non déployé |
| `life-story-delivery` | 2 | Même lecture brute |
| `nova-civic-poll` | 5 | Contrôle explicite de consentement et de questionnaire canonique absents, délai de lecture HTTP absent |

La présence de `verify_jwt=false` **n'est pas en elle-même une
vulnérabilité** pour un endpoint explicitement public : l'application
doit néanmoins prouver ses contrôles propres. **La différence avec
le dépôt ne prouve aucune exploitation ni fuite réelle.**

Ces écarts empêchent d'affirmer que les changements GitHub sont en
production, notamment les PR #836 (lectures en flux borné),
#848 (sessions privilégiées SQL) et les garde-fous NOVA de `main`.

## Nouveau garde de surveillance passif

`scripts/audit_edge_deployed_source_readonly.py` vérifie :

- Un inventaire complet des Edge Functions actives obtenu par le
  Management API de Supabase, sans données utilisateurs.
- L'ensemble **exact** des quatre fonctions exemptées de JWT natif.
  Tout autre endpoint `verify_jwt=false` est un **NO_GO**.
- L'état `ACTIVE`, les versions, les doublons et le format du JSON.
- Pour chacune de ces fonctions, le fichier `index.ts` effectivement
  téléchargé via `supabase functions download`, comparé octet pour
  octet après normalisation des fins de ligne à la source canonique.
- Les accès par liens symboliques, les sources illisibles ou trop
  volumineuses et les inventaires mal formés sont refusés.
- Aucune source, clé, donnée de session ou réponse de bulletin n'est
  affichée dans les journaux ; uniquement le nom de l'endpoint en
  dérive et un diagnostic `NO_GO`.

Le workflow
`.github/workflows/sinjira-edge-deployment-drift-readonly.yml`
exécute les tests synthétiques en CI sur PR **sans aucun secret**.
Une vérification de production purement passive est prévue au
déclenchement manuel et tous les jours une fois le correctif
fusionné dans `main`.

La vérification réelle nécessite la création volontaire d'un secret
GitHub **`SUPABASE_EDGE_READONLY_TOKEN`**, émis exclusivement avec
le droit `edge_functions:read` / `edge_functions_read`, sans
permission de déployer ou d'accéder à la base SQL. En absence de ce
secret, le workflow refuse toute assertion de succès plutôt que de
contourner la vérification.

## Effet attendu et limite importante

**Sur la production actuelle, cette vérification doit renvoyer
`NO_GO`** tant que les quatre sources actives sont différentes du
code revu. C'est un résultat de contrôle correct, non une régression
de la fonction publique.

Le contrôle ne fait aucun `POST` de sondage et aucun appel aux
endpoints clients, ne déploie aucune Edge Function, n'exécute aucun
SQL, ne lit aucune table d'utilisateur ni ne modifie le DNS. Il
n'atteste pas non plus de la justesse fonctionnelle de l'autorisation
interne : les tests Auth/RLS, CAPTCHA, consentement et qualité des
réponses NOVA doivent être menés avec des **fixtures en staging**.

Une dérive ne doit pas être corrigée par `supabase functions deploy`
en lot. Il faut confirmer pour chaque slug la source à déployer,
les imports partagés, la correspondance API/SQL, le statut JWT et
le plan de retour arrière. Seuls des déploiements ciblés,
revus et testés sont autorisés (issues #702, #713, #725, #759).

### Documentation fournisseur

- https://supabase.com/docs/reference/api/v1-list-all-functions
- https://supabase.com/docs/reference/api/v1-get-a-function-body
- https://supabase.com/docs/guides/functions/quickstart-dashboard

**Aucun changement Supabase de production, aucune migration et
aucune ouverture du sondage ne sont exécutés par ce workflow.**

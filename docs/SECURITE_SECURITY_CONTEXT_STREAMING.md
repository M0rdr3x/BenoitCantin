# SINJIRA — durcissement préparatoire de security-context

## Écart confirmé dans le code GitHub

La version source `supabase/functions/security-context/index.ts`
utilisait `await req.text()` avant de calculer le nombre d'octets reçus.
Un corps HTTP transmis sans `Content-Length` (ou avec une taille mensongère)
pouvait donc être entièrement alloué avant la limite de **4 Kio**. Son
gestionnaire d'erreurs journalisait également l'objet brut de l'exception
sans garantie d'expurgation de détails d'authentification ou du fournisseur.

La correction proposée utilise le lecteur partagé
`readLimitedUtf8Body(req, MAX_REQUEST_BYTES)` avec limite **durant**
la réception, décodeur UTF-8 strict et refus de longueur déclarée invalide.
Elle écrit un **code d'erreur constant**, sans corps de requête, JWT ni
détails d'exception. Les contrôles existants JWT, identité issue du jeton,
RPC de sécurité, no-store et minimisation des données sont conservés.

## Contrôles

- `scripts/test_security_context_streaming.mjs` exécute le lecteur
  partagé réel en Node (sans réseau, sans JWT ni accès à une base) :
  4096 octets acceptés, 4097 refusés, longueur déclarée mensongère,
  en-tête surdimensionné, UTF-8 invalide, log expurgé et validation
  JWT avant lecture du corps.
- `scripts/validate_security_context_request_security.py` refuse aussi
  la réintroduction de `req.text()`, d'un log d'exception brut,
  la suppression du lecteur streaming, le déplacement de l'authentification
  après la lecture et les altérations des en-têtes privés.
- Le workflow `SINJIRA — garde Edge Functions publiques` lance les deux
  tests avant toute promotion du code.

## Blocage absolu avant déploiement

La fonction **déployée** `security-context` et le schéma PostgreSQL
**actuellement déployé** n'ont pas le même contrat que le code source
enregistré dans GitHub (suivi **#713**).

Le code GitHub appelle `service_security_evaluate_context_session`.
Cette RPC peut ne pas exister en production tant que les migrations
approuvées ne sont pas installées. Publier uniquement cette modification
du lecteur pourrait donc **casser la connexion ou le contrôle de sécurité**.

La PR peut être revue et testée, mais demeure **NO_GO de déploiement**
jusqu'à réconciliation des migrations, audit RLS/auth.sessions, essais
sur base isolée, contrôle des issues #713 et #725, fenêtre de livraison
coordonnée et plan de retour arrière. Aucun SQL, fonction distante,
donnée utilisateur ni secret n'a été modifié ici.

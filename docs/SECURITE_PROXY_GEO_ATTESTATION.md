# SINJIRA — provenance des en-têtes de localisation de sécurité

**Périmètre :** `supabase/functions/security-context/index.ts`. La localisation est facultative et désactivée par défaut. Elle ne fait **jamais** office d'authentification ou de preuve d'identité. Les contrôles de JWT, de session, d'appareil et les RPC restent obligatoires.

## Menace et correction

Une requête directe vers une Edge Function Supabase peut inclure des en-têtes HTTP arbitraires. Un appelant peut donc écrire lui-même `cf-ipcountry: CA` ou `x-sinjira-region: Québec`. Le simple flag `SINJIRA_TRUST_GEO_HEADERS=true` ne prouve pas que la valeur a été ajoutée par un proxy de confiance.

La fonction ne transmet maintenant des valeurs de pays/région à `service_security_evaluate_context_session` que si **toutes** les conditions suivantes sont réunies :

1. `SINJIRA_TRUST_GEO_HEADERS=true` est activé côté Edge, et `SINJIRA_GEO_PROXY_HMAC_SECRET` est présent côté Edge (minimum 32 octets UTF-8, maximum 1 024).
2. Un proxy d'entrée **contrôlé**, qui dispose de ce même secret serveur, supprime les quatre en-têtes clients avant d'en générer de nouveaux; il ne les répercute jamais depuis le navigateur.
3. Les en-têtes fournis sont `cf-ipcountry` (deux lettres majuscules), `x-sinjira-region` (0–80 caractères géographiques), `x-sinjira-geo-timestamp` (millisecondes Unix, 13 chiffres) et `x-sinjira-geo-proof` (`v1=<64 caractères hexadécimaux minuscules>`).
4. La preuve HMAC-SHA256 est valide, son horodatage est dans une fenêtre de 60 secondes et elle est liée à `session_id` du JWT **déjà vérifié par le serveur**. La chaîne UTF-8 exacte à signer est :

```text
sinjira-geo/v1
<uuid-de-session-en-minuscules>
<horodatage-millisecondes>
<PAYS-ISO-2-MAJUSCULES>
<region-exacte>
```

Chaque ligne est séparée par un unique caractère `\n`, sans saut de ligne final. La preuve est un HMAC-SHA256 du message, encodé en hexadécimal minuscule, préfixé `v1=`. L'implémentation de vérification est `supabase/functions/_shared/verified-geo.mjs`.

En absence de signature valide, en cas d'erreur cryptographique, de secret manquant, de requête directe ou de preuve expirée, le service fournit **`country:null, region:null`**. Il poursuit l'évaluation de risque ordinaire **sans déclarer de localisation de confiance**.

## Conditions opérationnelles avant activation

- **Ne pas activer** la collecte approximative tant qu'un proxy signant effectivement les valeurs n'est pas déployé et testé. Mettre le secret dans les paramètres sécurisés de l'infrastructure et de Supabase, jamais dans GitHub, les fichiers statiques, une application mobile, les journaux ou une URL.
- La signature doit être calculée **après** la détermination de la session fiable, par une passerelle serveur qui valide le JWT ou reçoit l'identité vérifiée d'un composant de confiance. **Ne jamais signer un `session_id` fourni librement par le client.** Sans cette infrastructure, conserver le mode désactivé.
- Le proxy doit **écraser** les en-têtes de preuve et de localisation apportés par le client, y compris lorsqu'ils transitent via un CDN; sa liaison avec le serveur Edge doit être protégée.
- Dans une préproduction isolée, comparer pays correct, fausse région, signature altérée, secret erroné, session voisine, horodatage périmé, et requête directe contournant le proxy. Vérifier que les cas non attestés donnent un mode `disabled` et ne changent jamais l'authentification.
- Prévoir une **rotation simultanée** du secret proxy/Edge avec rollback explicite. Tout désalignement supprime la localisation, mais ne doit pas interrompre la validation du compte.
- La fenêtre de 60 secondes laisse une possibilité de rejeu *de la même localisation déjà attestée pour la même session* durant cette fenêtre; ce mécanisme n'est **pas** une garantie antirejeu absolue. Ne pas utiliser ce signal comme unique motif d'autoriser une opération sensible. Pour un usage plus critique, ajouter un nonce stocké côté serveur ou un contrôle de fraîcheur à usage unique.

## Contrôles automatiques

`node --test scripts/test_security_trusted_geo.mjs` exerce le véritable helper avec des requêtes simulées. `python scripts/validate_security_context_request_security.py` et son auto-test interdisent de revenir à une lecture directe des en-têtes dans la route. Le workflow `sinjira-public-edge-auth-guard.yml` lance ces contrôles à chaque PR pertinente.

**Aucun secret ni géolocalisation réelle n'est inclus dans ces tests; aucune modification des données et de la fonction déployée ne résulte de cette PR.**

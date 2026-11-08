# Sécurité SINJIRA — opérations sensibles et corps HTTP bornés

## Analyse du code source GitHub

Le code de trois fonctions exigeant un JWT valide vérifiait sa limite
de taille **après** `await req.text()`. Le `Content-Length` peut manquer,
être mensonger ou être malformé. Un corps non authentifié ne traverse pas
la barrière JWT, mais un client authentifié malveillant pouvait déclencher
une allocation hors limite avant le rejet de la requête.

| Fonction | Limite préexistante | Autorisations préservées |
| --- | ---: | --- |
| `delete-player-account` | 1 024 octets | identité JWT, confirmation, contrôle admin, conservation légale, MFA |
| `revoke-my-contributions` | 2 048 octets | identité JWT, portée explicite et UUID de session |
| `redeem-license-code` | 4 096 octets | identité JWT, code secret côté serveur et RPC service-only |

La lecture est maintenant assurée par
`readLimitedUtf8Body(req,MAX_REQUEST_BYTES)`, qui applique la limite
**pendant** la lecture, accepte un UTF-8 valide seulement et refuse les
`Content-Length` mensongers/invalides. Le format JSON et les contrôles
d'identité, de disponibilité et de MFA restent ceux des contrats existants.
Les erreurs de stockage, de fournisseur Auth, d'activation et de révocation
ne sont plus recopiées en clair dans les journaux : code constant uniquement.
`get-novel-file-url` expurge également son log d'exception, sans modifier
ses règles d'accès, ses fichiers privés ou la durée de ses URL signées.

## Régression

- `scripts/test_sensitive_account_streaming.mjs` :
  exécute le **vrai lecteur partagé** avec un JSON valide, le seuil exact,
  un octet en trop, un `Content-Length` mensonger, un en-tête malformé
  et un flux UTF-8 invalide, sans aucune requête distante ni compte réel.
- `scripts/validate_delete_account_v24_5_51.py` et
  `scripts/validate_contribution_revocation_v24_5_52.py` exigent le
  lecteur borné et rejettent les logs d'exception bruts.
- `scripts/validate_license_redemption_security.py` étend les
  mutations aux lectures intégrales et à la journalisation brute.
- `scripts/validate_edge_function_inventory.py` garde le contrat
  des fonctions sensibles et vérifie le code constant pour le roman privé.
- CI `SINJIRA — garde Edge Functions publiques` exécute ces validations
  sur les changements concernés.

## Politique de livraison

**Aucune migration SQL ni fonction Edge de production n'est modifiée**
par ce changement de code GitHub. Avant tout déploiement, réconcilier les
versions déployées avec les sources, les flags JWT et les migrations
(#702 et #713), puis valider les parcours réels de suppression de compte,
de conservation légale, de révocation, d'activation de licence et de
lecture privée sur une instance isolée. Exécuter le postflight de sécurité
des fonctions et disposer d'un retour arrière.

Ces protections empêchent certaines allocations et certains logs bruts,
mais elles ne remplacent **ni un quota réseau partagé, ni un WAF, ni un
audit d'autorisation et de conservation des données**.

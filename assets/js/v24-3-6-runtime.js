// Compatibilité V24.3.6 conservée volontairement.
//
// Depuis V24.4.11, ce runtime ne verrouille plus les formulaires Fracture et
// n'intercepte plus les soumissions. Le lobby officiel est géré exclusivement par :
//   - sinjira-fracture-lobby.js
//   - sinjira-fracture-engine.js
//   - les RPC serveur Fracture V24.4.6
//
// Garder ce fichier vide permet aux anciennes pages/cache qui le référencent encore
// de continuer à se charger sans recréer un deuxième contrôleur concurrent.
export const SINJIRA_V2436_RETIRED = true;

# Fracture du Réseau-Mère — mise à jour V9

Cette mise à jour est fondée sur le kit officiel fourni par Benoit Cantin.

## Fonctionnement

- Règles officielles publiées en HTML.
- 1 à 20 joueurs humains.
- Solo : 1 humain + Invisibles 2 et 3 dans une seule fiche privée.
- Duo : chaque humain possède sa fiche personnelle + sa propre fiche du Joueur invisible 3.
- 3 à 20 : une fiche personnelle privée par joueur.
- Sauvegarde automatique dans le Compte SINJIRA du joueur.
- Les fiches privées ne sont jamais copiées dans la base d’analyse.
- Seule la Feuille de fin de partie peut être transmise à SINJIRA.
- Format express 6 rondes activé seulement à 13-20 joueurs.

## Fichiers web

- `index.html` : description officielle.
- `regles.html` : règles complètes.
- `jouer.html` : création / jonction de parties.
- `partie.html` : fiche privée du joueur.
- `fin-de-partie.html` : résultats collectifs.
- `assets/js/sinjira-fracture-online.js` : logique en ligne.
- `assets/css/fracture-online.css` : styles.

## Supabase

Appliquer :
`supabase/migrations/20260810_fracture_online_1_20.sql`

Déployer :
`submit-fracture-endgame`

L’Edge Function ne lit jamais `fracture_player_documents`.
Elle lit uniquement `fracture_endgame_reports`.

Pour recevoir aussi un courriel de fin de partie, configurer :
- `RESEND_API_KEY`
- `REPORT_FROM_EMAIL`
- `FRACTURE_REPORT_TO_EMAIL` (facultatif; défaut : kingtyrano@gmail.com)

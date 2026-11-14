# SINJIRA™ — V92 : retour du cache de navigation, reprise de lecture et droits privés

**14 novembre 2026 — PR #1000 (DRAFT), pas de fusion ni de mise en production.**

## Problème

Sur Safari iOS et certains autres navigateurs, le bouton Retour peut restaurer la page depuis le **Back-Forward Cache (BFCache)**, sans recharger ses scripts. Le gestionnaire de `pagehide` fermait jusqu'ici le module des repères V28, dont `close()` est irréversible. Résultat possible : le texte demeure affiché mais les marque-pages, recherches et annotations ne fonctionnent plus après le retour.

Sur l'**édition intégrale**, une page conservée dans le BFCache ne doit jamais supposer que la session et le droit de lecture sont encore valides lorsque l'utilisateur revient.

## Correctifs V92

1. `pagehide(event.persisted===true)` : conserver le module de repères en mémoire, pour ne pas le fermer prématurément dans la **démo publique**. Une navigation normale hors cache continue de libérer le module.
2. Pour l'**édition privée**, cacher immédiatement `#reader-content` à la sortie; sauvegarder en mémoire la page et un ratio de défilement **numérique**, sans texte ni URL signé.
3. `pageshow(event.persisted===true)` en édition intégrale : revérifier l'utilisateur via `auth.getUser()` **puis** demander une nouvelle autorisation au serveur via `get-novel-file-url`. Contrôler `ok`, l'URL `https`, l'origine attendue et le préfixe du chemin signé avant de réafficher les octets déjà chargés en mémoire. Une session changée, un droit révoqué ou un réseau indisponible entraîne une **fermeture sécurisée** de la liseuse intégrale.
4. Après autorisation valide : réafficher le livre et restaurer son emplacement numérique en mémoire; aucune nouvelle écriture de progression ou stockage du texte n'est déclenché.
5. À la déconnexion ou invalidation : effacer aussi le repère éphémère BFCache.

## Recette et limites

- **Test navigateur automatisé démonstration** (Chromium/WebKit) dans `test_sinjira_liseuse_auto_resume_v85.py` : simuler `pagehide.persisted=true` puis `pageshow.persisted=true`, créer un marque-page sur la démo et vérifier qu'il est effectivement sauvegardé; vérifier que le lecteur reste visible.
- Les régressions existantes couvrent les gestes gauche/droite, la reprise locale après rechargement et les messages lorsque le stockage est refusé.
- **Non testé sur un compte réel** : restauration BFCache privée, révocation de droit, expiration de session et panne réseau sur iPhone et Android. La validation est conçue en mode « fail closed » mais doit être réceptionnée avec un environnement privé de test autorisé avant toute production.
- Le BFCache est un comportement de navigateur variable : un événement simulé prouve la logique applicative, pas l'usage réel de la mémoire de navigation de Safari.

**Décision NO-GO** : cette correction n'annule ni les risques connus du CAS cloud, ni les travaux RLS en PR séparées, ni les 13 conditions de lancement ouvertes. Aucune migration Supabase/SQL, aucun changement de droit, aucun roman privé stocké. Les indicateurs de référence restent inchangés : Nova 47 %, services publics Nova–Sinjira sans pourcentage global, sondage 54,5 %, boussole 75 %, SINJIRA 66,5 % ±10 points; aucune date de lancement supplémentaire garantie.

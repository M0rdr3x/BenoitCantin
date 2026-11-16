# SINJIRA V130 — annulation des gestes lors du passage en plein écran

**15 novembre 2026 — PR #1000 en brouillon, non fusionnée, non déployée.**

## Risque corrigé dans la branche candidate

Le module V28 émet `sinjira:reader-layout-will-change` avant de modifier `reader-focus-mode` et la taille CSS du livre. Cela peut se produire sans `resize`. V52 n'écoutait pas cet événement : une trajectoire tactile ou un drag souris PDF commencé avant la modification pouvait déclencher une page fantôme si l'affichage revenait à la géométrie initiale.

- V52 : annule immédiatement les trajectoires tactiles et souris PDF lors du signal V28, retire l'écouteur au démontage.
- V53 : invalide le contact avant la vérification du mode paginé; la conservation d'ancre V63 et la restauration V88 restent inchangées.
- Versions V52 `52.11.15.130` et V53 `53.11.15.130` mises à jour dans les pages et les tests.
- Tests Node ajoutés : plein écran sans resize pendant un toucher PDF / texte et pendant un drag souris; vérification de nouveaux gestes gauche/droite.
- Test Playwright V58 ajouté pour la vraie page HTML isolée, avec livre fictif et réseau Supabase bloqué.
- Contrôles GitHub Actions à **vérifier sur le SHA final** avant de déclarer leur réussite.

**Aucun accès au roman privé, stockage, droit serveur, Auth, RLS, SQL ou paiement modifié.**

**NO-GO production :** essais iPhone/Android physiques, VoiceOver/TalkBack, accès à l'intégrale, synchronisation entre appareils, revue indépendante et validation humaine restent obligatoires. Les pourcentages de maturité ne changent pas automatiquement.

# SINJIRA V135 — arrêter la voix quand la lecture passe en arrière-plan

**16 novembre 2026 — PR #1000 DRAFT, pas encore fusionnée ni déployée.**

## Risque mobile constaté dans le code

Sur téléphone, un changement d'application ou le verrouillage de l'écran peut déclencher `document.visibilitychange` sans `window.pagehide`. Le contrôleur arrêtait bien `speechSynthesis` sur `pagehide` et à la révocation de la session, mais ne l'arrêtait pas systématiquement sur `visibilitychange(hidden)`. Il existait donc un risque qu'un extrait du roman, y compris intégral privé, continue à être énoncé alors que la page est masquée.

## Correction

- Dès `document.visibilityState === 'hidden'`, demander l'arrêt explicite de la synthèse vocale, avant la sauvegarde locale et le masquage du roman privé. L'arrêt invalide le jeton des opérations de voix en attente.
- Ne pas reprendre la voix automatiquement quand l'application revient au premier plan. Si elle était active, afficher une indication claire : « Lecture vocale interrompue en arrière-plan. Relancez-la pour poursuivre. »
- Conserver la suspension/revalidation de la session et des droits serveur du roman intégral, et les gestes tactiles déjà validés.
- Actualiser la version de cache du script V26 dans `compte/liseuse.html` à `34.11.16.135`. Aucun service audio externe ou nouveau stockage n'est ajouté.

## Régression CI

Dans `tests/e2e/test_sinjira_liseuse_responsive_v58.py`, une voix synthétique silencieuse est installée **avant** l'initialisation du vrai lecteur (sur PDF fictif, sans Supabase). Après avoir commencé la lecture, un changement `visibilitychange(hidden)` doit :
1. appeler `cancel()` sur la voix silencieuse;
2. empêcher un ancien `onend` de démarrer un nouveau passage;
3. désactiver la commande Arrêter et signaler clairement l'interruption.

L'essai doit réussir sur Chromium et WebKit; **résultat GitHub Actions sur le SHA final à vérifier**. Les tests de synthèse simulée ne constituent pas une validation de VoiceOver/TalkBack ni du verrouillage physique iPhone/Android.

**NO-GO production** : pas de changement Auth/RLS/migration, PR liseuse DRAFT. Il reste les essais réels, le droit privé et sa révocation, et la synchronisation multiappareils. Le score global SINJIRA reste à **66,5 % estimés ±10 points**.

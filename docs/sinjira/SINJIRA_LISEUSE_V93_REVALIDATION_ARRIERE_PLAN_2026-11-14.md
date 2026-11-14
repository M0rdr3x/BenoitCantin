# SINJIRA™ — V93 : protéger la reprise du roman intégral sur mobile

**14 novembre 2026 — PR #1000 DRAFT, aucun déploiement.**

## Menace et comportement corrigé

Sur iPhone ou Android, un lecteur peut changer d'application ou verrouiller son téléphone sans déclencher `pagehide` ou la navigation BFCache. Dans V92, seule une restauration `pageshow.persisted` revalidait la session privée. Au retour d'une simple mise en arrière-plan, un ancien roman pouvait rester affiché sans vérifier que le compte détenait encore le droit. Par ailleurs, une vérification réseau antérieure pouvait se terminer **après** une seconde suspension et dévoiler un contenu devenu périmé. Enfin, masquer seulement `#reader-content` ne protégeait pas les citations et notes privées éventuellement présentes dans la barre latérale.

## Modifications V93

- **Au `document.visibilitychange(hidden)` ou `pagehide`** : mémoriser seulement la page et le ratio numérique en mémoire, incrémenter un jeton de génération, masquer le contenu **et** la barre latérale de l'édition intégrale; conserver la démo et ses marque-pages intacts.
- **Au retour `visibilitychange(visible)` ou `pageshow.persisted`** : nouvelle vérification de l'utilisateur par `auth.getUser()`, puis nouvelle autorisation par l'Edge Function `get-novel-file-url`. Vérifier l'URL HTTPS signée, l'origine attendue et son préfixe avant de montrer de nouveau le roman et ses notes.
- **Pendant un retour concurrent** : une seule vérification en vol, invalidation par `privateReturnGeneration` si une seconde suspension arrive; ne jamais réafficher un ancien PDF ou ses notes sur un résultat d'autorisation obsolète.
- **Droit révoqué, session différente ou erreur réseau** : `lockPrivateReader()` vide le texte, les notes et le canvas, masque le contenu et conserve un message d'erreur. Aucun texte du roman ou URL signée ne rejoint `localStorage`.
- Restauration de la position numérique en mémoire uniquement après une autorisation actuelle valide.

## Recette automatisée

Dans `tests/e2e/test_sinjira_liseuse_auto_resume_v85.py`, ajouter un scénario isolé de **page HTML intégrale simulée** en Chromium et WebKit : PDF synthétique de 520 pages, serveur Supabase remplacé par un stub local, origine signée simulée. Aucun appel externe ou roman intégral réel.

Contrôles :
1. Charger l'édition privée avec identité et droit simulés valides.
2. Masquer l'onglet : vérifier immédiatement que `#reader-content` et `.reader-sidebar` sont cachés.
3. Révoquer le droit de lecture, revenir au premier plan : vérifier que le contenu privé reste masqué et que le texte en mémoire est détruit.
4. Recharger le scénario, suspendre, lancer un `getUser` différé, suspendre **à nouveau**, achever la première vérification : aucun contenu ne peut être réexposé; une nouvelle revalidation doit réussir au retour suivant.

**Limites** : les événements et le serveur sont simulés; leur réussite ne remplace ni des tests sur appareils physiques ni une vraie revue RLS/Edge Function, ni la migration CAS V51. Les 13 conditions de lancement SINJIRA demeurent **NO-GO**. Référence des programmes au 8 novembre inchangée : Nova 47 %, Nova–Sinjira sans pourcentage défendable, sondage 54,5 %, boussole 75 %, SINJIRA 66,5 % ±10 points.
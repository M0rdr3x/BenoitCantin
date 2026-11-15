# SINJIRA V127 — bloquer les pages fantômes lorsque l'observateur a déjà livré les changements

**15 novembre 2026.** Code candidat PR #1000, non fusionné et non déployé.

## Cas résiduel après V126

Le moteur paginé V53 inspectait depuis V126 les enregistrements `MutationObserver.takeRecords()` **en attente** avant `touchend`. Mais si l'observateur a déjà appelé son callback lors d'une micro-tâche (par exemple après un `await`), il ne restait aucun record et le moteur ne remettait pas `gesture` à `null`. Une page de texte remplacée ou le livre intégral masqué puis révélé pouvait alors autoriser la fin d'un balayage commencé sur le contenu précédent.

La V53 a priorité sur la V52 en phase de capture pour le mode texte paginé : la seule protection V52 ne suffit pas.

## Correctif

- Dans le callback du texte (`childList`, `characterData` ou `hidden`), annuler immédiatement le geste en cours avant `afterTextChanged()`. Garder l'actualisation normale des écrans.
- Sur les changements `hidden` de `#reader-content`, annuler également le geste que la fermeture/réouverture du livre privé ait précédé `touchend` ou non. Préserver la purge du statut vocal PDF de V124.
- V127 inspecte aussi les mutations de visibilité de `#reader-content` encore en attente dans `flushPendingTextMutation()`, y compris si aucune mutation de texte n'est en attente. L'interception n'interfère ni avec la sélection ni avec les gestes démarrés après l'actualisation.
- Aucun changement d'authentification, stockage, contenu de roman ni sauvegarde; la V52 PDF conserve ses protections V125.
- Cache V53 **`53.11.15.127`** dans la page, la fixture et les contrats de test. V52 reste en `52.11.15.125`.

## Recette

Node : callback déjà livré entre `touchstart` et `touchend`, mutation de texte, fermeture/réouverture d'un roman, mutation `hidden` encore en attente, puis retour aux vrais swipes gauche/droite. Playwright Chromium et WebKit sur la vraie liseuse isolée (roman fictif) : `await Promise.resolve()` entre l'actualisation et `touchend`, aucun tournage d'écran ni de page source.

**Statut NO-GO :** PR brouillon, non fusionnée sur `main`, aucun déploiement. Homologation sur vrais iPhone/Android, VoiceOver/TalkBack, droits Auth/RLS et synchronisation interappareils, plus validation humaine des 13 conditions de lancement. Les scores de maturité Nova/SINJIRA ne sont pas recalculés.

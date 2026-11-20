# SINJIRA V143 — préserver le PDF lors d'une rotation en arrière-plan

**16 novembre 2026 — PR #1000 DRAFT, non déployée.**

## Problème

Sur iPhone/Android, l'apparition et la disparition des barres du navigateur, une rotation, un retour depuis une autre application ou le verrouillage de l'écran peuvent envoyer `resize` lorsque la liseuse est masquée. La méthode V26 `refreshVisiblePdfPreservingSpot()` continuait à mesurer `#reader-viewer.clientWidth` et à appeler `renderPage()` après un délai de 250 ms, même avec le roman masqué ou suspendu. Une largeur nulle peut produire un canvas miniature et une restauration de position incorrecte, surtout dans les pages illustrées PDF.

## Correctif V143

- Ignorer les événements `resize` lorsque l'onglet ou `#reader-content` est caché, et si l'édition privée est suspendue/révoquée, grâce à `canRecordReaderInteraction()`.
- **Revalider au déclenchement effectif de `refreshVisiblePdfPreservingSpot()`**, car un délai programmé en premier plan peut expirer après une transition vers le masquage.
- Ne pas remplacer `state.restorePending`, `state.restoringScroll`, la taille du canvas ou les préférences lorsque le lecteur est indisponible.
- Conserver le comportement de zoom/rotation lorsque le PDF est de nouveau visible et la session autorisée.
- Ne modifier ni les droits Supabase, ni le stockage du roman, ni les gestes tactiles gauche/droite. Cache JS V26 aligné sur `34.11.16.143` dans l'HTML et le contrat Node.

## Vérification

Test Playwright V57 avec vrai HTML, PDF fictif et Supabase interdit. Ouvrir le mode PDF, enregistrer dimensions du canvas, page, zoom et progression; déclencher un `resize` puis masquer aussitôt l'écran AVANT l'expiration des 250 ms; confirmer aucune mutation après 340 ms. Recommencer avec un `resize` émis pendant le masquage. Réafficher le PDF, effectuer un `resize` normal et revenir au mode paginé pour vérifier la régression mobile. Exécuter les suites Chromium et WebKit sur le SHA exact.

**État : candidate en PR DRAFT; résultats CI à vérifier.** La réception physique iPhone Safari/Android Chrome, VoiceOver/TalkBack, l'homologation des droits/révocations réels et la synchronisation multiappareils restent nécessaires. Les indicateurs d'avancement Nova/SINJIRA ne changent pas.

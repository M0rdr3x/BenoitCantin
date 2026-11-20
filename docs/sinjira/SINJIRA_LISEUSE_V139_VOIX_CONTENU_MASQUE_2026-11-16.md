# SINJIRA V139 — narration arrêtée dès que le livre est masqué

**16 novembre 2026 — PR #1000 DRAFT, aucun déploiement.**

## Risque couvert

Les correctifs V135/V136 empêchent la narration lorsque l'onglet du navigateur devient `visibilityState === hidden`, et lors de la suspension/révocation des droits des livres intégraux. Mais une interface peut masquer `#reader-content` sans masquer l'onglet, lors d'une transition d'édition, d'une fermeture de panneau ou d'une suspension privée en cours. Dans ce cas, la lecture à voix haute ne doit ni démarrer ni poursuivre un passage, même si des promesses `PDF.getPage/getTextContent` se terminent tard.

## Correction

- Introduire `canNarrateVisibleBook()` : onglet visible, contenu du roman affiché, et pour l'édition intégrale ni suspension ni révocation.
- Appeler ce contrôle avant le démarrage, après les chargements asynchrones, à chaque segment de `speechSynthesis`, et avant la reprise d'une voix en pause.
- Observer **uniquement** les mutations de l'attribut `hidden` de `#reader-content` (aucun texte lu, transmis ou conservé). À tout masquage/affichage, invalider le jeton de narration en attente et annuler les paroles anciennes. En cas de retour, il faut cliquer volontairement sur « Écouter ».
- Actualiser le cache V26 vers `34.11.16.139` dans le vrai HTML et le contrat Node, sans modifier les autorisations serveur, les données personnelles ou les fichiers de roman.

## Régression automatisée

Le parcours `tests/e2e/test_sinjira_liseuse_responsive_v58.py` utilise la vraie page HTML, un PDF fictif local, les services Supabase bloqués et une voix silencieuse injectée avant initialisation. Il masque `reader-content` sans toucher à `document.visibilityState`, déclenche le bouton « Écouter », vérifie l'absence de narration, puis teste une reprise explicite visible. Il masque également le roman pendant une voix active, force un ancien `onend`, et alterne rapidement masqué/visible pendant un démarrage asynchrone pour confirmer qu'aucun passage tardif ne commence.

**CI du SHA final à vérifier** dans les navigateurs Chromium et WebKit. Il reste à homologuer les appareils physiques, VoiceOver/TalkBack, les droits et leur révocation avec des comptes de test, et la synchronisation multiappareils avant fusion. **Les scores globaux Nova/SINJIRA demeurent inchangés.**

# SINJIRA V132 — sélection de texte sans menu : ne pas tourner l'écran

**16 novembre 2026. Correctif candidat sur la PR #1000 (DRAFT), non fusionné et non déployé.**

## Cas limite traité

Dans certains navigateurs tactiles, notamment avec les poignées de sélection iOS, un utilisateur peut ajuster une sélection pendant un contact sans ouverture du menu `contextmenu`. La V131 annulait le contact à l'ouverture du menu, mais une modification de sélection pouvait se produire sans menu. Même si le texte est désélectionné avant `touchend`, un déplacement latéral résiduel ne doit pas être interprété comme « suivant » ou « précédent ».

## Correction

- **V52 (PDF et texte continu)** : suivre `document.selectionchange` et invalider uniquement les trajectoires tactile/souris déjà en cours. Ne pas lire, enregistrer ni émettre le texte sélectionné. Les gestes et menus natifs restent libres.
- **V53 (texte paginé)** : invalider la trajectoire d'un doigt actif lors de `selectionchange`, sans modifier les curseurs de lecture ni écrire de progression.
- Retirer les écouteurs au démontage. Les nouveaux glissements **gauche = suivant** et **droite = précédent** fonctionnent normalement après la sélection.
- Versions de cache synchronisées : **V52 52.11.16.132**, **V53 53.11.16.132** dans `compte/liseuse.html`, les imports ESM, la fixture et les tests.

## Tests prévus

1. Node PDF : `selectionchange` entre `touchstart` et `touchend` et entre `pointerdown` et `pointerup` ; aucune page fantôme, puis navigation gauche/droite, nettoyage du listener.
2. Node texte paginé : même situation et aucun changement d'écran, puis navigation normale.
3. Playwright Chromium/WebKit, page HTML de test isolée avec roman fictif et Supabase interdit : signal de sélection avant la fin d'un swipe, sans `contextmenu`.
4. **Consulter les résultats GitHub Actions du SHA final** avant toute validation.

**Statut de lancement : NO-GO**, tant que les essais sur appareils physiques, VoiceOver/TalkBack, droits serveur des œuvres intégrales, synchronisation et revue indépendante n'ont pas été homologués. Les scores globaux Nova/SINJIRA ne sont pas rehaussés par ce seul correctif.

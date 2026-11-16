# SINJIRA V145 — restaurer la lecture au retour d'une application mobile

**16 novembre 2026 — PR #1000 DRAFT, non fusionnée ni déployée.**

## Cas découvert

V144 reporte le recalcul de pagination lorsque l'écran est masqué pendant une rotation. Il réactivait ce calcul à la réouverture de `#reader-content[hidden]`. Mais sur la démo et certains navigateurs mobiles, passer dans une autre application change **`document.hidden` sans modifier `#reader-content.hidden`**. Si un `resize` se produit pendant cet arrière-plan, `deferredLayoutRatio` reste en mémoire, et aucune restauration n'est lancée au retour. Le navigateur peut aussi remettre `scrollTop` à 0 pendant une suspension.

## Correctif

- Introduire une seule fonction `resumeDeferredLayout()` de réouverture (2 requestAnimationFrame), utilisée à la fois par l'observateur de visibilité du contenu et par `visibilitychange` quand l'onglet redevient visible.
- Refuser toute reprise si le roman reste masqué ou si la fenêtre ne peut pas naviguer; pour les œuvres privées, l'autorisation reste gérée par la revalidation serveur avant réaffichage.
- Restaurer la dernière ancre/position connue après retour sans enregistrer de texte du livre, sans écriture en base, sans prétendre avoir validé les appareils physiques.
- Ne pas réactiver deux fois une restauration : la première reprise consomme `deferredLayoutRatio`; les callbacks ultérieurs ne font que resynchroniser l'interface. Les gestes volontaires continuent d'invalider une restauration obsolète.
- Cache V53 synchronisé vers `53.11.16.145` dans HTML, fixture et tests Node/E2E V58.

## Régression

Dans `tests/e2e/test_sinjira_liseuse_real_page_v57.py`, avec PDF synthétique et Supabase bloqué : lire au milieu de la page 3, simuler `document.hidden=true` et un `resize`, remettre le défilement à 0 comme le ferait un navigateur ayant perdu le scroll, puis restaurer `document.hidden=false` **sans changer `#reader-content.hidden`**. Après 12 frames, vérifier la même page et la restitution du passage proche de sa position initiale, dans Chromium et WebKit. Les suites tactiles V64–V69 doivent rester vertes.

**CI du SHA final à contrôler.** La réception iPhone Safari, Android Chrome, tablettes physiques, VoiceOver/TalkBack, droits et révocations des livres intégralement privés et synchronisation multiappareils restent des conditions de publication. **NO-GO production**, scores programmes inchangés.

# SINJIRA V146 — conserver le mode de lecture paginé lors d'un masquage

**16 novembre 2026 — PR #1000 DRAFT, non fusionnée et non déployée.**

## Constat

Les correctifs V140/V141 sécurisent les réglages PDF et typographiques lors du masquage d'un livre. Il restait un autre contrôle de présentation : la case `#reader-screens-enabled` de la liseuse V53. Son événement `change` pouvait encore enregistrer `sinjira:liseuse:lecture-par-ecrans:v53` et recalculer la disposition lorsque le livre était masqué ou l'onglet passé en arrière-plan. Un `change` différé depuis le téléphone pouvait donc faire basculer silencieusement la lecture par écrans vers le mode continu, ou l'inverse.

## Correctif

- Initialiser `acceptedScreenToggle` avec le choix chargé au démarrage; il demeure le dernier choix confirmé en mémoire, même si localStorage est indisponible.
- Refuser les `change` du mode écrans lorsque `canNavigate()` est faux, **avant** toute modification d'ancre, sauvegarde de préférence, changement de mode ou restauration de scroll.
- Rétablir immédiatement la case à son dernier état accepté, sans émission d'un nouveau signal `change` et sans modifier un livre privé masqué.
- En lecture visible, accepter les modifications explicites comme avant et continuer d'enregistrer `on/off` dans localStorage, avec maintien des gestes gauche/droite et du mode continu.
- Synchroniser la version de cache du moteur V53 à **53.11.16.146** dans l'HTML, le test Node, la fixture et les imports E2E.

## Test de non-régression

Dans `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : ouvrir la vraie page HTML avec PDF fictif et services privés bloqués, masquer `#reader-content`, tenter un changement de case et comparer strictement état, mode, page, annonce d'écran et préférence locale. Réouvrir puis désactiver/réactiver volontairement le mode paginé; confirmer que le mode continu puis le mode écrans se rétablissent et que la préférence est enregistrée seulement pendant une interaction visible. Exécuter ensuite les parcours de gestes Chromium/WebKit.

**CI du SHA exact encore à contrôler.** La réception sur vrais appareils iOS/Android, VoiceOver/TalkBack, la révocation effective des droits privés et la synchronisation multiappareils ne sont pas certifiées. **NO-GO production**; les scores globaux Nova/SINJIRA ne changent pas.

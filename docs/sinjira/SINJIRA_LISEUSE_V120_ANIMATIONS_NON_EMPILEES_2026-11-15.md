# SINJIRA V120 — tournage rapide fluide sans animations superposées

**15 novembre 2026 — correctif candidat dans la PR #1000, non publié.**

## Problème UX

V119 a ajouté un liseré de 180 ms au bord du livre pour confirmer chaque changement de page. Des glissements gauche/droite rapprochés pouvaient lancer plusieurs animations simultanées sur le même élément et créer des éclairs superposés, gênants pendant la lecture prolongée sur cellulaire.

## Changement

- V52 conserve **une animation active au maximum par élément de lecture**, au moyen d'un `WeakMap` éphémère. L'effet précédent est annulé avant un nouveau tournage; les événements de fin ou d'annulation libèrent la référence.
- Si l'utilisateur active la préférence système `prefers-reduced-motion: reduce` pendant la lecture, le prochain geste arrête aussi le liseré précédent et n'en crée pas d'autre, tout en tournant normalement la page.
- Les pertes de focus, la mise en arrière-plan, la fermeture de page et la destruction des contrôleurs V52/V53 arrêtent l'effet restant. L'animation est facultative : une API absente ou défaillante ne bloque jamais les gestes.
- Aucun changement des extraits de livre, de la progression, des identifiants, des droits privés ni de la synchronisation. Les numéros de page, les protections antérieures et les choix d'affichage restent inchangés.
- Versionnement cohérent : touch `52.11.15.120`, reflow `53.11.15.120`.

## Recette

- Node : 2 changements de page rapprochés annulent le premier effet, le second reste seul; passage en mouvement réduit coupe la seconde animation sans en ajouter; un effet terminé ne garde plus de référence; nettoyage explicite idempotent.
- Playwright Chromium/WebKit : instrumentation de la vraie page mobile pour deux swipes normaux, vérification de l'annulation du premier effet, puis activation de la préférence de réduction de mouvement et confirmation de l'arrêt du dernier effet sans empêcher l'avancement et le retour de page.

**Statut NO-GO** : PR #1000 DRAFT, non fusionnée dans `main` et non déployée. Tests sur appareils physiques iOS et Android, VoiceOver/TalkBack, droits d'accès privés Auth/RLS, synchronisation multi-appareils et les 13 conditions de lancement doivent encore être homologués. Les pourcentages Nova et SINJIRA n'en sont pas recalculés.

# SINJIRA — V109 : restaurer immédiatement le curseur tactile interrompu

**14 novembre 2026 (Québec) — candidat en revue PR #1000 ; NO-GO production.**

## Problème et correctif

Lors d'un glissement sur « Aller à l'écran », le curseur pouvait afficher une sélection d'écran différente de la portion réellement lue si l'utilisateur changeait d'application ou interrompait le geste et si le navigateur n'envoyait ensuite aucun événement `change`. Le texte de l'attribut `aria-valuetext` continuait alors d'annoncer « relâcher pour lire », alors que le doigt n'était plus sur le curseur.

V109 rétablit immédiatement la valeur du curseur et son libellé accessible via `sync()` **uniquement lorsqu'une prévisualisation a été interrompue**. Ce traitement ne déplace pas le livre, n'envoie aucun événement `sinjira:reader-screen-turn` et n'enregistre aucune position. Les confirmations tardives sont toujours ignorées et un nouveau glissement fonctionne normalement.

## Validation automatisée

- Tests Node : perte de focus, visibilité, `pagehide`, `touchcancel` et nouveau glissement.
- Parcours navigateur de la vraie page sous Chromium et WebKit, avec capture du curseur et de `aria-valuetext` **avant** toute confirmation différée, puis reprise normale.
- Cache du moteur V53 mis à jour sur `53.11.14.109` dans la page, la fixture et les tests.

Aucune modification des romans privés, du contrôle d'accès, des comptes, de Supabase, de RLS, des migrations ou du site déployé.

**Publication non autorisée** avant réception sur iPhone Safari / Android Chrome physiques, VoiceOver/TalkBack, contrôle des droits de livres privés, synchronisation entre deux appareils et homologation humaine des portes de lancement. Aucun changement aux pourcentages des programmes.

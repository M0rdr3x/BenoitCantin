# SINJIRA V121 — annonces des vraies pages PDF aux lecteurs d'écran

**15 novembre 2026** — code candidat PR #1000, non publié.

## Cas corrigé

Le mode texte paginé dispose déjà d'une zone `aria-live` pour les écrans. En revanche, cette zone est masquée en mode PDF et texte continu. La position affichée dans la barre mobile est `aria-hidden`. La simple modification de l'attribut `aria-label` du visualiseur n'annonce pas systématiquement une nouvelle page sans mouvement du focus sur VoiceOver/TalkBack.

## Solution

Créer dès le chargement un statut dédié `#reader-page-announcement` (`role=status`, `aria-live=polite`, `aria-atomic=true`), réduit visuellement à 1 pixel par CSS sans `display:none` ou `aria-hidden`.

Le moteur V53 attend l'événement canonique V26 `sinjira:reader-page-change`. Si le numéro de page a réellement changé, que le mode écran texte n'est pas actif et que le contenu est visible dans un onglet actif, il écrit uniquement « Page N sur TOTAL du livre. » dans la zone. Aucun extrait de roman, identifiant, statut d'accès ou progression privée n'est transmis. Les chargements initiaux, les événements répétés, les numéros invalides et les pages masquées ne sont pas annoncés.

## Couverture

Node : page initiale silencieuse, PDF changeant de page, répétition, texte paginé sans double annonce, onglet suspendu, livre masqué, entrée invalide et vérification des attributs ARIA/CSS. Playwright Chromium/WebKit sur fixture locale à roman fictif : signal de page simulé, contrôle d'annonce, répétition silencieuse, dimensions de zone cachée et restauration de la lecture.

Module V53 version `53.11.15.121` et CSS `53.11.15.121`; module tactile V52 inchangé. **NO-GO publication :** PR brouillon non fusionnée, validation réelle VoiceOver/TalkBack et appareils iOS/Android, droits Auth/RLS, synchronisation et 13 conditions de sortie toujours nécessaires. Les taux de maturité Nova/SINJIRA ne changent pas.

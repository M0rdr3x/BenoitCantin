# SINJIRA V124 — ne pas annoncer la page d'un ancien livre

**15 novembre 2026 — PR #1000 en brouillon, pas de déploiement.**

## Cas corrigé

Le lecteur d'écran dispose depuis V121 d'un statut live dédié aux pages PDF, mais ce message pouvait rester dans le DOM lorsque l'on cachait un roman privé ou que l'on repassait au mode de texte paginé. Si un autre livre est réaffiché sur la même page source, une ancienne annonce peut être trompeuse. Le numéro de page lui-même n'est pas une citation, mais il ne devrait pas survivre au changement de livre.

## Solution

- Lorsque le lecteur passe en mode texte paginé (qui possède déjà son `aria-live`) ou que la lecture n'est plus visible/autorisée, vider l'ancien message PDF dans `#reader-page-announcement`. Aucun changement de focus, de progression, de texte ou de pages.
- Surveiller uniquement l'attribut `hidden` de `#reader-content`. S'il est masqué sans événement de nouvelle page, purger immédiatement le message via `MutationObserver`. Une réouverture ne réémet pas automatiquement l'ancien statut. Une vraie nouvelle page PDF reste annoncée comme avant.
- Nettoyer l'observateur au démontage du lecteur. Aucun stockage ni nouvel appel serveur.
- Mise à jour cache-bust V53 `53.11.15.124` dans HTML, fixture et assertions; V52 tactile conserve `52.11.15.123`.

## Tests

Node : purger un numéro de page annoncé lors du masquage, rester silencieux au retour sur la même page, annoncer un véritable nouveau numéro, vider le statut PDF en mode écran. Adaptation des assertions V121 à cette suppression intentionnelle de la valeur périmée. Playwright Chromium/WebKit sur le HTML isolé : afficher l'annonce PDF d'un roman fictif, masquer et réafficher `#reader-content`, contrôler le silence, puis restaurer les pages de texte sur cellulaire.

**NO-GO publication :** PR #1000 DRAFT, non fusionnée dans `main`, aucun déploiement; essais physiques Safari iPhone/Chrome Android, VoiceOver/TalkBack, contrôle Auth/RLS des romans privés, synchronisation multi-appareils et les 13 portes de lancement toujours à homologuer. Les pourcentages Nova/SINJIRA restent ceux du bilan documentaire de novembre 2026.

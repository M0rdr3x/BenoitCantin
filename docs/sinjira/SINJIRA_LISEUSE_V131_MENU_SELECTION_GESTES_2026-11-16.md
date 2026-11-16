# SINJIRA V131 — conserver la sélection sans tourner le livre accidentellement

**16 novembre 2026 — PR #1000 DRAFT, non fusionnée et non déployée.**

## Risque identifié
Le menu contextuel natif d'un appui prolongé (sélection, copier) peut être ouvert sur mobile sans `touchcancel`. Un swipe antérieur ou un drag PDF à la souris pourrait être finalisé après l'ouverture du menu, provoquant un changement de page involontaire.

## Modification candidate
- **V52 PDF** : écouter `contextmenu` sur la zone du livre; annuler l'origine tactile et le drag souris en cours et toute animation périmée, sans utiliser `preventDefault`.
- **V53 pages d'écran** : appliquer la même annulation de contact dès l'ouverture du menu, sans supprimer la sélection native.
- Supprimer les écouteurs au démontage. La logique des boutons et des nouveaux gestes gauche/droite reste inchangée.
- Versions cache V52 `52.11.16.131` et V53 `53.11.16.131` synchronisées dans HTML, fixture, import et tests.
- Régressions Node V52/V53 et contrôle Playwright V58 sur une page de livre fictif avec Supabase bloqué.

## Livraison
**CI à vérifier sur le SHA final.** Aucune modification Auth, RLS, stockage privé, synchronisation ou migration. PR #1000 maintenue **DRAFT / NO-GO**, essais iOS/Android physiques, VoiceOver/TalkBack, droits des romans privés et approbation humaine toujours requis. Le score SINJIRA n'est pas réévalué du seul fait de cette modification.

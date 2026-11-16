# SINJIRA V137 — protéger toutes les commandes de navigation quand le livre est masqué

**16 novembre 2026 — code de travail dans la PR #1000 DRAFT, non déployée.**

## Risque

Les gestes tactiles du moteur V52/V53 vérifient déjà si le livre est masqué, mais l'ancienne fonction centrale `changePage()` du moteur V26 pouvait aussi être appelée depuis les champs numériques, curseurs, choix de chapitre, boutons ou compagnon de lecture, sans vérifier systématiquement la suspension de l'édition privée. Cela pouvait modifier la position ou solliciter un rendu de page lorsque le roman devait rester invisible jusqu'à une nouvelle autorisation.

## Correction

- Au point d'entrée commun `changePage()`, refuser la navigation lorsque `visibilityState === 'hidden'`, lorsque `#reader-content` est masqué, ou lorsque l'édition intégrale est suspendue/révoquée.
- Ne pas écrire de nouvelle progression, ne pas lancer de rendu ni changer la page. Re-synchroniser uniquement les contrôles de page avec la valeur canonique pour éviter une fausse page affichée après une action refusée.
- Aucune nouvelle permission ou API privée; les contrôles d'autorisation serveur et les gestes précédemment validés restent inchangés.

## Régression

Sur la vraie page de démonstration HTML en Playwright, avec fichier PDF fictif et réseau Supabase interdit, masquer `#reader-content` puis tenter de changer la page par le champ, le curseur, le sélecteur de chapitre et les boutons. Vérifier que le numéro, les contrôles et la position restent identiques, puis vérifier la réouverture en mode paginé. Exécuter la suite Chromium/WebKit et les régressions Node du dépôt sur le SHA exact du correctif.

**Validation sur compte intégral privé autorisé/révoqué et véritable appareil physique : encore requise avant production.** Les scores documentés Nova/SINJIRA ne changent pas.

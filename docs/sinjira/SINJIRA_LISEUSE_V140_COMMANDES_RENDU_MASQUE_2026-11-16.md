# SINJIRA V140 — bloquer les changements d'affichage d'un livre masqué

**16 novembre 2026 — PR #1000 DRAFT, non fusionnée ni déployée.**

## Risque ciblé

La V137 bloque les changements de page lorsque le livre est masqué; la V138 refuse les sauvegardes de position déclenchées hors premier plan; la V139 arrête la narration lorsqu'un livre est masqué. Malgré cela, le bouton `#reader-mode` (PDF/texte adaptable) et la sélection `#reader-zoom` pouvaient toujours déclencher un nouveau rendu depuis un événement différé, même si `#reader-content.hidden` était vrai ou si un roman intégral était suspendu/révoqué.

## Modification

- Le gestionnaire du bouton de mode vérifie `canRecordReaderInteraction()` **avant** l'arrêt de narration, le changement de mode et `renderPage()`. Si le livre est masqué, la commande est ignorée.
- Le gestionnaire du zoom vérifie la même condition **avant** de modifier `state.zoom`, les préférences et le rendu. Si la commande est interdite, sa valeur HTML revient à la valeur canonique sans signal global de pagination.
- Aucune donnée d'œuvre privée n'est extraite, enregistrée ou copiée dans les tests; aucun changement d'autorisation Supabase ni de schéma.
- Le cache du script V26 et le contrat de test Node sont alignés sur `34.11.16.140`.

## Régression

Dans le test Playwright `tests/e2e/test_sinjira_liseuse_real_page_v57.py`, le vrai HTML avec PDF de laboratoire et Supabase isolé masque `#reader-content`, tente les contrôles numéro/curseur/chapter/boutons, puis clique PDF/texte et déclenche une valeur de zoom différente. Il doit retrouver exactement les mêmes indicateurs de page, de mode, de libellé accessible et de zoom après les commandes refusées. La suite vérifie ensuite que la pagination et les gestes restent utilisables une fois le livre réaffiché.

**Résultat de CI à confirmer sur le SHA final**; les tests de navigateur ne remplacent pas les essais iPhone/Android réels, les droits serveur et leur révocation, VoiceOver/TalkBack ou la synchronisation multiappareils. **NO-GO production; scores globaux inchangés.**

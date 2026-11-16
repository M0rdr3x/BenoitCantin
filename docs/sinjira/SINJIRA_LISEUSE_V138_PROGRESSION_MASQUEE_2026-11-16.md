# SINJIRA V138 — empêcher la sauvegarde fantôme après masquage du livre

**16 novembre 2026 — PR #1000 DRAFT, sans fusion ni déploiement.**

## Pourquoi corriger

La V137 empêche les commandes de changer de page pendant qu'un livre est masqué, mais les événements `scroll` et `sinjira:reader-screen-turn` du contrôleur V26 disposaient d'autres chemins vers `persist()`. Après un verrouillage ou une rotation, le navigateur peut encore transmettre des événements de scroll différés, parfois avec une hauteur de lecteur égale à zéro, ce qui risquerait d'écraser la dernière vraie position du roman (localement et, en édition privée, lors de la prochaine synchronisation).

## Changement précis

- Introduire `canRecordReaderInteraction()` : PDF prêt, document visible, contenu réellement affiché et, pour le livre intégral, session ni suspendue ni révoquée.
- Bloquer les écritures liées à un `sinjira:reader-screen-turn`, un `scroll` et son rappel différé (650 ms), ainsi qu'un clic sur « Enregistrer ma position » reçu après masquage.
- Annuler un rappel de scroll en attente lorsqu'un scroll est reçu après le masquage.
- Préserver volontairement le **flush sur pagehide/visibilitychange avant le masquage** : la dernière position légitime doit continuer d'être conservée. Ne pas ajouter de garde global à `persist()` qui supprimerait cette sauvegarde.
- Aucun contenu privé lu ou ajouté au dépôt. Aucun changement de Supabase Auth, RLS, stockage ou schéma.

## Validation demandée

Playwright Chromium/WebKit sur le vrai HTML avec PDF synthétique et réseau externe bloqué : attendre les écritures initiales, masquer la zone de lecture, déclencher un signal d'écran, un événement de défilement et un clic Enregistrer; attendre plus de 650 ms, puis confirmer que page, emplacement, horodatage et annonce de sauvegarde n'ont pas changé. Réafficher le roman et exécuter les tests existants de pagination, gestes et curseur.

Le résultat GitHub Actions doit être confirmé pour **le SHA exact**. Les tests artificiels de masquage ne prouvent pas les droits serveur du roman intégral; ils exigent une homologation sur compte autorisé/révoqué, iPhone/Android physiques et synchronisation réelle.

**NO-GO production : PR #1000 maintenue en brouillon. Les scores Nova/SINJIRA demeurent inchangés.**


## Régression découverte lors de la réception du premier commit V138

Le commit `6a852de` a échoué dans le parcours V69, sur Chromium **et** WebKit, au contrôle de présence du curseur de pagination après la simulation de masquage. Les 203 tests Node ont réussi. Le moteur V53 recevait toujours un `scroll` alors que le livre était masqué et appelait `sync()` avec une géométrie réduite à zéro, ce qui masquait son curseur. **Ce n'était pas un problème de sécurité Auth/RLS**, mais une régression d'interface révélée par le nouveau test.

**Réparation :** `onScroll` de V53 refuse les événements lorsque `canNavigate()` est faux, sans modifier la position ou l'affichage mémorisé. Les observateurs de masquage restent actifs pour invalider les anciens gestes. Les versions de cache du script **V53 53.11.16.138** et le contrat HTML/Node/fixture/Playwright sont alignés; le CSS, non modifié, conserve sa version précédente. Le test V57 existant vérifie aussi le curseur après réouverture. **La CI du commit réparé est obligatoire avant qualification.**

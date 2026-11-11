# SINJIRA™ — V61 : clavier et libellés accessibles en lecture mobile

**11 novembre 2026 — correctif candidat, non fusionné, non déployé.**

## Problème et intention

La version candidate V53 captait les flèches gauche/droite et les touches PageUp/PageDown au niveau de `document`. En mode mobile paginé, un lecteur pouvait donc déclencher un changement d'écran alors que son focus se trouvait **ailleurs que sur le livre**, par exemple sur le fond de la page. Cette interception globale gêne potentiellement la navigation clavier, les technologies d'assistance et la compréhension des contrôles.

Les boutons « Précédente » / « Suivante » servent par ailleurs à deux fonctions différentes selon le mode :
- **pages d'écran** : avancer/reculer d'une portion de texte, puis d'une page source une fois la fin atteinte;
- **PDF ou défilement libre** : changer directement de page source PDF.
Leurs anciens libellés `aria-label` permanents ne distinguaient pas ces comportements.

## Anomalie révélée par la vraie page et corrigée en V61

Le premier parcours V61 sur `compte/liseuse.html` a démontré un vrai défaut d'intégration : la V53 gérait correctement le focus, **mais le moteur historique `sinjira-liseuse-v26.js` captait également les flèches au niveau global du document**. Appuyer sur la flèche droite hors de la zone du roman changeait directement la page PDF source.

Le moteur V26 exige maintenant lui aussi le focus de `#reader-viewer`, respecte les entrées et la sélection de texte, ignore les événements déjà empêchés par V53, et **s'abstient totalement lorsque le mode `screens` est actif**. Il continue à permettre de tourner les pages dans le mode PDF lorsque le livre est au focus. La recette réelle teste le cas qui échouait, pour prévenir toute régression.

## Changement de code

- Les touches **ArrowLeft, ArrowRight, PageUp et PageDown** sont interceptées uniquement lorsque le focus est sur `#reader-viewer` ou dans un de ses descendants non interactifs.
- Lorsque le focus est hors de la zone de lecture, aucun événement de flèche n'est empêché par la V53.
- Les commandes principales et tactiles reçoivent des **libellés ARIA mis à jour uniquement lorsqu'ils changent** :
  - mode paginé : « Écran suivant, ou page du livre suivante à la fin » et équivalent précédent;
  - mode PDF/défilement libre : « Page du livre suivante » et « Page du livre précédente ».
- La véritable page HTML explique qu'il faut atteindre la zone du livre au clavier avec Tab, et lui associe `aria-keyshortcuts` pour les quatre touches.
- Le focus clavier du lecteur est rendu visible par une bordure de 3 px. Aucun style d'impression ou taille de police utilisateur n'est imposé.
- Aucun changement aux données du livre, à la synchronisation V51, à la sécurité V59, aux droits privés ou au stockage.

## Contrôles

- Quatre tests Node supplémentaires vérifient les flèches **hors du livre**, les libellés alternant entre écrans et pages sources, ainsi que le HTML/CSS accessibles.
- Le parcours Playwright de la **vraie page `compte/liseuse.html`**, avec livre synthétique, contrôle la zone au focus, le retour arrière, un champ de réglage au focus et les libellés de navigation après désactivation puis réactivation de la pagination.
- Les mêmes suites de navigation V52–V60 sont rejouées en **Chromium et WebKit**, sur cinq formats mobile/tablette, avec PDF.js fictif et appels Supabase bloqués.
- Les tests ne certifient pas VoiceOver/TalkBack, les raccourcis natifs des vrais appareils, ni le fonctionnement avec les romans intégrals privés.

## Ordre de réception

**Pile à examiner : V61 → [V60 #991](https://github.com/M0rdr3x/BenoitCantin/pull/991) → [V58 #983](https://github.com/M0rdr3x/BenoitCantin/pull/983) → `main`.** La PR est volontairement en brouillon. Ne pas publier avant une revue indépendante, des essais physiques et les autorisations distinctes du serveur de livres intégraux.

Le bilan documentaire de Projet Nova reste [consolidé dans `main`](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md). Les chiffres du 8 novembre 2026 ne changent pas du fait d'une nouvelle série de tests : **SINJIRA 66,5 % ±10 points**, **13/13 portes de lancement OPEN** et date de fin non certifiée.

# SINJIRA V122 — empêcher un vieux swipe PDF de tourner le texte

**15 novembre 2026 — PR #1000 en brouillon, pas de déploiement.**

## Défaut fonctionnel

La liseuse passe parfois du PDF au texte adaptable en conservant le même numéro de page, sans émettre l'événement canonique. Le module tactile V52 vérifiait déjà le mode du geste pour les tapotements de marge, mais pas pour les swipes complets. Un mouvement commencé sur le PDF pouvait donc être relâché sur le texte continu et tourner la mauvaise page, ou inversement.

## Correction

Au début du toucher, le module capture l'état de la représentation PDF/texte. Il compare cet état aux événements `touchmove` et `touchend` : si la représentation a changé, le geste est rejeté. La validation reste indépendante du numéro de page V117, du signal V118, du layout V78, du zoom V71 et de l'orientation V72. Les swipes suivants restent disponibles dans le nouveau mode, gauche pour avancer, droite pour revenir. Aucun stockage, texte privé, statut de compte ni permission n'est modifié.

## Recette

- Node : PDF → texte et texte → PDF pendant le contact n'entraînent pas de page supplémentaire, alors que les swipes suivants fonctionnent. Un changement PDF → texte → PDF observé à `touchmove` est également rejeté.
- Playwright sur la vraie liseuse isolée avec roman fictif, Chromium et WebKit : changement de représentation à numéro constant pendant un contact PDF, sans signal de changement, absence de page fantôme, puis retour à la pagination mobile.
- Cache JavaScript touch `52.11.15.122` synchronisé dans HTML, imports V53, fixtures et tests; V53 conserve `53.11.15.121`.

**NO-GO publication** : PR toujours DRAFT, non fusionnée dans `main`, non déployée. Restent les essais physiques iPhone et Android, VoiceOver/TalkBack, droits Auth/RLS, synchronisation interappareils et les 13 critères de lancement. Le correctif ne recalcule pas les pourcentages de maturité des programmes.

# SINJIRA™ — V89 : préserver la lecture entre les modes « continu » et « pages d’écran »

**14 novembre 2026 — PR #1000, candidat non fusionné, non publié.**

## Anomalie traitée

La liseuse possède une ancre éphémère (`lastAnchor`) et une restauration différée sur deux `requestAnimationFrame`. Lorsqu'un lecteur désactive les pages d'écran et fait défiler le roman librement, l'ancienne ancre du mode paginé peut rester en mémoire. Au retour en mode paginé, son utilisation peut ramener le lecteur à l'ancien passage. Si la personne désactive puis réactive rapidement le mode, une restauration du premier mode peut également gagner la course et écraser la nouvelle position.

## Correction V89

- Au changement de mode, capturer le **ratio courant** et, lorsque le caractère est réellement visible dans la fenêtre, une **ancre éphémère actuelle** plutôt que réutiliser aveuglément `lastAnchor`.
- Invalider tout réagencement en attente avant de planifier le nouveau, conformément aux priorités d'interaction V69/V85. Si l'API caret n'est pas disponible ou le texte n'est pas visible, revenir au ratio courant du défilement.
- Conserver les préférences existantes, le toucher, les commandes PDF, le zoom, le stockage limité à page/ratio et les droits du roman intégral inchangés.

## Vérifications

1. Tests Node : bascule rapide `pages → continu → lecture plus loin → pages` avant le terme des deux frames et bascule après restitution terminée. Le défilement courant doit être conservé.
2. Test E2E responsive sur `compte/liseuse.html` avec PDF fictif : partir de l'affichage paginé, revenir en mode continu, avancer au milieu du texte, mesurer un caractère visible, remettre le mode paginé et vérifier la position du même caractère (écart maximal 35 px).
3. GitHub Actions : exécuter les suites V64/V66/V67/V68/V69 en Chromium et WebKit; vérifier les contrôles de sécurité et le non-déploiement.

**Limite :** l'ancre de caractère ne peut être prélevée que si le texte est visible et si le navigateur fournit l'API caret adéquate. Le repli sur le ratio est intentionnel. Un test Chromium/WebKit automatisé ne remplace pas la réception iPhone/Android physiques et VoiceOver/TalkBack.

**Décision : NO-GO production** jusqu'à homologation des droits privés, de CAS V51/V59 et des 13 conditions SINJIRA. Les taux de référence du 8 novembre restent inchangés : Nova 47 %, Nova–Sinjira sans taux vérifiable, sondage 54,5 %, boussole 75 %, SINJIRA 66,5 % ±10 points.

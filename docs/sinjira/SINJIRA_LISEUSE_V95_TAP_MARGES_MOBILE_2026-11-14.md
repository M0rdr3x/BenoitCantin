# SINJIRA™ — V95 : tourner les écrans en touchant les marges de la liseuse

**14 novembre 2026 — PR #1000 (brouillon), non fusionnée et non déployée.**

## Objectif

Compléter le **balayage gauche/droite déjà disponible** sur téléphone et tablette par une navigation discrète à une main : **tapotement bref dans la marge droite = écran suivant**, **tapotement bref dans la marge gauche = écran précédent**. Les boutons tactiles et les raccourcis clavier restent également utilisables. Le passage entre deux pages PDF conserve le mécanisme de pagination V53 existant.

Cette nouvelle option **n'est active qu'en mode texte reformaté par écrans**, et non en mode PDF brut ni en mode défilement libre.

## Garde-fous de lecture

- Zone active : bande latérale intérieure d'environ 7 % à 26 % de la largeur du lecteur à gauche, et son symétrique à droite. Les 7 % extérieurs (au moins 28 px) sont exclus pour préserver les gestes système. Le calcul utilise la **position réelle du conteneur** (y compris page centrée/tablette), pas une coordonnée de fenêtre arbitraire.
- Seulement si la zone de lecture mesure **au moins 240 px**, pour éviter les pressions involontaires sur très petit écran.
- Un contact doit durer **au plus 300 ms** et se terminer à **12 px** maximum de son point de départ. Le déplacement maximal observé pendant `touchmove` est aussi limité à 12 px, même si le doigt revient exactement à sa position initiale.
- Refuser le tapotement si une sélection de texte est active, si un élément interactif est touché, en présence de pinch zoom, de défilement natif ou imbriqué, ou si le lecteur est redimensionné ou change de mode pendant le contact.
- L'écran central reste libre pour toucher/sélectionner le texte sans tourner de page. Les balayages existants conservent la priorité.
- Les zones sont **logiques** : pas de calque invisible sur le texte et pas d'éléments supplémentaires capturant la sélection ou l'accessibilité. Les boutons officiels demeurent accessibles.
- Conserver la sauvegarde de position automatique existante via `sinjira:reader-screen-turn`; aucun stockage de contenu privé, changement d'authentification ou modification de tables.

## Tests et réception

Dans `tests/sinjira-liseuse-reflow-v53.test.mjs` :
1. Classification du tapotement des deux côtés, exclusion du centre et des bords système.
2. Refus des appuis prolongés, d'un mouvement revenu au départ, des sélections, du zoom et du défilement.
3. Intégration de la navigation texte : l'écran avance et recule sans saut de page PDF.
4. Mode continu : tapotement désactivé.

Dans `tests/e2e/test_sinjira_liseuse_mobile_v54.py` : toucher les deux marges de la **vraie zone DOM de lecture** en mobile simulé, puis le centre ; vérifier le déplacement d'écran, l'absence de déplacement central et l'absence de changement de page source PDF. Chromium et WebKit doivent réussir.

Le fichier `compte/liseuse.html` annonce ces gestes aux lecteurs et référence le module V53 cache-busté en `v=53.11.14.95`; la fixture navigateur utilise la même révision.

## Limites et décision

Les touchers sont synthétiques en navigateur automatisé, pas une validation tactile sur iPhone Safari / Android Chrome physiques. Le lecteur ne reproduit pas une animation de coin de papier ni un moteur EPUB propriétaire; le texte est repaginé à partir du PDF et la pagination réelle est testée avec des documents de démonstration.

**NO-GO production** maintenu : PR brouillon, non fusionnée, contrôles sur appareils réels, droits privés, CAS/RLS, accessibilité VoiceOver/TalkBack et les 13 conditions de lancement toujours à homologuer.

**Scores de référence du 8 novembre inchangés** : Nova 47 %, Nova–Sinjira sans taux vérifiable, sondage 54,5 %, boussole électorale 75 %, SINJIRA complet 66,5 % ±10 points ; Nova 31 décembre 2027 cible conditionnelle uniquement, aucune date fiable de fin des autres projets.

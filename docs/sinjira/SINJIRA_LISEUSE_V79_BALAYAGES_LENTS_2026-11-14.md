# SINJIRA™ — V79 : glissements volontaires plus lents sur cellulaire

**14 novembre 2026** — [PR unique d'intégration de la liseuse #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), toujours **DRAFT, non fusionnée et non déployée**.

## Motivation : accessibilité de la lecture tactile

Dans le lecteur V52/V53, les gestes d'une durée supérieure à **850 ms** étaient automatiquement rejetés. Une personne qui déplace volontairement son doigt plus lentement (fatigue, difficultés motrices, grand téléphone) pouvait ne pas réussir à avancer/reculer sans utiliser les boutons.

## Règle V79, commune PDF et texte paginé

- Les gestes de **0 à 850 ms** conservent les seuils existants : au moins 56–100 pixels CSS selon la largeur, et une direction horizontale dominante (facteur 1,65).
- Les gestes de **plus de 850 ms à 1 800 ms** sont désormais recevables seulement si le déplacement latéral atteint au moins **112 pixels CSS ou 1,5× le seuil courant**, et dépasse **2,2× le déplacement vertical**. Cette règle s'applique dans les deux directions : gauche = suivante; droite = précédente.
- Les gestes au-delà de 1 800 ms et les glissements courts/diagonaux sont refusés; la protection des sélections de texte, du zoom natif, du scroll horizontal/vertical imbriqué, des gestes système, de la rotation et des changements de mode reste active.
- Les boutons Précédente/Suivante, la navigation clavier, la position sauvegardée, les contrôles de droits et Supabase ne sont pas modifiés.

## Régression automatique

Quatre tests supplémentaires : deux sur le classificateur (lenteur acceptée et gestes involontaires refusés), un sur les boutons PDF avec deux glissements lents et un sur le texte paginé avec aller-retour. Contrôler les workflows Chromium/WebKit **sur le SHA V79 exact**, sans réutiliser les preuves du commit V78.

## Réception physique obligatoire

Sur iPhone Safari et Android Chrome, essayer 1,2 s et 1,6 s gauche/droite en mode texte et PDF, puis une pression prolongée, une diagonale, un déplacement vertical, une sélection, le zoom, les bords système et les contrôles de navigation. Vérifier VoiceOver et TalkBack, les progrès enregistrés, les droits aux romans intégraux et la restauration interappareils avant fusion et publication.

**Statut : DRAFT / NO-GO.** Le programme global SINJIRA reste à **66,5 % ±10 points** estimés et les 13 conditions de lancement restent ouvertes. Pas de date finale certifiable.

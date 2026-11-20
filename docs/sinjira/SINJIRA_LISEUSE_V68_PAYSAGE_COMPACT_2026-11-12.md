# SINJIRA — V68 : vraie zone de lecture adaptée au téléphone en paysage

**12 novembre 2026. Changement candidat, non fusionné dans `main`, non déployé.**

## Défaut de mise en page

Les règles héritées de la liseuse imposaient des hauteurs minimales de **340 à 410 pixels CSS** en mode mobile. Sur un téléphone tourné à l'horizontale, le viewport peut être beaucoup moins haut (par exemple 568×320). Le livre prenait alors plus de hauteur que l'espace visible, indépendamment du mode lecture par écrans. L'utilisateur devait déplacer la page entière pour retrouver la lecture, alors qu'une liseuse doit privilégier une fenêtre lisible.

## Correction

Un groupe CSS **limité aux écrans de largeur au plus 980 px, hauteur au plus 480 px et orientation paysage** donne à la zone du livre une hauteur bornée `clamp(176px, calc(100dvh - 120px), 360px)` et un minimum de 176 px, au lieu des 340–410 px hérités. Les paddings passent à 8/10 px; les textes sont espacés de 12/16 px dans le mode « pages d'écran ». Les commandes tactiles **restent de 48 px minimum** avec la barre fixe et les zones de sécurité, et les dimensions portrait sont inchangées.

Ce changement ne modifie **aucun moteur JavaScript**, ni les gestes gauche/droite V52–V67, ni les positions enregistrées, ni les comptes ou autorisations. Il permet à l'algorithme de pagination existant de recalculer le nombre de portions selon la hauteur effectivement disponible.

## Réception navigateur

Extension de `tests/e2e/test_sinjira_liseuse_responsive_v58.py` sur la vraie page :
- À **844×390 px**, la hauteur du livre doit être entre 175 et 300 px et laisser au moins 100 px au reste de l'écran.
- À **568×320 px**, la hauteur du livre doit être entre 175 et 240 px et les deux boutons tactiles doivent mesurer au moins **44 px**.
- Les contrôles de reflow, même caractère après rotation, police à 34 px, largeur, pages PDF, focus, tailles portrait/tablettes et gestes tactiles sont rejoués en **Chromium et WebKit**.
- Le scénario utilise uniquement un PDF synthétique avec comptes Supabase bloqués. Ce n'est **pas** une preuve de réception physique Safari iPhone ou Chrome Android.

**Conditions avant GO :** réussite de la CI sur le SHA final; examen des appareils physiques, des barres de navigateur dynamiques, du clavier virtuel, VoiceOver/TalkBack et de la sélection; contrôle des droits serveur sur les vrais livres privés et des marque-pages synchronisés. La [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) reste DRAFT, et la [PR sécurité #986](https://github.com/M0rdr3x/BenoitCantin/pull/986) distincte.

Ce correctif ne change pas l'audit de SINJIRA **66,5 % ±10 points**, 13/13 portes de lancement ouvertes, ni les autres taux de référence du **8 novembre 2026**.
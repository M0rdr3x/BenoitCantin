# SINJIRA — V102 : repère de progression visible sur téléphone

**14 novembre 2026 · PR #1000 ouverte en brouillon · aucun déploiement.**

## Objectif de lecture

Dans les versions V97–V101, le doigt permet de passer d'un écran de texte à l'autre, de toucher les marges pour changer de page et d'utiliser le PDF comme un véritable livre. Cependant, sur les téléphones très étroits (320 à 400 px), la barre inférieure fixe **masquait le texte d'aide**, et donc aucun repère de l'écran courant n'était visible à proximité des commandes de lecture.

La V102 introduit un **compteur compact de progression** dans cette barre tactile :
- **Pages d'écran :** `Écr. 2/8 · p. 3 / 20` (deuxième écran de texte de la troisième page source).
- **PDF :** `PDF · p. 3 / 20` (pagination du document original).
- **Texte continu :** `Continu · p. 3 / 20` (sans inventer des sous-écrans).

Le repère indique seulement des **nombres d'emplacement**, jamais du contenu de roman ou l'identité du compte. Il utilise le statut `aria-live` existant pour les lecteurs d'écran; le duplicata de la barre visuelle a `aria-hidden=true`, afin d'éviter les annonces répétées.

## Changements techniques

1. `assets/js/sinjira-liseuse-reflow-v53.mjs` : fonction pure `formatReaderMobileLocation` et mise à jour du libellé lors du glissement, du changement de mode, de l'affichage PDF et de la modification de page.
2. `assets/js/sinjira-liseuse-v26.js` : événement DOM `sinjira:reader-page-change` émis **après** la mise à jour des champs canonique `reader-page` et `reader-total`; ne modifie aucune sauvegarde.
3. `compte/liseuse.html` : repère `#reader-touch-location`; aide et versions cache V26 `34.11.14.102`, V53 `53.11.14.102`, CSS `53.11.14.102`. Le module tactile V52 reste à `52.11.14.101`, sans double chargement.
4. `assets/css/sinjira-liseuse-v26.css` : à 320–400 px, deux boutons restent côte à côte sur la première ligne de la barre; l'emplacement apparaît sur la deuxième ligne. Boutons au moins 48 px, zones sûres respectées et espace réservé au bas du document.
5. Fixtures et tests synchronisés sur la version V102, sans touche aux systèmes d'authentification ni aux politiques RLS.

## Conditions de réception

- Unitaires : chaque mode donne un libellé français correct; valeurs hors bornes gérées; l'emplacement évolue lors du glissement et du retour PDF/texte.
- Intégration sur la **vraie page SINJIRA** avec livre fictif et services privés bloqués dans Chromium et WebKit : l'écran avance de 1 à 2, le PDF affiche la bonne page après changement, et à **320 px** le libellé reste visible avec les deux boutons tactiles de 48 px et sans débordement horizontal.
- La publication est interdite tant que les workflows applicables ne sont pas validés sur le SHA exact, et tant que les 13 conditions de lancement SINJIRA ne sont pas closes.

**NO-GO production** : les essais sur appareils iPhone/Android physiques, VoiceOver/TalkBack ainsi que la validation authentifiée des droits, RLS/CAS et synchronisation entre appareils restent à effectuer.

## Avancement de référence inchangé (8 novembre 2026)

Projet Nova programme : **47 %**, date cible **31 décembre 2027 conditionnelle**, report possible en 2028 ou après. Nova–Sinjira : **aucun pourcentage vérifiable**, 14 secteurs inventoriés. Sondage citoyen : **54,5 %** (6/11 portes). Boussole électorale : **75 %** (9/12). SINJIRA complet : **66,5 % ±10 points**, 13 conditions de lancement ouvertes. Aucun score global n'augmente automatiquement du seul fait de ce repère mobile.

# SINJIRA™ — Liseuse tactile V52 : glisser pour tourner les pages
**Dossier de livraison candidate, 10 novembre 2026. Revue et tests sur téléphone réel obligatoires.**

## Objectif utilisateur

Sur la liseuse [`/compte/liseuse.html?edition=demo`](/compte/liseuse.html?edition=demo), un glissement horizontal **vers la gauche** doit ouvrir la **page suivante** et un glissement **vers la droite** revenir à la **page précédente**. L'expérience est conçue pour le **téléphone** et la **tablette** avec la même mécanique, en édition démo et en édition intégrale autorisée.

La navigation reste compatible avec les commandes précédentes/suivantes existantes, les flèches du clavier, la lecture vocale, le plein écran, le texte adaptable, les thèmes sépia/clair/nuit, les préférences typographiques et les repères de lecture. Une barre inférieure à grands boutons (48 px minimum) s'affiche sur les écrans étroits, en tenant compte de la zone de sécurité iOS.

## Principe d'intégration

- `assets/js/sinjira-liseuse-touch-v52.mjs` est un module **distinct**. Il ne modifie pas `assets/js/sinjira-liseuse-v26.js`, qui est simultanément en revue pour le correctif CAS V51 dans [PR #947](https://github.com/M0rdr3x/BenoitCantin/pull/947).
- Un geste valide actionne **le bouton de navigation existant**, afin de réutiliser les contrôles natifs : limites de la page, rendu du PDF, enregistrement local, reprise, arrêt de narration et contrôles des droits. Pas d'accès direct à Supabase, de requête réseau supplémentaire, de copie du PDF ni de nouveau stockage de contenu.
- Les écouteurs tactiles sont **passifs**. Le défilement vertical, le pincement/zoom, la sélection, les gestes multi-doigts, l'interaction avec les boutons et le défilement horizontal d'une page PDF agrandie ne doivent pas être interprétés comme des changements de page.
- **Renforcement du 14 novembre** : un défilement du conteneur (vertical ou horizontal) annule le geste, tout comme une trajectoire d'abord franchement verticale, même si le doigt revient finalement à hauteur de départ. Trois scénarios unitaires protègent ce comportement sans désactiver le scroll natif.
- Le contrôle de distance impose `max(56px, min(100px, largeur * 0.14))`, un déplacement horizontal dominant (rapport 1,65) et une durée maximale de 850 ms. Un geste est pris en compte à la levée du doigt, pas pendant le défilement.
- Les commandes accessibles déjà présentes conservent leur rôle. La nouvelle aide gestuelle est référencée par `aria-describedby` et les deux boutons tactiles portent un nom accessible.
- Le chargement du nouveau module et le CSS possèdent des **versions d'URL explicites** pour réduire les conflits de cache lors de la mise à jour. Le module de lecture intégrale n'a pas été changé.

## Ce que la V52 ne prétend pas faire

Cette modification **tourne les pages du document PDF** dans la liseuse existante, aussi bien en mode texte adaptable qu'en mode PDF. Elle **n'introduit pas** encore de moteur de *repagination automatique de chapitres*, comme un EPUB reflow complet selon la taille de l'écran. Un tel chantier distinct exigerait une définition des unités de position, des ancres, de l'accessibilité, de l'édition et de la compatibilité des marque-pages déjà enregistrés.

La V52 ne certifie **pas** la synchronisation entre plusieurs appareils : [PR #947 (CAS V51)](https://github.com/M0rdr3x/BenoitCantin/pull/947) reste en DRAFT, et le contrôle des droits du roman [issue #955](https://github.com/M0rdr3x/BenoitCantin/issues/955) reste ouvert. Elle ne doit pas entraîner la fusion ou le déploiement d'une migration Supabase.

## Contrôles automatisés avant revue

Le fichier `tests/sinjira-liseuse-touch-v52.test.mjs` contient des tests Node pour :
- gestes gauche/droite, seuil relatif à la largeur, gestes trop courts/lents/diagonaux/verticaux et entrées impossibles;
- pincement, annulation, sélection de texte, contrôle interactif et pages indisponibles;
- scroll horizontal quand le PDF est plus large que l'écran;
- boutons mobiles visibles, leur état désactivé, détachement des écouteurs;
- présence des descriptions et des versions dans le HTML/CSS, et absence d'accès aux services privés dans le module.

Workflow dédié : `.github/workflows/sinjira-liseuse-touch-v52.yml` avec `contents: read`, aucun secret ni déploiement.

## Réception manuelle : à effectuer sur appareils réels (non faite par cette PR)

| Cas à vérifier | Critère |
| --- | --- |
| iPhone Safari actuel, iPhone petit écran, Android Chrome | Geste gauche/droite change d'une page exacte; les contrôles sont accessibles du pouce |
| iPad Safari, tablette Android | Geste fonctionne sans empêcher la lecture en mode paysage/portrait |
| Démo PDF de 82 pages, première et dernière pages | Aucun dépassement; boutons correctement désactivés |
| Mode texte et PDF, zoom 80 % à 150 % | Le défilement vertical reste libre; le PDF agrandi garde le pan horizontal |
| Sélection, surlignage et annotations | Appui long et sélection ne changent pas la page |
| Lecture vocale en cours, changement de page | La voix s'arrête proprement via les commandes existantes |
| VoiceOver, TalkBack, clavier matériel, focus | Navigation décrite, boutons énoncés, activation et annonce des changements compréhensibles |
| Mode concentration, tailles 16–34 px, thèmes nuit et sépia | Pas de contenu caché par la barre inférieure, texte lisible et stable |
| Rotation, entrée/sortie plein écran, cache PWA | Aucun code obsolète ni régression; événement tactile attaché une seule fois |
| Compte autorisé, déconnexion, réouverture, deux appareils | Droits inchangés; pas de synchronisation V51 déclarée opérationnelle sans acceptation séparée |

**Décision de livraison :** PR candidate pour revue; expérience tactile **non encore attestée sur appareils physiques**. Ne pas annoncer une hausse de **66,5 % ±10 points** ou un GO de SINJIRA™ sur la seule base du code et des tests. Le registre global maintient **13/13 portes de lancement ouvertes**.

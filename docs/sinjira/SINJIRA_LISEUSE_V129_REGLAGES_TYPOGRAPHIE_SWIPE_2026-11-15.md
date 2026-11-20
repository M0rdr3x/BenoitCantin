# SINJIRA V129 — éviter la page fantôme pendant un réglage typographique

**15 novembre 2026.** Correctif candidat PR #1000, non fusionné et non déployé.

## Problème

Le texte adaptable de la liseuse peut modifier la police, la taille, l'interligne, l'espacement des lettres et la largeur de colonne. Un lecteur ayant posé le doigt sur l'ancien affichage pourrait voir ces réglages changer, puis revenir aux valeurs d'origine **avant** `touchend`, de sorte que le même numéro de page, le même mode et la même géométrie finale donnent l'impression d'un geste valide. Ce contact périmé risque de tourner une portion d'écran ou une page PDF.

## Correctif

- V53 : en phase capture des `input` et `change` pour les cinq réglages de lecture, invalider le contact `gesture` immédiatement. Préserver `scheduleLayoutRestore(lastRatio, anchor)` et l'ancre de caractère V63 pour garder l'emplacement lu après le réagencement.
- V52 : observer ces mêmes cinq identifiants de réglages en capture et annuler le geste tactile ou souris PDF en cours. Les contrôles étrangers au livre ne bloquent pas la lecture. Déconnecter les écouteurs au démontage.
- Événements contrôlés : `reader-size`, `reader-font`, `reader-line-height`, `reader-letter-spacing`, `reader-text-width`. Aucun nouveau stockage de texte, identifiant privé, progression, droit ou appel réseau.
- Cache V52 `52.11.15.129` et V53 `53.11.15.129` synchronisé dans HTML, fixture, import V53 et tests.

## Recette

- Node V52 : tous les cinq changements durant le contact PDF, drag souris, contrôle externe ignoré, nouveaux swipes gauche/droite et déconnexion.
- Node V53 : même matrice, aucune portion d'écran tournée par un ancien toucher, nouveau geste gauche/droite, et régression des restaurations de l'ancre de lecture V56/V63.
- Playwright V58 Chromium/WebKit : vraie liseuse HTML isolée, taille de police 20→24→20 entre `touchstart` et `touchend`, sans modification de page ni de position. Les autres scénarios mobiles/paysage restent dans les suites existantes.

**Publication NO-GO :** PR #1000 toujours DRAFT et non fusionnée dans `main`, non déployée. Restent les essais sur iPhone/Android physiques, VoiceOver/TalkBack, sécurité Auth/RLS des romans privés, synchronisation entre appareils et homologation humaine des 13 conditions de lancement. Aucun recalcul des pourcentages Nova/SINJIRA.

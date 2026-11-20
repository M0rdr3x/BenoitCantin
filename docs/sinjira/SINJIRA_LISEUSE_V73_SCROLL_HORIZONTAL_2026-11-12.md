# SINJIRA™ — V73 : réserver le glissement aux passages défilants du roman

**12 novembre 2026** — Amélioration dans la [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), candidate et non publiée.

## Intention de lecture

Le lecteur SINJIRA tourne un écran ou une page lorsqu'on **glisse de droite à gauche**; **de gauche à droite**, il revient. Le lecteur de texte recompose les paragraphes pour le téléphone. Cependant, un encadré, un tableau ou une annotation dont le contenu déborde horizontalement peut recevoir son propre geste de défilement. Le moteur ne doit alors **pas voler ce geste** au profit d'une page suivante du roman.

## Correctif V73

- Au début du contact, inspecter uniquement les ancêtres depuis la cible tactile jusqu'au conteneur du livre.
- Si un sous-conteneur possède `scrollWidth > clientWidth + 4`, réserver le glissement horizontal à ce conteneur, même si la liseuse entière ne déborde pas.
- Appliquer la même règle aux modes PDF (V52) et pages de texte reflow (V53), sans modifier la sauvegarde de progression ni l'authentification.
- Ne pas désactiver les boutons tactiles Suivante et Précédente; conserver les garde-fous sur la sélection de texte, le pincement/zoom, la rotation et les bordures système.

## Tests de régression

Quatre tests Node supplémentaires vérifient : détection sur des ancêtres appartenant au lecteur, tolérance de quatre pixels, conservation de la page PDF sur un panneau défilant, absence de `preventDefault` en mode texte et maintien du geste normal hors de ce panneau.

Commande CI : `node --test tests/sinjira-liseuse-touch-v52.test.mjs tests/sinjira-liseuse-reflow-v53.test.mjs`. Les parcours Chromium et WebKit avec PDF fictif et les workflows V64–V69 doivent également réussir **sur le dernier SHA**.

## Recette obligatoire avant publication

Sur iPhone Safari et Android Chrome réels : lire normalement, glisser gauche/droite, ouvrir une démo contenant un élément interne horizontalement défilant, glisser à l'intérieur puis à l'extérieur de cet élément, utiliser les deux boutons tactiles, tester le zoom et la rotation. Confirmer les permissions serveur pour un vrai livre privé autorisé, la sauvegarde sur deux appareils, le clavier et les lecteurs d'écran.

**Statut : DRAFT / NO-GO de production.** Ne pas confondre couverture CI et homologation physique. Les pourcentages Nova/Nova–Sinjira/SINJIRA ne changent pas par ce seul correctif.

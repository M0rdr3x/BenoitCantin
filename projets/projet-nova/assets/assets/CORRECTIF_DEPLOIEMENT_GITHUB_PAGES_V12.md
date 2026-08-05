# Correctif final AAA++ — Projet Nova v12

## Corrections visuelles

- Image 2 réduite fortement et centrée sous l’en-tête.
- Bandeau `Statut public` conservé, mais rendu plus discret.
- CSS cache-busting : `v=12-final-deploy`.
- Structure statique conservée pour GitHub Pages.

## Correctif GitHub Pages

Un workflow propre a été ajouté :

```text
.github/workflows/pages.yml
```

Ce workflow publie directement le site statique avec :

- `actions/configure-pages@v5`
- `actions/upload-pages-artifact@v3`
- `actions/deploy-pages@v4`

## Pourquoi l’ancien déploiement échouait

Le build passait, mais l’étape `deploy` échouait côté GitHub Pages avec :

```text
Deployment failed, try again later.
```

Ce type d’erreur indique généralement un problème de publication GitHub Pages, pas une erreur HTML/CSS. L’ancien artifact affiché dans GitHub était aussi expiré, donc il faut déclencher un nouveau déploiement.

## Étapes après intégration

1. Déposer tous les fichiers du dossier `projetnova-main` à la racine du dépôt GitHub.
2. Aller dans `Settings > Pages`.
3. Régler la source sur `GitHub Actions`.
4. Aller dans `Actions`.
5. Lancer `Deploy Projet Nova to GitHub Pages` ou pousser un nouveau commit sur `main`.
6. Si un ancien workflow `pages-build-deployment` échoue encore, ignorer l’ancien et vérifier le nouveau workflow `Deploy Projet Nova to GitHub Pages`.

## Vérifications finales

- Accueil desktop.
- Accueil mobile.
- Boutons et navigation.
- Image 2 sous l’en-tête.
- Page `documents.html`.
- Page `avis-legal.html`.
- Page `confidentialite.html`.
- Page `transparence.html`.

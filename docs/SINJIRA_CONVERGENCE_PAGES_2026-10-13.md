# SINJIRA — intégration des catalogues et de la sécurité Pages

13 octobre 2026 — Préparation non publiée.

- Main de départ : 790b1424b20e98ef31ec6597e98c5c8f6b4aa23d
- Sécurité Pages PR #458 : 7cdd33e05615ddf68b05b190dd0b079778de67f0
- Catalogues officiels PR #637 : 81971a0c66ac419bc7c533ec0ab29c6f52c2b919

Les 12 fichiers de la PR #637 sont repris depuis leurs blobs Git exacts dans
l'arbre de la PR #458, sans régénérer les trois visuels binaires et sans
modifier les romans ni les droits privés.

## Contrat de publication

Le manifeste approuve 614 fichiers historiques et 4 ressources supplémentaires :
`projets/sinjira/logiciels/index.html` et les trois bannières de Romans,
Jeux et Logiciels. Total : **618 sources**, **31 fichiers Jekyll générés**,
soit **649 fichiers statiques**. Lors d'une publication contrôlée, le seul
reçu dynamique SHA/run porte le total à **650**.

Le garde de sécurité impose désormais la présence des quatre ressources.
Les audits de navigation couvrent les trois portails et leurs images,
et les tests CDN comparent **18 ressources critiques** aux blobs Git du
SHA de publication. Cette preuve couvre désormais aussi l'accueil SINJIRA,
les pages Romans et Jeux, la feuille de style, la bibliothèque et le
sitemap. Des autotests refusent explicitement les anciennes versions
de chacune de ces pages et ressources.

## Conditions bloquantes

CI du SHA combiné réussie ; réglage Pages = GitHub Actions confirmé par
l'administrateur ; absence de publication racine concurrente ; DRY_RUN
sans upload ; approbation humaine du PUBLISH sur le main exact ; contrôle
HTTPS, 404/410 privés, reçu SHA/run et intégrité des ressources.
Cette branche ne déclenche aucune publication.

## Surveillance quotidienne compatible avec la bascule

Le workflow `publication-boundary-watch.yml` est maintenu en lecture
seule. Son exigence historique `Netlify` devient une alternative
fermée : Netlify avec sa signature d'origine **ou** GitHub Pages avec
le reçu `.well-known/sinjira-pages-release.json` au SHA exact de
`main` exécutant la surveillance. Un simple en-tête `Server:
GitHub.com` ne suffit jamais à faire passer le contrôle.

Les 13 routes privées de l'audit Pages et l'ancien chemin de build
Netlify (14 chemins techniques uniques au total) doivent répondre
en HTTP 404/410, sans redirection trompeuse. Les autotests refusent
les statuts 200, 301, 302, 403, 500, la disparition de preuve,
l'en-tête de fournisseur ambigu, le reçu obsolète, falsifié ou hors MIME.
Le contenu des routes techniques n'est jamais lu par le surveillant.

La surveillance GitHub Pages n'est réputée conforme qu'après la
bascule administrative, la fusion autorisée et un PUBLISH réussi.
Tant que le site sert la racine technique, le monitoring doit
continuer à signaler le risque et ne doit pas être neutralisé.

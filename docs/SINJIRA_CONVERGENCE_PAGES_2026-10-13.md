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
et les tests CDN comparent les octets des trois images et de la page
Logiciels à ceux des blobs Git du SHA de publication.

## Conditions bloquantes

CI du SHA combiné réussie ; réglage Pages = GitHub Actions confirmé par
l'administrateur ; absence de publication racine concurrente ; DRY_RUN
sans upload ; approbation humaine du PUBLISH sur le main exact ; contrôle
HTTPS, 404/410 privés, reçu SHA/run et intégrité des ressources.
Cette branche ne déclenche aucune publication.

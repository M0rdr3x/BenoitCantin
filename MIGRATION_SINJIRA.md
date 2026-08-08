# Migration majeure vers SINJIRA

## Nom officiel
La franchise narrative porte maintenant le nom **SINJIRA**.

## Hiérarchie
- SINJIRA - franchise
- SINJIRA - La Cendre du Jugement - roman
- SINJIRA - Fracture du Réseau-Mère - jeu
- SINJIRA - Réseau-Mère : Résistance - jeu
- Registre des Consciences - programme participatif de SINJIRA

## Identité visuelle
- `assets/media/sinjira-emblem.webp` : emblème principal sans texte.
- `assets/media/sinjira-banner.webp` : bannière sans l’ancien titre, conçue pour recevoir le mot SINJIRA en HTML.
- `assets/icons/sinjira.svg` : pictogramme vectoriel léger pour navigation et interfaces.

## Compatibilité
Les anciennes pages sous `projets/ere-des-consciences/` sont remplacées par des redirections vers SINJIRA. Ne les supprimez pas immédiatement : elles protègent les anciens favoris et liens externes.

## Démo de La Cendre du Jugement
Le fichier PDF de démonstration était déjà présent dans le dépôt GitHub mais n’était pas disponible dans l’archive locale utilisée pour cette migration. Les nouvelles pages continuent donc temporairement de pointer vers son URL existante sous l’ancien dossier. Après validation, copiez le fichier :
`projets/ere-des-consciences/documents/La_Cendre_du_Jugement_DEMO.pdf`
vers :
`projets/sinjira/documents/La_Cendre_du_Jugement_DEMO.pdf`
puis remplacez l’URL absolue dans `projets/sinjira/romans/index.html` et `projets/sinjira/romans/lire-demo.html`.

## Fichiers anciens pouvant être supprimés après validation
- `assets/media/ere-banner.webp`
- `assets/media/ere-icon.webp`
- `assets/icons/ere-consciences.svg`
Les redirections HTML sous `projets/ere-des-consciences/` doivent toutefois être conservées.

# Propositions citoyennes publiques — mode d’emploi

Cette page permet aux visiteurs d’envoyer une proposition publique au Projet Nova.

## Fonctionnement

1. Le visiteur remplit le formulaire sur `propositions.html`.
2. Le message est envoyé à Formspree et au courriel officiel du Projet Nova.
3. Le message n’est pas publié automatiquement.
4. Après validation, une version publique peut être ajoutée dans `data/propositions-publiques.json`.
5. Le site est retéléversé sur GitHub.

## Pourquoi une validation avant publication

La validation protège le site contre :

- les insultes;
- les messages haineux;
- les accusations personnelles non vérifiées;
- les renseignements personnels publiés par erreur;
- les messages automatisés ou inutilisables.

## Exemple d’entrée JSON

```json
{
  "date": "2026-06-21",
  "nom": "Citoyen de Québec",
  "region": "Québec",
  "categorie": "Administration et bureaucratie",
  "titre": "Réduire les délais de réponse",
  "message": "Les délais administratifs devraient être publiés et suivis publiquement.",
  "statut": "À analyser"
}
```

Ne jamais publier le courriel du citoyen.

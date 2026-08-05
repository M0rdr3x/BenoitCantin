# Guide de tenue des registres — Projet Nova

## 1. Comptabilité publique

Le fichier à mettre à jour est `data/comptabilite.json`. Chaque entrée devrait contenir :

```json
{
  "date": "2026-07-05",
  "type": "depense",
  "categorie": "Site web",
  "description": "Description courte et factuelle",
  "fournisseur_ou_source": "Nom public ou source",
  "montant": 0.00,
  "statut": "À vérifier"
}
```

Règles : ne pas publier de coordonnées personnelles, ne pas publier de pièces contenant des renseignements personnels, et ne pas présenter une dépense comme officielle si elle n’a pas été validée.

## 2. Registre des rencontres

Le fichier à mettre à jour est `data/rencontres.json`. Chaque entrée devrait contenir :

```json
{
  "date": "2026-07-05",
  "type": "consultation",
  "sujet": "Sujet public",
  "participants_resume": "Citoyens anonymisés",
  "resume_public": "Résumé sans renseignement personnel",
  "suivi": "Action à faire",
  "statut_publication": "Public anonymisé"
}
```

Règles : obtenir un consentement clair avant de nommer une personne, anonymiser les citoyens par défaut, et conserver les listes nominatives à l’interne seulement si nécessaire.

## 3. Avant publication

- Vérifier la clarté du texte.
- Vérifier l’absence de renseignements personnels.
- Vérifier que le contenu ne ressemble pas à une sollicitation financière non autorisée.
- Vérifier que le document porte l’avis préparatoire et indicatif lorsque nécessaire.
- Archiver l’ancienne version.

# Architecture — Compte SINJIRA universel

```text
Compte SINJIRA
├── Mon espace
├── Bibliothèque
│   ├── Fracture du Réseau-Mère
│   ├── Réseau-Mère : Résistance
│   └── futurs jeux
├── Documents approuvés
├── Mes parties
├── Playtests
├── Profil
├── Contributions
└── Paramètres
```

## Niveaux de documents

- `public` : public si le projet est public.
- `account` : tout Compte SINJIRA connecté.
- `player` : joueur explicitement approuvé pour le projet.
- `tester` : testeur explicitement approuvé pour le projet.
- `admin` : administration seulement.

Le statut **Contributeur** est séparé de ces niveaux. Il correspond à un consentement volontaire de partage de données de gameplay.

## Documents privés

Les documents non publics ne doivent pas être placés dans GitHub Pages.

Ils sont téléversés dans le bucket privé :

`sinjira-private-documents`

Quand un joueur ouvre un document, `get-document-url` :
1. vérifie que le document est approuvé;
2. vérifie le projet;
3. vérifie le niveau d'accès du compte;
4. génère un lien signé temporaire de 10 minutes.

## Playtests

Un compte peut poser sa candidature.
L'administration approuve ou refuse.
Une approbation peut automatiquement donner le niveau `tester` sur le projet.

## Futures extensions

Les commentaires de joueurs utilisés dans la section Extensions proviennent uniquement des contributions volontaires.
Les courriels, pseudos, codes de partie et notes privées ne sont pas inclus dans l'analyse de gameplay.

# Architecture — Compte SINJIRA universel

> Référence normative : [`CAHIER_MAITRE_SINJIRA.md`](CAHIER_MAITRE_SINJIRA.md). En cas de conflit, le Cahier maître prévaut.

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
├── Ma sécurité
│   ├── Mes appareils
│   ├── Connexions récentes
│   ├── Mode Voyage
│   ├── Passkeys et authentification
│   ├── Téléphone perdu
│   ├── Compte compromis
│   └── Récupération du compte
└── Paramètres
```

## Principe de sécurité du Compte

Le Compte universel respecte le principe **protéger sans surveiller** : les données techniques utilisées pour la sécurité sont minimisées et ne sont pas réutilisées à des fins publicitaires, commerciales, sociales, de Rencontres, d’Emploi ou de profilage sans consentement distinct.

La localisation seule ne suffit pas à conclure qu’une connexion est frauduleuse. Le Bouclier de connexion doit combiner plusieurs signaux, avec une réponse graduée et une authentification renforcée lorsque le risque l’exige.

Le **Registre des Consciences**, les conversations privées avec l’IA personnelle et les moyens de récupération du compte appartiennent au niveau **extrêmement sensible** et peuvent exiger une nouvelle authentification même lorsqu’une session est déjà ouverte.

## Mode Voyage

Le Compte doit prévoir un Mode Voyage accessible depuis **Ma sécurité**. L’utilisateur peut indiquer une destination ou région approximative et une période, sans fournir d’hôtel, de trajet quotidien, de numéro de vol ou de GPS permanent.

Les données spécifiques au voyage doivent avoir une durée de conservation courte et servir exclusivement à la sécurité.

## Appareils de confiance

L’utilisateur doit pouvoir reconnaître et révoquer ses appareils de confiance, déconnecter un appareil ou déconnecter toutes les autres sessions. L’application mobile peut devenir l’appareil principal de confiance pour autoriser ou refuser certaines nouvelles connexions.

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

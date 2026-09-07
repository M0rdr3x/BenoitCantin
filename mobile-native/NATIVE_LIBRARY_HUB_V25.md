# Hub Bibliothèque natif V25

## Principe

**L’HUMAIN AVANT TOUT. Protéger sans surveiller.**

`NativeLibraryHub` est un sas de navigation uniquement. Il ne devient jamais une source de vérité pour la bibliothèque du compte.

## Données volontairement absentes du natif

Le hub ne reçoit, ne lit, ne calcule et ne stocke aucun :

- rôle propriétaire ou administrateur;
- droit d’accès à un projet;
- licence ou droit numérique;
- progression de lecture, page courante ou dernière ouverture;
- inventaire de documents privés;
- demande testeur ou son statut;
- compteur de projets, lectures, droits ou demandes;
- identifiant technique de projet, produit, document, licence ou utilisateur.

## Mutations interdites

Le hub ne peut pas :

- demander un accès testeur;
- attribuer, retirer ou modifier un droit;
- créer ou révoquer une licence;
- modifier une progression de lecture;
- télécharger ou mettre en cache un inventaire privé;
- classer l’utilisateur selon ses lectures ou ses accès.

Toutes ces opérations restent dans les surfaces Web/serveur authentifiées existantes.

## Navigation autorisée

Le hub peut seulement ouvrir explicitement :

- `/compte/bibliotheque.html?surface=web`;
- `/compte/mes-lectures.html?surface=web`;
- `/compte/licences.html?surface=web`;
- `/compte/documents.html?surface=web`.

## Sécurité

Aucun `Supabase`, RPC, `fetch`, WebView, SecureStore, AsyncStorage, notification ou accès biométrique n’est ajouté au composant. Les droits réels du compte restent évalués côté Web/serveur.

La bibliothèque ne doit pas devenir un profil comportemental : la présence d’un roman, d’un projet ou d’une licence ne doit pas être réutilisée dans le natif pour déduire des intérêts, une identité ou une valeur de l’utilisateur.

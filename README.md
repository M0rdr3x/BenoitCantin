# Portail personnel de Benoit Cantin

Site statique professionnel préparé pour le domaine **benoitcantin.ca**.

## Ce qui est construit

- Nom corrigé partout : **Benoit Cantin**, sans accent.
- Identité cosmique professionnelle centrée sur l'idée : **« Je bâtis plusieurs mondes. »**
- Sceau personnel `BC` à côté du nom.
- Section des projets compacte, environ deux fois moins haute qu'une présentation traditionnelle en grandes cartes.
- Cinq espaces autonomes :
  - L'ère des consciences
  - Lumina
  - Futurax
  - Chroniques des Mondes Fracturés
  - Projet Nova
- Site complet de Projet Nova intégré dans `projets/projet-nova/`.
- Liens Facebook du roman et de Projet Nova.
- Questionnaire Web complet du Registre des Consciences, basé sur le PDF officiel.
- Version PDF du questionnaire téléchargeable.
- Formulaires préparés pour Netlify Forms.
- Pages de confidentialité, avis légal, contact, erreur 404 et remerciement.

## Important : démo du roman manquante

Le fichier `La_Cendre_du_Jugement_DEMO.pdf` n'était pas dans les fichiers reçus. Le lien et le dossier sont prêts, mais le bouton reste désactivé pour éviter une erreur 404.

Instructions : `projets/ere-des-consciences/documents/AJOUTER_LA_DEMO_ICI.txt`.

## Mise en ligne recommandée : Netlify

Netlify est recommandé parce que les formulaires sont déjà configurés avec `data-netlify="true"`.

1. Créer un compte Netlify.
2. Glisser le dossier complet du site dans Netlify Drop, ou connecter un dépôt GitHub.
3. Vérifier que les formulaires `contact-general` et `registre-des-consciences` apparaissent dans **Forms**.
4. Tester une soumission de chaque formulaire.
5. Ajouter le domaine `benoitcantin.ca` dans **Domain management**.
6. Configurer les enregistrements DNS demandés par Netlify.
7. Activer HTTPS.

Le fichier `CNAME` contient déjà `benoitcantin.ca`. Si un autre domaine est choisi, modifiez aussi `robots.txt` et `sitemap.xml`.

## Gestion privée des participations

Les réponses du Registre sont accessibles seulement dans le tableau de bord privé Netlify du propriétaire du site.

Procédure recommandée :

1. Ouvrir **Netlify > Forms > registre-des-consciences**.
2. Examiner uniquement les renseignements nécessaires.
3. Documenter la sélection hors ligne dans un registre administratif privé.
4. Quand le personnage est créé et que les données sources ne sont plus nécessaires, supprimer définitivement la soumission et toute photo associée.
5. Traiter rapidement toute demande de correction ou de retrait reçue avant l'intégration définitive.

## Gestion des identités visuelles

Les visuels officiels reçus sont dans `assets/media/`. L’icône de Futurax demeure temporaire dans `assets/icons/`, puisqu’aucun nouveau visuel Futurax n’a été fourni dans ce lot.

## Validation obligatoire avant collecte publique

Le questionnaire contient des renseignements personnels, une photo facultative et un volet pour les mineurs. Avant de rendre le formulaire public, faites valider par un juriste :

- le texte de consentement;
- la politique de confidentialité;
- la conservation et la suppression;
- la participation des mineurs;
- les droits liés aux photographies;
- les modalités d'utilisation créative et commerciale.

Le PDF source lui-même indique que ces aspects doivent être validés par un juriste compétent.


## Identités visuelles officielles intégrées

Les fichiers fournis le 3 août 2026 ont été optimisés en WebP et intégrés au portail :

- bannière et icône de **L’ère des consciences**;
- identité visuelle de **Lumina**;
- couverture de **Chroniques des Mondes Fracturés**;
- bannière et logo de **Projet Nova**.

L’ancienne route `projets/jeux-creations/` redirige vers `projets/chroniques-des-mondes-fractures/` afin de préserver les anciens liens.

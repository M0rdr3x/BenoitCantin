# SINJIRA™ — Liseuse tactile V64, intégration issue du `main` à jour

**Date : 11 novembre 2026. Statut : PR de revue DRAFT, NON fusionnée, NON déployée.**

## Objectif

Réunir dans **un seul candidat d'intégration** les fonctions V52–V63 de lecture tactile, au lieu de fusionner des branches empilées et désormais en retard par rapport à `main`.

Lors de la préparation, `main` avait reçu deux nouveaux commits touchant les workflows d'authentification, les fonctions de registre et les questionnaires, **sans chevauchement des fichiers de liseuse**. Le code V64 est donc reconstruit à partir du `main` courant, avec six fichiers de lecteur et six fichiers de test de V63.

## Expérience utilisateur proposée

| Action | Résultat attendu |
|---|---|
| Balayer à gauche | Avancer d'une portion d'écran de texte; tourner la page PDF source seulement quand elle est terminée |
| Balayer à droite | Revenir à la portion précédente, puis à la dernière portion de la page PDF précédente |
| Changer police, interligne ou largeur | Recomposer la page en conservant autant que possible le même caractère visible, sinon restaurer un ratio proportionnel |
| Tourner un téléphone | Retrouver le passage lu après portrait/paysage; test ajouté spécifiquement en V64 |
| Lire en PDF | Conserver un mode PDF fidèle avec un seul changement de page source par geste |
| Lire au clavier | Touches de page uniquement avec focus sur le livre; éviter les doublons des moteurs historiques V26/V28 |
| Utiliser petit/grand écran | Formats de 320 px à 820 px, texte jusqu'à 34 px, mode lecture concentrée, pas de débordement horizontal |
| Sélectionner du texte | Ne pas interpréter une sélection ou un défilement vertical comme un balayage horizontal |
| Enregistrer le livre démo | Conserver localement le numéro de la page source et une proportion de position au rechargement |

Le texte du livre provient encore de l'extraction PDF ; la pagination est calculée selon la hauteur disponible, **pas** selon les propriétés sémantiques d'un EPUB natif. L'ancre V63/V64 reste temporaire **en mémoire du navigateur**, sans persistance du texte ni synchronisation cloud.

## Couverture V64

- **68 tests Node** (modules de gestes et reflow réunis).
- Trois parcours Playwright dans les moteurs **Chromium et WebKit** : fixture tactile isolée; vraie page `compte/liseuse.html` avec faux PDF; et tailles de téléphone/tablette, clavier, typographie et ancre.
- Le nouveau test V64 vérifie **la même position de caractère après rotation** une fois la police agrandie à 34 px.
- Les requêtes de compte et les ressources externes privées sont bloquées en test. Aucun roman acheté, aucun compte Supabase, aucun secret ni migration de données.
- Une seule CI principale `.github/workflows/sinjira-liseuse-mobile-v64-integration.yml`, en lecture seule.

## Ordre de revue et risques

1. La PR **V64** constitue désormais **le point d'entrée unique** pour l'intégration sur le `main` récent; elle regroupe les fonctionnalités de [V62 #996](https://github.com/M0rdr3x/BenoitCantin/pull/996) et [V63 #998](https://github.com/M0rdr3x/BenoitCantin/pull/998). Ne **pas** fusionner en plus ces deux anciennes PR sans coordination.
2. Obtenir les **deux résultats CI SUCCESS sur le dernier SHA**, revue du différentiel et absence de conflit avec la base.
3. Faire les essais physiques Safari iPhone, Android Chrome et tablettes, en portrait/paysage, sur petits écrans et avec zoom/accessibilité.
4. Valider VoiceOver/TalkBack, focus, sélection, grosse police, gestes de retour, barre supérieure fixe et absence de texte masqué.
5. Éprouver des PDF réels autorisés, 82 pages démo / 520 pages intégrales le cas échéant, et la fluidité sur téléphones peu puissants.
6. Faire approuver indépendamment la protection des romans privés, le service worker/cache et la synchronisation multiappareil. Les RPC candidates V51/V59 dans [PR #986](https://github.com/M0rdr3x/BenoitCantin/pull/986) restent **séparées et non déployées**.
7. Exiger un responsable de publication, un protocole de retour arrière et la mise à jour formelle des portes de lancement avant un éventuel merge.

**Décision actuelle : PAS DE GO production.** Le score audit interne SINJIRA reste **66,5 % ±10 points**, les **13 portes de lancement restent ouvertes**, aucune date de livraison certifiée.

## Autres chantiers du projet Pays

La référence du 8 novembre est inchangée : **Projet Nova politique 47 %** (finances 3/16, cible conditionnelle 31 décembre 2027), **Nova–Sinjira services publics 14 secteurs sans pourcentage global fiable**, **boussole 75 % (9/12)** et **sondage 54,5 % (6/11)**. Voir le [bilan consolidé fusionné dans `main`](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md).

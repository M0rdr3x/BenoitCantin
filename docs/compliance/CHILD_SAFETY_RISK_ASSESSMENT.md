# SINJIRA™ — analyse de risque pour les enfants et adolescents

Version V24.4.83 — 2026-08-19.

## Population et limites

- Moins de 13 ans: inscription libre-service interdite.
- 13 ans: autorisation parent/tuteur adulte vérifiée par le mécanisme SINJIRA™ obligatoire.
- 14–17 ans: compte jeunesse; protections sociales renforcées.
- Rencontres SINJIRA™: 18+ uniquement au niveau serveur.

## Menaces prioritaires

1. Contact adulte-mineur et contournement de la séparation d'âge.
2. Grooming, sexualisation, demande de photos intimes ou secret imposé.
3. Déplacement vers une application externe/téléphone/courriel afin d'échapper à la modération.
4. Sollicitation financière, cartes-cadeaux, crypto, extorsion ou fraude.
5. Prostitution, proxénétisme, traite/vente de personnes et recrutement à des fins d'exploitation.
6. Vente de drogues ou de produits illicites.
7. Doxxing, géolocalisation précise, exposition du vrai nom ou de coordonnées.
8. Harcèlement, haine, menace, manipulation et usurpation.
9. Design persuasif incitant à réduire la confidentialité ou à fournir plus de données.
10. Profilage/recommandation susceptible de pousser du contenu nuisible.

## Mesures techniques obligatoires

- Cohortes jeunesse/adulte séparées côté serveur; aucune confiance dans le seul JavaScript.
- `youth_pending` sans interaction sociale tant que le niveau requis n'est pas vérifié.
- Confidentialité élevée par défaut.
- Aucune géolocalisation précise d'un mineur rendue visible à un autre utilisateur.
- Aucun ciblage publicitaire comportemental.
- Aucun commerce sexuel ou contenu sexuel payant.
- Garde serveur sur contenus persistés et messagerie jeunesse.
- Blocage + signalement accessibles; les signalements de danger ne dépendent pas de l'acceptation préalable des règles.
- Signalements critiques convertis en dossier d'escalade interne.
- Supervision parent/tuteur limitée aux métadonnées de sécurité prévues; ne pas transformer la supervision en lecture générale secrète des conversations.
- Le jeune doit pouvoir comprendre qu'une supervision est active.

## Design et UX

- Explications adaptées à l'âge, courtes et concrètes au moment du risque.
- Aucun bouton précoché qui publie une information privée.
- Aucun nudge poussant le jeune à rendre son profil plus public.
- Les fonctions facultatives sont désactivées par défaut.
- La sortie/blocage/signalement doit être plus simple que la poursuite d'une interaction inquiétante.

## Mesures de gouvernance

- Revoir cette analyse avant chaque nouvelle messagerie, partage média, live audio/vidéo, géolocalisation, recommandation sociale ou système économique jeunesse.
- Tester spécifiquement les contournements d'âge, changement de date de naissance, comptes adultes se faisant passer pour mineurs et comptes mineurs se faisant passer pour adultes.
- Examiner les rapports prioritaires sans demander au modérateur de rechercher du matériel d'exploitation sexuelle d'enfants.
- Limiter l'accès aux dossiers sensibles au strict besoin.

## Fonctions non activables sans nouvelle analyse

- messages adulte-mineur;
- Rencontres sous 18 ans;
- partage d'images arbitraires en Rencontres;
- géolocalisation précise jeunesse;
- diffusion vidéo jeunesse avec inconnus;
- paiements/achats destinés aux mineurs;
- système d'identité sous 13 ans;
- profilage publicitaire ou vente de données.

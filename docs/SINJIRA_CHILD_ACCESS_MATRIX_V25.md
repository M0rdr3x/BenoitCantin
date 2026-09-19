# SINJIRA™ V25 — Matrice d'accès 11–12 ans

## Principe

**L'humain avant tout. Protéger sans surveiller.**

Un compte `child` correspond à un membre de 11 ou 12 ans avec supervision parentale/tuteur vérifiée. Pour cette tranche d'âge, une page du compte ne doit jamais devenir accessible par accident parce qu'elle a simplement été ajoutée au dépôt.

La règle V25 est donc **fail-closed** : chaque page `compte/*.html` appartient à une catégorie explicite. Toute nouvelle page non classée doit échouer en CI et reste inaccessible aux comptes 11–12 ans jusqu'à décision.

Cette matrice est une frontière de navigation et de produit. Elle ne remplace pas les contrôles serveur : les fonctions sensibles doivent aussi rester protégées par RLS, RPC, triggers ou Edge Functions.

## Catégorie A — autorisé 11–12 ans

Ces surfaces sont privées, de sécurité, de création personnelle, propres à la Communauté Junior ou bornées par un classement de contenu explicite.

- `index.html` — accueil du compte;
- `bibliotheque.html` — bibliothèque filtrée côté serveur : seuls les projets explicitement `approved_11_12` sont visibles; aucun achat, licence, demande testeur ou lecture privée non classée;
- `documents.html` — documents filtrés côté serveur : le document **et** son projet doivent tous deux être explicitement approuvés 11–12 ans;
- `projet.html` — fiche d'un projet approuvé 11–12 ans; aucun bouton de jeu ou playtest n'est présenté au compte enfant tant que ces parcours n'ont pas leur propre certification;
- `blocages.html` — personnes masquées / sécurité sociale;
- `communaute-junior.html` — fil Junior 11–12 ans;
- `confidentialite-joueur.html` — information vie privée;
- `histoire-de-vie.html` — espace personnel privé;
- `moderation.html` — décisions et appels concernant son propre compte;
- `mon-personnage.html` — création privée de son personnage;
- `mes-personnages.html` — consultation de ses personnages;
- `notifications.html` — notifications de son compte;
- `parametres.html` — préférences du compte;
- `profil.html` — profil de son propre compte; il n'est pas utilisé comme identité dans le fil Junior;
- `registre-personnel.html` — registre privé protégé;
- `regles-communaute-junior.html` — règles spécifiques Junior;
- `relations.html` — lien parent/tuteur et relations privées;
- `securite.html` — sécurité du compte, appareils et protections;
- `vie-privee.html` — centre de vie privée.

## Catégorie B — authentification et récupération autorisées

Ces pages restent disponibles parce qu'elles servent à établir ou récupérer l'accès au compte, pas à ouvrir un module métier.

- `connexion.html`;
- `inscription.html`;
- `mot-de-passe-oublie.html`;
- `reinitialiser-mot-de-passe.html`;
- `mfa.html`.

## Catégorie C — redirection vers l'équivalent Junior

- `communaute.html` → `communaute-junior.html`;
- `regles-communaute.html` → `regles-communaute-junior.html`.

Un compte 11–12 ans ne doit jamais rester dans la communauté générale pendant que la détection d'âge est en cours.

## Catégorie D — restreint 11–12 ans jusqu'à revue dédiée

Ces surfaces ne sont pas ouvertes à un compte `child`. Certaines pourront être réouvertes plus tard lorsqu'un contrat d'âge, de contenu ou de responsabilité aura été prouvé.

### Contenu et jeux encore fermés

- `mes-lectures.html`;
- `mes-parties.html`.

La Bibliothèque, Documents et Projet ont maintenant un classement humain explicite. Le défaut `unreviewed` reste fermé. Aucun projet ou document existant n'est automatiquement approuvé parce qu'il était déjà public, associé au compte ou accessible à un adulte. Les lectures privées et parties restent fermées jusqu'à leur propre contrat d'âge.

### Social général et communication

- `messages.html`;
- `messages-reels.html`;
- `messages-personnage.html`;
- `mes-commentaires.html`;
- `reseau-personnage.html`;
- `rencontres.html`.

La Communauté Junior ne crée aucune messagerie privée. Rencontres reste strictement 18+.

### Commerce, argent et licences

- `jetons.html`;
- `licences.html`;
- `marche.html`;
- `mes-achats.html`.

Une future ouverture éventuelle exige un parcours parental distinct; le simple fait d'être supervisé ne constitue pas une autorisation d'achat.

### Participation, travail et modules non encore certifiés

- `contributions.html`;
- `emploi.html`;
- `playtests.html`;
- `mon-ia.html`;
- `monde-parallele.html`;
- `signaler-deces.html`.

Le Programme Contributeur reste neutralisé côté serveur pour 11–12 ans. Emploi, Mon IA, Monde parallèle, playtests et procédure de décès demandent chacun une revue spécifique avant toute ouverture Junior.

## Comportement de navigation

Pour un compte `child` :

1. les liens de navigation vers une surface restreinte sont masqués;
2. une URL directe vers une surface restreinte est redirigée vers `/compte/communaute-junior.html?from=restricted&module=...`;
3. la page Junior explique qu'une section non certifiée n'est pas encore disponible;
4. une nouvelle page `compte/*.html` non présente dans cette matrice est **restreinte par défaut**;
5. la communauté générale et ses règles sont remplacées par leurs versions Junior.

## Décision de capacités self-only

`sinjira_my_account_capabilities()` centralise maintenant les décisions de surface du compte courant. Le RPC n’accepte **aucun UUID** et ne renvoie ni date de naissance, courriel, pseudo ni identité. Il expose uniquement des capacités fonctionnelles comme `child_11_12`, `native_general_hubs`, `general_community`, `dating` et `library_mode`.

Les bandes `child_pending`, `youth_pending`, `under11`, `unverified` ou autres états non vérifiés reçoivent un `account_mode` **restricted** par défaut. Seuls `adult` et `youth` vérifiés reçoivent le mode `standard`; `child` reçoit le mode Junior 11–12.

Le Web, la Bibliothèque, la Communauté générale et le pont mobile utilisent ce même contrat afin d’éviter des décisions d’âge divergentes entre interfaces.

## Invariants serveur

La navigation n'est jamais considérée comme une barrière de sécurité suffisante. Les invariants suivants restent obligatoires :

- aucune messagerie privée pour la bande `child`;
- aucune interaction sociale historique via `sinjira_can_social_interact`;
- Rencontres 18+ côté serveur;
- Programme Contributeur forcé à `false` pour 11–12 ans;
- Communauté Junior via RPC bornées uniquement, sans accès table direct;
- aucun UUID auteur, nom réel, avatar ou courriel dans le fil Junior;
- activation Communauté Junior révocable par un parent/tuteur vérifié;
- un lien `guardian_links` révoqué (`revoked_at` non nul) ne peut ni maintenir l’activation Junior ni conserver l’enfant dans la liste Junior de ce tuteur, même si un autre tuteur valide maintient la bande `child`;
- sortie automatique de la bande Junior à 13 ans;
- les nouvelles surfaces restreintes doivent recevoir leur propre garde serveur avant d'être déplacées en catégorie A;
- pour Bibliothèque/Documents/Projet, `unreviewed` et `blocked_11_12` restent fermés; seul `approved_11_12` ouvre le contenu;
- l'approbation 11–12 est une décision humaine distincte pour le projet et pour chaque document; elle enregistre le réviseur et l'heure de décision;
- toute décision admin `approved_11_12`, `blocked_11_12` ou retour à `unreviewed` exige un second facteur configuré et une session `aal2` active avant l'écriture.

## Couverture

La matrice couvre exactement les **44** fichiers HTML présents directement sous `compte/` au moment de cette révision.

Toute divergence entre le dossier réel, cette classification et les ensembles utilisés par `sinjira-account.js` doit faire échouer la validation CI.

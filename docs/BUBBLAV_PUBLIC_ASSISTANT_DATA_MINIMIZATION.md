# BubblaV — minimisation des formulaires du chatbot public

Dernière revue : 29 septembre 2026.

Suivi fournisseur : issue GitHub **#443** — désactivation/retrait des six formulaires hors périmètre.

## Principe

Le chatbot public **Nova × SINJIRA** sert à expliquer et orienter à partir des contenus publics. Il ne remplace pas les parcours authentifiés de SINJIRA et ne doit pas devenir une seconde voie de collecte pour les fonctions de compte, de jeu, du Registre ou des commentaires.

La règle appliquée est :

- contenus publics et orientation : autorisés;
- contact humain demandé explicitement : autorisé avec minimisation et consentement;
- connexion, création/rejoindre une partie, Registre des Consciences, commentaire de roman et autres actions de compte : renvoi vers le parcours officiel du site;
- aucune donnée privée de compte n'est nécessaire pour utiliser le chatbot public.

## État BubblaV observé lors de la revue

Huit formulaires BubblaV étaient actifs et affichaient tous `submission_count=0`.

### Conservés

1. `33f468ed-d73e-40cb-b6e2-fddff06f73eb` — **Contacter Le Projet Nova**
   - coordonnées, sujet, message;
   - consentement explicite obligatoire pour l'utilisation des renseignements.

2. `62cdc933-e88a-481d-be2e-f76bc3ba007d` — **Contacter Benoit Cantin**
   - coordonnées, projet, message;
   - consentement explicite obligatoire pour l'utilisation des renseignements.

L'intégration BubblaV `contact_form` / **Escalate to Human** reste aussi active uniquement pour une demande explicite de contact humain.

### À retirer ou désactiver côté fournisseur

Les formulaires suivants avaient zéro soumission au moment de la revue. Ils ont été identifiés comme non nécessaires au chatbot public et doivent être retirés ou désactivés côté fournisseur afin de réduire la collecte et éviter des parcours concurrents. La tentative de suppression automatique a été bloquée par les contrôles de sécurité du connecteur; ils doivent donc être considérés comme encore actifs tant qu’une vérification fournisseur ne prouve pas le contraire :

- `4bf9fa08-80af-4a71-991f-3c4ea3e3ecf7` — **Se Connecter À Son Compte**;
- `fb6b7188-0ff5-4eec-b751-2a3af99dfb89` — **Rejoindre Une Partie**;
- `89288220-eda7-4a73-8d71-832e1c31ad6f` — **Créer Une Partie**;
- `f5924b79-7932-4651-9621-5e7f538752ee` — **Inscrire Une Conscience**;
- `7fa76ade-5322-4465-a579-db56ab21b402` — **Soumettre Un Commentaire**;
- `a8806fd2-8030-4104-a73c-c3a9470bcd37` — **Support Request Form**.

## État d’application

- règle de gouvernance Git : appliquée;
- pages publiques et politique de confidentialité : alignées;
- accueil du widget BubblaV : aligné pour rediriger les actions de compte vers les parcours officiels;
- suppression/désactivation des six formulaires fournisseur non nécessaires : **non confirmée**;
- revérification fournisseur : les 8 formulaires sont toujours `enabled=true`; les six formulaires ciblés affichent toujours `submission_count=0`;
- aucune suppression de soumission ou d’historique fournisseur n’a été effectuée.

## Parcours canoniques

- connexion et récupération : pages officielles du Compte SINJIRA;
- création/rejoindre une partie : parcours de jeu authentifié;
- Registre des Consciences : formulaire officiel du Registre avec ses protections de compte;
- commentaires : parcours roman relié au compte et à la modération;
- support général : Contact officiel ou escalade humaine explicite;
- Projet Nova : formulaire public de contact avec consentement.

## Garde de gouvernance

Toute nouvelle forme de collecte ajoutée à BubblaV doit être revue avant activation selon :

1. nécessité réelle;
2. minimisation des champs;
3. caractère public ou authentifié du parcours;
4. consentement lorsque requis;
5. absence de doublon avec un parcours sécurisé existant;
6. conservation et destination des données;
7. protection particulière des mineurs et des données sensibles.

Cette revue ne modifie aucune migration Supabase, aucun secret, aucun reviewed batch et aucune ligne du ledger production.

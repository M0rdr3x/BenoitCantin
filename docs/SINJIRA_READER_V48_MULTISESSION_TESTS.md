# SINJIRA — V48 : recette PostgreSQL multi-connexion de la liseuse V32

**Date : 8 novembre 2026 — programme SINJIRA.** Ce chantier fait progresser **la confiance dans la migration V32**, sans modifier la production ni fermer prématurément les deux jalons `reader_v32_prod` et `reader_two_devices`.

## Pourquoi cette recette existe

La V47 (PR #899, fusionnée) a constaté sur la base Supabase réelle **7 PASS, 2 BLOCK, 1 REVIEW, NO_GO**. Le champ `scroll_ratio` et sa contrainte 0..1 manquent toujours sur la production; la migration V32 existe dans le dépôt mais n'est pas encore appliquée.

Les tests V48 vont plus loin qu'un inventaire de catalogues : ils exécutent **la vraie migration V32 du dépôt**, mais **uniquement** sur un PostgreSQL 17 éphémère contenant deux comptes et deux romans **fictifs**. Aucune vraie session, aucun PDF privé, aucun document ou identifiant Supabase n'est utilisé.

## Quatre connexions de test isolées

| Connexion psql | Scénario attendu | Critère |
|---|---|---|
| **1. Setup** | Création d'un schéma miniature, politique RLS propriétaire, deux positions héritées `scroll_ratio=NULL`, exécution originale V32 | `numeric(5,4)`, contrainte existante, aucune progression héritée perdue |
| **2. Client A** | Connexion sous le rôle `authenticated` et revendication de compte fictive A, mise à jour puis UPSERT | Page 13, 28 %, position 0.5678 sauvegardées; ratios négatifs et supérieurs à 1 refusés; B invisible |
| **3. Client B** | Connexion SQL distincte avec une autre revendication fictive; tentative de lire, modifier ou créer une ligne appartenant à A | Refus RLS, aucune modification de la ligne A; B peut sauver sa propre position; `anon` ne voit aucune ligne malgré ses GRANT simulés |
| **4. Retour A** | Nouvelle connexion SQL distincte avec revendication fictive A | La sauvegarde initiale 13 / 28 % / 0.5678 est retrouvée intacte après le passage de B; ratios limites 0 et 1 admis |

Chaque étape exécute une **invocation `psql` indépendante** et échoue si la progression attendue est fausse ou si l'usurpation réussit. Les valeurs de compte sont des UUID purement artificiels. Les revendications de session sont simulées par une variable PostgreSQL : **cela ne teste pas la validation cryptographique d'un JWT Supabase réel ni la révocation des sessions**.

## Contrôles de sécurité CI

Le workflow `.github/workflows/sinjira-reader-v48-multisession.yml` démarre PostgreSQL 17.6 **seulement sur le runner GitHub jetable**. Il expose son port uniquement sur `127.0.0.1`, avec confiance limitée au service temporaire, sans secret enregistré, jeton de production ni connexion distante. Des tests Python veillent au caractère fictif des utilisateurs, à la RLS et à l'utilisation du fichier V32 original.

Ce banc d'essai vérifie la **persistance et le contrôle SQL sur plusieurs connexions**, et non la véritable expérience sur deux appareils. Il ne prouve pas non plus la sécurité des Storage URLs, la gestion hors ligne, le cache PWA, le contrôle des droits de romans ni la concordance totale du schéma de la production avec le schéma miniature. Un succès ne doit donc **jamais** être présenté comme une certification multi-appareils ou de production.

## Prochaines actions obligatoires

1. **Vérifier les droits et les sauvegardes réels** de la table dans un environnement isolé fidèle, et l'absence de politique supplémentaire ou de passage par fonction privilégiée.
2. **Faire appliquer V32 selon le runbook protégé**, avec approbation explicite, dry-run, workspace limité, surveillance et stratégie de retour arrière. Ne pas utiliser un push global sur la base liée.
3. **Rejouer V47 sur les catalogues de production** : les 2 BLOCK doivent passer à PASS, les GRANT `anon` sont à revoir, et la décision automatique reste seulement `REVIEW_REQUIRED`.
4. **Réaliser l'essai réel sur deux appareils** (ou deux navigateurs distincts connectés à une instance de staging fidèle) : sauvegarde page + scroll, réouverture, reconnexion, changement d'utilisateur, perte réseau, contrôle des lectures d'autrui, fermeture et restauration de l'application; enregistrer une preuve autorisée.
5. **Fermer les jalons du registre** seulement après la preuve de fonctionnement réel, pas après la CI isolée. Le taux global reste **66,5 % ≈ 67 %**, avec une date de fin **indéterminée**.

Suivi général : [issue #826](https://github.com/M0rdr3x/BenoitCantin/issues/826). Audit de la liseuse : [PR #899](https://github.com/M0rdr3x/BenoitCantin/pull/899). Le programme Fracture reste par ailleurs **NO_GO réseau** dans [issue #872](https://github.com/M0rdr3x/BenoitCantin/issues/872).

# SINJIRA V25 — Porte consolidée de décisions humaines

Date : 4 octobre 2026  
PR : #435 — `a1/integration-rehearsal`  
HEAD de référence : `193b686f34ba89fe7ec91022faf1651f14bf3e18`

> **STATUT : DÉCISIONS HUMAINES EN ATTENTE.**
>
> Ce document résume les choix qui doivent être explicitement acceptés, refusés ou renvoyés en modification avant toute promotion des 44 migrations futures. Il ne constitue aucune approbation, ne modifie aucun SQL, ne modifie pas `supabase/production-reviewed-migration-batch.txt`, ne modifie pas `supabase/production-migration-ledger.txt` et n'autorise aucune écriture Supabase production.

## Preuve technique attachée au HEAD

- PR draft, mergeable, 1698 commits devant `main`, 0 derrière.
- CI complète : **144 runs terminés = 131 success / 12 skipped / 1 failure**.
- L'unique failure est le verrou volontaire `migration-history-guard` : toutes les étapes de sécurité, plan, traçabilité et provenance passent; seule la promotion des migrations non approuvées est refusée.
- **44 migrations futures** restent hors du reviewed batch.
- **42/44** correspondent aux blobs déjà préparés dans les paquets de revue historiques.
- La 44e migration est `20261004235000_sinjira_v25_livre_i_master_2026_10_04.sql` : correction forward-only du catalogue Livre I de 1066 à 1027 pages; elle ne configure aucun bucket/path, n’active aucune diffusion et ne modifie aucune migration historique.
- La migration enfant `20260916210000_sinjira_v25_child_guardian_signup.sql` a été corrigée après la décision technique #453; blob courant : `3231fc2720a28700be9d1be117e53a9a2448b08b`.
- Les frontières calendaires 11 / 13 / 18 ans repassent **75/75** en pgTAP; cette preuve ne vaut pas approbation du Lot B.

## Mode de décision

Pour chaque ligne ci-dessous, le reviewer humain doit inscrire **exactement une** décision :

- `ACCEPTER`
- `REFUSER`
- `MODIFIER`

Une justification courte est obligatoire. `EN ATTENTE` n'est pas une approbation.

| ID | Décision humaine requise | Comportement actuellement implémenté | Statut |
|---|---|---|---|
| H1 | **Mode Voyage — portée du risque** | Un voyage actif ne neutralise que le signal géographique attendu; appareil inconnu, récupération, action sensible et impossible travel conservent leurs risques/challenges. | **EN ATTENTE** |
| H2 | **Mode Voyage — rétention** | Les plans expirés sont purgés par une fonction serveur/service-role selon `delete_after`; aucun ordonnanceur implicite n'est créé par le lot. | **EN ATTENTE** |
| H3 | **Âge minimal et bandes 11 / 13 / 18 ans** | <11 refusé; 11–12 = `child/child_pending`; 13–17 = `youth/youth_pending`; 18+ = `adult`; seuils basés sur âge complété. | **EN ATTENTE** |
| H4 | **Supervision 11–12 et transition à 13 ans** | Un tuteur vérifié est requis pour le parcours 11–12; les capacités sensibles restent fail-closed; le passage à 13 change la bande sans ouvrir automatiquement les capacités non permises. | **EN ATTENTE** |
| H5 | **AAL2 tuteur / retrait immédiat du mineur** | Création/lecture de codes et actions tuteur sensibles exigent AAL2; le mineur conserve les voies de désactivation/retrait immédiat prévues sans dépendre d'un step-up du tuteur. | **EN ATTENTE** |
| H6 | **Fin de visibilité du tuteur à la majorité** | À 18 ans, les liens/invitations de supervision cessent d'être visibles au tuteur; la personne concernée conserve son propre historique. | **EN ATTENTE** |
| H7 | **Métadonnées parentales** | Opt-in par défaut à `false`; consentement explicite + AAL2 pour les métadonnées permises; réponse minimisée; pas d'UUID, nom privé complet, alias Junior ou contenu des messages/publications. | **EN ATTENTE** |
| H8 | **Rôles owner / service_role / member** | L'autorité propriétaire vient du rôle serveur canonique, jamais d'un courriel gravé dans SQL; `service_role` reste réservé aux opérations serveur; aucun faux achat/entitlement n'est créé pour l'owner. | **EN ATTENTE** |
| H9 | **Accès explicite player/tester versus droits commerciaux** | Un droit `player/tester` explicite peut ouvrir certains projets non publics pour adult/youth; il reste distinct d'un achat. Une commande ne donne un droit produit que si elle est réellement `paid`, ou via entitlement canonique. | **EN ATTENTE** |
| H10 | **Famille créateur** | La famille créateur utilise un registre privé sans courriel stocké dans la table, avec catalogue distinct des droits commerciaux; les comptes 11–12 restent minimisés et sans accès intégral non classé. | **EN ATTENTE** |
| H11 | **Communauté Junior — consentement et révocation** | Junior exige le consentement prévu; toute révocation masque/ferme les capacités associées sans ressusciter automatiquement un consentement antérieur. | **EN ATTENTE** |
| H12 | **Communauté Junior — modération** | Une publication masquée n'accepte plus de nouveaux commentaires; le contenu existant n'est pas supprimé silencieusement; les décisions de modération restent humaines et réversibles selon les outils prévus. | **EN ATTENTE** |
| H13 | **Contenus 11–12** | Accès uniquement aux projets/documents explicitement `approved_11_12`; contenus non classés, payants non autorisés, playtests et modules sensibles restent fermés par défaut. | **EN ATTENTE** |
| H14 | **RPC / helpers self-only** | Les appels navigateur sont bornés à `auth.uid()`; un UUID tiers retourne fail-closed; les implémentations privilégiées sont déplacées hors de la surface API publique lorsque nécessaire. | **EN ATTENTE** |

## Décisions bloquantes par lot

### Lot A — Mode Voyage
Bloqué tant que **H1 + H2** ne sont pas explicitement décidés.

### Lot B — Enfant / Junior / Tuteur
Bloqué tant que **H3 + H4 + H5 + H6 + H7 + H11 + H12 + H13** ne sont pas explicitement décidés.

### Lots C / D / E — Compte, catalogue, helpers, famille créateur
Bloqués tant que **H8 + H9 + H10 + H14** ne sont pas explicitement décidés.

### Lot F — correctifs Junior forward-only
Bloqué tant que **H11 + H12** sont décidés et que leur cohérence avec le Lot B est confirmée.

## Vérifications obligatoires après toute décision `MODIFIER`

Si un seul choix reçoit `MODIFIER` :

1. ne toucher ni au reviewed batch ni au ledger;
2. modifier uniquement le SQL/code nécessaire sur la branche #435;
3. recalculer le blob des migrations touchées;
4. considérer l'ancienne décision invalide pour chaque blob modifié;
5. reconstruire Supabase localement depuis zéro;
6. relancer les pgTAP/validateurs/workflows associés;
7. mettre cette fiche à jour avec le nouveau HEAD et les nouvelles empreintes;
8. demander une nouvelle décision humaine sur le diff final.

## Porte avant reviewed batch

Le reviewed batch ne peut être envisagé que lorsque :

- [ ] H1 à H14 ne contiennent plus aucun `EN ATTENTE`;
- [ ] toute décision `MODIFIER` a été implémentée puis revalidée;
- [ ] les 44 migrations du HEAD décidé sont gelées par empreinte;
- [ ] la migration Livre I 2026-10-04 est revue comme changement technique de métadonnée, sans être confondue avec une autorisation de diffusion privée;
- [ ] les tests associés sont verts;
- [ ] le reviewer confirme séparément qu'il approuve **le lot complet des 44 migrations**, pas seulement les principes;
- [ ] #240, #439 et #437 restent traités comme des verrous indépendants;
- [ ] aucune écriture production n'est déduite de la revue.

## Porte avant ledger

Le ledger production ne doit changer **qu'après** une application production explicitement autorisée et prouvée. Une approbation de migration, un merge ou une CI verte ne constituent jamais cette preuve.

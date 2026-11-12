# Projet Nova — P50H : habilitations, preuves et séparation des décisions
**14 octobre 2026 · Document préparatoire · NO_GO publication · V3.40 inchangée**

## 1. Portée et continuité
Ce jalon prolonge P50F (PR 645) et P50G (PR 646), sans modifier le site public, les statuts ni les droits d'autrui. Le mandat des personnes, la conformité juridique, la situation financière et l'autorisation électorale ne sont **pas** démontrés par un accès à GitHub. Les PR 636 et 638 demeurent en revue; PR 640 est exclusivement une branche d'intégration **NE PAS FUSIONNER**.

**Constat du 14 octobre 2026 :** zéro revue formelle constatée dans l'API de GitHub pour les PR 636, 638 et 646. Ce constat doit être rafraîchi avant toute décision. SHA de `main` lu : `9ed5f70cbe7022f25a679346a1288701f3b09067`.

## 2. Principe cardinal
Une habilitation requiert au moins : une source d'autorité identifiée (loi, mandat ou délégation), le périmètre de décision, sa durée, les incompatibilités et la preuve de validité. **La possession de droits techniques d'écriture ou de fusion ne vaut pas délégation d'autorité.** Aucun document de cette PR n'atteste une habilitation.

### Matrice de responsabilité (proposée, sous réserve de désignations réelles)

| Fonction | Peut préparer | Doit vérifier | Ne peut pas faire seul |
|---|---|---|---|
| Responsable du contenu | formulations et concordance | exactitude, identité et archives | autoriser fusion ou publication |
| Réviseur technique indépendant | analyse diff, CI, dépendances | SHA précis, risques de régression | remplacer validation juridique |
| Responsable confidentialité | registre des traitements | minimisation, durée, incidents, transferts | signer une autorisation électorale |
| Conseil juridique externe | avis daté | statut applicable, finances et collecte | représenter une autorité publique sans mandat |
| Mainteneur habilité | intégration technique | branche, revues, code, rollback | décider seul de la légalité ou du mandat |
| Opérateur habilité | déploiement et restauration | sauvegarde, cache, capacité de retour | déployer sans autorisation |
| Décideur habilité | décision finale en amont | ensemble des portes PRE et réserves | déclarer une preuve technique comme juridique |
| Responsable de recette indépendant | observations après déploiement | HTTP, redirections, contenus, formulaires, paiement | conclure seul au respect de la loi |

En cas de cumul des rôles, documenter la justification et établir un contre-contrôle indépendant; pour les fonctions décision, exploitation et recette, privilégier trois intervenants distincts. Aucun nom, signature ou mandat non public ne doit être consigné dans Git.

## 3. Chaîne de preuves et classification
Chaque preuve demeure dans un espace contrôlé hors dépôt : identifiant opaque `EV-...`, nature, auteur habilité, date, SHA visé, méthode de vérification, résultat, période de validité et mécanisme de révocation. **Seuls les identifiants non sensibles et états agrégés** peuvent apparaître au registre public.

Quatre états de suivi : `NON_DOCUMENTE`, `A_VERIFIER`, `VERIFIE_HORS_DEPOT`, `REJETE`. Un statut `VERIFIE_HORS_DEPOT` n'est pas une validation automatique; il doit être confirmé par l'autorité humaine compétente. Un document expiré, signé par une personne non habilitée, au mauvais SHA, non indépendant lorsque nécessaire ou déclaré erroné devient `REJETE`.

## 4. Portes ordonnées (P50G consolidé)
Les **12 portes de préparation** doivent être satisfaites avant qu'un GO humain puisse être envisagé :
- B01 — identité publique : Projet Nova; « Parti Nova » uniquement comme appellation future conditionnelle.
- B02 — vérification du régime électoral et du périmètre autorisé; aucune contribution, dette, prêt ou sollicitation sans droit vérifié.
- B03 — aucun formulaire, embed de collecte, paiement ou adhésion activés.
- B04 — sécurité du dépôt et absence de données personnelles réelles dans les registres publics.
- B05 — avis de confidentialité adapté au traitement réel : contact courriel, finalité, accès, destruction, transfert éventuel et incidents.
- B06 — revue indépendante des derniers SHA de la PR 636.
- B07 — revue indépendante des derniers SHA de la PR 638.
- B08 — contrôle d'intégration CI, dépendances, branches et PR 640 non fusionnée.
- B09 — mandat et pouvoir de décision documentés; séparation technique/politique/juridique.
- B10 — sauvegarde et exercice de restauration **isolé** plus plan d'exploitation révisé.
- B11 — décision humaine écrite, datée, sur les SHA et le périmètre final.
- B13 — procédure d'alerte, d'arrêt et d'incident prête et attribuée.

Les **deux portes de clôture post-déploiement**, impossibles à attester préalablement, sont :
- B12 — recette réelle des six URL HTTPS, réponses HTTP, redirections, empreintes, textes, formulaires et paiements après un déploiement légalement autorisé.
- B14 — procès-verbal de clôture, réserves traitées, archive probante.

Le contrôleur automatique contrôle la forme du registre et les incohérences internes; il **ne pourra jamais produire un GO** et ne constitue pas une preuve d'identité, de signature, de revue GitHub ni de déploiement.

## 5. Règles de décision
1. Avant décision : toutes les portes PRE applicables doivent être étayées, à jour et vérifiées indépendamment; toute incertitude reste bloquante.
2. Les preuves sont à reprendre après changement de SHA, expiration de mandat, découverte d'incident ou modification des flux de données.
3. Seule une décision expresse émise par l'autorité habilitée, après avis nécessaires et dans les limites de la loi, peut autoriser une action définie.
4. La PR 640 reste **non fusionnable**. Toute fusion des PR 636 et 638 et de cette PR exige des décisions et revues distinctes.
5. Après une mise en ligne réellement autorisée : réaliser B12 puis B14, sinon revenir à NO_GO ou ouvrir incident. Ne jamais baptiser « publié » un simple résultat CI.
6. Un retour arrière Git ne supprime pas les informations déjà transmises ni les traces externes (cache, moteur de recherche, courriel), à traiter distinctement.

## 6. Dossier de constat à la date du jalon
- V3.40 : inchangée.
- P2-C0-49 EN_COURS; W0 NON_CLOTUREE; W1 NO_GO; W2–W4 NON_AUTORISEES.
- E26 0/20; pouvoirs 0/14; pièces financières 0/16; 14/14 portes financières bloquantes.
- 14 portes P50G/P50H : **zéro attestée par ce jalon**. Les éléments externes devront être recueillis; ne pas fabriquer de validation.
- Aucune décision de déploiement prise; tous les formulaires externes demeurent suspendus.

## 7. Sources d'orientation externes, non attestation individuelle
- Élections Québec, autorisation du financement politique : https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-une-autorisation/
- Commission d'accès à l'information, principaux changements Loi 25 : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25
- CAI, rôle du responsable en entreprise : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/responsable-protection-renseignements-personnels-entreprise

Le régime légal concret (particulier, société, parti en voie d'autorisation, etc.) doit être déterminé par un juriste compétent; une page générale ne le prouve pas.

## 8. Prochaine étape conditionnelle : P50I
Collecter **hors Git** les habilitations réelles et avis juridiques, fixer les responsables de protection des renseignements et de publication, vérifier les conflits de rôle, puis seulement considérer un dossier de décision humaine. P50I n'est pas une approbation préalable ni une promesse de mise en ligne.

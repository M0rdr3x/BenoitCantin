# Projet Nova — P50J : protocole de réception sécurisée et d'authenticité des preuves

**Date : 14 octobre 2026 · Nature : CONCEPTION PRÉPARATOIRE · Décision : NO_GO.**
**Aucun coffre de documents, formulaire, compte ou canal de réception n'est déployé par ce jalon.**

## 1. Objet, portée et invariants

P50J prolonge P50I (qualification juridique et neuf familles de preuves Q01–Q09) et P50H (12 portes avant décision et deux portes après déploiement). Le jalon prépare **une méthode** pour que des responsables effectivement habilités puissent ultérieurement recevoir et contrôler des justificatifs. Il ne constitue pas la réception d'une pièce ni l'authentification d'un mandat.

- Identité actuelle : **Projet Nova** ; « Parti Nova » uniquement comme éventuelle appellation future conditionnelle.
- Formulaires, adhésions, signatures d'électeurs, dons, prêts et paiements : **aucune activation**.
- PR **640 : NE PAS FUSIONNER**. PR 636, 638 et 645–648 conservent leurs validations propres.
- Base maîtresse V3.40 inchangée ; P2-C0-49 EN_COURS, W0 NON_CLOTUREE, W1 NO_GO, W2–W4 NON_AUTORISEES, E26 0/20, pouvoirs 0/14, pièces financières 0/16 et 14/14 portes financières bloquantes demeurent sans levée.
- Les pièces d'identité, signatures, états financiers, renseignements d'électeurs, coordonnées privées, actes notariés et mandats signés **NE DOIVENT PAS entrer dans GitHub, Issues, PR, CI, captures d'écran, journaux ni pièces jointes publiquement accessibles**.

## 2. Démarrage interdit sans décision de conformité

Avant de concevoir un canal réel de dépôt, déterminer **hors dépôt** : (i) la personne ou entité juridiquement porteuse, (ii) la finalité nécessaire de chaque type de pièce, (iii) la base juridique et les obligations de confidentialité applicables, (iv) le responsable de traitement, (v) les prestataires et transferts, (vi) les durées légales de conservation, (vii) le mécanisme d'effacement, (viii) la gestion des demandes et des incidents, (ix) les habilitations et remplacements des opérateurs.

Un avis juridique et une revue de protection des renseignements documentés par des professionnels compétents sont **préalables**, non postérieurs, à tout déploiement ou demande de transmission de pièces.

## 3. Architecture cible à valider (aucune infrastructure construite)

| Zone | Information permise | Contrôle cible |
| --- | --- | --- |
| A — GitHub public | Procédures, modèle vide, statuts agrégés non individuels | Aucun nom, justificatif, hachage de pièce privée, identifiant de dossier réel |
| B — Répertoire interne d'orientation | Codes Q01–Q09 et liste des pièces à vérifier | Accès restreint, MFA, responsable identifié |
| C — Coffre privé non déployé | Originaux et métadonnées à caractère personnel, selon nécessité | Chiffrement en transit et au repos, contrôle d'accès par rôle, journal d'accès, sauvegarde protégée |
| D — Dossier de décision | Attestations internes, analyses et décisions signées | Vérification de mandat, double contrôle, piste d'audit, conservation légale déterminée |
| E — Traces d'incident | Journaux limités et registre d'incidents, données minimisées | Accès indépendant, gestion d'incident, conservation conforme au régime applicable |

**Aucun lien direct A → C.** Une référence publique ne doit pas révéler l'identité, le nom de fichier, le type sensible, le hachage ou l'existence d'une preuve personnelle. Les identifiants privés de référence, et leur table de correspondance, demeurent dans le coffre. Aucune plateforme/fournisseur réel n'est sélectionné par ce texte.

## 4. États et transitions contrôlées

Les neuf familles Q01–Q09 commencent à **NON_RECU**. Une procédure réelle future pourrait suivre :
`NON_RECU → RECU_ISOLE → EN_VERIFICATION → VERIFIE_HORS_DEPOT`, avec chemins `REJETE` ou `SUSPENDU`. Les états `EXPIRE` et `REVOQUE` sont bloquants.

| Transition | Justificatif attendu |
| --- | --- |
| NON_RECU → RECU_ISOLE | Dépôt via canal sécurisé *déjà autorisé* et accusé de réception privé |
| RECU_ISOLE → EN_VERIFICATION | Quarantaine technique, provenance contrôlée, absence de contenu malveillant, vérificateur habilité |
| EN_VERIFICATION → VERIFIE_HORS_DEPOT | Source primaire authentifiée, cohérence des dates et du périmètre, **deux contrôles humains indépendants**, aucun conflit d'intérêts |
| EN_VERIFICATION → REJETE | Motif de refus consigné, recours ou correction si applicable |
| tout état non terminal → SUSPENDU | Anomalie, conflit, indisponibilité de contrôle ou incident |
| état contrôlé → EXPIRE | Échéance ou révocation de la source non encore confirmée |
| état contrôlé → REVOQUE | Révocation de mandat, perte de confiance, fraude ou information contradictoire |

**Pas de retour automatique** de `EXPIRE` ou `REVOQUE` à `VERIFIE_HORS_DEPOT` : ouvrir une **nouvelle référence** et refaire la vérification. Une pièce rejetée ne devient pas valide par simple changement d'étiquette. L'audit logiciel présenté dans ce jalon ne peut ni recevoir les originaux ni valider les signatures.

## 5. Contrôle d'authenticité à deux personnes (proposé)

1. Le réceptionniste autorisé consigne, dans le coffre privé, la preuve de réception et un identifiant opaque **non réutilisé**; il ne juge pas la validité.
2. Le premier vérificateur effectue un examen documentaire (émetteur, période, numéro de référence, périmètre, expiration), contacte **indépendamment** l'autorité émettrice lorsque requis, et consigne méthode et résultat.
3. Le second vérificateur, indépendant du demandeur et du premier, examine la chaîne de confiance, les pouvoirs et les divergences. Aucun « approuvé » par une CI, un modèle IA, une capture GitHub ou une réponse courriel non authentifiée.
4. En cas d'ambiguïté, conflit d'intérêts, source indisponible ou discordance : **SUSPENDU / NO_GO**. Demander une vérification externe proportionnée plutôt que d'inventer l'authenticité.
5. Une fois les deux contrôles effectués, le responsable habilité peut prendre une décision **distincte** dans les limites de son mandat. Ce contrôle ne vaut ni permis électoral ni autorisation de fusion ou de publication.

Pour les originaux numériques, l'intégrité peut être vérifiée par une empreinte **gardée dans le coffre privé seulement**. Une empreinte publiée peut révéler qu'une pièce particulière est détenue : elle n'est pas publique.

## 6. Détention, expiration, purge et incidents

- **Principe de minimisation** : ne demander que les champs et pièces nécessaires, après avis juridique et inventaire.
- **Accès au besoin de connaître** : MFA, délégations limitées dans le temps, révocation rapide, journalisation et revue des accès; aucune permission de production accordée à ce stade.
- **Conservation** : durée déterminée en fonction de chaque finalité et des obligations réellement applicables, **sans durée uniforme arbitraire**; gel légal documenté lorsqu'il est requis.
- **Purge** : processus vérifié pour copies, sauvegardes, exportations et prestataires; journal technique sans copie de la pièce, avec exceptions légales.
- **Incident** : confinement, triage, protection des personnes, registre et notifications selon le régime juridique et la gravité. Une simple réversion Git ne supprime pas les copies ou courriels transmis.
- **Réexamen** : changement de titulaire, modification de SHA, contrat, mandat, droit applicable, prestataire ou découverte d'incident ⇒ reprendre les vérifications concernées.

La CAI indique que les organisations privées doivent prendre des mesures de sécurité proportionnées et détruire de manière sécuritaire les renseignements devenus inutiles, sous réserve des obligations légales. Le régime exact de Projet Nova reste à qualifier avant une mise en exploitation.

## 7. Menaces principales et réponses

| Menace | Réponse requise |
| --- | --- |
| Usurpation d'émetteur ou faux mandat | Confirmation auprès de la source primaire indépendante |
| Pièce périmée / pouvoir retiré | Expiration, liste de révocation et revalidation |
| Prétexte de « GO » par métadonnée | Machine de statut fail-closed, aucune approbation automatique |
| Consultation non autorisée | Cloisonnement, MFA, journal et alertes |
| Fuite par Git ou logs | Modèles vides, aucun identifiant réel, empreintes et originaux privés |
| Courriel usurpé / pièce jointe malveillante | Vérification indépendante, quarantaine, politique de fichiers et outils de sécurité |
| Suppression trop rapide ou conservation indéfinie | Calendrier documenté après qualification légale, gel et purge contrôlée |
| Duplicata contradictoire | Versionnement privé immuable, lien de remplacement et analyse de cohérence |
| Abus de privilège interne | Contrôle croisé, délégations limitées et séparation des fonctions |
| Indisponibilité du coffre | Sauvegarde protégée, test de restauration isolé et plan de continuité |

## 8. Critères de sortie P50J

**Livrables préparatoires** : protocole, modèle public Q01–Q09, politique de transition, validateur statique, tests non déployants et matrice d'incidents. **Aucun des livrables ne vaut un coffre réellement prêt, un contrôle juridique achevé ou un registre de preuves authentifiées.**

P50J est **achevé comme jalon de conception** lorsque ses fichiers ont été enregistrés et ses tests exécutés; il demeure **NO_GO pour collecte, dépôt, autorisation, fusion et publication**. La prochaine étape logique **P50K** sera un exercice de gouvernance et une évaluation d'impact sur la vie privée par des responsables réels avant de choisir un outil technique.

## Références de cadrage, non certificats de conformité
- CAI, entreprises : incidents et mesures de sécurité — https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/incidents-confidentialite-mesures-securite-entreprises
- CAI, entreprises : conservation et destruction — https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/conservation-destruction-renseignements-personnels
- CAI, partis politiques provinciaux — https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-pour-partis-politiques-provinciaux

**Mention expresse :** aucune donnée d'électeur, aucun justificatif signé, aucune candidature ni autorisation n'a été reçu(e) ou vérifié(e) par P50J.

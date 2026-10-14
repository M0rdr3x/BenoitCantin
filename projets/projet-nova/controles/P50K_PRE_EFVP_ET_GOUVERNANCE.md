# Projet Nova — P50K : pré-EFVP, gouvernance opérationnelle et critères fournisseur

**État : CONCEPTION / NON VALIDÉ. Date de revue : 2026-10-14. Publication, collecte et déploiement : NO_GO.**

## 1. Continuité documentaire et délimitations

P50K complète **P50J** (PR 649) sans le modifier. L'identité actuelle est **Projet Nova**; « Parti Nova » demeure un nom futur conditionnel à sa légalité et à son autorisation. Aucun statut juridique du porteur ni aucune autorisation électorale n'ont été établis. La base maîtresse **V3.40 reste inchangée**.

**P50K n'est pas une EFVP achevée et ne prouve pas qu'une EFVP obligatoire a été effectuée.** Il structure une évaluation *avant* l'engagement de prestataires ou la création d'un coffre. Une personne réellement responsable, un juriste et un spécialiste de la protection de la vie privée devront évaluer les traitements réels et signer les conclusions **hors GitHub**.

Le site existant annonce un contact volontaire minimal par **courriel**. Cela ne signifie pas que le flux technique de la messagerie, la localisation des données, les sauvegardes, les délégations ou les durées de conservation ont été audités. Toute preuve d'audit réel reste à fournir.

## 2. Qualification du régime applicable

La Loi sur la protection des renseignements personnels dans le secteur privé (Québec), dont les articles **3.3** (certains projets de systèmes ou services électroniques) et **17** (certaines communications hors Québec), prévoit des obligations d'évaluation pertinentes selon le régime applicable. Les obligations particulières des **partis politiques provinciaux** doivent être examinées séparément, selon les dispositions de la Loi électorale et de la Loi sur le privé. Les dispositions relatives aux **organismes publics** ne doivent pas être automatiquement appliquées au Projet Nova.

En conséquence, avant toute conclusion :
1. Identifier le porteur réel et son statut juridique, ses représentants habilités et la finalité du projet.
2. Inventorier tous les renseignements actuellement traités par le canal courriel et tout autre mécanisme effectif, y compris métadonnées et journaux.
3. Qualifier **chaque** situation pouvant déclencher une EFVP, avec source précise du texte applicable et avis indépendant.
4. Déterminer si un fournisseur traite ou accède aux renseignements **hors Québec**; cartographier sous-traitants, sauvegardes et assistance.
5. Documenter pour chaque flux : finalité, nécessité, transparence, fondement applicable, consentement s'il est requis, accès, durée, destruction et gestion des droits de la personne selon son régime.
6. Ne pas utiliser l'absence de demande de signatures pour conclure que les courriels ne comportent aucun renseignement personnel ou politique sensible.

## 3. Cartographie à deux périmètres

| Périmètre | État | Données potentielles / inconnues | Conclusion actuelle |
| --- | --- | --- | --- |
| **F01 — contact courriel existant** | Canal de contact déclaré public | Expéditeur, adresse électronique, objet, message, fichiers éventuellement envoyés volontairement, métadonnées du service, accès/support/backup encore à vérifier | Flux réel à auditer; aucun accès à la boîte ni preuve fournisseur reçu |
| **F02 — futur coffre de pièces** | **NON DÉPLOYÉ** | Mandats, actes, signatures, preuves financières et références juridiques seulement si nécessaires et autorisés; données sensibles potentielles | Aucune collecte, aucun stockage réel et aucun prestataire sélectionné |
| **F03 — GitHub public** | Documentation et code préparatoires | Procédures vides et métadonnées de tests synthétiques uniquement | Interdiction absolue des dossiers, noms, signatures, empreintes d'originaux et données privées |
| **F04 — logs, CI et journaux futurs** | CI de validation statique existante; registre privé éventuel non créé | Traces d'accès, erreurs, chemins, IP ou contenus selon outil; flux à vérifier | Interdiction de pièces réelles dans CI; politique de journalisation future à valider |

Le **flux F01** et le **projet F02** ne sont pas interchangeables. Une pré-EFVP destinée au coffre futur ne remplace pas l'audit des pratiques de la boîte de réception actuellement utilisée.

## 4. Méthode de pré-EFVP (sans attribution artificielle)

Phase A — cadrage : responsable réel, forme juridique, finalités, nécessité et alternatives sans collecte; cartographie des personnes concernées et des flux.

Phase B — analyse : catégories et sensibilité; volume probable **inconnu**; pays de traitement, sous-traitants, rétention et droits; contrôle juridique des hypothèses. Aucune estimation quantitative inventée.

Phase C — risques : évaluer chaque scénario **seulement lorsque la probabilité et la gravité sont motivées**. Tant que les preuves manquent, écrire `INCONNU`, et non `FAIBLE`, `ACCEPTABLE` ou `0`.

Phase D — atténuation : mesures organisationnelles, contractuelles et techniques; distinguer les mesures **proposées** des mesures **prouvées mises en œuvre**. Ne pas déduire une efficacité par simple existence dans la documentation.

Phase E — revue indépendante : consulter un professionnel de la confidentialité, un responsable de sécurité et, si nécessaire, un conseil juridique; conserver les avis et pièces dans un environnement approprié **hors dépôt**.

Phase F — décision : dossier de recommandations, risques résiduels explicitement évalués, conditions d'arrêt, responsable habilité et plan de reprise; aucune sortie `GO` produite par l'automatisation. Une décision humaine favorable ne dispense pas de légalité électorale ni de consentement requis.

## 5. Catalogue initial de 14 risques (hypothèses à vérifier)

- **R01** : renseignement politique sensible ou document personnel transmis spontanément dans le courriel actuel, avec classification insuffisante.
- **R02** : stockage, sauvegarde, assistance ou transfert hors Québec non cartographié.
- **R03** : mauvais destinataire ou transfert accidentel d'un courriel/pièce sensible.
- **R04** : compromission du compte de messagerie, hameçonnage ou détournement de session.
- **R05** : droits d'accès excessifs, départ d'un responsable ou délégation non révoquée.
- **R06** : fournisseur et sous-traitants non évalués, droit de sous-traiter sans contrôle.
- **R07** : origine falsifiée d'un mandat ou d'un document d'autorisation.
- **R08** : preuve périmée, révoquée ou liée à un périmètre différent.
- **R09** : conservation indéfinie, copies persistantes ou destruction impossible à démontrer.
- **R10** : journaux, sauvegardes, rapports CI ou dépôt Git contenant des données identifiables.
- **R11** : indisponibilité du service, perte des preuves ou restauration non testée.
- **R12** : incident non détecté, registre et notifications réglementaires non définis.
- **R13** : changement de finalité, profilage ou réutilisation des renseignements sans justification.
- **R14** : confusion entre réussite CI, statut de vérification, habilitation et autorisation officielle.

Ces 14 risques **ne sont ni constatés, ni quantifiés, ni évalués comme acceptables**; les propriétaires de contrôles sont à désigner. Chaque risque doit recevoir un scénario précis, une source, une gravité argumentée, une vraisemblance motivée, des mesures et une évaluation résiduelle avant décision.

## 6. Critères éliminatoires pour un prestataire futur (aucun choix effectué)

Un prestataire ne peut être présélectionné sans démontrer au minimum :
1. contrat et base juridique de traitement adaptés, dont confidentialité et restitution;
2. preuve du lieu de stockage, d'administration et de sauvegarde, et des sous-traitants;
3. évaluation hors Québec et protection adéquate si applicable, **avant** tout transfert;
4. contrôle d'accès granularisé, MFA et révocation;
5. chiffrement transit et repos, politiques de clés et séparation des environnements;
6. journaux d'accès minimisés et protégés, mécanisme de revue;
7. isolation des pièces et prévention de fichiers malveillants;
8. sauvegarde et restauration testables, objectifs RPO/RTO **à déterminer** et non annoncés;
9. export maîtrisé et destruction vérifiable y compris les sous-traitants;
10. procédure d'incident, coopération et délais contractuels évalués juridiquement;
11. garanties d'audit, tests de sécurité et gestion des correctifs;
12. clauses de fin de contrat, sortie et portabilité sans dépendance excessive.

Les critères sont **bloquants**, non simplement compensés par une note commerciale. Le prix, les performances et la facilité d'usage seront comparés **après** satisfaction documentée des critères éliminatoires et des besoins réels. **Aucun fournisseur n'est noté ou approuvé par P50K.**

## 7. Gouvernance des décisions et garde-fous techniques

Le propriétaire juridique des données, le responsable de confidentialité, le responsable cybersécurité, le responsable d'exploitation, le réviseur indépendant et le décideur habilité restent à identifier et à mandater **hors dépôt public**. Les incompatibilités de fonctions exigent une revue indépendante.

Interdictions maintenues :
- Aucun coffre privé, aucun formulaire, aucune signature, aucune cotisation, aucun don ou contribution, aucune collecte politique activée.
- **PR 640 : NE PAS FUSIONNER**. PR 636/638 et 645–649 : contrôle humain distinct avant fusion; aucune validation de GitHub ne prouve une autorisation juridique.
- Les portes institutionnelles et financières antérieures demeurent bloquées; P2-C0-49 EN_COURS, W0 NON_CLOTUREE, W1 NO_GO, W2–W4 NON_AUTORISEES; E26 0/20, pouvoirs 0/14 et finances 0/16, quatorze portes financières bloquantes.
- Aucun nom ni preuve réelle dans GitHub; aucune empreinte d'un document privé publiée.
- Toute situation **INCONNUE** à une porte critique entraîne **NO_GO**, sans « risque acceptable » calculé automatiquement.

## 8. Livrables et prochain jalon

Le jalon P50K produit une méthode publique de pré-EFVP, une matrice **vide d'évaluation** de 14 risques, un formulaire d'analyse de 12 critères éliminatoires, un validateur `NO_GO_AUTOMATIQUE` et des tests sur données fictives. **Il ne constitue pas un rapport EFVP signé, une autorisation de traitement ou un certificat de sécurité.**

La suite recommandée **P50L** : constituer *hors Git* les responsabilités et attestations réelles, inventorier le flux de courriel existant, faire déterminer par un juriste le régime et les EFVP obligatoires puis, seulement après, examiner les prestataires sur pièces. Tant que les éléments ne sont pas disponibles, maintenir le statut **NO_GO** sans déclencher d'action publique.

## 9. Références officielles consultées

- CAI — Loi 25, principaux changements : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25
- CAI — Utilisation et communication (entreprises) : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/utilisation-communication-renseignements-personnels
- CAI — Conservation et destruction : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/conservation-destruction-renseignements-personnels
- CAI — Incidents de confidentialité et sécurité : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/incidents-confidentialite-mesures-securite-entreprises
- CAI — Partis politiques provinciaux : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-pour-partis-politiques-provinciaux

Aucune page de référence ne prouve le statut individuel de Projet Nova, ses traitements effectifs ni les habilitations d'une personne.

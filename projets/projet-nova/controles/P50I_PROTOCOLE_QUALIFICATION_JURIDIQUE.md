# Projet Nova — P50I : qualification juridique et recevabilité des pièces

**Jalon : 14 octobre 2026 · Projet préparatoire · Statut externe NON ATTESTÉ · Décision NO_GO**

## 1. Périmètre et séparation des sources

Ce protocole est la suite de P50H (PR 647), sans effet sur les formulaires, les finances ni les publications. L'identité éditoriale active est **Projet Nova**. L'appellation **Parti Nova** n'est envisagée que pour une démarche éventuelle, sous réserve du nom disponible et d'une autorisation applicable. Les documents historiques SCQ relèvent du corpus de référence; ils ne démontrent aucun enregistrement du projet actuel.

### Trois catégories qu'il est interdit de confondre
1. **Fait public observé** : documentation officielle consultée, code GitHub ou présentation publique; toujours avec date et source.
2. **Fait privé à confirmer** : existence d'une personne morale, d'une association, d'une délégation, d'un compte, d'un mandat, d'un statut électoral ou d'une personne responsable.
3. **Décision juridique opposable** : décision écrite de l'autorité compétente, document vérifié avec portée, validité et procédure d'authentification.

Une publication, un logo, un nom de domaine, une politique interne, des statuts préparés ou des droits de fusion GitHub ne prouvent pas à eux seuls les éléments des catégories 2 et 3.

## 2. Qualification : scénarios, pas déclarations

| Situation | Ce qu'il faudrait établir | Traitement actuel |
| --- | --- | --- |
| Initiative ou collectif informel | Porteur, responsabilités, rapports contractuels, lois applicables | **Non qualifié** |
| Organisation privée structurée | Forme juridique, inscription/immatriculation si applicable, capacité d'engager l'organisation, obligations de vie privée | **Non attestée** |
| Projet de parti politique provincial | Chef et dirigeants, représentant officiel, auditeur, pièces et démarches réglementaires | **Éventuel; aucune demande présumée** |
| Parti politique provincial autorisé | Décision du DGEQ et fiche officielle REPAQ au nom exact | **Non vérifié comme autorisé** |
| Regime municipal ou fédéral | Périmètre territorial et régime législatif distinct | **Hors périmètre; renvoyer à un avis spécialisé** |

**Ne pas inférer qu'aucun parti n'existe à partir d'une recherche infructueuse.** Ne pas inférer qu'une autorisation existe à partir d'une simple intention d'utiliser le nom.

## 3. Règles officielles utiles, à recontrôler au moment de toute démarche

Selon Élections Québec, la demande provinciale d'autorisation d'un parti politique comporte notamment :
- au moins **100 signatures** de membres ayant la qualité d'électeur, sur les fiches prévues;
- un **dépôt de 500 $** selon les règles officielles;
- renseignements sur le chef, au moins deux autres dirigeants, le représentant officiel et l'auditeur;
- identification des adresses et lieux de tenue des comptes requis;
- possibilité de **réservation du nom**, distincte de l'autorisation, pour un maximum de six mois.

**Ces exigences ne déclenchent aucune collecte sur Projet Nova.** Les fichiers contenant signatures, coordonnées des électeurs, numéros de carte ou renseignements financiers doivent rester exclusivement dans un système autorisé et sécurisé, jamais Git ni un formulaire public non validé. La demande d'autorisation, les coûts ou les sollicitations éventuelles exigent un avis préalable et le respect de la loi; le présent protocole n'envoie rien à Élections Québec.

À la date de ce jalon, le **statut individuel du Projet Nova auprès du DGEQ n'a pas été confirmé par une décision officielle vérifiée**.

## 4. Privacy by design et statut des renseignements

- Les règles de protection doivent être qualifiées à partir de la **forme juridique et des traitements effectivement opérés**, y compris les messages reçus par courriel, l'hébergement, la maintenance, les sauvegardes et la sécurité.
- Pour un parti politique provincial, les dispositions précises applicables aux renseignements des électeurs peuvent différer du régime général. Ne pas promettre automatiquement les mêmes recours dans tous les régimes.
- Examiner les obligations de nécessité, de consentement, de limitation de finalité, de rétention et de destruction.
- Une communication ou un traitement de renseignements à l'extérieur du Québec peut déclencher des obligations d'évaluation des facteurs relatifs à la vie privée et d'entente écrite selon le régime applicable.
- Aucune réactivation de Formspree ou d'un fournisseur analogue; aucune collecte de signatures ou données électorales dans le présent travail.

## 5. Recevabilité : neuf familles de preuves à obtenir HORS DÉPÔT

| Code | Famille | Justificatif admissible à faire vérifier |
| --- | --- | --- |
| Q01 | Porteur et forme juridique | Acte authentique/inscription officielle ou analyse justifiée de son absence |
| Q02 | Périmètre électoral | Note indépendante qualifiant les activités et le régime provincial envisagé |
| Q03 | Dénomination | Recherche datée REPAQ et, si elle a lieu, confirmation officielle de réservation |
| Q04 | Organes et nominations | Décisions et acceptations écrites, vérifiées par une personne habilitée |
| Q05 | Financement et dépenses | Avis financier/juridique, délégations autorisées et controls de trésorerie |
| Q06 | Données personnelles | Inventaire des traitements réels, analyse d'applicabilité du régime, politique approuvée |
| Q07 | Sous-traitance et circulation | Inventaire fournisseurs, hébergement, transfert hors Québec, EFVP si requis |
| Q08 | Traçabilité et protection | Contrôles d'accès, conservation, destruction, incidents, sécurité, revue indépendante |
| Q09 | Mandat de décision | Habilitation d'autoriser une publication et séparation des responsabilités |

Un registre public n'accueille **que** l'identifiant opaque d'une preuve (si justifié), son état agrégé et le fait qu'elle doit être réévaluée. Aucun nom, signature, date de naissance, numéro de carte, adresse ou courriel individuel.

## 6. Règle de décision fail-closed

État de base de chaque Q01–Q09 : **NON_DOCUMENTE**. Les états `A_REVOIR`, `VERIFIE_HORS_DEPOT`, `REJETE` servent à la traçabilité, mais ne confèrent aucune autorisation. Toute déclaration `VERIFIE_HORS_DEPOT` doit être corroborée par un responsable réellement habilité dans un espace contrôlé.

**Le validateur de ce jalon ne délivre qu'un résultat de structure, jamais de GO.** La décision de publier, la décision de demander une autorisation provinciale et la décision d'activer une collecte sont trois décisions différentes.

## 7. Raccordement aux portes antérieures

- **B02 (P50H)** : qualification de la législation applicable; bloque les demandes, la collecte et les dépenses non autorisées.
- **B05** : confidentialité vérifiée avant ajout d'un traitement; les courriels de contact existants restent un flux à analyser.
- **B09 et B11** : mandat et décision humaine séparés des accès GitHub.
- **B12 et B14** : uniquement après déploiement réellement autorisé et exécuté, jamais avant.
- PR **640 : NE PAS FUSIONNER**. PR 636, 638, 645, 646, 647 : ne pas fusionner sans revue indépendante et pouvoir d'agir établi.
- Base maîtresse V3.40 inchangée; états P2-C0-49, W0/W1/W2–W4, E26, finances et pouvoirs antérieurs préservés.

## 8. Sources de vérification
- Élections Québec — obtention de l'autorisation : https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-une-autorisation/
- Élections Québec — REPAQ : https://www.electionsquebec.qc.ca/partis-et-autres-entites-politiques/
- Loi électorale du Québec, chapitre E-3.3 : https://www.legisquebec.gouv.qc.ca/fr/document/lc/E-3.3
- CAI — partis politiques provinciaux : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-pour-partis-politiques-provinciaux
- CAI — responsabilité des organisations privées : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/responsable-protection-renseignements-personnels-entreprise
- CAI — communication et traitement hors Québec : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/utilisation-communication-renseignements-personnels

**Nature : dossier d'instruction, non avis juridique indépendant, non dossier déposé, non enregistrement, non preuve de consentement.**

## 9. Suite recommandée — P50J
Établir une procédure confidentielle de réception de **vraies** preuves institutionnelles par des personnes habilitées, avec contrôles d'authenticité et échéances, sans déposer les justificatifs dans GitHub et sans annoncer de démarche officielle tant que le régime n'a pas été clarifié.

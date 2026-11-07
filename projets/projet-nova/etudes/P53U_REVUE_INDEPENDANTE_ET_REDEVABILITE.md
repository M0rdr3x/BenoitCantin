# Projet Nova — P53U : procédure de revue indépendante et de recevabilité des preuves

**22 octobre 2026 — cadre préparatoire, avis indépendants non obtenus, décisions financières non adoptées.**

## 1. Pourquoi P53U suit P53T

Les validations P53R (48 tests), P53S (64 tests) et P53T (56 tests) sont confirmées dans GitHub Actions. Le contrôle local d'empreinte SHA-256 de P53T peut établir une concordance d'octets à une valeur déclarée, mais **ne démontre pas** la source, l'indépendance du vérificateur, le droit de consulter l'original ou la justesse du calcul. Aucun fichier original n'a été acquis par ce programme.

P53U établit **8 contrôles successifs pour chacun des 6 organismes**, soit **48 positions procédurales**, destinées à examiner les **102 types de pièces P53Q**. Chacune mentionne le rôle responsable de la préparation et un **rôle de relecture nominalement distinct**, plus une liste d'éléments à examiner. Des rôles distincts dans un fichier informatique ne prouvent **jamais que des personnes, les entités ou leurs intérêts sont effectivement indépendants**.

## 2. Les huit étapes obligatoires

| Étape | Rôle de préparation | Éléments à vérifier |
|---|---|---|
| 1. Origine et identité de l'émetteur | Collecte documentaire | Émetteur réel, période, version, preuve de communication et autorisation |
| 2. Intégrité et chaîne de conservation | Contrôle technique | Référence fiable de hachage, contrôle des mouvements, accès aux originaux |
| 3. Droit d'accès et confidentialité | Examen juridique | Documents légalement accessibles, droits des tiers, caviardage |
| 4. Contreparties et consolidation 2024 | Examen comptable | Deux grands livres, pièces bilatérales, périmètre et éliminations préexistantes |
| 5. Emplois, conditions et continuité des services | Examen comptable | Effectifs et conditions maintenus, accès humain, droits des usagers |
| 6. Coûts complets et double compte | Examen comptable | Coûts de transition et récurrents, charges transférées, rapprochement de coûts |
| 7. Examen juridique séparé | Examen juridique | Compétence et indépendance de l'expert, conflit d'intérêts, avis signé |
| 8. Avis comptable indépendant | Examen comptable | Méthode admissible, conflit d'intérêts, preuve suffisante, avis signé |

Le **rôle de relecture prévu** pour chaque étape est REVUE_QUALITE_INDEPENDANTE. Le modèle impose une séparation *de rôles*, non une affirmation que des personnes qualifiées ont été nommées, mandatées ou ont signé des avis.

Le séquencement technique exige que les étapes précédentes soient au moins **déclarées revues** et non bloquées avant d'autoriser une nouvelle entrée déclarative. Même si les huit étapes sont toutes déclarées, leur statut demeure **« examen déclaré sans certification »** : aucune valeur comptable, identité de signataire, signature, licence professionnelle ou avis original n'est authentifié par les données.

## 3. Verrous renforcés

- **Conflit d'intérêts** : toute indication de conflit interdit une progression, y compris si un autre statut est positif; le contrôle de l'indépendance personnelle doit être réalisé hors du logiciel.
- **Droits d'accès** : les personnes chargées de l'examen ne reçoivent pas automatiquement accès aux dossiers fiscaux, au grand livre ou aux données personnelles.
- **Québec et RTC** : l'élimination des écritures interorganismes déjà effectuée en 2024 reste un point de contrôle obligatoire. Une consolidation déjà publiée ne doit pas être présentée comme une économie future.
- **Travailleurs et usagers** : les huit garanties de maintien de l'emploi, du salaire, de la qualité de service, de l'accès humain, de la continuité essentielle et des recours ne peuvent être levées par une déclaration.
- **Provenance et périmètre** : les sources municipales 2024 ne sont pas le budget provincial et ne sont pas une estimation de recettes fiscales d'un Québec souverain hypothétique.
- **Aucune certification automatique** : rejet des champs additionnels d'identité, signature, montant financier, avis prétendu certifié, acte adopté ou autorisation de fusion.

## 4. Normes de référence

Le protocole est inspiré notamment des **Global Internal Audit Standards** de l'Institute of Internal Auditors, publiées en 2024 et en vigueur depuis le **9 janvier 2025**, notamment l'indépendance organisationnelle, l'objectivité, les compétences, la protection des informations, la documentation de l'engagement et la surveillance des recommandations.

- https://www.theiia.org/en/standards/2024-standards/global-internal-audit-standards/
- https://csrc.nist.gov/glossary/term/chain_of_custody
- https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1

Il s'agit de références méthodologiques : le Projet Nova n'affirme ni être une fonction d'audit professionnelle accréditée, ni être soumis de plein droit au référentiel d'une institution étatique, ni avoir reçu des avis signés.

## 5. Utilisation

    python scripts/verifier_separation_controles_nova_p53u.py --rapport p53u_bilan.json --matrice p53u_48_controles.json
    python scripts/verifier_separation_controles_nova_p53u.py --exiger-certification-independante

Un document local de déclaration peut être passé par --declaration fichier.json. Les déclarations n'acceptent aucun nom, adresse, numéro, URL privé, montant de projet ou signature cryptographique : elles indiquent seulement les rôles prévus et les **états non certifiés**. Les sorties publiques restent agrégées et ne divulguent ni code institutionnel d'une déclaration ni dossier financier sensible. Les entrées du programme ne contiennent aucun acte d'envoi, de déploiement, de publication ou de validation juridique.

Code 0 = structure conforme, **pas conformité comptable ou juridique**; code 2 = incohérence ou fichier existant; code 3 = refus attendu d'une demande de certification par ce système.

## 6. État et continuité

**NO_GO_AUTOMATIQUE** : aucun original primaire reçu et authentifié, aucune indépendance personnelle vérifiée, aucun avis juridique ou comptable signé, aucune économie opérationnelle certifiée, aucun taux fiscal adopté. Les preuves F01–F20 et les 1 320 valeurs financières Nova demeurent inconnues. Les projets de demande P53R ne sont pas envoyés; la PR #673 reste en brouillon, main intacte, SINJIRA inchangé.

Suite à envisager : P53V pourrait prévoir une **réconciliation formelle des constats bloquants et des vérifications croisées de cohérence documentaire**, toujours sans prétendre remplacer une vérification professionnelle externe.

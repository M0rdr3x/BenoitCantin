# Projet Nova — P53T : protocole d'intégrité locale et chaîne de conservation des preuves

**22 octobre 2026 — étude candidate, aucune pièce financière primaire réellement authentifiée.**

## 1. Avancement matériel

Le protocole P53T relie les **six dossiers** d'organismes réels à l'inventaire **P53Q de 17 pièces chacun (102 positions)**, aux **six projets de demande non envoyés P53R** et aux **66 positions de suivi P53S**. Il va au-delà d'une grille déclarative : un outil Python peut désormais calculer **réellement** une empreinte SHA-256 à partir des octets d'un fichier local explicitement fourni, la comparer à une référence déclarée et classer le résultat.

Ce contrôle de concordance est **technique et local**. Il ne prouve ni qui a émis le document, ni la date authentique de sa création, ni sa portée juridique, ni la sincérité de son contenu comptable. Le NIST distingue explicitement l'intégrité donnée par un hash seul de l'authentification de la source et recommande une véritable chaîne de conservation avec contrôle d'accès et journalisation.

Références méthodologiques : 
- NIST, définition de la chaîne de conservation : https://csrc.nist.gov/glossary/term/chain_of_custody
- NIST IR 8387, *Digital Evidence Preservation* : https://nvlpubs.nist.gov/nistpubs/ir/2022/NIST.IR.8387.pdf
- NIST SP 800-175B Rev. 1, limites de la fonction de hachage seule : https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-175Br1.pdf

Les référentiels méthodologiques ne remplacent **pas** une opinion juridique sur l'accès aux dossiers québécois, et ne transforment pas le projet Nova en service public accrédité.

## 2. Règles techniques et sécurité

L'utilisateur habilité doit fournir volontairement un fichier JSON de manifeste et une **racine locale**. Chaque entrée associe un code d'organisme, un type de pièce P53Q, un chemin relatif sous cette racine, l'empreinte déclarée de référence, une date de collecte déclarative au format UTC, une catégorie de preuve, un rôle de collecte et un rôle de relecture distinct, des droits d'accès et un journal de mouvements. Les mouvements comprennent réception, copie contrôlée, consultation et transfert, avec horodatage croissant et finalité de manipulation.

Le programme vérifie structure, chemins, séquencement, rôles, doublons, algorithme de hachage et concordance d'octets. Les chemins absolus, traversées de dossiers, liens symboliques, fichiers non réguliers et fichiers de plus de 4 MiB sont **refusés**. Les fichiers marqués RESTREINT sont **ignorés** et leur contenu n'est pas lu. L'absence d'autorisation légale ne doit jamais être contournée en modifiant une étiquette de confidentialité.

Les journaux, rôles, dates et empreintes fournis par l'opérateur sont **des déclarations** : aucun contrôle de signature électronique, aucune authentification d'émetteur et aucune expertise indépendante ne sont effectués automatiquement. Un hash peut établir que les octets consultés correspondent à la valeur annoncée, mais cette référence peut elle-même avoir été produite par une partie non habilitée.

## 3. Flux probatoire à accomplir hors GitHub

Pour passer de « concordance des octets » à une preuve financière auditable, le responsable habilité devra :
1. Confirmer le **droit de recevoir et d'examiner** le document, les règles de confidentialité, les secrets commerciaux et les droits des tiers.
2. Vérifier la provenance auprès de l'organisme ou de l'émetteur, obtenir une **preuve de communication** ou signature vérifiable et identifier les versions et rectifications.
3. Consigner dans un référentiel documentaire **protégé et à accès restreints** tous les détenteurs réels, contrôles d'accès, horodatages de collecte, transferts et motifs. Une chaîne de conservation affichée seulement dans un JSON GitHub ne peut être réputée authentique.
4. Faire lire et rapprocher les deux grands livres, contrats, factures et paiements, avec **contreparties identifiées et périmètre de consolidation**.
5. Pour **Ville de Québec–RTC**, interdire la seconde élimination d'opérations réciproques déjà éliminées dans les états consolidés.
6. Contrôler l'absence de suppressions d'emplois, de dégradation des services essentiels et de transferts de charges vers les ménages ou entreprises.
7. Obtenir des avis **indépendants, datés et réellement signés** avant toute comptabilisation d'économie opérationnelle; séparer Québec dans le Canada et Québec souverain hypothétique, sans addition des deux régimes.

L'outil actuel ne remplit automatiquement **aucune** de ces décisions humaines.

## 4. Exécution

    python scripts/verifier_integrite_locale_nova_p53t.py --bilan p53t_bilan.json --inventaire p53t_102_positions.json
    python scripts/verifier_integrite_locale_nova_p53t.py --manifeste chemin/local/manifest.json --racine-preuves chemin/local/preuves --bilan rapport_local.json
    python scripts/verifier_integrite_locale_nova_p53t.py --exiger-authentification-ou-economie

Le premier mode génère un inventaire neutre, tous les documents étant **NON_PRESENTE**. Le second mode, réservé à un opérateur ayant le droit de consulter les fichiers, effectue de véritables comparaisons locales et ne publie qu'un **compte agrégé** de correspondances, désaccords et fichiers restreints non consultés. Il ne divulgue dans le bilan ni chemin d'original, ni empreinte, ni code de personne, ni montant. La racine et le manifeste local doivent rester **hors dépôt Git**, et aucun document confidentiel ne doit être transmis au CI.

Code **0** : exécution structurelle ou concordance terminée **sans certification**; code **2** : entrée invalide ou sortie existante; code **3** : refus d'une demande d'authentification financière automatique. Les tests créent exclusivement des fichiers synthétiques locaux, jamais de preuve supposée gouvernementale.

## 5. Statut de décision

**NO_GO_AUTOMATIQUE** : 0 preuve de source certifiée, 0 signature d'émetteur validée, 0 revue indépendante validée, 0 économie budgétaire certifiée, 0 demande d'accès envoyée par le protocole, F01–F20 non validées, 1 320 valeurs fiscales inconnues, aucune décision de fusion sur main, aucune suppression de postes ou de services.

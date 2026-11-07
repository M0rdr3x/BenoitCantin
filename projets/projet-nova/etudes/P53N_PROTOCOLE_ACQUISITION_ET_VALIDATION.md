# Projet Nova — P53N : protocole d'acquisition et de validation des pièces financières

**22 octobre 2026 — procédure candidate, sans demandes expédiées, documents acquis ni économies certifiées.**

## 1. Continuité des jalons

P53N fait suite au registre P53M : **deux régimes exclusifs** (Québec dans le Canada, Québec souverain hypothétique) × **six catégories** (achats, formalités, énergie, entretien, licences, contrats) = **douze fiches de préparation**. Chaque fiche définit douze familles de pièces justificatives, soit **144 emplacements documentaires prévus**, non 144 documents détenus ou 144 demandes d'accès déposées.

Les 1 344 organismes municipaux observés dans l'extraction MAMH 2024 et les 26 dossiers de rapprochement P53K sont conservés comme contexte vérifiable, sans présumer qu'ils relèvent du même périmètre de dépense. Aucune somme comptable n'est ajoutée aux budgets du Québec 2026–2027 ni utilisée pour imaginer des économies ou des recettes fiscales.

## 2. Ordre opérationnel avant toute dépense ou proposition d'accès

1. **Définir la compétence** : organisme réellement responsable, statut juridique du document, habilitation de la personne sollicitant l'information et périmètre de l'exercice 2024.
2. **Repérer les publications existantes** : budgets, comptes, rapports d'audit, indicateurs, contrats et engagements disponibles légalement. Un lien candidat n'est pas une preuve de provenance authentifiée.
3. **Préparer les documents à obtenir** : nom fonctionnel, période, poste, nature de la pièce et justification. Demander seulement les informations nécessaires; ne pas solliciter de renseignements personnels sans fondement juridique.
4. **Faire décider par un responsable habilité** : choix de l'organisme destinataire et examen juridique, y compris les limites à la communication. Aucune demande n'est transmise par P53N.
5. **Distinguer demande préparée, envoi, réponse, refus** : ces événements ne sont reconnus qu'après vérification réelle; les déclarations locales ne peuvent servir d'attestation.
6. **Conserver et authentifier hors GitHub** : originaux complets, dates et versions, preuve de transmission et de réception, empreintes calculées sur les fichiers eux-mêmes, droits d'accès, traçabilité des corrections et inventaire des restrictions.
7. **Contrôle indépendant** : vérifier cohérence des périmètres, coût complet et transferts indirects, changement de période, chevauchements, investissements, maintien des effectifs et huit garanties de services de P53L.
8. **Décision ultérieure seulement** : évaluer des économies budgétaires vérifiées et un éventuel pouvoir d'achat, sans jamais utiliser une élimination de consolidation comme trésorerie disponible.

## 3. Encadrement légal des demandes

Au Québec, la demande d'accès à des documents administratifs doit être suffisamment précise et dirigée vers le responsable compétent. La publication préalable doit être vérifiée; une demande peut nécessiter le traitement d'exceptions, la protection de renseignements personnels et un recours. Les délais légaux commencent à la **réception effective** d'une demande, pas à la préparation informatique du présent registre. Les règles et organismes compétents doivent être revalidés lors du dépôt.

Références publiques vérifiées :
- https://www.quebec.ca/acces-information
- https://www.quebec.ca/gouvernement/travailler-gouvernement/normes-gouvernance-pratiques-internes/protection-des-renseignements-personnels/acces-aux-renseignements-personnels/reperage-documents
- https://www.cmq.gouv.qc.ca/fr/verification-municipale/notre-mandat-en-bref
- https://www.tresor.gouv.qc.ca/performance-de-letat/cadre-de-gestion-de-ladministration-gouvernementale/evaluation-de-programme

Ces références décrivent les institutions en vigueur; elles **ne démontrent pas** la validité juridique d'un futur ordre constitutionnel.

## 4. Classification probatoire et sécurité

Les états autorisés pour une fiche déclarative sont NON_DEMANDE, REPERE_PUBLIC_DECLARATIF, DEMANDE_PREPAREE_NON_ENVOYEE, ENVOI_DECLARE_NON_VERIFIE, REPONSE_DECLAREE_NON_VERIFIEE et REFUS_DECLARE_NON_VERIFIE. **Aucun état n'implique une validation de preuve.** Le modèle refuse explicitement les valeurs CERTIFIE, AUTHENTIFIE, DEMANDE_ENVOYEE_VERIFIEE ou ECONOMIE_PROUVEE.

Le programme n'accepte ni adresse, nom d'employé, courriel, référence de facture, numéro de compte, montant individuel ni lien de document privé dans les déclarations. Il ne sauvegarde que la structure et les états non attestés; les rapports CI contiennent uniquement un bilan agrégé et le registre modèle. Les garanties inconnues bloquent toute décision, une garantie violée bloque immédiatement l'examen. Les deux régimes ne sont jamais cumulés dans le calcul de ressources fiscales.

## 5. Commandes

    python scripts/preparer_acquisition_preuves_nova_p53n.py --rapport p53n_bilan.json --registre p53n_plan_12.json
    python scripts/preparer_acquisition_preuves_nova_p53n.py --exiger-preuves-certifiees

Les déclarations facultatives, sans pièce réelle, peuvent être évaluées via --declaration chemin-local.json. Les sorties existantes ne sont pas écrasées. Code **0** : contrôle de structure réussi, **2** : entrée invalide, **3** : refus de certification attendu. Aucun appel réseau, demande envoyée, collecte de données personnelles ou changement à la fiscalité n'est exécuté.

## 6. État de décision

**NO_GO_AUTOMATIQUE** : 0 demande d'accès effectivement déposée par ce jalon, 0 original authentifié, 0 avis indépendant validé, aucune économie démontrée, F01–F20 non validées, 1 320 variables financières inconnues. Aucune fusion sur main, aucune norme activée, aucune réduction d'emploi et aucun transfert de frais vers les citoyens.

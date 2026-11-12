# Projet Nova — P53K : chaîne de preuve pour opérations interorganismes (2024)

**22 octobre 2026 — étude candidate sans collecte effective, certification ni adoption.**

## Travail réalisé

P53K hérite du contrôle P53J des **1 344 organismes** MAMH 2024, de la version révisée P53I et des **25 priorités** historiques P53H. Il ouvre un **26e dossier séparé** pour Saint-Valère (39135), arrivée dans P53I. Ces dossiers sont des **organismes à examiner**, pas 26 transactions identifiées.

L'outil génère le registre des 26 dossiers, avec leur statut **PIECES_PRIMAIRES_A_OBTENIR**. Il peut lire, uniquement en local, des fiches de métadonnées déclaratives à deux écritures : codes d'organismes, références d'écritures, postes compatibles, dates 2024, montants CAD identiques, références de documents par SHA-256, déclaration du périmètre de consolidation et d'une éventuelle élimination antérieure.

Les contrôles vérifient la **forme** et la cohérence interne des informations saisies. Ils **ne lisent ni n'authentifient les pièces originales**; une empreinte déclarée ne prouve pas la possession d'un document. Même un dossier techniquement cohérent conserve le statut **CANDIDAT_ARITHMETIQUE_NON_CERTIFIE**, sans montant éliminable, économie budgétaire ni recette fiscale.

## Pièces primaires et contrôle humain obligatoires

Demander à chaque organisme concerné, avec les autorisations appropriées : grand livre payeur et bénéficiaire, résolution ou entente, facture ou appel de quote-part, justificatif de paiement, états de consolidation et leur périmètre, écritures d'élimination déjà enregistrées, corrections et ajustements de période. Vérifier les identités juridiques et les doubles emplois entre organismes contrôlés, y compris les comptes déjà consolidés; obtenir une **revue indépendante écrite et signée**. Les originaux et métadonnées de transactions doivent rester dans un espace documentaire autorisé, hors GitHub et hors artéfacts CI.

Le programme distingue **pièces manquantes**, **périmètre inconnu**, **opération déclarée déjà éliminée**, **opération hors périmètre**, **candidat arithmétique non certifié**. Une source incohérente ou une déclaration invalide entraîne refus; un résultat complet de comparaison ne démontre pas une réduction de dépense pour les contribuables.

Références officielles :
- https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/manuel
- https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/normes-comptables
- https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier

## Utilisation

- Exécuter Python scripts/preparer_controles_probatoires_nova_p53k.py avec --rapport p53k_bilan.json et --export-registre p53k_registre_26.csv.
- Ajouter --dossier avec le chemin local d'une fiche JSON préparée dans un espace autorisé si une analyse déclarative est requise.
- Ajouter --exiger-certification pour vérifier le refus avec code de retour **3**.
- Code **0** : contrôle de forme reproductible réussi; **2** : erreur ou source incohérente; **3** : refus de certification.

Aucune sortie existante n'est écrasée. Les artéfacts CI ne contiennent que des bilans agrégés, jamais les fiches ni les références des transactions.

## Décision

**NO_GO_AUTOMATIQUE** : aucune pièce nouvelle obtenue, 0 appariement certifié, 0 économie démontrée, 20 preuves fiscales F01–F20 non validées, 1 320 montants Nova inconnus, aucun taux adopté et aucun avis indépendant signé.

Aucune addition des données municipales 2024 au budget québécois 2026–2027; aucune fusion de PR, modification de main ou de SINJIRA, collecte, paiement, suppression de postes ou publication d'une norme adoptée.

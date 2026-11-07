# P53W — Premier dossier pilote fondé sur des pages publiques officielles

Exercice financier 2024, dossier Ville de Québec 23027 et RTC T0088. Vérification documentaire effectuée le 24 octobre 2026. Cette étude ne constitue ni un audit institutionnel indépendant ni une preuve comptable transactionnelle.

## Publications officielles
- Rapport financier municipal 2024 : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf
- Répertoire de rapports financiers de la Ville : https://www.ville.quebec.qc.ca/apropos/profil-financier/rapport-financier.aspx
- Publication MAMH repérée, non comparée octet par octet à celle de la Ville : https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf

Le rapport municipal comprend 230 pages dans le visualiseur consulté. Les pages visibles 35 (index PDF 34) et 197 (index PDF 196) ont été inspectées. Aucun PDF n'a pu être téléchargé dans l'espace local de ce projet : empreinte SHA-256 exacte et correspondance avec la version MAMH inconnues. Ces informations sont explicites dans le JSON, jamais remplacées par un zéro ou un faux hash.

## Huit observations traçables
- F01, page couverture index 0 : exercice terminé le 31 décembre 2024.
- F02, index 34 / imprimée 35, note 2A : le RTC et la Société municipale d'habitation Champlain (SOMHAC) sont dans le périmètre comptable des organismes contrôlés.
- F03, index 34 / imprimée 35, note 2A : comptes consolidés ligne par ligne.
- F04, index 34 / imprimée 35, note 2A : les opérations interorganismes et soldes réciproques sont déjà éliminés lors de cette consolidation.
- F05, index 196 / imprimée 197 : les notes de rapprochement des prévisions budgétaires sont marquées « Non audité ».
- F06, index 196 / imprimée 197, note 2 : les opérations entre compétences d'agglomération, locales et organismes contrôlés ont également été éliminées dans les budgets présentés.
- F07, index 196 / imprimée 197, note 3 : la résolution CA-2023-0771 est citée pour le budget RTC 2024; l'original de la résolution n'est pas vérifié.
- F08, répertoire de la Ville : le rapport 2024 figure parmi les rapports antérieurs.

Ne jamais généraliser la mention « Non audité » de la page 197 à l'ensemble des états financiers. La mention de la SOMHAC n'ajoute pas un organisme au classement historique des six dossiers P53P.

## Ce que ces observations ne démontrent pas
La mention de consolidation et d'élimination ne fournit aucun appariement de grand livre ou d'opération précise; il est incorrect de présenter les montants interorganismes comme des économies à réaliser une deuxième fois. Le document ne suffit pas à établir des économies évitables, des coûts de transition, des impacts sur les emplois/services ou le budget du Québec souverain hypothétique.

Six vérifications restent obligatoires : authenticité de la version du PDF; comparaison des éditions Ville/MAMH; grands livres et pièces bilatérales; détail des écritures déjà éliminées; préservation des travailleurs et des services; avis comptable et juridique indépendant. Toutes sont NON_RESOLUE_BLOQUANTE.

## Exécution
    python scripts/constituer_dossier_pilote_nova_p53w.py --bilan p53w_bilan.json --dossier p53w_pilote.json
    python scripts/constituer_dossier_pilote_nova_p53w.py --exiger-gain-certifie

La commande contrôle la cohérence du dossier de recherche et ses ancrages. Elle ne télécharge pas le PDF, n'effectue pas de vérification cryptographique de version, n'acquiert aucun original confidentiel ni n'authentifie la source elle-même. Tests sans réseau avec seules données publiques paraphrasées. Les déclarations locales sont expressément NON AUTHENTIFIEES. Code 0 : structure conforme; 2 : entrée invalide; 3 : refus de certification.

Décision : NO_GO_AUTOMATIQUE, zéro économie certifiée, aucun nouveau taux fiscal adopté, maintien des protections travailleurs et services, zéro fusion autorisée. Le pilote concerne les comptes municipaux 2024, pas les deux régimes fiscaux distincts de Projet Nova.

# Projet Nova — P53O : matrice de sources publiques et ordre de vérification

**22 octobre 2026 — étude candidate, non adoptée, sans acquisition ni certification financière.**

## Résultat

Sept **pages institutionnelles officielles** ont été repérées, orientant les recherches sur les marchés publics (SEAO), l'information municipale (MAMH), la performance gouvernementale (SCT), l'audit municipal (CMQ), et le droit d'accès (CAI / gouvernement du Québec). Ces adresses sont des **portes d'entrée**, pas les documents transactionnels originaux, et ne permettent pas de conclure qu'une dépense précise est évitable. Aucune série de contrats, aucune facture et aucune pièce primaire de 2024 n'a été téléchargée, auditée ou authentifiée par P53O.

Le programme produit une matrice de **12 dossiers** (2 régimes hypothétiques comparés × 6 familles P53L–P53M). Chaque dossier possède une liste de sources pertinentes et **six phases procédurales** non commencées. L'ordre des phases reflète des **préalables de preuve**, pas un classement financier, ni une accusation de dépense inutile.

## Sources vérifiées en tant que pages d'orientation

- **SEAO / Données Québec** : https://www.donneesquebec.ca/recherche/dataset/systeme-electronique-dappel-doffres-seao — jeux de données sur les contrats, dépenses supplémentaires et informations finales; le contenu d'une publication ne prouve pas le coût complet ni une dépense évitable.
- **Portail administratif du SEAO** : https://www.quebec.ca/gouvernement/services-organisations-publiques/services-transformation-numerique/systeme-electronique-dappel-doffres-seao — cadre de publicité applicable aux donneurs d'ouvrage concernés, sous réserve du type de contrat.
- **Rapports financiers MAMH** : https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier — **uniquement pour les organismes municipaux visés**; les rapports peuvent être corrigés et mis à jour; ils ne sont pas les grands livres de tous les ministères du Québec.
- **Performance de l'État — Secrétariat du Conseil du trésor** : https://www.tresor.gouv.qc.ca/performance-de-letat — cadre de gestion, programmes, résultats, audits et reddition de comptes, **pas un registre universel d'écritures**.
- **Audit municipal — Commission municipale du Québec** : https://www.cmq.gouv.qc.ca/fr/verification-municipale/questions-frequentes — méthodologie d'efficacité, d'efficience et d'économie; une page générale ne remplace pas un audit financier signé spécifique.
- **Commission d'accès à l'information** : https://www.cai.gouv.qc.ca/acces-documents-organismes-publics/citoyens-acces-documents-publics/comment-acceder-documents-organismes-publics — demande au responsable de l'organisme détenteur, restrictions possibles et recours en cas de refus.
- **Accès à l'information, Québec.ca** : https://www.quebec.ca/acces-information — procédure publique de demande. Le délai général est de 20 jours après réception, avec prolongation possible de 10 jours selon les conditions applicables; préparer une fiche P53O **ne déclenche aucun délai**.

L'existence de l'interface publique ne garantit pas qu'un document particulier est communicable, accessible sans frais, archivé dans cette page ou pertinent pour un organisme donné. Les marchés publics de 2024 et les autres données ouvertes devront être interrogés sur la bonne période, la bonne entité et la bonne version, puis conservés et hachés dans un espace autorisé pour être vérifiés.

## Six phases de priorité procédurale

1. **P0 — Identifier l'organisme** : compétence juridique, détenteur de la pièce, pouvoir réel et périmètre de consolidation. Le Québec souverain est un régime hypothétique : les institutions actuelles ne créent aucune compétence future par simple analogie.
2. **P1 — Consulter les documents publics existants** : vérifier date, exercice, jeu de données, version, portée, organisme et statut de publication.
3. **P2 — Répertorier les pièces primaires encore absentes** : facture, contrat, avenants, grand livre, indicateurs de qualité, coût de transition et décompte des transferts.
4. **P3 — Vérifier les droits d'accès** : document détenu par quel organisme, restrictions commerciales, renseignements personnels, droits de tiers et éventuel cadre de demande écrite.
5. **P4 — Tester les conséquences** : huit protections P53L concernant les emplois, les conditions de travail, l'accès humain, les services essentiels et les citoyens; mesurer les coûts complets et les coûts transférés.
6. **P5 — Examiner par expertise indépendante** : revue signée, règles budgétaires et compétences; une estimation positive n'est pas une économie certifiée.

Les six phases sont **A_REALISER** dans chacune des 12 fiches; un état « page repérée » est déclaratif dans toute fiche facultative et ne devient jamais une preuve vérifiée. Le code interdit qu'un lien ajouté arbitrairement se fasse passer pour une source institutionnelle autorisée.

## Usage et limites

    python scripts/prioriser_sources_officielles_nova_p53o.py --bilan p53o_bilan.json --matrice p53o_matrice_12.json
    python scripts/prioriser_sources_officielles_nova_p53o.py --exiger-economies-certifiees

Des déclarations de consultation locales, sans URL ni document, peuvent être évaluées par --declaration. Les fichiers confidentiels ne sont ni lus ni publiés dans la CI. Code 0 : contrôle de structure seulement, 2 : incohérence / sortie existante, 3 : **REFUS strict** de certifier des économies. Aucun fichier existant n'est écrasé.

**NO_GO_AUTOMATIQUE** : 20 preuves F01–F20 non validées, 1 320 paramètres financiers inconnus, aucune économie certifiée, aucun taux fiscal adopté, aucune suppression de personnel et aucune réduction des services autorisée. P53O ne modifie pas main, le site public ni SINJIRA; la PR #673 reste en brouillon.

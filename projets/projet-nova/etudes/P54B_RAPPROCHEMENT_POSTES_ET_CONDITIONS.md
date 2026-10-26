# Projet Nova — P54B : comparabilité des postes financiers (exercice 2024)

**24 octobre 2026.** P54B se fonde sur les captures publiques réellement réalisées dans P53Z et P54A (GitHub Actions 40113700739 et 40116065853), non sur un jeu fictif de comptes.

## Sources déjà constatées
- Ville de Québec, rapport 2024 : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf — 230 pages, SHA-256 de la copie HTTPS b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399
- MAMH, publication assemblée 2024 pour organisme 23027 : https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf — 177 pages, SHA-256 de la copie HTTPS 4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00
- P54A a retenu douze candidats de pages similaires, par exemple indices PDF 14 Ville / 173 MAMH et 145 Ville / 146 MAMH, sans établir leur identité juridique ou leur concordance comptable.

Ces empreintes sont celles des fichiers capturés aux dates consignées, pas des signatures officielles d'émetteur ni une garantie que les versions restent inchangées à l'avenir. P54B doit recapturer les sources et recalculer directement les empreintes octet par octet; si une édition change, il refuse de transférer automatiquement les correspondances de P54A à cette nouvelle édition.

## Normes et catégories pertinentes
Le MAMH précise que les municipalités appliquent les normes canadiennes du secteur public et consolident les entités contrôlées :
https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/normes-comptables

Les documents du ministère peuvent contenir des renseignements financiers audités et d'autres renseignements non audités et faire l'objet d'une nouvelle transmission :
https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier

Référentiel historique pour la présentation 2024 (ne pas appliquer rétroactivement une norme entrée en vigueur en 2027) :
https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/manuel_information_financiere/manuel_complet.pdf

## Les huit contrôles requis pour chaque paire

1. Même **exercice et période** : valeurs 2024 réelles, et non 2023, estimation ou période différente.
2. Même **entité et périmètre de consolidation** : Ville, RTC, SOMHAC, agglomération, activités locales, etc.
3. Même **base comptable et convention** : traitement et conciliation fiscale, charges et transferts.
4. Même **statut d'audit** : ne pas comparer une prévision non auditée comme une valeur certifiée.
5. Même **devise, unités et signe** : CAD, milliers ou dollars, parenthèses négatives et colonne.
6. Même **libellé, rubrique et note** : sens comptable, ventilations et reclassements.
7. Même **état des opérations réciproques** : les écritures Québec–RTC déjà éliminées ne deviennent jamais une nouvelle économie.
8. **Effets complets et garanties** : emplois, conditions de travail, tiers payeurs, coûts de transition et continuité des services.

Les 12 paires multipliées par huit contrôles donnent **96 positions en attente**, statut NON_INSTRUIT. Cette matrice ne constitue pas 96 écarts prouvés.

## Mesure lexicalement descriptive

Le logiciel calcule, page par page, le nombre de jetons numériques extractibles, leurs occurrences communes, leurs occurrences non communes et leur coefficient de recouvrement de Dice. Un jeton peut être une année, un numéro de page, un code administratif, un pourcentage ou une somme financière. Aucune classification automatique comme « montant » n'est acceptable.

Le bilan public ne contient aucun jeton ou chiffre de poste brut, aucun nom de personne, et aucun extrait de page. Les PDF sont lus en mémoire par le processus et ne sont pas conservés dans les artefacts CI.

Un fort recouvrement numérique **ne prouve pas** l'identité de deux rubriques comptables, et un faible recouvrement **ne démontre pas** une anomalie. Les indices de pages proposés par P54A restent des indices PDF commençant à zéro, pas les numéros imprimés.

## Commandes

Inventaire des contrôles, sans réseau :

    python scripts/comparer_postes_financiers_nova_p54b.py --bilan p54b_neutre.json --matrice p54b_matrice.json

Nouvelle mesure, uniquement sur copies strictement identiques aux captures P53Z :

    python scripts/comparer_postes_financiers_nova_p54b.py --comparer-publications --bilan p54b_mesures.json

Refus explicite de certifier une comparabilité comptable :

    python scripts/comparer_postes_financiers_nova_p54b.py --exiger-concordance-comptable

Codes de retour : 0 pour conformité structurelle / comparaison lexicale effectuée, 2 pour erreur de validation, 3 pour refus de certification, 4 pour copies absentes, modifiées ou illisibles. Un workflow CI vert ne prouve pas automatiquement l'aboutissement de la mesure réelle : consulter les champs comparaison_lexicale_des_nombres_executee et deux_copies_conformes_aux_empreintes_P53Z.

## Verrous de décision

Le projet ne dispose pas des grands livres bilatéraux, pièces de paiement, dossiers de consolidation, preuves de coûts réellement évitables ni avis juridiques/comptables indépendants originaux signés permettant d'annoncer une économie. Le maintien de la main-d'œuvre et des services essentiels est une contrainte explicite. Les scénarios « Québec dans le Canada » et « Québec souverain hypothétique » ne sont jamais additionnés ou traités comme un seul régime fiscal.

**NO_GO_AUTOMATIQUE** — aucun montant financier certifié, aucune économie adoptée, aucun taux fiscal arrêté, aucune fusion main ni modification de SINJIRA.

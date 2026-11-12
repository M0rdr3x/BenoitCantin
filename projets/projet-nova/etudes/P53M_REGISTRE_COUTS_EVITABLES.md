# Projet Nova — P53M : registre de coûts évitables et preuves exigées

**22 octobre 2026 — étude candidate et non adoptée.**

## Nouvelle architecture

Les six pistes P53L sont déclinées en 12 fiches : six pour le Québec dans le Canada et six pour un Québec souverain *hypothétique*. Elles ne représentent pas 12 mesures adoptées ni 12 économies. Une comparaison entre régimes ne peut additionner deux simulations alternatives.

Le registre conserve la traçabilité des 1 344 organismes municipaux du fichier MAMH 2024 (P53I–P53J) et des 26 dossiers à instruire (P53K) sans les traiter comme les dépenses du budget québécois 2026–2027. Les données manquantes sont nulles et non égales à zéro.

## Pièces et critères d'examen

Chaque fiche requiert le périmètre de la dépense, le poste budgétaire, la compétence juridique, les réalisations comptables, contrats et factures, les volumes de service, les coûts initiaux et récurrents, les coûts reportés sur d'autres acteurs, la comparabilité, les indicateurs avant-après, la consultation des employés/usagers, le contrôle anti-double-compte et une expertise indépendante.

Pour les six familles — achats groupés, formalités, énergie/bâtiments, entretien préventif, licences et contrats — P53M propose quatre indicateurs opérationnels à mesurer. Ces noms d'indicateurs ne sont ni des observations ni des cibles validées.

Huit garanties P53L restent obligatoires : protection des postes, des heures et conditions de travail, maintien de la qualité et des délais, accès humain, continuité des services essentiels et préservation des droits. Une valeur NON impose le refus, INCONNU empêche toute conclusion. Des cases OUI auto-déclarées ne constituent pas une preuve indépendante.

## Distinction des niveaux de résultat

Une fiche peut être une proposition à documenter, une déclaration avec pièces manquantes, un scénario absent ou une hypothèse positive **non certifiée**. Le programme contrôle la structure des fiches et réutilise les tests financiers conservateurs P53L, mais **n'acquiert, ne lit et n'authentifie aucun contrat ni grand livre original**. Il refuse les postes budgetaires répétés dans le même périmètre et le même régime.

Les résultats publics sont agrégés sans identifiant ni montant individuel, même pour des simulations. Aucune élimination de consolidation, variation statistique ou diminution d'un transfert n'est assimilée automatiquement à une véritable économie de trésorerie. Les pièces originales et avis d'audit doivent être traités dans un espace documentaire autorisé, hors GitHub.

## Vérification technique

    python scripts/construire_registre_couts_evitables_nova_p53m.py --bilan p53m_bilan.json --registre p53m_registre_12.json
    python scripts/construire_registre_couts_evitables_nova_p53m.py --exiger-certification

Sortie 0 : registre généré et contrôles de structure satisfaits, **pas certification**. Sortie 2 : erreur, entrée incohérente ou écrasement refusé. Sortie 3 : refus explicite de certification malgré des scénarios hypothétiques. Aucun fichier de sortie existant n'est remplacé.

## Conclusion

**NO_GO_AUTOMATIQUE.** Les 20 pièces F01–F20 de la réforme fiscale et les 1 320 champs financiers Nova demeurent non validés ou inconnus. Zéro gain opérationnel démontré, aucun taux adopté, aucune réduction de personnel autorisée, aucune fusion de la PR ou modification de la documentation publique officielle. Seuls les formulaires de contrôle candidats et leurs tests sont ajoutés.

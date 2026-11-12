# P54N — Passation opérationnelle aux vérificateurs habilités

**Projet Nova — 24 octobre 2026.** P54N transforme la chaîne documentaire P54D–P54M en un dossier de travail structuré destiné à une transmission future **uniquement après autorisation humaine**. Aucun contact, contrat ou avis n'est créé.

## Références d'origine

Le workflow P54M #40141896102 a réussi 72 tests. P54E a répertorié quatre occurrences indéterminées parmi cinq occurrences numériques lexicales non appariées : Ville de Québec index PDF 102, zone FIN, dossier P54E-V-001; MAMH index PDF 162 zone DEBUT dossier P54E-M-001; MAMH index PDF 162 zone FIN dossiers P54E-M-002 et P54E-M-003. Ces indices sont à base zéro et les zones ne localisent pas le caractère exact. L'observation distincte année/date probable n'est pas résolue.

Ces observations ne sont pas quatre anomalies financières démontrées. La portée des rapports étudiés concerne la ventilation des dépenses mixtes locales et d'agglomération et le R.A.V.Q. 1435, non la certification du budget Nova ou d'économies fiscales hypothétiques.

## Trois livrables publics

Le générateur scripts/preparer_passation_humaine_nova_p54n.py produit :

- p54n_dossier_passation.json — quatre fiches P54E, liens vers les deux PDF publics, index PDF, zones, dix tâches par dossier et critères de réception.
- p54n_instructions_verificateurs.md — instructions lisibles pour un examinateur habilité, comptable et juriste à mandater, et contre-reviseur indépendant.
- p54n_bilan_neutre.json — statistiques des dossiers et tâches non instruits et décision NO_GO_AUTOMATIQUE.

Quarante tâches à instruire ne constituent **ni quarante actes réalisés ni quarante anomalies**. Le paquet ne contient aucun nom, permis, signature, jeton brut, extrait de pièce protégée ou digest privé.

## Responsabilités concrètes

**Identification primaire** : recapturer les deux publications, vérifier les empreintes des originaux, localiser chaque occurrence, distinguer folio, date, référence normative, identifiant ou valeur à examiner. Les quatre références P54E sont des indices d'observation, non des positions de caractères.

**Examen comptable sous mandat réel éventuel** : vérifier exercice 2024, unité, devise, signes, colonne, périmètre, consolidations et écritures réciproques entre Ville, RTC et SOMHAC. Un gain déjà éliminé comptablement ne peut être décompté une nouvelle fois. Aucun poste ne peut être présumé monétaire avant confirmation explicite.

**Examen juridique sous mandat réel éventuel** : vérifier la portée du règlement R.A.V.Q. 1435 et la portée du rapport spécialisé des auditeurs, les droits d'accès et la protection des pièces.

**Contre-examen et décision** : contre-revue distincte, conservation des contradictions et suspensions, vérification professionnelle réelle du statut, des conflits et des signatures, avis originaux et décision institutionnelle compétente. Aucun état logiciel ou hachage de document ne remplace ces actes.

**Garanties** : continuité des emplois et services essentiels, confidentialité hors GitHub, séparation des scénarios Québec au Canada et Québec souverain hypothétique.

## Usage sans pièce privée

Commande de génération :

    python scripts/preparer_passation_humaine_nova_p54n.py --dossier p54n_dossier_passation.json --instructions p54n_instructions_verificateurs.md --bilan p54n_bilan_neutre.json

Commande de refus explicite de transmission non autorisée :

    python scripts/preparer_passation_humaine_nova_p54n.py --exiger-transmission

Codes : 0 = génération de documents seulement; 2 = source incohérente ou sortie existante; 3 = refus de transmission prétendument automatique. Les sorties existantes et liens symboliques sont refusés.

## Seuil d'arrêt et travail restant

L'étape n'est pas terminée institutionnellement tant que les cinq positions ne sont pas qualifiées sur originaux, que la contre-revue et les avis pertinents ne sont pas réellement obtenus et que les réserves ne sont pas levées par des personnes habilitées. Le système ne doit pas enchaîner des certifications logicielles fictives. Les 96 contrôles P54B et huit contrôles P54C demeurent non attestés.

Les sites institutionnels de référence pour la vérification par des personnes habilitées sont :
- Barreau du Québec : https://www.barreau.qc.ca/fr/grand-public/faire-affaire-avec-un-avocat/verification-statut-avocat/
- Tableau de l'Ordre des CPA : https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/

**NO_GO_AUTOMATIQUE** : zéro mandat attribué, zéro avis signé authentifié, zéro économie certifiée, aucune fusion main ni intervention SINJIRA.

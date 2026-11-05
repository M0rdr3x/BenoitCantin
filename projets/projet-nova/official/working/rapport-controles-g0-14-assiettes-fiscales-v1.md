# NOVA-FIN-G0.14 — Rapport de contrôles des recettes et de l'exposition budgétaire

**Date :** 5 novembre 2026  
**Projet :** Projet Nova  
**Statut :** validation technique **interne**, non audit financier indépendant et non approbation d'une réforme.  
**Complétude du programme : 47/100**, inchangée.

## 1. Sources inspectées

- Rapport préélectoral sur l'état des finances publiques du Québec, **août 2026**, tableau des revenus 2026–2027 et finances pluriannuelles.
- https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/finances/publications-adm/Rapport_preelectoral/FR/MINFR_RP_2026.pdf
- Transcription de concordance des chiffres du rapport gouvernemental : https://www.sec.gov/Archives/edgar/data/722803/000106299326004487/exhibit99-5.htm
- Revenu Québec, cotisations et conventions fiscales; gouvernement du Québec, cadre municipal et fiscalité.

Le fichier G0.14 est rapproché au **jeu G0.13 conservé dans le même dépôt**, ce qui empêche d'ajouter une catégorie ou de modifier un montant sans modifier explicitement le tableau de référence.

## 2. Contrôles arithmétiques et périmètre

| Élément | Résultat (M$) | Contrôle |
| --- | ---: | --- |
| Huit catégories de revenus autonomes | **135 343** | Somme exacte des postes du rapport |
| Transferts fédéraux | **33 046** | Poste distinct |
| **Total des recettes** | **168 389** | 135 343 + 33 046 |
| Impôt des particuliers + impôts des sociétés | **65 640** | Deux catégories du rapport, **non** une assiette taxable |
| FSS, foncier scolaire et consommation | **41 521** | Trois postes candidats à l'analyse, **non** somme de taxes automatiquement abolissables |
| Solde budgétaire officiel de référence | **−7 690** | Après Fonds des générations |
| Solde mécanique si 41 521 M$ disparaissaient sans compensation | **−49 211** | **Stress-test figé uniquement**, pas prévision Nova |
| Ajustement hypothétique pour atteindre un solde nul dans ce test | **49 211** | Ni recette promise, ni économie certifiée |

Le scénario d'exposition conserve par hypothèse les autres recettes, dont la catégorie **mixte** de 6 484 M$ de droits, permis et redevances. **Il ne représente pas à lui seul un nouveau système à seulement deux prélèvements.**

## 3. Séparation juridique essentielle

Les impôts fédéraux et les recettes municipales sont **hors du périmètre budgétaire provincial consolidé** et ne peuvent pas être ajoutés sans justification. Les cotisations du RRQ et du RQAP et certains fonds de santé ne sont pas des recettes libres pour financer une autre mission. Le montant d'une hypothétique mesure contre les paradis fiscaux demeure **null** : une sanction, une lutte contre la fraude et une nouvelle taxe à assiette distincte ne sont pas économiquement ou juridiquement équivalentes.

Les deux scénarios du projet sont traités séparément : Québec au Canada (transferts **prévus, non garantis sous toute réforme**) et Québec souverain (transferts post-transition **non chiffrés**, jamais reconduits automatiquement). Aucun solde Nova n'est publié.

## 4. Tests effectivement exécutés

Le 5 novembre 2026, après l'ajout d'un diagnostic spécifique au refus d'une hausse artificielle du pourcentage, la suite `tests/g14-fiscal-assiettes.test.mjs` a été exécutée **avec Node.js v26.12.1 dans un environnement externe temporaire**.

**Résultat final : 16 tests réussis sur 16; zéro échec, zéro test ignoré, code de sortie 0.**

Le premier essai avait donné **15/16** : le moteur refusait un changement du score, mais ne retournait pas l'erreur spécifique attendue. Le validateur a été corrigé afin de distinguer explicitement `UNPROVEN_PROGRAMME_PROGRESS`, puis **les seize tests ont tous été réexécutés avec succès**.

Les tests couvrent : sommes comptables, rapprochement avec G0.13, retranchement hypothétique, absence de budget Nova, taxe « paradis fiscaux » non chiffrée, protections fédérales, municipales et sociales, refus des transferts en souveraineté, refus de taxes inventées, et rejet du passage fictif de 47 à 48 %.

Le test final a été exécuté depuis le dépôt GitHub à une révision contenant le correctif, mais **pas dans une exécution GitHub Actions confirmée**. Les tests contrôlent la cohérence du registre et du moteur : ils ne constituent **pas** une expertise économique indépendante ni une preuve de rendement fiscal.

## 5. Conditions restant ouvertes

1. Définir précisément la légalité et l'assiette de l'impôt sur les revenus des personnes et entreprises, et des exceptions.
2. Clarifier si la mesure anti-paradis fiscaux est juridiquement une seconde taxe ou un mécanisme de conformité du premier impôt.
3. Ventiler les redevances, droits, taxes indirectes, FSS et financement scolaire.
4. Protéger les régimes de retraite, parentaux, médicaments, les emplois et l'autonomie municipale.
5. Vérifier les effets sur ménages par décile, entreprises, inflation, investissement, emploi et régions.
6. Chiffrer les deux statuts constitutionnels avec données sources, puis la soutenabilité sur dix ans.
7. Soumettre les analyses à un examen juridique et financier indépendant avant toute promesse de taux.

## 6. Statut

**47/100 — score de préparation du programme inchangé.**

G0.14 a ajouté une classification vérifiable et révélé des montants à analyser, **pas** une économie, un taux fiscal, une loi, un budget équilibré ou une autorisation de gouverner. Les quatre références officielles candidates et le manifeste `data/sources.json` demeurent protégés.

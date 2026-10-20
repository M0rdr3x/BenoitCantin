# Projet Nova — P52O : programme de collecte des preuves et budgétisation des études

**19 octobre 2026 · Projet non adopté · Aucune sollicitation, aucun contrat ni montant fictif · NO_GO.**

## 1. Changement de méthode

P52A–P52N décrivent les vingt justificatifs F01–F20, les contrôles documentaires, les comités proposés et les cahiers de mandat. **Aucun avis extérieur n'est acquis.** P52O fournit un ordre de dépendances et des premières sources publiques effectivement repérées en consultation Web. Il n'attribue pas d'expertise, ne promet pas de taux fiscaux et ne permet pas la publication d'un programme budgétaire adopté.

La règle budgétaire est **« inconnu ≠ zéro »** : les prix d'experts, jours de travail, licences, frais juridiques, vérification, frais annexes et provisions restent `null` tant qu'aucun devis licite, daté et authentifié n'est obtenu. Les **600 montants** de P52B et **720 montants** de P52D ne sont pas fournis ici.

## 2. Dépendances des vingt preuves

| Vague | Preuves | Objectif |
| --- | --- | --- |
| V1 | F01, F02, F03, F04, F07, F09, F19, F20 | Légalité provinciale/fédérale, fiscalité locale, bases du budget, démocratie et confidentialité |
| V2 | F05, F06, F13, F14, F15 | Assiettes fiscales, réglementation anti-abus, subventions, continuité, hypothèses dette-actifs |
| V3 | F08, F16, F17 | Rendement anti-évasion, nouvelles fonctions publiques et relations monétaires |
| V4 | F10 | Scénarios financiers décennaux sans supposer recettes nettes nouvelles |
| V5 | F11, F18 | Distribution des revenus et critères d'abolition prudente |
| V6 | F12 | Audit final de l'emploi, des services et des économies vérifiables |

Les vagues expriment un **ordre de finalisation méthodologique**, non un ordre obligatoire de prise de contact. Par exemple : les démarches de licence BD/MSPS et la préparation d'un inventaire municipal peuvent commencer en parallèle des premiers avis juridiques, **après** validation du mandat et de l'autorité. Chaque preuve a ses dépendances explicites et doit conserver son comité pilote de P52M. Le script empêche un cycle ou une dépendance future et refuse l'effacement d'une des vingt exigences.

## 3. Sources officielles consultées et limites

Le registre `P52O_SOURCES_OFFICIELLES_REPEREES.json` contient **dix pages officielles repérées**, mais pas dix preuves expertisées. Les principaux repères documentaires sont :

- **Constitution** : https://laws-lois.justice.gc.ca/fra/const/section-92.html?wbdisable=true — compétences provinciales, à interpréter avec le reste du régime constitutionnel.
- **Douanes** : https://www.laws-lois.justice.gc.ca/fra/lois/C-54.011/index.html — texte fédéral actuellement pertinent; n'attribue aucun pouvoir douanier au Québec provincial.
- **Administration fiscale** : https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-6.002/20260401 — version datée; recours et modifications ultérieures à vérifier.
- **TVQ** : https://www.legisquebec.gouv.qc.ca/fr/document/lc/t-0.1/20241201 — version **2024**, **non** garantie à jour en 2026, à actualiser avant avis.
- **Budget 2026–2027** : https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/index.asp — prévision, pas réalisation finale ni financement de la fiscalité Nova.
- **Finances municipales** : https://www150.statcan.gc.ca/n1/fr/catalogue/1010002001 — tableau statistique 10-10-0020-01, année, catégories et unités à consolider sans double compte.
- **BD/MSPS** : https://www.statcan.gc.ca/fr/microsimulation/bdmsps/bdmsps et https://www150.statcan.gc.ca/n1/fr/catalogue/89F0002X2026001 — progiciel statique canadien (version 34.0, base 2022, produit mis à disposition en 2026) : **gratuit mais entente de licence signée nécessaire**. Formation, recrutement, analyse, validation, accès au modèle et adéquation à la population québécoise non évalués et non budgétés. N'EST PAS un simulateur d'État souverain.
- **Contrats publics** : https://www.legisquebec.gouv.qc.ca/fr/tdm/lc/c-65.1 et https://www.quebec.ca/gouvernement/services-organisations-publiques/services-transformation-numerique/systeme-electronique-dappel-doffres-seao — à examiner **seulement** si le futur organisme acheteur entre effectivement dans le champ des règles publiques. Ne pas déclarer qu'un simple projet politique est assujetti par défaut.

Chaque source est une **référence publique de départ**; les URL et résumés ne remplacent ni PDF archivé, ni certificat d'authenticité, ni interprétation juridique ou audit externe. Les dates et versions peuvent changer après la consultation.

## 4. Six lots de travail proposés sans prix inventés

| Lot | Périmètre | Principal livrable recherché |
| --- | --- | --- |
| B-JUR | Droit constitutionnel, fiscal, droits | Avis motivés sur compétences, limites et recours |
| B-BUD | Finances provincial/municipal et horizon décennal | Concordance comptable et scénarios financiers |
| B-ANT | Fiscalité anti-abus international | Définition et rendement net prudent |
| B-SOC | Redistribution, services, protection des personnes | Mesure d'incidence et effets défavorables |
| B-TRA | Dette, actifs, fonctions souveraines hypothétiques | Scénarios de coûts et continuité |
| B-SUB | Aides aux entreprises | Coûts temporaires, fins d'aide et contrôle |

Les lots peuvent se chevaucher : **ne jamais additionner deux devis couvrant le même travail** sans ventiler les charges. Les domaines partagés (F06, F10, F14) nécessitent des limites de prestation explicites. Les devis futurs devront spécifier **périmètre, méthode, jours/tarifs, frais, droits d'usage, taxes applicables, plafond, responsabilités, délais, conflits d'intérêts et conditions de réception**. Aucune sollicitation ni attribution automatique n'est lancée.

## 5. Comparaison de devis — contrôle technique uniquement

Le fichier `P52O_SIMULATIONS_DEVIS_VIDES.json` contient zéro soumission réelle ou fictive. Le validateur peut exercer sur un fichier local de **devis entièrement synthétiques** la qualité d'une saisie des montants et l'identité des postes, sans exporter les montants ni « attribuer » un contrat. Pour une comparaison, au moins **deux devis synthétiques distincts** sur le même lot et périmètre, avec même devise CAD, période de validité et poste de frais doivent être présents. Les champs financiers réels du registre restent inconnus.

Le calcul arithmétique d'un devis éventuel ne prouve ni compétitivité, ni authentification d'une offre, ni juste prix du marché. **Ne pas entrer de propositions confidentielles ou noms de professionnels dans GitHub ni GitHub Actions.** Vérifier individuellement prix, durée et conflits hors dépôt, sous règles de confidentialité et de passation légalement applicables.

```bash
python scripts/auditer_acquisition_preuves_nova_p52o.py --rapport /chemin/prive/p52o.json
python scripts/auditer_acquisition_preuves_nova_p52o.py --exiger-preuves --rapport /chemin/prive/p52o_refus.json
```

Résultats : **0** = conformité mécanique de la maquette, toujours NO_GO; **2** = anomalie; **3** = acquisition des preuves/autorisation réelle insuffisante. Les rapports sont non écrasants, sans références nominatives ou montants fictifs.

## 6. Décisions humaines à obtenir avant un engagement

1. Autorité de signer des contrats et cadre juridique applicable (projet partisan ≠ organisme public d'office).
2. Identification des besoins précis avec les experts potentiels, sans favoritisme ni collecte abusive de données.
3. Budget réellement approuvé et sources de financement conformes, distinct du futur budget public hypothétique.
4. Approvisionnement transparent et gestion des conflits d'intérêts, incluant possibilité d'avis contradictoires.
5. Mise à disposition/licence réelle des données, particulièrement pour F11 et BD/MSPS; évaluer si les mesures des effets sont représentatives et correctement limitées.
6. Réception d'avis indépendants et consolidation budgétaire. Maintenir P52A–P52N en NO_GO tant qu'il manque les signatures, l'attestation et l'autorité démocratique.

**Suite P52P proposée :** créer des dossiers de preuve contrôlables, un plan de validation des versions budgétaires et un tableau de couverture des sources/données manquantes. Éviter de prolonger les seules simulations si des humains ne sont pas mandatés.

**Gouvernance :** PR #673 en brouillon, sans fusion; protection `main` absente (#135), réviseurs réels à nommer (#662); préserver SINJIRA et le blocage de PR #640.

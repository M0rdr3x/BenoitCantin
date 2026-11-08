# Projet Nova — P56I : opinion d'audit avec réserve, annexe non auditée et chaîne probante des transferts

**7 novembre 2026. Statut : revue critique documentaire candidate, non adoptée. Décision : `NO_GO_AUTOMATIQUE`.**

## 1. Constat central et rectification de la qualification des sources

Le jalon P56H a déterminé **une identité numérique exacte** entre trois lignes de recettes municipales 2024 d'Alma et un montant du programme MAMH 40350 (**3 320 039 $**) et **un écart de −2 $** entre le programme 40561 et sa catégorie de recette municipale TVQ (**1 665 578 $** contre **1 665 580 $**).

Une revue attentive du rapport primaire souligne une **qualification déterminante** : le [Rapport financier consolidé 2024 de la Ville d'Alma](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-93042.pdf), code municipal 93042, possède un rapport d'auditeur indépendant **avec réserve**, et non une opinion sans réserve. L'auditeur indique que la Ville n'a pas identifié et évalué tous les passifs liés à la mise hors service d'immobilisations, en contravention du chapitre **SP 3280** des normes comptables canadiennes pour le secteur public. L'auditeur explique ne pas pouvoir déterminer les ajustements qui pourraient découler de cette omission. Le rapport est daté du **12 mai 2025**.

**Précision :** cette réserve concerne le traitement des obligations de mise hors service. Elle ne prouve pas à elle seule une anomalie des transferts provinciaux; il ne faut ni la minimiser, ni inventer une relation de causalité avec l'écart TVQ de deux dollars. Les informations détaillées de l'**annexe S27 (Analyse des revenus consolidés, pages imprimées 47 et 52)** sont expressément indiquées **« Non audité »**, même si le rapport contient par ailleurs des états financiers consolidés audités avec réserve.

Les listes provinciales ministérielles, [juillet 2024](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_juillet_2024.pdf) (programme 40350, ligne 1193) et [avril 2024](https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/documents_administratifs/acces_information/engagements_financiers/2024/LIS_engagements_avril_2024.pdf) (programme 40561, ligne 746), décrivent des **engagements financiers ministériels**. Leur libellé « versement » ne démontre pas la **date précise de paiement**, l'**encaissement par Alma**, ni la **constatation de la même opération en 2024**.

## 2. État rigoureux des deux rapprochements

| Rapprochement | Montant municipal | Montant provincial | Écart | Qualification |
|---|---:|---:|---:|---|
| Compensations santé, cégeps et écoles — programme 40350 | 3 320 039 $ | 3 320 039 $ | **0 $** | **Concordance arithmétique exacte, annexe S27 non auditée** |
| Part de croissance TVQ — programme 40561 | 1 665 578 $ | 1 665 580 $ | **−2 $** | **Écart non expliqué, non apparié comptablement** |

Les documents ont des **exercices différents** : année municipale close au 31 décembre 2024 et exercice provincial 2024-2025. Une égalité de montants ne permet pas d'en déduire l'égalité des droits, de la période de constatation ou des mouvements de trésorerie. Toute réduction d'une dépense à cause d'un transfert interne nécessiterait en plus de définir le périmètre de consolidation et ne représenterait **jamais une économie réelle à elle seule**.

## 3. Registre structuré des neuf points de contrôle

Le fichier `P56I_REGISTRE_ASSURANCE_PREUVES_ET_RESERVES_ALMA_2024.json` suit neuf points :

| Identifiant | Point de contrôle | Statut |
|---|---|---|
| I01 | Opinion d'audit sur les comptes d'Alma **avec réserve SP 3280** | Fait documenté |
| I02 | Annexe municipale S27 **non auditée** | Fait documenté |
| I03 | Engagement ministériel ≠ preuve datée de paiement | Non démontré |
| I04 | Exercices municipal et provincial non appariés | Non démontré |
| I05 | Origine de l'écart de **2 $** | Non démontré |
| I06 | Récupération du PDF binaire canonique, contrôle de page et SHA-256 | Non démontré |
| I07 | Éliminations par périmètre entre organismes | Non démontré |
| I08 | Écriture comptable réciproque authentifiée | Non démontré |
| I09 | Financement décennal et fiscalité Nova démontrés | Non démontré |

**Deux constats publics documentés** et **sept points nécessitant une preuve** ne constituent pas un score d'avancement nouveau. L'absence de démonstration d'un paiement ne signifie pas que celui-ci n'a pas eu lieu.

### Contrôle matériel non achevé

Le 7 novembre 2026, une nouvelle tentative de téléchargement des PDF originaux et de capture visuelle dans l'outil de consultation n'a **pas abouti**. L'outil a fourni des extraits de texte public indexés, mais la capture a retourné une **erreur de cache** pour les pages concernées. Nous **n'avons ni PDF canonique enregistré et vérifié, ni empreinte SHA-256 calculée, ni attestation indépendante** concernant les opérations. Ce manque n'autorise pas à affirmer que les PDF officiels sont erronés; c'est une limite de cette vérification et du mode d'accès.

## 4. Justificatifs nécessaires pour passer de « concordance numérique » à « écriture rapprochée »

Les cinq catégories `H01` à `H05` demeurent explicitement sans preuve attachée :

1. Les trois PDF originaux en versions vérifiées, empreintes SHA-256 et comparaison visuelle des pages pertinentes.
2. Les bordereaux MAMH, les références de transaction et les dates d'ordonnancement et de paiement pour les programmes 40350 et 40561.
3. Les journaux de constatation ou d'encaissement municipal et les annexes de ventilation des rubriques correspondantes.
4. Une explication documentée, et non supposée, du **−2 $** observé.
5. Un avis signé d'un comptable municipal indépendant précisant les réserves, la concordance des périodes et le périmètre de consolidation.

Les pièces de paiement et les journaux ne sont pas acquis simplement parce qu'un tableau public et un programme ministériel utilisent des chiffres similaires. Les droits et obligations des municipalités doivent rester financés et protégés.

## 5. Livrables et contrôle reproductible

- `projets/projet-nova/etudes/P56I_REGISTRE_ASSURANCE_PREUVES_ET_RESERVES_ALMA_2024.json` : risques, sources, limites d'assurance et preuves manquantes.
- `scripts/auditer_chaine_preuves_finances_municipales_nova_p56i.py` : validateur de la chaîne P56G → P56H → P56I avec refus de fausses certifications.
- `scripts/tests/test_auditer_chaine_preuves_finances_municipales_nova_p56i.py` : 37 tests dont refus de prétendre une opinion sans réserve, une annexe auditée, une date de paiement inventée, un rapprochement ou une économie non prouvés.
- `.github/workflows/validate-nova-p56i.yml` : régression des contrôles P56G, P56H et P56I.
- Cette note méthodologique.

Exécution locale :

```bash
python scripts/auditer_chaine_preuves_finances_municipales_nova_p56i.py \
  --registre projets/projet-nova/etudes/P56I_REGISTRE_ASSURANCE_PREUVES_ET_RESERVES_ALMA_2024.json \
  --p56h projets/projet-nova/etudes/P56H_DECOMPOSITION_REVENUS_ALMA_2024_CORRESPONDANCES_PROVINCIALES.json \
  --p56g projets/projet-nova/etudes/P56G_PREMIER_PONT_PROVINCIAL_MUNICIPAL_ALMA_2024.json
```

Le mode `--exiger-certification` refuse la réussite (code de sortie 3); les rapports existants ne sont pas écrasés et les sources sont traitées en lecture seule. Une réussite des tests vérifie les **conditions codées de cohérence**, pas les PDF originaux, les dates de paiement ni les opinions professionnelles attendues.

## 6. Ce qui ferait réellement monter la complétude du projet

P56I met de l'ordre dans la **qualité des preuves**, mais aucune nouvelle cellule du budget P52B n'est renseignée : **600 postes financiers encore inconnus**, **720 éléments d'incidence P52D inconnus** et **20 preuves fiscales P52A à valider**. Le score estimatif **P55N reste 53 % (fourchette 45–60 %)**; la présence de nouveaux scripts n'augmente pas artificiellement ce chiffre.

**Prochaine orientation P56J :** obtenir des pièces financières prouvant une transaction de même origine et période, puis un audit contradictoire; simultanément, amorcer l'étude des assiettes fiscales en deux régimes et des obligations de financement des services, plutôt que prolonger indéfiniment les contrôles d'une seule municipalité.

**Aucun taux fiscal adopté, aucune économie certifiée, aucune dépense ou contact externe, aucune publication normative, aucun changement à SINJIRA ni à `main`. Statut : `NO_GO_AUTOMATIQUE`.**

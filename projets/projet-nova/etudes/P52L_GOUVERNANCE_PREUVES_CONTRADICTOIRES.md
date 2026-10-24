# Projet Nova — P52L : gouvernance contradictoire des preuves F01–F20

**19 octobre 2026 · Version candidate non adoptée · Aucune autorisation ni fusion · NO_GO.**

## 1. Pourquoi P52L ?

Les jalons P52A–P52K ont mis en place des modèles comparant les régimes provinciaux et souverains, une revue des sources budgétaires et des contrôles de provenance. Ils ne prouvent **pas** la viabilité d'une réforme fiscale à deux prélèvements, ne certifient aucun taux et ne démontrent pas une absence de perte de pouvoir d'achat. Les **20 preuves F01–F20 sont toutes non validées**; la grille P52B garde 600 valeurs financières inconnues et P52D en garde 720. La simple mention d'un expert dans P52A est une **fonction à pourvoir**, pas une personne mandatée.

P52L institue un dispositif de **réception, examen contradictoire, suspension, contre-expertise et proposition de décision** dans les travaux internes. Il ne crée **pas** d'autorité publique ni de statut juridique. La matrice reflète fidèlement la description des 20 exigences de P52A, sans faire passer un avis requis pour un avis existant.

## 2. Séquence documentaire, contrôle indépendant et contestation

| Stade technique | Définition | Interdiction particulière |
| --- | --- | --- |
| NON_RECUE | Aucun dépôt constaté | Ne pas écrire « validé » |
| RECUE_A_CONTROLER | Une pièce est déclarée déposée | Un document n'est pas encore authentifié |
| CONTROLE_DOCUMENTAIRE_DECLARATIF | Une autre fonction déclare le contrôle d'intégrité | Un SHA-256 ne prouve pas la fiabilité scientifique ni une signature |
| AVIS_INDEPENDANT_DECLARE | Une personne distincte se présente comme expert | Identité, compétences, indépendance, mandat et signature restent à vérifier hors du code |
| EN_CONTESTATION | Une objection est ouverte, toute décision envisagée est suspendue | Ne pas ignorer la contre-expertise |
| REEXAMEN_REQUIS | Contestation déclarée résolue; refaire contrôle et expertise | Ne pas recycler automatiquement un avis antérieur |
| PROPOSITION_DE_DECISION_NON_AUTHENTIFIEE | Un rôle distinct a formulé une proposition, après avis déclaré | **Ne signifie jamais décision légale, adoption ou GO** |

Les actions possibles sont `DEPOSER`, `CONTROLER`, `AVIS`, `CONTESTER`, `RESOUDRE`, et `PROPOSER_DECISION`. Le validateur interdit les transitions illogiques et la concentration des rôles : le déposant ne contrôle pas son propre dépôt, l'expert ne peut être ni le déposant ni le vérificateur, l'autorité proposée ne peut jouer aucun des trois premiers rôles, et le règlement de contestation ne peut provenir de l'auteur, de l'expert ni de la personne contestataire.

Il exige des dates UTC ordonnées, un ID F01–F20 reconnu, un **périmètre juridique exact** (Québec au Canada, transition, Québec souverain hypothétique ou tous), la correspondance des empreintes SHA-256 de la pièce documentaire d'un événement à l'autre et une trace d'acte distincte. Une déclaration de conflit pour un acte d'avis, de contrôle ou de décision **bloque le journal** : aucune validation silencieuse.

Ces contrôles sont des vérifications de cohérence **sur des assertions non authentifiées**. Même si tous les rôles, empreintes et actes sont déclarés cohérents, une personne pourrait les avoir inventés : le programme ne vérifie pas une signature cryptographique externe, un mandat réel, des titres professionnels, un conflit d'intérêts réel ou une décision juridiquement valable. **Tout rapport se conclut donc par NO_GO_AUTOMATIQUE**.

## 3. Matrice d'acceptation humaine à organiser

**Avant recevabilité d'une pièce :** déterminer le document primaire complet, version, date, périmètre institutionnel et statut prévision/réalisé. Exiger la preuve de sa provenance, l'archivage licite, l'empreinte intègre et un processus de correction des versions. Écarter les données confidentielles du dépôt public.

**Avant avis externe favorable :** mandat réel, identité et compétence indépendamment vérifiées, déclaration de conflits d'intérêts, contre-lecture par un second professionnel lorsque le risque est élevé, conclusion et réserves datées, accès à la méthode et aux données licites. Un expert ayant participé à produire le chiffre ne peut être son propre contradicteur.

**En cas de désaccord :** constituer les motifs, garder les deux versions de la preuve, saisir un tiers compétent, documenter la résolution, relancer le contrôle et l'avis sur la version concernée. Une contradiction non résolue interdit une proposition recevable.

**Avant une décision de fond :** constater la totalité des obligations fiscales, les droits, le financement des services, la distribution des effets et les finances sur dix ans **pour chacun des régimes**; confronter les mises à jour budgétaires et les dépenses de reprise des fonctions fédérales en cas de souveraineté seulement hypothétique. La preuve F19 exige distinctement les autorités et procédures démocratiques réelles; aucun résultat CI ni vote interne de dépôt ne les remplace.

**Conditions pratiques bloquantes :** avis F09 de finances publiques sans double comptage; audit F11/F12 sur pouvoir d'achat et emploi; F18 sur équilibres et dette; F20 sur vie privée et recours; F01–F04 et F14–F17 sur compétences et continuités. Les recettes anti-évasion additionnelles demeurent à zéro comme **hypothèse prudente**, non comme recette réalisée.

## 4. Fichiers du jalon et rapports

- `P52L_MATRICE_REVUES_INDEPENDANTES.json` : 20 exigences exactes et toutes les validations réelles laissées à `false` ou `null`.
- `P52L_JOURNAL_DECLARATIF_VIDE.json` : journal d'exemple vide; zéro témoin, zéro avis inventé. Les événements d'un véritable dossier ne doivent **pas** être publiés avec des identités ou copies de justificatifs.
- `scripts/evaluer_relectures_independantes_nova_p52l.py` : contrôle de cohérence des phases, indépendance déclarée, conflits, juridictions, dates et gestion des contestations. Un journal passé par `--journal` est traité comme une **entrée locale non fiable**, pas comme preuve de validation.
- `scripts/tests/test_evaluer_relectures_independantes_nova_p52l.py` : tests adversariaux des changements de statut et des fausses approbations.
- `.github/workflows/validate-nova-p52l.yml` : exécution en lecture seule, sans données personnelles et avec un rapport agrégé limité aux compteurs des phases.

```bash
python scripts/evaluer_relectures_independantes_nova_p52l.py \
  --rapport /chemin/temporaire/p52l_rapport.json
python scripts/evaluer_relectures_independantes_nova_p52l.py \
  --exiger-validation --rapport /chemin/temporaire/p52l_refus.json
```

Le second mode retourne le code **3** même si les métadonnées sont cohérentes : aucune attestation humaine authentifiée n'a été reçue. Erreur documentaire : code **2**. Rapport ordinaire techniquement cohérent : code **0**, **sans GO**. La création de rapport est non écrasante; aucun fichier externe ni identité n'est écrit dans le dépôt.

## 5. Responsabilités et prochaine suite

Un **comité réel d'examen** doit être constitué par les responsables habilités; ne jamais ajouter de noms de personnes, de signatures ou d'approbations fictives dans le code. À terme, définir des règles de quorum, récusation, conflits d'intérêts, voies de recours et publication des motifs expurgés, et soumettre ces règles à une critique externe.

**Priorités opérationnelles :** mandat d'experts réels pour F01–F20, acquisition/archivage des PDF originaux P52K et réconciliation des données des différents niveaux gouvernementaux. En parallèle, faire activer par un administrateur l'application **serveur** d'une protection `main` (#135), et obtenir des réviseurs indépendants (#662). Le dépôt Projet Nova et SINJIRA partagent le même `main` : ne pas agir sur l'administration du dépôt sans coordination.

Le jalon suivant **P52M** pourra préparer le mandat et les livrables des comités d'examen, un registre de réserves sans données nominatives, la politique de conflits d'intérêts et une matrice des seuils de risque, avant toute adoption programmatique.

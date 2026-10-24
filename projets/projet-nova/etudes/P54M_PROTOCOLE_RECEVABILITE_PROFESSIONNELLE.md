# P54M — Matrice de recevabilité préparatoire des preuves d'authentification

**Projet Nova — 24 octobre 2026 — statut non certifiant.** Ce jalon organise l'instruction documentaire des pièces potentiellement obtenues après P54L. Il n'a sollicité ni expert, ni ordre professionnel, ni autorité publique.

## Chaîne de preuve et périmètre

Le jalon précédent [P54L, workflow #40140705919](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40140705919) a **réussi 73 tests**. P54M contrôle la continuité des fiches privées P54I, P54J et P54K, puis le hachage et le contenu structuré de P54L.

Les deux mandats (comptabilité municipale 2024 et droit municipal) se rapportent aux quatre dossiers P54E-V-001, P54E-M-001, P54E-M-002 et P54E-M-003. **Les quatre restent ouverts.** Les 96 vérifications P54B et huit contrôles P54C ne deviennent pas attestés du fait de cette matrice.

P54M autorise seulement **huit positions de dossier × mandat** à évaluer, et huit contrôles préparatoires par position; il ne préjuge pas que toutes ces positions sont pertinentes ni qu'il existe huit avis.

## Quatre catégories documentaires nécessaires à un examen formel déclaratif

Une déclaration EXAMEN_FORMEL_NON_ATTESTE n'est acceptée que si, pour le **même dossier et le même mandat**, P54L possède une pièce locale de SHA-256 distinct et vérifié pour chacune des quatre catégories; quatre IDs renvoyant aux mêmes octets sont insuffisants :

1. Tableau professionnel;
2. Authenticité de signature;
3. Conflits d'intérêts;
4. Validité du mandat.

En outre, les huit contrôles de P54M doivent être déclarés examinés, sans réserve ni suspension ou contradiction amont. Même avec toutes ces conditions, le résultat demeure **EXAMEN_FORMEL_DECLARATIF_NON_ATTESTE**, et jamais « professionnel authentifié ». Des contrôles auto-déclarés ne garantissent ni la qualité des pièces ni l'identité des personnes.

Le vocabulaire accepte également : DEMANDER_COMPLEMENT, IRRECEVABILITE_PROVISOIRE et SUSPENSION_DEMANDEE. Les réserves sont conservées, et aucune décision institutionnelle n'est possible depuis ce programme.

## Ordre de priorité des décisions

Une suspension provenant de P54I–P54L ou du formulaire P54M prévaut sur les autres états. Les contradictions non résolues viennent ensuite, puis les réserves, le refus provisoire déclaré, la demande de complément, et l'examen formel simplement préparatoire.

Le bilan public ne montre que les codes de dossiers et les statistiques des évaluations procédurales. Il ne révèle ni identités, ni permis, ni originaux, ni signatures, ni extraits, ni empreintes privées. Les pièces restent dans une zone locale privée en dehors de GitHub.

## Séparation des vérifications institutionnelles

Le [Barreau du Québec](https://www.barreau.qc.ca/fr/grand-public/faire-affaire-avec-un-avocat/verification-statut-avocat/) prévoit la vérification du statut d'un avocat et une démarche distincte d'authentification de signature auprès de son Service des greffes. **Le code n'exécute aucune de ces démarches.**

Le [tableau de l'Ordre des CPA du Québec](https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/) permet d'examiner certains renseignements concernant les membres, leurs permis et limitations, mais il ne fournit pas l'historique professionnel complet ou les antécédents disciplinaires. Le [cadre CPA sur les conflits d'intérêts](https://cpaquebec.ca/fr/membres-cpa/deontologie/devoirs-generaux/conflit-dinterets/le-conflit-dinterets/) distingue conflits réels, apparents et potentiels et les mesures de sauvegarde appropriées.

La réception locale d'une copie de certificat d'authentification ne prouve pas, à elle seule, qu'elle a été effectivement émise par l'autorité invoquée. La vérification officielle exigerait l'accès autorisé aux originaux et aux canaux institutionnels par une personne compétente. Ces opérations ne sont pas réalisées par P54M.

## Mode opératoire

Sans sources privées, produire seulement la matrice neutre :

    python scripts/evaluer_recevabilite_authentifications_nova_p54m.py --bilan p54m_bilan.json

Pour créer le modèle d'évaluation privé lié aux fiches P54I/P54J/P54K/P54L déjà présentes :

    python scripts/evaluer_recevabilite_authentifications_nova_p54m.py --p54i /espace_prive/p54i.json --p54j /espace_prive/p54j.json --p54k /espace_prive/p54k.json --p54l /espace_prive/p54l.json --modele-prive /espace_prive/p54m.json

Après déclaration de critères examinés, sans prétendre les authentifier :

    python scripts/evaluer_recevabilite_authentifications_nova_p54m.py --p54i /espace_prive/p54i.json --p54j /espace_prive/p54j.json --p54k /espace_prive/p54k.json --p54l /espace_prive/p54l.json --evaluations-locales /espace_prive/p54m.json --bilan p54m_public.json

Le refus d'une prétendue décision automatique se teste par :

    python scripts/evaluer_recevabilite_authentifications_nova_p54m.py --exiger-decision

Les codes de retour sont 0 (format et liens acceptés seulement), 2 (refus technique ou probatoire) et 3 (refus de prétention de décision). Aucun code de retour ne vaut acte professionnel.

## Garanties et suites institutionnelles

L'étude des écritures Ville–RTC éliminées en consolidation reste distincte de toute économie nouvelle. Les protections de l'emploi et des services publics restent impératives; aucun changement constitutionnel n'est décidé ou présumé. Les deux scénarios Québec dans le Canada et Québec souverain hypothétique restent distincts.

Le jalon ne doit pas être employé pour affirmer que des experts réels sont mandatés, que des avis officiels ont été remis, ni que des dépenses ont été identifiées comme supprimables. Une éventuelle évaluation financière demanderait de véritables pièces, des hypothèses comptables comparables, des responsabilités identifiées et des examens indépendants formalisés.

**NO_GO_AUTOMATIQUE** : zéro signature authentifiée, zéro avis certifié, zéro économie démontrée, aucun dossier fermé, aucune fusion dans main et aucune modification SINJIRA.

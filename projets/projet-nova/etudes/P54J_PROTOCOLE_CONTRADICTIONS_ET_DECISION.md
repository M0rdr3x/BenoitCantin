# P54J — Confrontation des conclusions déclarées et prévention des décisions prématurées

**Projet Nova — 24 octobre 2026.** Ce protocole concerne la préparation institutionnelle de la revue des deux projets de mandat : comptabilité municipale et droit municipal. Il ne certifie pas l'authenticité des avis, n'atteste aucune signature et ne calcule aucune économie.

## Faits déjà vérifiés et limites

Le workflow [P54I #40128168040](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40128168040) a réussi **68 tests**. Ses procédures vérifient la structure de documents privés et les SHA-256 des fichiers effectivement présents sur une machine autorisée, mais elles ne démontrent pas qu'un avis émane d'un professionnel habilité.

Les mandats MANDAT-COMPTABLE-2024 et MANDAT-JURIDIQUE-2024 sont encore **des projets non transmis**. Aucun avis indépendant signé n'a été authentifié, aucune revue réelle n'est déclarée par Nova. Les quatre dossiers P54E-V-001 et P54E-M-001/002/003 restent ouverts. Les 96 contrôles P54B et huit contrôles P54C ne sont toujours pas instruits.

## Principes de décision

P54J impose trois séparations successives :

1. **Intégrité technique** : la fiche privée de réception P54I est validée et liée par son SHA-256 calculé sur les octets réels de cette fiche. Chaque fichier cité passe les contrôles de P54I et P54F.
2. **Interprétation documentaire déclarée** : une hypothèse de conclusion est saisie avec un dossier déterminé, un mandat précis et une réserve. Pour déclarer une conclusion autre que « aucune », il faut une pièce locale du type « avis non authentifié », appartenant au même mandat et couvrant le même dossier.
3. **Authentification indépendante et décision** : cette étape ne peut être automatisée par P54J. Les titres professionnels, déclarations d'intérêts, mandats signés, signatures vérifiées, règles de preuve, validité d'une opinion et décisions budgétaires nécessitent des procédures et autorisations externes réellement effectuées.

Le système peut seulement produire un état de **triage documentaire**, jamais un certificat d'économie, de légalité ou de conformité comptable.

## Ne pas assimiler droit et comptabilité

La conclusion d'un juriste sur les limites du R.A.V.Q. 1435 peut différer de l'opinion d'un comptable sur l'étendue des écritures municipales, **sans qu'il existe automatiquement une contradiction**. Même deux opinions portant sur la même page ne sont pas comparables sans examiner la question posée, les unités, l'exercice et le périmètre.

Par conséquent, P54J distingue :
- Aucun avis local lié au dossier;
- Une conclusion déclarée d'un seul volet non authentifié;
- Deux conclusions déclarées de domaines différents, encore non authentifiées;
- Réserve documentaire ouverte;
- Contradiction expressément signalée et à examiner;
- Suspension conservée.

La **suspension prime** toute autre situation; une contradiction déclarée n'est pas considérée comme résolue. Une réserve P54I ne peut être levée silencieusement dans P54J. Les réserves P54I ne sont propagées qu'aux dossiers effectivement couverts par la fiche de réception, et non indistinctement aux quatre dossiers.

Une déclaration AUCUNE_CONCLUSION ne compte pas comme un avis, même si elle occupe une ligne de formulaire.

## Dix contrôles documentaires par mandat

- Lien à la fiche P54I, authentification technique de ses octets et empreinte;
- Existence d'une pièce locale dont le SHA-256 a été recalculé;
- Définition de la question professionnelle et de la portée du mandat;
- Périmètre des entités et écritures de consolidation;
- Exercice comptable 2024, folio et comparabilité;
- Unités, signes et conventions numériques;
- Conflits d'intérêts et indépendance à authentifier par des personnes autorisées;
- Signature originale et qualité professionnelle à authentifier;
- Réserves et contradictions à conserver;
- Continuité des emplois et des services, absence de nouvel avantage fictif sur des opérations déjà éliminées.

Les vingt positions documentaires (deux mandats × dix contrôles) sont **non attestées** jusqu'à réalisation d'examens professionnels indépendants. Ces vingt contrôles ne sont ni des anomalies ni des économies.

## Protection des documents et anonymat

Les fiches P54I et P54J doivent demeurer dans un dossier local privé **extérieur au dépôt Git**. P54J exige le mode privé du système pour les fichiers de saisie, des valeurs à vocabulaire fermé, un identifiant de dossier connu et des références de mandat non équivoques. Les pièces originales, notes et communications demeurent hors GitHub; aucun nom, numéro de permis, texte d'avis, empreinte locale, valeur numérique brute ou chemin de document n'apparaît dans les bilans publics.

La vérification d'une empreinte est une vérification d'intégrité. Elle ne démontre pas qui a rédigé le fichier ou si le contenu est véridique.

## Commandes

Bilan neutre, sans réseau et sans accès aux pièces privées :

    python scripts/qualifier_contradictions_avis_nova_p54j.py --bilan p54j_bilan.json

Créer d'abord une fiche P54I dans un dossier privé, puis générer un modèle P54J automatiquement lié à ses octets :

    python scripts/qualifier_contradictions_avis_nova_p54j.py --fiche-reception-p54i /dossier_prive/p54i_fiche.json --modele-prive /dossier_prive/p54j_conclusions.json

Après examen manuel et consignation des conclusions **déclarées**, produire la matrice de suivi :

    python scripts/qualifier_contradictions_avis_nova_p54j.py --fiche-reception-p54i /dossier_prive/p54i_fiche.json --conclusions-locales /dossier_prive/p54j_conclusions.json --bilan p54j_synthese_publique.json

Si la fiche P54I est modifiée, le lien SHA-256 échoue et la fiche P54J devra être révisée; il est interdit de remplacer la preuve silencieusement.

Toute prétendue décision automatique doit être refusée (code de sortie 3) :

    python scripts/qualifier_contradictions_avis_nova_p54j.py --exiger-go

Le code 0 indique uniquement que les champs et les relations techniques sont cohérents. Le code 2 indique un refus de données ou de structure. Aucun de ces états n'atteste un avis professionnel indépendant.

## Précautions institutionnelles

Les avis comptables et juridiques devront être réellement mandatés et reçus, confrontés à des pièces primaires et à des signatures vérifiables, puis analysés selon leur champ spécifique par une autorité compétente avant toute décision publique. Les quatre dossiers P54E restent ouverts; l'hypothèse de date probable relevée par P54D n'est pas close.

Le droit du travail, la continuité des services publics, le refus de toute double comptabilisation Ville–RTC et la séparation des scénarios Québec au Canada / Québec souverain hypothétique demeurent des garanties impératives.

**NO_GO_AUTOMATIQUE** : aucun mandat signé authentifié, aucun avis vérifié, aucune économie certifiée, aucune fusion dans main et aucune modification de SINJIRA.

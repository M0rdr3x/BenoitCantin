# Projet Nova — P53V : réconciliation des constats potentiels et plans de correction

**23 octobre 2026 — protocole d'examen, aucun manquement financier prouvé et aucune clôture.**

## 1. Objet : éviter la certitude fabriquée

Après P53U (56 tests réussis), le projet contient un cadre de revue de provenance, d'intégrité, d'accès, de consolidation, d'emploi et de services. P53V prépare la gestion des **écarts potentiels** à partir de six dossiers d'organismes 2024 et huit domaines de vérification : **48 positions à examiner**. Tous les champs de départ sont **NON_INSTRUIT**.

Une catégorie d'écart est un **thème de contrôle**, jamais une accusation d'irrégularité, de détournement ou de mauvaise administration. Aucun organisme n'est présenté comme coupable d'une erreur. Deux positions (Ville de Québec 23027 et RTC T0088, catégorie éliminations préexistantes) renvoient à une **précaution comptable documentée dans P53P** : des opérations internes ont déjà été éliminées dans le périmètre consolidé, et il faut empêcher une nouvelle élimination des mêmes écritures. Ce signalement n'est pas un jugement d'inexactitude des rapports.

## 2. Catégories et correctifs à instruire

| Écart **à rechercher** | Vérification ou correction envisageable |
|---|---|
| Émetteur ou version non confirmé | Confirmer l'organisme d'origine, la version officielle et les rectificatifs |
| Référence d'intégrité non fiable | Réconcilier l'empreinte avec une référence sûre et la chaîne de conservation |
| Accès et confidentialité incertains | Qualification de droit d'accès, caviardage, droits des tiers et autorisations |
| Contrepartie bilatérale non établie | Grand livre payeur et bénéficiaire, factures, paiements, période et périmètre |
| Élimination déjà réalisée à réconcilier | Contrôler ajustements de consolidation, éviter les doubles retraits |
| Emplois et continuité des services non démontrés | Garantir effectifs, conditions, accessibilité et indicateurs de qualité |
| Coût complet et transferts non établis | Recenser coûts de transition et récurrents, tiers payeurs, risques et effets nets |
| Indépendance et avis originaux absents | Vérifier compétences, mandats, conflits d'intérêts, avis datés et signés hors dépôt |

Les catégories sont liées aux **huit contrôles P53U** pertinents et une action corrective précise est proposée pour chacune, sans engager un organisme à agir.

## 3. Traitement des déclarations contradictoires

Deux rôles sont prévus : **collecte documentaire** et **revue de qualité indépendante**. Une déclaration strictement limitée aux statuts non certifiés peut être associée à chaque rôle par organisme et catégorie; le système accepte donc au plus 96 déclarations (2 × 48). Aucun nom, signature, montant, chemin de fichier, adresse, URL de dossier privé ou contenu comptable ne peut être saisi.

En présence de deux appréciations **différentes**, le dossier est classé comme **contradiction déclarée non résolue**, sans automatiquement privilégier la version optimiste. Si l'une des deux appréciations révèle un blocage déclaré — conflit, accès interdit, risque d'emploi/service ou incohérence de périmètre — la contradiction reste **bloquante**. Deux appréciations concordantes ne deviennent pas davantage une preuve vérifiée : des rôles distincts ne prouvent pas que les évaluateurs sont personnellement indépendants.

**Aucun état "CLOS", "CORRIGE_CERTIFIE", "ECONOMIE_VALIDEE" ou "DECISION_ADOPTEE" n'est autorisé.** Une proposition ou un examen déclaré de correctif ne vaut jamais exécution, expertise ou levée de blocage.

## 4. Clôture future sous supervision humaine

Pour envisager une clôture ultérieure dans un dispositif distinct, il faudrait au minimum :

1. Une description factuelle du désaccord, sans imputation à une personne ou à un organisme.
2. Les documents originaux et versions fiables, ainsi que les droits d'accès et la chaîne de conservation vérifiés hors Git.
3. Le rapprochement des deux écritures et des éliminations antérieures, dans le périmètre et l'exercice comparables.
4. Une mesure corrective formulée par la personne ou administration habilitée et une trace d'exécution réelle.
5. Une évaluation des effets sur les travailleurs, conditions de travail, services essentiels, contribuables et tiers.
6. Un contrôle indépendant sur les éléments probants et les éventuelles limites de l'examen.
7. Une décision de clôture réellement signée par les détenteurs de l'autorité requise, et conservée dans un espace documentaire autorisé.

L'**Institute of Internal Auditors**, Global Internal Audit Standards 2024, notamment normes **15.1** et **15.2**, distingue les constats, plans d'action, leur suivi et la confirmation de mise en œuvre. Ce référentiel est utilisé comme **inspiration méthodologique**, non comme preuve que Projet Nova exerce une fonction d'audit professionnel certifié :
https://www.theiia.org/en/content/standards/complete-global-internal-audit-standards/

## 5. Exécution de l'inventaire

    python scripts/reconcilier_ecarts_nova_p53v.py --bilan p53v_bilan.json --registre p53v_48_positions.json
    python scripts/reconcilier_ecarts_nova_p53v.py --exiger-correctifs-clos

Le programme construit une matrice de 48 contrôles et un bilan agrégé. Les déclarations locales s'ajoutent avec --declaration chemin.json, dans la limite de 96. Il n'accède à aucune pièce confidentielle et n'effectue aucun envoi ou demande d'accès. Les sorties n'écrasent aucun fichier existant.

Code de retour **0** : cohérence de structure seulement, **2** : déclaration non conforme, rôle dupliqué ou fichier existant, **3** : refus obligatoire de prétendre qu'un correctif est réellement clos. Les tests utilisent uniquement des cas de synthèse; aucun organisme réel n'est soumis à un constat par les tests.

## 6. Limites financières et constitutionnelles

Le programme ne calcule **aucun montant** à partir des recettes historiques MAMH 2024. Les 102 pièces P53Q n'ont pas été collectées ni authentifiées, les 48 revues P53U ne sont pas complétées, les 162 exigences restent à vérifier, les preuves fiscales F01–F20 et 1 320 variables Nova sont toujours en suspens. Les scénarios Québec dans le Canada et Québec souverain hypothétique ne sont pas additionnés; le cadre d'accès actuel ne confère pas de nouvelles compétences.

**NO_GO_AUTOMATIQUE** : aucune économie certifiée, aucun avis professionnel indépendant signé, aucune clôture réelle de correctif, aucune intervention sur main ou SINJIRA, aucun recul des conditions de travail ou de l'accès aux services.

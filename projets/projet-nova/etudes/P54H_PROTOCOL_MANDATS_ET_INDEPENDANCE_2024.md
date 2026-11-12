# P54H — Mandats d'expertise indépendants : CPA et droit municipal

**Projet Nova — 24 octobre 2026 — projets de mandat à examiner, non transmis.**

## Objet et chaîne de preuve

Les étapes P54B à P54G ont construit une chaîne de comparaison documentaire des publications financières 2024 de la Ville de Québec et du MAMH, puis des procédures de revue humaine. La répartition actuelle demeure **4 observations indéterminées** et **1 année/date probable non confirmée** entre les pages PDF index 102 (Ville) et 162 (MAMH), à propos d'un rapport d'audit spécialisé des dépenses mixtes locales et d'agglomération (R.A.V.Q. 1435).

Les quatre dossiers P54E-V-001, P54E-M-001, P54E-M-002 et P54E-M-003 restent ouverts. Les 96 contrôles P54B, les huit contrôles P54C et les 40 vérifications P54E n'ont pas été transformés en preuves signées. P54F et P54G ont été testés avec succès; les tests ne créent pas de vrais experts, de contrats ni de signatures.

P54H introduit **deux projets de mandat distincts**, avant toute recherche, contact ou sélection effective :

1. **MANDAT-COMPTABLE-2024** — comptabilité municipale, périmètre consolidé, écritures réciproques, pièces de contrepartie, statut audité ou non, unités et signes; évaluation de la portée réelle du rapprochement et de la possibilité même de qualifier un poste financier.
2. **MANDAT-JURIDIQUE-2024** — portée du R.A.V.Q. 1435, interprétation du mandat précis des auditeurs, droit municipal et limites juridiques de toute utilisation des publications, droits d'accès aux pièces et confidentialité.

Ces mandats ne doivent pas être confondus avec un audit intégral des finances municipales, un audit de performance ou une estimation des économies fiscales proposées par le Projet Nova. Toute extension de portée exige un accord écrit préalable et des pièces distinctes.

## Règles professionnelles pertinentes

La présentation de l'**Ordre des CPA du Québec** rappelle que le code de déontologie exige d'identifier et de traiter les conflits d'intérêts **réels, apparents et potentiels**, y compris les relations avec le cabinet ou d'autres clients : https://cpaquebec.ca/fr/membres-cpa/deontologie/devoirs-generaux/conflit-dinterets/le-conflit-dinterets/

L'Ordre permet de consulter son **tableau des membres**, avec notamment la possibilité de vérifier certains renseignements relatifs au titre et au permis de comptabilité publique : https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/

Le **Code de déontologie des avocats** applicable au Québec encadre l'intégrité, la confidentialité, l'indépendance, la compétence, les conflits d'intérêts et les limites du mandat : https://www.legisquebec.gouv.qc.ca/fr/document/rc/B-1,%20r.%203.1/

Ces sources fournissent un **cadre de préparation**. Le logiciel ne consulte pas automatiquement le tableau des professionnels, ne valide pas les titres, ne conclut pas à l'absence de conflits ni à la conformité déontologique d'un cas particulier. Tout cas de conflit doit être soumis aux règles de la profession concernée et aux personnes habilitées. Une déclaration d'absence de conflit ne constitue pas une attestation.

## Douze contrôles par mandat (24 positions préparatoires)

1. Délimitation et preuves de la compétence professionnelle.
2. Examen de l'ordre professionnel applicable, du statut et des permis pertinents.
3. Déclaration de conflits réels, apparents ou potentiels.
4. Déclaration des liens avec clients, cabinets, entreprises et intervenants antérieurs.
5. Modalités des honoraires, rémunération variable et incitations liées au résultat.
6. Confidentialité, secret professionnel et accès aux données.
7. Contrat écrit envisagé, mission, limites et livrables attendus.
8. Catalogue des documents originaux, versions et empreintes.
9. Droit d'accès aux grands livres et aux tiers.
10. Traitement des opérations réciproques et de la consolidation.
11. Incidence sur les emplois, les conditions de travail et la continuité des services.
12. Règles de remise, de vérification et d'authentification d'un véritable avis daté et signé.

Les honoraires liés au résultat sont recensés comme **un risque à apprécier**, et non automatiquement transformés en faute juridique. Le résultat du mandat reste libre de conclure qu'aucune différence financière n'est prouvée ou que les pièces sont insuffisantes.

## Confidentialité et gestion des dossiers

Le registre GitHub comprend seulement les codes de mandat et les contrôles. Les identités réelles, permis professionnels, déclarations détaillées d'intérêts, courriels, curriculum vitae, contrats, correspondances, devis, preuves et notes de consultation devront être conservés hors du dépôt et hors de GitHub Actions, dans un espace sécurisé adapté au secret professionnel.

Une fiche locale facultative peut recueillir des **déclarations pseudonymisées**, au vocabulaire strictement fermé, sur des contrôles supposément examinés. Le programme refuse les champs libres, noms, adresses, contrats, montants ou signatures. Il vérifie les permissions du fichier (0600 requis) et empêche sa lecture dans le dépôt. Même une fiche décrivant tous les contrôles comme examinés ne constitue ni qualification confirmée, ni engagement contractuel, ni avis reçu.

## Commandes

Produire le dossier de mandat vierge et son bilan public :

    python scripts/preparer_mandats_experts_nova_p54h.py --mandats p54h_mandats.json --bilan p54h_bilan.json

Créer la fiche de déclaration dans un espace local privé, **hors GitHub** :

    python scripts/preparer_mandats_experts_nova_p54h.py --modele-prive /repertoire_prive/p54h_declarations.json

Valider la structure des déclarations sans révéler les candidats :

    python scripts/preparer_mandats_experts_nova_p54h.py --declarations-locales /repertoire_prive/p54h_declarations.json --bilan p54h_agrege.json

Refuser toute attribution de certification au programme :

    python scripts/preparer_mandats_experts_nova_p54h.py --exiger-avis-certifie

Codes : 0 = structure conforme; 2 = schéma ou accès irrecevable; 3 = refus explicite d'une certification revendiquée. Aucun de ces codes ne constitue une approbation de candidature ou de dépense.

## Critères réels de progression

Une véritable vérification ultérieure devrait déterminer si une personne a été régulièrement choisie, si son permis est pertinent et valide, si les conflits sont correctement évalués, si le client a consenti à toutes les mesures de sauvegarde applicables, si le contrat a effectivement été signé, si les pièces primaires ont été communiquées selon les droits d'accès et si l'avis indépendant a réellement été reçu et authentifié. Cela exige des opérations humaines ou des connecteurs officiels autorisés **non présents dans P54H**.

Aucune procédure automatisée ne peut transformer un statut « candidat déclaré », « contrôle examiné » ou « absence de conflit déclarée » en « expert accepté », « indépendance certifiée » ou « montants validés ».

Les opérations Ville–RTC déjà éliminées restent exclues des nouvelles économies; aucune atteinte à la main-d'œuvre locale ou aux services essentiels n'est admise; les scénarios du Québec au Canada et du Québec indépendant demeurent séparés.

**NO_GO_AUTOMATIQUE — 2 projets de mandats non transmis, 0 expert engagé, 0 avis signé authentifié, 0 économie, aucune fusion main et aucune intervention sur SINJIRA.**

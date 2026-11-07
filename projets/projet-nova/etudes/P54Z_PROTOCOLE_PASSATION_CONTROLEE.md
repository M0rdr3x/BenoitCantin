# P54Z — Passation contrôlée à la revue humaine (3 novembre 2026)

**Statut : dossier technique de préparation, non certifiant.** Le jalon P54Y vérifiait la présence de huit chaînons documentaires (P54Q–P54X), mais ne désignait aucun professionnel et n'authentifiait aucune expertise. P54Z donne aux équipes habilitées une trame locale de **cinq observations × huit contrôles = 40 positions** sans transformer cette trame en preuve d'exécution.

## Contenu et provenance

- Les cinq références sont reprises de P54W et P54X, et leur périmètre est vérifié contre P54U. Parmi elles, quatre dossiers P54E et une occurrence pouvant correspondre à une année/date restent à qualifier sur pièce.
- Les huit contrôles reprennent exactement le vocabulaire de P54W : origine de la source, offset NFKC, observation visuelle sur la page, nature de l'occurrence, distinction date/folio/référence/valeur, vérification de l'unité/exercice/colonne, maintien des réserves, contre-revue indépendante.
- Les références publiques sont des points de localisation, **pas des preuves de montants monétaires ou d'économies**. Les originaux PDF de la Ville et du MAMH et les documents privés P54V/P54W doivent être revérifiés hors Git conformément à P54X avant toute revue substantielle.

## Parcours d'utilisation

1. Un responsable documentaire habilité récupère légalement les pièces originales et vérifie leurs droits d'accès. **Aucune demande ou transmission n'est effectuée par cet outil.**
2. Créer le modèle local hors dépôt : `python scripts/preparer_passation_controlee_nova_p54z.py --creer-modele /chemin/hors-depot/passation-privee.json`. Le fichier est créé neuf avec permissions 0600.
3. Les rôles **GARANT_DOCUMENTAIRE, LECTEUR, CONTRE_LECTEUR, REFERENT_JURIDIQUE, REFERENT_COMPTABLE** restent non attribués. Aucune personne n'est prétendue engagée, indépendante, compétente ou habilitée du seul fait d'un rôle indiqué.
4. Facultativement, contrôler des déclarations locales limitées à `NON_INSTRUIT`, `PREPARATION_DECLAREE_NON_VERIFIEE` et `SUSPENDU` par `--declarations /chemin/hors-depot/passation-privee.json`. Les préparations déclarées restent **non vérifiées**; toute suspension demeure bloquante.
5. Produire un bilan strictement agrégé : `python scripts/preparer_passation_controlee_nova_p54z.py --bilan-public p54z_bilan.json`. La sortie ne contient ni identité, signature, chemin privé, occurrence textuelle, montant, PDF, ni jeton.
6. Vérifier indépendamment les aptitudes, les mandats, les pièces, la chaîne de conservation, les conflits d'intérêts et les avis originaux signés **en dehors de cet outil** avant toute décision. Aucune de ces obligations ne peut être réputée satisfaite automatiquement.

## Interdictions et motifs de refus

Le script rejette les identités, signatures, commentaires libres, pièces jointes, chemins dans les déclarations, champs supplémentaires et statuts prétendant une certification. Il refuse les déclarations non conformes, hors périmètre, dupliquées, trop volumineuses, les symlinks, les droits supérieurs à 0600 et toute création de modèle dans le dépôt. Il refuse d'écraser une sortie déjà présente.

Le bilan public force : **aucun avis authentifié, aucune qualification définitive, aucun GO, aucune fusion autorisée, aucune économie certifiée**. La revue devra aussi traiter **40 tâches P54N, 10 blocages P54O, 96 contrôles P54B et huit contrôles P54C** encore non attestés. Les opérations comptables Ville–RTC–SOMHAC déjà éliminées ne doivent pas être additionnées comme économies nouvelles.

**Protection constante** : aucun travailleur licencié au titre de cette étude, aucune réduction des services essentiels, aucune dépense transférée artificiellement à la population, maintien de deux régimes constitutionnels distincts, aucune intervention sur SINJIRA ou sur `main`. **Décision : NO_GO_AUTOMATIQUE.**

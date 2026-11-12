# P54K — Habilitations, signatures et chaîne de preuve professionnelle

**Projet Nova — 24 octobre 2026.** Protocole préparatoire, sans examen officiel exécuté ni authentification professionnelle obtenue.

## Origine et portée

Les tests de P54J [Actions #40130254551](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40130254551) sont réussis. P54K reprend les deux projets de mandat du Projet Nova, un comptable municipal et un juridique, ainsi que les quatre dossiers P54E toujours ouverts. Les rapports Ville de Québec/MAMH 2024 ne prouvent à eux seuls aucune économie financière pour Nova.

Le programme P54K **ne prétend pas vérifier l'identité d'un CPA ou d'un avocat**. Il constitue une grille d'instruction pour un contrôleur humain, et s'assure qu'aucune déclaration de contrôle ou de double revue ne puisse se faire passer pour une authentification par un ordre professionnel.

## Sources institutionnelles à employer par des professionnels autorisés

- **Barreau du Québec** : https://www.barreau.qc.ca/fr/grand-public/faire-affaire-avec-un-avocat/verification-statut-avocat/ . Le Barreau expose des démarches de vérification du statut d'un avocat au Tableau de l'Ordre et un service d'authentification des signatures par ses greffes. P54K ne communique pas avec le Barreau, ne sollicite pas cette authentification et ne peut pas représenter une consultation de ce service.
- **Ordre des CPA du Québec — Tableau de l'Ordre** : https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/ . L'examen du permis et du champ de pratique exige les informations réelles du professionnel, qui ne doivent pas être copiées dans GitHub.
- **Ordre des CPA — Conflits d'intérêts** : https://cpaquebec.ca/fr/membres-cpa/deontologie/devoirs-generaux/conflit-dinterets/le-conflit-dinterets/ . Les conflits réels, apparents et potentiels, de même que les mesures de sauvegarde appropriées, doivent être évalués selon les règles professionnelles applicables.

Ces références institutionnelles ne sont ni des preuves concernant un expert déterminé ni des certificats produits pour le Projet Nova.

## Trois fichiers locaux liés et non interchangeables

1. La **fiche P54I** est contrôlée sur les octets des pièces disponibles sous le répertoire privé preuves/. Elle fournit l'étendue du mandat et les documents déclarés, sans certifier leur signature.
2. La **fiche P54J** doit être liée au SHA-256 de la fiche P54I, indiquer le dossier P54E correspondant et disposer d'une conclusion substantielle déclarative adossée à une pièce de type avis non authentifié. Une ligne « aucune conclusion » ne vaut pas avis.
3. La **fiche P54K** indique les seuls contrôles déclarés par un examinateur ou un contre-réviseur et contient **les empreintes SHA-256 des deux fiches sources**. Elles ne sont publiées ni dans les bilans ni dans les artefacts GitHub.

Toute modification des octets de P54I ou P54J rend caduque la correspondance avec P54K et provoque un refus explicite. Les avis, codes pseudonymes, noms, permis, signatures, pièces brutes et fichiers de travail demeurent exclusivement hors du dépôt.

## Douze contrôles de référence

Les douze rubriques sont : Tableau professionnel, permis et limitations, identité du rédacteur, procédure officielle de contrôle de signature, mandat écrit et consentement, conflits d'intérêts et indépendance, provenance de la chaîne SHA, adéquation du périmètre de l'avis, réserves et contradictions, exercice et unités, consolidations Ville–RTC, impacts sur emplois et services.

Le système prévoit quatre dossiers, deux disciplines et deux rôles de vérification déclaratifs, soit **16 positions théoriques de rôle**. Ce chiffre est un plafond de saisie, pas un nombre d'experts engagés. Les codes de rôle pseudonymisés ne démontrent ni identité distincte ni indépendance. Même la déclaration de toutes les rubriques examinées, sous les deux rôles, ne vaut aucune certification.

## Traitement des alertes et des suspensions

La matrice publique admet les états suivants : aucune revue professionnelle, revue partielle non authentifiée, deux revues déclarées non authentifiées, alerte de vérification, réserve ouverte, contradiction ouverte ou suspension prioritaire.

La suspension issue de P54I/P54J ou déclarée dans P54K prévaut sur les autres statuts. La contradiction de P54J et les réserves héritées restent ouvertes. Les deux disciplines sont distinctes : une portée juridique différente d'une portée comptable n'est pas automatiquement qualifiée de contradiction.

Les champs indiquant que l'identité, le permis, la signature, l'indépendance, la valeur de l'avis ou la décision publique sont certifiés doivent rester à false et sont rejetés s'ils sont mis à true.

## Commandes de contrôle, sans aucun réseau

Bilan vierge :

    python scripts/verifier_habilitations_signatures_nova_p54k.py --bilan p54k_neutre.json

Modèle privé lié aux empreintes réellement présentes dans P54I et P54J :

    python scripts/verifier_habilitations_signatures_nova_p54k.py --fiche-p54i /dossier_prive/p54i.json --fiche-p54j /dossier_prive/p54j.json --modele-prive /dossier_prive/p54k.json

Après des examens humains réellement documentés, mais **non authentifiés par le logiciel** :

    python scripts/verifier_habilitations_signatures_nova_p54k.py --fiche-p54i /dossier_prive/p54i.json --fiche-p54j /dossier_prive/p54j.json --revue-locale /dossier_prive/p54k.json --bilan p54k_public.json

Vérification du refus d'un statut d'authenticité automatisée :

    python scripts/verifier_habilitations_signatures_nova_p54k.py --exiger-authenticite

Code 0 : schémas et hachages cohérents, sans attestation. Code 2 : refus d'une source, d'un schéma ou d'une transition incohérente. Code 3 : refus attendu d'une authentification revendiquée.

## Décision et prudence financière

Les quatre dossiers P54E ne sont pas clos, les 96 contrôles P54B et huit contrôles P54C restent à instruire; la preuve d'une économie budgétaire ne peut pas être inférée des différences lexicales de deux versions de PDF. Aucune élimination Ville–RTC déjà prise en compte en consolidation ne peut être convertie artificiellement en économie nouvelle.

Les emplois et services sont protégés; les régimes Québec au Canada et Québec souverain hypothétique sont conservés dans des analyses distinctes.

**NO_GO_AUTOMATIQUE** — aucun professionnel authentifié, aucun avis indépendant signé reçu, aucune réduction de services, aucune modification de SINJIRA et aucune fusion dans main.

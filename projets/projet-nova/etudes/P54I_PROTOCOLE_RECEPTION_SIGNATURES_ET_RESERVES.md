# P54I — Réception technique de mandats et avis professionnels : intégrité, réserves et limites

**Projet Nova — 24 octobre 2026.** Le présent protocole prépare une future réception de pièces privées. Il ne présume aucun contact, engagement, mandat signé ni avis professionnel réellement obtenu.

## Point de départ prouvé

Le jalon P54H a réussi [72 tests automatisés](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40126735096). Les deux projets, MANDAT-COMPTABLE-2024 et MANDAT-JURIDIQUE-2024, sont **non transmis**. Les quatre dossiers P54E restent ouverts, tout comme les 96 contrôles P54B et les huit contrôles P54C. Une occurrence numérique dite année/date probable n'a pas été authentifiée.

## Trois niveaux à ne jamais confondre

1. **Fichier matériellement disponible dans un espace privé.** Un fichier a été trouvé et est lisible avec les permissions requises. Cela n'identifie pas l'auteur.
2. **Empreinte d'intégrité recalculée.** L'outil hache les octets par SHA-256 et confronte le résultat à une valeur déclarée dans la fiche privée. Cela prouve une concordance d'octets, et rien sur la validité du contenu.
3. **Authenticité et valeur professionnelle.** Seuls des contrôles réellement effectués sur l'identité, les titres, les conflits d'intérêts, le contrat, la signature et la portée pourraient soutenir une authentification indépendante. **P54I n'effectue pas ce troisième niveau.**

L'absence d'anomalie de hachage ne démontre ni un avis authentique, ni un audit conforme, ni une économie d'argent public.

## Réception et réserves

Le modèle P54I distingue projet de mandat, avis professionnel non authentifié et annexe justificative. Les réserves possibles couvrent la signature, la portée, les pièces primaires manquantes, les conflits, les contradictions, les unités ou périmètres et une suspension expresse.

Les seuls statuts techniques sont :

| État | Interprétation limitée |
|---|---|
| FICHIER_LOCAL_NON_RECU | Aucune pièce locale reliée au mandat |
| FICHIER_LOCAL_INTEGRE_NON_AUTHENTIFIE | Une ou plusieurs pièces correspondent aux empreintes déclarées, sans authentification de leur auteur |
| RESERVE_OUVERTE | Fichier local présent, réserve déclarée non levée |
| SUSPENDU | Suspension explicite, y compris si aucun fichier local n'est accessible |

Deux mandats, dix contrôles chacun : lieu de stockage, empreinte SHA-256, type et périmètre, exercice 2024, conflits, signatures, réserves, accès et confidentialité, emplois/services, consolidations Ville–RTC. Aucun de ces vingt points n'est attesté initialement.

## Conditions de conservation

La fiche et les originaux restent exclusivement **hors GitHub**, sous contrôle d'accès approprié. Les pièces se trouvent dans un répertoire local preuves/, jamais dans le dépôt. La routine de sécurité héritée de P54F refuse les chemins traversants, les liens symboliques, les permissions publiques et les fichiers dépassant 32 Mio par pièce. Les types de pièces doivent être compatibles : une déclaration d'avis requiert un type de preuve AVIS_PROFESSIONNEL_NON_ATTESTE; un projet de mandat relève de PIECE_JUSTIFICATIVE_PRIVEE.

Une pièce ne peut pas être utilisée deux fois dans la même fiche pour faire croire à deux avis indépendants distincts. Les SHA privés, noms, permis, chemins de fichiers, documents originaux, extraits et autres renseignements identifiants n'apparaissent pas dans le bilan public.

## Commandes opératoires

Créer un bilan neutre sans connexion ni document privé :

    python scripts/recevoir_mandats_et_avis_nova_p54i.py --bilan p54i_bilan.json

Créer une fiche privée à permissions 0600 dans un emplacement local **hors dépôt** :

    python scripts/recevoir_mandats_et_avis_nova_p54i.py --modele-prive /dossier_prive/p54i_fiche.json

Une personne habilitée complétera les rubriques pieces et receptions selon les énumérations du registre de configuration. Les documents se trouvent sous /dossier_prive/preuves/. Tout SHA doit être calculé sur les octets réellement reçus, et non recopié depuis une publication externe non vérifiée.

Analyser localement, sans partager les originaux :

    python scripts/recevoir_mandats_et_avis_nova_p54i.py --fiche-locale /dossier_prive/p54i_fiche.json --bilan p54i_synthese.json

Refus exprès de prétendue certification :

    python scripts/recevoir_mandats_et_avis_nova_p54i.py --exiger-authenticite-certifiee

Codes : **0** = contrôles structurels et d'intégrité réussis; **2** = problème technique ou probatoire; **3** = authentification automatique demandée et refusée. Un code 0 n'est **jamais** un avis indépendant signé.

## Verrous institutionnels

Le programme ne contacte aucun expert, ne signe rien, n'effectue aucune transmission, ne valide aucun permis ou statut professionnel et ne rend aucune décision budgétaire. Toute conclusion sur un poste monétaire nécessitera un mandat réel, une pièce originale authentique, des unités et périmètres comparables, la prise en compte des éliminations réciproques et un contrôle contradictoire indépendant.

**NO_GO_AUTOMATIQUE.** Zéro mandat authentifié, zéro avis professionnel signé vérifié, zéro économie certifiée, maintien des emplois et des services, régimes Québec au Canada et Québec souverain hypothétique distincts, branche main et SINJIRA inchangés.

# P54O — Précontrôle de qualité et conditions réelles de passation

**Projet Nova — 24 octobre 2026.** P54O ne crée aucun mandat, avis ou certificat. Il vérifie que le dossier P54N reproduit les faits documentaires établis par P54D/P54E, sans modifications donnant artificiellement à croire qu'une tâche a été réalisée ou qu'une transmission a été autorisée.

## Ancrage confirmé

Le workflow P54N #40149291336 a réussi **64 tests** :
https://github.com/M0rdr3x/BenoitCantin/actions/runs/40149291336

Le projet suit quatre dossiers P54E et **une cinquième occurrence distincte** probable de date/année, sur les index PDF Ville 102 et MAMH 162 (base zéro). Les zones documentaires ne sont que des positions approximatives et les valeurs exactes restent hors Git.

| Référence | PDF | Index | Zone | Classification indicative |
|---|---|---:|---|---|
| P54E-V-001 | Ville | 102 | FIN | INDETERMINE |
| P54E-M-001 | MAMH | 162 | DEBUT | INDETERMINE |
| P54E-M-002 | MAMH | 162 | FIN | INDETERMINE |
| P54E-M-003 | MAMH | 162 | FIN | INDETERMINE |
| P54O-DATE-001 | MAMH | 162 | FIN | ANNEE_DATE_PROBABLE |

La cinquième occurrence est une **observation à confirmer**, pas un cinquième dossier P54E et encore moins une anomalie comptable. Les cinq indices d'observation P54D sont 0, 1, 3, 4 et 2. Leur ordre de présentation n'est pas l'ordre de lecture du PDF.

## Contrôle de cohérence P54N

Le programme de contrôle contrôle_qualite_passation_nova_p54o.py reconstruit exactement le paquet P54N canonique puis compare l'objet JSON fourni et, si présentes, les instructions Markdown. Une fausse clôture, un changement d'index, une autorisation inventée, un statut « accompli » ou un ajout de champ sensible entraînent le refus. Les deux empreintes des PDF sont celles **consignées par P54D**; la CI ne prétend pas retélécharger ou authentifier les originaux.

Un résultat « CONFORME_AUX_SOURCES_VERSIONNEES » signifie seulement qu'aucun changement par rapport au paquet généré n'a été constaté. Ce résultat ne constitue jamais une certification des PDF ou une autorisation de remise externe.

## Dix conditions de travail à instruire

| Phase | Étape non accomplie | Responsable envisagé |
|---|---|---|
| Avant remise | Autorisation écrite de remise, finalité et portée | Gouvernance à désigner |
| Avant remise | Destinataire habilité et conflits à examiner | Gouvernance à désigner |
| Avant examen | Accès autorisé aux pièces et diagnostic privé | Responsable des données à désigner |
| Examen initial | Localisation exacte des cinq occurrences | Examinateur documentaire à désigner |
| Examen initial | Qualification individuelle avec pièces | Examinateur documentaire à désigner |
| Après examen | Contre-revue distincte et contradictions | Contre-réviseur à mandater |
| Si pertinent | Interprétation juridique du R.A.V.Q. 1435 | Juriste à mandater |
| Si monétaire | Périmètre, unités et écritures réciproques | CPA à mandater |
| Avant conclusion | Vérification originale des signatures et habilitations | Autorité humaine compétente |
| Hors logiciel | Acte décisionnel réel, extérieur au programme | Autorité compétente |

**Important :** les deux premières conditions sont les préalables à une remise autorisée; les autres concernent l'instruction et la conclusion ultérieures. La présence des étapes conditionnelles n'affirme pas qu'il existe un litige, un montant à récupérer ou un besoin réel d'engager un professionnel.

## Commandes

Génération préalable du paquet public P54N :

    python scripts/preparer_passation_humaine_nova_p54n.py --dossier p54n_canonique.json --instructions p54n_canonique.md

Précontrôle P54O du paquet public et production de la matrice bloquée :

    python scripts/controler_qualite_passation_nova_p54o.py --paquet-p54n p54n_canonique.json --instructions-p54n p54n_canonique.md --plan p54o_plan_controle.json --rapport p54o_rapport_bloque.md --bilan p54o_bilan_neutre.json

Démonstration de refus automatique d'une remise présumée :

    python scripts/controler_qualite_passation_nova_p54o.py --exiger-transmission

Codes de sortie : **0** = conformité structurelle aux sources versionnées; **2** = contenu ou chemin refusé; **3** = refus d'une prétendue transmission automatique. Aucun résultat ne certifie une valeur financière.

## Décision

Les 40 tâches P54N, 96 contrôles P54B et huit contrôles P54C restent à instruire. L'authentification humaine des avis professionnels, les pièces primaires et les éventuelles analyses comptables sont manquantes. Aucun montant ni aucune économie n'est démontré. Les opérations Ville–RTC–SOMHAC déjà éliminées ne seront jamais comptées deux fois. Les emplois et services sont protégés et les deux scénarios constitutionnels doivent rester séparés.

**NO_GO_AUTOMATIQUE** : paquet non transmis, cinq observations non qualifiées définitivement, aucun contrat, aucun avis certifié, aucune fusion main, aucune opération SINJIRA.

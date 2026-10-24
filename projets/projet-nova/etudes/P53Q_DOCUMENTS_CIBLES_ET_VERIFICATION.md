# Projet Nova — P53Q : inventaire opérationnel des pièces et contreparties 2024

**22 octobre 2026 — étude préparatoire non adoptée, pièces encore non obtenues.**

## Objet et résultat technique

P53Q poursuit les six dossiers P53P : Montréal (66023), ARTM (T1025), Québec (23027), STM (T0081), RTC (T0088), et Saint-Valère (39135). Les cinq premiers conservent leurs rangs historiques P53H ; Saint-Valère est le code ajouté par la révision P53I, **hors du top 25**.

Chaque dossier reçoit les **17 familles de documents** ci-dessous, soit **102 emplacements à renseigner**. Il s'agit de catégories de preuves, non de 102 documents obtenus, ni de 102 envois de demandes, ni de 102 dépenses évitables.

### Inventaire complet par organisme

| Famille de pièce | Finalité probatoire |
|---|---|
| Compétence et identité juridique | Identifier l'organisme détenteur, le décideur habilité, la date et la juridiction |
| États financiers officiels 2024 (version précise) | Documenter la base d'exercice et les éventuelles révisions |
| Périmètre de consolidation 2024 | Empêcher le mélange de comptes déjà regroupés |
| Grand livre du payeur | Retrouver la contrepartie de charge et son numéro d'écriture |
| Grand livre du bénéficiaire | Retrouver la contrepartie de recette et son numéro d'écriture |
| Entente, résolution et avenants | Établir nature, compétence, modalités et conditions |
| Facture ou appel de quote-part | Confronter identité du débiteur, période, taxes, montant signé |
| Preuve de paiement | Vérifier la réalisation de la transaction et sa période |
| Éliminations déjà comptabilisées | Empêcher une **seconde élimination** de flux consolidés |
| Subventions et origine de financement | Distinguer sources municipales, provinciales et fédérales |
| Coût opérationnel de référence | Identifier charges évitables, fixes et incompressibles |
| Coûts de transition | Recenser les dépenses initiales et risques d'exécution |
| Coûts récurrents après changement | Comparer les coûts à service et périmètre équivalents |
| Transferts de coûts vers des tiers | Empêcher de déplacer des charges aux ménages et entreprises |
| Indicateurs de qualité et d'accès aux services | Mesurer délais, capacité, continuité, accès humain, satisfaction |
| Protection des emplois et conditions de travail | Documenter effectifs, temps de travail, salaires et droits |
| Avis indépendant comptable et juridique | Contrôler calculs, admissibilité, périmètres et pièces authentifiées |

Ces familles proviennent de la méthodologie P53K–P53P et sont une **liste de travail**, non une preuve qu'un document concret existe ou qu'un responsable est déjà désigné.

## Première pièce à rechercher pour chaque organisme

| Organisme | Première priorité documentaire | Justification du séquencement |
|---|---|---|
| Montréal | Périmètre de consolidation 2024 | Distinguer ville, agglomération, unités et organismes contrôlés avant les totaux |
| ARTM | Ententes, résolutions et avenants | Reconstituer les obligations et les contributions sans supposer un double emploi |
| Ville de Québec | Éliminations déjà comptabilisées | Éviter de réutiliser les écritures que le rapport consolidé signale comme éliminées |
| STM | Indicateurs de qualité, accès et disponibilité des services | Fixer les contraintes de qualité avant tout scénario administratif |
| RTC | Éliminations déjà comptabilisées | Reconcilier les entités du périmètre consolidé avec la Ville de Québec |
| Saint-Valère | États financiers originels de 2024 | Vérifier le dossier ajouté par la révision et l'année/source exactes |

Une priorité documentaire **ne correspond pas à une somme économisable**. Les autres 16 familles demeurent obligatoires pour tous les dossiers et leur classement interne n'autorise pas à sauter une pièce.

## Prévention du double compte Québec–RTC

Le rapport financier 2024 de la Ville de Québec indique que le **RTC entre dans son périmètre consolidé** et que les soldes/opérations réciproques sont éliminés. La mention est dans les notes annexes (p. imprimée 35, PDF index 34). La note non auditée sur la présentation du périmètre budgétaire (p. imprimée 197, PDF index 196) nécessite un examen séparé.

Source institutionnelle ciblée : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf

La présence d'une telle note ne permet pas d'affirmer que **toute** transaction donnée est appariée, ni qu'une autre élimination doit être faite. **Aucune somme liée aux recettes 2024 de Québec, du RTC ou d'autres organismes n'est utilisée comme réduction de dépense** dans P53Q.

## Processus d'usage

1. Identifier juridiquement l'organisme et son périmètre, sans confondre les niveaux municipal, provincial et fédéral.
2. Examiner les publications publiques déjà repérées par P53P et préciser **exactement la version** de chaque pièce.
3. Réunir ultérieurement, dans un espace autorisé et après vérification des règles de communication, le grand livre de chaque partie, l'entente, la facture et le paiement.
4. Réconcilier le flux : période, nature, montant signé, devise, code institutionnel et corrections, puis rechercher les éliminations **déjà** effectuées.
5. Évaluer séparément le coût administratif réellement évitable après investissements, frais récurrents et effets sur les autres administrations, sans réduction de personnel ou de qualité.
6. Obtenir une revue comptable/juridique indépendante et signée avant d'envisager une économie certifiée ou un changement fiscal.

Les demandes d'accès doivent être transmises aux **responsables compétents de chaque organisme**, selon les règles québécoises applicables. Une fiche préparée ne lance aucun délai de réponse. Le responsable peut confirmer qu'un document n'est pas détenu ou que l'accès est restreint. Références institutionnelles : https://www.quebec.ca/acces-information ; https://www.quebec.ca/gouvernement/travailler-gouvernement/normes-gouvernance-pratiques-internes/protection-des-renseignements-personnels/acces-aux-renseignements-personnels/reperage-documents ; https://www.cmq.gouv.qc.ca/fr/verification-municipale/questions-frequentes .

## Exécution contrôlée

    python scripts/inventorier_pieces_primaires_nova_p53q.py --bilan p53q_bilan.json --inventaire p53q_102_pieces.json
    python scripts/inventorier_pieces_primaires_nova_p53q.py --exiger-preuves-certifiees

Les déclarations locales optionnelles via --declaration ne contiennent **aucune pièce, facture, écriture, montant ou identité personnelle**. Le programme n'émet pas de demande, n'envoie aucun message, n'authentifie aucun original et n'agrège aucun montant de scénario. Codes de retour : **0** = structure conforme seulement, **2** = données invalides ou sortie existante, **3** = refus de certification.

## Décision et limites

**NO_GO_AUTOMATIQUE**. 0 original reçu et authentifié par P53Q, 0 appariement bilatéral vérifié, 0 économie certifiée, 0 avis indépendant signé, 20 preuves fiscales F01–F20 non validées, 1 320 montants financiers Nova inconnus, aucun taux adopté. Pas de fusion sur main, pas de collecte de fonds ou de données personnelles, pas d'intervention sur SINJIRA ni de dégradation des emplois ou services.

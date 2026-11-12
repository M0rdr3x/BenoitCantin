# Projet Nova — P54D : qualification prudente des cinq jetons numériques différents

**24 octobre 2026 — étude documentaire, pas audit de finances publiques.**

## Ancrage réel P54B et P54C

Ville de Québec, PDF 2024 index de page 102, et MAMH, index de page 162, ont été recapturés et vérifiés contre les SHA-256 de P53Z. Les deux publications contiennent les marqueurs du même **type de rapport d'auditeurs sur la ventilation des dépenses mixtes** entre compétences locales et d'agglomération, renvoyant au R.A.V.Q. 1435.

Les 40 tests P54C et les 23 contrôles complémentaires ont réussi. Référence : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40119313052

P54B a comptabilisé 10 occurrences numériques dans le texte de la page Ville, 13 côté MAMH, et 9 occurrences communes (coefficient Dice 0,7826). Il en reste exactement **une** sans équivalent Ville et **quatre** sans équivalent MAMH, soit **cinq occurrences, pas cinq erreurs**.

## Méthode P54D et prudence

P54D reprend sans altération la définition des jetons numériques de P54B; chaque occurrence est ensuite appariée une seule fois à l'occurrence identique de l'autre source. Un mot identique compté deux fois n'est pas éliminé deux fois s'il apparaît seulement une fois dans l'autre édition.

Pour les seules occurrences restantes, P54D utilise un **contexte court et local**, analysé uniquement en mémoire. Il classe la proximité de mentions de dates, de pagination, de règlements, d'identifiants ou de symboles de valeurs numériques. Les six catégories de sorties sont :
- ANNÉE/DATE PROBABLE;
- PAGINATION/FOLIO PROBABLE;
- RÉFÉRENCE RÉGLEMENTAIRE PROBABLE;
- COORDONNÉE/IDENTIFIANT PROBABLE;
- VALEUR CHIFFRÉE À QUALIFIER;
- INDÉTERMINÉE.

**Les catégories sont indicatives et ne prouvent pas la nature juridique ou comptable d'un jeton.** Un chiffre proche du symbole dollar reste une valeur potentielle, pas un montant établi dans un état financier. Aucun zéro et aucune somme d'économie ne sont inventés.

L'outil vérifie avant tout rapprochement l'empreinte SHA-256 calculée sur les octets de chaque copie HTTPS. Si un PDF a changé, s'il ne contient pas le rapport ciblé, ou si les nombres ne correspondent plus exactement aux valeurs P54B, l'analyse échoue de manière contrôlée et aucun rapprochement nouveau n'est publié.

## Protéger les originaux et les renseignements personnels

Le rapport public de la CI ne peut afficher les **valeurs numériques brutes** ni les **passages de texte**. Il contient seulement le nombre de classes, la source Ville/MAMH de chaque occurrence, une zone approximative dans la page et un niveau explicitement NON CERTIFIÉ.

Une option distincte permet à un professionnel habilité de produire un diagnostic privé local, comprenant valeurs et courts contextes. **L'option ne doit jamais être utilisée dans GitHub Actions** et le fichier doit impérativement être conservé hors dépôt Git, avec permissions 0600. Les documents PDF restent en mémoire; ni les originaux ni les diagnostics privés ne sont transférés dans le dépôt ou dans les artefacts de la CI.

## Exécution

Aucun appel réseau, état préparatoire :

    python scripts/classer_ecarts_numeriques_nova_p54d.py --bilan p54d_neutre.json

Analyse par recapture de deux PDF publics inchangés :

    python scripts/classer_ecarts_numeriques_nova_p54d.py --reanalyser-copies --bilan p54d_typologie_publique.json

Option privée uniquement pour contrôle humain local, **hors Git** :

    python scripts/classer_ecarts_numeriques_nova_p54d.py --reanalyser-copies --diagnostic-prive /repertoire_prive/p54d_contextes.json --bilan p54d_public.json

Exiger une prétendue certification doit échouer :

    python scripts/classer_ecarts_numeriques_nova_p54d.py --exiger-preuve-comptable

Codes de retour : 0 = conformité structurelle ou classification indicative complète; 2 = paramètre ou destination interdit; 3 = refus explicite d'une certification; 4 = source modifiée/indisponible, page non pertinente ou chiffres non reproduits.

## Décision institutionnelle

Les **96 contrôles de comparabilité P54B** et les **8 contrôles contextuels P54C** ne sont pas réputés résolus par la classification d'un jeton. Toute comparaison de montants réels nécessitera les rubriques, conventions de signe, unités, statuts d'audit, grands livres réciproques et avis indépendants.

Les opérations Ville–RTC déjà éliminées n'impliquent pas de nouvelles économies. Les garanties d'emploi, de qualité et d'accès aux services sont préservées. Les scénarios du Québec au Canada et du Québec souverain hypothétique ne doivent pas être confondus.

**NO_GO_AUTOMATIQUE : zéro économie certifiée, zéro irrégularité financière démontrée, aucune fusion main.** SINJIRA reste indépendant.

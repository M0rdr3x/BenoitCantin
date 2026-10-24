# P53Y — Registre de versions documentaires et vérification croisée des métadonnées

**24 octobre 2026.** Ce jalon complète la première application documentaire P53W, puis le comparateur PDF P53X. Il ne constitue pas un audit comptable, une expertise de provenance ou une validation d'un gain financier.

## Situation vérifiable

- Le rapport financier municipal 2024 de la Ville de Québec est référencé ici : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf
- Le dossier financier 2024 mis à disposition par le MAMH est référencé ici : https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf
- Le rapport municipal indique une consolidation ligne par ligne incluant le RTC et la SOMHAC, avec opérations réciproques déjà éliminées, dans ses notes de la page imprimée 35. La section budgétaire de la page 197 porte la mention « Non audité ».
- Le MAMH peut présenter les documents dans un PDF assemblé. Deux fichiers de longueurs ou de paginations différentes ne prouvent pas que les comptes sont contradictoires.
- Les fichiers PDF officiels eux-mêmes ne sont pas présents dans cette branche de travail. Aucune empreinte authentifiée, signature d'émetteur, équivalence réelle entre versions officielles ou économie chiffrée n'est déclarée.

## Ce que P53Y apporte

Le logiciel prépare **deux registres de sources et douze points de revue** (six par source) :

1. Provenance de la source, version exacte et identité institutionnelle.
2. Intégrité des octets avec référence de hachage fiable.
3. Pagination et extraction de texte, y compris pages indéterminées.
4. Droits d'accès, confidentialité et droits des tiers.
5. Comptabilité, périmètre consolidé, contreparties et écritures déjà éliminées.
6. Expertise comptable et juridique indépendante, sauvegardes des emplois et services.

Le registre initial contient zéro version officiellement authentifiée, zéro avis indépendant signé, zéro analyse comptable certifiée et un gain financier **inconnu (null)**, jamais assimilé à zéro.

## Deux catégories de données

Les **fiches de versions déclarées** sont des fichiers JSON conservés localement hors GitHub. Une fiche peut décrire la date, le canal de réception, l'empreinte SHA-256, la taille et le nombre de pages déclarés. Elle doit conserver le statut non authentifié. Elle ne peut ni contenir les noms ou coordonnées des détenteurs ni déclarer un avis professionnel certifié.

Un **détail privé P53X** optionnel peut être importé pour contrôler les métadonnées et la cohérence interne du rapprochement : les empreintes annoncées, l'indicateur d'identité binaire, les comptes de pages, les paires de pages uniques et les trois ancrages P53W. P53Y ne lit pas le PDF original et ne refait **pas** le calcul SHA-256. Il confronte seulement deux séries de déclarations : une concordance ne prouve donc ni l'identité de l'émetteur, ni l'exactitude des originaux, ni l'indépendance des experts.

Une mention « accès interdit » ou « risque pour les emplois et services » place le dossier dans un statut de suspension. Les statuts restent déclaratifs. Le programme ne ferme aucune anomalie et n'en accuse aucun organisme.

## Exécution

Registre initial sans aucune prétendue copie obtenue :

    python scripts/enregistrer_versions_documentaires_nova_p53y.py --rapport bilan.json --registre registre.json

Réconciliation de deux fiches locales avec le détail produit par P53X :

    python scripts/enregistrer_versions_documentaires_nova_p53y.py --detail-p53x /repertoire_prive/detail_p53x.json --fiche /repertoire_prive/ville.json --fiche /repertoire_prive/mamh.json --rapport bilan.json

Refus explicite de toute attestation non fondée :

    python scripts/enregistrer_versions_documentaires_nova_p53y.py --exiger-authentification

**Codes :** 0 = structure et cohérence déclarative uniquement; 2 = incohérence, fichier hors périmètre ou écrasement interdit; 3 = refus attendu d'une certification automatique.

Le rapport public est agrégé : ni adresse de fichier, ni date de collecte, ni hash, ni identité. Les documents réels et les détails privés sont exclus de GitHub et de ses artefacts CI. Le workflow utilise des exemples purement synthétiques.

## Préconditions à toute conclusion financière

Les six questions bloquantes de P53W demeurent. Les grands livres payeur/bénéficiaire, les éliminations comptables déjà enregistrées, les coûts de transition et les avis indépendants signés sont toujours nécessaires. Le Québec dans le Canada et le Québec indépendant hypothétique restent deux périmètres distincts. Aucun retrait d'emploi, aucune réduction de service essentiel et aucune hausse cachée de coûts aux citoyens ne peut être justifié par ces contrôles.

**NO_GO_AUTOMATIQUE** — aucune version officiellement authentifiée, aucune économie certifiée, aucune fusion dans main, aucun changement à SINJIRA.

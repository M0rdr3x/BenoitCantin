# P53Z — Capture réelle conditionnelle de publications financières publiques

**24 octobre 2026.** Les deux documents publics 2024 visés sont le rapport financier de la Ville de Québec et la publication correspondante du MAMH.

## Sources

- Ville : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf
- MAMH : https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf
- Présentation des publications MAMH : https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/publications-financieres/rapport-financier

Le MAMH précise que les pièces financières peuvent être réunies dans un PDF assemblé et mises à jour. La date d'une acquisition HTTP ne prouve ni la date de production d'un document ni l'identité d'une édition juridiquement définitive.

## Exécution et résultat attendu

P53Z tente de récupérer deux fichiers depuis des domaines institutionnels fixés dans le code. Les certificats TLS sont contrôlés par défaut, les redirections sont limitées aux mêmes domaines officiels, les fichiers sont plafonnés à 64 Mio et le format PDF est contrôlé avant une comparaison par le programme P53X. Les fichiers sont gardés seulement en mémoire volatile. Ils ne rejoignent jamais le dépôt GitHub ni les artefacts de la CI.

Une capture réussie produira dans le bilan une taille et une empreinte SHA-256 **de la copie téléchargée**, avec un horodatage UTC réel de l'acquisition. Il ne s'agit pas d'une signature numérique de la Ville ou du MAMH. Le texte extrait et les fichiers originaux ne sont pas diffusés.

Une acquisition refusée ou un serveur injoignable conduira à un statut explicite ECHEC_ACQUISITION avec une catégorie d'erreur. Aucun faux SHA-256 ne doit être produit. Deux téléchargements réussis permettront de comparer pages, empreintes et textes. Deux sources institutionnelles ne deviennent pas pour autant deux audits indépendants.

## Commandes

Sans accès réseau :

    python scripts/acquerir_publications_nova_p53z.py --bilan etat_neutre.json

Tentative effective des deux seules publications publiques :

    python scripts/acquerir_publications_nova_p53z.py --acquerir --bilan copies_publiques.json

Interdire toute prétendue authentification :

    python scripts/acquerir_publications_nova_p53z.py --exiger-authenticite

Codes de sortie : 0 signifie que la commande s'est terminée, avec comparaison réussie ou aucun essai demandé; 4 signifie que l'acquisition/comparaison effective n'a pas abouti; 2 indique une erreur technique de l'outil; 3 confirme le refus de certification. Un workflow CI réussi avec code d'acquisition 4 ne confirme **pas** l'acquisition des deux publications : consulter séparément les champs copies_https_observees et comparaison_octets_officiels_effectuee.

## Limites non négociables

Le rapport 2024 de la Ville indique que RTC et SOMHAC sont dans le périmètre comptable et que les opérations réciproques sont déjà éliminées (page 35). La section budgétaire de la page 197 est explicitement non auditée. Il est interdit de transformer une différence entre fichiers PDF ou une écriture réciproque déjà éliminée en économie financière future.

Les grands livres, les pièces transactionnelles, le maintien de l'emploi et de la continuité des services et les avis juridiques/comptables indépendants signés restent nécessaires. P53Z ne prétend pas résoudre les six questions bloquantes P53W. Les scénarios constitutionnels Québec dans le Canada et Québec indépendant hypothétique restent distincts.

**NO_GO_AUTOMATIQUE** : aucune économie certifiée, aucun taux fiscal modifié, aucune fusion sur main et aucune modification de SINJIRA.

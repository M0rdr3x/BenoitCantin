# P55B — Acquisition et recevabilité des deux sources officielles, préparation des mandats (3 novembre 2026)

**État réel : deux URL officielles identifiées; aucune copie PDF obtenue et hachée dans cette étape; aucun expert contacté ni mandat signé.** P55B prolonge P55A et complète P54Q/P54H : il ne refait pas un audit, n'invente pas une économie et ne donne aucune autorisation d'engagement.

## Sources exactes à acquérir localement

| Code | Publication officielle | Index PDF zéro (P54Q) | Taille historique | Empreinte historique SHA-256 |
|---|---|---:|---:|---|
| VILLE_2024 | [Ville de Québec — Rapport financier 2024](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf) | 102 | 8 984 919 octets | `b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399` |
| MAMH_23027_2024 | [MAMH — Rapport financier consolidé 2024, organisme 23027](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf) | 162 | 10 818 312 octets | `4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00` |

Les deux adresses ont été repérées sur des domaines publics institutionnels au 3 novembre 2026. Le contenu intégral en octets **n'a pas été téléchargé ni comparé** dans ce jalon. Les deux empreintes et tailles sont celles du **registre historique P54Q** du projet, pas des constats de téléchargement le 3 novembre 2026. Les autorités peuvent republier ou corriger un document à la même adresse; une différence doit être conservée comme **édition distincte à instruire**, et jamais contournée par mise à jour silencieuse des empreintes de référence.

**Important :** SHA-256 identique prouve la concordance des octets avec la copie historique de référence, pas une origine institutionnelle authentifiée, la valeur juridique du document, la nature d'une observation, ni une économie.

## Répartition des observations

- Source Ville, page PDF index zéro 102 : `P54E-V-001`.
- Source MAMH, page PDF index zéro 162 : `P54E-M-001`, `P54O-DATE-001` (année/date probable), `P54E-M-002`, `P54E-M-003`.
- Les **quatre dossiers P54E** demeurent indéterminés; la cinquième référence est une observation de date à qualifier, pas un montant financier.

## Huit étapes opérationnelles, sans action extérieure automatique

1. **Acquisition** par un responsable documentaire humain habilité : télécharger ou obtenir les deux publications depuis leurs canaux officiels et conserver les fichiers **hors Git**, selon les règles d'accès.
2. **Confrontation d'édition** : comparer localement PDF, tailles et SHA-256 aux références P54Q. Un changement d'édition entraîne une suspension de la comparaison historique et l'établissement d'un nouveau dossier de provenance, pas l'écrasement des anciennes empreintes.
3. **Droits et origine** : vérifier la provenance, les dates de publication, les autorisations de consultation et les restrictions documentaires; distinguer rapport public et annexes éventuellement protégées.
4. **Localisation et qualification** : revoir les cinq observations sur les pages visuelles, comparer l'extraction NFKC et garder séparées les classifications date, référence, folio et véritable valeur monétaire.
5. **Réserves/suspensions** : documenter désaccords et contre-examens; aucune absence de fiche ne doit effacer une suspension P54Z/P55A.
6. **Mandats écrits** : reprendre séparément les projets `MANDAT-COMPTABLE-2024` et `MANDAT-JURIDIQUE-2024` de P54H; soumettre leurs compétences, conflits d'intérêts, honoraires non incitatifs et limites à une gouvernance réelle; **aucun envoi ni nomination par le programme**.
7. **Avis d'expert et vérification** : seuls les professionnels réellement mandatés peuvent rendre des avis, assortis de la vérification humaine de l'identité, des permis, des signatures et des réserves, sous confidentialité et avec contre-revue.
8. **Décision institutionnelle** : hors du logiciel, sur la base des originaux et des preuves authentifiées; aucune conclusion fiscale automatique.

Le programme `scripts/controler_acquisition_sources_nova_p55b.py` permet **une comparaison cryptographique des copies locales publiques**. Il accepte les déclarations privées facultatives P54Z et P55A pour consolider des compteurs non authentifiés. **Il ne télécharge, ne contacte, n'envoie et ne rémunère personne.**

## Commandes pour l'opérateur autorisé

1. Disposer d'un environnement local où les deux PDF de référence sont enregistrés **hors du dépôt**, sans lien symbolique, avec accès `0600`. Vérifier les droits et l'intégrité des fichiers auprès des sources officielles.
2. Contrôler les deux fichiers sans produire aucun résultat monétaire :

```bash
python scripts/controler_acquisition_sources_nova_p55b.py \
  --ville-pdf /stockage_hors_git/ville2024.pdf \
  --mamh-pdf /stockage_hors_git/mamh23027_2024.pdf \
  --bilan-public /stockage_hors_git/p55b_bilan.json
```

3. Pour relier la déclaration P55A à P54Z, fournir `--declarations-p54z /stockage_hors_git/p54z.json --relecture-p55a /stockage_hors_git/p55a.json`. **Aucun de ces chemins privés ne doit être utilisé dans GitHub Actions**, ni versé à un artefact ou au dépôt.
4. Produire un plan public **non nominatif** avec `--plan-public /stockage_hors_git/p55b_plan.json`. Sans fichiers PDF le bilan restera `NON_FOURNIE`.
5. L'option `--exiger-go` retourne un refus explicite, même si les deux SHA concordent.

**Codes de sortie :** 0 = contrôle technique réalisé sans authentification; 2 = entrée/sortie ou schéma rejeté; 4 = copie fournie d'une édition différente, non retenue pour reproduction historique; 3 = prétention à une autorisation ou certification automatiquement refusée.

Les comparaisons financières P54B (96) et P54C (8), 40 tâches P54N et 10 blocages P54O restent ouverts. Les éliminations comptables Ville–RTC–SOMHAC ne constituent pas de nouvelles économies; aucune réduction d'emplois, de services ou de pouvoir d'achat ne peut être justifiée sans analyse vérifiée. Les régimes Québec au sein du Canada et Québec souverain hypothétique ne se confondent pas. PR en brouillon, pas de fusion `main`, aucun changement SINJIRA.

**Décision : `NO_GO_AUTOMATIQUE`.**

# Projet Nova — P53D : acquisition d'un profil municipal 2024 et garde-fous d'interprétation

**21 octobre 2026 — archive d'une extraction textuelle MAMH, non une comptabilité consolidée.**

## Résultat effectivement obtenu

Le fichier public **Profil financier des municipalités 2024-2025, données 2024 agrégées pour le Québec**, publié par le ministère des Affaires municipales et de l'Habitation, est accessible :

- Catalogue : https://www.donneesquebec.ca/recherche/dataset/profil-financier-des-municipalites-locales/resource/5dec077d-4ef9-4e22-99e9-0c4f3a6dd52d
- CSV : https://mamh.gouv.qc.ca/fichiersdonneesouvertes/PF-2024-2024-Prov.csv
- Licence indiquée sur Données Québec : **CC BY 4.0**; attribution au MAMH.
- Fichier de travail dans la PR : `projets/projet-nova/etudes/sources/P53D_MAMH_PROFIL_2024_AGREGAT_QUEBEC_CAPTURE.csv`.
- Champs : trois identifiants (`an_edition`, `an_donnee`, `cod_prov`) et **38 colonnes codées**, une ligne agrégée `2024,2024,PROV`.

La capture a été produite par un outil d'extraction et enregistrée telle qu'obtenue sous forme de texte. **Ce n'est pas une copie binaire authentifiée des octets du CSV original.** Le SHA Git du contenu capturé est `6acff78c6fd6122d6630f0a8f8eea7e59e265946`; il ne doit pas être appelé SHA-256 de l'original. L'empreinte SHA-256 du fichier d'origine demeure **inconnue**. La fiche Données Québec indique une dernière modification en septembre 2026.

**Constat important :** les colonnes `CIALC*`, `CIAIC*` et `CIIIC*` sont des indicateurs codés. Sans le dictionnaire d'indicateurs, leurs unités et leur base de calcul, leur valeur ne peut pas devenir une recette d'impôt foncier en dollars ou un total des taxes de toutes les municipalités. Le code refuse explicitement une telle conversion.

## Statistique Canada toujours incomplet

Le tableau 10-10-0020-01 (`10100020`) demeure la cible statistique pour des finances locales en millions de dollars : https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001. L'API officielle est décrite par [Statistique Canada](https://www.statcan.gc.ca/en/developers/wds/user-guide). La tentative d'accès au ZIP officiel a donné une réponse HTML d'indisponibilité et l'accès à l'API n'a pas permis une extraction exploitable dans cette séance. **Aucun ZIP authentifié, aucun total géographique 2024 Québec et aucun fichier de métadonnées StatCan n'ont été archivés.** La capture MAMH ne remplace pas automatiquement le tableau StatCan.

## Deux questions non résolues dans P53A

- **E04 :** taxes foncières réellement perçues par les municipalités québécoises en 2024, selon une liste précise de collectivités et un périmètre non doublonné.
- **E05 :** autres revenus locaux perçus en 2024, dont recettes non fiscales, transferts, impositions de droits et frais; distinguer les transferts entre niveaux de gouvernement.

Ces deux montants restent **`null`**, non zéro. Les **166 492 M$** du budget provincial 2026-2027 (P53A) et les **43 549,895 M$** d'impôt fédéral net des particuliers de 2024 (P53C) ne sont pas additionnés à un total « Québec »; exercices, couvertures et destinataires divergent.

## Véritable suite d'acquisition

1. Obtenir un ZIP officiel intact du tableau StatCan 10-10-0020-01 ou un export MAMH par poste budgétaire plutôt qu'un simple profil d'indicateurs.
2. Conserver les **octets bruts**, leur SHA-256, la version, les métadonnées et les licences.
3. Contrôler le dictionnaire des codes, le périmètre des administrations, les sources de taxes et les transferts interadministrations; isoler l'année 2024 et les éventuelles notes de suppressions/révisions.
4. Compléter E04/E05 uniquement à partir de postes de recettes libellés, exprimés en dollars ou millions de dollars et vérifiés par deux voies indépendantes.
5. Confier la consolidation 2024–2026‑2027 à une expertise fiscale et comptable réelle, avec préservation de la non-adoption.

### Exécution documentaire

```bash
python scripts/auditer_donnees_municipales_nova_p53d.py --rapport p53d_bilan.json --export-csv p53d_champs_mamh.csv
python scripts/auditer_donnees_municipales_nova_p53d.py --exiger-recettes-municipales
```

Le succès technique confirme la cohérence du **fichier capturé**, jamais celle d'un total municipal ou d'un financement fiscal Nova. **NO_GO_AUTOMATIQUE** pour tout taux, fusion, diffusion comme réforme adoptée ou attribution de mandat. Les 20 preuves restent non validées et les 1 320 valeurs financières Nova demeurent inconnues.

# Projet Nova — P53H : priorisation des vérifications comptables interorganismes (2024)

**21 octobre 2026 — État de recherche non consolidé.** Ce document ne crée aucune accusation envers les organismes mentionnés et ne présente pas les flux reçus comme des doubles comptes.

Les fichiers sources proviennent des [Données réelles 2024 du MAMH](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents), et le [Manuel de la présentation de l'information financière municipale](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/information-financiere/presentation/manuel) définit les transferts, quotes-parts et périmètres d'organismes municipaux. Dans les comptes, les quotes-parts peuvent notamment servir au financement des MRC, régies, communautés et organismes de transport, mais **aucun lien payeur-bénéficiaire individuel n'a été démontré dans notre extraction**.

## Ce qui est mesuré

Les **1 343 organismes** sont répartis entre municipalités locales, MRC, régies intermunicipales, communautés métropolitaines et organismes de transport. Les flux candidats sont la **somme signée des recettes de quotes-parts (CRIIX00408) et de transferts (CRIIX00409)**, avec les blancs conservés distinctement. Les sommes négatives restent négatives. Le rang compare la valeur absolue de cette somme et non le niveau de fraude, d'erreur ou de duplication.

| Type | Organismes | Flux de quotes-parts et transferts 2024 (CAD) |
|---|---:|---:|
| Municipalité locale | 1094 | 6 223 496 057 |
| Municipalité régionale de comté | 85 | 1 029 814 166 |
| Communauté métropolitaine | 2 | 110 339 077 |
| Régie intermunicipale | 150 | 457 926 937 |
| Organisme public de transport | 12 | 3 042 705 964 |
| **Total brut signé** | **1 343** | **10 864 282 201** |

Les **25 premiers organismes** par montant absolu représentent **7 069 371 200 $**, soit environ **65,1 %** de l'exposition signée totale; cette mesure de concentration aide à **prioriser une revue**, elle n'établit ni contrepartie ni montant à éliminer. La liste nominative, les codes MAMH, les valeurs brutes de chaque composante et les réserves sont dans `P53H_PRIORITES_VERIFICATION_2024.json`.

## Nouvelle méthode de travail opérationnelle

Pour chaque organisme priorisé, la vérification doit localiser le **payeur réel** et son **poste de dépense**, ainsi que l'écriture du bénéficiaire et la période. Les recettes des deux parties ne prouvent pas à elles seules un double compte : certaines charges ne sont pas incluses dans les seuls postes de revenus. Pour neutraliser un flux consolidé, contrôler l'identité des administrations, la nature, le montant, les signes, les transferts intergouvernementaux et les états déjà consolidés, puis obtenir un avis indépendant.

Un journal complet de 1 343 lignes peut être généré; les champs `payeur_identifie`, `ecriture_reciproque`, `preuve_documentaire` y sont volontairement vides. Le classement ne permet pas de déduire des économies de 7,069 G$ ni 10,864 G$.

Les données observées couvrent l'exercice **2024**. Elles ne sont pas additionnées directement au budget du Québec **2026-2027**, ni aux montants fédéraux, ni traitées comme recettes garanties d'un Québec souverain. **F01–F20 demeurent non validées, 1 320 paramètres financiers Nova demeurent inconnus, PR #673 brouillon, aucune fusion ou adoption.**

```bash
python scripts/valider_priorites_rapprochement_nova_p53h.py --rapport p53h_bilan.json --export-csv p53h_journal_1343_organismes.csv
python scripts/valider_priorites_rapprochement_nova_p53h.py --exiger-appariement
```

Code 0 : contrôles historiques reproductibles avec `NO_GO_AUTOMATIQUE`. Code 2 : fichier, calcul ou statut invalide. Code 3 : impossibilité de certifier des éliminations sans rapprochement réciproque et avis humain.

# P55C — Réception probatoire et rapprochement des cinq observations PDF 2024

**3 novembre 2026 — protocole local, non certifiant.** P55C complète P55B et reprend les mécanismes de reproduction historique P54Q/P54P. Aucun original PDF n'a été obtenu dans ce jalon et aucune revue professionnelle authentifiée n'a été effectuée.

## Séquence opérationnelle

La revue doit commencer par la **réception locale des deux PDF publics** (Ville de Québec et MAMH, organisme 23027). Leurs tailles et SHA-256 sont comparés aux copies historiques référencées dans P54Q. Une discordance **suspend le rapprochement de cette version** : une mise à jour silencieuse du SHA historique est interdite. Une concordance octet à octet ne certifie pas l'origine institutionnelle ou les conclusions comptables.

**Après concordance des deux copies**, l'algorithme P54Q/P54P doit reproduire les cinq observations à partir du texte des PDF. Une reproduction technique n'est pas une revue sur la page visuelle, et les offsets NFKC ne sont pas des coordonnées PDF. En cas d'absence, d'édition différente ou d'échec de reproduction, aucune fiche privée P55C utilisable ne peut être produite. Le programme ne produit aucun texte brut ni extrait, ni copie PDF dans ses bilans.

Les cinq références documentaires, avec index de page PDF de base zéro, sont :

| Référence | Source | Index PDF | Observation P54D | Qualification initiale indicative |
|---|---|---:|---:|---|
| P54E-V-001 | Ville | 102 | 0 | Indéterminée |
| P54E-M-001 | MAMH | 162 | 1 | Indéterminée |
| P54O-DATE-001 | MAMH | 162 | 2 | Année/date probable, non confirmée |
| P54E-M-002 | MAMH | 162 | 3 | Indéterminée |
| P54E-M-003 | MAMH | 162 | 4 | Indéterminée |

## Fiche locale de travail (hors Git)

Uniquement après reproduction technique intégrale : créer la **fiche privée P55C**. Elle contient cinq références fixées, chacune liée aux mêmes pages et positions NFKC reproduites par P54Q, sans commentaire libre, identité, signature ou montant. La fiche conserve l'état `NON_EXAMINE` jusqu'à examen visuel humain réel; les autres états déclaratifs possibles sont `REPERE_DECLARE_NON_AUTHENTIFIE`, `RESERVE_OUVERTE`, `SUSPENDU`.

Une qualification déclarée peut être : non qualifiée, date probable, folio, référence normative, identifiant, ou valeur à examiner. **Même `VALEUR_A_EXAMINER_NON_CERTIFIEE` ne vaut pas montant, écart ou économie.** La contre-revue peut être déclarée distincte, mais le programme n'authentifie pas la personne ni son indépendance.

Le statut `REPERE_DECLARE_NON_AUTHENTIFIE` requiert **les huit contrôles P54Z et les dix points P55A déclarés préparés sur cette référence**; les statuts `RESERVE` ou `SUSPENDU` de l'amont empêchent cet état. Une fiche complète ne peut lever une réserve ancienne. Toutes les étapes d'expertise, signature et décision institutionnelle restent **à réaliser hors logiciel**.

## Utilisation locale, après obtention réelle des PDF

1. Installer la version de `pypdf` prescrite par P54Q (`pypdf==5.9.0`) dans un environnement adapté, sans introduire les originaux dans Git.
2. Enregistrer les deux PDF publics dans un répertoire **hors dépôt**, sans lien symbolique, avec droits `0600`.
3. Générer la fiche locale vierge *seulement après reproduction des cinq positions* :

```bash
python scripts/rapprocher_pieces_documentaires_nova_p55c.py \
  --ville-pdf /hors_git/ville2024.pdf \
  --mamh-pdf /hors_git/mamh2024.pdf \
  --creer-fiche-privee /hors_git/p55c_fiche.json
```

4. Pour lire une fiche P55C renseignée, les déclarations P54Z/P55A correspondantes sont obligatoires :

```bash
python scripts/rapprocher_pieces_documentaires_nova_p55c.py \
  --ville-pdf /hors_git/ville2024.pdf \
  --mamh-pdf /hors_git/mamh2024.pdf \
  --declarations-p54z /hors_git/p54z_fiche.json \
  --relecture-p55a /hors_git/p55a_fiche.json \
  --fiche-privee-p55c /hors_git/p55c_fiche.json \
  --bilan-public /hors_git/p55c_bilan.json
```

5. Sans PDF, le bilan est strictement neutre (`NON_TENTE`). Avec éditions divergentes ou reproduction échouée, le traitement retourne un statut `NON_REPRODUIT`, sans créer de fiche. Les résultats publics ne contiennent aucun chemin privé, offset, jeton, SHA de fiche ou catégorie par référence.

**Codes :** 0 = schémas acceptés et/ou reproduction technique complète, toujours sans attestation; 2 = refus d'entrée, fichier ou schéma non conforme; 3 = refus d'un faux GO; 4 = sources fournies mais version ou reproduction non conforme.

La matrice P55C ne modifie pas l'analyse P54B/P54C : **96 et 8 contrôles restent non attestés**, tout comme 40 tâches P54N et dix blocages P54O. Quatre dossiers P54E et la date probable demeurent ouverts. Un rapprochement des dépenses Ville–RTC–SOMHAC ne constitue pas une économie si les opérations réciproques sont déjà éliminées; protéger les effectifs, la continuité des services et le pouvoir d'achat. Québec au Canada et Québec souverain hypothétique restent deux scénarios distincts.

**NO_GO_AUTOMATIQUE — aucun expert engagé, aucune signature authentifiée, aucune économie certifiée, aucune fusion `main`, aucune intervention SINJIRA.**

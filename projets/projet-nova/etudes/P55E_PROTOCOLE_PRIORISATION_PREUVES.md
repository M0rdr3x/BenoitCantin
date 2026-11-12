# P55E — Priorisation des preuves manquantes, droits d'accès et parcours d'expertise

**3 novembre 2026 — préparation opérationnelle sans certification.** P55D a réussi 69 tests synthétiques ([Actions #41744420776](https://github.com/M0rdr3x/BenoitCantin/actions/runs/41744420776)). Ces tests n'ont pas contrôlé les octets des deux PDF publics actuels, ni reçu d'avis professionnel. P55E **ne crée pas de preuve absente** et ne contacte personne.

## Pourquoi P55E

Les jalons P55A–P55D définissent des précautions et des fiches, mais la chaîne reste bloquée en amont faute de contrôle sur les deux **copies historiques exactes** du rapport financier 2024 de la Ville de Québec et du rapport MAMH de l'organisme 23027. Les empreintes historiques P54Q permettent de détecter une **édition différente**; elles ne prouvent pas à elles seules la provenance institutionnelle.

P55E fournit **une file de travail conditionnelle et triée**, et non une promesse de conformité. Elle indique ce qui doit être fait **maintenant** avant les étapes dépendantes, et conserve les réserves au lieu de les effacer.

## Priorités vérifiables

| Ordre | Dépendance / obstruction | Action humaine attendue | Accès |
|---|---|---|---|
| 1 | Une copie PDF manque | Obtenir les copies historiques 2024 et les garder hors du dépôt | Rapport public |
| 1 | Une copie PDF diffère | Documenter l'édition et sa provenance; interdire l'écrasement de l'ancienne référence | Vérification documentaire |
| 2 | Les deux octets concordent, mais les cinq occurrences ne se reproduisent pas | Exécuter P54Q/P55C et instruire l'échec technique, sans lire de faux montants | Examen autorisé |
| 3 | Les cinq positions sont reproduites | Examiner les pages visuelles, leurs colonnes/unités, le R.A.V.Q. 1435 et les restrictions de droit d'accès | Personnel habilité |
| 4 | Réserves, suspensions, contradictions ou documents inaccessibles | Conserver les obstacles et organiser une véritable contre-revue | Revue indépendante |
| 5 | Examen comptable/juridique à conduire | Soumettre les deux projets de mandat P54H à la gouvernance humaine, vérifier titre, permis, conflits, mission, coûts et secret professionnel | Mandat autorisé |
| 6 | Aucun avis indépendant authentifié | Recevoir et vérifier manuellement les originaux, signatures, limites et désaccords | Autorité humaine |
| 7 | Aucune décision formelle | Décision institutionnelle indépendante du logiciel | Autorité compétente |

Dans le cas initial observé, **la prochaine action n'est pas l'embauche automatique d'un expert** : c'est l'obtention puis la confrontation exacte des deux PDF. Les cinq observations demeurent quatre dossiers P54E ouverts et une **date/année probable**. L'outil ne se prononce pas sur des économies.

## Parcours de traitement

Le script `scripts/prioriser_pieces_manquantes_nova_p55e.py` accepte deux modes :

- **Plan sans pièce** : produit un rapport public neutre et ordonne l'acquisition des publications, puis les vérifications futures. Ne prétend à aucun contrôle réel.
- **Examen local sur copies réelles** : reprend la vérification historique P54Q et les cinq positions P55C; lorsque les fiches P54Z, P55A, P55C et P55D sont fournies **ensemble**, il valide leur chaînage et établit une matrice privée de priorité par observation, sans copier de jetons, d'offsets, de noms, d'extraits ni de signatures. La matrice privée n'est jamais téléversée dans GitHub.

Commandes, depuis la racine du dépôt :

```bash
python scripts/prioriser_pieces_manquantes_nova_p55e.py \
  --plan-public /hors_git/p55e_plan_public.json \
  --bilan-public /hors_git/p55e_bilan_public.json
```

```bash
python scripts/prioriser_pieces_manquantes_nova_p55e.py \
  --ville-pdf /hors_git/ville2024.pdf --mamh-pdf /hors_git/mamh2024.pdf \
  --declarations-p54z /hors_git/p54z.json --relecture-p55a /hors_git/p55a.json \
  --fiche-p55c /hors_git/p55c.json --suivi-p55d /hors_git/p55d.json \
  --plan-prive /hors_git/p55e_plan_local.json \
  --bilan-public /hors_git/p55e_bilan_public.json
```

**Contrôles stricts :** `pypdf==5.9.0`; fichiers privés `0600`, hors dépôt et sans liens symboliques; destinations inexistantes; aucune combinaison partielle des fiches privées; aucune insertion de texte ou d'identifiants libres; aucune transmission extérieure.

**Codes :** 0 = plan/bilan produits sans authentification; 2 = entrée, chemin ou chaîne non conforme; 4 = PDF d'édition divergente ou reproduction historique non aboutie; 3 = refus explicite de `--exiger-go`.

## Décisions et données à ne pas extrapoler

Les **40 exigences P55D**, les 40 tâches P54N, dix blocages P54O, 96 contrôles P54B et huit P54C ne sont pas des économies. Même 40 préparations déclarées ne remplacent pas la réception des pièces primaires, un mandat signé, un avis professionnel authentifié ni une décision compétente.

Aucune double prise en compte d'éliminations entre Ville de Québec, RTC et SOMHAC. La continuité des emplois et services et le pouvoir d'achat doivent être préservés. Les scénarios **Québec au Canada** et **Québec souverain hypothétique** restent séparés.

**Décision : `NO_GO_AUTOMATIQUE`.** Aucun contact, aucune dépense ou envoi automatisé, aucune fusion dans `main`, aucune modification SINJIRA.

# P55G — Reçu local d'intégrité des rapports financiers 2024

**Nature : contrôle d'intégrité des copies locales, sans certification institutionnelle ni expertise comptable.** Le statut P55F a été validé dans GitHub Actions ([run #41750982513](https://github.com/M0rdr3x/BenoitCantin/actions/runs/41750982513), 60 tests synthétiques). Les deux copies PDF de 2024 n'ont toujours **pas été acquises et relues sur leurs octets réels** dans cette chaîne d'analyse.

## Finalité

Le registre P54Q fixe des empreintes historiques; P55B compare les octets; P55C localise cinq occurrences; P55D et P55E structurent les preuves et obstacles; P55F bloque les faux gains. P55G permet d'**enregistrer et de recontrôler** les octets d'une **paire de PDF locaux** dans un reçu non écrasant, afin de détecter une copie modifiée, une édition divergente ou un changement de fichier pendant le traitement.

Deux références publiques prédéfinies : [rapport financier 2024 de la Ville de Québec](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf) et [rapport 2024 MAMH organisme 23027](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf). Une URL est une référence de recherche, **pas une preuve d'identité de version**. Tout octet divergent conserve son SHA propre dans le reçu privé, mais **ne remplace jamais** la référence historique dans le code. Une concordance SHA-256 n'est pas une authentification de l'émetteur, de la signature ou du mandat d'audit.

## Opérations

1. Le responsable documentaire obtient légalement les deux PDF exacts et note **hors de ce logiciel**, sous contrôle humain, la provenance, la date d'accès, l'édition et les permissions.
2. Le script exige les deux copies **hors du dépôt**, avec droits `0600` et sans aucun lien symbolique. Une lecture de flux calcule taille et SHA-256, en vérifiant que les fichiers n'ont pas été remplacés pendant la lecture.
3. Si les deux versions correspondent aux valeurs historiques P54Q, la reproduction P55C/P54Q peut être exécutée en lecture seule. Une nouvelle lecture de contrôle après reproduction détecte un changement intervenu entre les deux opérations. Les cinq positions NFKC restent des positions **textuelles**, pas une confirmation visuelle.
4. Le reçu privé P55G contient la date UTC de **contrôle informatique** (pas de réception institutionnelle), le SHA-256 de chaque copie, leur taille, leur statut face à l'édition historique, et une empreinte globale des seules métadonnées. Il ne contient **ni nom, ni chemin de document, ni texte extrait, ni signature ni montant d'économie**. La présence d'une date et d'une empreinte globale **ne crée pas un témoignage signé ni une chaîne de conservation opposable à elle seule**.
5. La relecture du reçu privé contre les deux mêmes fichiers doit échouer si l'un est modifié, remplacé ou présenté dans un ordre trompeur. Le reçu n'est jamais mis à jour en place; une édition différente exige un **nouveau** reçu et un examen humain de la provenance.
6. Le bilan public donne seulement les nombres de copies non fournies, historiquement concordantes ou divergentes. Il ne divulgue **aucun chemin local, SHA, offset, nom, ni texte PDF**. Il conserve `NO_GO_AUTOMATIQUE`.

## Commandes locales

Sans source : créer un **bilan neutre** et un plan public d'acquisition :

```bash
python scripts/controler_integrite_pieces_nova_p55g.py \
  --bilan-public /hors_git/p55g_bilan_neutre.json \
  --plan-public /hors_git/p55g_plan_neutre.json
```

Après obtention réelle des deux PDF :

```bash
python scripts/controler_integrite_pieces_nova_p55g.py \
  --ville-pdf /hors_git/ville2024.pdf \
  --mamh-pdf /hors_git/mamh2024.pdf \
  --creer-recu-prive /hors_git/p55g_recu_original.json \
  --bilan-public /hors_git/p55g_bilan.json
```

Plus tard, comparer les **mêmes octets** au reçu initial, sans réécrire ce dernier :

```bash
python scripts/controler_integrite_pieces_nova_p55g.py \
  --ville-pdf /hors_git/ville2024.pdf \
  --mamh-pdf /hors_git/mamh2024.pdf \
  --verifier-recu-prive /hors_git/p55g_recu_original.json
```

Codes de sortie : **0** pour traitement neutre ou concordance technique **non certifiante**, **4** pour édition différente ou échec de reproduction, **2** pour erreur de chaîne, de permission, de schéma ou de fichier modifié, **3** pour le refus demandé par `--exiger-authenticite`. Un reçu peut être créé pour une édition divergente, classée comme telle, mais **ne la valide pas**.

## Conditions de recevabilité humaine

Le contrôle du hash n'est qu'une étape. Avant toute conclusion, un lecteur et un contre-lecteur examinent visuellement les cinq pages, leur colonne, unité et exercice. Le CPA indépendant vérifie les opérations réciproques Ville–RTC–SOMHAC, le périmètre de consolidation et les corrections comparatives, notamment les 1 825 176 $ imputés au comparatif antérieur (pas une économie 2024). Le juriste examine la portée du R.A.V.Q. 1435 et des avis. Ces mandats **ne sont pas signés**. Aucun contrôle logiciel ne peut les signer ou les authentifier.

Conserver les quatre dossiers P54E et l'année/date probable ouverts, 40 tâches P54N, dix blocages P54O, 96 P54B et huit P54C non attestés; ne réduire ni emplois, ni services ni pouvoir d'achat sur des gains non établis. Maintenir la distinction entre Québec dans le Canada et Québec souverain hypothétique.

**`NO_GO_AUTOMATIQUE` — pas de transmission ni dépense, aucune modification SINJIRA, aucune fusion `main`.**

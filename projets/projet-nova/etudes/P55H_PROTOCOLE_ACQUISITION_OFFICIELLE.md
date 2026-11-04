# P55H — Acquisition volontaire et contrôlée des deux publications financières de 2024

**Objet.** Lever matériellement le blocage documentaire relevé de P55B à P55G, sans attribuer au logiciel la capacité d'authentifier un organisme public, une signature ou un chiffre d'économie. Les deux rapports sont publics, mais leurs versions récentes et leurs octets **n'ont pas été vérifiés dans l'environnement de préparation**.

## Principe de sécurité

Le script P55H **ne fait aucun accès réseau par défaut**. Il ne peut télécharger qu'après activation explicite de `--autoriser-lecture-https-public` **et** désignation d'un nouveau répertoire privé `--destination-privee` hors du dépôt GitHub. Aucune URL personnalisée n'est acceptée, ni identifiant/mot de passe/cookie, ni redirection HTTP(S), ni passage par un proxy d'environnement. Les seules URL admissibles sont les deux références institutionnelles codées dans P54Q/P55B :

1. [Ville de Québec — rapport financier 2024](https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf) : référence historique de 8 984 919 octets, page PDF ciblée index zéro 102.
2. [MAMH — rapport financier 2024 et autres, organisme 23027](https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf) : référence historique de 10 818 312 octets, page PDF ciblée index zéro 162.

Les **empreintes SHA-256 historiques** restent dans P54Q et ne sont jamais écrasées par un téléchargement récent. Une édition différente peut être une retransmission légitime; c'est un **objet à instruire**, pas une anomalie automatiquement établie. Le fournisseur peut imposer une redirection : dans ce cas l'opération échoue par sécurité jusqu'à une décision humaine documentée. Aucune exception automatique n'est prévue.

## Déroulement reproductible

1. La personne responsable autorise la consultation HTTPS des deux **publications publiques**, sans contacter un agent, solliciter d'avis ni envoyer de documents.
2. Le logiciel crée un nouveau répertoire `0700` hors du dépôt (refus des liens symboliques). Il conserve uniquement les deux fichiers PDF sous des noms prévisibles et avec des permissions `0600`.
3. Chaque réponse doit être HTTP 200, provenir de l'URL exacte (sans redirection), être de type PDF ou binaire et commencer par `%PDF-`. La lecture s'effectue par blocs d'au plus 1 Mio, avec limite stricte de **20 millions d'octets par fichier**. Une réponse HTML ou un fichier incomplet invalide l'opération. En cas d'erreur réseau, de contrôle ou de taille, **le répertoire et les copies partielles créées par l'opération sont supprimés**.
4. La taille et le SHA-256 de chacun des fichiers sont comparés à leur version historique. Une seconde lecture par P55G, sur les fichiers locaux, confirme leur stabilité avant émission du reçu.
5. Le fichier privé `RECU_P55H.json` donne la date UTC du contrôle informatique, les **deux** tailles et empreintes réellement calculées, les statuts et l'empreinte des métadonnées. Il ne contient ni chemins, ni nom de personne, ni signature, ni textes extraits du PDF, ni données fiscales inventées. Le rapport public n'expose **aucune empreinte courante** : uniquement des compteurs.
6. Si une édition diffère, **les copies restent hors Git dans le répertoire privé et le programme retourne 4**. Un humain doit alors conserver les preuves de provenance et comparer les éditions; il est interdit de modifier P54Q pour faire disparaître cette divergence.

Un SHA-256 identique établit la **concordance des octets à une référence historique**, et non l'authenticité de l'auteur ou la qualification d'une ligne. Une date UTC enregistrée par le programme n'est pas un horodatage électronique certifié.

## Exécution

**Mode neutre, sans réseau (test et consultation de plan) :**

```bash
python scripts/acquerir_pdfs_publics_nova_p55h.py \
  --plan-public /hors_git/p55h_plan.json \
  --bilan-public /hors_git/p55h_bilan_neutre.json
```

**Mode volontaire, accès en lecture aux deux publications officielles, sans transfert des PDF sur GitHub :**

```bash
python scripts/acquerir_pdfs_publics_nova_p55h.py \
  --autoriser-lecture-https-public \
  --destination-privee /hors_git/nova_sources_2024_nouvelle_acquisition \
  --bilan-public /hors_git/p55h_bilan_reel.json
```

Le répertoire de destination doit **ne pas exister** au préalable; le programme le crée sans écraser d'ancienne acquisition. Un statut `CONCORDANCE_HISTORIQUE_NON_AUTHENTIFIANTE` signifie que les octets retrouvés sont identiques à ceux de P54Q, **pas** que la source a été authentifiée par l'émetteur.

**Étape suivante, uniquement sur la paire acquise avec concordance historique :**

```bash
python scripts/controler_integrite_pieces_nova_p55g.py \
  --ville-pdf /hors_git/nova_sources_2024_nouvelle_acquisition/VILLE_2024.pdf \
  --mamh-pdf /hors_git/nova_sources_2024_nouvelle_acquisition/MAMH_23027_2024.pdf \
  --creer-recu-prive /hors_git/p55g_recu_independant.json
```

P55G tente ensuite la reproduction des cinq positions P55C/P54Q; la revue **visuelle** et contradictoire reste à effectuer par des personnes compétentes. Les deux mandats comptable et juridique demeurent non transmis et non signés.

**Codes de sortie :** 0 = bilan neutre ou deux concordances techniques; 4 = une ou deux éditions différentes (copies conservées en réserve); 2 = erreur réseau, de chemin, de statut HTTP, de taille, de contenu ou d'intégrité, avec suppression des téléchargements partiels; 3 = refus délibéré de `--exiger-authenticite`.

## GitHub Actions et limites

La CI du jalon utilise **exclusivement des faux PDF et des réponses HTTPS simulées**; elle n'exécute **jamais** le drapeau `--autoriser-lecture-https-public` et n'archive aucun fichier PDF réel, aucune empreinte courante ou reçu privé. Les sources réelles doivent donc être récupérées, contrôlées et interprétées dans un environnement autorisé. Ne pas présenter des tests unitaires comme une acquisition réelle.

Les quatre dossiers P54E et la date/année probable restent ouverts; 40 tâches P54N, dix blocages P54O, 96 contrôles P54B et huit P54C non attestés. Le redressement comparatif 2023 de 1 825 176 $ n'est pas une économie 2024, et les éliminations Ville–RTC–SOMHAC ne sont pas de nouveaux gains. Respecter les emplois, la continuité des services, le pouvoir d'achat et la séparation des scénarios Québec au Canada et Québec souverain hypothétique.

**Décision : `NO_GO_AUTOMATIQUE`.** Pas de contact humain ni transmission, pas d'engagement financier, pas de changement SINJIRA, pas de fusion vers `main`.

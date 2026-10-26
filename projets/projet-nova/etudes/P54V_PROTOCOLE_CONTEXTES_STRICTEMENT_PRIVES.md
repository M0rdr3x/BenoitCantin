# P54V — Préparation privée des contextes NFKC pour examen humain

**Projet Nova — 24 octobre 2026.** Livrable d'appui concret à la localisation documentaire, **à utiliser uniquement par une personne habilitée en possession des deux PDF publics originaux**. P54V ne télécharge pas les PDF, ne contacte aucun tiers, ne les transmet pas et ne certifie pas leur contenu.

## Pourquoi ce jalon

Le workflow historique [P54P #40151185184](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40151185184) a haché deux copies exactes des rapports 2024 et reproduit cinq positions de caractères du texte extrait, normalisé Unicode NFKC. P54T a conservé les deux bilans publics en Git avec leurs SHA-256. P54U a produit cinq fiches de localisation (4 dossiers P54E indéterminés; 1 observation d'année/date probable non certifiée).

Les offsets ne désignent **pas** des coordonnées sur une page PDF. Un examinateur ne peut pas en déduire la nature d'une occurrence sans accéder aux vrais originaux et à un contexte lisible. P54V met ce contexte à disposition **seulement dans un fichier privé**, après une validation complète en lecture locale.

## Chaîne de preuve technique obligatoire

La commande de P54V :

1. Refuse l'absence d'un des deux PDF et refuse tout chemin dans le dépôt Git ou via un lien symbolique;
2. Vérifie sur chaque fichier local le format PDF, les tailles et empreintes SHA-256 historiques : Ville 8 984 919 octets, SHA-256 b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399, et MAMH 10 818 312 octets, SHA-256 4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00;
3. Revérifie sur leurs octets les deux bilans JSON P54T, mais **ne lit pas le ZIP historique**;
4. Extrait localement la page index zéro **102 pour la Ville** et **162 pour le MAMH**, avec pypdf 5.9.0, et contrôle leur portée commune d'audit;
5. Reproduit les cinq occurrences P54D/P54P par le parseur d'origine et exige strictement les offsets historiques **2359/2364, 18/2439, 2420/2439, 2430/2439 et 2436/2439**;
6. Produit un fichier privé contenant cinq références, les jetons et passages voisins pour contextualisation humaine, et **40 contrôles de revue non attestés** (5 observations × 8 rubriques).

Le passage voisin peut contenir des données personnelles ou autres informations sensibles : il est destiné à un opérateur autorisé et doit être géré conformément aux règles de confidentialité applicables. Il ne peut pas être placé dans un dépôt Git, un commentaire de PR, un artefact CI ou un message public.

Une égalité d'empreintes vérifie les octets de la copie, **pas** sa signature institutionnelle. Une correspondance d'offsets ne prouve pas une anomalie comptable. Les quatre dossiers P54E et la cinquième occurrence restent non qualifiés définitivement jusqu'à examen réel.

## Utilisation hors réseau, en local uniquement

Installer pypdf==5.9.0 puis disposer des deux rapports financiers publics originaux dans un espace extérieur au dépôt. Préparer un dossier privé à accès limité. Ne pas choisir une destination située dans le dépôt.

Production d'un bilan neutre sans PDF et sans aucune donnée brute :

    python scripts/preparer_contextes_prives_nova_p54v.py --bilan-public p54v_bilan_neutre.json

Production des **cinq fiches privées** à partir des deux copies exactes :

    python scripts/preparer_contextes_prives_nova_p54v.py --ville-pdf /espace_hors_git/ville_2024.pdf --mamh-pdf /espace_hors_git/mamh_2024.pdf --fiche-privee /espace_prive_hors_git/p54v_contextes_strictement_prives.json --bilan-public p54v_bilan_agrege.json

Le fichier privé est créé en mode 0600, sans écrasement de fichier existant, et les données brutes **ne sont jamais affichées sur stdout ou stderr**. Si l'une des preuves techniques échoue, aucune fiche n'est produite. Le bilan agrégé n'affiche que le nombre de copies/positions vérifiées, sans jetons, extraits ni chemins privés.

L'opérateur habilité doit ensuite inspecter les pages originales, comparer les passages, identifier dates, folios, références, identifiants ou valeurs, qualifier les cinq occurrences dans leur contexte et organiser une contre-revue distincte. **P54V ne saisit pas ni ne déclare ces conclusions**.

Vérifier que le programme ne peut pas émettre de certificat :

    python scripts/preparer_contextes_prives_nova_p54v.py --exiger-certification

Codes : 0 = génération technique sans authentification, 2 = sources/fichiers refusés, 3 = refus explicite de certification.

## Limites et protections permanentes

Le workflow GitHub P54V n'ouvre **aucun PDF authentique**, n'écrit aucune fiche contenant des jetons et ne téléverse qu'un bilan neutre. Les tests utilisent des fichiers et extraits fabriqués, non des rapports financiers véritables.

Les cinq observations ne correspondent à aucune économie prouvée; les 96 contrôles P54B, huit contrôles P54C, 40 tâches P54N et dix blocages P54O restent à instruire. L'interdiction de compter deux fois des écritures Ville–RTC–SOMHAC, le maintien des emplois et des services, et la séparation Québec au Canada / souveraineté hypothétique demeurent impératifs.

**NO_GO_AUTOMATIQUE** — Aucun avis professionnel authentifié, aucune conclusion budgétaire, aucun mandat ni décision institutionnelle généré, aucune fusion main et aucune opération SINJIRA.

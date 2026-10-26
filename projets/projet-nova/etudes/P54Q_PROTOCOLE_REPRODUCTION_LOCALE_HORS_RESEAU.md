# P54Q — Reproduction hors réseau des localisations PDF

**Projet Nova — 24 octobre 2026 — continuité technique de P54P.**

## Pourquoi ce jalon

Le workflow P54O #40150320973 a terminé ses **79 tests avec succès**. P54P introduit une tentative d'acquisition HTTPS des deux rapports financiers 2024 et une reproduction conditionnelle des cinq occurrences P54D, avec **70 tests de non-régression** au dernier commit. La réussite du workflow P54P, même confirmée, ne doit pas être confondue avec la réussite du téléchargement ou de la reproduction des offsets.

P54Q enlève une dépendance opérationnelle : si une personne habilitée possède déjà les **deux copies PDF publiques aux empreintes exactes**, elle peut reproduire les localisations sans requête réseau, sans soumettre ces copies à GitHub et sans leur donner une valeur de certification indépendante.

## Versions exactes indispensables

| Source | Page PDF (index de base zéro) | Taille exacte | SHA-256 P54D |
|---|---:|---:|---|
| Ville de Québec — rapport financier 2024 | 102 | 8 984 919 octets | b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399 |
| MAMH — rapport financier de l'organisme 23027, 2024 | 162 | 10 818 312 octets | 4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00 |

Ces empreintes proviennent des références P53Z/P54D. Elles permettent un contrôle d'intégrité contre les anciennes copies versionnées dans la chaîne, **pas une preuve autonome d'émission par les institutions**.

Le programme refuse les chemins de source sous le dépôt Git, les liens symboliques de fichier ou de répertoire, les alias pointant sur la même copie, les entrées non régulières et les fichiers inexistants. Avant extraction, la taille et le SHA-256 sont comparés aux références. Une édition différente conduit à un résultat NON_REPRODUIT; aucun offset partiel n'est produit. L'examen des textes et des observations est réutilisé depuis P54P.

## Exécution locale par une personne autorisée

Installer pypdf 5.9.0 dans un environnement approprié et invoquer depuis la racine du dépôt :

    python scripts/reproduire_pdf_locaux_nova_p54q.py --ville-pdf "/chemin/hors-git/ville_2024.pdf" --mamh-pdf "/chemin/hors-git/mamh_2024.pdf" --bilan "/chemin/hors-git/p54q_bilan.json"

**Ne pas fournir de documents personnels ou confidentiels** : P54Q est conçu uniquement pour les rapports publics de référence 2024. Les copies doivent se trouver hors de toute arborescence du dépôt et ne seront pas placées dans les artefacts Actions.

Il est possible de générer un résultat neutre sans source PDF :

    python scripts/reproduire_pdf_locaux_nova_p54q.py --bilan p54q_neutre.json

L'option de refus explicite est :

    python scripts/reproduire_pdf_locaux_nova_p54q.py --exiger-certification

Codes de sortie : **0** = résultat neutre sans tentative ou reproduction intégrale des cinq occurrences; **4** = deux copies fournies, mais comparaison ou localisation non réussie; **2** = fichier, chemin, configuration ou sortie invalides; **3** = impossibilité de délivrer une certification logicielle.

## Qu'est-ce qui pourrait réellement progresser ?

Si et seulement si les deux copies sont exactes, la reproduction P54P de l'audit spécialisé correspond et les cinq jetons non appariés se retrouvent dans l'ordre et les zones attendus, P54Q peut émettre **cinq offsets de caractères du texte pypdf normalisé Unicode NFKC**.

Cela facilite le repérage de quatre dossiers P54E indéterminés et d'une cinquième occurrence **ANNEE_DATE_PROBABLE** non close. Les offsets ne sont pas des coordonnées sur la page. Le système n'émet jamais les jetons, le contexte avoisinant, les fichiers PDF, les chemins privés ou le nom d'une personne.

L'intégrité des octets ne garantit pas le sens d'un jeton. Une extraction technique réussie n'est pas un avis professionnel, une validation d'unités comptables ni une preuve de différence monétaire.

## CI et preuve négative

Le workflow P54Q exécute **68 tests sur des PDF synthétiques** pour démontrer les contrôles de chemin, de taille, de SHA-256, de non-réutilisation, de non-fuite et de refus de faux succès. **Aucun PDF public réel n'est téléchargé ni fourni au runner P54Q.** Son artefact est exclusivement le bilan neutre NON_TENTE. L'authenticité et la reproduction réelle ne seront établies que par une exécution locale contrôlée sur les fichiers d'origine.

P54Q ne clôt ni les quatre dossiers P54E, ni les 96 contrôles P54B, ni les huit contrôles P54C. Il ne crée aucun mandat professionnel et ne transmet aucune preuve à un tiers. Les opérations Ville–RTC–SOMHAC déjà neutralisées en consolidation ne doivent pas être comptabilisées comme économies nouvelles. Maintenir emplois, services et séparation des scénarios Québec dans le Canada / souveraineté hypothétique.

**NO_GO_AUTOMATIQUE. Aucune fusion dans main; aucune opération SINJIRA.**

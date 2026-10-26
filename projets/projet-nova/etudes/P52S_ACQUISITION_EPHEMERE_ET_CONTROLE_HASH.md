# Projet Nova — P52S : acquisition éphémère de deux PDF budgétaires et preuve de transport

**20 octobre 2026 · Contrôle expérimental en lecture seule · NO_GO.**

## 1. Problème concret traité

P52J/P52R ont vérifié visuellement les tableaux budgétaires de mars 2026, mais les tentatives locales de téléchargement ont échoué à cause de l'accès réseau/DNS. P52K porte toujours une valeur `null` pour chaque empreinte PDF d'origine et la mention `NON_EFFECTUEE` pour l'acquisition. Il serait mensonger de transformer ces lacunes en « copies officiellement archivées ».

P52S introduit **une seconde voie de collecte**, exécutée en environnement éphémère GitHub Actions, en consultation HTTPS directe de deux URL officielles exactement autorisées. Les octets PDF **ne sont jamais déposés dans GitHub, conservés dans les artefacts, ni incorporés dans un nouveau commit par le robot**. Si le transfert réussit, un reçu technique enregistre la taille et l'empreinte SHA-256 des *octets effectivement reçus*. En cas de blocage TLS, HTTP, redirection, taille excessive ou contenu incompatible avec un en-tête de PDF, **aucune empreinte n'est inventée**.

**Attention aux niveaux de preuve :**
1. Une URL officielle consultable par navigateur n'est pas une copie originale enregistrée.
2. Une empreinte du flux reçu par HTTPS indique l'identité de ces octets **au moment de la tentative**, pas une signature vérifiée par le ministère.
3. Les contrôles `%PDF-` et `%%EOF` sont **superficiels** : ils ne prouvent pas que le PDF est bien formé, complet, signé ou identique à une édition antérieure.
4. Une réussite GitHub Actions signifie uniquement que les **tests techniques et les gardes NO_GO** ont fonctionné; la capture réseau peut échouer sans rendre la PR publiable.
5. Une archive autonome conforme, une vérification documentaire indépendante et l'avis d'un professionnel mandaté sont nécessaires avant de faire avancer F09.

## 2. Deux sources et juridictions

- `DISC2026_T3` — discours, tableau 3, page 27 (page PDF index 29), 34 pages signalées par le lecteur Web officiel.
- `PLAN2026_F2` — plan, tableau F.2, page F.9 (page PDF index 277), 426 pages signalées par le lecteur Web officiel.

Les tableaux contiennent des **prévisions** de revenus et de dépenses du Québec pour 2026-2027. Le service de la dette, la provision et les versements au Fonds des générations ne doivent pas être comptés deux fois; les transferts fédéraux ne sont pas des revenus fiscaux d'un Québec souverain.

## 3. Comment inspecter un résultat

```bash
# Sans aucune connexion externe, rapport toujours NO_GO:
python scripts/capturer_pdf_budget_nova_p52s.py --mode bilan --rapport /tmp/p52s_bilan.json

# Mode réseau (seulement si explicitement souhaité et autorisé en exploitation):
python scripts/capturer_pdf_budget_nova_p52s.py --mode sonde --rapport /tmp/p52s_reception.json

# Ne prétend pas que ces octets authentifient la source légale:
python scripts/capturer_pdf_budget_nova_p52s.py --mode sonde --exiger-expertise
```

Le mode réseau demande directement les deux PDF par HTTPS avec validation TLS standard, refuse les redirections, et limite la taille à 50 Mo pour chaque source. Le flux est lu par blocs et haché sans fichier permanent. Le rapport ne conserve ni pièces ni coordonnées d'experts. Une erreur est réduite à une catégorie technique plutôt qu'à une chaîne pouvant contenir des renseignements sensibles.

Codes : **0** = exécution technique normale même si des téléchargements ont été refusés, avec compteur explicite; **2** = registre invalide ou échec de production du rapport; **3** = mode strict `--exiger-originaux` non satisfait ou `--exiger-expertise` demandé sans attestation. Aucun mode n'autorise les taux, les recettes de la réforme, un contrat ou une fusion.

## 4. Contrôle CI et voie de réception sérieuse

Dans `.github/workflows/validate-nova-p52s.yml`, les tests adversariaux se déroulent d'abord **sans réseau** et sans écriture dans le dépôt. Une seconde étape tente la récupération du PDF depuis le runner GitHub; elle dépose uniquement un **reçu technique** et une synthèse des deux statuts. La réussite du job ne signifie pas que le réseau a fonctionné : la présence éventuelle de hash doit être regardée explicitement dans les résultats.

Pour passer à une authentification professionnelle, un responsable habilité devra comparer les empreintes du runner à une **copie originale acquise indépendamment**, archivée sous droits et datée, vérifier l'édition/PDF et ses tableaux, comparer toute mise à jour, obtenir l'avis d'un expert F09 mandaté et résoudre les réserves. P52K ne sera mis à jour vers « acquis » qu'après une réception réellement établie par ce responsable. **Aucune validation automatique de F09** et aucune altération de `main` ou de SINJIRA.

## 5. Prochain travail à valeur élevée

L'étape P52T pourra préparer la **réception croisée par deux opérateurs indépendants**, comparer les empreintes et consigner les différences entre éditions (avec preuve de la version, de la date et de la source), sous stricte séparation des pouvoirs. Cela ne remplace pas les véritables avis juridiques pour F01–F08 et F19–F20.

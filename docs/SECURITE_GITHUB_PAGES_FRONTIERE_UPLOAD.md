# Sécurité de la publication GitHub Pages — frontière `_site`

## Constat vérifié dans le dépôt

La publication manuelle `.github/workflows/deploy-github-pages-isolated.yml`
génère un site public réduit avec `scripts/build_netlify_public.py`, puis
téléverse **`path: _site`** via `actions/upload-pages-artifact`.

Le dépôt contient également des répertoires techniques tels que
`supabase/`, `scripts/`, `tests/`, `mobile-native/` et `docs/`.
Une future modification accidentelle du champ `path` vers `.`
pourrait introduire ces sources dans le contenu Pages publié.

## Protection ajoutée

Le validateur `scripts/validate_pages_artifact_boundary.py` parcourt les
fichiers `.github/workflows/*.yml` et `.yaml`, en lecture seule :

- un unique `actions/upload-pages-artifact` et un unique
  `actions/deploy-pages` sont permis, dans le seul workflow isolé;
- les deux actions doivent provenir des dépôts officiels et être
  épinglées aux SHA validés;
- l'upload doit spécifier exactement `path: _site`; les valeurs
  `.`, parent, absentes, multiples ou variables sont refusées;
- les verrous de déclenchement manuel, confirmation explicite,
  accusé des lacunes d'en-têtes, SHA de commit, `main` et génération
  via le builder isolé doivent être présents;
- un second workflow qui utiliserait les actions Pages est refusé;
- 13 tests de mutations négatives examinent les erreurs courantes, y compris un faux `path` inséré dans `env:` et un doublon de section `with:`.

Le workflow
`.github/workflows/github-pages-artifact-scope-security.yml`
lance ces contrôles sans secret, sans permission Pages write et sans
aucun déploiement.

## Frontières de garantie

**Une CI statique n'est pas une configuration d'hébergement.**
La protection s'applique aux workflows GitHub versionnés, mais elle
ne peut pas empêcher une publication déclenchée par le mécanisme
automatique GitHub Pages configuré sous *Settings > Pages* ou
par un administrateur qui change ce réglage.

Ce validateur n'analyse pas toutes les constructions YAML possibles
ni une commande shell arbitraire de publication. Il réduit le risque
d'un retour involontaire de `path: .` dans les workflows approuvés.

Pour considérer le risque #450 résolu, le propriétaire doit encore :

1. vérifier la source Pages effectivement active dans Settings;
2. exiger la publication depuis un artefact isolé, et non la racine;
3. contrôler l'URL live sur les chemins techniques et le SHA livré;
4. vérifier HSTS/CSP/no-store et redirections en production chez
   l'hébergeur cible, avec un plan de retour arrière;
5. activer des règles de branche qui imposent les validations (#135).

**Aucun réglage DNS, Pages, hébergement, branche `main` ni déploiement
de production n'est changé par ce correctif.**

# NOVA — Réception de la boussole sur le domaine public (8 novembre 2026)

**Objet :** vérifier deux critères de la boussole indépendamment de la réception du sondage : `COMPASS_DEPLOYMENT_RELEASE` et `COMPASS_PARTIAL_PROFILE_RELEASE`.

**Domaine testé :** https://www.benoitcantin.com/projets/projet-nova/boussole-electorale.html

## 1. Parité source / production en lecture seule

Récupération HTTP du contenu publié avec relecture fraîche (`maxAge: 0`), et comparaison **caractère par caractère** avec `main` sur GitHub. Les cinq comparaisons ont réussi, sans divergence :

| Fichier public | Taille des contenus source et public | Identique |
| --- | ---: | :---: |
| `assets/boussole-electorale.js` | 51 049 caractères | Oui |
| `assets/boussole-public-corpus.js` | 384 458 caractères | Oui |
| `assets/nova-civic-integrity.js` | 8 169 caractères | Oui |
| `assets/sondage-citoyen.js` | 18 057 caractères | Oui |
| `assets/sondage-public-corpus.js` | 2 086 caractères | Oui |

La page du domaine public sert bien `assets/boussole-electorale.js?v=3.4.26` et affichait la réception précédente `7/12 = 58,3 %` au moment du contrôle, conformément à `main` avant cette mise à jour. La page `sondages-a-valider.html` affichait elle aussi `58,3 %`.

Les contrôles GitHub Actions précédemment réussis incluent le scénario de 64 questions et les révisions de la boussole : [PR #881](https://github.com/M0rdr3x/BenoitCantin/pull/881), [PR #886](https://github.com/M0rdr3x/BenoitCantin/pull/886), [PR #889](https://github.com/M0rdr3x/BenoitCantin/pull/889) et [PR #900](https://github.com/M0rdr3x/BenoitCantin/pull/900), dont [le run navigateur multi-moteurs #42538803964](https://github.com/M0rdr3x/BenoitCantin/actions/runs/42538803964).

## 2. Parcours navigateur sur la version réellement publiée

Contrôle interactif d'un navigateur distant sur le domaine public, session de vérification `01a1bdaf-4388-7774-8e0d-faa8c7621a9f` (Firecrawl, session éphémère). Le test a utilisé des choix **synthétiques**, exclusivement locaux, sans formulaire de sondage ni partage externe.

| Vérification | Résultat observé |
| --- | --- |
| Recommencer puis démarrer à Q01 | Q01 affichée, aucune réponse présélectionnée |
| Q01 : accord fort, importance forte, consultation du profil partiel | 16 cartes; aucun score ou marqueur de position artificiel |
| Q02 : accord fort, importance faible, consultation du profil partiel | 1 dimension calculable, 15 non calculables, score `+50` |
| Changement d'importance de Q02 à forte | Score actualisé à `0` |
| Retour à Q01 puis « Sans opinion » | Score indisponible `—`, sans point de position fabriqué |
| 64 réponses « Sans opinion / passer » jusqu'à Q64 | 64 étapes parcourues, 16 cartes sans scores, aucun polygone trompeur |
| Remise à zéro | Formulaire initial rétabli; résultats masqués |
| Requêtes pendant la phase testée | 0 requête observée, 0 requête bloquée, 0 POST |

Le test enregistre et bloque toute requête autre que GET ou vers un autre domaine *à partir du démarrage des interactions de vérification*. Il ne remplace pas une analyse indépendante du réseau sur tous les appareils, ni une inspection des journaux techniques des hébergeurs.

La sortie structurée du test a indiqué `ok: true`, `errors: []`, `visited: 64`, `cardCount: 16` et le script `v=3.4.26`.

## 3. Décision de réception limitée

- **PASS** `COMPASS_PARTIAL_PROFILE_RELEASE` : bouton de profil partiel, absence de scores artificiels, pondération et remise à zéro confirmés sur la version publique.
- **PASS** `COMPASS_DEPLOYMENT_RELEASE` : scripts JS publics comparés intégralement au dépôt et suite CI pertinente réussie.
- **RESTENT PENDING** `COMPASS_CROSS_BROWSER` (appareils physiques, Safari/Firefox en production et cache), `COMPASS_ACCESSIBILITY` (audit WCAG manuel indépendant), `COMPASS_DOCUMENTARY_VALIDATION` (relecture de sources primaires et impartialité).
- Le **sondage demeure non homologué, non ouvert et inchangé** ; aucune opinion n'a été soumise à Supabase. L'homologation globale et l'autorisation d'ouverture ne découlent pas de ce contrôle.

**Pourcentage conditionnel après fusion et validation CI de cette preuve :** boussole `9/12 = 75,0 %`, sondage `6/11 = 54,5 %`, ensemble `15/23 = 65,2 %`. Le site public ne doit afficher ces taux qu'après synchronisation de son prochain déploiement ; toute divergence est signalée par `scripts/smoke_nova_live_public.py`.

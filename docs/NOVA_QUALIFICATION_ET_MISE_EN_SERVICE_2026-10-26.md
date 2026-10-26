# Projet Nova — preuve de qualification et conditions de mise en service

**État du 26 octobre 2026 (Québec).** Ce document est une attestation technique de l'aperçu, **pas** une approbation de mise en production ni de collecte d'opinions politiques.

## 1. Identité exacte du code qualifié

- Dépôt : `M0rdr3x/BenoitCantin`.
- PR d'intégration : [#639](https://github.com/M0rdr3x/BenoitCantin/pull/639), toujours DRAFT.
- Branche d'audit isolée : `audit/nova-40-64-boussole-2026-10-25`.
- SHA audité : `231322dbaa75e1b3b2ef2bb44d986b2e33b6ccaa`.
- SHA de PR contrôlé lors de cette attestation : `a7a097a70107d81f6345e22dcc3747eceb45f538`.
- [Exécution d'audit GitHub Actions #40165526096](https://github.com/M0rdr3x/BenoitCantin/actions/runs/40165526096) : **completed / success** sur le SHA audité ; les quatre jobs sont tous **success** :
  1. `Nova 40/64/Boussole — chromium`
  2. `Nova 40/64/Boussole — firefox`
  3. `Nova 40/64/Boussole — webkit`
  4. `Nova — contrats JS des trois parcours`

**Correspondance de contenu prouvée** : 19 fichiers sur 19 comparés entre les deux SHAs présentent exactement le même SHA de blob Git. L'identité du contenu, et non seulement celle de la branche, rattache les tests aux questionnaires candidats.

| Groupe | Fichiers à empreinte identique |
| --- | --- |
| Pages (4) | `projets/projet-nova/index.html`, `consultation-40.html`, `sondage.html`, `boussole-electorale.html` |
| Scripts (3) | `projets/projet-nova/assets/consultation-40.js`, `sondage.js`, `boussole-electorale.js` |
| Questions (3) | `projets/projet-nova/data/consultation-40-v1.json`, `sondage-questions-v1.json`, `boussole-electorale-v2.json` |
| Tests (5) | `tests/e2e/test_nova_consultation40_visual.py`, `test_nova_survey_visual.py`, `test_nova_compass_full_preview.py`, `tests/test_nova_compass_scores.cjs`, `tests/test_nova_survey_privacy.cjs` |
| Contrats source (4) | `scripts/validate_nova_consultation40.py`, `validate_nova_survey.py`, `validate_nova_public_access.py`, `validate_nova_public_results.py` |

**Différence prévue** : `.github/workflows/nova-civic-preview.yml` n'a pas le même blob : les déclencheurs sont adaptés à la branche d'audit. La réussite sur le SHA audité ne certifie pas tous les autres workflows de la PR ni ses 161 fichiers modifiés.

## 2. Périmètre réussi

- **Consultation civique 40** : 40 questions uniques, attestation 18+, accord explicite de démonstration, navigation, révision et suppression des choix; pas de soumission réelle.
- **Sondage citoyen 64** : 64 propositions, 16 dimensions à 4 questions, distinction entre réponses et « Sans opinion », révision, réinitialisation, collecte désactivée.
- **Boussole électorale 64** : 16 dimensions, calcul effectué localement, tests d'axes neutres et polarisés, seuils d'échantillonnage par axe, pondérations, absence de POST, effacement du profil.
- **Vie privée en mode démonstration** : les scripts effacent les réponses au retrait de l'accord/attestation, au redémarrage et à la navigation; tests de protection intégrés.
- Le corpus et les scripts qualifiés sont **identiques en octets** à ceux trouvés sur #639 au contrôle indiqué.

Ce PASS signifie **aperçu fonctionnel qualifié au SHA attesté**, pas « 100 % de conformité juridique », « publication terminée » ou « statistiques représentatives ».

## 3. Blocages de publication et de collecte

| Porte | État | Exigence de passage |
| --- | --- | --- |
| Publication publique de l'accueil et des sondages | **NO-GO** | Le domaine sert toujours l'ancien accueil ; les deux pages `/projets/projet-nova/consultation-40.html` et `/sondage.html` restent absentes. |
| Sécurité de l'hébergement — [#450](https://github.com/M0rdr3x/BenoitCantin/issues/450) | **NO-GO** | Ne plus publier les sources techniques du dépôt; valider l'artefact public isolé, la cible d'hébergement approuvée, les en-têtes et les chemins HTTP. |
| Candidat web-only — [#449](https://github.com/M0rdr3x/BenoitCantin/pull/449) | **NON APPROUVÉ** | PR brouillon, non fusionnable à la vérification du 26 octobre; aucun raccourci vers `main`. |
| Collecte d'opinions 40/64 — [#675](https://github.com/M0rdr3x/BenoitCantin/issues/675) | **NO-GO** | Revue EFVP/vie privée, consentement distinct, méthode, contrôle juridique, sécurité SQL/RLS/Edge Functions, anti-doublons, retrait/agrégation, décision humaine explicite. |
| Résultats publics | **FERMÉS** | N'ouvrir qu'après seuils de confidentialité, agrégation réellement vérifiée, revue documentaire et approbation distincte. |

Les deux clients conservent `COLLECTION_OPEN = false` et `LIVE_OPINION_CONSENT_GRANTED = false`. Ces verrous doivent rester inchangés jusqu'à approbation documentée. Ne pas appliquer les migrations candidates en production, activer les Edge Functions ou collecter un vote de démonstration.

## 4. Séquence de livraison vérifiable (aucune étape implicite)

1. Faire confirmer par l'administrateur le plan de bascule d'hébergement #450 et les droits nécessaires ; suivre `docs/PAGES_CONTROLLED_CUTOVER.md` ou le processus Netlify approuvé. **Ne pas déployer `publish = "."` depuis la racine du dépôt.**
2. Reconstruire un artefact public isolé depuis le **SHA final précis**, puis obtenir tous les PASS de sécurité (inventaire allowlisté, 0 chemin technique servi, en-têtes, HTTPS, origine canonique, empreintes des octets).
3. Vérifier les changements et les required checks de la PR web concernée; obtenir les approbations humaines de publication puis effectuer une publication contrôlée (pas une fusion automatique de #639).
4. Confirmer sur `www.benoitcantin.com` : l'accueil expose distinctement **les trois cartes**, les liens mènent à des pages HTTP 200 avec les bons fichiers CSS/JS/JSON, et les questionnaires se parcourent sans transmettre d'opinions.
5. Rejouer sur le **domaine public** les tests du parcours 40, du parcours 64 et du calcul de la Boussole; constater 0 URL technique servie et enregistrer le SHA effectivement publié.
6. Maintenir la collecte **fermée** même lorsque les démonstrations sont visibles. Toute collecte effective exige un second GO, lié exclusivement à #675 et aux versions de corpus approuvées.

## 5. Règle d'acceptation

**Aperçu des outils : PASS. Publication des outils : NO-GO. Collecte : NO-GO.**

Aucune réussite d'audit, aucun pourcentage et aucune capture d'écran ne valent autorisation de contourner #450, #675 ou de publier la racine technique. Cette attestation cesse d'être suffisante si le contenu des 19 fichiers change : dans ce cas, exiger une nouvelle preuve sur le SHA candidat.

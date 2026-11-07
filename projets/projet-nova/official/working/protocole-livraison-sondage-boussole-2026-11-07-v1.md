# Livraison contrôlée — Boussole électorale et sondage citoyen Nova

**Date :** 7 novembre 2026  
**Objet :** préparer une validation de staging et de production sans contourner la sécurité du projet.  
**Statut :** protocole de publication; **aucun déploiement ou lancement de vote n'est attesté**.

## 1. Code concerné

- `boussole-electorale.html` : bouton « Voir mon profil actuel (même incomplet) », résultat sans score lorsque la couverture est insuffisante, retour aux réponses, remise à zéro et partage facultatif.
- `assets/boussole-electorale.js` : validation du corpus et calcul délégué au moteur pur.
- `assets/nova-civic-integrity.js` : source canonique des huit formulations du sondage, validation des 64 propositions et `scoreCompass` déterministe.
- `sondage-citoyen.html` : consentement exprès aux fins d'agrégation, avertissements sur les résultats publics et l'absence de retrait individuel.
- `assets/sondage-citoyen.js` et CSS : formulaire accessible, condition d'âge, antirobot et progression, sans publication automatique.
- `tests/nova-civic-integrity.test.mjs` : 35 tests, `tests/nova-civic-scoring.test.mjs` : 25 tests, `tests/nova-civic-readiness.test.mjs` : 10 tests, soit **70 tests déclarés**.

## 2. Contrôles déjà effectués, sans extrapolation

- Les huit questions du sondage ont été comparées mot à mot aux huit lignes SQL Supabase.
- Les quatre corpus JavaScript publics de la boussole ont été comparés aux JSON GitHub.
- **260 profils de test** ont donné les mêmes sorties entre l'ancien calcul et le nouveau, et des contrôles supplémentaires ont vérifié les bornes, valeurs nulles et seuils de calcul.
- Les cinq tables SQL du sondage sont protégées par RLS et sans CRUD public; le RPC `nova_poll_submit` est réservé au rôle serveur.
- Une session navigateur a fait Q01–Q25 avec « Sans opinion », une autre Q01/Q02 puis `Recommencer`.
- Le bouton de profil partiel **n'était pas visible** sur le site public lors de la dernière vérification. Cela **empêche toute attestation de déploiement**.
- Les statuts de réussite de l'exécution complète GitHub Actions et l'approbation externe ne sont pas attestés.

## 3. Préproduction — étapes autorisées

1. Sur une branche `a1/web-release-*` issue d'un commit exact, exécuter la suite Node `node --test projets/projet-nova/tests/*.test.mjs`. Les échecs bloquent le passage.
2. Contrôler `python3 scripts/build_netlify_public.py --check` et valider la sortie `_site` : HTML, CSS, scripts versionnés, aucun export de votes, secrets, données privées ou document non autorisé.
3. Exécuter **manuellement**, à partir du seul ref de release, `.github/workflows/deploy-netlify-staging.yml`. Le workflow exige `expected_sha` (SHA exact du commit), `expected_site_name` (nom réel et connu du site Netlify), et `confirmation=STAGING_ONLY`. **Ne jamais deviner un site ou des identifiants, ni stocker les secrets dans Git.**
4. Le workflow construit deux déploiements non promus : **preview** et **production-candidate**; vérifier les permaliens immuables et les preuves `.well-known/release.json` ainsi que l'identité du site.
5. Exécuter sur le preview la boussole jusqu'à un résultat **partiel**, puis **complet 64/64**, en testant valeurs extrêmes, neutralité, « sans opinion », focus/clavier, mobile, navigation arrière, remise à zéro et partage sans envoi.
6. Faire auditer les traitements du sondage dans une **préproduction séparée et isolée**, avec Turnstile de test, anti-rejeu, concurrence, absence de réidentification par lots, conformité juridique et état `published:false` maintenu en production.
7. **Ne promouvoir en production** qu'après autorisations explicites, contrôles réussis, preuves de version SHA et confirmation du responsable du site.

## 4. Sortie de staging à conserver comme preuve

- SHA exact de la source testée et SHA du site publié.
- Résultats des suites de tests avec horodatage.
- URL du preview immuable, identité du site Netlify, résultat du test de build.
- Procès-verbal des vérifications de confidentialité, du fonctionnement navigateur et de la revue d'accessibilité.
- Décision d'approbation explicite pour l'ouverture du sondage et politique de conservation des données.

**La boussole peut être livrée séparément**, sans ouvrir le sondage. **La fonction Supabase active ne signifie pas que les votes sont ouverts** : l'activation est une décision réglementaire et opérationnelle distincte.

## 5. Limite du « 100 % »

Sans navigation et tests exhaustifs, revue de la légalité, vérification du deployment live et autorisation de vote, **on ne peut pas certifier 100 % des deux outils**. Le tableau de réception `data/validation-sondage-boussole-2026-11-07.json` reste la vérité de contrôle et non un argument marketing.

**Distinct :** le score de préparation du programme politique Nova est de **47/100** selon le dernier audit interne G0.12; il ne doit pas être augmenté par ces correctifs numériques.

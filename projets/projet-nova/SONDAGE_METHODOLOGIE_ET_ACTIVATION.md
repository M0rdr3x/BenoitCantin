# Projet Nova — Sondage 18+ : méthode, confidentialité et mise en service

## Statut réel (19 octobre 2026)

**Préparé dans la PR #639, non publié. COLLECTE DÉSACTIVÉE.** L'interface du questionnaire fonctionne en mode aperçu; le bouton de transmission est volontairement désactivé. Le site est encore bloqué par la publication GitHub Pages `legacy` (issue #450). Ne pas présenter ce projet comme un sondage publié ou comme des réponses déjà comptabilisées.

## Questions et population

- **64 propositions** : cliché immuable `data/sondage-questions-v1.json`, copié depuis `data/boussole-electorale-v2.json`, version source **2.2.0**. Les 16 thèmes existants sont conservés; toute nouvelle formulation requiert **une nouvelle version du sondage** et une nouvelle vague de collecte.
- Questionnaire **distinct** de la Boussole électorale : les résultats individuels de cette dernière sont calculés localement; ils ne sont pas automatiquement envoyés au sondage.
- Population admissible déclarée : **18 ans et plus**. L'attestation est une déclaration volontaire, **pas une preuve d'âge**. Aucune date de naissance ou pièce d'identité n'est recueillie. Une vérification d'âge indépendante exige une analyse distincte avant activation si nécessaire.
- Réponses : « Tout à fait en désaccord » (-3) à « Tout à fait d'accord » (+3), milieu « Ni d'accord ni en désaccord » (0), plus « Sans opinion / passer » (skip), sans l'assimiler à une position neutre.
- **64 réponses explicites** requises pour envoi, y compris les choix `skip`; progression réversible, une question par écran, consentement modifiable avant l'envoi.
- Pas de vote, d'adhésion, de contribution, de sollicitation électorale ni de recommandation de parti.

## Portée scientifique

Ce dispositif constitue une **consultation volontaire de personnes ayant accès au site et à un compte**, et **non** un échantillon probabiliste représentatif des adultes du Québec. Il n'autorise **aucune marge d'erreur probabiliste ni extrapolation de soutien électoral**. Si des résultats devaient être diffusés, toujours indiquer : dates de collecte, mode de recrutement, nombre de participants uniques, taux de réponses « Sans opinion », version et formulation des questions, exclusions, méthode de calcul, biais de sélection et limites. Pas de comparaisons de sous-groupes sensibles ni de cellules de faible effectif. Ne jamais inventer des résultats.

## Collecte minimale prévue

1. La personne s'authentifie avec son compte Supabase du portail. **Une soumission maximum par compte**, sans prétendre garantir une personne unique par compte.
2. Avant l'envoi, elle déclare avoir 18 ans ou plus et donne un consentement **exprès et séparé**, informé par une notice transparente.
3. L'Edge Function `nova-survey-submit` exige un jeton JWT, l'origine officielle, un corps JSON borné, la version exacte, l'attestation et le consentement. Le drapeau serveur `NOVA_SURVEY_COLLECTION_ENABLED` doit être exactement `true`.
4. Un secret serveur `NOVA_SURVEY_PEPPER` de longueur suffisante sert à dériver avec HMAC-SHA256 un jeton anti-doublon de l'UID. **Aucun UID, adresse courriel, date de naissance, adresse IP ou ensemble de réponses individuelles n'est écrit dans les tables du sondage.**
5. La fonction SQL `nova_survey_submit_v1` valide dans une transaction les 64 réponses, insère une trace pseudonyme de déduplication et incrémente uniquement les **comptages agrégés** par question/choix. Tables RLS sans politiques pour `anon`/`authenticated`; accès réservé à `service_role`. Aucune lecture publique des agrégats.
6. Un compte soumettant une deuxième fois reçoit `ALREADY_SUBMITTED` ; le compteur n'est pas augmenté. Les mauvaises requêtes, personnes non authentifiées et choix invalides sont refusés.

**Limite :** la pseudonymisation ne signifie pas l'anonymat complet. Le fournisseur d'authentification et d'hébergement peut produire des journaux techniques. Revue et documentation du risque, des contrats, de la localisation, de la durée de conservation et des droits d'accès **obligatoires avant ouverture**.

## Étapes obligatoires pour un lancement réel

- [ ] Vérifier avec la personne responsable de la confidentialité le fondement, la finalité, les champs sensibles et le consentement appropriés; mettre à jour la politique de confidentialité et les clauses fournisseur, prévoir retrait/suppression et durée de conservation.
- [ ] Définir le calendrier de la vague, sa population, la gestion des comptes et des doublons et une éventuelle méthode de vérification d'âge respectueuse de la vie privée.
- [ ] Approbation explicite de l'administrateur pour appliquer la migration et déployer l'Edge Function, dans l'environnement Supabase prévu; aucune donnée historique ni fichier privé ne doit changer.
- [ ] Provisionner `NOVA_SURVEY_PEPPER` **dans les secrets du serveur uniquement**, au moins 32 caractères aléatoires; laisser `NOVA_SURVEY_COLLECTION_ENABLED=false` jusqu'à la décision de lancement.
- [ ] Tester en environnement isolé : personne non authentifiée, moins de 18 ans déclaré, consentement absent, 63 réponses, valeur invalide, 64 réponses valides, doublon concurrent, secrets absents, RLS et absence de résultats publics, non-conservation des opinions individuelles.
- [ ] Résoudre l'incident GitHub Pages #450, imposer les required checks, approuver/fusionner selon la procédure contrôlée, effectuer DRY_RUN, PUBLISH et vérifications HTTP privées/publiques.
- [ ] Seulement après ces portes, basculer le drapeau serveur **et** `COLLECTION_OPEN` côté interface avec un commit revu. Publier la date d'ouverture. Tester réellement la confirmation `RECORDED`.
- [ ] Préparer une fermeture par drapeau et un processus de destruction/anonymisation de la table de déduplication. Contrôler la diffusion de toute statistique agrégée et le seuil minimal de confidentialité.

**Important :** aucun résultat ne doit être publié automatiquement pendant cette phase. Un sondage citoyen autoselectionné ne devient pas représentatif parce qu'il compte de nombreux répondants.

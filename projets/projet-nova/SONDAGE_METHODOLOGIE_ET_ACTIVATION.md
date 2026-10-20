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

**Important :** Aucun résultat n'est publié automatiquement pendant cette phase. Aucune donnée de participation, aucun comptage et aucune statistique Nova ne sont rendus publics avant une revue méthodologique, un contrôle des seuils de confidentialité et une approbation de publication distincte. Un sondage citoyen autoselectionné ne devient pas représentatif parce qu'il compte de nombreux répondants.

## Consultation séparée des 40 questions fondamentales

La banque fournie pour le Projet Nova a été conservée dans une
**consultation distincte** : `consultation-40.html`, le corpus immuable
`data/consultation-40-v1.json` et le client
`assets/consultation-40.js`. Il n'est **pas** substitué aux 64
questions de la Boussole ni au questionnaire exploratoire de 64
propositions. Ces 40 propositions couvrent explicitement
l'indépendance et le statut national, les institutions, la fiscalité,
la santé, l'éducation, les droits, l'énergie et l'environnement.
Certaines questions sont conditionnelles à une éventuelle
indépendance et n'engagent aucun gouvernement.

**Accès et parcours :** âge minimal autodéclaré de 18 ans et
consentement explicite séparé; une seule question visible à la fois,
boutons Précédent/Suivant, choix **Pour**, **Contre** ou **Sans
opinion**, récapitulatif, aucun stockage local des opinions,
aucun envoi tant que la collecte n'est pas autorisée. L'attestation
ne constitue pas une preuve vérifiée de l'âge.

**Préparation du serveur, non déployée :**
`supabase/candidate-migrations/20261019190000_nova_foundations_40_survey_v1.sql`
et `supabase/functions/nova-consultation40-submit/index.ts`.
Ces ressources ont leur propre identifiant de sondage
`nova-orientations-40-v1`, une clé pseudonyme HMAC de déduplication,
une insertion SQL atomique et des agrégats par réponse. La RLS des
deux tables interdit les lectures publiques et seules les opérations
`service_role` peuvent enregistrer les résultats. Le secret serveur
`NOVA40_SURVEY_PEPPER` doit être distinct, long et aléatoire; le
drapeau `NOVA40_COLLECTION_ENABLED` doit rester absent ou
différent de `true`.

**Avant toute collecte réelle :** validation juridique des 40
formulations, revue de confidentialité des opinions politiques,
base légale et conservation, processus d'effacement/retrait,
vérification d'âge adaptée, revue des risques de comptes multiples,
appels aux contributions non partisans, revue de sécurité et tests
SQL/Edge isolés. Il faut ensuite autoriser explicitement la
migration, le déploiement Edge et l'ouverture synchronisée du
drapeau serveur et du client. Ces étapes ne sont pas approuvées ici
et l'incident Pages #450 reste bloquant.

Une participation volontaire sur ce site **n'est pas un sondage
statistiquement représentatif** du Québec. Les résultats ne doivent
pas être présentés comme un référendum, une intention de vote
représentative ou une marge d'erreur scientifique.

Validation : `scripts/validate_nova_consultation40.py` et
`tests/e2e/test_nova_consultation40_visual.py`, lancés sur les PR
pour les trois moteurs navigateur et sans service externe.


## Parcours finalisé de la consultation référendaire — 19 octobre 2026

La consultation comporte **40 questions** dans l'ordre immuable approuvé. La question 1 concerne une éventuelle souveraineté du Québec; les 39 questions suivantes portent sur des orientations publiques. Un intitulé visible précise explicitement qu'il ne s'agit **pas d'un référendum officiel** ni d'une décision légalement contraignante. Les choix restent « Pour », « Contre » et « Sans opinion » (sans assimilation de « Sans opinion » à une abstention officielle ou à un vote valide). Aucune formulation du corpus source n'a été changée.

**Parcours de qualité sondage :** attestation volontaire 18+ et consentement séparé avant l'accès; chargement contrôlé des questions; un seul énoncé à la fois; sélection obligatoire d'un des trois choix pour avancer (y compris « Sans opinion »); retour possible; progression question courante et nombre de choix; récapitulatif des 40 réponses **personnelles et non publiques**, avec bouton « Modifier » pour chaque question; retour libre en relecture; commande explicite et confirmée « Effacer mes choix et recommencer » qui purge toutes les réponses en mémoire, décoche l'âge et le consentement et restaure les portes d'entrée. Aucun stockage local, aucun résultat simulé, aucun envoi en mode aperçu.

**Périmètre des résultats :** il s'agit d'un outil de consultation volontaire et non probabiliste. Aucune déduction de volonté populaire, aucune extrapolation référendaire, aucune marge d'erreur probabiliste ou statistique de soutien n'est autorisée sur la base de ce dispositif sans protocole méthodologique distinct. L'éventuelle collecte reste désactivée à la fois dans le client et par les drapeaux serveur tant que les obligations de confidentialité, le cadre juridique, le processus de collecte, la sécurisation Pages et la revue des migrations ne sont pas approuvés. Les tests navigateurs vérifient le parcours, la relecture, la purge et l'absence d'envoi.


## Vérification SQL isolée des 40 et 64 questions

La CI inclut maintenant un job PostgreSQL local jetable qui charge exclusivement les deux migrations candidates, sans accès à Supabase en production. Le test SQL contrôle les droits anon et authenticated, la RLS, le rôle service_role, les versions et réponses refusées, les doublons et les comptages agrégés. Identifiants et réponses : fictifs. Cette vérification technique ne remplace pas la revue juridique, méthodologique et de confidentialité, ni la revue du lot des migrations de production. Aucune migration n'est approuvée ou déployée automatiquement.


## Transparence des retraits et effacement local — 19 octobre 2026

Les deux pages 18+ informent désormais clairement que le modèle d’agrégation projeté ne permet pas de soustraire ultérieurement un bulletin individuel des totaux : l’effacement de la clé pseudonyme anti-doublon ne suffirait pas. La collecte reste fermée tant qu’une décision juridique, technique et méthodologique n’aura pas résolu cette limite dans l’issue #675. La politique de confidentialité expose distinctement le questionnaire 40 (référendaire consultatif non officiel), le sondage 64 et la Boussole. Le sondage 64 offre maintenant l’effacement confirmé **des seules données en mémoire** ainsi que de l’attestation 18+ et du consentement, aux étapes intermédiaires et finales, tout comme le parcours 40. Cette commande n’est pas un processus de retrait serveur après soumission.


## Migrations candidates strictement isolées

Les DDL des consultations Nova 40 et 64 sont stockés **sans modification** sous `supabase/candidate-migrations/` et non plus sous le répertoire normal `supabase/migrations/` utilisé pour les déploiements. Le builder production exclut expressément les fichiers candidats de son workspace. Leurs empreintes Git sont contrôlées par `scripts/validate_nova_candidate_migrations.py` (incluant le refus de leur inscription prématurée au lot de migrations production). Les tests SQL locaux appliquent les deux DDL dans une base PostgreSQL jetable ; le schéma de production reste vérifié séparément. Les questions, la collecte désactivée, les migrations historiques et le ledger ont été conservés. La promotion devra être approuvée explicitement après résolution des enjeux de confidentialité (#675) et de publication Pages (#450).


### Protection supplémentaire des Edge Functions candidates

Le workspace Supabase lié exclut maintenant les répertoires Edge `nova-survey-submit` et `nova-consultation40-submit` en plus des deux fichiers SQL candidats. Le validateur de plateforme `scripts/validate_supabase.py` accepte uniquement ces deux RPC *précisément identifiées* comme candidates si et seulement si leur DDL figé reste présent dans la zone isolée, si les appels proviennent exclusivement de leur Edge Function dédiée et si chaque fonction garde son drapeau serveur de collecte verrouillé. Toute RPC de production manquante ou tout appel supplémentaire continue de faire échouer la CI. Le déploiement des fonctions Nova nécessite encore une revue et une approbation distinctes; les validations locales ne l'autorisent pas.

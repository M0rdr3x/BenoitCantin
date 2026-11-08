# Projet NOVA — Mise en service contrôlée du sondage citoyen V1

**Statut : PRÉPARATION / PAS DE COLLECTE DE VOTES ACTIVE.**  
**Public :** personnes se déclarant âgées de 18 ans et plus.  
**Méthode :** consultation citoyenne ouverte, non probabiliste. Elle ne constitue ni une étude représentative de la population, ni une prédiction électorale.

## Révision documentaire des questionnaires complets 64/40

La PR candidate historique #639 contient deux questionnaires **non approuvés** : un sondage d'opinion de 64 questions (copie de la boussole v2.2.0, distinct de son calcul local) et une consultation consultative de 40 questions « Pour / Contre / Sans opinion », explicitement non officielle. Les deux sources exactes sont archivées dans `docs/nova-sondages/`, à partir du commit `5726b7262a89ddb42d210407c6d5473cc815feb0`, sans réponses de citoyens.

La page **`sondages-a-valider.html`** expose les 104 questions en lecture seule depuis la page d'accueil et le sondage de huit questions. Elle ne contient aucun formulaire ni script de collecte et reste `noindex`. Cette visibilité sert à examiner les formulations et le protocole; elle **n'autorise pas** à ouvrir les votes. Le test `scripts/test_nova_candidate_questionnaires.py` compare texte par texte, ordre et version, bloque toute divergence, et interdit les composants de saisie; les contrôles de publication Netlify/Jekyll et la surveillance du site réel exigent cette page.

Les huit questions de `sondage-citoyen.html` demeurent provisoires, fermées et distinctes du futur sondage d'opinion de 64 questions et de la consultation de 40 questions. Avant une collecte éventuelle, obtenir l'approbation documentaire et une analyse de confidentialité spécifique (voir issue #675), puis tester dans une base isolée. Aucun vote réel n'est créé par cette publication.

## Compatibilité du site public GitHub Pages/Jekyll

Le 3 novembre 2026, des contrôles HTTP ont établi que le mode d'hébergement Jekyll historique ne servait pas les fichiers `data/sondage-citoyen-v1.json`, `data/boussole-electorale-v2.json` et les références documentaires de la boussole (HTTP 404), bien qu'ils existent dans GitHub et dans le paquet public isolé Netlify. Le filtre Jekyll strict doit rester en place pour ne pas publier les autres fichiers de travail.

Les copies JavaScript **publiques** et versionnées `assets/sondage-public-corpus.js` et `assets/boussole-public-corpus.js` exposent uniquement les corpus déjà explicitement autorisés, sans bulletin individuel, et sont comparées intégralement aux sources JSON par `scripts/test_nova_public_bundles.py`. L'interface privilégie ces copies et conserve un repli sur les fichiers JSON pour les hébergements isolés. Le contrôle de confinement Jekyll exige désormais les deux bundles et les deux pages. Toute modification du corpus source nécessite de régénérer les bundles avec le même contenu et de réussir la CI avant déploiement. Le sondage **reste fermé** tant que l'approbation explicite de sa version n'est pas reçue.

## Vérification de cohérence des résultats avant exposition

La lecture des questions, des résultats par option et du total des bulletins publiés utilise plusieurs requêtes PostgREST. Même si l'écriture SQL des publications est atomique, un lecteur pourrait interroger des états antérieurs et postérieurs à la transaction, et voir des totaux temporairement incompatibles. La fonction Edge vérifie désormais que **chaque question totalise exactement le nombre de bulletins du dernier lot publié**, que les catégories et questions sont connues, qu'aucun couple catégorie/question ne se répète et que tous les nombres sont des entiers non négatifs sûrs. En cas de divergence, l'API répond **503** sans divulguer de répartition. Les tests Node simulent des transitions 0 → 10 → 20, les données invalides et des lectures concurrentes. Aucun vrai vote n'est créé.

Le contrôle HTTP de production signale aussi comme incident grave le cas où l'API renverrait `open=true` alors que le corpus public versionné affiche `published=false`.

## Surveillance de la publication réelle

Le workflow GitHub `.github/workflows/nova-public-readonly-smoke.yml` effectue un **contrôle HTTP quotidien en lecture seule**. Il vérifie le domaine officiel, les liens du sondage et de la boussole, l'ordre des scripts, les deux corpus publics JS comparés aux sources, la disponibilité de la fonction Supabase, la concordance des huit questions et le refus de servir certains fichiers techniques. Aucun secret n'est utilisé; **aucun bulletin de vote n'est envoyé**.

Les échecs doivent déclencher une revue de la publication du domaine et du fournisseur d'hébergement. Le workflow n'active jamais la collecte et n'assure pas l'unicité des participants.

## Contenu de cette livraison

- `projets/projet-nova/sondage-citoyen.html` : page publique, questionnaire, résultats agrégés publiés par lots et méthode.
- `projets/projet-nova/data/sondage-citoyen-v1.json` : huit formulations **provisoires** extraites *sans modification* de la Boussole Nova. Ne pas présumer qu'il s'agit du questionnaire historiquement approuvé sans comparaison avec les questions soumises antérieurement.
- `projets/projet-nova/assets/sondage-citoyen.{js,css}` : parcours anonyme et visualisation accessible.
- `supabase/functions/nova-civic-poll/index.ts` : API autonome avec limites de taille, validation d'origine, Turnstile, HMAC serveur, dépouillement atomique, seuil de publication et publication par lots espacés.
- `supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql` : script de schéma déployé sur Supabase en mode préouverture le 3 novembre 2026; ce fichier reste la référence de vérification.
- `projets/projet-nova/assets/boussole-electorale.js` : radar : les 16 axes conservent leurs positions même si des questions sont passées.
- `scripts/test_nova_civic_poll.py` : contrôles statiques en CI.

## État technique contrôlé le 3 novembre 2026

- Supabase projet `gpvivleexywljowcqkru` : cinq tables `nova_poll_*` créées et RLS activée, droits publics de lecture/écriture refusés.
- Base : huit questions préparatoires, **zéro bulletin**, zéro choix comptabilisé et zéro instantané public.
- Fonction serveur `nova-civic-poll` version 1 : déployée, sans authentification JWT générique mais avec accès public en lecture protégé par origine et écriture fermée sans variables d'activation et Turnstile.
- La fonction ne doit **pas** être déclarée prête à recueillir des avis politiques tant que l'environnement, les secrets, la vérification Cloudflare, les tests de charge/anti-abus et la conformité n'ont pas été passés.
- Le questionnaire V1 contient huit questions sélectionnées dans la boussole, **qui ne peuvent pas être présumées identiques aux questions fournies auparavant sans vérification du document d'origine**.
- Une fois le scrutin ouvert et des bulletins reçus, traiter les changements de questions comme une nouvelle version : ne pas réécrire rétroactivement les compteurs.

## Clarification indispensable sur les versions du questionnaire

Un inventaire historique de GitHub confirme l'existence de **trois périmètres différents** qui ne doivent pas être amalgamés :

- **Boussole électorale : 64 questions / 16 dimensions**, instrument de profil individuel **sans envoi de réponses**.
- **Sondage d'opinion historique : 64 questions**, distinct de la boussole, préparé sur une PR brouillon (issue [#674](https://github.com/M0rdr3x/BenoitCantin/issues/674)).
- **Consultation référendaire historique : 40 questions**, projet distinct également documenté dans l'issue [#675](https://github.com/M0rdr3x/BenoitCantin/issues/675).
- **Consultation actuellement codée : 8 questions** reprises de la boussole, version `nova-consultation-v1`, **provisoire et fermée**.

Les huit questions ne doivent pas être considérées automatiquement comme le questionnaire original fourni par le propriétaire : le fichier source mentionné historiquement dans les échanges n'est pas rattaché de manière vérifiable à ce corpus. **Décision humaine requise** : identifier quel questionnaire doit être publié (8, 40, 64 ou le texte original), contrôler sa rédaction, figer la version et respecter la revue confidentialité. Toute nouvelle version modifie les clefs de la collecte, la documentation et les tests; les choix déjà agrégés ne sont jamais réinterprétés sous un nouveau libellé.

Le schéma Supabase V1 contient huit questions et **ne convient pas** à une consultation de 40 ou 64 questions sans nouvelle migration évaluée et nouvelle fonction Edge. Conserver le vote désactivé en attendant le choix officiel. Les obstacles légaux et de responsabilité sont suivis dans l'issue [#675](https://github.com/M0rdr3x/BenoitCantin/issues/675), qui bloque l'ouverture.

## Prérequis avant ouverture effective du vote

1. **Valider la formulation des huit questions** avec le texte approuvé et faire une révision de neutralité, accessibilité, clarté, bilinguisme si requis et conformité. Conserver le corpus source et la version de publication sans réécrire les questions après le premier bulletin.
2. **Revue sécurité et confidentialité avant collecte**, y compris l'évaluation du service Cloudflare Turnstile, de Supabase, de leur traitement de données techniques, des durées de conservation, de la Loi 25 et des obligations légales applicables. Prévoir contact, registre d'incidents et responsabilités.
3. **Infrastructure installée le 3 novembre 2026** : migration `nova_poll_private_aggregates_prelaunch_20261103` appliquée au projet Supabase `gpvivleexywljowcqkru`. Les cinq tables ont **RLS activée** ; vérification SQL : rôles `anon` et `authenticated` sans lecture, écriture ni exécution de `nova_poll_submit`; rôle `service_role` réservé au serveur. Contrôler à nouveau après toute évolution de schéma.
4. Configurer Cloudflare Turnstile pour les domaines `www.benoitcantin.com` et `benoitcantin.com`. Créer un secret HMAC long, aléatoire, dédié, non partagé et **non publié dans Git**. Configurer les variables privées dans Supabase : `NOVA_POLL_TURNSTILE_SECRET`, `NOVA_POLL_TURNSTILE_SITE_KEY`, `NOVA_POLL_HMAC_KEY`, `NOVA_POLL_ENABLED=false` par défaut, et `NOVA_POLL_APPROVED_VERSION` absent jusqu'à l’approbation formelle du corpus. Pour ouvrir, cette dernière variable doit être exactement `nova-consultation-v1`. La variable d'approbation n'est pas un secret mais doit être gérée côté serveur. Supabase fournit `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` côté fonction ; jamais les afficher au navigateur.
5. **Fonction Edge installée le 3 novembre 2026**, version 1, `verify_jwt=false`, en mode fermeture de vote par défaut (`NOVA_POLL_ENABLED` absent ou différent de `true`, ou `NOVA_POLL_APPROVED_VERSION` absent ou différent du corpus). Avant activation, contrôler les appels navigateur et les tests d'origin. Attention : la validation du seul header Origin n'est pas une authentification ; la protection serveur repose également sur Turnstile, la validation stricte et le refus des privilèges directs aux clients.
6. **Reste à faire avant activation :** exécuter les tests négatifs et positifs en environnement de préproduction : hors origine, préflight, appel sans CAPTCHA, CAPTCHA invalide, âge non confirmé, questionnaire incomplet, doublon, replay, réponses hors plage, corps volumineux, erreurs réseau, refus de publication avant 10 bulletins, publication par lots d'au moins 10 nouveaux votes, délai minimal de 6 heures, interdiction d'accéder aux compteurs bruts et accès public uniquement aux instantanés agrégés.
7. Appliquer des mécanismes **complémentaires anti-abus** (contrôle de débit au niveau de la passerelle/WAF et surveillance anonymisée) sans stocker d'opinions politiques reliées à l'IP. **Ni CAPTCHA ni identifiant local ne garantissent l'unicité d'une personne** ; annoncer explicitement cette limite.
8. Tester mobile, clavier, lecteur d'écran, focus, erreurs, qualité des données, sauvegardes, reprise et compatibilité navigateur.
9. Après approbation du questionnaire définitif et validation de sécurité, fixer `published:true` dans `data/sondage-citoyen-v1.json`, puis fixer `NOVA_POLL_APPROVED_VERSION=nova-consultation-v1` et activer `NOVA_POLL_ENABLED=true` dans les variables serveur, sans oublier les secrets CAPTCHA/HMAC. Vérifier sur le **domaine public** le déroulement intégral puis observer les métriques techniques sans enregistrer de réponses individuelles.
10. Conserver un protocole de clôture, de suppression des empreintes de jeton et de conservation des seuls compteurs agrégés. Le vote ne peut pas être supprimé individuellement après agrégation, puisqu'aucune association identité-réponse n'est conservée.

## Données, transparence, limitations

Le modèle de dépouillement ne stocke **pas de bulletin individuel** : seuls les compteurs par question et option sont persistés. Un HMAC de jeton aléatoire de navigateur est enregistré *séparément* pour détecter le rejeu du même jeton. Ce dispositif ne vérifie ni l'identité ni la citoyenneté et permet un nouveau vote si quelqu'un change d'appareil ou supprime les données du navigateur. L'âge 18+ est autodéclaré et non vérifié par une pièce d'identité.

Les résultats par option sont masqués tant que le sondage n'a pas atteint **10 bulletins**. Les résultats sont ensuite publiés seulement quand **au moins 10 nouvelles participations** ont été reçues depuis l'instantané précédent et **au moins 6 heures** se sont écoulées depuis la dernière publication. Cela réduit le risque de dévoiler un bulletin en comparant deux lectures successives. Les pourcentages portent sur les réponses reçues, incluant la catégorie « Sans opinion ». Ils ne décrivent pas l'opinion des Québécois et ne devraient pas être présentés comme tels.

La Boussole électorale, en revanche, est **distincte du sondage** : ses 64 réponses et son profil à 16 dimensions restent en mémoire locale et ne sont pas transmis au serveur par ce module. Les comparaisons de positions des partis demeurent soumises aux preuves documentaires et ne donnent aucune recommandation de vote.

## Publication et retour arrière

- Le socle front-end a été fusionné sur `main` le 3 novembre 2026 (PR nº 733). La publication visible sur le domaine peut dépendre du pipeline d'hébergement. Ne jamais déduire sa présence de la fusion seule.
- Un déploiement de la page statique avant la mise en service backend est sûr : formulaire visible, envoi **désactivé**.
- Pour arrêter immédiatement la collecte : `NOVA_POLL_ENABLED=false` côté Supabase. Les résultats agrégés peuvent rester visibles si la base et l'API sont disponibles.
- Conserver les journaux techniques de validation sans données sensibles et les résultats de vérification pour audit.

**Ne jamais annoncer « 100 % opérationnel » avant réussite des tests réels, examen des exigences applicables et validation de publication sur le domaine.**

## Confidentialité : catégories de très faible effectif

Le seuil d'au moins dix bulletins **ne suffit pas** à protéger une catégorie comptant un à quatre avis (par exemple neuf réponses pour une option et une pour une autre). Le serveur NOVA refuse désormais **toute la répartition, le total et la date de publication** lorsqu'une seule des six catégories d'une des huit questions contient entre un et quatre avis. Les catégories à zéro et à cinq ou davantage restent permises, sous le seuil général de dix participations. Le navigateur vérifie indépendamment ce même invariant. Aucun arrondi ni valeur inventée ne remplace un petit effectif. Tests sans réseau : répartitions fictives 9/1, 6/4 et 5/5, incluant un unique item sensible.

**Limitation restante et bloquante avant ouverture :** la comparaison de deux lots publiés peut permettre de déduire une variation individuelle, même si chaque instantané satisfait le seuil de cinq par catégorie. Une analyse de divulgation temporelle et des mesures supplémentaires (report, regroupement ou politique de publication appropriée) restent indispensables. Ni l'absence de noms en base ni cette barrière ne justifient la promesse d'anonymat absolu. Ne pas activer `NOVA_POLL_ENABLED` avant revue du questionnaire, confidentialité et recette isolée.

## Vérification défensive des résultats publics côté navigateur

Le navigateur contrôle également chaque lecture de l'API — y compris le bouton « Actualiser les résultats » — avant d'afficher une répartition. Les huit formulations et leur ordre doivent correspondre à la version locale, les résultats non publiés ne doivent contenir aucun petit effectif, et pour chaque lot public les six catégories de réponse doivent totaliser **exactement** le nombre de bulletins publiés, sous forme d'entiers sûrs et non négatifs. Toute donnée défectueuse ou incohérente est masquée plutôt que transformée en pourcentage. Si l'API annonce la fermeture pendant une session ouverte, le bouton d'envoi est désactivé immédiatement. Des tests Node sur le véritable code navigateur vérifient le contrat et les cas négatifs, sans vote ni réseau.

### Résilience bornée du contrôle réseau

Les contrôles de disponibilité HTTP effectuent jusqu'à **trois lectures GET** en cas de HTTP 503 temporaire, séparées par des délais de 0,3 s et 0,6 s. Ils ne réessaient **jamais** l'envoi POST, ne masquent pas une panne persistante et vérifient les protections CORS et le refus des votes même lorsque la première lecture a dû être répétée. Des tests hors réseau simulent les échecs ponctuels et permanents. Les résultats restent invisibles si le service ne fournit pas de réponse cohérente.

## Reprise d’une erreur de lecture transitoire sans ouvrir le vote

Le service public Supabase peut répondre temporairement 503 à la première consultation. Au chargement, le navigateur effectue déjà une seconde lecture des résultats; désormais, si cette relecture est conforme, l’interface remet son statut exact (« consultation en préparation » ou « ouverte » uniquement avec toutes les conditions vérifiées), au lieu de laisser une alerte d’indisponibilité périmée. Si la relecture échoue, elle garde l’envoi désactivé et affiche l’indisponibilité. Ce changement concerne **uniquement la lecture GET**; aucun envoi POST n'est répété et les exigences d'âge, d'approbation de version et de CAPTCHA ne sont pas assouplies. Un test Node du gestionnaire réel simule l'incident et vérifie l'absence d'ouverture d'un corpus provisoire.

## Confidentialité des publications successives — sécurité en base

La comparaison de deux totaux publics permettrait autrement de révéler une variation de seulement 1 à 4 réponses dans une catégorie même si chaque total cumulé dépasse cinq. La fonction PostgreSQL `nova_poll_submit` applique désormais un garde **dans la transaction de publication** : elle compare les nouveaux compteurs agrégés aux compteurs du dernier lot publié et **ne publie aucun nouveau lot** si une catégorie quelconque a augmenté de 1 à 4, ou si un compteur a diminué. Un premier lot est soumis à la même règle (comptage depuis zéro). Cette décision porte sur toutes les questions et options : la publication reste entièrement différée jusqu'à ce que tous les écarts positifs soient au moins cinq, ou nuls. Le seuil de dix participations et le délai de six heures continuent de s'appliquer. Les réponses restent comptabilisées en interne et ne sont pas perdues lorsque la publication est reportée.

Le test `scripts/test_nova_poll_delta_privacy.py` vérifie la présence des conditions dans le SQL versionné et simule les deltas 9/1, 6/4, 5/5, 1/9, 0/10, ainsi que les compteurs décroissants, sans modifier la production. Cette défense protège **les écarts par option** mais ne prouve pas l'anonymat absolu face à toutes les corrélations entre questions, aux informations externes ou à des groupes connus. Une EFVP et une approbation documentaire sont toujours requises avant toute collecte.


## Limite complète du temps de réponse HTTP du sondage

Les requêtes GET des résultats et POST de soumission disposent d'une limite de **10 secondes englobant la réception des en-têtes et la lecture/décodage du corps JSON**. L'ancien contrôle levait sa limite à la réception des seuls en-têtes : un serveur transmettant HTTP 200 puis bloquant le corps pouvait immobiliser l'interface. Le contrôleur d'annulation reste actif jusqu'à la fin du décodage et le délai est nettoyé en cas de succès, d'erreur HTTP ou de JSON invalide. Le test Node `scripts/test_nova_poll_network.cjs` simule séparément le blocage des en-têtes et celui du corps pour GET et POST, sans requête réelle.

**Cas particulier du POST :** une expiration du délai ne prouve pas que le serveur a refusé le bulletin. L'interface annonce donc seulement que l'envoi n'a **pas été confirmé** et réutilise le même jeton de participation lors d'une tentative ultérieure; le garde serveur d'anti-rejeu reste l'autorité. Aucune relance automatique du POST, aucune collecte supplémentaire et aucune modification des seuils de confidentialité.


## Échec sécurisé sur corpus de sondage incomplet

Le navigateur valide le corpus public **avant tout appel réseau au service de vote** : version et état de publication explicites, consultation ouverte non probabiliste réservée aux 18 ans et plus, huit questions distinctes avec ordre 1–8 et texte non vide, six choix avec valeurs et libellés identiques au questionnaire canonique. Une copie tronquée, dupliquée ou modifiée n'est jamais filtrée silencieusement pour former un questionnaire partiel. Dans ce cas, le navigateur affiche un message d'indisponibilité, masque les répartitions, verrouille l'envoi et ne contacte pas l'API de vote.

Le test d'intégration `scripts/test_nova_poll_runtime.cjs` vérifie les cas négatifs et le comportement réel du chargement avec un corpus corrompu, sans réseau. Cette vérification n'autorise pas l'activation d'un corpus provisoire et ne remplace pas la revue de confidentialité ni l'approbation du questionnaire définitif.

## Sécurisation de la lecture des corps POST (sans vote réel)

La fonction Edge `nova-civic-poll` limite déjà le bulletin JSON à **8 Kio**. Son lecteur de flux dispose maintenant aussi d'une échéance totale de **8 secondes**, indépendante du nombre de morceaux reçus. Une déconnexion du client annule la lecture et un dépassement ne doit jamais attendre indéfiniment le nettoyage d'un flux hostile. Les corps annoncés trop grands sont refusés avant lecture; les octets réellement reçus restent limités. La validation JSON/UTF-8 est conservée.

Le test Node `scripts/test_nova_poll_body_read.cjs` exécute le véritable parseur de la source Edge avec des flux de test : corps valide, type/longueur incorrects, JSON/UTF-8 invalides, corps dépassant 8 Kio, connexion suspendue et abandon du client. Tous les délais sont nettoyés et **aucun bulletin ni appel réseau n'est effectué**. Les limites de plateforme ne dispensent pas d'une protection applicative; les tests d'intégration Supabase restent nécessaires avant une autorisation de collecte.

## Contrôle de l'identité du questionnaire côté fonction Edge

En complément du verrou client, la fonction `nova-civic-poll` contient une liste **canonique et immuable** des huit identifiants, rangs et textes du sondage. Le point de lecture `GET` refuse de produire un état public en cas de dérive, et le point `POST` retourne un état d'indisponibilité **avant toute écriture RPC** si l'une des huit questions stockées dans Supabase ne correspond plus strictement au questionnaire approuvé. Le contrôle ne se contente plus de vérifier le nombre de questions.

Le test hors réseau `scripts/test_nova_edge_canonical_questions.cjs` compare le contrat serveur au JSON officiel et simule les permutations, doublons, suppressions, formulations modifiées et ordinaux invalides. Il vérifie la présence de ce contrôle dans les deux flux de l'API. Toute modification éditoriale devra rester une modification de version documentée et approuvée, et non une simple mise à jour silencieuse des textes de la base.

Cette protection est fusionnable et testable **sans mise en service de collecte**. Elle n'autorise ni déploiement de la fonction Edge sans revue, ni activation de `NOVA_POLL_ENABLED` ou `NOVA_POLL_APPROVED_VERSION`. La politique d'avis politiques sensibles et les décisions de gouvernance restent à faire valider par les personnes compétentes.

## Verrou d'âge et de consentement côté API

Le sondage public comporte **deux cases distinctes** et obligatoires : déclaration personnelle d'avoir au moins 18 ans, puis consentement exprès à la transmission d'opinions politiques et à leur comptabilisation sous forme agrégée. Le client ne transmet un bulletin que lorsque les deux cases sont cochées; l'enveloppe JSON contient maintenant deux booléens indépendants : `ageConfirmed:true` et `consentConfirmed:true`.

La fonction Edge refuse toute enveloppe avec consentement absent, faux ou non booléen **avant** CAPTCHA, HMAC ou accès à la base. La validation des huit choix, des jetons et des versions reste obligatoire. Le test `scripts/test_nova_edge_explicit_consent.cjs` exécute le vrai validateur d'enveloppe avec des cas valides et altérés, sans envoyer de bulletin ni accéder au réseau. Le script HTML du sondage change de version de cache pour diffuser le nouveau champ.

**Limite importante :** ces deux valeurs sont des **déclarations effectuées par le client**, pas une vérification indépendante de l'âge ou du consentement effectif. Le système n'enregistre pas de preuve nominative et ne doit pas prétendre le faire. La revue humaine sur l'information à fournir, le fondement juridique, la conservation, les possibilités de retrait et la conformité applicable au Québec reste une condition bloquante de l'ouverture.

Ce contrôle est préparatoire : les flags d'ouverture de la fonction Supabase et `published:false` restent inchangés. Aucun déploiement de la fonction Edge n'est autorisé par cette modification seule.

## Verrou de participation en l'absence de stockage local

Après une réponse **HTTP 201 acceptée** ou **HTTP 409 déjà enregistrée**, le navigateur verrouille immédiatement toute nouvelle participation **en mémoire pour la session courante**, puis tente de conserver ce statut dans `localStorage`. Si le stockage est refusé (navigation privée, paramètres restrictifs, quota), l'écriture peut échouer mais **les choix et le bouton d'envoi restent désactivés** jusqu'au rechargement de la page. Un échec réseau non confirmé n'active pas ce verrou : l'utilisateur peut réessayer avec le **même jeton aléatoire**, conservé en mémoire durant la session.

La limitation reste explicitement documentée : sans stockage persistant, le blocage du navigateur disparaît au rechargement, et l'outil ne prétend pas vérifier l'unicité d'une personne. Le mécanisme serveur d'anti-rejeu repose sur l'empreinte HMAC du jeton; ni le jeton ni l'état de confirmation ne doivent contenir les choix politiques. Aucun identifiant de personne n'est créé par ce correctif.

Le test `scripts/test_nova_poll_runtime.cjs` simule une erreur d'écriture dans `localStorage` et vérifie que l'état de participation confirmée verrouille le bouton et les réponses. Il vérifie également le branchement du verrou aux réponses 201 et 409. Le client est versionné `sondage-citoyen.js?v=14` pour éviter une mise en cache périmée. Les approbations humaines de confidentialité restent obligatoires avant toute ouverture.

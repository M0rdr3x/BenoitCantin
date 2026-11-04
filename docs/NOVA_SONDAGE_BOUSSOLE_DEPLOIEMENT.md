# Projet NOVA — Mise en service contrôlée du sondage citoyen V1

**Statut : PRÉPARATION / PAS DE COLLECTE DE VOTES ACTIVE.**  
**Public :** personnes se déclarant âgées de 18 ans et plus.  
**Méthode :** consultation citoyenne ouverte, non probabiliste. Elle ne constitue ni une étude représentative de la population, ni une prédiction électorale.

## Compatibilité du site public GitHub Pages/Jekyll

Le 3 novembre 2026, des contrôles HTTP ont établi que le mode d'hébergement Jekyll historique ne servait pas les fichiers `data/sondage-citoyen-v1.json`, `data/boussole-electorale-v2.json` et les références documentaires de la boussole (HTTP 404), bien qu'ils existent dans GitHub et dans le paquet public isolé Netlify. Le filtre Jekyll strict doit rester en place pour ne pas publier les autres fichiers de travail.

Les copies JavaScript **publiques** et versionnées `assets/sondage-public-corpus.js` et `assets/boussole-public-corpus.js` exposent uniquement les corpus déjà explicitement autorisés, sans bulletin individuel, et sont comparées intégralement aux sources JSON par `scripts/test_nova_public_bundles.py`. L'interface privilégie ces copies et conserve un repli sur les fichiers JSON pour les hébergements isolés. Le contrôle de confinement Jekyll exige désormais les deux bundles et les deux pages. Toute modification du corpus source nécessite de régénérer les bundles avec le même contenu et de réussir la CI avant déploiement. Le sondage **reste fermé** tant que l'approbation explicite de sa version n'est pas reçue.

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

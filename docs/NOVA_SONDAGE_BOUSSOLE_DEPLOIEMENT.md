# Projet NOVA — Mise en service contrôlée du sondage citoyen V1

**Statut : PRÉPARATION / PAS DE COLLECTE DE VOTES ACTIVE.**  
**Public :** personnes se déclarant âgées de 18 ans et plus.  
**Méthode :** consultation citoyenne ouverte, non probabiliste. Elle ne constitue ni une étude représentative de la population, ni une prédiction électorale.

## Contenu de cette livraison

- `projets/projet-nova/sondage-citoyen.html` : page publique, questionnaire, résultats agrégés publiés par lots et méthode.
- `projets/projet-nova/data/sondage-citoyen-v1.json` : huit formulations **provisoires** extraites *sans modification* de la Boussole Nova. Ne pas présumer qu'il s'agit du questionnaire historiquement approuvé sans comparaison avec les questions soumises antérieurement.
- `projets/projet-nova/assets/sondage-citoyen.{js,css}` : parcours anonyme et visualisation accessible.
- `supabase/functions/nova-civic-poll/index.ts` : API autonome avec limites de taille, validation d'origine, Turnstile, HMAC serveur, dépouillement atomique, seuil de publication et publication par lots espacés.
- `supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql` : script de schéma proposé, **non exécuté lors de cette livraison**.
- `projets/projet-nova/assets/boussole-electorale.js` : radar : les 16 axes conservent leurs positions même si des questions sont passées.
- `scripts/test_nova_civic_poll.py` : contrôles statiques en CI.

## Prérequis avant ouverture effective du vote

1. **Valider la formulation des huit questions** avec le texte approuvé et faire une révision de neutralité, accessibilité, clarté, bilinguisme si requis et conformité. Conserver le corpus source et la version de publication sans réécrire les questions après le premier bulletin.
2. **Revue sécurité et confidentialité avant collecte**, y compris l'évaluation du service Cloudflare Turnstile, de Supabase, de leur traitement de données techniques, des durées de conservation, de la Loi 25 et des obligations légales applicables. Prévoir contact, registre d'incidents et responsabilités.
3. Examiner `supabase/NOVA_POLL_SCHEMA_PREDEPLOY.sql` et le déployer via une migration formelle Supabase en fenêtre de changement maîtrisée. Confirmer que les trois tables ont **RLS activée** et qu'aucun rôle public `anon` / `authenticated` ne peut interroger, modifier les compteurs ou lancer `nova_poll_submit`.
4. Configurer Cloudflare Turnstile pour les domaines `www.benoitcantin.com` et `benoitcantin.com`. Créer un secret HMAC long, aléatoire, dédié, non partagé et **non publié dans Git**. Configurer les variables privées dans Supabase : `NOVA_POLL_TURNSTILE_SECRET`, `NOVA_POLL_TURNSTILE_SITE_KEY`, `NOVA_POLL_HMAC_KEY`, `NOVA_POLL_ENABLED=false` par défaut. Supabase fournit `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` côté fonction ; jamais les afficher au navigateur.
5. Déployer `nova-civic-poll` avec `verify_jwt=false` **uniquement après les tests**. Contrôler que cette API ne répond qu'aux origines autorisées. Attention : la validation du seul header Origin n'est pas une authentification ; la protection serveur repose également sur Turnstile, la validation stricte et le refus des privilèges directs aux clients.
6. Exécuter les tests négatifs et positifs en environnement de préproduction : hors origine, préflight, appel sans CAPTCHA, CAPTCHA invalide, âge non confirmé, questionnaire incomplet, doublon, replay, réponses hors plage, corps volumineux, erreurs réseau, refus de publication avant 10 bulletins, publication par lots d'au moins 10 nouveaux votes, délai minimal de 6 heures, interdiction d'accéder aux compteurs bruts et accès public uniquement aux instantanés agrégés.
7. Appliquer des mécanismes **complémentaires anti-abus** (contrôle de débit au niveau de la passerelle/WAF et surveillance anonymisée) sans stocker d'opinions politiques reliées à l'IP. **Ni CAPTCHA ni identifiant local ne garantissent l'unicité d'une personne** ; annoncer explicitement cette limite.
8. Tester mobile, clavier, lecteur d'écran, focus, erreurs, qualité des données, sauvegardes, reprise et compatibilité navigateur.
9. Après validation, fixer `published:true` dans `data/sondage-citoyen-v1.json`, puis activer `NOVA_POLL_ENABLED=true` dans les secrets serveur. Vérifier sur le **domaine public** le déroulement intégral puis observer les métriques techniques sans enregistrer de réponses individuelles.
10. Conserver un protocole de clôture, de suppression des empreintes de jeton et de conservation des seuls compteurs agrégés. Le vote ne peut pas être supprimé individuellement après agrégation, puisqu'aucune association identité-réponse n'est conservée.

## Données, transparence, limitations

Le modèle de dépouillement ne stocke **pas de bulletin individuel** : seuls les compteurs par question et option sont persistés. Un HMAC de jeton aléatoire de navigateur est enregistré *séparément* pour détecter le rejeu du même jeton. Ce dispositif ne vérifie ni l'identité ni la citoyenneté et permet un nouveau vote si quelqu'un change d'appareil ou supprime les données du navigateur. L'âge 18+ est autodéclaré et non vérifié par une pièce d'identité.

Les résultats par option sont masqués tant que le sondage n'a pas atteint **10 bulletins**. Les résultats sont ensuite publiés seulement quand **au moins 10 nouvelles participations** ont été reçues depuis l'instantané précédent et **au moins 6 heures** se sont écoulées depuis la dernière publication. Cela réduit le risque de dévoiler un bulletin en comparant deux lectures successives. Les pourcentages portent sur les réponses reçues, incluant la catégorie « Sans opinion ». Ils ne décrivent pas l'opinion des Québécois et ne devraient pas être présentés comme tels.

La Boussole électorale, en revanche, est **distincte du sondage** : ses 64 réponses et son profil à 16 dimensions restent en mémoire locale et ne sont pas transmis au serveur par ce module. Les comparaisons de positions des partis demeurent soumises aux preuves documentaires et ne donnent aucune recommandation de vote.

## Publication et retour arrière

- Lien GitHub : branche feature + PR vers `main`. La branche ne modifie pas le site de production jusqu'à fusion et déploiement réussi.
- Un déploiement de la page statique avant la mise en service backend est sûr : formulaire visible, envoi **désactivé**.
- Pour arrêter immédiatement la collecte : `NOVA_POLL_ENABLED=false` côté Supabase. Les résultats agrégés peuvent rester visibles si la base et l'API sont disponibles.
- Conserver les journaux techniques de validation sans données sensibles et les résultats de vérification pour audit.

**Ne jamais annoncer « 100 % opérationnel » avant réussite des tests réels, examen des exigences applicables et validation de publication sur le domaine.**

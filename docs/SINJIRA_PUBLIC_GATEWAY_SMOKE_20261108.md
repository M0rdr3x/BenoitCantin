# SINJIRA — Validation HTTP publique et JWT (8 novembre 2026)

Le correctif des Comptes et du Registre est estimé à 80 % : les réglages de
courriels Auth/Formspree et leurs essais restent à vérifier. Ce contrôle est
**sans secret, sans compte et sans mutation métier**.

Le job GitHub Actions teste depuis un environnement réseau indépendant :
- HTTP 200 et présence des marqueurs du formulaire d'inscription;
- page de confirmation et script dédié;
- Registre, consentement facultatif et script corrigé v24.5.8;
- POST anonyme vide vers `notify-account-confirmation`, attendu rejet 401/403
  explicite Auth/JWT;
- POST anonyme vide vers `submit-character-questionnaire`, attendu rejet 401/403.

Les deux essais POST n'ont ni JWT, ni email, ni nom, ni questionnaire; ils
doivent échouer **avant** tout traitement côté fonction. Si l'un des contrôles
ne peut être réalisé, le job échoue **sans modifier les données** et il faut
examiner le journal pour distinguer panne de réseau et régression sécurité.

Ce test **ne constitue pas** un test d'inscription, d'authentification AAL2 ou
de livraison de courriels. Pour clôturer les 20 % restants :
1. exécuter le prévol hébergé Auth protégé déjà fusionné
   `.github/workflows/sinjira-auth-email-production-preflight.yml`;
2. vérifier les notifications réelles Formspree à
   `sinjiraofficiel@gmail.com` sur les deux formulaires avec consentement;
3. contrôler l'absence de doublons dans le journal et les essais AAL2.

Aucun abonnement payant ni clé serveur n'est utilisé par ce contrôle.

## Vérification supplémentaire Auth publique, sans secret — 8 novembre 2026

Le prévol HTTP vérifie aussi `GET /auth/v1/settings` avec la clé **publishable** déjà livrée au navigateur. Il contrôle seulement les indicateurs publics : fournisseur Email activé (`external.email`), création de comptes ouverte (`disable_signup=false`) et confirmation des adresses requise (`mailer_autoconfirm=false`). Le script ne publie jamais la clé ni le JSON de réponse. Des auto-tests négatifs simulent les régressions et les pannes réseau.

Cette vérification est strictement en lecture seule et ne prouve **pas** les paramètres privés `Site URL`, l'allowlist des redirections, le modèle HTML de confirmation ou la réception des notifications Formspree. Ces éléments nécessitent toujours le prévol Auth protégé GitHub puis des essais de messagerie réels.

Sources officielles : https://github.com/supabase/auth/blob/master/internal/api/settings.go ; https://supabase.com/docs/guides/getting-started/api-keys.


## Extension — cinq scripts JavaScript critiques

Le contrôle HTTP vérifie désormais cinq fichiers en plus des pages publiques,
de la porte JWT et des paramètres Auth : inscription, confirmation au clic,
Registre AAL2, client Supabase et configuration publique. Tous doivent servir
un HTTP 200, un type MIME JavaScript et les marqueurs des versions corrigées.
Les tests négatifs vérifient le 404, le repli HTML, l'ancienne version et la
taille de réponse anormale.

Le bilan réseau passe de 6 à **11 contrôles**. Aucun compte, secret, questionnaire
ou courriel n'est créé. Cette vérification ne démontre pas la réception Formspree
ni la configuration Auth privée; le correctif global reste à 82 % jusqu'à
validation de ces derniers jalons.

## Dépendance JavaScript Supabase figée — 8 novembre 2026

La version du SDK utilisée par le navigateur est désormais épinglée sur **@supabase/supabase-js 2.119.0** au lieu de `@2/+esm`. La version 2.119.0 est la version officielle stable du 4 novembre 2026; les URL jsDelivr flottante et explicite ont été vérifiées en lecture seule, toutes deux en HTTP 200 et `application/javascript`, avec un export `createClient`. Le changement ne modifie donc pas la version effectivement chargée au moment de la vérification. Il protège seulement contre une mise à niveau automatique lors d'une future publication Supabase.

Le validateur statique du parcours inscription → confirmation → AAL2 → Registre exige désormais exactement cet import et les options de session attendues. Le code ne contient ni nouveau secret ni règle de données. **Limite :** l'épinglage de version n'est pas une empreinte SRI du fichier généré par jsDelivr; son contenu reste construit par le fournisseur. Les tests de livraison des courriels et le contrôle Auth privé restent distincts; **84 %** n'est pas augmenté par cette maintenance préventive.

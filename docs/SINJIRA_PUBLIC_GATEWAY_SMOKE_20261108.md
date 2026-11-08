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

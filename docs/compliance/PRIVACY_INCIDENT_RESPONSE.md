# SINJIRA™ — procédure de réponse aux incidents de confidentialité

Version V24.4.83.

## 0. Objectif

Réagir rapidement sans détruire de preuve, sans exposer davantage les données et sans faire de déclaration juridique improvisée. Chaque incident potentiel est inscrit au registre interne dès qu'il est raisonnablement identifié.

## 1. Contenir

- révoquer/faire tourner les secrets compromis;
- fermer l'accès fautif ou la fonction concernée;
- limiter les privilèges;
- conserver les journaux nécessaires dans un emplacement protégé;
- ne pas copier inutilement des renseignements sensibles.

## 2. Inscrire au registre

Consigner au minimum: circonstances, catégories de données, date/période de l'incident, date de découverte, estimation du nombre de personnes, sensibilité, utilisations malveillantes possibles, conséquences, probabilité, mesures prises et notifications. Le registre est conservé au moins cinq ans après la découverte.

## 3. Évaluer le risque

Évaluer séparément:
- sensibilité des renseignements;
- possibilité d'usurpation, fraude, discrimination, humiliation, exploitation ou danger physique;
- nombre de personnes;
- présence de mineurs ou personnes vulnérables;
- durée d'exposition et possibilité réelle d'accès/copie;
- chiffrement/contrôles disponibles;
- probabilité et gravité du préjudice.

## 4. Déterminer les obligations de notification

- Québec: si l'incident présente un risque de préjudice sérieux, préparer les avis requis à la Commission d'accès à l'information et aux personnes concernées selon la loi.
- Canada/LPRPDE si applicable: évaluer le « risque réel de préjudice grave » et les obligations fédérales.
- RGPD/UK GDPR si applicable: déclencher immédiatement l'analyse permettant de respecter le délai réglementaire de notification applicable, notamment 72 heures lorsqu'il s'applique.
- Autre juridiction: documenter l'analyse et obtenir un avis local si nécessaire.

Ne jamais retarder l'analyse sous prétexte que la juridiction n'est pas encore certaine.

## 5. Avis aux personnes

Un avis doit être clair, factuel et utile: nature du risque, renseignements concernés dans la mesure appropriée, mesures prises, gestes de protection recommandés et moyen de contacter SINJIRA™. Ne pas divulguer de détails techniques qui augmenteraient le risque d'exploitation.

## 6. Correctif et post-mortem

- cause racine;
- contrôles qui ont échoué;
- données réellement exposées;
- correctifs déployés et tests;
- révision EFVP/menaces;
- mise à jour des politiques et du calendrier de conservation;
- fermeture uniquement lorsque les obligations et actions sont terminées.

## 7. Secrets et transparence

Les secrets, tokens, clés de service et données privées ne doivent jamais être copiés dans GitHub public, dans une issue publique ou dans une réponse destinée à l'utilisateur. La transparence publique sur un incident doit préserver la sécurité des personnes et toute enquête légitime.

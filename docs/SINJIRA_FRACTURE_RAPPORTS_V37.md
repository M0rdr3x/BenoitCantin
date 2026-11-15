# SINJIRA™ — Fracture V37 : rapports publics et Preuve unique

**Référence éditoriale :** `projets/sinjira/jeux/fracture-du-reseau-mere/regles.html`, édition « Déduction simplifiée ».

## Ce qui est effectivement développé

`assets/js/sinjira-fracture-reports-v37.mjs` ajoute un protocole **pur et déterministe** pour la phase de rapports publics d'une ronde. Il ne crée **aucun salon ni partie réseau** :

1. Pour 1–20 humains, préparer les 3–20 sièges et un ordre explicite de passage; appliquer 10 rondes ou 6 en Express dès 13 humains.
2. Accepter **un rapport par siège** (`resistance`, `reseau` ou `equilibre`) dans l'ordre indiqué. Un rapport mensonger reste autorisé; sa véracité n'est jamais déduite de la main.
3. Traiter immédiatement après chaque rapport le choix facultatif de révéler **une Preuve**, une seule fois par siège **pour toute la partie**.
4. Si une Preuve est publiée, exiger que son identifiant corresponde à l'une des **deux cartes Opération canoniques** de la main fournie au vérificateur. Ne publier que la carte révélée; ne jamais retourner la deuxième carte.
5. Rejeter les sièges erronés, tours décalés, doublons de Preuve, cartes inventées ou mains incohérentes.

Les états retournés sont gelés (`Object.freeze`) et ne contiennent que des informations **publiques** : configuration de ronde, ordre des sièges, rapports et cartes publiquement montrées comme Preuve. L'état ne contient aucun compte, identifiant de connexion, identité de faction ni main privée.

## Limites de sécurité : non négociables avant le réseau

- **Le module n'est pas un mécanisme d'autorisation.** Un navigateur peut forger `seat`, `state` ou `receivedCards`. Le futur serveur doit charger l'état de partie et les mains depuis un stockage protégé, authentifier la session, contrôler l'appartenance à la partie, le siège réellement contrôlé et le numéro de ronde. Pour Solo/Duo, le contrôle du siège invisible s'appuie sur `fractureSeatController` (V36) **côté serveur**.
- Les mains, identités, soupçons et accusations restent **strictement privés**. Ne jamais envoyer `receivedCards` ni l'état privé au navigateur d'un autre joueur, ni les journaliser. Le client reçoit seulement la sortie publique après validation serveur.
- Les transitions doivent être **atomiques** et vérifiées contre une version attendue (verrou/transaction) pour éviter deux rapports ou Preuves concurrents. L'utilisation de `Object.freeze` ne suffit pas contre les courses réseau.
- Le registre `usedProofSeats` doit être maintenu **durablement côté serveur**, reconstruit à partir d'un journal authentique et jamais accepté tel quel depuis le client.
- Une Preuve exige la comparaison avec la vraie main récupérée au **second passage**. La propriété d'une carte ne peut pas être prouvée par un argument de fonction que le navigateur contrôle.
- Refuser en production tout événement hors phase, d'un autre compte, d'un siège non contrôlé, d'une session expirée/révoquée ou d'une requête rejouée; vérifier RLS et absence de fuite inter-comptes en environnement isolé.
- Réévaluer les preuves lorsque le schéma des parties réseau sera arrêté; le moteur ancien reste suspendu. Aucun changement de base, Supabase, compte, secret, paiement, page publique ou activation du lobby dans cette V37.

## Prochaines étapes vérifiables

1. Implémenter les **soupçons confidentiels** (un numéro de joueur suspect par humain et par ronde), avec traitement privé et sans notification révélatrice.
2. Ajouter les **accusations finales** : nombre d'accusations distinctes égal au nombre d'agents, interdiction de s'accuser soi-même, départage par soupçons agrégés puis aléa autorisé et audit, bonus de 3 points par accusation.
3. Raccorder **côté serveur** les opérations, la progression et les contrôles d'identité/RLS à des transactions atomiques; tester plusieurs véritables comptes, la reconnexion, les rejets et les erreurs réseau.
4. Après validation éditoriale et technique, effectuer une recette multijoueur et seulement ensuite décider d'une éventuelle réactivation de `jouer.html`.

## Contrôles exécutables

`node --test tests/games/test_fracture_reports_v37.mjs` couvre les parcours de 1 à 20 joueurs, l'ordre non standard, les rapports mensongers, les Preuves légitimes/illégitimes, la non-divulgation de la main et le registre multi-rondes. Le workflow GitHub V37 lance aussi les tests V36 exacts sur `main`/PR.

**Programme complet :** suivi [#826](https://github.com/M0rdr3x/BenoitCantin/issues/826). Cette version est **une brique technique** et ne justifie pas d'augmenter à elle seule la maturité globale actuelle estimée à **67 %**.

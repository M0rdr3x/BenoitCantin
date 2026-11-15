# SINJIRA — Formspree : essais synthétiques sur lancement manuel

Date : 2026-11-08. Objet : vérifier l'acceptation technique des **deux**
endpoints Formspree, sans transmettre la moindre donnée d'utilisateur.

## Déclenchement (doit être autorisé explicitement)

1. Accéder au workflow :
   https://github.com/M0rdr3x/BenoitCantin/actions/workflows/sinjira-formspree-synthetic-smoke.yml
2. Choisir **Run workflow** puis **main**, entrer exactement
   `AUTORISER_DEUX_TESTS_FORMSPREE`.
3. Approuver l'environnement GitHub `production`, si la protection est active.
4. Vérifier le résultat du job `Deux POST synthétiques sous approbation`.
   Aucun envoi sur `push` ni sur une PR : ceux-ci ne font qu'un auto-test local.

Le job fait **au plus un POST par endpoint** de cette exécution :
`xzeeqynp` (compte), `mrppvrwa` (Registre). Les données ne comprennent
que : email de test `sinjiraofficiel@gmail.com`, identifiant d'exécution
de CI, date, libellé de test, message indiquant qu'il ne s'agit **pas** d'une
inscription ni d'un questionnaire réel.

Aucun mot de passe, jeton, nom, questionnaire, photo, identifiant de compte
ou donnée de participant n'est transmis. Aucun secret GitHub n'est lu, aucune
configuration modifiée, aucun paiement et aucune répétition automatique
après erreur réseau ou HTTP. La sortie ne publie pas le contenu des réponses
du service tiers.

## Ce que ce test permet et ne permet pas

Un résultat `PASS ... HTTP 2xx` signifie uniquement que Formspree **a
accepté les POST**, **pas** qu'une notification a été remise dans la boîte
de réception ni qu'un accusé automatique participant est configuré.

La vérification humaine suivante est obligatoire : rechercher les deux
messages portant `TEST_TECHNIQUE_SINJIRA` dans le tableau de bord
Formspree et dans les courriels administratifs, contrôler les indésirables,
puis confirmer la règle de destinataire `sinjiraofficiel@gmail.com`.
Éliminer les soumissions de test selon les réglages de conservation du compte.

Pour passer à 100 % : prévol hébergé Supabase Auth (Site URL, redirections,
modèle de confirmation), parcours test réel avec consentement et AAL2,
preuve de réception des notifications et accusés. Un POST synthétique direct
ne remplace **pas** un test de la fonction Edge après consentement.

Le pourcentage global reste estimé à **82 %** tant que les livraisons
effectives ne sont pas attestées.

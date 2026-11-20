# SINJIRA — V118 : annuler le geste en cours dès qu'une nouvelle page est signalée

**15 novembre 2026** — correctif en revue dans la PR #1000, sans déploiement.

## Problème

La V117 invalidait le geste en cours si le **numéro de la page source** avait changé entre `touchstart` et `touchend`. Mais le moteur PDF principal V26 émet `sinjira:reader-page-change` au chargement d'une nouvelle page; une nouvelle édition, une réinitialisation ou un retour à la même page peut conserver le même numéro et rendre néanmoins le geste précédent obsolète.

## Correctif

Les gestionnaires tactiles **V52** (PDF tactile et glissement souris) et **V53** (texte adaptable paginé) invalident immédiatement leur contact en cours à la réception de `sinjira:reader-page-change`, quel que soit le numéro affiché. Le moteur V52 nettoie aussi cet écouteur à la destruction. Les protections V117 fondées sur les numéros restent en place pour les changements n'émettant pas l'événement.

Aucun contenu de livre, identifiant, autorisation, emplacement ou compte n'est lu ni stocké. Aucun appel au serveur. Les gestes suivants, commencés sur la page nouvellement chargée, continuent à tourner les pages dans les deux sens. URLs cache mises en cohérence : V52 `52.11.15.118` et V53 `53.11.15.118`.

## Tests

- Tests Node en modes PDF tactile, PDF souris et texte paginé : événement source sans changement de numéro pendant le contact, ancien geste annulé, geste suivant accepté, nettoyage de l'écouteur vérifié.
- Playwright Chromium/WebKit sur la vraie page HTML avec roman synthétique : émission de l'événement canonique au milieu du contact et vérification de l'absence de tournage involontaire. Le parcours complet continue de vérifier les balayages avant/arrière et les dimensions mobiles.

**NO-GO publication** : la PR demeure DRAFT, non fusionnée et non déployée. Les essais sur appareils physiques iPhone/Android, VoiceOver/TalkBack, droits Auth/RLS, synchronisation réelle, revue humaine et les 13 conditions de lancement restent obligatoires. Les chiffres globaux des programmes Nova/SINJIRA demeurent ceux des audits précédents.

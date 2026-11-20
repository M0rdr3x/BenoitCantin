# SINJIRA™ — V99 : gestes tactiles natifs dans le navigateur mobile

**Date : 14 novembre 2026 · PR #1000 DRAFT · aucun déploiement.**

## Objectif et portée

La V97 offre les balayages gauche/droite et les tapotements sur les marges en **texte paginé** et en **PDF**. La V98 vérifie le comportement sur la vraie page `compte/liseuse.html`, mais avec des `TouchEvent` construits par JavaScript. La V99 ajoute une preuve distincte : de **véritables événements tactiles émis par les moteurs de navigateur** sous Playwright en mode mobile (`is_mobile=True`, `has_touch=True`) via `page.touchscreen.tap(x,y)`.

Cette simulation demeure une **émulation de navigateur**, pas une mesure sur un écran tactile physique iPhone ou Android.

## Scénarios ajoutés dans `tests/e2e/test_sinjira_liseuse_real_page_v57.py`

1. Charger la page HTML officielle en édition de démonstration, **sans roman privé**, avec PDF fabriqué localement et appels externes interdits.
2. Après les contrôles V98, en **mode PDF** et à la page 4 : toucher le centre (aucun changement), la marge gauche (une seule page précédente) et la marge droite (une seule page suivante). Compter les clics sur les commandes canoniques, afin de détecter un double passage lié au `click` synthétisé après un `touchend` natif.
3. Vérifier que `touchstart` provient bien du moteur de navigateur (`event.isTrusted`) et correspond à un seul contact.
4. Revenir au **texte paginé** et toucher la marge droite pour faire avancer un écran, puis la marge gauche pour revenir au début sans changer la page source PDF.
5. Conserver tous les tests V57–V98 : balayage, lecture responsive, rotation, navigation clavier, et sauvegarde locale de la progression dans le livre de démonstration.

Les positions des touches sont calculées à partir des coordonnées visibles de la liseuse. Un contrôle DOM `elementFromPoint` vérifie que la cible est à l'intérieur du vrai lecteur, après l'avoir ramené dans la fenêtre si nécessaire.

## Conditions de validation et risques résiduels

Les vérifications Chrome/Chromium et Safari/WebKit Linux sont exécutées dans la CI, en conditions sans connexion à Supabase et sans donnée privée. L'homologation doit vérifier un succès de tous les jobs requis **sur le commit HEAD exact de la PR**, et non sur un ancien commit. Le statut sera publié dans le fil de la PR après les contrôles.

Restent hors de portée : véritables appareils iPhone/Android, lecteurs d'écran VoiceOver/TalkBack, autorisations et révocations des romans privés authentifiés, synchronisation CAS/RLS multi-appareils, 13 portes de lancement de SINJIRA. **NO-GO production.**

## Référence d'avancement conservée

Bilan du 8 novembre 2026 : Nova **47 %** (cible conditionnelle 31 décembre 2027, report possible en 2028+), Nova–Sinjira **sans pourcentage global vérifiable** (14 secteurs recensés), sondage citoyen **54,5 %** (6/11 critères), boussole électorale **75 %** (9/12 critères), SINJIRA complet **66,5 % ±10 points** avec 13/13 conditions de lancement ouvertes. Aucun de ces scores n'est recalculé par un test de liseuse.

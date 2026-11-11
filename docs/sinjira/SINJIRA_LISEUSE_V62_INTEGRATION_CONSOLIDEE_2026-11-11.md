# SINJIRA — Liseuse tactile V62, intégration consolidée depuis `main`

**11 novembre 2026 · PR candidate, à revoir, NON publiée.**

## Pourquoi une intégration unique ?

Les changements de la liseuse tactile ont été préparés dans des branches successives V52 à V61, avec trois niveaux critiques de navigation : moteur PDF historique V26, compagnon de livre V28 et reflow mobile V53. La base de [l'intégration V58 #983](https://github.com/M0rdr3x/BenoitCantin/pull/983) avait pris du retard par rapport à `main`, même si les nouvelles modifications du site ne touchaient pas les mêmes fichiers.

**V62 reprend directement les fichiers de code et de tests validés dans la branche V61 sur le `main` actuel.** Elle remplace l'empilement comme point d'entrée de revue, sans appliquer les modifications SQL V51/V59, sans copier les multiples workflows historiques et sans modifier les autres fonctionnalités du site.

## Expérience de lecture visée

| Interaction | Comportement |
|---|---|
| Glisser vers la gauche | Lire l'écran de texte suivant; changer de page source PDF seulement lorsque sa lecture est terminée |
| Glisser vers la droite | Revenir à l'écran précédent; à la première portion, revenir à la fin de la page source précédente |
| Lecture sur téléphone | Texte adapté à la largeur et aux préférences, 5 formats tests de 320 à 820 px, paysage inclus |
| Fin de page | Éviter les micro-écrans de quelques pixels; conserver une ligne de recouvrement |
| Réglages | Taille jusqu'à 34 px, interligne, rotation; reprise proportionnelle après redimensionnement |
| Lecture continue | Option sans pagination par écrans et mode PDF conservés |
| Navigation clavier | Flèches seulement lorsque le **livre est au focus**; aucune commande PDF historique en double |
| Lecteurs d'écran | Libellés ARIA « écran » ou « page du livre » selon le mode, annonces de progression non répétées, focus visible |
| Reprise locale | Marque-page de démo conservé et retrouvé sur rechargement dans les tests |
| Mode PDF | Un seul changement de page source par geste |

Ce système découpe le **texte extrait du PDF** et n'est **pas encore un moteur EPUB sémantique**; les ancrages dépendent encore de `scroll_ratio`. Les documents longs, images et mises en page inhabituelles imposent des essais complémentaires.

## Comparaison et provenance

- Source des implémentations : [PR V61 #995](https://github.com/M0rdr3x/BenoitCantin/pull/995) et ses ancêtres [V60 #991](https://github.com/M0rdr3x/BenoitCantin/pull/991) et [V58 #983](https://github.com/M0rdr3x/BenoitCantin/pull/983).
- Refonte sur une **nouvelle branche issue de `main`**, afin de conserver les corrections contemporaines aux comptes, aux registres et au site qui ne chevauchent pas les modules de liseuse.
- Six fichiers de code/site : `compte/liseuse.html`, `assets/css/sinjira-liseuse-v26.css`, moteurs V26/V28 et modules V52/V53.
- Six fichiers de test : deux suites Node, trois scénarios Playwright et une fixture HTML fictive.
- Un seul workflow CI de lecture et un seul dossier consolidé pour l'examen de cette version; pas de migrations, de nouvelles routes Supabase, de clés ou de fichiers de romans dans cette PR.

## Vérifications de réception V62

La CI `.github/workflows/sinjira-liseuse-mobile-v62-consolidee.yml` doit réussir **64 tests Node** et trois suites de navigateur sur la **vraie page de la liseuse** dans **Chromium et WebKit**. Elle vérifie la navigation, le passage entre pages sources, le mode PDF, les commandes accessibles, la position de lecture locale, les cinq formats mobiles/tablettes, la police de 34 px et l'orientation.

Les parcours isolent le PDF **par du faux texte** et interdisent les accès au compte Supabase. Leur succès ne constitue **pas** une réception iPhone/Android réelle. Les résultats ne sont considérés validés qu'une fois les deux jobs réussis sur le SHA final.

## Portes obligatoires avant fusion/publication

- [ ] Deux jobs CI Chromium/WebKit verts sur le commit final
- [ ] Revue du diff et décision responsable, comprenant le mode PDF historique
- [ ] Essais gestuels physiques iPhone Safari et Android Chrome (petit/grand écran), tablette et rotation
- [ ] Essais VoiceOver/TalkBack, sélection, clavier physique, police 34px, focus et annonce de page
- [ ] Essais d'un PDF démo réel et d'une édition intégrale autorisée avec le nombre réel de pages, performance et mémoire
- [ ] Validation des droits d'accès au roman, du retrait des jetons et des caches PWA
- [ ] Synchronisation de la position entre deux appareils, y compris en cas de conflit, avec sécurité SQL V51/V59 ([PR #986](https://github.com/M0rdr3x/BenoitCantin/pull/986))
- [ ] Validation de publication et plan de retour arrière

La présente PR est **un candidat de mise en commun**, pas un déploiement. Ne pas fusionner simultanément #983, #991 et #995 en plus de V62, pour éviter les modifications concurrentes. Garder les PR historiques accessibles comme preuves jusqu'à ce que la réception soit terminée.

## Avancement des autres projets

Les scores du [bilan du 8 novembre consolidé dans `main`](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md) restent : **Nova 47 % (finances 3/16, fin 2027 conditionnelle), Nova–Sinjira : aucun taux global calculable sur 14 secteurs, boussole 75 %, sondage 54,5 % et SINJIRA 66,5 % ±10 points avec 13/13 portes de lancement ouvertes.** Cette PR ne les modifie pas, ne lance pas de sondage et ne garantit aucune date de fin.

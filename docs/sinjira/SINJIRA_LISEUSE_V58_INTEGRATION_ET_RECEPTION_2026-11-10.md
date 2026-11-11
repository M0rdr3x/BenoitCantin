# SINJIRA™ — V58 : intégration de la liseuse mobile et contrôle de publication

**Date du référentiel : 10 novembre 2026 · Statut : candidate DRAFT · Pas de déploiement.**

## Décision recherchée

Transformer les six travaux dispersés de la liseuse mobile **V52→V57** en **une seule demande d'intégration à examiner pour `main`**, afin de ne pas publier les modules dans le mauvais ordre. La V58 ajoute une matrice réelle de tests de rendu responsive et un rapport de réception.

**Attention :** la branche d'intégration dérive de V57 et non directement du `main` courant. Le dépôt peut avoir avancé depuis sa création. Avant une fusion éventuelle, vérifier le différentiel, les conflits éventuels, les 8 commits `main` observés en avance sur la branche V57 lors de la préparation, et refaire tous les contrôles sur la version réconciliée. Ne pas présumer le statut de mergeabilité.

## Comportements attendus de la liseuse

| Cas d'utilisation | Comportement visé |
| --- | --- |
| Geste gauche en texte adaptable | Un écran lisible plus loin; **pas** une page PDF entière si du texte reste sur la page source |
| Geste droite en texte adaptable | Reculer d'un écran, puis dernière portion de la page PDF précédente |
| Geste gauche/droite en mode PDF | Une seule page PDF par balayage; garder le zoom et le défilement utiles |
| Smartphone petit | Pas de débordement horizontal, texte à l'intérieur de la zone de lecture, boutons tactiles >=44px |
| Smartphone standard | Même comportement avec plus d'espace |
| Rotation en paysage | Recalcul des portions sans changement de page source involontaire |
| Tablette 768/820px | Même lecture par écrans avec contrôles tactiles accessibles |
| Police maximale (34px), interligne 2.1 | Reflow cohérent, pas de débordement horizontal ni ligne masquée d'un écran à l'autre |
| Lecture plein écran | Activation/sortie du mode sans perdre les commandes ou l'emplacement |
| Marque-page et reprise | Numéro de page source et proportion `scroll_ratio` récupérés après rechargement de la démo |
| Vie privée | Aucune donnée d'édition intégrale, jeton, PDF privé ou identifiant Supabase dans les tests |

## Évidence technique cumulative

1. V52 #961 : détection des gestes horizontaux, protection contre diagonales, sélection de texte et zoom PDF.
2. V53 #964 : pagination verticale par portions d'écran du texte existant (pas de parser EPUB natif).
3. V54 #968 : tests Playwright dans Chromium et WebKit avec texte synthétique.
4. V55 #973 : marge intérieure et recouvrement d'une ligne pour réduire les sauts visuels.
5. V56 #975 : réduction des annonces `aria-live` répétées et restauration de position regroupée lors des changements de taille/orientation.
6. V57 #977 : **vraie page HTML** `compte/liseuse.html` testée avec un faux PDF, détection et correction du troisième gestionnaire tactile hérité de V28; sauvegarde/reprise de démo vérifiées. [CI V57 : deux navigateurs réussis](https://github.com/M0rdr3x/BenoitCantin/actions/runs/42945731621).
7. V58 : tests supplémentaires `test_sinjira_liseuse_responsive_v58.py` couvrant **320×568, 390×844, 844×390, 768×1024 et 820×1180** pixels, la taille de texte 34px, l'interligne 2.1, les boutons tactiles, le mode lecture plein écran et les débordements horizontaux. La réussite éventuelle des CI doit être vérifiée **sur le dernier SHA** de l'intégration.

### Ce que ces tests ne certifient pas

Le navigateur Chromium/WebKit sur Linux, même simulant une interface mobile, **n'est pas un iPhone Safari physique, un téléphone Android réel ni un test VoiceOver ou TalkBack**. Le PDF et le système de connexion sont remplacés par un matériau synthétique; la reprise d'un roman privé multiappareil et le contrôle réel des droits d'accès restent **non certifiés**.

## Portes formelles avant fusion et publication

- [ ] Différence `main`→V58 réconciliée avec le dernier `main` : conflit nul ou arbitrage revu
- [ ] Exécution finale de tous les jobs Chromium et WebKit en statut SUCCESS sur le **SHA à fusionner**
- [ ] Essais physiques de lecture sur iPhone Safari et Android Chrome (petit/grand écran, portrait/paysage)
- [ ] Essais tablette Safari/Android, boutons et taille de police 34px
- [ ] VoiceOver/TalkBack, focus clavier, surlignage et sélection, absence d'annonces parasites
- [ ] Vérification de PDF réel des 82 pages démo et 520 pages intégrales avec accès valide
- [ ] Validation de l'autorisation privée côté serveur et de la migration V51 [#947](https://github.com/M0rdr3x/BenoitCantin/pull/947), notamment le signalement [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955)
- [ ] Revue du service worker/cache PWA, de l'absence de versions mélangées et du droit de retrait sur déconnexion
- [ ] Essai de synchronisation de progression entre deux appareils sans écrasement de la position la plus récente
- [ ] Approbation responsable de production et plan de retour arrière

**Décision actuelle : PAS DE GO production.** Maturité SINJIRA **66,5 % ±10 points**, 13/13 portes de lancement globales toujours ouvertes. Un succès du contrôle des gestes ne constitue pas une autorisation de publier un site ni une preuve d'atteindre 100 %.

## Priorités interprojets conservées

- **Projet Nova politique :** 47 % au référentiel; budget décennal, fiscalité et arbitrage juridique à compléter; cible du 31 décembre 2027 conditionnelle.
- **Nova–Sinjira services publics :** 14 secteurs, mais taux global non estimable avec preuve suffisante.
- **Boussole :** 75 %, 9/12 portes; **sondage :** 54,5 %, 6/11 portes.
- **SINJIRA :** 66,5 % ±10 points; date de livraison non certifiable.

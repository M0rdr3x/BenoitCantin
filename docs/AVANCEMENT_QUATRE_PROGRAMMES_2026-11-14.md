# Bilan des quatre programmes — référence du 14 novembre 2026

**Date de référence demandée : 14 novembre 2026.** Vérification des sources versionnées et de la branche de liseuse : 15 novembre 2026. **Bilan interne, non certifié.**

> Ce rapport ne recalcule pas arbitrairement les indicateurs : les derniers registres source ne démontrent pas un nouvel état homologué au 14 novembre. Le score de maturité du programme, l'inventaire des services, les portes d'homologation des outils civiques et l'estimation de maturité de SINJIRA sont des mesures **distinctes et non additionnables**.

## Chiffres de référence et dates

| Périmètre | Indicateur vérifiable | Méthode et source datée | Fin |
| --- | ---: | --- | --- |
| Projet Nova — programme politique | **47 / 100 = 47 %** | Audit provisoire du **5 novembre**, 10 dimensions pondérées | **31 décembre 2027** : *objectif conditionnel* uniquement; 2028 ou au-delà possible |
| Projet Nova–SINJIRA — 14 secteurs | **Pourcentage global non calculable** | Registre du **3 novembre**, contrôle documentaire du **12 novembre** : 14 secteurs identifiés, **0** jeu précis complet documenté, **0** coût validé, **0** contrôle qualité validé | **Inconnue** |
| Projet Nova — boussole électorale | **9/12 = 75 %** | Portes d'homologation du **8 novembre**, non un résultat électoral | **Inconnue** — 3 portes ouvertes |
| Projet Nova — sondage citoyen | **6/11 = 54,5 %** (arrondi) | Portes d'homologation du **8 novembre**, non un résultat de participation | **Inconnue** — 5 portes ouvertes; collecte non ouverte |
| SINJIRA™ — plateforme complète | **66,5 %** (incertitude **±10 points**) | Moyenne pondérée de 10 domaines au **8 novembre**; **13/13 conditions de lancement ouvertes** | **Inconnue** — aucun GO de lancement |

**Précaution de date.** Ces dernières valeurs sont soutenues par leurs sources d'origine des 3–12 novembre. Aucune mesure certifiée nouvelle au 14 novembre n'autorise à changer ces scores ni à extrapoler une date de fin depuis un pourcentage restant.

## Dépendances majeures

### Projet Nova
Le score **finances est de 3/16** dans l'audit. Avant de déclarer un programme complet : textes et compétences juridiques, assiettes fiscales et effets de distribution, budgets décennaux **dans les deux scénarios** (Québec au Canada et souveraineté), dette, coût des transitions, garanties de services, avis juridiques/financiers indépendants et consultation/adoption formelles. La date de fin 2027 est une cible d'organisation, **pas une adoption garantie**.

### Nova–SINJIRA
Achever **G0 (qualité des preuves)** pour NV-01 à NV-14 avant de comparer des modes de service ou de chiffrer les bénéfices. Chaque dossier requiert jeu de données identifié, période, territoire, population, unités, année de prix, modes de coût comparables, personnel, transition, impacts sur les citoyens et revue indépendante. Le zéro de preuves validées **ne signifie pas 0 % du travail réalisé**.

### Boussole et sondage
- **Boussole :** revue WCAG/accessibilité indépendante, essais appareils réels et sources comparatives des partis. Le profil individuel reste distinct du sondage, la comparaison de partis non homologuée.
- **Sondage :** choix et approbation du questionnaire exact (8/40/64 questions selon les objets distincts), revue de confidentialité/loi applicable, CAPTCHA et contrôles anti-abus, tests privés de bout en bout et décision d'ouverture expresse. **Ne pas recueillir d'opinions politiques par anticipation.**

### SINJIRA — liseuse tactile
La [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) demeure **DRAFT, non fusionnée, non déployée**. La branche contient la navigation **glissement gauche = suivant / droite = précédent**, les pages de texte adaptées à l'écran du téléphone et le mode PDF, la rotation, le réglage typographique et le retour de lecture. Les révisions testées au **15 novembre** atteignent **V129**; il s'agit d'une **actualité technique postérieure à la date de référence du bilan**, sans rehausser le 66,5 %. Les 40 workflows GitHub Actions du **SHA V129** examiné le 15 novembre (31 réussis, 9 ignorés conditionnellement, 0 échoué) attestent la **CI de ce SHA**, non la réception réelle. **Suite V130 (15 novembre, après la référence du bilan)** : [correctif plein écran dans la même PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), commits `9ed3abe437dda3ac3cf643138aab0188aa7fa71f` et `5502156943a577bb586bb1de30cd1780fdbac541`. Le premier SHA V130 a révélé des **assertions de versions V129 obsolètes dans la CI**, corrigées dans le second SHA. **CI finale de V130 vérifiée sur `5502156943a577bb586bb1de30cd1780fdbac541` : 40 workflows terminés, 31 SUCCESS, 9 SKIPPED conditionnels et 0 FAILURE.** Ces tests ne certifient pas une réception sur téléphone physique ni les droits d'accès privés. Aucun changement des cinq indicateurs ci-dessus ni publication de la liseuse.

**Suivi technique ultérieur au 16 novembre — liseuse V131 :** le [correctif de gestion du menu contextuel](https://github.com/M0rdr3x/BenoitCantin/pull/1000) a été enregistré dans la PR #1000 au commit `84ff39a2687ce6bc32b08116c212922e80b91747`. Les commandes de lecture doivent ignorer les anciens contacts après un appui long ou l'ouverture du menu de sélection, sans intercepter la sélection native. Tests Node/Playwright ajoutés et **CI du SHA V131 `84ff39a2687ce6bc32b08116c212922e80b91747` vérifiée : 40/40 workflows terminés, 31 SUCCESS, 9 SKIPPED conditionnels, 0 FAILURE**. Les tests automatisés ne certifient ni les gestes sur appareils physiques ni les accès privés. Ce changement postérieur au 14 novembre ne modifie pas les pourcentages de référence.

**Actualisation technique du 16 novembre — liseuse V132 :** [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), commit `3faf44c5742bfd2b9611a902e44d65e66ea74f22`. Correction du risque de changement de page involontaire lorsque la sélection d'un texte change sans ouvrir un menu contextuel. Les commandes gauche/droite restent actives et aucune donnée de sélection n'est enregistrée. **GitHub Actions sur le SHA final : 40 workflows terminés, 31 SUCCESS, 9 SKIPPED conditionnels, 0 FAILURE**. Cette avancée est **postérieure à la référence du 14 novembre** et n'augmente pas le score SINJIRA (66,5 % ±10 points), qui exige toujours une réception matérielle et serveur.

Avant fusion et publication : [matrice d'essais sur appareils physiques](https://github.com/M0rdr3x/BenoitCantin/blob/review/sinjira-liseuse-mobile-v64-integration-main-20261111/docs/sinjira/SINJIRA_LISEUSE_RECEPTION_APPAREILS_PHYSIQUES_2026-11-12.md), VoiceOver/TalkBack, PDF autorisés, droits serveur et révocation de l'accès privé, synchronisation entre deux appareils, validation d'une éventuelle migration avec approbation explicite et revue indépendante. Ne pas toucher aux secrets, au backend de production ou aux données réelles depuis le bilan.

**Intégrité du contrôle de sécurité (16 novembre 2026) :** la [PR #1051](https://github.com/M0rdr3x/BenoitCantin/pull/1051) a été fusionnée dans `main` au commit `851c9b28a790b799b6fe262811bb8140df5960fb` après **25 workflows réussis sur 25**. Elle corrige un validateur qui rejetait à tort le script MFA `24.4.70` en exigeant exactement `24.4.69`. Le garde-fou exige toujours une version au moins égale à `24.4.69` et refuse les doublons et versions absentes. Aucun score de complétude n'est modifié par cette maintenance CI. Le présent rapport attend sa propre validation de branche avant toute fusion.

## Ordre de livraison recommandé

1. **P0 sécurité et intégrité :** traiter les droits des livres intégraux (notamment [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955)), l'autorisation et les contrats serveur, sans déploiement implicite.
2. **P0 liseuse :** terminer l'homologation multi-appareils de la PR #1000 et documenter chaque scénario PASS/FAIL avec SHA et navigateur.
3. **P0 données de programme :** réduire les lacunes de preuve de la dimension finances Nova et des 14 secteurs sans inventer des coûts.
4. **P1 outils civiques :** revue indépendante et prévol privé du sondage; conserver la collecte fermée jusqu'à approbation.
5. **P1 décision de lancement :** CI sur SHA final, revue sécurité/accessibilité, plan de retour arrière et décision humaine formelle.

## Sources versionnées

- [Nova, audit 47/100](../projets/projet-nova/data/audit-completude-programme-nova-2026-11-05.json)
- [Nova–SINJIRA, registre 14 secteurs](../projets/projet-nova/data/registre-donnees-services-nova-sinjira.json)
- [Contrôle du registre au 12 novembre](NOVA_SINJIRA_PREUVES_14_SECTEURS_2026-11-12.md)
- [Boussole/sondage, 9/12 et 6/11](nova-sondages/reception-sondage-boussole-2026-11-08.json)
- [SINJIRA, score pondéré et 13 portes ouvertes](sinjira/programme-readiness-2026-11-08.json)
- [Bilan de référence du 10 novembre](AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md)
- [PR #1000, liseuse mobile candidate](https://github.com/M0rdr3x/BenoitCantin/pull/1000)

**Limite méthodologique :** aucun pourcentage n'est issu d'un décompte homogène d'issues/PR, d'une durée de travail mesurée ou d'une certification indépendante. L'avancement du code sur une branche de préproduction n'est pas un déploiement en service.


## Qualification technique complémentaire — 16 novembre 2026 (V146)

**Mise à jour postérieure au bilan du 14 novembre; les indicateurs de référence ne changent pas.**
La [PR de liseuse tactile #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) demeure **ouverte en brouillon et non fusionnée**. Son HEAD examiné est `d666ef994b9f6e342bc1d0296e73d0b9d9bccc97` (V146). L'application publiée depuis `main` ne doit donc pas être présentée comme disposant déjà de cette version.

### Preuves GitHub au SHA V146

- **40 workflows terminés** sur le SHA exact : **31 `success`**, **9 `skipped`**, **0 `failure`**. Les workflows pertinents incluent V64 (mobile), V65 (gestes natifs Chromium), V66 (trajectoires), V67 (bords du navigateur), V68 (paysage) et V69 (priorité des gestes).
- La PR contient le balayage **gauche → écran/page suivante** et **droite → écran/page précédente**, la pagination du texte par écran, le PDF, les options de police et d'espacement, les modes portrait/paysage, les commandes tactiles/clavier et la sauvegarde de position. Les protections contre les gestes verticaux, la sélection de texte et l'état masqué ont été renforcées jusqu'à V146.
- La comparaison `main...branche V146` lors de ce contrôle signale **272 commits d'avance et 10 de retard** : la branche doit être rapprochée de `main` avec revue des changements et nouvelle CI avant toute fusion.
- Les tests automatisés avec moteurs Chromium/WebKit et PDF fictif **ne remplacent pas** des essais sur iPhone/iPad et Android physiques, ni une vérification de Safari iOS, VoiceOver et TalkBack.

### Portes de publication toujours fermées

1. **Essais physiques et accessibilité** : balayage dans les deux sens, pagination sur téléphone, zoom PDF, sélection de texte, geste système de retour, rotation, petite hauteur paysage, lecteur d'écran et réduction des animations; enregistrer appareils, versions et PASS/FAIL dans la [matrice de réception](https://github.com/M0rdr3x/BenoitCantin/blob/review/sinjira-liseuse-mobile-v64-integration-main-20261111/docs/sinjira/SINJIRA_LISEUSE_RECEPTION_APPAREILS_PHYSIQUES_2026-11-12.md).
2. **Sécurité du Livre I intégral** : accès autorisé puis révoqué, expiration de session, retour d'onglet/bfcache, absence de fuite du PDF privé ou de ses données dans le dépôt et le stockage local; vérifier les contrôles serveur et le coffre privé avant de publier.
3. **Synchronisation et robustesse** : reprise entre deux appareils réels, réseau instable/hors ligne, changement de police/rotation pendant lecture, sauvegarde et reprise après fermeture.
4. **Publication contrôlée** : rebaser/synchroniser proprement sur le `main` le plus récent, relancer toutes les CI au SHA final, revoir les différences, prévoir le retour arrière et obtenir une décision humaine explicite.

**Statut : NO-GO production** tant que ces preuves ne sont pas réunies. **Nova 47 %, Nova–SINJIRA non mesurable, boussole 75 %, sondage 54,5 %, SINJIRA 66,5 % ±10 points** : aucun taux n'est relevé du seul fait de ces travaux candidats. La cible politique conditionnelle du 31 décembre 2027 n'est pas une date de mise en production de SINJIRA.


### Actualisation technique du 16 novembre 2026 — synchronisation V152

La [PR #1085](https://github.com/M0rdr3x/BenoitCantin/pull/1085) a **fusionné `main` dans la branche candidate de la liseuse #1000**, sans fusion de #1000 dans `main` et sans publication du livre. Le commit de synchronisation est `22b40e3341d45e8e24ecef8c35123711915e4dd7`. Cette opération apporte **10 commits récents** de `main`, contenant des protections et tests de sécurité, tout en conservant les changements de la liseuse (moteur de pagination **V152**). Le contrôle `compare main...branche-liseuse` après fusion indique **273 commits d'avance et 0 de retard**. Les 44 fichiers de `main` ayant changé depuis la base commune ne chevauchaient aucun des 107 chemins modifiés dans la branche de la liseuse.

**Réception CI :** au premier contrôle sur ce nouveau SHA, les 40 workflows avaient été créés, dont **9 SKIPPED**, les autres étant encore en attente ou en cours. **Ne pas réutiliser les 31 succès de V146 pour certifier V152** : seul le résultat final sur `22b40e3...` permettra la clôture de cette étape. La PR #1000 reste **DRAFT / NO-GO production**. Restent les essais sur iOS/Android physiques, VoiceOver/TalkBack, les droits sur livres privés et la reprise multiappareil. Aucun des cinq indicateurs de complétude du bilan n'est augmenté automatiquement.

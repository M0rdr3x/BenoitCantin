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
La [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) demeure **DRAFT, non fusionnée, non déployée**. La branche contient la navigation **glissement gauche = suivant / droite = précédent**, les pages de texte adaptées à l'écran du téléphone et le mode PDF, la rotation, le réglage typographique et le retour de lecture. Les révisions testées au **15 novembre** atteignent **V129**; il s'agit d'une **actualité technique postérieure à la date de référence du bilan**, sans rehausser le 66,5 %. Les 40 workflows GitHub Actions du SHA de tête examiné le 15 novembre (31 réussis, 9 ignorés conditionnellement, 0 échoué) attestent la **CI**, non la réception réelle.

Avant fusion et publication : [matrice d'essais sur appareils physiques](https://github.com/M0rdr3x/BenoitCantin/blob/review/sinjira-liseuse-mobile-v64-integration-main-20261111/docs/sinjira/SINJIRA_LISEUSE_RECEPTION_APPAREILS_PHYSIQUES_2026-11-12.md), VoiceOver/TalkBack, PDF autorisés, droits serveur et révocation de l'accès privé, synchronisation entre deux appareils, validation d'une éventuelle migration avec approbation explicite et revue indépendante. Ne pas toucher aux secrets, au backend de production ou aux données réelles depuis le bilan.

## Ordre de livraison recommandé

1. **P0 sécurité et intégrité :** traiter les droits des livres intégrals (notamment [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955)), l'autorisation et les contrats serveur, sans déploiement implicite.
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

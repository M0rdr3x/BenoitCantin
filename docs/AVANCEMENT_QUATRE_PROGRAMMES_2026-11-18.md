# Bilan des quatre programmes — 18 novembre 2026

**Statut : bilan interne, non certifié indépendamment.** Les pourcentages sont les **derniers indicateurs sourcés** et ne constituent pas une réévaluation automatique à la date de ce rapport. Les indicateurs mesurent des périmètres différents et ne sont pas additionnables.

| Périmètre | Dernier indicateur démontré | Date de la mesure source | Date d'achèvement |
| --- | --- | --- | --- |
| Projet NOVA — programme politique | **47/100 = 47 %** (audit interne pondéré) | 5 novembre 2026 | **31 décembre 2027 : cible conditionnelle**, non garantie; 2028+ possible |
| NOVA–SINJIRA — réforme de 14 secteurs de services | **Non calculable** : pourcentage global non attesté | Registre du 3 novembre, contrôle du 12 novembre | Inconnue |
| NOVA — sondage citoyen | **6/11 = 54,5 %** de critères de réception (arrondi) | 8 novembre 2026 | Inconnue; collecte fermée |
| NOVA — boussole électorale | **9/12 = 75 %** de critères de réception | 8 novembre 2026 | Inconnue |
| SINJIRA™ — programme numérique et culturel complet | **66,5 % ±10 points** (grille interne pondérée de 10 domaines) | 8 novembre 2026 | Inconnue; **13/13 portes de lancement ouvertes** |

**Méthode :** on ne peut pas déduire une date de fin de « 100 moins le pourcentage ». Ni les durées du chemin critique, ni les preuves de réception indépendantes, ni les autorisations opérationnelles ne sont consolidées. La cible politique 2027 ne vaut pas date de livraison du site, de la liseuse ou d'une réforme des services.

## Actions prioritaires et critères de sortie

1. **NOVA — finances et cohérence juridique (P0).** Le pilier finances est à **3/16**. Établir les sources primaires, arbitrer « taxe unique » / « deux prélèvements », produire les budgets décennaux distincts Québec dans le Canada / Québec souverain, scénarios, compétences, avis juridiques/financiers indépendants et décisions documentées. Ne pas inventer de recettes de lutte anti-évasion ou considérer une proposition comme du droit en vigueur.
2. **NOVA–SINJIRA (P0).** Compléter et faire homologuer les preuves **G0** pour chacun des 14 secteurs avant G1–G4 (comparaison des coûts, droit et financement, pilote, évaluation). Aucune attestation G0 indépendante dans le dernier registre ne signifie pas « 0 % de travail accompli ». Ne pas attribuer de taux global sans modèle et validation.
3. **Sondage et boussole (P0/P1).** Garder le sondage **fermé** jusqu'à prévol privé complet, audit d'accessibilité WCAG 2.2 AA, CAPTCHA/anti-rejeu, confidentialité et autorisation expresse. Pour la boussole, faire homologuer accessibilité, navigateurs/appareils réels et sources documentaires comparatives des partis, en préservant une présentation neutre.
4. **SINJIRA et liseuse (P0).** Les contrôles automatisés du SHA candidat corrigé sont réussis; qualifier maintenant la navigation mobile et les droits privés sur matériel réel avant toute mise en service. Repasser la CI au SHA exact de livraison après toute modification. Valider séparation démo/édition intégrale, droit et révocation serveur, reprise de marque-page entre deux appareils, VoiceOver/TalkBack, sauvegarde CAS/RLS et revue indépendante. Aucun roman intégral ni secret dans GitHub.
5. **Décision de mise en service.** Ne pas fusionner une PR DRAFT sur simple succès synthétique. Obtenir revue indépendante, résultats PASS documentés sur appareils physiques et comptes fictifs de préproduction, plan de retour arrière et approbation du responsable. Les changements GitHub ne valent pas déploiement Supabase ou publication effective du site.

## Liseuse SINJIRA — situation technique au 18 novembre

La [PR #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) demeure **DRAFT, non fusionnée dans `main`, non déployée**. Le code candidat prévoit :

- **Glissement vers la gauche** : écran/page suivante; **vers la droite** : écran/page précédente.
- Sur téléphone, **pagination du texte par hauteur d'écran**, changement d'écran avant le passage à la page PDF suivante, réglages typographiques, portrait/paysage et conservation de l'emplacement lors de certains changements de disposition.
- Mode PDF fidèle avec boutons tactiles, clavier et, selon le périphérique, glissements au doigt/stylet/souris; protection contre les faux gestes (défilement vertical, sélection, zoom, bords système, masque de livre).
- Le mode privé exige **toujours** un contrôle réel côté serveur avant publication; une protection de l'interface n'est pas une preuve d'autorisation RLS/SQL.

**CI validée sur SHA exact de la liseuse :** le précédent commit `0a4f541d1cc579e9f70116236f259a31cd44b22a` avait **25 SUCCESS / 9 SKIPPED / 6 FAILURE**; les six suites V64–V69 échouaient sur une assertion de version de cache HTML obsolète (`52.11.18.158` dans le test contre `52.11.18.161` dans la page). Le correctif ciblé a été **commité dans la PR #1000** au SHA [`bbd1eb385b1558f22364068d0ba9286bb49af374`](https://github.com/M0rdr3x/BenoitCantin/commit/bbd1eb385b1558f22364068d0ba9286bb49af374). **Résultats GitHub Actions contrôlés sur ce SHA : 40 workflows terminés, 31 SUCCESS, 9 SKIPPED conditionnels, 0 FAILURE.** Les six workflows spécialisés V64, V65, V66, V67, V68 et V69 ont chacun conclu **SUCCESS**, ainsi que les autres contrôles applicables. Les 9 SKIPPED ne sont pas des homologations. **Ce résultat clôt le blocage de CI sur le SHA candidat, mais pas la recette matérielle, la sécurité serveur ni l'approbation de publication.**

**NO-GO publication maintenu**, indépendamment de la CI. Conditions externes non levées : iPhone/iPad/Android physiques, lecteur d'écran, serveurs et droits des romans privés, révocation et synchronisation sur deux appareils. Cela ne change pas le score SINJIRA.

## Sources primaires et suivi

- [Bilan historique du 14 novembre](AVANCEMENT_QUATRE_PROGRAMMES_2026-11-14.md) et [audit NOVA 47/100](../projets/projet-nova/data/audit-completude-programme-nova-2026-11-05.json), [issue #840](https://github.com/M0rdr3x/BenoitCantin/issues/840).
- [Registre NOVA–SINJIRA (14 secteurs)](../projets/projet-nova/data/registre-donnees-services-nova-sinjira.json), [issue #931](https://github.com/M0rdr3x/BenoitCantin/issues/931).
- [Registre de réception sondage / boussole](nova-sondages/reception-sondage-boussole-2026-11-08.json), [issues #934](https://github.com/M0rdr3x/BenoitCantin/issues/934) et [#919](https://github.com/M0rdr3x/BenoitCantin/issues/919).
- [Grille SINJIRA et 13 portes](sinjira/programme-readiness-2026-11-08.json), [issue #955 sur les droits des livres](https://github.com/M0rdr3x/BenoitCantin/issues/955).
- [PR liseuse #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) et [matrice d'essais physiques](https://github.com/M0rdr3x/BenoitCantin/blob/review/sinjira-liseuse-mobile-v64-integration-main-20261111/docs/sinjira/SINJIRA_LISEUSE_RECEPTION_APPAREILS_PHYSIQUES_2026-11-12.md).

**Interdictions de surinterprétation :** aucune affirmation « 100 % », « aucune faille », lancement autorisé, collecte politique ouverte, lecture privée homologuée ou date de fin garantie sans pièces probantes et validation indépendante.

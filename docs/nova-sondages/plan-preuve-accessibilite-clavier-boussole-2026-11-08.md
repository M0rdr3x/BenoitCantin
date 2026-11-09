# Projet Nova — Boussole électorale : parcours clavier vérifiable et limites d'accessibilité

**État au 8 novembre 2026 — proposition en demande de modification, non homologuée.**

## Ce qui est déjà documenté

La boussole est à **9 critères de réception réussis sur 12** (75 % de couverture) dans `reception-sondage-boussole-2026-11-08.json`. Les trois critères encore **PENDING** sont l'accessibilité indépendante, la compatibilité et le cache en conditions réelles, ainsi que la relecture documentaire des sources des partis. Le sondage reste **6/11** (54,5 %), `published:false` et `opening_poll_approved:false`. Ces fractions ne sont pas des pourcentages certifiés de lancement.

Le test local existant `tests/e2e/test_public_site.py` couvre beaucoup de fonctions de la boussole; la vérification publique `scripts/smoke_nova_live_compass_browser.py` parcourt déjà les 64 questions avec des choix synthétiques, dans trois navigateurs et un mobile émulé. Ni une émulation mobile ni une CI ne remplacent la revue manuelle de lecteurs d'écran et de dispositifs réels.

## Nouvel essai automatisé ciblé et reproductible

`tests/e2e/test_nova_compass_keyboard.py` est exécuté exclusivement contre `localhost` ou `127.0.0.1`. La CI l'intègre au pipeline navigateur existant : **Chromium, Firefox et WebKit**, chacun avec un profil desktop et un viewport mobile émulé. Il vérifie sans souris :

1. L'accès au bouton **Commencer** par focus et Entrée, et les repères de question.
2. La structure `fieldset > legend`, l'association ARIA entre le groupe et le libellé, les huit choix radio accessibles et l'importance nommée.
3. Le focus visible de la formulation de question; Tab atteignant le premier radio; Espace sélectionnant une réponse.
4. La mise à jour `aria-valuenow` (sur 64), les boutons désactivés tant que la question n'a pas reçu de réponse, puis Entrée pour avancer.
5. La sélection par clavier de **Sans opinion**, distincte d'une réponse neutre.
6. Le profil partiel sans position politique fabriquée et la restitution du focus au titre des résultats.
7. Le retour à zéro et la restitution du focus au démarrage, puis la vérification après rechargement.
8. L'absence de requêtes d'écriture et de connexions externes pendant la réponse; le test n'enregistre jamais les choix ni des URL de fuite potentielle.

**Aucune écriture en production, vote fictif sur Supabase, collecte citoyenne ou activation de comparaison de partis n'est effectuée.**

## Décision d'homologation strictement distincte

Même si ce nouveau test est vert, le critère `COMPASS_ACCESSIBILITY` reste **PENDING** jusqu'à un examen manuel indépendant incluant :

- Navigation clavier complète, pièges au focus, annonces vocales et compréhension des changements d'état;
- Essais avec technologies d'assistance (notamment lecteurs d'écran) et différents systèmes;
- Mesures documentées de contraste, redimensionnement, reflow et mouvement réduit;
- Évaluation de l'accessibilité sur les appareils et navigateurs effectivement visés, avec correctifs et revérification par une personne compétente.

Les deux autres critères `COMPASS_CROSS_BROWSER` et `COMPASS_DOCUMENTARY_VALIDATION` conservent également leur statut **PENDING**. Aucune hausse de 9/12 vers 10/12 ni déclaration à 100 % ne serait justifiée par le test clavier seul.

**Suivi des autres projets inchangé :** Nova politique **47/100** (cible de planification fin 2027 non garantie), modèle Nova–Sinjira **sans taux autonome**, SINJIRA complet **66,5 % ±10 points de maturité estimée** avec **13 portes de lancement ouvertes**.

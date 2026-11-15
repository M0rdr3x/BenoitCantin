# SINJIRA — V100 : balayage tactile natif sur la vraie page PDF

**14 novembre 2026 — PR #1000, brouillon non fusionné, non déployé**

## Pourquoi cette vérification

Les versions V97–V99 permettent déjà les glissements gauche/droite, les tapotements de marges et le retour à la position du livre. Le laboratoire V80 employait déjà le véritable moteur tactile Chromium via `Input.dispatchTouchEvent`, mais ses vérifications PDF concernaient en réalité le **mode texte à défilement libre**. Le mode **page PDF dessinée sur canvas** n'y était pas explicitement validé par un glissement natif.

## Réception V100

Le test `tests/e2e/test_sinjira_liseuse_native_touch_v65.py` ouvre la vraie page `compte/liseuse.html?edition=demo` dans Chromium mobile émulé, avec PDF fictif et appels réseau externes bloqués :

1. Il bascule de la lecture texte au **vrai mode PDF** et exige que `#reader-text` soit caché avec `readerLayout='scroll'`.
2. En partant de la page 4, un balayage tactile gauche **CDP natif** doit montrer la page 5; une seule activation de `#reader-next` est autorisée.
3. Un balayage tactile droit doit revenir à la page 4; une seule activation de `#reader-previous` est autorisée.
4. Le lecteur revient ensuite au **texte paginé**. Un nouveau glissement gauche doit avancer **d'un écran de texte** sans changer la page PDF sous-jacente, et sans double écouteur résiduel.
5. Les contrôles existants V65–V99 subsistent : gestes lents et rapides, seuil long, téléphones de 320 px, sélection, défilements, rotation, reprise, marges tactiles et absence d'accès aux données privées.

Les événements d'entrée proviennent de `Input.dispatchTouchEvent` et sont vérifiés `isTrusted`. Cela ne remplace pas un essai physique sur iPhone ou Android. Les autres suites de tests exécutent la lecture tactile dans Chromium et WebKit émulés.

## Conditions de sortie

- Exiger tous les workflows applicables en SUCCESS sur le **SHA exact** du dernier commit, sans échec.
- Ne pas fusionner la PR tant que les tests réels iPhone Safari, Android Chrome, lecteurs d'écran, contrôles des droits privés et synchronisation sécurisée entre appareils ne sont pas homologués.
- **NO-GO production** ; les 13 conditions de lancement SINJIRA restent ouvertes.

## Pourcentages inchangés (audit du 8 novembre 2026)

**Projet Nova : 47 %** (cible du 31 décembre 2027 conditionnelle; report possible en 2028 ou après). **Nova–Sinjira : aucun pourcentage global fiable**, 14 secteurs recensés. **Sondage citoyen : 54,5 %** (6/11 critères). **Boussole électorale : 75 %** (9/12). **SINJIRA complet : 66,5 % ±10 points**, 13/13 conditions de lancement ouvertes. Aucun de ces pourcentages n'augmente mécaniquement après un test de liseuse.

# SINJIRA™ — V96 : aucune navigation fantôme pendant une lecture privée masquée

**14 novembre 2026 · PR #1000 DRAFT · aucun déploiement.**

## Incident évité

Les versions V93/V94 masquent le contenu de lecture privée et les notes lors d'une suspension du navigateur ou de la perte des droits. Mais les moteurs V52 et V53 conservaient leurs écouteurs sur la page cachée. Un événement synthétique ou retardé (touche clavier, commande de pagination, contact tactile) pouvait encore modifier la page en mémoire et déclencher une progression alors que le roman était temporairement inaccessible.

Le correctif bloque ces **actions de navigation**, sans modifier le fait que le moteur de disposition peut recalculer les écrans pour le retour après une rotation ou un changement de taille.

## V96 — comportement

1. **Texte repaginé V53** : `canNavigate()` vérifie à chaque commande que `document.hidden` est faux et qu'aucun ancêtre du lecteur ne porte `[hidden]` (en particulier `#reader-content`). L'entrée dans un geste, les mouvements, la fin du geste, le tapotement V95 des marges, les flèches du clavier, les boutons tactiles et les boutons PDF canoniques se bloquent tant que la lecture est masquée.
2. Les clics sur les boutons PDF canoniques sont arrêtés **en phase de capture** lorsque le lecteur est masqué, avant que le moteur historique V26 ne les reçoive. Ainsi, un clic programmatique ne contourne pas simplement le contrôle de V53.
3. **Mode PDF V52** : mêmes barrières de visibilité pour la reconnaissance du balayage horizontal et pour les deux boutons tactiles.
4. **Reprise** : aucun état de progression n'est écrit ou effacé par la vérification. Lorsque le livre redevient visible, les gestes reprennent normalement après la validation privée V93/V94. `isPaged()` reste indépendant du masquage pour ne pas changer le mode de mise en page au cours d'une suspension.
5. Mise en cache : URLs V52 `?v=52.11.14.96` et V53 `?v=53.11.14.96` synchronisées entre HTML, imports ESM, fixture E2E, contrôles de contrat et les **7 imports de test de réagencement**; aucune double instance n'est attendue.

## Recette et contrôle

- `tests/sinjira-liseuse-reflow-v53.test.mjs` : parent caché, rejeter les gestes, les taps, le clavier et les boutons; le mode texte reste paginé et la reprise restaurée autorise à nouveau un vrai geste. Vérifier aussi l'onglet caché sans émission de `touchcancel`.
- `tests/sinjira-liseuse-touch-v52.test.mjs` : PDF visible/caché, boutons mobiles inactifs pendant la suspension et actifs au retour.
- `tests/e2e/test_sinjira_liseuse_mobile_v54.py` : sur la page HTML mobile de démonstration, masquer temporairement `#reader-content`, simuler les gestes, le clavier et les clics, confirmer que la page PDF source et le ratio restent inchangés.
- Chromium et WebKit sont des simulations de navigateur avec texte synthétique; aucun compte réel ni roman intégral n'est testé.

## Limites et décision de lancement

Aucun test sur de vrais iPhone/Android ni homologation VoiceOver/TalkBack. Aucun changement de session Auth, RLS, Edge Function, base de données, PDF privé ou synchronisation CAS. Le lecteur tactile **n'est pas encore déployé** : la PR reste en brouillon et les 13 portes de lancement SINJIRA demeurent ouvertes.

**Référence de programme inchangée au 8 novembre 2026** : Nova **47 %**, cible du **31 décembre 2027 conditionnelle**; Nova–Sinjira **sans pourcentage mesurable**; sondage **54,5 %**, boussole **75 %**; SINJIRA **66,5 % ±10 points**, date de fin indéterminée.

# SINJIRA V136 — empêcher le démarrage audio différé hors premier plan

**16 novembre 2026 — PR #1000 DRAFT, code candidat non fusionné ni déployé.**

## Menace ciblée

La V135 arrête la synthèse à la réception de `visibilitychange(hidden)`. Toutefois, une action de lecture programmée alors que l'onglet est déjà caché, ou une opération asynchrone `getPage/getTextContent` débutée juste avant sa suspension, peut aboutir après le changement d'application sur mobile. Les callbacks d'une voix active peuvent également intervenir sans nouvel événement de visibilité. Le lecteur doit refuser toute nouvelle émission audio dans ces cas.

## Code modifié

- Au début de `startNarration()`, interdire le démarrage si `document.visibilityState === 'hidden'` ou si le livre intégral privé est suspendu ou révoqué.
- Réévaluer **après les chargements asynchrones** et avant de remplir les segments de synthèse; conserver le garde de jeton et de page déjà existant.
- Dans `speakNext()` et la reprise audio, refuser aussi la synthèse lorsque l'onglet est caché ou les droits de lecture suspendus/révoqués, et annuler si besoin.
- Synchroniser la version de cache V26 à `34.11.16.136` dans le HTML et le contrat Node. Aucune donnée privée envoyée, aucune migration ni service externe.

## Recette automatisée

Sur la vraie page de démonstration HTML, avec PDF fictif et voix synthétique muette :
1. Fermer l'affichage fictivement, cliquer sur « Écouter », vérifier que `speak()` ne se déclenche pas.
2. Lancer `startNarration()` depuis le premier plan puis masquer l'onglet avant la reprise de ses promesses; aucun `speak()` tardif n'est accepté.
3. Revenir au premier plan et lancer la voix **volontairement**; elle fonctionne, puis Arrêter l'interrompt.
4. Vérifier l'absence de requêtes Supabase/réseau privées et de régression sur les gestes tactiles, via les workflows Chromium et WebKit.

**Exiger le résultat GitHub Actions sur le SHA final** pour qualifier l'essai. Un navigateur de laboratoire n'est pas une réception VoiceOver/TalkBack ni une preuve sur appareil physique.

**NO-GO publication** : PR #1000 en brouillon, tests de téléphones physiques, contrôle Auth/RLS/révocation serveur et synchronisation entre appareils à homologuer; chiffres Nova/SINJIRA inchangés.

# SINJIRA — V117 : ignorer le contact obsolète après changement de page

**15 novembre 2026** — correctif candidat à la PR #1000, sans fusion ni déploiement.

## Cas corrigé

Un utilisateur commence un glissement gauche/droite sur la page du roman N, puis une autre commande change le document à la page N+1 avant que le doigt (ou le bouton de la souris) soit relâché. Il ne faut pas que le `touchend`/`pointerup` de la page N tourne par erreur la page N+1.

## Intervention

- V52 : le champ canonique `#reader-page` est injecté au démarrage du moteur PDF. Il est lu au début de chaque toucher ou glissement souris; tout mouvement ou fin de contact sur un autre numéro est ignoré.
- V53 : la liseuse de texte paginé possède déjà `pageField`; la même vérification protège ses événements `touchmove` et `touchend`.
- La vérification est limitée à un numéro de page éphémère. Elle n'ajoute aucune lecture du livre, aucun stockage, aucun traitement d'identité ou des accès privés. Elle n'affecte pas les gestes normaux sur la page en cours.
- Cache des modules synchronisé : touch `52.11.15.117`, reflow `53.11.15.117`.

## Tests

Tests Node sur PDF tactile, PDF souris et texte paginé : le changement de page durant le geste n'est pas interprété comme un nouveau tournage, tandis qu'un nouveau geste normal continue à fonctionner. Test navigateur Playwright Chromium/WebKit sur la vraie page HTML avec roman synthétique et réseau privé interdit, en simulant un changement du numéro de page pendant le contact.

**NO-GO publication** : la PR reste brouillon, non fusionnée et non publiée. Essais sur iPhone/Android physiques, VoiceOver/TalkBack, Auth/RLS et accès privés, synchronisation réelle et approbation humaine des 13 conditions de lancement restent indispensables. Les pourcentages de maturité des programmes restent basés sur les audits internes.

# SINJIRA™ — V63 : conserver le passage lu après changement de police ou orientation

**11 novembre 2026. Changement candidat, non fusionné, non déployé.**

## Pourquoi une ancre de texte ?

Les versions V52–V62 permettent de glisser à gauche ou à droite et de lire une page PDF source en plusieurs écrans adaptables au téléphone. Après un changement important de taille de police, d'interligne, de largeur ou d'orientation, la V56 restaurait la **même proportion** `scrollTop/maxScroll`. Cette fraction peut pointer vers une autre phrase lorsque les lignes se recomposent.

V63 utilise en priorité **la position en mémoire d'un caractère visible**, puis conserve le ratio existant comme repli si le navigateur ne propose pas d'API caret ou si la page texte a changé.

## Modifications

- Capturer avec `document.caretPositionFromPoint` (Chromium) ou `document.caretRangeFromPoint` (WebKit) un offset dans un nœud texte situé près du haut de la zone de lecture.
- Mesurer le caractère avec un `Range` d'une seule lettre, puis enregistrer **en mémoire seulement** `node`, `offset` et sa position verticale dans le lecteur. Le texte du livre n'est pas copié ni persisté.
- Sur changements de typographie, capturer en phase `document` **avant** la mise en page du moteur historique V26; attendre deux trames, puis replacer le caractère au même niveau vertical.
- Sur rotation/resize, utiliser la dernière ancre visible capturée lors des changements d'écran ou des défilements, si elle est toujours valide.
- Refuser les ancres dont le nœud n'appartient plus à l'article texte (page PDF source remplacée) et retourner au ratio V56 sans erreur.
- Borner la nouvelle position aux limites de défilement. Aucune modification des droits, du PDF, des tables de progression ou des sauvegardes V51/V59.

## Preuves et réception

- Quatre nouveaux tests Node vérifient la capture locale, le repositionnement après reflow, le rejet d'une ancre périmée et la borne de fin de livre.
- Le parcours Playwright ouvre **la véritable page `compte/liseuse.html`** avec un livre synthétique : il relève un offset dans le texte de la page 3, change la police à **34 px**, puis contrôle que le **même caractère** reste pratiquement au même niveau vertical après mise en page.
- Le workflow V63 réexécute également gestes, pagination, sauvegarde/reprise locale et cinq tailles mobiles/tablettes sous **Chromium et WebKit**.
- La CI est exigée **verte sur le dernier SHA** avant de considérer l'amélioration candidate comme validée.

## Limites avant publication

Cette fonctionnalité n'est pas un moteur EPUB à ancrage sémantique permanent : l'ancre disparaît avec le document et n'est **pas synchronisée entre appareils**. Les marque-pages persistants V31/V51 continuent d'utiliser un numéro de page PDF et une proportion de défilement. Les livres privés, les tests réels Safari iPhone / Chrome Android, la sélection et les lecteurs d'écran VoiceOver/TalkBack doivent encore être homologués.

**Ordre de revue :** V63 (cette PR) → [V62 #996](https://github.com/M0rdr3x/BenoitCantin/pull/996) → `main`. Les contrôles d'autorisation V51/V59 [#986](https://github.com/M0rdr3x/BenoitCantin/pull/986) restent séparés. **NO_GO production**, aucun changement au score SINJIRA **66,5 % ±10 points**, **13/13 portes de lancement ouvertes**.

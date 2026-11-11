# SINJIRA™ — V53 : lire par écrans comme dans une liseuse mobile
**Travail candidat du 10 novembre 2026 — PR empilée sur V52 (#961), aucune publication.**

## Besoin et résultat proposé

L'utilisateur veut tourner le livre **avec le doigt** : balayage vers la **gauche = écran de lecture suivant**, vers la **droite = précédent**, notamment sur un téléphone. La V52 ajoutait ces gestes mais tournait toujours directement **une page PDF entière**, même quand son mode texte exigeait un long défilement vertical.

La V53 introduit sur écran étroit une option **« Lire par pages d’écran (texte adaptable) »**, active par défaut, pour parcourir le **texte déjà extrait de la page source** par segments de la hauteur disponible. Quand la dernière portion de cette page a été lue, le même geste fait passer à la page PDF source suivante. Le retour arrière de première portion doit ouvrir **la dernière portion** de la page PDF précédente.

### Fonctionnement et différences

- **Texte adaptable, 320 px → tablette :** le texte continue à se réorganiser selon la largeur, la police, le thème et l'espacement existants; chaque geste horizontal fait avancer/reculer d'environ un écran entier, aligné sur un nombre entier de lignes pour conserver un chevauchement visuel. Le marqueur « Écran X sur Y · page Z du livre » distingue les pages d'écran des pages source.
- **Mode PDF fidèle :** conservation du rendu PDF actuel, du zoom et du défilement horizontal quand la page dépasse la largeur. V52 continue à tourner directement les **pages du document**.
- **Mode continu :** l'utilisateur peut décocher l'option et revenir au défilement vertical naturel. Le changement de préférence ne doit jamais déclencher une modification du droit de lecture.
- **Données de progression :** la liseuse V31 mémorise `scrollTop / (scrollHeight - clientHeight)` par page PDF sous la forme d'un `scroll_ratio`; V53 navigue **au moyen du même scrollTop**, sans nouvelle écriture de contenu ni identifiant. Le `scroll_ratio` est une position **proportionnelle**, pas une ancre sémantique exacte; la lecture au retour peut être légèrement décalée si les métriques de police, la version du document ou l'extraction de texte changent.
- **Compatibilité V51 :** ni le SQL ni le lecteur principal `sinjira-liseuse-v26.js` ne sont modifiés par V53. Les écritures distantes du roman complet restent régies par le moteur en place et par la revue **CAS V51 [#947](https://github.com/M0rdr3x/BenoitCantin/pull/947)**, qui est **DRAFT**. Avant d'approuver le déploiement de V53, la migration V51 et le contrôle des droits [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955) exigent leurs propres recettes.
- **Accessibilité :** grandes commandes tactiles, touches fléchées et PageUp/PageDown, texte DOM sélectionnable, choix du mode continu pour les technologies d'assistance, indication d'écran avec `aria-live`. Le balayage ignore les sélections, les champs interactifs, les gestes diagonaux, les pincements et les mouvements verticaux.
- **Confidentialité :** le seul paramètre supplémentaire enregistré localement est `on/off` pour le mode d'affichage. Aucune copie de roman intégral, citation privée, identité ou URL signée n'est enregistrée par V53.

### Ce qui n'est pas encore un moteur EPUB

Il s'agit d'une **pagination d'affichage du texte issu du PDF**, non de l'import natif EPUB/KEPUB ni d'un découpage sémantique de paragraphes indépendant de la version du roman. Le mode PDF source est conservé pour les illustrations et la fidélité éditoriale. Une éventuelle V54 pourrait ajouter ancres textuelles stables, position par paragraphe, footnotes et gestion avancée de pagination au niveau des chapitres **après** une revue de compatibilité des repères sauvegardés.

## Contrôles automatisés dans la PR V53

- `assets/js/sinjira-liseuse-reflow-v53.mjs` : fonctions pures `measureReaderScreen`, `readerScreenState`, `planReaderScreenTurn`, plus un raccordement DOM au moteur PDF existant.
- `tests/sinjira-liseuse-reflow-v53.test.mjs` : **27 tests** (mouvement, retour, écran final, limites du livre, clavier, sélection, mode PDF, mode continu, sans faux service d'accès).
- Workflow `.github/workflows/sinjira-liseuse-reflow-v53.yml` : contrôle de syntaxe JS, tests V52 et V53, permissions de lecture seules, aucun accès à Supabase ni migration.

Un contrôle supplémentaire empêche de charger deux instances du gestionnaire V52 (même URL versionnée dans l'HTML et l'import V53). Les tests valident la **logique** et des interactions DOM simulées, **pas** l'ergonomie physique ni le rendu sur appareils.

## Porte de réception sur appareils réels — encore ouverte

| Appareil ou situation | Ce qu'il faut recevoir |
| --- | --- |
| iPhone Safari petit/grand, Android Chrome | Les gestes tournent une portion sans sauter de texte ni doubler la page PDF |
| iPad Safari / tablette Android, portrait et paysage | Recalcul de l'écran et maintien approximatif de la position dans la page |
| Police 16–34 px, interligne, mode nuit et clair | Texte lisible; portion finale courte; indicateur d'écran cohérent |
| Première et dernière page source | Boutons/défilements internes utilisables même si le bouton PDF est désactivé |
| Dernier écran → PDF suivant; premier écran → PDF précédent | Le retour s'effectue sur la dernière portion de la page précédente |
| Sélection, surlignage, annotation, recherche, lecture vocale | Aucun geste parasite et aucun contenu privé hors contexte |
| VoiceOver, TalkBack, clavier et lecteur d'écran | Contrôles accessibles, choix de défilement, annonces non envahissantes |
| Déconnexion, reprise et écran verrouillé | Aucun texte privé affiché après changement de compte; progression locale conservée si autorisée |
| Réseau instable et deux appareils | Aucun écrasement de progression par la V53; synchronisation V51 homologuée séparément |
| Tests de cache PWA | Aucun mélange de modules V52/V53 et ancienne API |
| Mémoires faibles et PDF de 520 pages | Temps de rendu, fluidité des gestes et empreinte mémoire acceptables |

**État :** livrable candidat pour revue, essais mobiles et compatibilité V51. Pas de GO production; les **13/13 portes SINJIRA restent ouvertes**, score de maturité **66,5 % ±10 points** inchangé. Issue de suivi [#962](https://github.com/M0rdr3x/BenoitCantin/issues/962).

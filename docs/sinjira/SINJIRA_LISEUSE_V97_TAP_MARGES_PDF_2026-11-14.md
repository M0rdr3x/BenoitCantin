# SINJIRA™ — V97 : tapotements de marges sur les pages PDF et texte paginé

**14 novembre 2026 · PR #1000 (DRAFT) · aucun déploiement ou fusion.**

## Amélioration de la liseuse mobile

La lecture mobile pouvait déjà changer d'écran par balayage gauche/droite et, en texte paginé, en tapotant les marges. La **V97 étend les tapotements aux vraies pages PDF** : marge droite intérieure = page suivante, marge gauche intérieure = page précédente. Le centre reste libre. Les balayages précédents continuent de fonctionner dans les deux modes.

Le classificateur de tapotement, auparavant local à V53, est centralisé dans **V52** (`classifyReaderEdgeTap`) puis réexporté par V53 pour assurer des seuils identiques et préserver les tests existants.

### Conditions strictes

- Les tapotements ne sont reconnus en V52 **que si l'article `#reader-text` était caché au début et reste caché à la fin du contact** (mode PDF effectif). Le défilement texte continu n'acquiert donc aucune nouvelle zone de navigation.
- Bandes intérieures de 7 à 26 % de la largeur du lecteur, en conservant au moins 28 px de marge extérieure côté système. Largeur du lecteur au moins 240 px; coordonnées calculées par rapport au vrai cadre de la liseuse.
- Un seul contact, au plus 300 ms, écart final au plus 12 px horizontal et vertical et déplacement observé au plus 12 px, même si le doigt revient à son point de départ.
- Un appui prolongé, la sélection du texte, un zoom natif/pincement, un changement d'orientation, une zone interactive, une note ou un panneau défilé, un document masqué, la perte du focus ou une suspension excluent le geste.
- Le swipe horizontal existant est évalué **avant** le tapotement; une même interaction ne doit jamais déclencher deux changements PDF.
- Aucun changement aux bases, à l'authentification, aux signaux d'accès, aux droits des livres, à la progression CAS ou au contenu privé.

### Vérification

- `tests/sinjira-liseuse-touch-v52.test.mjs` : cas droit/gauche, centre, bords système, texte continu, long-press, scroll, pincement, sélection, changement de mode pendant un contact et un vrai balayage conservé.
- `tests/sinjira-liseuse-reflow-v53.test.mjs` : contrat V53 réexportant exactement le même classificateur et singleton V52.
- `tests/e2e/test_sinjira_liseuse_mobile_v54.py` : DOM mobile de test, passer en mode PDF, tapoter droite puis milieu puis gauche, vérifier les numéros de pages et l'absence de double navigation, conserver le test du swipe PDF historique.
- Les imports `?v=52.11.14.97` et `?v=53.11.14.97` sont alignés dans le site, les fixtures et les sept imports directs des tests responsives pour éviter les instances multiples.

### Limites

Chromium et WebKit automatisés ne remplacent pas l'homologation sur des téléphones physiques, le test VoiceOver/TalkBack ni la revalidation des droits serveur avec de vrais comptes. Les données de navigation de test sont fictives. La PR reste **NO-GO production**, non fusionnée; 13 conditions globales SINJIRA demeurent ouvertes.

**Scores des programmes de référence au 8 novembre 2026 inchangés** : Nova 47 % (cible conditionnelle 31 décembre 2027), Nova–Sinjira sans pourcentage vérifiable, sondage citoyen 54,5 %, boussole électorale 75 %, SINJIRA complet 66,5 % ±10 points. Aucune date globale certaine de fin.

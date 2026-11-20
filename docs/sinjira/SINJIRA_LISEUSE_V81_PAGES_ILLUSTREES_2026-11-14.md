# SINJIRA™ — V81 : conserver les pages illustrées dans une vraie liseuse mobile

**14 novembre 2026** — correctif dans la [PR unique d'intégration #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), toujours **DRAFT / non publiée**.

## Défaut concret avant V81

Le mode texte adaptable reposait sur l'extraction textuelle PDF. Pour une page sans texte extractible (couverture, carte, illustration, page scannée), `renderPage` montrait seulement une phrase disant d'ouvrir le PDF. Le lecteur ne voyait **pas** la page originale, contrairement à une liseuse réellement utilisable.

## Comportement V81

1. L'utilisateur conserve la préférence **texte adaptable**. Les pages textuelles conservent leur texte reflow, sélectionnable, la pagination par écran, le zoom typographique et les fonctions existantes.
2. Si la page actuelle n'a **aucun texte extrait lisible**, le moteur affiche automatiquement le **canvas de la page PDF**, masque la zone texte vide et quitte la pagination par écran pour cette page seulement. Un court message `role=status` explique cette adaptation sans mettre le roman privé dans les journaux.
3. Un geste **gauche** sur la page illustrée tourne le PDF à la page suivante; si elle contient du texte, le moteur restaure automatiquement la pagination par écrans. Un geste **droite** effectue le chemin inverse.
4. Si l'utilisateur a explicitement choisi le **mode PDF**, il reste en PDF sur toutes les pages, sans imposer de retour en texte.
5. Le moteur vérifie `renderVersion` après le rendu canvas pour ne pas réafficher une version devenue obsolète. Aucun changement de permissions, téléchargement, localStorage roman, API Supabase, RLS ni migration.

## Tests navigateur de la vraie page

Le scénario `tests/e2e/test_sinjira_liseuse_image_fallback_v81.py`, exécuté dans **Chromium et WebKit** par le workflow V69, charge `compte/liseuse.html?edition=demo` et la page PDF fictive n°4 dépourvue de texte :

- page 3 texte -> page 4 illustrée PDF visible, message annoncé et préférence non modifiée;
- swipe gauche -> page 5 texte paginé, message masqué;
- page 4 et swipe droite -> retour à page 3 texte;
- choix PDF explicite -> rester PDF sur les pages 4 puis 5;
- aucune erreur JS, aucun accès externe, aucun compte ou texte privé.

Les autres suites V54–V80 et les vérifications GitHub doivent réussir **sur le SHA V81 exact** avant clôture du correctif. Ce test de livre factice ne remplace pas une vérification avec un ouvrage illustré dont les droits de lecture sont autorisés.

## Conditions de livraison

Recette physique iPhone Safari / Android Chrome (couverture, carte, images et pages scannées), gros caractères, VoiceOver/TalkBack et description alternative des illustrations. Tester également la transition PDF/texte avec un vrai roman sous autorisation serveur, et l'emplacement de lecture synchronisé entre appareils. PR **DRAFT/NO-GO**, **13 portes de lancement ouvertes**; SINJIRA global : **66,5 % ±10 points** estimés, inchangés.

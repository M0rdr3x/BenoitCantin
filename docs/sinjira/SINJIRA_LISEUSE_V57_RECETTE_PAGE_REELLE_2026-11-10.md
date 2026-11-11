# SINJIRA™ — V57 : vérifier la véritable page de lecture mobile

**10 novembre 2026 — contrôle de réception candidat, non publié.**

## Pourquoi une V57 ?

La chaîne V52→V56 a introduit les gestes tactiles, la pagination par écrans, la continuité typographique et la reprise d'emplacement. Les tests navigateurs V54/V56 contrôlaient une page de **simulation** comportant les modules tactiles, mais pas le véritable lecteur `compte/liseuse.html` et son moteur PDF.js.

La V57 ajoute un parcours Playwright qui ouvre **la page HTML réelle du dépôt** dans les moteurs Chromium et WebKit en mode mobile simulé (390 × 844 px), avec les fichiers JS de lecture et d'accessibilité utilisés par l'application.

## Isolement des données et des comptes

- Le serveur HTTP écoute uniquement sur **127.0.0.1** pendant le test.
- Le PDF public de démonstration est remplacé par un faux fichier de test de plus de 1 024 octets.
- Le module PDF.js externe est remplacé par un adaptateur en mémoire qui renvoie **82 pages synthétiques**, exclusivement du texte fictif créé pour le test.
- Le module de compte Supabase est remplacé par un adaptateur qui **lève une erreur à toute tentative d'accès**. Les autres appels externes sont bloqués, sans identité, cookie de compte, roman intégral ni clés d'accès.
- Le lecteur réel traite donc des pages de faux texte au travers de `pdfTextToParagraphs`, de son état `reader-page`, de `changePage`, du mode texte/PDF et des mécanismes réels `persist/restorePage`.

## Parcours proposé

1. Charger `/compte/liseuse.html?edition=demo`, confirmer la page par défaut et le mode « pages d'écran ».
2. Geste gauche/droite entre **portions du texte** de la vraie liseuse, sans passer immédiatement à la page PDF suivante.
3. Parcourir l'intégralité de la page source jusqu'à un **seul changement** de numéro PDF, puis revenir à sa dernière portion.
4. Enregistrer la position de lecture de la démo dans la clé V31 `sinjira:liseuse:demo:la-cendre-du-jugement:spot`.
5. Recharger la vraie page et vérifier la **page PDF** et la **proportion de lecture** retrouvées.
6. Basculer en PDF fidèle et confirmer qu'un geste ne saute **qu'une seule** page source; revenir ensuite au texte adaptable.
7. Échouer en présence d'erreur JS de page ou de communication réseau externe inattendue.

Le test s'ajoute aux **53 tests Node V52–V56** et aux parcours de test synthétiques V54.

## Limites

Cette recette utilise de vrais moteurs navigateur mais **pas** un appareil physique. Le PDF et l'authentification sont volontairement simulés; elle ne certifie ni le rendu réel des 82/520 pages, ni la disponibilité de la distribution intégrale, ni VoiceOver/TalkBack, ni la synchronisation privée V51. En particulier, le test n'est **pas une épreuve des droits** de la fonction `get-novel-file-url`.

La pile de dépendances reste : V57 → V56 #975 → V55 #973 → V54 #968 → V53 #964 → V52 #961 → `main`. Toutes ces PR restent en **DRAFT**. La migration et la sécurité V51 [#947](https://github.com/M0rdr3x/BenoitCantin/pull/947) et [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955) ont leur propre porte de réception.

**Pas de hausse automatique du score SINJIRA (66,5 % ±10 points), ni de fermeture des 13 conditions de lancement.**

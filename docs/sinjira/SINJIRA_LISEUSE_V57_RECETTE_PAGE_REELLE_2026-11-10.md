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

Le test s'ajoute aux **56 tests Node V52–V57** et aux parcours de test synthétiques V54.

## Défaut d'intégration identifié par la recette réelle

La première exécution de la V57 a mis en évidence un vrai défaut que la fixture V54 ne couvrait pas : lors d'un balayage sur une page avec de longs paragraphes, le module V53 avançait correctement d'un écran **mais** `sinjira-liseuse-companion-v28.mjs` disposait encore de son ancien gestionnaire `touchend`, qui tournait systématiquement une **page source PDF**. Le lecteur sautait ainsi du texte malgré la V53.

La pile V57 propose le correctif suivant :
- `sinjira-liseuse-touch-v52.mjs` déclare `data-reader-touch-managed="v52"` sur la zone de lecture, puis le retire au démontage;
- le compagnon V28 ne tourne plus le PDF lorsque V52 détient la gestion tactile, lorsque la présentation est `screens`, ou lorsqu'un événement a déjà été annulé; il conserve seulement un repli pour une ancienne page n'ayant pas chargé V52;
- la V52 n'interprète pas les gestes `screens`, laissant V53 agir seule en lecture paginée;
- les contrôles Node supplémentaires et le scénario V57 sur **l'HTML réel** doivent vérifier qu'un balayage ne change pas le numéro PDF tant qu'il reste du texte à lire.

Ce défaut n'est **pas** une preuve qu'il s'est produit chez un utilisateur en production : les versions V52–V56 n'étaient pas encore déployées. L'échec des premières CI V57 est conservé dans l'historique pour démontrer le défaut et son correctif.

## Limites

Cette recette utilise de vrais moteurs navigateur mais **pas** un appareil physique. Le PDF et l'authentification sont volontairement simulés; elle ne certifie ni le rendu réel des 82/520 pages, ni la disponibilité de la distribution intégrale, ni VoiceOver/TalkBack, ni la synchronisation privée V51. En particulier, le test n'est **pas une épreuve des droits** de la fonction `get-novel-file-url`.

La pile de dépendances reste : V57 → V56 #975 → V55 #973 → V54 #968 → V53 #964 → V52 #961 → `main`. Toutes ces PR restent en **DRAFT**. La migration et la sécurité V51 [#947](https://github.com/M0rdr3x/BenoitCantin/pull/947) et [#955](https://github.com/M0rdr3x/BenoitCantin/issues/955) ont leur propre porte de réception.

**Pas de hausse automatique du score SINJIRA (66,5 % ±10 points), ni de fermeture des 13 conditions de lancement.**

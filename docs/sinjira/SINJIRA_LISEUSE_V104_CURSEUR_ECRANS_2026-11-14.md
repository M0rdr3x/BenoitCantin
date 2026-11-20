# SINJIRA — V104 : navigation tactile directe entre les écrans de texte

**14 novembre 2026 — PR #1000 (ouverte en brouillon), aucun déploiement**

## Objectif

Un même feuillet source PDF peut contenir de nombreux écrans de texte adaptable sur téléphone, notamment avec une grande police. Les versions V97–V103 permettent déjà les balayages du doigt (gauche pour suivant, droite pour précédent) et des commandes de marge, ainsi qu'une position locale conservée. La V104 ajoute un **curseur de progression au sein de la page source**, pour atteindre rapidement un écran plus éloigné, puis revenir sans devoir effectuer des dizaines de gestes.

## Fonctionnement

- Le contrôle **« Aller à l’écran »** apparaît uniquement quand la liseuse est en **mode texte paginé**. Il est masqué pendant la lecture PDF originale, le texte à défilement continu et sur les écrans où la pagination texte n'est pas active.
- Le curseur est borné entre `1` et le nombre réel d'écrans calculés selon la police, l'interligne et la hauteur disponibles. Chaque déplacement sélectionne **un écran de texte de la page PDF courante**.
- La dernière valeur rejoint le **vrai bas du texte**, même lorsque le dernier écran est plus court qu'une ligne, sans inventer un nouvel écran.
- L'accessibilité reste assurée par un `input[type=range]` avec libellé explicite et `aria-valuetext` (« Écran 3 sur 8 · page 4 du livre »). Cible verticale de **44 px** pour l'interaction tactile.
- Les moteurs de balayage gauche/droite (V52/V53), de PDF (V26), de droits et de stockage ne sont pas modifiés. La navigation utilise la même routine `scrollToScreen(...,{userInitiated:true})` que les autres actions de lecture : elle annule toute restauration obsolète et notifie le système existant de progression locale. Aucune nouvelle donnée privée n'est stockée.

## Changements GitHub

- `compte/liseuse.html` : curseur `#reader-screen-jump` dans les préférences d'affichage et aide à la lecture; version du module V53 `53.11.14.104`.
- `assets/js/sinjira-liseuse-reflow-v53.mjs` : compteur actualisé par `sync()`, contrôle du mode actif, navigation vers le pas d'écran calculé, validation stricte des indices, nettoyage des abonnements d'événements.
- `assets/css/sinjira-liseuse-v26.css` : contrôle tactile de 44 px, adaptatif, focus accessible et couleurs cohérentes avec le lecteur.
- `tests/sinjira-liseuse-reflow-v53.test.mjs` : écran 1, navigation aux écrans 3 puis dernier, retour, validation des bornes et absence de changement de page PDF; curseur masqué en PDF et texte continu.
- `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : vrai HTML `compte/liseuse.html?edition=demo`, PDF fictif isolé, passage à l'écran 3 puis retour 1 en restant à la page source 3; vérification du libellé accessible et du masquage en PDF.
- Fixture V54 et tests responsives V58 : imports du module synchronisés.

## Critères de validation et de lancement

Les tests Chromium/WebKit sont exécutés par GitHub Actions sur le SHA exact de la PR. Un résultat de tests « vert » ne constitue pas une homologation physique. La PR reste **NO-GO production** tant que les essais réels iPhone/Android, VoiceOver/TalkBack, les droits d'accès aux ouvrages privés et la synchronisation CAS/RLS inter-appareils ne sont pas clos. Les **13 conditions de lancement SINJIRA** restent ouvertes.

## Avancement des programmes (référence documentaire du 8 novembre 2026)

Projet Nova — programme politique **47 %** (objectif conditionnel du 31 décembre 2027, report 2028+ possible). Nova–Sinjira — 14 services-sectoriels inventoriés, **aucun pourcentage global vérifiable**. Sondage citoyen **54,5 %** (6/11 critères), boussole électorale **75 %** (9/12 critères), SINJIRA complet **66,5 % ±10 points**, 13 conditions ouvertes. Les autres dates de livraison sont indéterminées. Aucun pourcentage global n'augmente mécaniquement suite à cette fonction.

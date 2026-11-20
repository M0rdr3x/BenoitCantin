# SINJIRA — V116 : ne pas tourner une page si le geste change franchement de sens

**15 novembre 2026 — correctif candidat de la PR #1000, non déployé.**

## Constat
La classification de la liseuse utilisait surtout la distance horizontale finale. Une hésitation importante, où le doigt avait déjà balayé dans le sens opposé avant de terminer, pouvait déclencher un passage de page inattendu. Cette situation concerne le PDF, le texte paginé et la souris PDF.

## Correctif
Les moteurs V52 (PDF tactile et souris) et V53 (texte paginé tactile) mémorisent les amplitudes maximales gauche/droite **pendant le contact**. Le classificateur commun refuse la navigation si l'amplitude opposée au sens final atteint le même seuil que le geste de page (56–100 px suivant la largeur). Une petite correction de la trajectoire reste admise. La protection du scroll vertical, de la sélection de texte, des gestes système et du zoom/pinch est préservée.

Les nouveaux champs sont temporaires et ne mémorisent ni livre ni données personnelles. Les URLs JS et tests sont synchronisés : touch `52.11.15.116`, reflow `53.11.15.116`.

## Recettes
Tests Node sur le classificateur, les swipes PDF et le texte paginé, le drag souris, l'inversion dans les deux sens et la possibilité de tourner normalement. Test Playwright Chromium/WebKit sur la vraie page HTML avec roman fictif : inversion gauche/droite sans changement, puis gestes valides à gauche et à droite ramenant à l'écran initial.

**Statut NO-GO :** PR en brouillon, non fusionnée ni publiée. Tests physiques iPhone/Android, VoiceOver/TalkBack, accès privé Auth/RLS, synchronisation entre appareils et approbation des 13 conditions de lancement toujours nécessaires. Les pourcentages globaux des programmes Nova et SINJIRA ne changent pas.

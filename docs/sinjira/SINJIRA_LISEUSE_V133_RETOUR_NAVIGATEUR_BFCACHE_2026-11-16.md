# SINJIRA V133 — reprendre sa lecture après Retour du navigateur

**16 novembre 2026 — développement candidat dans PR #1000, DRAFT et non déployé.**

## Problème visé
Les navigateurs iOS et Android peuvent restaurer le roman depuis le cache de retour/avance (BFCache). Une autre hauteur de viewport peut être restaurée sans événement `resize` ; la position lue dans le texte paginé peut se retrouver décalée. Le nouveau lecteur doit aussi refuser de terminer un ancien toucher lorsque la page redevient active.

## Changement ciblé
- **V53 / texte paginé** : sur `pageshow.persisted === true`, invalider le contact en cours, vérifier que le roman est visible/autorisé, puis reprendre la restauration d'ancre/ratio déjà appliquée aux changements de taille. Aucun déplacement du texte sur un pageshow ordinaire.
- **V52 / PDF** : annuler les contacts et drags périmés au retour BFCache sans bloquer les nouveaux gestes gauche/droite.
- Écouteurs libérés au démontage. Aucune nouvelle persistance, aucun accès au livre privé, aucune modification Auth/RLS, aucun déploiement.
- Versions cohérentes : **V52 52.11.16.133** et **V53 53.11.16.133** dans HTML, fixture et tests.

## Preuves demandées
- Node V52 : `pageshow.persisted=false` préserve le geste normal; `true` empêche la page fantôme.
- Node V53 : ratio 0,5 conservé quand la hauteur paginée varie; geste ancien annulé, nouveaux balayages gauche/droite admis.
- Playwright Chromium/WebKit sur livre fictif : événement `pageshow.persisted` synthétique pendant le toucher, aucune page fantôme.
- Résultat GitHub Actions sur **le commit exact** requis avant de déclarer les tests réussis. Le BFCache natif et la navigation iPhone réelle nécessitent une réception physique.

**NO-GO production** : PR #1000 toujours DRAFT, essais matériels, VoiceOver/TalkBack, droits des livres intégrals, révocation serveur et synchronisation entre appareils à homologuer. Les indicateurs Nova/SINJIRA ne changent pas automatiquement.

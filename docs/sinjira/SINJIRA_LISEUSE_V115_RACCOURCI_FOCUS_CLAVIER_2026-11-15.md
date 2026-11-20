# SINJIRA — V115 : aller au roman ET pouvoir tourner ses écrans au clavier

**15 novembre 2026, heure du Québec** — PR #1000 non fusionnée, changement de revue seulement.

## Problème

Le raccourci mobile V110/V112 « Aller directement au livre » renvoyait vers le fragment `#reader-viewer`, mais n'affectait pas explicitement le focus clavier de cette zone. Le navigateur pouvait conserver le focus sur le lien de la barre latérale ; les raccourcis `ArrowRight/ArrowLeft/PageDown/PageUp` de V53 n'agissent délibérément **que lorsque le lecteur est focalisé**. Une personne qui active ce lien peut alors voir son livre sans pouvoir passer d'écran au clavier.

## Correction

La fonction `bindReaderQuickAccess` reçoit également `viewer` et, sur activation volontaire du lien, appelle `viewer.focus({preventScroll:true})` sans annuler la navigation native par fragment, les règles de capture de touches ou les gestes tactiles. Un clic synthétique sur un lien caché ou une édition suspendue ne reçoit aucun focus et sa navigation est annulée. L'observateur V112 continue de refléter la seule décision de visibilité du moteur V26. Le nouvel écouteur est retiré lors du nettoyage de la fonction.

Aucun changement au PDF, au texte privé, au compte, aux autorisations serveur/RLS, à la progression, aux droits d'achat ou à la synchronisation. La ressource JS V53 est cache-bustée sous `53.11.14.115` dans la page et la fixture.

## Tests ajoutés

- Node : lien interdit durant suspension, focus explicite après ouverture, conservation de l'ancre native, reblocage sur fermeture, second accès autorisé, nettoyage de l'événement et de l'observateur.
- Playwright (vraie page HTML avec PDF fictif, Chromium et WebKit) : clic réel du lien mobile, fragment `#reader-viewer`, focus sur la zone de roman, flèche droite pour avancer à l'écran suivant, flèche gauche pour revenir à l'écran initial sans changement de page PDF.

**NO-GO publication :** version candidate dans PR DRAFT, pas de fusion ni de déploiement. Les essais sur iPhone Safari / Android Chrome physiques, VoiceOver/TalkBack, protections des livres privés et synchronisation entre appareils restent à homologuer. Les pourcentages des programmes demeurent ceux des audits de référence.

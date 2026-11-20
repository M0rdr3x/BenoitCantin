# SINJIRA™ — V65 : gestes tactiles transmis par Chromium sur la vraie liseuse

**11 novembre 2026 — campagne de réception candidate, non publiée.**

## Objectif et distinction des preuves

Les PR V52–V64 apportent le geste gauche/droite, la pagination par écrans adaptés au téléphone, les marges, la continuité de la position, l'accessibilité au clavier et les contrôles de l'HTML réel. Les tests V54 et V57 fabriquaient toutefois un événement JavaScript `Event('touchend')` doté de propriétés `TouchLike`. Cela vérifie la **logique du gestionnaire d'événements**, mais **pas complètement le chemin du moteur de navigateur lorsque l'utilisateur balaye l'écran**.

V65 ajoute une épreuve mobile supplémentaire avec `Input.dispatchTouchEvent` du **Chrome DevTools Protocol (CDP)**. Chromium crée lui-même la séquence touchstart → touchmove → touchend, avec `event.isTrusted === true`. Le scénario est exécuté sur **la véritable page `compte/liseuse.html`**, non uniquement sur la fixture V54.

## Scénarios V65

- Sur 390×844 px, geste gauche : l'écran de texte avance **sans changer de page PDF source**.
- Geste droite : la lecture revient au premier écran.
- Geste vertical : le navigateur peut défiler naturellement, mais **ne change pas de page PDF**.
- Sur 320×568 px, un geste horizontal peut encore avancer d'un écran sans perdre de contenu.
- En mode défilement libre et sans débordement horizontal, le geste gauche tourne **une seule page PDF**, sans double commande du compagnon historique V28.
- Le test refuse des événements `touchstart`/`touchend` non fiables, signale les exceptions JavaScript, bloque les ressources externes et **interdit tout accès aux comptes**.

La CI ajoute cette épreuve au corpus des **68 tests Node** déjà exécutés dans V64. Le faux PDF et le texte synthétique du laboratoire V57 restent utilisés; aucune copie d'un roman ni d'un jeton privé n'est chargée.

## Pourquoi cela ne remplace pas un téléphone réel

Un événement émis par CDP est **créé par Chromium, et non par un véritable doigt ni un écran tactile physique**. Il augmente la confiance dans l'intégration navigateur Android/Chrome, mais **ne certifie pas** Safari iOS, l'accélération du défilement sur téléphone, les gestes du système, le retour navigateur, le zoom à deux doigts, les dispositifs d'assistance, l'autonomie, les livres complets ni les performances sur appareils anciens.

WebKit continue d'être couvert par les tests de moteur simulé V64; V65 **ne prétend pas offrir une injection native équivalente dans WebKit**.

## Contexte de publication

L'intégration principale [V64 #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000) reste **DRAFT**, non fusionnée et non déployée. La V65 s'empile sur V64 pour renforcer la réception avant revue. La sécurité des livres et de leurs marque-pages demeure distincte dans [V59 #986](https://github.com/M0rdr3x/BenoitCantin/pull/986), sans migration autorisée. Pour un éventuel GO, vérifier de vrais téléphones, l'accessibilité VoiceOver/TalkBack, le contenu intégral, les autorisations, les caches PWA et la synchronisation réelle.

Aucun changement des taux d'achèvement certifiés : Projet Nova **47 %** (objectif de fin 2027 conditionnel), Nova–Sinjira **non mesurable globalement**, boussole **75 %**, sondage **54,5 %** et SINJIRA **66,5 % ±10 points, 13 conditions de lancement ouvertes**. Source : [bilan des quatre programmes dans `main`](https://github.com/M0rdr3x/BenoitCantin/blob/main/docs/AVANCEMENT_QUATRE_PROGRAMMES_2026-11-10.md).

# SINJIRA — V103 : description accessible de la zone de lecture

**14 novembre 2026 · PR #1000 ouverte en brouillon · NO-GO production**

## Objectif

Les versions V97–V102 proposent la lecture par pages d'écran, les gestes gauche/droite, les marges tactiles, le PDF et un repère visuel compact sur mobile. La navigation est déjà exploitable au clavier et les commandes comportent des libellés accessibles. La V103 complète ces libellés : **la zone du livre elle-même annonce son mode et l'emplacement lorsque l'utilisateur y place le focus**.

Dans un lecteur d'écran, le point d'entrée de lecture peut maintenant avoir un nom explicite :

- **Texte paginé :** « Lecture du roman, texte adapté : écran 2 sur 8, page 3 sur 82. »
- **PDF :** « Lecture du roman en PDF : page 3 sur 82. Pour une lecture accessible, choisissez le texte adaptable. »
- **Texte continu :** « Lecture du roman, texte adaptable en défilement continu : page 3 sur 82. »

Le compteur mobile V102 reste visible et `aria-hidden=true`. Les annonces `aria-live` existantes (V28 pour la progression de page et V53 pour les écrans) restent inchangées pour **éviter les annonces redondantes**. La région du livre possède `role=region`, `tabindex=0` et un `aria-label` actualisé à chaque modification du mode, de la page ou de l'écran affiché. Les raccourcis du clavier et l'aide `aria-describedby` sont conservés.

## Portée technique

- `assets/js/sinjira-liseuse-reflow-v53.mjs` : fonction pure `formatReaderAccessibleLocation`, contrôle du `aria-label` existant à chaque `sync()`, et mutualisation du calcul d'écran V102. Aucun appel réseau, identifiant de lecteur ou texte de roman.
- `compte/liseuse.html` : `role="region"` et chargement rafraîchi V53 `53.11.14.103`.
- `tests/sinjira-liseuse-reflow-v53.test.mjs` : cas de texte paginé, PDF, texte continu, bornes invalides, synchronisation après un swipe et changement de page ou de mode.
- `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : vérification sur le vrai lecteur HTML et un **PDF fictif de démonstration**, dans Chromium et WebKit isolés; contrôle du libellé à l'écran 1 puis à l'écran 2, en PDF pages 3 et 4, et absence de texte du roman dans le libellé.
- Import V53 `53.11.14.103` synchronisé dans le HTML et les fixtures de tests.

## Condition de validation

Ne qualifier V103 de validée que lorsque les workflows applicables à **son commit HEAD exact** sont terminés sans échec. Les tests automatisés d'attributs ARIA et la simulation de navigateur ne constituent **pas une homologation VoiceOver/TalkBack sur de véritables appareils**.

## Limites et suivi

La PR #1000 reste en brouillon, non fusionnée et non déployée. Les tests physiques iOS/Android, VoiceOver/TalkBack, les droits d'accès aux romans privés et la synchronisation sûre entre appareils (CAS/RLS) restent hors de portée de ce correctif. Les 13 conditions de lancement SINJIRA sont encore ouvertes, donc **NO-GO production**.

## Pourcentages globaux inchangés — référence du 8 novembre 2026

- **Nova — programme politique : 47 %** ; objectif du **31 décembre 2027 conditionnel**, report 2028+ possible.
- **Nova–Sinjira — services publics : non calculable** ; 14 secteurs recensés, coûts et données encore non validés.
- **Sondage citoyen : 54,5 %**, soit 6/11 critères ; collecte non ouverte.
- **Boussole électorale : 75 %**, soit 9/12 critères.
- **SINJIRA complet : 66,5 % ±10 points** ; 13 conditions de lancement ouvertes, date de fin inconnue.

Les mesures documentaires ne sont pas recalculées automatiquement lorsqu'un nouveau correctif de liseuse est intégré.

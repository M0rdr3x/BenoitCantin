# SINJIRA — V105 : cohérence du curseur de navigation sur téléphone

**14 novembre 2026 · PR #1000 en brouillon · NO-GO production.**

## Constat

La V104 introduit `Aller à l’écran` pour naviguer rapidement dans les longues pages de texte adaptable. Lorsqu'on passe en mode **PDF** ou en **texte continu**, la V104 cache l'élément `input[type=range]`, mais laisse son **élément parent `label`** visible. Ce texte sans commande est trompeur, particulièrement sur les petits écrans. De plus, les pages qui tiennent entièrement dans un écran affichaient un curseur inutile.

## Correction V105

- Le libellé du curseur possède maintenant un identifiant explicite `#reader-screen-jump-label`, et est initialement masqué dans le HTML.
- Le moteur `assets/js/sinjira-liseuse-reflow-v53.mjs` synchronise ensemble la visibilité **du curseur et de son libellé** ; ils apparaissent seulement si le texte est en mode **pages d'écran**, sur une largeur mobile/tablette prise en charge, et que la page source demande **plus d'un écran**.
- Quand la page redevient longue (reflow après changement de police, chargement ou orientation), les deux contrôles reviennent. La valeur maximale reste calculée à partir du contenu réel.
- Un événement `input` résiduel sur un curseur caché pendant une page d'un seul écran ne provoque pas de navigation.
- Tous les mouvements gauche/droite, tapotements de marges, navigation PDF, libellés ARIA, coordonnées de lecture et sauvegarde locale existante sont conservés. Aucun nouveau stockage ni transfert de données.

## Tests et réception

- `tests/sinjira-liseuse-reflow-v53.test.mjs` : contrôle du curseur ET du parent à quatre étapes (texte paginé, PDF, continu, retour), raccourcissement à un écran, impossibilité d'avancer par un curseur caché, retour de la commande si la page grandit.
- `tests/e2e/test_sinjira_liseuse_real_page_v57.py` : vérification du libellé visible sur vraie page HTML avec livre fictif en texte paginé, puis masqué en PDF, sur Chromium et WebKit isolés.
- `compte/liseuse.html`, fixture V54 et tests responsive V58 : import du module V53 synchronisé à `53.11.14.105`. Le cache charge la correction sur la vraie page.
- Les workflows applicables doivent tous réussir sur le SHA HEAD exact avant toute déclaration de validation.

## Homologation non réalisée

Ce correctif n'est pas une homologation sur iPhone/Android physiques ni VoiceOver/TalkBack. Il ne prouve pas les droits RLS/CAS des romans privés ou la synchronisation inter-appareils. La **PR reste DRAFT**, ni fusionnée ni déployée, et **les 13 conditions de lancement SINJIRA restent ouvertes**.

## Bilan global inchangé, référence du 8 novembre 2026

| Programme | Avancement documenté | Fin |
|---|---|---|
| Projet Nova politique | **47 %** | **31 décembre 2027**, cible conditionnelle et report en 2028+ possible |
| Projet Nova–Sinjira services publics | **Pas de % global vérifiable**, 14 secteurs | Indéterminée |
| Projet Nova sondage citoyen | **54,5 %** (6/11 critères) | Indéterminée |
| Projet Nova boussole électorale | **75 %** (9/12 critères) | Indéterminée |
| SINJIRA plateforme complète | **66,5 % ±10 points**, 13 conditions ouvertes | Indéterminée |

Les correctifs d'interface ne justifient pas à eux seuls une hausse de ces pourcentages.

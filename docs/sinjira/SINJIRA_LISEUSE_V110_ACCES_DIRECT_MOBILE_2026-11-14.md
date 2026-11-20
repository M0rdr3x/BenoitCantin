# SINJIRA — V110 : arriver directement au livre sur téléphone

**14 novembre 2026 (heure du Québec)** — correctif de la branche d'intégration PR #1000, **NO-GO production**.

## Défaut d'ergonomie

Deux panneaux de personnalisation et de synthèse vocale possédaient l'attribut HTML `open`, sur mobile également. Avant même d'accéder au roman, le lecteur devait faire défiler deux formulaires déroulés, gênant l'expérience de type liseuse.

## Changement non destructif

- Les deux panneaux sont désormais **fermés initialement dans le HTML**. Un appareil mobile de largeur ≤980 px arrive sur un volet de réglages compact, sans attendre le chargement JavaScript ; la personne peut ouvrir chaque `<summary>` avec le doigt ou le clavier.
- Un lien « Aller directement au livre ↓ » est visible au-dessus des réglages **sur mobile et tablette**, avec une cible de 48 px et un contraste/focus explicite. Il vise la vraie zone `#reader-viewer` déjà accessible au clavier.
- Sur ordinateur (>980 px), le module V53 ouvre les deux panneaux au chargement comme auparavant et masque le raccourci mobile. La fonction ne s'exécute qu'à l'initialisation : elle ne referme pas des réglages ouverts volontairement et ne surveille pas les changements de largeur.
- Navigation gauche/droite, mode PDF, texte reformaté, accessibilité, sauvegarde et sécurité ne sont pas modifiés.

## Contrôles

- Test Node du DOM de base, du CSS et du comportement téléphone/ordinateur, y compris ouverture volontaire.
- Playwright Chromium et WebKit sur la **vraie page HTML**, sans données privées : panneaux fermés sur 390 px, lien visible et hauteur ≥44 px, clic vers le livre, ouverture manuelle du premier panneau, recharge à 1280 px et ouverture des deux panneaux.
- Cache CSS et JS V53 alignés sur `53.11.14.110` dans les ressources et les contrats existants.

**Limites** : validation réelle sur iPhone et Android, VoiceOver/TalkBack, droits de romans intégraux, RLS, synchronisation multi-appareils et autorisation humaine restent à obtenir ; la PR reste DRAFT. Aucune mise en production, migration, ouverture de sondage ou modification des pourcentages globaux.

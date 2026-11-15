# SINJIRA — V111 : réglages lisibles lors du passage ordinateur → mobile

**14 novembre 2026 au Québec** — amélioration candidate de la PR #1000, **non publiée**.

## Constat

V110 repliait les réglages sur un chargement mobile et les ouvrait sur ordinateur. Mais lorsque le viewport franchissait le seuil tablette de **980 pixels** sans rechargement, ces panneaux pouvaient garder l'état automatique du bureau, obligeant à faire défiler les réglages au lieu du roman.

## Correction

Le nouveau `bindReaderResponsivePanels` écoute uniquement les changements du `matchMedia('(max-width: 980px)')`. Il ouvre les panneaux **automatiques** en format ordinateur et les replie en format mobile/tablette. Dès qu'une personne active le `summary` d'un panneau avec la souris, le doigt ou le clavier (événement natif `click`), ce panneau passe sous son contrôle exclusif : ni rotation ni redimensionnement ne le referme ou le rouvre.

À aucun moment le moteur ne modifie le roman, la position de lecture, les droits privés, le stockage ou les synchronisations. L'abonnement peut être retiré proprement.

## Vérifications

- Test Node : passages successifs 1280 → 820 → 1280 → 390 px, ouverture puis fermeture manuelles et retrait des écouteurs.
- E2E sur la **vraie page** avec roman synthétique : changements de viewport et de mode PC/tablette, conservation du livre et du choix explicite de l'utilisateur. Ces parcours sont exécutés par les workflows Chromium/WebKit habituels.
- Version cache V53 du HTML, de la fixture et des tests : `53.11.14.111`.

**Release : NO-GO**. Tests physiques Safari iPhone / Chrome Android, VoiceOver/TalkBack, accès aux romans intégraux autorisés, synchronisation réelle entre appareils, sécurité et approbation humaine restent obligatoires. Les quatre pourcentages de programme et la non-mesurabilité des 14 secteurs ne changent pas.

## Réparation du scénario d'homologation V111

La première tentative CI V111 a révélé une erreur dans le **test**, pas un défaut confirmé du lecteur : le test V110 ouvrait puis refermait manuellement les paramètres avant de demander au test V111 qu'un redimensionnement les rouvre automatiquement, ce qui violait la priorité donnée à l'utilisateur. Le test a été précisé : il vérifie d'abord que la fermeture manuelle survit au passage sur ordinateur, recharge la page pour retrouver des panneaux non modifiés par l'utilisateur, puis vérifie les transitions automatiques ordinateur → tablette et la priorité aux ouvertures manuelles. Les suites du commit corrigé doivent être revalidées séparément.

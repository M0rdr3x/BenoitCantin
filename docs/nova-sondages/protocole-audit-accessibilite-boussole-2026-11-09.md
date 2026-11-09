# NOVA — Protocole d'audit indépendant d'accessibilité de la boussole

**Préparé le 9 novembre 2026 — document de travail, aucun audit indépendant encore effectué.**  
**Périmètre :** [Boussole électorale Nova](https://www.benoitcantin.com/projets/projet-nova/boussole-electorale.html), questionnaire de 64 propositions, 16 dimensions, profil partiel, résultat, partage facultatif et explorateur des sources.  
**Critère du registre :** `COMPASS_ACCESSIBILITY` reste **PENDING**; la boussole demeure **9/12 critères de réception réussis (75 % de couverture)** selon `docs/nova-sondages/reception-sondage-boussole-2026-11-08.json`.  
**Interdit :** aucune activation du sondage, aucun envoi de votes, aucune préférence politique transmise, aucune approbation de comparaison entre partis.

## 1. Référentiel de test et limites

Référentiel de contrôle proposé : [WCAG 2.2 du W3C](https://www.w3.org/TR/WCAG22/), **niveau AA comme cible d'examen**. Cette cible technique n'est **pas** une déclaration de conformité juridique ou de certification. Les niveaux doivent être respectés tels que publiés : notamment **2.4.11 Focus Not Obscured (Minimum) est AA**, **2.4.12 Focus Not Obscured (Enhanced) est AAA**, et **2.4.13 Focus Appearance est AAA**; ces deux derniers sont des recommandations additionnelles et ne doivent pas être annoncés comme des exigences AA. Les essais manuels sont nécessaires en complément de l'automatisation.

Le changement en PR #917 améliore les contours de focus et ajoute un essai de visibilité géométrique des éléments focalisés. **Un élément visible dans le rectangle de la fenêtre peut encore être couvert par une bannière ou un panneau flottant.** Le test géométrique ne prouve donc pas à lui seul 2.4.11 ni l'ensemble du niveau AA.

## 2. Matrice d'examen humain à exécuter

| ID | Référence WCAG 2.2 | Scénario reproductible et critère d'acceptation | État |
|---|---|---|---|
| A01 | 2.1.1 Clavier (A), 2.1.2 Pas de piège au clavier (A) | Depuis la barre d'adresse, parcourir les 64 questions à Tab/Maj+Tab, Espace, Entrée et flèches; pouvoir revenir, finir et quitter chaque zone sans souris ni piège | **À examiner** |
| A02 | 2.4.3 Ordre du focus (A) | À Q01, Q02, Q64, après « Profil actuel » et « Recommencer », ordre logique ; le focus ne disparaît pas derrière la page | **À examiner** |
| A03 | 2.4.7 Focus visible (AA), 2.4.11 Focus non masqué (AA) | Tracer tous les contrôles : réponse, importance, précédent, suivant, aperçu, partage et recommencer; aucun focus entièrement masqué par bandeau, barre collante ou dialogue | **À examiner** |
| A04 | 1.4.11 Contraste non textuel (AA), 1.4.3 Contraste minimum (AA) | Mesurer avec outil référencé les contrastes de texte, labels, options non sélectionnées, cercles et indicateurs de focus en normal et en contraste forcé | **À mesurer** |
| A05 | 1.4.10 Redistribution (AA), 1.4.4 Redimensionnement du texte (AA) | À largeur équivalente à 320 px CSS et zoom 200 % puis 400 % selon le cas, tous les contenus et commandes restent accessibles sans perte de fonction | **À examiner** |
| A06 | 1.3.1 Information et relations (A), 4.1.2 Nom/rôle/valeur (A) | Vérifier fieldset/legend, groupes radio, labels de sélecteur, états de commandes, progression 1/64…64/64 et description du résultat par technologie d'assistance | **À examiner** |
| A07 | 4.1.3 Messages d'état (AA) | Le statut « Réponse enregistrée localement », erreurs de chargement et résultats partiels sont annoncés de manière appropriée, sans interruption ou répétition excessive | **À examiner** |
| A08 | 2.2.2 Mettre en pause, arrêter, masquer (A), 2.3.3 Animation issue des interactions (AAA facultatif) | Avec « Réduire les animations » activé, contrôler transitions et effets non nécessaires; documenter séparément toute amélioration AAA | **À examiner** |
| A09 | 2.5.8 Taille de cible minimale (AA) | Inspecter les zones tactiles des réponses, du sélecteur et des boutons en mobile réel; appliquer les exceptions normatives si elles sont pertinentes | **À examiner** |
| A10 | 3.3.2 Étiquettes ou instructions (A), 3.3.1 Identification des erreurs (A) | Vérifier les instructions, « Sans opinion », chargement impossible, sélection incomplète et saisie facultative du destinataire du courriel | **À examiner** |
| A11 | 1.1.1 Contenu non textuel (A) | La carte à 16 dimensions et les éventuels SVG ont une alternative intelligible : les chiffres, pôles et couvertures sont présents en texte, indépendamment des couleurs et marqueurs | **À examiner** |
| A12 | 3.2.2 À la saisie (A), 3.2.4 Identification cohérente (AA) | Changer un poids ou une réponse ne provoque pas une navigation inattendue; Retour, Profil, Recommencer et Partage ont des noms et comportements cohérents | **À examiner** |

**Ce tableau est un plan d'essais, pas une liste de critères déjà passés.** Les critères non applicables doivent être explicitement motivés dans le procès-verbal, jamais assimilés d'office à des réussites.

## 3. Matrice de plateformes et niveaux de preuve

| Environnement | Composants | Type de preuve attendue | État |
| --- | --- | --- | --- |
| Windows + Firefox/Chrome + NVDA (versions consignées) | Clavier, annonces de statut, radios, progression, carte textuelle | Rapport de session humaine, anomalies et versions | **À planifier** |
| macOS + Safari + VoiceOver | Clavier, focus, contrôles et partage | Rapport de session humaine, captures des défauts sans réponses personnelles | **À planifier** |
| iPhone physique + Safari + VoiceOver | Navigation tactile, zoom et lisibilité | Modèle, iOS, Safari, configuration et résultats | **À planifier** |
| Android physique + Chrome + TalkBack | Navigation, labels, états et indicateurs de progression | Modèle, Android, version, résultat, risques | **À planifier** |
| Contraste forcé et zoom fort | Contraste, reflow, focus non masqué | Mesures et parcours documentés | **À planifier** |

Les simulations de mobile Playwright existantes **ne remplacent pas** des tests sur appareils physiques. Les tests E2E de la PR #917 sont exécutés en environnement isolé avec **requêtes d'écriture HTTP bloquées** et servent à détecter des régressions, pas à homologuer la production.

## 4. Pièces à joindre avant toute promotion de PENDING à PASSED

Un dossier de réception indépendante doit inclure :
1. **Mandat du réviseur** et déclaration documentée de son indépendance; préciser la qualification, la portée et les conflits éventuels.
2. **URL et identifiant de version réellement évalués**, code déployé, date et heure locale, navigateurs et technologies d'assistance exacts.
3. **Rapport pour les 12 cas A01–A12** : PASS, FAIL, NOT_APPLICABLE avec justification, sévérité, preuve, reproduction et correctifs attribués; les observations personnelles ne doivent pas conserver d'opinion ou profil politique.
4. **Nouvelle exécution après correctif** sur l'artefact public réellement mis en ligne; comparer à la source autorisée et consigner le cas échéant la gestion du cache.
5. **Avis indépendant final et décision d'acceptation** : seuls les responsables habilités révisent `COMPASS_ACCESSIBILITY`; la présence d'un document ou une CI verte ne suffit pas.

**Champs de réception non renseignés à ce jour :** responsable mandaté = inconnu; versions d'appareil physiques = inconnues; rapport humain = absent; décision de certification = absente; date de fin = inconnue.

## 5. Interactions avec les deux autres critères de la boussole

- `COMPASS_CROSS_BROWSER` : les moteurs locaux Chromium/Firefox/WebKit sont testés; restent les appareils réels et le contrôle de la version/cache en production.
- `COMPASS_DOCUMENTARY_VALIDATION` : les sources primaires des positions des partis et la seconde relecture factuelle indépendante demeurent à documenter **de manière égale**, sans inventer de soutien partisan.

Le **sondage citoyen** demeure fermé (`published:false`) et soumis à ses cinq critères encore en attente, dont confidentialité, anti-rejeu et autorisation juridique. Le présent protocole ne les satisfait pas.

**Conclusion :** procédure de revue indépendante rendue explicite. **Score de réception boussole 9/12 inchangé**, **Projet Nova 47/100 inchangé**, aucune homologation ni activation automatique.

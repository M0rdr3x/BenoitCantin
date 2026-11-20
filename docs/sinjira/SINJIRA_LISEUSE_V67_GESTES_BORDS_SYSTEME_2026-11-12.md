# SINJIRA™ V67 — Préserver le retour du système depuis les bords du téléphone

**12 novembre 2026 — correctif candidat de confort et d'accessibilité, non déployé.**

## Problème

Les gestes gauche/droite du lecteur SINJIRA permettent de changer d'écran de texte (V53) ou de page PDF source (V52). Or, sur les téléphones, certains gestes initiés **au bord même de l'écran** peuvent être réservés à la navigation du navigateur ou du système (retour, transition entre pages). Un gestionnaire de livre trop agressif peut interpréter ce geste comme « page précédente » ou « page suivante » et provoquer un changement de livre inattendu.

## Comportement retenu

- Un toucher qui **commence dans les 24 premiers ou derniers pixels CSS du viewport** n'est pas revendiqué comme geste de navigation par la liseuse.
- Le geste est traité normalement lorsqu'il commence **dans l'intérieur de l'écran**; les seuils, directions et protections de trajectoire V66 restent identiques.
- Le calcul utilise `window.innerWidth`, la largeur courante du viewport; il suit donc les changements portrait/paysage sans valeur enregistrée.
- Si la largeur du viewport est absente ou invalide, l'exclusion de bord n'agit pas : les gestes demeurent compatibles avec les anciens navigateurs et les tests en laboratoire.
- Les commandes accessibles « précédent » et « suivant » continuent de fonctionner partout. Aucune règle ne bloque les boutons, la navigation clavier, la sélection de texte ou le mode PDF.
- **Aucune donnée de position du doigt n'est enregistrée ni transmise.** Le contrôle s'effectue pendant la session seulement.

## Tests

- Trois tests Node V52 supplémentaires : limites gauche/droite à 24 px, valeurs invalides et balayages centraux inchangés.
- Deux tests Node V53 supplémentaires : en mode texte, ignorer les amorces de bord; suivre les nouvelles dimensions après rotation.
- Le parcours Playwright de la vraie page HTML V66 est étendu : à 390×844 et 320×568, les gestes des deux bords ne changent pas de page en mode texte; ils ne changent pas non plus de page PDF en mode libre, alors que les gestes centraux fonctionnent.
- La CI V67 reprend également les parcours V54, V57, V58 et les événements tactiles de moteur Chromium V65.

Les tests de navigateur peuvent confirmer que le lecteur **n'intercepte pas** les gestes de bord dans des scénarios déterminés. Ils ne prouvent **pas** que Safari iOS exécutera le geste « retour » de la même façon qu'un véritable iPhone : une réception physique reste nécessaire.

## État et dépendances

La V67 est empilée sur la [PR d'intégration de liseuse #1000](https://github.com/M0rdr3x/BenoitCantin/pull/1000), toujours en brouillon et non fusionnée dans `main`. Les vérifications de droits et de progression synchronisée [V59 #986](https://github.com/M0rdr3x/BenoitCantin/pull/986) sont un chantier distinct. Aucune modification SQL, aucune clé, aucun PDF de roman intégral ni aucune mutation de compte n'est nécessaire ici.

**NO_GO production** en attendant la réception sur iPhone Safari, Android Chrome, VoiceOver/TalkBack, les PDF intégraux autorisés, la sécurité des accès et les tests multiappareils.

La maturité auditée au **8 novembre 2026** reste : Projet Nova **47 %** (objectif de fin 2027 conditionnel), Nova–Sinjira **pas de pourcentage global calculable**, boussole **75 %**, sondage **54,5 %** et SINJIRA **66,5 % ±10 points** avec **13 portes de lancement ouvertes**. Le présent correctif ne constitue pas une nouvelle évaluation globale.
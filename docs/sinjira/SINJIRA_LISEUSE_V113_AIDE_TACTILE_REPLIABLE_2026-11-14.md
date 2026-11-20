# SINJIRA — V113 : gestes accessibles sans écran d'instructions envahissant

**14 novembre 2026 (heure du Québec)** — ajout proposé à la demande d'intégration GitHub #1000, **NO-GO publication**.

## Problème traité

Après l'écran de lecture, la version mobile affichait en permanence un paragraphe très long de consignes. Ce contenu repoussait les autres informations, allongeait inutilement la page du téléphone et masquait le principe simple « gauche pour avancer, droite pour reculer ».

## Changement

Le texte explicatif est maintenant dans un élément HTML natif `<details>`, **fermé initialement**. Son `<summary id="reader-swipe-help">` annonce les deux gestes principaux en français. L'utilisateur peut ouvrir et refermer les consignes complètes en touchant le résumé ou avec Entrée au clavier. L'identifiant `reader-swipe-help` reste la cible du `aria-describedby` de la zone de lecture, qui fournit dès l'entrée un rappel court des gestes. La surface minimale du résumé atteint **44 px** et dispose d'un focus visible ; les consignes longues, intactes, sont disponibles sur demande.

Le guide est affiché seulement au format mobile défini par les styles existants (≤760 px). Aucune logique de navigation, d'autorisations, d'identité, de roman privé, de sauvegarde ou de synchronisation n'est modifiée.

## Vérifications

- Test Node : contrat HTML `details/summary`, fermeture initiale, libellé de gestes, maintien du texte explicatif et du lien `aria-describedby`, styles de focus et taille.
- Playwright sur la **vraie page avec PDF synthétique**, Chromium et WebKit : guide présent, texte long masqué initialement, ouverture au doigt, fermeture au clavier et page source du roman inchangée.
- Version du CSS incrémentée à `53.11.14.113` dans le HTML pour éviter l'ancien cache.

## Réserves de déploiement

Les suites GitHub ne prouvent pas l'expérience sur un iPhone/Android réel ni la compatibilité VoiceOver/TalkBack. La PR reste en brouillon : droits d'accès privés, Auth/RLS, synchronisation multi-appareils, homologation des 13 conditions de lancement et accord humain toujours requis. Aucune mise en ligne ni modification des pourcentages des programmes.

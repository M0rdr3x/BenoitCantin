# SINJIRA V123 — détecter une bascule transitoire de lecture pendant un swipe

**15 novembre 2026** — correctif candidat PR #1000, non fusionné et non déployé.

## Risque résiduel après V122

V122 invalide le toucher lorsque le mode final (PDF/texte) ne correspond plus au mode d'origine. Mais une séquence PDF → texte → PDF **entre deux événements tactiles** conserve la même représentation et le même numéro de page à `touchend`. Un contact démarré sur une ancienne édition peut alors tourner la page d'une représentation rechargée. De même, masquer puis réafficher rapidement le contenu d'un roman privé ne doit pas permettre la fin d'un geste ancien.

## Correctif

Le gestionnaire V52 utilise un `MutationObserver` ciblé pour les seuls changements d'attribut `hidden` de `#reader-text` et du conteneur `#reader-content`. Dès qu'un changement est observé, il annule tout toucher ou glissement souris en cours, même si l'état est déjà revenu à la valeur initiale. Les protections V117 (numéro), V118 (événement canonique) et V122 (mode en début/fin) restent actives.

Aucun texte de roman, identifiant, autorisation, appel réseau ou écriture de progression n'est ajouté. L'observateur est déconnecté lors de la destruction du gestionnaire. Les swipes valides suivants (gauche = suivante, droite = précédente) restent normaux.

## Validation

- Tests Node : faux `MutationObserver` vérifiant les deux éléments surveillés, la bascule transitoire PDF → texte → PDF, le masquage temporaire du roman, la préservation de nouveaux gestes valides et la déconnexion complète des observateurs.
- Playwright Chromium/WebKit sur vrai HTML isolé : interruption d'un toucher pendant un aller-retour PDF → texte → PDF, avec micro-tâche pour vider les observations de mutations; vérification qu'aucune page ne tourne et que le mode paginé est restauré.
- Cache busting V52 **`52.11.15.123`** synchronisé dans HTML, fixture, import V53 et tests. V53 reste à `53.11.15.121`.

**Statut NO-GO** : la PR demeure DRAFT, non fusionnée sur `main`; aucun déploiement. iPhone Safari/Android Chrome physiques, VoiceOver/TalkBack, Auth/RLS et livre privé, synchronisation multi-appareils et 13 conditions de lancement restent à homologuer. Les scores globaux des programmes Nova/SINJIRA demeurent ceux des audits historiques.

# SINJIRA™ — V56 : annonces accessibles et reprise de la position sur mobile

**10 novembre 2026 — modification candidate. Ne pas publier directement.**

## Pourquoi poursuivre après V52–V55 ?

La V52 assure le geste gauche/droite sur la page source; V53 découpe le texte de la page PDF en portions lisibles sur téléphone; V54 a ajouté les parcours Chromium et WebKit simulés; V55 laisse une ligne de recouvrement entre écrans pour limiter les passages perdus.

Deux risques d'ergonomie et d'accessibilité restaient à traiter :
1. La zone `aria-live` indiquant « Écran X sur Y » pouvait être **réécrite sur chaque événement de défilement**, même si l'écran annoncé ne changeait pas. Une technologie d'assistance peut alors annoncer plusieurs fois le même contenu.
2. Lors d'une rotation ou de changements rapprochés de taille de police, les événements **resize**, **input**, **change** ou **media change** pouvaient déclencher plusieurs corrections de position et recalculer la proportion depuis une mise en page déjà modifiée.

## Correctif V56

- L'indicateur accessible n'est modifié que lorsque la phrase décrivant **l'écran réellement affiché** change, évitant les mutations DOM répétées.
- Les recalculs de géométrie d'un même changement de mise en page se regroupent en **une seule restauration** d'emplacement après deux trames d'affichage.
- La première position **proportionnelle** (scrollTop / longueur défilable) est conservée pendant ce recalcul, pour empêcher un événement intermédiaire de remplacer le point de référence.
- L'ancienne position reste une proportion de la page PDF. Cette amélioration **ne garantit pas une ancre sémantique exacte** lorsqu'un texte ou sa mise en page change fortement.
- Pas de modification du code de droits `get-novel-file-url`, des rôles Supabase, du stockage du livre intégral, de la synchronisation CAS V51 ou des migrations.

## Vérification

- **33 contrôles Node V53–V56 + 20 contrôles V52 = 53 contrôles de logique** : cas limites de pagination, chevauchement de lignes, annonce non répétée au micro-défilement, restauration de ratio sous événements resize/media en double, taille de police avec input/change en rafale.
- Parcours de navigateur **Chromium et WebKit** : vérification réelle de l'absence de mutations `aria-live` redondantes; conservation approximative du ratio pendant rotation portrait/paysage; maintien des contrôles gestuels, du mode PDF et de la sélection.
- Workflow `.github/workflows/sinjira-liseuse-accessibilite-v56.yml` en `contents:read`, aucun compte ni roman privé dans les tests.

## Conditions de fusion inchangées

Cette PR doit être revue dans sa **pile V56 → V55 → V54 → V53 → V52 → main**. Les essais sur **iPhone Safari réel, Android Chrome réel, tablette, VoiceOver/TalkBack, gros caractères, rotation, sélection et annotations**, ainsi que les droits du livre intégral et la synchronisation V51, restent nécessaires avant une décision de publication.

La maturité globale **SINJIRA 66,5 % ±10 points** demeure celle du registre de référence, avec **13/13 portes de lancement encore ouvertes**. Une réussite de tests automatisés ne représente ni une approbation de sortie ni un taux de complétude de 100 %.

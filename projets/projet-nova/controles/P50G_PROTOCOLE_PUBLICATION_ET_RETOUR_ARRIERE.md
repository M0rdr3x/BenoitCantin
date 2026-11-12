# Projet Nova — P50G : protocole de décision et de restauration

**14 octobre 2026 | Dossier de revue, non constitutif d'une autorisation.** Base maîtresse V3.40 inchangée. Statut de publication : **NO_GO**.

## Fondement

P50F a établi trois écarts sur les pages publiques `participer.html`, `avis-legal.html`, `code-conduite.html`; `recrutement.html` montre déjà le contact volontaire minimal. Les PR 636 et 638 contiennent les corrections proposées, la PR 640 n'est qu'une branche de recette et doit demeurer **non fusionnée**. P50F se trouve dans la PR 645 (constat documentaire).

L'ancienne checklist recommandait d'activer Formspree : P50G supprime cette instruction périmée. Le site indique la suspension des formulaires externes. Les affirmations publiques sont une **déclaration éditoriale**, et non une preuve de flux réels ou de conformité juridique.

## Séparation fonctionnelle

| Fonction | Preuve attendue | Limite |
| --- | --- | --- |
| Relecteur de contenu | Concordance des six pages, textes et statut Projet Nova | N'atteste pas le déploiement |
| Réviseur technique indépendant | Revues des PR 636 et 638 aux derniers SHA, diff et CI | N'autorise pas à lui seul la fusion |
| Responsable confidentialité | Révision des flux de courriel, finalité, sécurité, accès, effacement, sous-traitants, hors Québec | Ne donne pas de statut électoral |
| Conseil juridique | Analyse du régime applicable et réserves écrites | L'autorité compétente conserve sa compétence |
| Mainteneur habilité | Vérification des versions et des conflits, journal Git | Ne décide pas de l'opportunité politique |
| Opérateur de site | Sauvegarde, déploiement, test de restauration et procédure d'incident | Ne publie pas sans GO |
| Décideur habilité | Décision GO/NO_GO écrite, datée, avec périmètre et SHA | Ne peut ignorer une interdiction légale |
| Responsable de recette | Réponses HTTP et vérification après changement réel | N'atteste pas la conformité juridique |

Aucune de ces fonctions ni aucun de leurs mandats ne peut être présumé à partir d'un compte GitHub.

## Matrice des 14 portes

- **B01 — Identité** : Projet Nova actuellement; « Parti Nova » uniquement au futur conditionnel.
- **B02 — Statut électoral** : vérifier l'autorisation applicable auprès d'Élections Québec; aucune contribution ni sollicitation non autorisée.
- **B03 — Collecte** : aucun formulaire nouveau, aucun embed de collecte, aucun lien de paiement.
- **B04 — Protection** : aucune donnée personnelle réelle dans Git, CI, captures ou registre public.
- **B05 — Confidentialité** : finalité, minimisation, conservation, demandes, sécurité, hébergement, accès et traitement externe.
- **B06 — Revue PR 636** : revues documentées sur la révision finale.
- **B07 — Revue PR 638** : revues documentées sur la révision finale.
- **B08 — Intégration** : dépendances, base SHA, conflits, CI; **NE PAS FUSIONNER PR 640**.
- **B09 — Mandat** : autorité du décideur et du mainteneur démontrée hors dépôt public.
- **B10 — Réversibilité** : sauvegarde, plan de retour arrière et exercice isolé.
- **B11 — Autorisation** : décision humaine sur les SHA précis avant toute fusion.
- **B12 — Production** : contrôle HTTP réel après publication autorisée, six URL, empreintes et comportements.
- **B13 — Incident** : procédure d'arrêt, de remontée et de restauration habilitée.
- **B14 — Clôture** : signature de recette et archivage des éléments contrôlables.

**L'absence d'une seule porte applicable = NO_GO.** Le contrôleur statique P50G émet toujours `NO_GO_AUTOMATIQUE`, même si son tableau est complet. Il ne peut pas certifier l'authenticité des pièces ni l'habilitation de la personne signataire.

## Séquence A/B/C

### A. Sans impact public
1. Lire `main` et les PR à la date réelle, geler les SHA, consigner les écarts et les six pages.
2. Exécuter les tests sur une copie locale, sans données personnelles, et placer les justificatifs sensibles dans un stockage adapté.
3. Vérifier les rôles et les revues externes. Constituer un dossier de décision indépendant.
4. Préparer une sauvegarde et une procédure documentée de retour arrière.
5. Simuler une altération puis une restauration **uniquement sur des copies**. Cet essai ne démontre pas la restauration de l'hébergement ou du domaine.

### B. Autorisation distincte
Le responsable habilité émet une décision avec SHA, périmètre, durée, réserves, exécution et recette. Toute nouvelle modification après cette décision force une réévaluation. En son absence : NO_GO.

### C. Seulement après GO
Le mainteneur habilité peut intégrer séparément PR 636 et PR 638, si elles demeurent pertinentes. La PR 640 reste non fusionnée. La recette indépendante doit observer le déploiement effectif et les six pages HTTP, puis conclure par procès-verbal. Tout échec implique un arrêt et l'éventuelle restauration selon le mandat.

## Retours arrière : limites obligatoires

Conserver l'identifiant du contenu antérieur, le SHA de référence, le plan de restauration, les accès autorisés et la preuve d'un exercice isolé. Documenter les caches CDN, DNS, dépendances, pages indexées et les données ou emails déjà transmis qui ne peuvent pas être effacés par un simple retour arrière Git. **N'effectuer aucune restauration sur le site public sans une autorisation distincte.**

## Situation institutionnelle préservée
P2-C0-49 EN_COURS; W0 NON_CLOTUREE; W1 NO_GO; W2–W4 NON_AUTORISEES; E26 0/20; pouvoirs 0/14; pièces financières 0/16; portes financières bloquantes 14/14. Aucune porte n'est levée par P50G.

## Références externes
- Élections Québec — autorisation pour contributions et dépenses : https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-une-autorisation/
- Québec — protection des renseignements, outils : https://www.quebec.ca/gouvernement/travailler-gouvernement/normes-gouvernance-pratiques-internes/protection-des-renseignements-personnels/outils

Ces sources générales ne déterminent pas le statut légal particulier du Projet Nova. Une revue compétente demeure obligatoire.

**Suite recommandée : P50H — revue indépendante et registre d'habilitations sans publication ni fusion automatique.**

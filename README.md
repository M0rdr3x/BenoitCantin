# Portail personnel de Benoit Cantin

Site public de `www.benoitcantin.com`, publié depuis la branche `main` avec GitHub Pages.

## Focus public actuel

Le portail met volontairement en avant trois portes principales :

- **SINJIRA™** — univers narratif, romans, jeux et espaces communautaires;
- **Registre des Consciences** — création et suivi des personnages liés à SINJIRA™;
- **Projet Nova** — projet citoyen indépendant.

D’autres prototypes ou expériences peuvent rester présents dans l’historique du dépôt pour continuité technique, sans faire partie du focus public actuel.

## Principes obligatoires

### L'humain avant tout

Les choix de conception, de sécurité et d'évolution du projet doivent placer la personne, sa dignité et sa sécurité avant les objectifs techniques, commerciaux ou d'automatisation.

### Protéger sans surveiller

La sécurité doit être obtenue avec le moins de collecte et de surveillance possible. Une mesure de protection ne doit pas devenir un prétexte pour suivre inutilement les personnes.

### Solaire : surfaces déjà artificialisées d'abord

Pour tout projet solaire soutenu, proposé, conçu, recommandé ou intégré par ce portail et ses projets, la priorité est obligatoire : **installer d'abord les panneaux sur les toitures de bâtiments, les stationnements avec ombrières solaires et, lorsque pertinent, les autres surfaces ou friches déjà artificialisées et adaptées**.

Une installation solaire ne doit pas servir de justification pour détruire, défricher ou convertir une forêt, une terre agricole productive, un milieu humide ou un habitat naturel. Ces espaces doivent être protégés avant d'envisager une nouvelle emprise au sol pour produire de l'énergie solaire.

Cette règle constitue un critère de conception et de décision du projet, et non une simple préférence.

## SINJIRA™

Chemin principal : `projets/sinjira/`

- Romans : `projets/sinjira/romans/`
- Jeux : `projets/sinjira/jeux/`
- Registre des Consciences : `projets/sinjira/registre/`
- Communauté : `projets/sinjira/communaute/`
- Monde parallèle : `projets/sinjira/monde-parallele/`

Les anciennes URL conservées dans le dépôt servent uniquement à la compatibilité lorsque nécessaire.

## Données, secrets et services externes

Les identifiants techniques privés, adresses de destination internes, clés API et autres secrets opérationnels ne doivent pas être documentés ici ni exposés au navigateur. Les formulaires publics utilisent leur configuration de routage sans publier les adresses privées de destination.

SINJIRA™ fonctionne actuellement en **mode gratuit verrouillé** : les fonctions payantes, paiements en ligne, achats de Points et fournisseurs d’IA distante payante ne sont pas activés en production.

## Déploiement

- GitHub Pages publie depuis `main` à la racine.
- Domaine canonique : `www.benoitcantin.com`.
- Supabase est synchronisé au moyen des workflows protégés et du ledger de migrations de production.
- Les migrations déjà appliquées en production ne doivent pas être réécrites; toute évolution passe par une nouvelle migration.

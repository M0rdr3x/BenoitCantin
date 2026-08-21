# Portail personnel de Benoit Cantin

Site public de `www.benoitcantin.com`, publié depuis la branche `main` avec GitHub Pages.

## Focus public actuel

Le portail met volontairement en avant trois portes principales :

- **SINJIRA™** — univers narratif, romans, jeux et espaces communautaires;
- **Registre des Consciences** — création et suivi des personnages liés à SINJIRA™;
- **Projet Nova** — projet citoyen indépendant.

D’autres prototypes ou expériences peuvent rester présents dans l’historique du dépôt pour continuité technique, sans faire partie du focus public actuel.

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

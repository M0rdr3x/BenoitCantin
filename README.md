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

### Transparence sur l'intelligence artificielle

Les idées, la vision, les orientations et les décisions finales sont humaines. Benoit Cantin utilise des outils d'intelligence artificielle comme assistance pour structurer, rédiger, programmer, corriger, vérifier et mettre en œuvre certaines de ses idées.

La mention publique standard est :

> **Idées, vision et décisions : Benoit Cantin. Mise en œuvre assistée par des outils d'intelligence artificielle. Validation finale et responsabilité du contenu : Benoit Cantin.**

La règle détaillée se trouve dans `AI_TRANSPARENCY.md` et la déclaration publique dans `/transparence-ia.html`. La gouvernance du chatbot public Nova × SINJIRA est versionnée dans `ASSISTANT_GOVERNANCE.md` et présentée publiquement dans `/assistant.html`. Les nouveaux livrables publics autonomes doivent inclure cette mention, ou une formulation équivalente, lorsque leur format le permet.

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

## Livre I — actifs de diffusion courants

Le candidat web #449 utilise désormais comme démo publique officielle de **SINJIRA™ — Livre I : La Cendre du Jugement** le PDF de **84 pages** fourni le 4 octobre 2026 :

- chemin public : `projets/sinjira/documents/SINJIRA_Livre_01_La_Cendre_du_Jugement_DEMO.pdf`;
- taille : **941 065 octets**;
- SHA-256 : `d0668a7b07a07321ef1e02cfceb826d3881330bb36417d53e5ff5bd32635628e`;
- contenu annoncé : prologue + chapitres 1 à 3.

Le nouveau master intégral contient **1027 pages**, taille **7 325 502 octets**, SHA-256 `9acc8f561962850158cb073b122ee038c2731ee3b165deae482260c0cc1ad2d8`. Il reste strictement hors de l’artefact public : sa diffusion est préparée côté backend privé #435 et doit passer par un Storage privé et des URL signées après contrôle serveur du droit d’accès.

Le lecteur démo, ses contrôles de progression et la CI sont verrouillés sur 84 pages afin d’empêcher le retour silencieux de l’ancienne limite à 83 pages.

## Données, secrets et services externes

Les identifiants techniques privés, adresses de destination internes, clés API et autres secrets opérationnels ne doivent pas être documentés ici ni exposés au navigateur. Les formulaires publics utilisent leur configuration de routage sans publier les adresses privées de destination.

SINJIRA™ fonctionne actuellement en **mode gratuit verrouillé** : les fonctions payantes, paiements en ligne, achats de Points et fournisseurs d’IA distante payante ne sont pas activés en production.

## Déploiement

- Domaine canonique : `www.benoitcantin.com`.
- **Hébergement public actuel vérifié le 30 septembre 2026 : GitHub Pages.** Le run GitHub `pages build and deployment` associé à `main` a effectué le checkout de `main` puis téléversé l’artefact Pages avec `path: .`. Le domaine répond aussi avec `Server: GitHub.com`.
- Cette publication de la racine du dépôt est encore trop large : l’observation HTTP en lecture seule a confirmé `200` pour `/supabase/config.toml`, `/tests/e2e/test_public_site.py` et `/mobile-native/App.tsx`. Ces artefacts ne sont pas des secrets nouveaux puisque le dépôt est public, mais ils ne doivent pas faire partie du site applicatif.
- Le candidat web-only #449 contient une configuration Netlify qui construit un publish public isolé dans `_site`, mais **Netlify n’est pas l’hébergeur actif observé du domaine**. Les règles `netlify.toml` ne protègent donc pas le site live actuel.
- Avant toute publication de #449, la source GitHub Pages qui publie `main` avec `path: .` doit être désactivée ou remplacée par un mécanisme qui déploie uniquement l’artefact public allowlisté; alternativement, une migration explicite vers Netlify doit être configurée puis prouvée par une vraie Deploy Preview.
- Tant que cette bascule n’est pas prouvée, un merge ou un push sur `main` peut republier la racine technique et ne constitue pas une release sûre.
- Supabase est synchronisé au moyen des workflows protégés et du ledger de migrations de production.
- Les migrations déjà appliquées en production ne doivent pas être réécrites; toute évolution passe par une nouvelle migration.

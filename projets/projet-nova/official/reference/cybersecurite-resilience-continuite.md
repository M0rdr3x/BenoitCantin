# V317 — Cybersécurité de l’État, résilience, réponse aux incidents et continuité numérique

## 1. Objet
V317 ajoute une couche de cybersécurité opérationnelle au Projet Nova sans élargir les pouvoirs de surveillance de l’État et sans modifier les protections V316 sur l’identité, la vie privée, les permissions et les journaux d’audit.

Le principe directeur est simple : **un service public numérique doit rester défendable, récupérable et contrôlable même lorsqu’un système, un fournisseur, un compte privilégié ou une dépendance technique échoue.**

La cybersécurité est une fonction de protection et de continuité. Elle ne devient pas une justification générale pour collecter davantage de renseignements sur la population, contourner les règles d’accès ou fusionner les dossiers.

## 2. Inventaire, criticité et dépendances
Tout service numérique important doit connaître les systèmes, données, interfaces, comptes privilégiés, fournisseurs et dépendances dont il dépend. Un actif critique qui n’est pas inventorié ne peut pas être correctement protégé, restauré ou remplacé.

Chaque service critique doit identifier ses dépendances techniques, humaines, contractuelles et physiques, ainsi que les conséquences plausibles d’une indisponibilité ou d’une compromission. La criticité doit être justifiée par l’impact sur le service, les droits, la sécurité, les finances publiques ou la continuité institutionnelle.

## 3. Architecture défensive et séparation
Les systèmes sensibles doivent être organisés de manière à limiter la propagation d’une compromission. Les accès administratifs, environnements de production, sauvegardes, outils de développement et systèmes moins sensibles ne doivent pas être traités comme un seul périmètre de confiance implicite.

Les communications et accès entre zones doivent être autorisés selon le besoin réel, la fonction et la finalité. La simple présence sur un réseau gouvernemental ne constitue pas une autorisation générale.

V317 ne crée pas une architecture centralisée unique obligatoire. La segmentation, la redondance et la séparation peuvent être adaptées au risque et à la nature du service.

## 4. Configuration sécurisée, changements et vulnérabilités
Les systèmes doivent disposer de configurations de référence connues, de changements traçables et d’un mécanisme permettant d’identifier les écarts importants. Une modification critique doit pouvoir être reliée à une autorisation, un responsable et un plan de retour arrière lorsque pertinent.

Les vulnérabilités et expositions doivent être découvertes, évaluées, priorisées et corrigées selon le risque réel. Les systèmes exposés à Internet, les composants critiques et les accès privilégiés exigent une attention proportionnée à leur impact potentiel.

V317 ne fixe pas un délai universel de correction applicable à toutes les vulnérabilités ni un score unique de criticité obligatoire.

## 5. Sauvegardes, intégrité et restauration
Les données et configurations nécessaires à la continuité doivent disposer de sauvegardes ou mécanismes de récupération adaptés à leur importance. Une sauvegarde qui n’a jamais été restaurée avec succès ne constitue pas une preuve suffisante de récupérabilité.

Les mécanismes de sauvegarde doivent réduire le risque qu’une compromission du système principal permette de détruire simultanément toutes les copies de récupération. Les restaurations doivent être testées et documentées selon le risque et la criticité.

V317 ne fixe pas un RPO, un RTO, un nombre universel de copies ou une fréquence unique de test pour tous les services.

## 6. Réponse aux incidents
Tout incident significatif doit suivre une chaîne identifiable : détection, qualification, confinement, préservation des preuves nécessaires, correction, restauration, validation du retour au service et leçon tirée.

Les responsabilités doivent être connues avant l’incident. Les décisions prises sous urgence doivent être consignées suffisamment pour permettre un contrôle après coup, sans empêcher les mesures immédiates nécessaires à la protection du service.

Un incident de sécurité ne suspend pas automatiquement les droits fondamentaux, les règles de preuve, les obligations de confidentialité ou les contrôles V316.

## 7. Communication et transparence en situation d’incident
Lorsqu’un incident touche la disponibilité d’un service, l’intégrité de données ou des renseignements personnels, la communication doit être proportionnée, exacte et utile. Elle doit distinguer ce qui est confirmé, ce qui est encore en analyse et les mesures concrètes que les personnes ou services concernés doivent prendre.

La transparence ne signifie pas publier des détails techniques qui faciliteraient une attaque en cours. La confidentialité opérationnelle temporaire doit cependant être justifiée et ne doit pas devenir un moyen d’effacer l’incident du registre public ou de l’audit.

## 8. Continuité des services et reprise après sinistre
Chaque service essentiel ou critique doit disposer d’un plan de continuité et de reprise correspondant à ses dépendances. Le plan doit préciser les fonctions minimales à maintenir, les alternatives possibles, les responsables, les dépendances prioritaires et les conditions de retour au fonctionnement normal.

Lorsque cela est raisonnablement nécessaire, des procédures manuelles, canaux alternatifs ou modes dégradés doivent permettre de préserver un service critique durant une panne numérique majeure.

La reprise doit être testée; un document jamais exercé ne doit pas être considéré comme une capacité démontrée.

## 9. Infrastructures numériques critiques
Les plateformes d’identité, réseaux essentiels, services de nommage, hébergement, clés et secrets, systèmes financiers, télécommunications institutionnelles et autres infrastructures critiques doivent éviter les points de défaillance uniques lorsque le risque le justifie.

Une panne d’un composant central ne doit pas automatiquement paralyser l’ensemble des services lorsqu’une architecture raisonnablement résiliente peut éviter cette dépendance.

## 10. Fournisseurs et chaîne d’approvisionnement numérique
Les services publics doivent connaître les fournisseurs, logiciels, composants et dépendances externes significatifs utilisés par leurs systèmes critiques. Une responsabilité contractuelle n’efface pas la responsabilité institutionnelle de vérifier la sécurité, la continuité, la réversibilité et la récupération des données.

Les changements majeurs de fournisseur, les dépendances propriétaires difficiles à remplacer et les accès techniques de tiers doivent être identifiés et suivis.

V317 n’impose pas un fournisseur, un nuage, une technologie ou un produit de sécurité unique.

## 11. Comptes privilégiés, secrets et administration
Les accès privilégiés doivent rester limités, attribuables et séparés des usages ordinaires. Les secrets, clés, jetons et mécanismes d’administration doivent être protégés, rotatifs ou révocables lorsque nécessaire, et ne doivent pas être stockés de façon à rendre leur compromission triviale.

Une fonction technique élevée n’accorde aucun pouvoir souverain. Les administrateurs de sécurité restent des exécutants d’un mandat limité et auditable.

## 12. Détection, surveillance technique et respect de la vie privée
Les systèmes peuvent être surveillés pour détecter les attaques, erreurs, abus techniques ou anomalies de sécurité. Cette surveillance doit être liée à une finalité de sécurité précise et respecter les restrictions V316.

Les journaux de sécurité ne doivent pas devenir un prétexte à la surveillance générale des citoyens, au profilage politique, à la constitution d’un dossier transversal ou à l’analyse comportementale sans base légale.

Les données collectées pour la sécurité doivent être minimisées, protégées et conservées selon des règles explicites.

## 13. Tests de sécurité et exercices
Les services critiques doivent pouvoir subir des tests contrôlés : revues de configuration, tests de restauration, exercices d’incident, évaluations de sécurité, simulations de panne ou tests d’intrusion autorisés selon le contexte.

Ces exercices doivent éviter de créer eux-mêmes un risque disproportionné pour les services réels ou les données de citoyens. Les résultats doivent produire des correctifs traçables et un suivi de leur résolution.

## 14. Registres V317
V317 introduit huit modèles interopérables :
1. registre des systèmes, services critiques et dépendances;
2. registre des vulnérabilités, expositions et correctifs;
3. registre des sauvegardes, restaurations et preuves de récupération;
4. registre des incidents de cybersécurité et réponses;
5. registre des plans de continuité et de reprise;
6. registre des fournisseurs et dépendances de chaîne numérique;
7. registre des changements de sécurité et configurations de référence;
8. registre des exercices, tests et correctifs de résilience.

## 15. Paramètres volontairement laissés ouverts
V317 ne fixe pas automatiquement :
- un RPO universel;
- un RTO universel;
- une fréquence universelle de sauvegarde ou de test de restauration;
- un délai universel de correction des vulnérabilités;
- un score universel de criticité;
- un seuil universel de déclaration d’incident;
- un délai universel de notification d’un incident;
- une durée universelle de conservation des journaux de sécurité;
- un nombre universel de centres de reprise ou de copies;
- une fréquence universelle d’exercice de crise;
- un fournisseur ou une technologie de cybersécurité imposée;
- un algorithme cryptographique unique inscrit politiquement dans la doctrine.

Ces paramètres doivent découler de la loi, des normes techniques applicables, de la criticité du service et de décisions explicitement adoptées.

## 16. Primauté citoyenne et absence d’effet juridique automatique
La cybersécurité protège les services et les droits; elle ne crée pas une nouvelle source de pouvoir sur la population. Aucun responsable cyber, administrateur, fournisseur ou opérateur d’infrastructure n’acquiert une autorité souveraine ou générale sur les citoyens.

V317 ne produit aucun effet juridique automatique, ne ferme aucune des 14 décisions politiques héritées, ne valide aucune des 26 sections anglaises, ne modifie aucun paramètre fiscal V308 et ne retire aucune protection V312 à V316.

---

**Transparence IA —** Idées, vision et décisions : Benoit Cantin. Mise en œuvre assistée par des outils d'intelligence artificielle. Validation finale et responsabilité du contenu : Benoit Cantin.

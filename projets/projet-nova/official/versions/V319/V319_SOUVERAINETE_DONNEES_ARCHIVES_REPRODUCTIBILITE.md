# V319 — Souveraineté des données publiques, archives pérennes, dépôt de source et reproductibilité

## 1. Objet
V319 complète l’architecture numérique V318 en traitant une question distincte : **comment l’État conserve-t-il la maîtrise de ses données, de ses dossiers et de sa capacité de reconstruire un service numérique au-delà d’un fournisseur, d’une génération technologique ou d’une équipe donnée?**

Le principe directeur est : **une fonction publique critique ne doit pas dépendre d’une mémoire technique, d’un format, d’un dépôt de code, d’une clé contractuelle ou d’un savoir détenu exclusivement par un tiers au point de devenir irréconstructible.**

V319 ne crée aucun droit de collecte supplémentaire. Il ne transforme pas la souveraineté des données publiques en droit de centraliser toutes les données sur les personnes.

## 2. Souveraineté des données : maîtrise juridique, opérationnelle et technique
La souveraineté des données publiques signifie que l’État doit pouvoir déterminer, conformément au droit applicable, qui peut accéder aux données, pour quelle finalité, selon quelles règles, pendant combien de temps et avec quelles responsabilités.

La maîtrise publique doit aussi être opérationnelle : l’État doit pouvoir récupérer les données nécessaires, vérifier leur intégrité, les interpréter, les migrer et poursuivre le service sans dépendance exclusive à une interface ou à une permission unilatéralement contrôlée par un fournisseur.

V319 n’impose pas une localisation physique universelle de toutes les données sur le territoire. Toute exigence de résidence des données doit être décidée selon la sensibilité, la continuité, les obligations juridiques, le risque et les capacités techniques.

## 3. Classification minimale avant conservation ou transfert
Les données et dossiers doivent être classés selon leur fonction et leur sensibilité avant qu’une règle de conservation, d’archivage, de réplication ou de transfert soit appliquée.

La classification distingue au minimum :
- données publiques ouvertes;
- documents administratifs ordinaires;
- dossiers contenant des renseignements personnels;
- informations confidentielles ou protégées;
- éléments de sécurité, secrets ou clés;
- archives à valeur historique ou probante.

Une même politique de conservation ou d’export ne doit pas être appliquée indistinctement à toutes ces catégories.

## 4. Portabilité intergénérationnelle des dossiers
Un dossier public important doit rester interprétable après le remplacement du système qui l’a créé.

La portabilité intergénérationnelle exige, lorsque nécessaire :
- le contenu du dossier;
- les métadonnées essentielles;
- les relations entre éléments;
- la provenance;
- les versions pertinentes;
- les règles de validation;
- la documentation du schéma;
- les pièces jointes nécessaires;
- les éléments permettant de vérifier l’intégrité.

Un fichier exporté sans contexte, un format dépendant d’un logiciel disparu ou une base impossible à relire ne constitue pas une conservation suffisante.

## 5. Paquet d’archive pérenne
Lorsqu’un dossier doit être conservé au-delà de la vie utile de son système d’origine, l’archive doit pouvoir être constituée comme un paquet cohérent : données, métadonnées, documentation, contexte, intégrité et règles de lecture.

Le paquet d’archive doit permettre de distinguer le contenu original, les transformations de conservation et les migrations ultérieures.

La migration de format ne doit pas effacer silencieusement l’historique ni faire passer une transformation pour l’original.

## 6. Intégrité, provenance et chaîne de conservation
Les données ou dossiers qui servent de preuve administrative, financière, juridique ou historique doivent conserver une provenance vérifiable.

Les mécanismes d’intégrité peuvent utiliser des empreintes, signatures, journaux de conservation, contrôles croisés ou autres moyens adaptés. V319 n’impose pas un algorithme cryptographique unique ni une notarisation externe universelle.

Les mécanismes de preuve doivent eux-mêmes être documentés afin qu’un futur système puisse expliquer ce qui a été vérifié et comment.

## 7. Source, configuration et matériaux de reconstruction
Pour un système public critique, la continuité ne doit pas dépendre d’un exécutable opaque impossible à reconstruire après la disparition d’un fournisseur ou d’une équipe.

Selon le risque et le modèle contractuel, l’État doit conserver ou obtenir un accès juridiquement opposable aux matériaux nécessaires à la reconstruction, par exemple :
- code source nécessaire;
- scripts de construction et de déploiement;
- définitions d’infrastructure;
- schémas de données;
- paramètres non secrets;
- documentation des dépendances;
- procédures d’installation;
- versions et artefacts de référence;
- instructions de restauration.

V319 n’impose pas la publication publique universelle du code source et ne convertit pas automatiquement les logiciels propriétaires en logiciels libres.

## 8. Dépôt de source et mécanismes d’entiercement
Lorsqu’un fournisseur conserve des éléments essentiels que l’État ne détient pas directement, un mécanisme d’entiercement ou une protection contractuelle équivalente peut être exigé afin d’éviter la perte du service.

Les conditions de déclenchement peuvent notamment couvrir l’abandon du produit, la cessation d’activité, l’insolvabilité, l’impossibilité durable d’assurer le service ou une rupture contractuelle affectant la continuité.

Les conditions exactes de déclenchement, les délais et le contenu minimal du dépôt doivent être adaptés au risque et explicitement adoptés; V319 ne les invente pas.

## 9. Reproductibilité des constructions
Lorsqu’elle est raisonnablement applicable, la chaîne de construction d’un système critique doit permettre de démontrer qu’un artefact déployé correspond aux sources, versions et dépendances déclarées.

La reproductibilité peut être exacte ou suffisamment déterministe pour permettre une comparaison et une investigation fiable selon la technologie concernée.

Une impossibilité technique légitime doit être documentée plutôt que masquée par une déclaration de conformité fictive.

## 10. Dépendances et chaîne de compilation
La capacité de reconstruire un système exige de connaître ses dépendances techniques et leurs versions, y compris les composants nécessaires à la compilation, à l’exécution, au déploiement et à la restauration.

Les dépendances externes critiques doivent être identifiables, remplaçables ou accompagnées d’un plan de continuité proportionné.

V319 complète les contrôles V317 sur la chaîne d’approvisionnement numérique et V318 sur l’enfermement fournisseur; il ne les remplace pas.

## 11. Documentation vivante et continuité du savoir
Un système critique ne doit pas dépendre de connaissances détenues uniquement dans la mémoire de quelques personnes.

La documentation nécessaire à l’exploitation et à la reconstruction doit être maintenue avec les changements significatifs : architecture, procédures, dépendances, responsabilités, sauvegarde, restauration, déploiement, reprise et limites connues.

La documentation n’a pas besoin de reproduire chaque détail banal, mais elle doit permettre à une équipe compétente et autorisée de reprendre le service sans dépendance personnelle irremplaçable.

## 12. Reconstruction indépendante et exercices
La continuité réelle se vérifie par la capacité de restaurer ou reconstruire à partir d’éléments contrôlés.

Les systèmes critiques doivent pouvoir faire l’objet d’exercices proportionnés de restauration, reconstruction ou migration. Les résultats, écarts et correctifs sont consignés.

V319 ne fixe pas une fréquence universelle d’exercice ni un temps maximal universel de reconstruction.

## 13. Conservation, minimisation et destruction
La pérennité ne signifie pas conservation infinie.

Les renseignements personnels et données sensibles doivent rester soumis aux principes V316 de finalité, minimisation, séparation des usages et limitation de conservation. Une obligation d’archive historique ou probante doit être distinguée d’une conservation opérationnelle courante.

Lorsqu’une destruction est requise, elle doit être contrôlée, traçable et compatible avec les obligations légales de preuve et d’archivage.

## 14. Migration entre générations
Une migration importante doit comparer avant et après :
- nombre et type d’objets;
- relations essentielles;
- métadonnées requises;
- pièces jointes;
- droits et restrictions;
- éléments de provenance;
- contrôles d’intégrité.

Les écarts non expliqués doivent être traités avant la fermeture définitive de l’ancien système.

## 15. Décommissionnement probant
Le décommissionnement V318 est complété par une exigence de preuve : avant de considérer un ancien système comme fermé, l’organisme doit pouvoir démontrer que les données requises ont été migrées ou archivées, que les obligations de conservation sont couvertes, que les secrets et accès ont été traités et que les matériaux nécessaires à une vérification future ont été préservés.

## 16. Registres V319
V319 introduit huit modèles interopérables :
1. registre de classification et de garde des données;
2. registre des archives pérennes, formats et plans de préservation;
3. registre des matériaux de reconstruction et de documentation technique;
4. registre des dépôts de source, entiercements et droits de continuité;
5. registre des constructions reproductibles et vérifications;
6. registre des migrations intergénérationnelles et contrôles d’intégrité;
7. registre de continuité du savoir et documentation opérationnelle;
8. registre des exceptions, risques et mesures compensatoires V319.

## 17. Paramètres volontairement laissés ouverts
V319 ne fixe pas automatiquement :
- une localisation territoriale universelle des données;
- une durée universelle de conservation;
- un format d’archive unique;
- un algorithme d’empreinte ou de signature unique;
- une obligation universelle de publication du code source;
- une fréquence universelle de dépôt de source;
- un délai universel de déclenchement d’un entiercement;
- une fréquence universelle de test de reconstruction;
- un temps maximal universel de reconstruction;
- un taux maximal de données pouvant nécessiter une migration manuelle;
- un outil unique de construction, d’archivage ou de dépôt;
- une règle universelle de conservation des versions historiques.

Ces paramètres doivent dépendre de la fonction, du risque, des obligations légales, de la sensibilité des données et de décisions explicitement adoptées.

## 18. Protections héritées et absence d’effet automatique
V319 préserve exactement les protections V316 sur l’identité et la vie privée, V317 sur la cybersécurité et la résilience, V318 sur l’interopérabilité et la réversibilité, la primauté citoyenne V312 et les paramètres fiscaux hérités V308.

La souveraineté des données publiques ne justifie ni une clé d’accès universelle, ni une superbase de données, ni un profil citoyen transversal, ni une surveillance générale.

V319 ne produit aucun effet juridique automatique, ne ferme aucune des 14 décisions politiques héritées, ne valide aucune des 26 sections anglaises et ne modifie aucun paramètre fiscal V308.

---

**Transparence IA —** Idées, vision et décisions : Benoit Cantin. Mise en œuvre assistée par des outils d'intelligence artificielle. Validation finale et responsabilité du contenu : Benoit Cantin.

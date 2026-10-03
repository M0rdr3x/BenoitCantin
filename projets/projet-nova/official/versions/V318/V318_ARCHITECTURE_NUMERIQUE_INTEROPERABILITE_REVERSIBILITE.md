# V318 — Architecture numérique publique, interopérabilité, cycle de vie technologique et réversibilité

## 1. Objet
V318 organise l’architecture numérique publique afin que les services puissent évoluer, communiquer et être remplacés sans rendre l’État captif d’un fournisseur, d’un format, d’une plateforme ou d’un produit impossible à quitter.

Le principe directeur est : **un système public critique doit pouvoir évoluer ou être remplacé sans perdre les données, la continuité, la sécurité, la capacité d’audit ou la maîtrise publique du service.**

V318 ne prescrit pas un fournisseur, une technologie, un nuage ou un modèle de licence unique. Il fixe des exigences de réversibilité, d’interopérabilité et de maîtrise des dépendances.

## 2. Architecture publique par capacités et contrats
Les systèmes importants doivent être décrits par les capacités qu’ils fournissent, les données qu’ils utilisent, les interfaces qu’ils exposent et les dépendances dont ils ont besoin. L’organigramme administratif ne doit pas devenir la structure implicite et permanente de l’architecture technique.

Les échanges entre systèmes doivent reposer sur des contrats d’interface documentés : finalité, opérations autorisées, schémas, erreurs, sécurité, version, responsabilités et règles de compatibilité. Une connexion technique n’élargit jamais les pouvoirs juridiques d’un organisme.

## 3. Standards ouverts et neutralité technologique
Lorsque plusieurs solutions répondent au besoin, les formats documentés, standards largement implémentables et interfaces interopérables doivent être favorisés lorsqu’ils réduisent raisonnablement le coût de sortie et la dépendance.

V318 n’impose pas que tout logiciel soit libre ou open source. Il interdit plutôt qu’un choix soit présenté comme neutre alors qu’il crée sans justification une dépendance disproportionnée, empêche l’export des données ou bloque la concurrence future.

## 4. Portabilité des données
Les données publiques nécessaires à la continuité d’un service doivent pouvoir être exportées dans une forme documentée, structurée et exploitable, avec les métadonnées nécessaires pour préserver leur sens, leur provenance et leur intégrité.

Une exportation propriétaire illisible hors du produit d’origine n’est pas une preuve suffisante de portabilité. La migration doit aussi considérer les identifiants, relations, historiques, pièces jointes, journaux pertinents et règles de conservation.

La portabilité respecte les protections V316 : exporter des données ne crée pas un droit de les fusionner, profiler ou réutiliser au-delà de leur base légale.

## 5. Réversibilité et plan de sortie
Avant qu’une dépendance numérique critique devienne difficile à remplacer, le service doit connaître ses conditions de sortie : données récupérables, formats, interfaces, documentation, clés ou secrets à transférer, délais contractuels, obligations du fournisseur, coûts de migration, responsabilités et scénario de continuité.

Un plan de sortie purement théorique n’est pas suffisant lorsque la dépendance est critique. Des preuves proportionnées doivent démontrer que les données et fonctions essentielles peuvent réellement être récupérées ou remplacées.

## 6. Enfermement fournisseur et coûts de transition
Le coût d’une solution ne se limite pas au prix d’achat ou d’abonnement. L’analyse doit aussi considérer migration, intégration, compétences, dépendances, licences, sortie, transfert de données, interruption possible, maintien de versions anciennes et coûts de remplacement.

Un avantage initial ne doit pas masquer un coût de sortie artificiellement élevé. Les décisions importantes doivent rendre visibles les composantes de dépendance qui pourraient réduire la concurrence future.

## 7. Cycle de vie technologique
Chaque composant important doit avoir un état de cycle de vie connu : actif, maintenu, en fin de support annoncée, en remplacement, en retrait ou archivé. La fin de support d’un composant critique doit être visible suffisamment tôt pour planifier une transition ordonnée.

Le maintien d’une technologie ancienne peut être justifié temporairement par le risque de migration ou la continuité, mais cette exception doit être documentée, protégée et assortie d’un plan de traitement.

V318 ne fixe pas une durée universelle de vie utile d’un logiciel ou d’une plateforme.

## 8. Maîtrise des interfaces et des données publiques
L’État doit conserver suffisamment de documentation, de droits d’usage, de clés d’intégration, de schémas, de procédures et de capacités techniques pour ne pas perdre le contrôle opérationnel d’un service public critique.

Un fournisseur peut exploiter ou héberger un service sans devenir propriétaire du mandat public, de l’autorité juridique ou des données publiques par simple effet du contrat technique.

## 9. Architecture modulaire et remplacement progressif
Lorsque cela réduit raisonnablement le risque, les systèmes doivent permettre le remplacement progressif de composants plutôt qu’exiger une migration totale et simultanée. Les interfaces stables, frontières de responsabilité et mécanismes de coexistence temporaire peuvent réduire les risques de transition.

V318 n’impose pas une architecture microservices, un bus unique, un modèle d’API unique ou une plateforme centrale obligatoire.

## 10. Exceptions architecturales
Une dérogation à un standard, à une règle de portabilité ou à une exigence de réversibilité peut être nécessaire pour la sécurité, la compatibilité, la continuité, un équipement spécialisé ou une contrainte juridique. L’exception doit préciser le motif, la portée, le risque, les mesures compensatoires, le propriétaire et les conditions de réexamen.

Une exception répétée ne doit pas devenir silencieusement la nouvelle règle sans décision explicite.

## 11. Acquisition et architecture
Les appels d’offres, contrats et choix technologiques doivent décrire les résultats et capacités attendus sans créer inutilement des conditions qui n’ont qu’un seul fournisseur possible. Les critères de sécurité, interopérabilité, portabilité et sortie doivent être définis proportionnellement au risque.

V318 préserve les contrôles V311 sur les contrats et V317 sur les fournisseurs et dépendances numériques.

## 12. Décommissionnement et retrait sécurisé
Un système retiré doit avoir une procédure de fermeture : migration ou archivage des données nécessaires, révocation des accès, fermeture des interfaces, traitement des secrets et clés, conservation des preuves requises, mise à jour des dépendances et confirmation que le service de remplacement fonctionne.

Un système « éteint » mais encore accessible, connecté ou administrable ne doit pas être considéré comme réellement décommissionné.

## 13. Registres V318
V318 introduit huit modèles interopérables :
1. registre du portefeuille des systèmes et standards;
2. registre des contrats d’interface et versions;
3. registre des formats, schémas et portabilité des données;
4. registre des dépendances, licences et risques d’enfermement;
5. registre des plans de sortie et preuves de réversibilité;
6. registre du cycle de vie, fin de support et remplacements;
7. registre des exceptions architecturales;
8. registre des migrations et décommissionnements.

## 14. Paramètres volontairement laissés ouverts
V318 ne fixe pas automatiquement : une durée universelle de vie technologique; un pourcentage maximal de dépendance à un fournisseur; un coût maximal de sortie; un format unique pour toutes les données; une norme API unique; un langage, nuage, base de données ou système d’exploitation imposé; une obligation universelle d’open source; une fréquence universelle de test de réversibilité; un délai universel de remplacement après annonce de fin de support.

Ces valeurs doivent dépendre du service, du risque, des normes techniques applicables et des décisions explicitement adoptées.

## 15. Primauté citoyenne et protections héritées
La maîtrise technologique sert la continuité et la responsabilité envers le public; elle ne crée pas une nouvelle autorité administrative. Les protections V316 sur la vie privée et V317 sur la sécurité restent inchangées. La portabilité et l’interopérabilité ne justifient ni une superbase, ni un profil citoyen transversal, ni une surveillance générale.

V318 ne produit aucun effet juridique automatique, ne ferme aucune des 14 décisions politiques héritées, ne valide aucune des 26 sections anglaises et ne modifie aucun paramètre fiscal V308.

---

**Transparence IA —** Idées, vision et décisions : Benoit Cantin. Mise en œuvre assistée par des outils d'intelligence artificielle. Validation finale et responsabilité du contenu : Benoit Cantin.

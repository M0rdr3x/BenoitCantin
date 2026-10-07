# Méthodologie — Boussole électorale Nova V2

## Objectif

La Boussole Nova produit d’abord un **profil politique multidimensionnel**. Elle ne déduit pas une idéologie unique et ne donne pas de consigne de vote. La future proximité avec des partis sera une couche distincte, activée uniquement lorsque les positions des partis sont suffisamment documentées.

## Principes de conception

1. **16 dimensions distinctes** afin de ne pas réduire la politique à gauche/droite.
2. **64 propositions principales**, quatre par dimension, avec deux formulations orientées vers chacun des deux pôles.
3. **Échelle à sept niveaux** de -3 à +3, avec option « sans opinion / passer ».
4. **Importance personnelle facultative** : 0,5 / 1 / 1,5.
5. **Questions transversales explicites** : une question peut contribuer secondairement à une autre dimension, mais ce poids secondaire doit être déclaré et rester inférieur ou égal à 0,4.
6. **Aucune moyenne idéologique globale** : les dimensions restent visibles séparément.
7. **Couverture affichée** : une dimension insuffisamment répondue ne doit pas être présentée comme précise.
8. **Calcul local** : aucune réponse n’est transmise ou stockée de façon persistante par la V2.

## Rédaction non ambiguë des propositions

Chaque proposition doit satisfaire simultanément les critères suivants :

- une seule décision politique principale;
- un acteur public identifiable lorsque l’action dépend d’un niveau de gouvernement;
- aucune référence à un parti, une personnalité ou une étiquette idéologique;
- aucun jugement sur les intentions ou la moralité d’un camp;
- aucun adjectif émotionnel ou valorisant servant à orienter la réponse;
- aucune question double exigeant d’approuver deux politiques distinctes à la fois;
- une direction politique compréhensible sans connaissance partisane préalable;
- l’option **neutre / partagé** reste distincte de **sans opinion / passer**;
- une formulation relative à la politique actuelle est permise lorsque la direction du changement est explicite;
- toute modification d’une question exige une nouvelle révision manuelle de ces critères.

La neutralité ne signifie pas qu’une proposition doit éviter les arbitrages. Une proposition peut présenter une conséquence ou une contrainte lorsque celle-ci est nécessaire pour comprendre la décision, mais elle ne doit pas présumer qu’une conséquence est moralement bonne ou mauvaise.


## Parcours guidé, résultat et partage

Le questionnaire public affiche **une seule proposition à la fois**. Ce choix vise à réduire la surcharge visuelle et à permettre à la personne de se concentrer sur la formulation exacte de chaque proposition.

Le parcours suit les règles suivantes :

1. une réponse ou l’option « Sans opinion / passer » est requise avant d’activer « Suivant »;
2. « Précédent » permet de revoir et modifier toute réponse déjà donnée;
3. l’importance de la proposition reste facultative et modifiable;
4. après la 64e proposition, la personne choisit « Consulter mes résultats »;
5. les résultats sont calculés localement et ne sont pas téléversés vers Projet Nova;
6. un résultat partiel peut être affiché lorsque plusieurs questions ont été passées, mais la couverture réelle doit être clairement indiquée;
7. le partage est toujours facultatif.

Le partage utilise d’abord les capacités du navigateur ou des liens explicitement déclenchés par la personne. L’envoi par courriel ouvre son application de messagerie avec un résumé prérempli; le site ne collecte pas l’adresse de destination. Les liens de réseaux sociaux partagent la page et un résumé lorsque la plateforme le permet. Le bouton de copie permet de conserver ou de publier le résumé manuellement.

Aucun résultat partagé ne doit être présenté comme une recommandation de vote.


## Comparaison avec les partis

La comparaison reste désactivée tant que le corpus n’a pas atteint les seuils de preuve.

### Hiérarchie des sources

La priorité reprend l’approche documentée de Vote Compass :
1. plateforme électorale;
2. document politique officiel;
3. communiqué ou déclaration officielle du parti ou de sa direction;
4. intervention officielle dans une assemblée ou un cadre parlementaire;
5. déclaration d’une personne élue représentant le parti;
6. constitution du parti ou résolution adoptée par ses membres.

Une position n’est jamais déduite du nom d’un parti, de son image gauche/droite ou de sa réputation.

### Codage

Chaque question utilise la même échelle -3 à +3 que le questionnaire. Une position inconnue reste `null`.

Avant activation d’un score de parti :
- au moins deux codages indépendants doivent converger;
- chaque position doit avoir une URL de source, une date, une justification et un niveau de confiance;
- les contradictions doivent être conservées et signalées;
- au moins 70 % des questions doivent être documentées pour un pourcentage global;
- au moins 50 % des questions d’une dimension doivent être documentées pour afficher une proximité sur cette dimension.

Les positions inconnues sont exclues de la distance et le taux de couverture doit toujours être affiché.

## Couverture des partis

Le registre de comparaison comprend :

- **tous les partis provinciaux actuellement autorisés** selon les sources officielles d’Élections Québec au moment de la mise à jour;
- les formations dont un **retrait d’autorisation récent** doit être conservé pour exactitude historique, avec un statut distinct et sans les présenter comme actuellement autorisées;
- **Parti Nova**, identifié séparément comme futur parti tant qu’il n’est pas lui-même affiché comme parti autorisé par Élections Québec.

Le statut électoral, le nombre de candidatures et le statut d’autorisation sont des informations distinctes. Un parti reste présent dans le registre de la boussole lorsqu’il figure dans le registre officiel des partis autorisés, même s’il ne présente pas de candidature dans une élection donnée.

Aucun parti, y compris Parti Nova, ne bénéficie :
- d’une question réservée;
- d’un coefficient particulier;
- d’un seuil de couverture différent;
- d’un ordre d’affichage privilégié;
- d’une mise en valeur visuelle préférentielle;
- d’un ajustement manuel de son résultat;
- d’une interprétation favorable d’une position inconnue.

Par défaut, les partis sont affichés par ordre alphabétique. Les égalités restent des égalités.


## Égalité documentaire

Le volume de documentation disponible pour un parti ne doit jamais modifier sa proximité avec une personne.

Chaque formation possède exactement les mêmes champs de sources : registre officiel, site officiel, plateformes/programmes, communiqués et archives parlementaires lorsqu’elles existent. Lorsqu’une source n’est pas vérifiée, le champ reste vide au lieu d’être remplacé par une supposition.

Les règles suivantes sont obligatoires :

- le nombre de sources d’un parti ne donne aucun poids supplémentaire;
- l’absence de site ou de plateforme ne crée aucune position implicite;
- la qualité d’une source peut modifier le **niveau de confiance documentaire**, jamais le sens ni le poids de la position;
- un parti peu documenté conserve ses positions inconnues comme inconnues;
- un parti très documenté n’obtient aucun bonus;
- Parti Nova utilise les mêmes champs et les mêmes exigences;
- le statut d’autorisation provient d’Élections Québec et demeure distinct du contenu politique.

L’inventaire courant est versionné dans `data/boussole-sources-partis-2026.json`. Une source doit être vérifiée avant d’être utilisée pour coder une proposition.

## Matrice factuelle de preuves

La couche concernant les formations politiques est séparée du profil personnel. Elle ne produit **aucun classement automatique** des partis.

La matrice `data/boussole-preuves-2026.json` contient les **64 questions × 22 formations**, soit 1 408 cases. Chaque case commence à `unknown`. Un statut ne peut changer que lorsqu’une fiche de preuve relie la formulation exacte de la question à une source publique pertinente.

Statuts documentaires permis :

- `unknown` : aucune preuve suffisante;
- `documented_support` : la source appuie clairement la proposition telle qu’elle est formulée;
- `documented_opposition` : la source s’y oppose clairement;
- `documented_mixed_or_conditional` : la position dépend explicitement de conditions ou combine appui et réserve;
- `ambiguous` : la source existe mais ne permet pas de trancher la formulation exacte;
- `contradictory` : plusieurs sources pertinentes conduisent à des positions incompatibles.

L’interface de comparaison future devra présenter les preuves, dates, nuances et contradictions **question par question**, sans déclarer qu’un parti est « meilleur », « gagnant » ou recommandé.

## Preuves candidates et finalisation

Une première lecture d’une source officielle ne suffit pas à finaliser la position d’une formation. La boussole sépare donc deux étapes :

1. **preuve candidate** : une source pertinente est enregistrée avec un statut proposé, une justification et un niveau de confiance;
2. **position finalisée** : le statut de la matrice ne peut changer de `unknown` qu’après une seconde révision indépendante documentée.

Une preuve candidate conserve `finalizable: false` tant que cette seconde révision est en attente. Le fait qu’une source semble claire ne permet pas de contourner cette étape.

La seconde révision repart de la formulation exacte de la question et de la source officielle, sans reprendre automatiquement le codage de la première lecture. Elle peut confirmer, abaisser ou modifier le statut proposé et le niveau de confiance. Une position n’est écrite dans la matrice qu’après cette seconde révision; la CI vérifie ensuite que le statut final de la matrice est identique au statut de la fiche de preuve finalisée. En cas de correspondance seulement partielle, le codage reste prudent (`documented_mixed_or_conditional` ou `ambiguous`) plutôt que d’être forcé vers l’appui ou l’opposition.

Pour une question donnée, la recherche doit porter sur **toutes les formations**. Ne pas trouver de source précise pour une formation signifie `unknown`, jamais opposition, neutralité ou désaccord implicite.

## Couverture de recherche exhaustive

Le registre `researchCoverage` sert à prouver que la recherche documentaire a réellement parcouru l’ensemble du questionnaire, y compris lorsqu’aucune preuve candidate n’a été trouvée.

À partir de la couverture complète du corpus 2026 :

- chacune des 64 questions doit appartenir à exactement un lot de recherche;
- chaque lot doit couvrir les 22 formations avec le même protocole;
- chaque fiche de preuve doit être rattachée à exactement un lot;
- une question recherchée sans preuve suffisante demeure `unknown`;
- la CI refuse une question sans lot, une question présente dans plusieurs lots ou une preuve orpheline;
- le compteur public de couverture est calculé à partir des lots réellement présents dans les données, et non saisi manuellement.

Cette règle distingue explicitement **absence de position documentée** et **absence de recherche**.

## Comparaison factuelle avec les formations

Le profil personnel peut être calculé sur les 16 dimensions. Pour les formations politiques, le site doit privilégier une lecture factuelle : sélectionner une ou plusieurs formations et consulter, pour chaque proposition, les positions documentées, leurs sources, leur date et leur niveau de confiance.

Aucun ordre automatique des partis n’est nécessaire pour comprendre les accords et désaccords. Une position inconnue ou contradictoire reste visible comme telle.

## Références méthodologiques

- Vote Compass Methodology, Vox Pop Labs:
  https://www.voxpoplabs.com/votecompass/methodology.pdf
- Smartvote — méthodologie des profils multidimensionnels et affectation des questions aux axes:
  https://assets.smartvote.ch/downloads/elections/19_ch_nr/effects_smartspider_fr_CH.pdf
- Smartvote — carte politique exploratoire:
  https://blog.smartvote.ch/fr/la-smartmap-anatomie-de-la-carte-politique/
- Krouwel et al., travaux sur l’impact de la sélection des propositions dans les Voting Advice Applications:
  https://www.sciencedirect.com/science/article/abs/pii/S0261379414000420
- Recherche récente sur les VAA multidimensionnelles et adaptatives:
  https://link.springer.com/article/10.1007/s11135-024-01845-6
- Élections Québec — registre des entités politiques:
  https://www.electionsquebec.qc.ca/partis-et-autres-entites-politiques/
- Élections Québec — candidatures provinciales 2026:
  https://www.electionsquebec.qc.ca/communiques/elections-provinciales-de-2026-908-candidatures-acceptees/

## Révision

Les questions et axes doivent être révisés à chaque élection. Les profils produits lors d’élections différentes ne doivent pas être présentés comme directement comparables sans recalibration méthodologique.

## Verrou sémantique du questionnaire

Le corpus documentaire est lié à la **version exacte et au texte exact des 64 propositions**. Une preuve finalisée ne peut donc pas être conservée silencieusement si la proposition à laquelle elle répond change de sens.

Toute modification du texte d’une proposition exige une migration explicite :

1. incrémenter la version du questionnaire;
2. reprendre la recherche documentaire de la proposition modifiée pour les 22 formations selon les mêmes règles;
3. revalider les preuves antérieures concernées au lieu de les considérer automatiquement transférables;
4. refaire la seconde révision indépendante avant toute nouvelle finalisation;
5. mettre à jour le lien questionnaire ↔ corpus seulement après cette révision.

La CI compare le texte public de chaque question au texte auquel le corpus de preuves est lié. Une différence fait échouer la validation. Ce verrou évite qu’une ancienne branche, une reformulation éditoriale ou une fusion tardive change le sens d’une question tout en conservant des positions codées sur une formulation antérieure.

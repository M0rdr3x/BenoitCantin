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

## Distance électorale

La proximité future utilisera une distance normalisée entre les réponses de la personne et les positions documentées du parti, avec pondération par l’importance choisie par l’utilisateur. Les résultats devront afficher les plus grands accords et désaccords, et non seulement un pourcentage.

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

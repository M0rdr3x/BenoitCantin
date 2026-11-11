# SINJIRA™ — V60 : éviter les micro-écrans à la fin des pages PDF

**10 novembre 2026 — correctif candidat, non fusionné, non publié.**

## Défaillance ergonomique potentielle

La pagination texte de la V53 (préparée pour la liseuse au doigt sur téléphone) avance normalement par une hauteur calculée selon les interlignes et les marges. Lorsque la longueur défilable ne dépasse que de **quelques pixels** un multiple entier de ce déplacement, le lecteur peut présenter un « dernier écran » qui avance à peine. Par exemple, avec un pas de **245 px** et une longueur défilable de **500 px**, les arrêts précédents pouvaient être **0 → 245 → 490 → 500** : la dernière commande déplace seulement **10 px**, ce qui n'a pas le comportement attendu d'une liseuse.

## Correctif candidat

- À condition qu'il ne reste **pas plus d'un interligne** après un pas entier, la pagination fusionne l'avant-dernier arrêt et le bord final du texte.
- L'exemple devient **0 → 245 → 500**, puis la vraie page PDF suivante. Le retour revient **500 → 245 → 0** dans l'ordre inverse.
- Le déplacement supplémentaire est plafonné par `min(0.18 * step, lineHeight)` afin de conserver les limites de recouvrement V55 et de ne pas masquer un passage complet.
- Un marque-page déjà sauvegardé dans un ancien arrêt proche de la fin peut rejoindre le vrai bord final par un seul geste; il n'est pas réécrit ni migré.
- Les modes défilement libre, PDF fidèle, sélection, gestes et navigation au clavier restent inchangés.
- **Aucune modification** de la synchronisation cloud V51, des tables PostgreSQL, des permissions ou du texte du roman.

## Vérifications et limites

- Quatre tests Node additionnels : suppression des micro-écrans, maintien d'un écran distinct lorsqu'il reste plus d'une ligne, reversibilité à limite exacte et reprise d'un ancien arrêt.
- Le parcours navigateur sur la vraie page SINJIRA contrôle le calcul V60 en Chromium et WebKit en plus des parcours tactiles et responsive V54/V57/V58. Les résultats de CI ne doivent être qualifiés de réussis qu'une fois vérifiés.
- Une simulation de navigateur ne remplace pas un essai physique sur iPhone/Android ou une réception de VoiceOver/TalkBack.
- Le caractère « réellement comme une liseuse » ne dépend pas de ce seul correctif : des tests de contenu réel, accessibilité, gros caractères, permissions et cache PWA restent nécessaires.

## Ordre de publication

**V60 est empilée sur [PR d'intégration V58 #983](https://github.com/M0rdr3x/BenoitCantin/pull/983), qui est toujours DRAFT.** Pour conserver une seule source de vérité, fusionner V58 et V60 dans cet ordre uniquement après les validations physiques et la revue. Ne pas publier les changements de gestes sans coordination avec le compagnon historique V28.

**Statut : NO_GO production.** La maturité globale SINJIRA reste **66,5 % ±10 points** et les **13 portes de lancement restent ouvertes**. La [PR de contrôle des droits V59 #986](https://github.com/M0rdr3x/BenoitCantin/pull/986) concerne séparément la base SQL candidate V51; elle ne doit pas être déployée sans revue indépendante.

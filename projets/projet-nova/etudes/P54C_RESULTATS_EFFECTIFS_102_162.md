# P54C — Observations effectivement vérifiées le 24 octobre 2026

P54C a été exécuté sur les deux fichiers PDF 2024 réellement capturés par HTTPS et vérifiés par SHA-256. L'exécution initiale a signalé une erreur de clé Unicode dans la configuration JSON, puis le correctif a rétabli la cohérence du schéma; la validation complète est ensuite réussie.

Exécution effective : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40119313052

Artefact public dérivé, sans PDF ni texte brut : https://github.com/M0rdr3x/BenoitCantin/actions/runs/40119313052/artifacts/12570109480

Empreinte SHA-256 de l'archive dérivée : f466f35a8432056c0dcf73bdc4ed9e95a944c60e57d0c8e39b6f5e935964a958

## Résultat de la comparaison contextuelle

Pour le rapport financier 2024 de la Ville, index PDF 102, et la publication correspondante MAMH, index PDF 162, le système a effectivement retrouvé **sept marqueurs contextuels sur sept dans les deux pages** :

1. Rapport des auditeurs indépendants.
2. Ventilation des dépenses mixtes.
3. Compétences de nature locale.
4. Compétences d'agglomération.
5. Exercice terminé le 31 décembre 2024.
6. Référence au R.A.V.Q. 1435.
7. Présence d'une opinion d'audit.

Les deux pages paraissent donc présenter le **même type de rapport d'audit à portée réglementaire précise**. Ce résultat est un rapprochement documentaire par expressions, et non une affirmation que chaque caractère des deux éditions est identique, ni que les montants sont égaux.

La divergence numérique lexicale précédente est reproduite exactement : dix jetons côté Ville, treize côté MAMH, neuf occurrences communes, une non appariée côté Ville, quatre côté MAMH, score Dice 78,26 %. Les cinq occurrences non appariées ne constituent pas cinq erreurs, et leur origine n'a pas été établie par l'analyse contextuelle.

Ces différences pourraient provenir de mentions de pagination, d'identifiants, de coordonnées imprimées ou d'autres éléments de présentation; il s'agit seulement d'hypothèses à vérifier.

## Portée et interdictions

Le rapport d'audit original porte sur la ventilation réglementaire des dépenses mixtes entre compétences locales et d'agglomération. Il n'est pas un audit de la politique fiscale du Projet Nova. Aucune preuve de poste comptable contradictoire, d'économie budgétaire, ni d'irrégularité n'est actuellement issue de la comparaison.

Les huit contrôles qualitatifs P54C doivent encore être instruits : nature du rapport, période, périmètre, base réglementaire, comparaison effective d'édition, cause des différences numériques, portée des signatures et avis, et effets sur les travailleurs/tiers/services. Les 96 contrôles comptables P54B demeurent non validés.

Le résultat observé est conservé dans P54C_OBSERVATIONS_AUDIT_2026_10_24.json, avec référence du workflow et indicateurs seulement. Un contrôle automatique distinct vérifie qu'aucun champ de conclusion ne puisse être changé en certification financière.

**Décision : NO_GO_AUTOMATIQUE**. Aucune économie certifiée, aucun poste supprimé, aucun service réduit, aucun merge dans main, aucune intervention sur SINJIRA.

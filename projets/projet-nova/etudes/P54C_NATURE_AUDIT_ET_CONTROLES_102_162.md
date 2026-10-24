# P54C — Examen ciblé des dépenses mixtes, Ville PDF 102 / MAMH PDF 162

**24 octobre 2026.** Le rapprochement P54B a identifié une paire de pages de plus faible recouvrement numérique lexical : Ville 102 ↔ MAMH 162 (indices PDF commençant à zéro). Les 56 tests P54B et 26 tests de suivi ont réussi.

## Observation directement appuyée par la source Ville

Le PDF municipal de 2024, index 102, est le début du **rapport des auditeurs indépendants sur le tableau de ventilation des dépenses mixtes entre les compétences locales et d'agglomération**. L'opinion porte sur cette ventilation et sa conformité au **R.A.V.Q. 1435** pour l'exercice terminé le 31 décembre 2024. Le rapport précise que le tableau répond à des exigences réglementaires particulières et peut ne pas convenir à un autre usage. La page PDF 103 poursuit les responsabilités, et la page PDF 104 contient le tableau de ventilation, avec des colonnes distinctes.

Référence primaire : https://www.ville.quebec.qc.ca/publications/docs_ville/Rapport_financier_2024.pdf

Ce constat est important : la différence entre les pages comparées concerne potentiellement la présentation **d'un rapport d'audit spécialisé**, et ne peut être interprétée comme une différence de montants d'exploitation sans revoir les tableaux et les notes.

## Comparaison documentaire à confirmer par capture MAMH

Le PDF MAMH est publié ici : https://www.mamh.gouv.qc.ca/documentsfinanciersweb/Rapport-financier-2024-et-autres-23027.pdf

Le moteur de lecture externe ne permettait pas d'inspecter cette copie à cause de sa taille. Le workflow P54C recapture les deux fichiers depuis les domaines officiels et refuse la comparaison si le SHA-256 réel ou la taille de l'un des PDF ne concorde plus avec les copies publiques de P53Z.

Après vérification des octets, il extrait **uniquement** les pages ciblées (Ville index 102 et MAMH index 162), classe les indicateurs documentaires suivants :
- Rapport des auditeurs indépendants et opinion;
- Tableau de ventilation des dépenses mixtes;
- Compétences de nature locale et compétences d'agglomération;
- Exercice 2024;
- Référence réglementaire R.A.V.Q. 1435.

Les champs indiquent seulement la présence des marqueurs de texte et un booléen de rapprochement de contexte. Le workflow ne publie ni le texte intégral des pages, ni noms d'auditeurs, ni coordonnées ni montants bruts.

## Origine possible des jetons numériques différents

P54B a identifié sur cette paire 10 occurrences de jetons numériques côté Ville, 13 côté MAMH et 9 occurrences communes, soit un Dice lexical de 78,26 %. Ce sont des observations techniques, **pas** des écarts de montants. Les jetons peuvent représenter numéros de pages, années, normes, références, identifiants et coordonnées imprimées sur le document. P54C recalcule ces observations sur les deux pages, sans afficher de valeurs numériques brutes. La cause des jetons distincts reste à établir tant que le rapprochement des contextes n'est pas confirmé.

## Conditions de clôture

Les huit contrôles qualitatifs P54C restent à instruire et à soumettre à une expertise indépendante lorsque les pièces probantes sont disponibles. Une opinion d'auditeurs publiée par la Ville à propos des dépenses mixtes ne constitue pas un avis indépendant destiné au Projet Nova sur ses économies hypothétiques.

Aucune double comptabilisation Ville–RTC n'est permise. Le maintien des effectifs, des droits du travail, de l'accès et de la qualité des services publics reste obligatoire. Les deux régimes, Québec au Canada et Québec souverain hypothétique, demeurent séparés.

Commandes : inventaire neutre : python scripts/analyser_contexte_audit_depenses_nova_p54c.py --bilan p54c_neutre.json ; acquisition réelle : python scripts/analyser_contexte_audit_depenses_nova_p54c.py --reanalyser-copies --bilan p54c_obs.json ; refus explicite : python scripts/analyser_contexte_audit_depenses_nova_p54c.py --exiger-audit-certifie.

Codes : 0 = exécution structurelle ou comparaison contextuelle sans certificat; 2 = erreur d'entrée ou destination; 3 = refus automatique de la prétendue certification; 4 = copies non disponibles ou extraction non concluante.

**NO_GO_AUTOMATIQUE** : aucun montant certifié, aucun avis indépendant signé pour Nova, aucune économie validée ni autorisation de diminuer les effectifs ou les services. PR GitHub #673 demeure en brouillon, sans fusion.

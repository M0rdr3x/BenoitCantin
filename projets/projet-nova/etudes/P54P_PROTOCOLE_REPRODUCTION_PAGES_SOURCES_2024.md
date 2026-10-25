# P54P — Reproduction conditionnelle des cinq positions sur PDF publics

**Projet Nova — 24 octobre 2026.** Cette étape sort du cycle des seules grilles préparatoires : elle retente l'acquisition HTTPS des deux PDF publics 2024, vérifie les versions exactes et tente de reproduire les cinq occurrences P54D dans leur texte de page. **La réussite des tests ne garantit pas que le téléchargement réel réussisse.**

## Deux originaux publics requis simultanément

- Ville de Québec, rapport financier 2024, page PDF index 102, 8 984 919 octets, SHA-256 b3ee3e671f7bf98e56c7d42b5e8b6c34de02a96c9dc1c96469819fa4dbfa7399.
- MAMH, rapport financier 2024 de l'organisme 23027, page PDF index 162, 10 818 312 octets, SHA-256 4323c87d2114b58cf7a093c08f3b30327e949db91b9beb46a627eac1ecb4fc00.

Ces empreintes sont **des références d'édition acquises lors de P53Z/P54D**, et ne sont pas des signatures numériques émises ou confirmées par les institutions. Le téléchargeur existant P53Z restreint HTTPS, les hôtes, redirections, volumes et types de réponse. Les octets PDF ne sont pas conservés dans les artefacts CI.

Si un seul document manque, si un hachage diffère, si l'extraction est incohérente ou si le même audit spécialisé n'est pas identifié des deux côtés, aucune position de caractère n'est déclarée reproduite.

## Cinq observations et portée limitée

P54P recalcule avec la même version de pypdf (5.9.0) les jetons numériques lexicaux non appariés. Il rapproche les positions de leur ordre et de leurs catégories P54D :

| Index P54D | Dossier | PDF | Page index zéro | Nature indicative |
|---:|---|---|---:|---|
| 0 | P54E-V-001 | Ville | 102 | Indéterminée, FIN |
| 1 | P54E-M-001 | MAMH | 162 | Indéterminée, DEBUT |
| 2 | Aucun dossier P54E | MAMH | 162 | Année/date probable, FIN |
| 3 | P54E-M-002 | MAMH | 162 | Indéterminée, FIN |
| 4 | P54E-M-003 | MAMH | 162 | Indéterminée, FIN |

Il ne publie que **des indices de caractères dans le texte extrait**, leur longueur de page et le rattachement au dossier. Les jetons, montants éventuels et passages voisins restent hors des rapports publics. Ces indices ne sont ni des coordonnées géométriques sur la page, ni des preuves d'une divergence comptable, ni des signatures d'audit.

La page Ville 102 contient un rapport des auditeurs indépendants sur la ventilation des dépenses mixtes suivant le R.A.V.Q. 1435. Cet audit porte sur son tableau réglementaire et **ne constitue pas** un audit des propositions budgétaires Nova. La correspondance de deux pages n'établit ni l'existence d'un double paiement, ni un montant économisable.

## Résultats et codes

Deux exécutions complémentaires :

    python scripts/reproduire_localisations_pdf_nova_p54p.py --bilan p54p_neutre.json

    python scripts/reproduire_localisations_pdf_nova_p54p.py --acquerir --bilan p54p_capture.json

Codes : **0** = bilan vierge produit ou reproduction technique intégrale des cinq occurrences; **4** = acquisition tentée mais reproduction impossible; **2** = configuration ou fichiers non recevables; **3** = refus d'une prétendue certification automatique.

L'état REPRODUCTION_TECHNIQUE_SANS_ATTESTATION signifie que deux copies HTTPS de SHA attendu ont été lues et que la comparaison lexicale de 5 positions a pu être faite. L'état NON_REPRODUIT signifie que la preuve requise n'est pas complète. Les erreurs réseau et les éditions changées ne doivent jamais être assimilées à une attestation.

Pour démontrer le refus d'une certification :

    python scripts/reproduire_localisations_pdf_nova_p54p.py --exiger-certification

## Limites et indépendance de la revue

La reproductibilité peut faciliter **la localisation initiale des cinq observations** et réduire le risque de mélanger plusieurs jetons de même zone. Une qualification documentaire définitive suppose l'examen des originaux et du contexte par des personnes compétentes, avec trace contrôlée et contre-revue.

P54P ne règle ni les 40 tâches P54N, ni les 96 contrôles de comparabilité P54B, ni les huit contrôles contextuels P54C. Si le téléchargement échoue, toutes les positions demeurent non confirmées; la CI peut réussir ses tests tout en produisant ce constat d'échec.

Aucune expertise indépendante signée, aucune valeur monétaire certifiée et aucune économie ne sont obtenues par P54P. Les éliminations de consolidation Ville–RTC–SOMHAC, les emplois et services et la séparation des scénarios constitutionnels restent protégés.

**NO_GO_AUTOMATIQUE.** Pas de transmission externe, pas de fusion dans main et aucune intervention sur SINJIRA.

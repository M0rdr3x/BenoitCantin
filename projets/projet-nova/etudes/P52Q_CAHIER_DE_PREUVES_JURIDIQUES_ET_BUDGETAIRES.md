# Projet Nova — P52Q : instruction de la première vague de huit preuves

**19 octobre 2026 · Étude juridique et documentaire préliminaire non adoptée · NO_GO.**

## Résultat concret

P52Q ajoute **13 références officielles exploitables comme points de départ**, notamment des textes législatifs fédéraux et québécois, une source nouvelle sur les finances municipales, et une source pour F19 sur la consultation populaire. Deux des treize renvoient aux PDF budgétaires déjà lus à titre assisté en P52J, sans nouvelle vérification binaire. Chaque source indique son URL, la version visible ou la date documentaire et les limites de ce qu'elle peut établir.

**Les nouvelles sources sont des pistes ajoutées aux 20 références historiques de P52P; elles ne sont pas des copies archivées ni des confirmations par juriste.** P52P conserve la photographie antérieure des lacunes, tandis que P52Q documente explicitement le progrès. F19, jusque-là sans source associée dans P52P, dispose désormais d'un texte officiel à examiner; ceci **ne comble pas l'avis F19**, qui exige une vérification de la compétence et de la procédure démocratique.

## Les huit dossiers de preuve

| ID | Sources nouvelles ou actualisées | Résultat manquant |
| --- | --- | --- |
| F01 | Art. 92 et 91 de la Constitution, TVQ version 2026 | Avis juridique provincial sur l'assiette et les textes à modifier |
| F02 | Art. 91-92, Loi fédérale sur la taxe d'accise | Délimitation de la TPS, des impôts fédéraux et des accords |
| F03 | Tarif des douanes et art. 91 | Avis de compétence douanière, sans faux pouvoir québécois |
| F04 | Loi sur la fiscalité municipale et rapports financiers MAMH | Consolidation des recettes locales, des transferts et des services |
| F07 | TVQ, A-6.002, F-2.1, rapports municipaux, E-15 | Registre exhaustif avec impôts, taxes, cotisations, redevances et frais |
| F09 | Deux PDF budget 2026-2027 déjà identifiés en P52J | Copies originales, rapprochement indépendant et contrôle des versions |
| F19 | Loi sur la consultation populaire C-64.1 | Avis sur autorités et processus démocratiques applicables |
| F20 | A-6.002, A-2.1 et P-39.1 | Analyse des droits fiscaux et du bon régime de confidentialité |

**F01–F03** : les art. 91 et 92 établissent la distinction de compétences mais pas une autorisation permettant au Québec provincial d'abolir les taxes fédérales. Le *Tarif des douanes* du Canada ne confère pas un droit provincial de répondre par des contre-tarifs. La source P52O antérieure vers la TVQ datait de 2024; P52Q introduit un texte daté du 1er janvier 2026, dont les éventuelles modifications postérieures doivent être vérifiées.

**F04/F07** : l'accès aux rapports MAMH permet de demander des extractions locales documentées plutôt que de présumer que les revenus locaux ou scolaires peuvent être supprimés sans perte de services. Les derniers rapports disponibles sur la page consultée portent notamment sur 2024, tandis que l'agrégation en données ouvertes peut évoluer; ne pas mélanger millésimes, organismes et transferts. Les textes consultés ne forment **pas** encore l'inventaire complet des prélèvements.

**F09** : P52J reprend deux tableaux budgétaires du Québec pour 2026-2027. Ils concernent des **prévisions**; les PDF originaux n'ont pas été archivés dans une chaîne indépendante (P52K), les comptes réels ne sont pas rapprochés, et le budget Nova à deux prélèvements n'est pas certifié. Éviter absolument de réétiqueter une lecture visuelle en expertise comptable.

**F19** : la *Loi sur la consultation populaire* régit des procédures référendaires qui peuvent être pertinentes selon la décision à prendre; elle ne déclenche pas elle-même un référendum ni une adoption de la réforme Nova. À distinguer de la gouvernance interne d'un parti, d'un vote parlementaire, d'une loi fiscale ou d'un changement constitutionnel.

**F20** : la loi A-2.1 concerne les organismes publics; P-39.1 concerne le secteur privé selon son champ d'application. La capacité juridique des entités du projet, la nature de leurs données et la réglementation des partis politiques doivent être **analysées spécifiquement** avant d'indiquer laquelle s'applique. Aucun renseignement de citoyen n'est demandé ni utilisé ici.

## Protocole exigé avant validation

Pour chaque dossier : 1) version officielle complète et date d'effet; 2) extraction des dispositions précises et de leur champ; 3) archive licite et empreinte originale; 4) méthode d'analyse et interprétations contradictoires; 5) avis indépendant avec signature, vérification de mandat et conflits d'intérêts; 6) effet sur le financement, les travailleurs et les services; 7) procédure de contestation et décision d'autorité compétente. Ces étapes restent non obtenues.

La liste de travaux par preuve se trouve dans `P52Q_DOSSIERS_INSTRUCTION_VAGUE1.json`. Les URL publiques consultées se trouvent dans `P52Q_REFERENCES_PRIMAIRES_VAGUE1.json`, sans stocker le HTML/PDF complet ni prétendre posséder des empreintes. L'outil P52Q vérifie le couplage exact avec P52A, P52O, P52N, P52P, P52J et P52K.

```bash
python scripts/controler_dossiers_primaires_nova_p52q.py --rapport /chemin/prive/p52q_rapport.json
python scripts/controler_dossiers_primaires_nova_p52q.py --exiger-expertises --rapport /chemin/prive/p52q_refus.json
```

Code 0 = conformité structurelle du registre avec maintien NO_GO; 2 = erreur documentaire; 3 = conformité mais expertises manquantes. Les résultats ne contiennent que des compteurs, et les rapports ne sont jamais écrasés.

### Priorité pratique suivante

Constituer **vraiment** les dossiers primaires F01/F02/F03 et F04/F07 avec la version applicable du droit et les données municipales, puis mandater des experts indépendants (ce qui requiert une autorité et un budget réels); F09 doit être traité en parallèle avec une archive vérifiable des PDF. Aucune valeur P52B/P52D n'est alimentée, aucune taxe, contrat, mandat ou consultation n'est adoptée.

Les issues #135 (protection effective de main) et #662 (revues humaines), le partage avec SINJIRA et le statut brouillon de PR #673 restent bloquants pour une fusion.

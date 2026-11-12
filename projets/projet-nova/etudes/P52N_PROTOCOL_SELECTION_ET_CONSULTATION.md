# Projet Nova — P52N : cahiers de mandat, impartialité et consultation publique

**19 octobre 2026 · Ébauche opérationnelle non adoptée. Aucun mandat signé, aucune consultation ouverte, aucune dépense ni publication programmatique autorisée.**

## 1. Passage de la gouvernance à l'instruction effective

Les jalons P52A–P52M ont identifié vingt preuves F01–F20, proposé cinq comités, codifié les sources et établi un mécanisme contradictoire. Ces éléments **ne constituent pas des expertises réalisées**. Les vingt éléments restent non attestés et les 1 320 montants P52B/P52D restent inconnus. P52N prépare désormais le dossier qu'un administrateur réellement compétent devrait autoriser avant tout recrutement d'experts, production de livrables et consultation publique.

Chaque fiche F01–F20, conservée dans `P52N_CAHIER_MANDATS_ET_CONSULTATION.json`, reprend **sans substitution** le régime juridique, la preuve requise et la fonction experte indiquée dans P52A, ainsi que le comité pilote, les regards croisés et la criticité **provisoire** de P52M. Chaque fiche ajoute un livrable de recherche ciblé et six annexes méthodologiques. Un texte de mission est **un objet proposé**, jamais un contrat; tous les champs de budget, prix et expert demeurent explicitement inconnus.

## 2. Procédure recommandée, non déclenchée

1. **Préparer le cahier des charges.** Définir livrables objectifs, sources officielles, années et unités, périmètres constitutionnels séparés, réserves, critères de reproduction, données sous licence et délais à discuter. Inclure les droits de vérification, contestation et correction.
2. **Identifier l'autorité et la source de financement.** Aucune dépense n'est autorisée par ce fichier. Les règles de contractualisation et d'appel d'offres réellement applicables doivent être déterminées et vérifiées avant sollicitation.
3. **Publier un appel neutre seulement après autorisation.** Annoncer la compétence souhaitée, les conflits d'intérêts, la confidentialité, les livrables, les critères préalablement établis et un mécanisme d'appel. Ne pas orienter le choix par proximité partisane.
4. **Contrôler la capacité réelle.** Vérifier références, diplômes, mandat, déclarations d'intérêts, disponibilité et droit d'utiliser les données. Les déclarations auto-remplies ne suffisent pas.
5. **Double examen et récusation.** Deux évaluateurs distincts, sans conflit déclaré ni responsabilité de candidature, apprécient cinq critères proposés entre 0 et 4 : compétence et indépendance, méthode, sources, traitement des risques, transparence et recours. La maquette rejette les auto-évaluations et récusations incomplètes.
6. **Décision humaine motivée et voies de recours.** La simulation ne peut que constater une admissibilité méthodologique hypothétique; elle n'attribue jamais un marché, ne désigne aucun expert et ne crée aucune relation contractuelle.
7. **Réception contradictoire.** Exiger avis datés, pièces primaires, hypothèses, scénarios défavorables, réserves et revue indépendante, avant d'envisager un examen public selon P52L et P52M.

## 3. Consultation publique informative et ouverte à la critique

La consultation, si elle est autorisée, doit proposer une description identique des objectifs et des incertitudes selon le régime **Québec au Canada** ou l'option **Québec souverain**, avec tableaux de coûts et de responsabilités distincts. Inclure des voix diverses sans chercher à persuader un groupe particulier. Une participation à consultation ne constitue ni vote légal ni échantillon statistique représentatif.

Publier un dossier accessible en français clair avec définitions, coûts non calculés, hypothèses ouvertes, limites légales, effets incertains sur les revenus, services et travailleurs, ainsi qu'un espace de questions et d'objections. Des accommodations et canaux alternatifs doivent être prévus selon une analyse juridique et opérationnelle réelle.

- **Transparence :** indiquer qui mène la consultation, comment les avis sont utilisés, quels critères sont appliqués et quels passages sont non vérifiés.
- **Équité :** même information initiale, possibilité de soutenir, critiquer ou proposer une solution différente.
- **Confidentialité :** aucune donnée d'identité, déclaration fiscale, adresse, signature ou contribution brute dans GitHub ou les artefacts CI. Prévoir règles de consentement, durée de conservation, droit de retrait applicable, modération et traitement des abus avant ouverture.
- **Réponse motivée :** pour chaque objection, tracer la question, les sources, la correction acceptée/refusée et les raisons, dans un espace sécurisé. Produire ensuite une synthèse anonyme lorsque sa publication a été autorisée.
- **Calendrier :** ni date d'ouverture ni délai légal ne sont présumés. Ils dépendent d'un lancement réellement autorisé, de l'accessibilité et du droit applicable.

Le journal `P52N_JOURNAL_SIMULATIONS_VIDE.json` est **vide** et **fictif**. Le programme peut simuler uniquement des identifiants techniques et métadonnées, sans texte libre de citoyens. Une réussite du programme n'atteste **aucune** candidature ni contribution réelle.

## 4. Livrables requis dans les domaines sensibles

- **F01–F04 :** validité constitutionnelle et compétence provinciale/fédérale/municipale, continuité des services.
- **F05–F08 :** conception explicite des deux prélèvements, revenus réellement vérifiables et aucun rendement anti-évasion additionnel supposé certifié.
- **F09–F10, F18 :** rapprochement documentaire budget 2026–2027, projection décennale, endettement et conditions prudentes; ne pas confondre prévision et comptes.
- **F11–F14 :** protections des ménages, des entreprises, de l'emploi, des services et des droits, microsimulation représentative seulement après accès légal aux données.
- **F15–F17 :** transition hypothétique avec reprise des compétences fédérales, coût, dette, monnaie et engagements internationaux.
- **F19–F20 :** légitimité démocratique, droits, vie privée et recours; une opinion technique ne remplace pas l'autorité légalement habilitée.

## 5. Contrôle informatique proposé

```bash
python scripts/auditer_mandats_consultation_nova_p52n.py --rapport /tmp/p52n_controle.json
python scripts/auditer_mandats_consultation_nova_p52n.py --exiger-autorisations --rapport /tmp/p52n_refus.json
```

Code **0** : le plan et les simulations éventuelles sont techniquement cohérents, toujours **NO_GO**. Code **2** : irrégularité. Code **3** : état cohérent mais **aucune autorisation humaine effective**. Les rapports n'écrasent jamais des résultats antérieurs. Le validateur refuse les champs supplémentaires susceptibles de porter des identifiants et n'exporte que des compteurs agrégés, jamais des notes par candidat.

## 6. Décisions et blocages restants

P52N ne crée pas d'appels d'offres, de dépenses, de contrats, de consultation ouverte, de données citoyennes ni d'avis publics. La PR #673 doit rester brouillon et ne pas être fusionnée sans protection effective de `main` et revue indépendante réelle, en préservant SINJIRA. Les issues #135 et #662 restent à régler avec des humains compétents.

**Étape P52O recommandée :** dresser le plan budgétaire de l'expertise (avec offres réelles autorisées, pas tarifs inventés), les priorités d'acquisition de preuves F01–F20 et le processus de sélection des organismes et données sources. À défaut de financement ou de mandat, garder NO_GO.

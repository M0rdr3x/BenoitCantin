# Projet Nova — P52V : cahier de mission de vérification indépendante F09

**20 octobre 2026 | Version de préparation | Aucune consultation, dépense, nomination ni signature engagée | NO_GO_AUTOMATIQUE**

## I. Portée du mandat proposé

Objet : évaluer de manière contradictoire la provenance, les chiffres et la signification comptable des publications budgétaires québécoises 2026-2027 utilisées comme **sources F09** pour les deux scénarios proposés par Projet Nova : Québec dans le Canada et Québec souverain hypothétique.

Les étapes P52S–P52U ont permis de réceptionner des octets PDF par HTTPS, d'obtenir des SHA-256 reproductibles, de contrôler les dimensions des deux documents (34 et 426 pages) et de retrouver **39 occurrences attendues sur les pages officielles ciblées**. Elles **n'ont pas certifié la correspondance ligne–valeur**, ni archivé durablement les originaux sous chaîne de garde, ni vérifié une signature de l'éditeur, ni reçu un avis professionnel. Une occurrence numérique trouvée ailleurs sur la même page ne remplace pas une relecture des lignes.

Ce cahier **ne constitue pas un appel d'offres lancé, un contrat, une dépense, ni une attestation professionnelle**. Le champ du mandat et la méthode doivent être validés par un responsable habilité avant de contacter un professionnel. Ne pas présumer que les règles de passation applicables aux organismes publics s'appliquent automatiquement à un projet politique privé; vérifier la nature juridique du mandant.

## II. Sources exactes et tiers de contrôle

- Source technique `DISC2026_T3` : discours budgétaire 2026-2027, *tableau 3*, page imprimée 27, index PDF 29, 29 positions (21 lignes + 8 agrégats).
- Source technique `PLAN2026_F2` : plan budgétaire 2026-2027, *tableau F.2*, page imprimée F.9, index PDF 277, 10 positions signées.
- Ministère des Finances du Québec, portail 2026-2027 : https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/index.asp
- Assemblée nationale, documents déposés le 18 mars 2026 : https://www.assnat.qc.ca/fr/travaux-parlementaires/assemblee-nationale/43-2/journal-debats/20260318so/documents-deposes.html — notamment le tableau des revenus `658-20260318` et le plan budgétaire `660-20260318`. **Ce repérage institutionnel est complémentaire; les PDF du dépôt parlementaire n'ont pas été téléchargés ou recoupés dans P52V.**
- Registre public de l'Ordre des CPA : https://cpaquebec.ca/fr/trouver-un-cpa/tableau-de-lordre/intro/ — permet des vérifications nominatives **quand un candidat réel existe**; l'inscription et les compétences pertinentes doivent être vérifiées au moment du mandat. Ne pas présenter le répertoire comme une validation automatique, ni présumer le besoin d'un permis de comptabilité publique pour tout type de prestation : faire préciser la nature de la mission.

## III. Livrable de travail ligne à ligne

Le fichier `P52V_REGISTRE_MISSION_F09.json` contient **39 positions de relecture**, identifiées sans ambiguïté `DISC-01…DISC-29` et `PLAN-01…PLAN-10`. Il s'agit de **39 positions, pas de 39 chiffres différents** : certains agrégats sont repris dans les deux tableaux, et une même valeur peut apparaître plusieurs fois.

Le professionnel devra pour **chaque position** :
1. Constater l'édition, la page, le libellé officiel exact, l'exercice, l'unité et la valeur avec signe.
2. Indiquer si la lecture antérieure P52J/P52U est correcte, incorrecte, ambiguë ou devenue obsolète.
3. Expliquer toute réserve, donner l'extrait/page justificatif archivé sous accès restreint et préciser la correction proposée sans supprimer l'original.
4. Séparer une simple transcription d'un jugement sur les normes comptables et du financement hypothétique de Projet Nova.

Le registre est volontairement **gelé en `NON_EXAMINE`**. Aucun programme GitHub ne doit permettre de remplir une « signature vérifiée » en modifiant seulement une cellule JSON.

## IV. Programme minimal de contre-expertise

- Contrôle de provenance : éditions, dates, PDFs complets, droits de conservation, SHA-256, limites de la chaîne HTTPS, modifications documentaires ultérieures.
- Rapprochement : 21 lignes, 8 agrégats, 10 montants signés, **trois éléments communs aux tableaux** : revenus autonomes 134 361 M CAD, transferts fédéraux 32 131 M CAD, revenus totaux 166 492 M CAD.
- Regroupements : TVA/TVQ et autres taxes à la consommation (ne pas confondre la catégorie « taxes de vente » et la seule TVQ), contributions santé, propriété scolaire, entreprises du gouvernement, transferts et frais.
- Signes et soldes : dépenses de portefeuilles, dette, provision, Fonds des générations, déficit comptable et solde de la loi d'équilibre budgétaire; éviter toute double comptabilisation.
- Périmètres : administration provinciale, fédérale, municipale, scolaire, et secteur non inclus; distinguer flux autonomes et transferts.
- Temporalité : **prévisions publiées le 18 mars 2026** et non comptes observés; rapprocher toute mise à jour et, lorsque disponible, les comptes réalisés dans une annexe datée.
- Régimes politiques : dans le Canada, les recettes fédérales ne deviennent pas provinciales par la réforme; en souveraineté hypothétique, **32 131 M CAD de transferts fédéraux ne sont pas présumés maintenus**.
- Modèle Nova : aucun bilan « deux taxes », calcul du gain net pour chaque foyer, économie publique, ou garantie sur l'emploi et les services ne peut être attesté avec ces deux seules pages.

## V. Candidature, indépendance et conditions préalables

Vérifier le statut du mandant, son autorité de dépenser, la nature de la mission (analyse, examen limité, audit ou autre) et les règles professionnelles applicables. Rechercher une personne réellement compétente en **finances publiques du Québec et lecture de documents gouvernementaux**, avec expérience vérifiable des périmètres et rapprochements. Envisager un professionnel CPA lorsque pertinent, vérifier son statut dans le registre de l'Ordre, ses limitations applicables et l'indépendance déclarée.

Exiger une lettre de mission établissant méthode, livrables, limites, coût réel, confidentialité, conservation, responsabilités, recours, traitement des erreurs et interdiction d'utiliser un avis hors contexte. Aucun candidat n'est nommé; **aucun devis, coût, contrat ou avis favorable n'est enregistré**. Lorsque le mandat est passé par un organisme public, les règles de contrats publics peuvent s'appliquer selon le statut, le type et le montant; vérifier auprès de l'autorité compétente avant tout engagement, sans inventer de seuil.

## VI. Décision et contrôles contradictoires

Les livrables attendus `L01…L08` et contrôles `C01…C12` figurent dans le JSON. Leur statut initial est **NON REÇU / NON EXÉCUTÉ HUMAIN**. Un responsable différent de l'auteur des chiffres doit vérifier la réception et permettre l'observation d'un désaccord ou d'un avis négatif; la direction politique ne peut pas transformer un avis en unilatéral en preuve certifiée.

Issues possibles (uniquement à l'issue d'une procédure humaine autorisée) : dossier incomplet, avis assorti de réserves, contradiction à résoudre, rejet, ou instruction poursuivie. **Une conformité technique P52V ne signifie jamais F09 valide** : il manque aussi la réconciliation au modèle financier Nova encore incomplet.

## VII. Utilisation automatisée (strictement sans réseau)

```bash
python scripts/preparer_mission_expert_nova_p52v.py --rapport /chemin/prive/bilan.json
python scripts/preparer_mission_expert_nova_p52v.py --export-csv /chemin/prive/relecture_39_positions.csv
python scripts/preparer_mission_expert_nova_p52v.py --exiger-expertise
```

Les commandes assurent que les 39 positions et les blocages sont identiques aux registres antérieurs. Les sorties n'exposent ni noms ni informations privées. Code **0** : dossier cohérent et **NO_GO**, code **2** : structure falsifiée ou sortie inaccessible, code **3** : attestation réellement manquante, non pas échec de test mécanique.

**Prochain acte externe réel :** autorisation de mandatement, sollicitation loyale de candidatures et devis, collecte sous contrôle d'accès, puis avis indépendant et contradictoire. Sans cela, F09 et les 19 autres preuves de P52A restent ouvertes; les **1 320 variables financières** du modèle demeurent inconnues. Maintenir la PR #673 en brouillon, protéger `main` (#135) et obtenir une revue humaine nommée (#662). Aucune modification SINJIRA ni fusion.

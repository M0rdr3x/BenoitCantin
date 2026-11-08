# Projet Nova — Matrice P0 de vérification juridique à deux contextes

**Version de travail du 8 novembre 2026.** **Aucune norme adoptée, aucun avis juridique indépendant déposé et aucune autorisation présumée.** Le Projet Nova demeure un programme candidat; le score documentaire de référence reste **47/100** (audit interne provisoire du 5 novembre), sans point supplémentaire pour cette matrice.

## Objet et portée

Transformer le blocage juridique de la [feuille de route 47→100](feuille-route-completude-47-100-nova-v1.md) en **12 demandes d'examen ciblées et traçables**, chacune examinée sous deux contextes : **Québec dans le Canada** et **Québec souverain hypothétique**. Le statut final d'une question ne se déduit pas d'un autre contexte.

La [matrice structurée](../../data/matrice-juridique-p0-2026-11-08.json) fournit les questions à instruire, la référence Nova actuelle, les pièces attendues et les champs d'homologation volontairement vides.

## Les 12 dossiers juridiques P0

| ID | Dossier | Domaine du score | Québec au Canada / Québec souverain |
| --- | --- | --- | --- |
| J01 | Fiscalité provinciale et deux instruments | FINANCES | Non vérifié / non vérifié |
| J02 | Mécanisme contre l'évasion et les paradis fiscaux | FINANCES | Non vérifié / non vérifié |
| J03 | Taxes municipales et financement des réseaux | FINANCES | Non vérifié / non vérifié |
| J04 | Pensions, cotisations et droits acquis | DROITS | Non vérifié / non vérifié |
| J05 | Réforme électorale à deux tours | INSTITUTIONS | Non vérifié / non vérifié |
| J06 | Vote à distance et preuve du scrutin | INSTITUTIONS | Non vérifié / non vérifié |
| J07 | Référendums, pétitions et révocation | INSTITUTIONS | Non vérifié / non vérifié |
| J08 | Services de santé et main-d'œuvre | SERVICES | Non vérifié / non vérifié |
| J09 | Égalité, langue, vie privée et droits numériques | DROITS | Non vérifié / non vérifié |
| J10 | Premières Nations, territoire et ressources | DROITS | Non vérifié / non vérifié |
| J11 | Transition souveraine, actifs, dette et reconnaissance | SOUVERAINETE | Non vérifié / non vérifié |
| J12 | Statuts, autorisation électorale et financement partisan | ADOPTION | Non vérifié / non vérifié |

**Règle de méthode :** « NON_VERIFIE » désigne l'absence d'une conclusion juridique indépendante dans ce dossier, pas une preuve d'illégalité ou de légalité. Une valeur `null` est une information **non établie**, jamais une validation implicite.

## Ordre de traitement et dépendances

**A — Droits et compétences (J01, J04, J09, J10, J11).** Déterminer ce qui est possible sous le droit actuellement applicable, les droits à préserver et les questions qui exigeraient une négociation ou une révision des textes. Les articles 91 et 92 de la Loi constitutionnelle de 1867 imposent d'analyser la compétence fiscale des deux ordres de gouvernement. Le Renvoi relatif à la sécession du Québec est une référence primaire à étudier avant toute conclusion sur un processus d'accession à la souveraineté.

**B — Budget et services (J02, J03, J08).** Relier la légalité des deux instruments fiscaux envisagés au financement réel des prestations, des municipalités et des salariés. Les pièces G0.14 à G0.17 et les comptes publics constituent un **point de départ documentaire**, pas des revenus additionnels certifiés. Le volet souverain ne conserve pas automatiquement les transferts fédéraux du volet provincial.

**C — Démocratie et publication (J05, J06, J07, J12).** Simuler le système à deux tours, contrôler les recours électoraux et le secret du vote, puis distinguer un parti **projeté** d'une formation **formellement autorisée**. Aucun formulaire, vote ni contribution ne doit être ouvert du seul fait de cette matrice.

## Dossier d'examen attendu par question

Pour chaque identifiant J01–J12, la personne responsable d'une revue externe devra produire : (1) texte en vigueur et compétence; (2) question précise et hypothèses; (3) conformité et objections juridiques contradictoires; (4) droits protégés, risques et recours; (5) coût, financement, personnel et continuité; (6) consultations et participation concernées; (7) scénario alternatif; (8) avis indépendant signé et daté avec limitations; (9) décision de l'instance compétente; (10) suivi de corrections et version.

Une revue **favorable** d'un article n'autorise pas les autres articles par contagion. La somme des tests réussis ne modifie pas automatiquement le 47/100 : le [moteur de clôture G0.17](../../assets/closure-gate-programme-core.mjs) conserve ses sept conditions cumulatives.

## Règles de conformité documentaire

- Les références courantes sont `official/reference/programme.md`, `corpus.md`, `finances.md` et `statuts.md`, toutes **candidates**.
- Les documents du **SCQ** conservés dans les archives sont **historiques** : ils ne deviennent pas le droit du Projet Nova par incorporation silencieuse.
- Les personnes habilitées et les dates autorisées ne sont pas désignées ici. Les champs correspondants restent `null`; aucun mandat ni consultation n'est fictivement attribué.
- Les avis juridiques doivent examiner notamment la Charte canadienne, la Charte québécoise, les droits des peuples autochtones, les garanties procédurales et les obligations du droit public selon leur pertinence.
- Les noms, adresses, renseignements de membre et preuves confidentielles ne doivent pas être publiés dans GitHub.

## Références officielles pour l'instruction (non assimilables à des avis indépendants)

- [Lois constitutionnelles de 1867 à 1982 — Justice Canada](https://laws-lois.justice.gc.ca/fra/const/TexteComplet.html?wbdisable=true).
- [Renvoi relatif à la sécession du Québec — Cour suprême du Canada](https://decisions.scc-csc.ca/scc-csc/scc-csc/fr/1643/1/document.do).
- [Élections Québec — Autorisation et financement politique](https://www.electionsquebec.qc.ca/comprendre/comprendre-le-financement-politique/obtenir-le-droit-de-collecter-des-contributions-ou-de-faire-des-depenses/).


## Contrôle de qualité automatique (branche de travail)

Le module `assets/matrice-juridique-p0-core.mjs` inspecte la matrice JSON, **séparément pour chacun des 24 contextes**. La CI lance `tests/matrice-juridique-p0.test.mjs` lors de changements au moteur, à la matrice ou aux tests.

Pour qu'un avis favorable **ou défavorable** soit déclaré documenté, ses références doivent comprendre : la décision/opinion datée, la pièce de mandat du réviseur et son indépendance déclarée, l'analyse des droits et recours, l'analyse budget/main-d'œuvre et le rapport de consultation. Une pièce manquante ou une date invalide bloque cette déclaration. L'audit global ne peut être déclaré achevé sans les 24 contextes documentés et ses propres références datées.

**Limite fondamentale :** un contrôle automatique ne sait pas établir l'authenticité, l'exactitude ni la qualité d'un avis externe. Les liens peuvent être syntaxiquement valides sans constituer une preuve. Seul l'examen humain qualifié et la décision de l'autorité compétente permettent de franchir les portes juridique et politique. Le module retourne toujours `certification_automatique_autorisee: false` et `points_supplementaires_autorises: 0`.

## Porte de sortie

Les **24 contextes d'examen (12 × 2)** doivent posséder des conclusions documentées, objections traitées, avis compétents, validations budgétaires et décisions explicites. Les dates de fin sont **conditionnelles** aux mandats, accès aux sources et délais de revue : aucune échéance de clôture n'est certifiée.

**Décision :** ce dossier permet de commencer une revue juridique structurée. Il **ne change ni loi, ni statut du parti, ni fiscalité, ni score du programme**.

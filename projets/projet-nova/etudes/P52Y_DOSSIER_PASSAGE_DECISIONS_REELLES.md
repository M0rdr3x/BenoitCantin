# Projet Nova — P52Y : dossier de remise aux véritables décideurs (sans décision simulée)

**État au 20 octobre 2026 : NON SOUMIS, NON SIGNÉ, SANS BUDGET.** Ce dossier est utilisable comme liste d'actions, mais n'est ni une délégation juridique, ni un engagement de dépense, ni une consultation de prestataires.

## Décision à obtenir, pas seulement un contrôle Python

Le Projet Nova possède déjà les documents budgétaires et les reçus des octets (P52S–P52U), les 39 positions de relecture F09 (P52V), un processus de sélection non adopté (P52W), et les douze préconditions juridiques et de confidentialité (P52X). Ajouter davantage de tests **ne comble pas** l'absence de responsable juridique, d'autorité budgétaire, de professionnel indépendant et de protection GitHub. P52Y donne un ordre exécutable **aux personnes compétentes**, avec pièces attendues et séparation des pouvoirs.

### D01 — Identifier et habiliter le mandant, avant tout contact professionnel

Identifier l'entité juridique exacte, sa capacité de contracter, la délégation authentique des signataires et la qualification du régime de contrats qui lui est applicable. Vérifier auprès des organismes compétents le statut politique/électoral, privé ou public. Un projet politique ne devient pas un parti autorisé ni un organisme public parce qu'un dépôt informatique le présente ainsi. Les X01–X04 et X07 de P52X doivent être instruits et authentifiés hors GitHub. Les décisions doivent être conservées dans un espace à accès limité.

### D02 — Décider si une étude rémunérée peut être financée

Obtenir un montant *réel* autorisé avec devise, taxes et éventuels frais, provenance licite et traitement comptable, portée approuvée, limite de dépenses, autorité de paiement et possibilité d'annulation. Les champs demeurent `null` ou `0` jusqu'à une vraie décision. **Aucun montant n'a été autorisé ni proposé dans P52Y.**

### D03 — Assurer la confidentialité, puis approuver les critères

Identifier un responsable de la protection des renseignements, déterminer les obligations applicables et configurer réellement une boîte ou plateforme de réception sécurisée. Documenter la localisation, les droits d'accès, la conservation et la suppression. Seule une vraie autorité peut approuver les critères S01–S05 de P52W et accepter une procédure de récusation et d'avis défavorable. Aucune offre, identité, CV, déclaration d'intérêts ou devis n'a sa place dans les artefacts publics de la PR. Ne pas contacter de candidats par un robot ni exploiter les répertoires professionnels pour constituer des listes de prospection.

### D04 — Sécuriser GitHub avant toute fusion

L'issue [#135](https://github.com/M0rdr3x/BenoitCantin/issues/135) concerne la protection de `main`. L'issue [#662](https://github.com/M0rdr3x/BenoitCantin/issues/662) concerne les véritables revues indépendantes. Elles restent ouvertes. Consulter aussi `P52Y_SPECIFICATION_PROTECTION_MAIN.md`. L'administrateur habilité doit vérifier en **temps réel** la présence effective de la protection, les rôles et les permissions; un JSON commité ne la crée pas. L'approbation humaine doit être enregistrée sur la PR; un test vert n'est pas une revue.

## Séquence opérationnelle A01–A10

| Action | Responsable fonctionnel à désigner | Préalables |
|---|---|---|
| A01 Identité et statut du mandant | Personne juridique habilitée | X01, X03 |
| A02 Délégation et séparation des pouvoirs | Autorité contractante | A01; X02, X07 |
| A03 Avis sur les règles applicables | Conseil juridique compétent | A01–A02; X04 |
| A04 Financement licite et budget | Responsable financier | A02–A03; X05–X06 |
| A05 Vie privée, réception et conservation | Responsable des renseignements personnels | A02–A03; X09–X11 |
| A06 Critères et gestion des objections | Comité de sélection habilité | A03–A05; X08, X12 |
| A07 Protection réelle de `main` | Administrateur GitHub | Issue #135 |
| A08 Revue GitHub indépendante obligatoire | Responsable de revue habilité | A07; issue #662 |
| A09 Décider si la consultation peut commencer | Autorité contractante | A01–A06 |
| A10 Recevoir avis F09 indépendant et contradictoire | Réviseur et autorité distincte | A09 et mission réellement conclue |

Aucune personne réelle n'est désignée par ces intitulés : ce sont **des fonctions requises**, pas des titulaires nommés. Les deux pistes « mandatement F09 » et « sûreté GitHub » sont indépendantes mais toutes deux nécessaires avant une décision de fusion ou de publication fiscale.

## Sorties et traçabilité

Le registre `P52Y_JOURNAL_DECISIONS_VIDE.json` reste à zéro; il n'est pas un système de signature ni un registre externe de conformité. Le script `scripts/auditer_passage_autorite_nova_p52y.py` vérifie que 10 actions, quatre décisions et les dépendances P52X/P52W restent non approuvées, et produit un plan CSV **sans noms**. Les rapports doivent demeurer agrégés; pour toute décision réelle, utiliser un dépôt confidentiel, un contrôle d'identité et des pièces hors Git, puis faire réviser la publication des éléments non sensibles.

- Exécution documentaire cohérente : code 0, toujours `NO_GO_AUTOMATIQUE`.
- Données incorrectes, ordre invalide, fausse délégation ou certificat imaginé : code 2.
- `--exiger-autorisations` : code 3 tant que les pouvoirs et revues réels manquent.
- Un scénario synthétique ne change jamais ces codes d'habilitation.

## Les blocages réels qui doivent changer

État vérifié : `main` non protégée (0 rulesets), zéro revue humaine de PR #673, 20 preuves F01–F20 non obtenues et 1 320 valeurs financières du modèle fiscal encore inconnues. Ces chiffres ne démontrent pas une fiscalité à deux prélèvements. Le Projet Nova doit obtenir un droit d'engager une expertise, un financement réel, des avis signés et une protection du code, **pas simplement augmenter le nombre de tests automatisés**.

**Aucune modification de SINJIRA, aucun contact professionnel, aucune dépense, aucune fusion et aucune décision fiscale dans ce jalon.**

# Projet Nova — P52Y : demande de configuration administrateur pour protéger `main`

**Spécification à soumettre à une véritable personne ayant l'accès administrateur. Non exécutée.**

## Situation attestée par lecture GitHub le 20 octobre 2026

- Dépôt : `M0rdr3x/BenoitCantin`.
- `main` : SHA `9ed5f70cbe7022f25a679346a1288701f3b09067`, `protected:false` et zéro ruleset, au moment de la vérification.
- [Issue #135](https://github.com/M0rdr3x/BenoitCantin/issues/135) : ouverte, action de protection serveur `main`.
- [Issue #662](https://github.com/M0rdr3x/BenoitCantin/issues/662) : ouverte, action de revue externe.
- [PR #673](https://github.com/M0rdr3x/BenoitCantin/pull/673) : ouverte en brouillon, sans revue; travail fiscal non adopté.

Cette photographie datée **ne garantit pas un état futur**. Un statut `passed` du workflow ne crée aucun réglage GitHub.

## Paramètres à examiner et appliquer après validation des permissions

Dans GitHub → dépôt → Settings → Rules → Rulesets ou Branches (selon les capacités activées), créer une règle **active** couvrant exactement `main`, puis vérifier que la règle est réellement **appliquée** et non seulement enregistrée. Envisager :

1. Exiger les modifications via pull request plutôt que push direct.
2. Exiger au moins une **approbation humaine compétente et indépendante**, à décider par l'autorité; ne pas se contenter d'un bot.
3. Empêcher de forcer les poussées et supprimer la branche, prévoir un refus explicite des contournements non justifiés.
4. Exiger la résolution des discussions et re-demander une approbation lorsque le code pertinent change, sous réserve des capacités GitHub disponibles.
5. Ajouter comme checks obligatoires les **noms exacts** des jobs GitHub réellement observés dans le dépôt, *après* avoir confirmé leur déclenchement, leur fiabilité, leurs permissions et leurs états. Ne pas inventer les identifiants de checks; un workflow peut réussir en étant insuffisant sur le fond.
6. Définir les réviseurs/owners réels dans un mécanisme approprié; ne pas inventer leur identité dans `CODEOWNERS`.

**Ne pas configurer à l'aveugle un workflow documentaire NO_GO comme preuve de validité fiscale.** Un test d'intégrité technique et un avis professionnel sont des portes distinctes.

## Vérification à produire réellement par l'administrateur

Recontrôler via l'interface ou l'API autorisée les rulesets, la protection de `main`, les checks obligatoires, les bypass actors et le droit de pousser directement. Faire vérifier par un second administrateur ou réviseur le résultat et documenter la date. Aucune simulation dangereuse de push ou d'effacement de branche n'est demandée.

Une approbation GitHub ne prouve **pas** l'indépendance de l'expertise F09 : la PR doit rester brouillon tant que les signatures, périmètres, conflits et les 20 preuves fiscales ne sont pas examinés par une véritable autorité.

**P52Y ne modifie ni les protections serveur, ni la branche `main`, ni les membres du dépôt.**

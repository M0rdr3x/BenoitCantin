# SINJIRA — Checklist administrateur GitHub pour les protections production

> Statut : préparation technique non destructive.  
> Cette checklist ne constitue ni une approbation de migration, ni une autorisation de merge, ni une autorisation de déploiement production.
>
> Principe : **L’HUMAIN AVANT TOUT. PROTÉGER SANS SURVEILLER.**

## Objectif

Consolider en un seul endroit les vérifications administrateur suivies par :

- **#135** — protection serveur de `main`;
- **#439** — protection de l’Environment GitHub `production`.

Ces deux frontières sont complémentaires :

1. `main` empêche qu’un code non validé entre dans la branche de référence;
2. l’Environment `production` protège les jobs qui peuvent écrire en production après fusion.

L’une ne remplace jamais l’autre.

---

## 1. Protection serveur de `main` — #135

Dans **GitHub → Settings → Rules → Rulesets** ou **Settings → Branches**, configurer une protection réellement appliquée à `main`.

### Exigences minimales

- [ ] Exiger le passage par une pull request avant fusion.
- [ ] Interdire les force-push.
- [ ] Interdire la suppression de `main`.
- [ ] Exiger la réussite des checks CI universels appropriés.
- [ ] Exiger la résolution des conversations si cette règle correspond au fonctionnement du dépôt.
- [ ] Vérifier que les administrateurs ne disposent pas d’un contournement involontaire de la règle, lorsque la configuration GitHub permet ce choix.
- [ ] Ne pas imposer un nombre d’approbations humaines impossible à satisfaire pour un dépôt mono-mainteneur.

### Checks universels actuellement adaptés

Les checks suivants ont été identifiés comme appropriés à une règle globale parce qu’ils s’exécutent sur les PR vers `main` et ne dépendent pas du ledger de migrations production :

- `SINJIRA — garde secrets Git / no-committed-secrets`
- `Tests navigateur SINJIRA / Contrat sécurité CI navigateur`
- `Validation du site SINJIRA / Contrat sécurité validation site`

### Checks à ne pas rendre required globalement pour l’instant

Ne pas rendre required au niveau global :

- `Supabase production — PRÉVOL`;
- les workflows qui appellent `validate_production_migration_ledger.py`;
- les workflows limités par `paths:` à un domaine particulier.

Raisons :

- les checks ledger sont volontairement rouges tant que les migrations futures restent hors du reviewed batch;
- un workflow `paths:` peut être absent d’une PR sans rapport et laisser un required check impossible à satisfaire.

### Preuve attendue pour fermer #135

Une preuve administrateur doit confirmer au minimum l’un des deux états suivants :

- `main` apparaît comme protégée côté GitHub; ou
- un ruleset actif s’applique effectivement à `main` avec les règles ci-dessus.

La présence de workflows CI n’est pas une preuve de protection serveur.

---

## 2. Environment `production` — #439

Dans **GitHub → Settings → Environments → production** :

- [ ] Vérifier que l’Environment `production` existe.
- [ ] Vérifier quels workflows sensibles l’utilisent.
- [ ] Activer une approbation humaine avant exécution des jobs production lorsque le plan GitHub et les réglages du dépôt le permettent.
- [ ] Vérifier que les workflows sensibles ne peuvent pas contourner cet Environment.
- [ ] Conserver les confirmations textuelles exactes déjà prévues dans les `workflow_dispatch` : elles sont un verrou supplémentaire, pas un remplacement du reviewer.
- [ ] Documenter explicitement si le plan GitHub ne permet pas les required reviewers.

### Important

Un job qui contient `environment: production` prouve uniquement qu’il référence cet Environment.

Cela **ne prouve pas**, à lui seul, qu’un reviewer humain est réellement requis dans les réglages GitHub.

### Preuve attendue pour fermer #439

La vérification administrateur doit consigner :

- Environment `production` actif;
- règle d’approbation humaine réellement configurée, si disponible;
- absence de contournement évident par les workflows sensibles;
- sinon, limitation du plan GitHub documentée explicitement.

---

## 3. Ordre de défense attendu

Pour une future écriture production SINJIRA :

1. code introduit dans `main` uniquement par PR protégée;
2. checks universels requis verts;
3. revue humaine des migrations concernées terminée sur les blobs exacts;
4. reviewed batch / ledger mis à jour seulement après cette décision;
5. lancement manuel du workflow production avec confirmation exacte;
6. franchissement de l’Environment `production` et de son approbation humaine lorsqu’elle est disponible;
7. prévol/revalidation de la cible;
8. écriture production;
9. postflight vérifiant l’état réellement appliqué.

---

## 4. État lié à la PR #435

Au HEAD de revalidation `b3495cf3216f8157e6014d29cf1564b0c7c57c78` :

- PR #435 toujours draft et non fusionnée;
- 43 migrations de #438 restent soumises à décision humaine;
- aucune migration SQL n’a changé depuis le SHA gelé `d424f26145422ea9f4dc23a087b155706bd6da51`;
- aucune promotion partielle ne doit être déduite d’une décision par lot;
- au moment d’une future promotion, les **57 migrations futures locales** attendues doivent être revalidées ensemble contre le builder;
- les checks ledger/reviewed batch volontairement rouges ne doivent pas être transformés en required checks globaux tant que cette frontière n’est pas résolue.

---

## 5. Règle de gouvernance

Cette checklist prépare les décisions et réduit les erreurs de configuration.

Elle ne remplace pas :

- la décision humaine #438;
- la protection réelle de `main`;
- les secrets GitHub Actions hors dépôt suivis par #240;
- l’éligibilité HIBP suivie par #437;
- une approbation humaine de l’Environment `production`;
- les vérifications post-déploiement.

Aucune étape de cette checklist ne doit être interprétée comme une autorisation implicite de production.

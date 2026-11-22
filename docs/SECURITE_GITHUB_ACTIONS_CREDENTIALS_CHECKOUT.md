# Sécurité CI GitHub — empêcher la persistance du jeton de checkout

**Candidat GitHub, non fusionné, aucun changement de configuration serveur.**

## Observation vérifiée au 21 novembre 2026

- `main` : branche rapportée `protected: false` par l'API GitHub.
- Rulesets visibles du dépôt : `[]`, donc aucune règle de revue/CI obligatoire active.
- `scripts/validate_workflow_supply_chain.py` contrôlait déjà les actions
  épinglées à des SHA, `pull_request_target` et des permissions explicites,
  mais **n'exigeait pas** que les étapes `actions/checkout` désactivent
  la persistance du jeton GitHub.
- Le défaut de `actions/checkout` est `persist-credentials: true`.
  Dans un environnement qui exécute du code fourni par une PR, cette
  persistance augmente l'exposition des credentials si une étape est
  compromise. La documentation GitHub indique que la version 6 stocke
  ces credentials sous `$RUNNER_TEMP`; **ce n'est pas une preuve
  de protection totale si l'option reste activée**.

## Correction préventive dans la PR

Le scanner existant vérifie chaque `actions/checkout@<SHA-40>` de
chaque workflow de `.github/workflows/` :

1. `with:` doit appartenir à **cette étape précise**.
2. Il doit comporter exactement une déclaration
   `persist-credentials: false`, au bon niveau YAML.
3. Un `false` écrit dans un commentaire, dans `run: |`, dans
   `env:`, dans une étape voisine, sous une mauvaise indentation
   ou accompagné d'un `true` ne peut pas valider le contrat.
4. Les références d'actions à des étiquettes mobiles restent interdites;
   les déclencheurs `pull_request_target` restent interdits.
5. Le contrôle est hors réseau, n'accède à aucun secret et ne tente
   aucune écriture dans GitHub.

Le workflow `.github/workflows/workflow-supply-chain-security.yml`
est désormais émis sur **toute PR vers `main`** et tout push `main`,
sans filtrage `paths:`. Il conserve des permissions `contents: read`,
une action Checkout et une action Setup Python épinglées à des SHA
immuables, et ne transmet pas de secrets.

### Exception d'écriture NOVA résolue sans désactiver la fonctionnalité

Le premier scan de 195 workflows a signalé une seule violation :
`.github/workflows/nova-seo-normalize.yml`, étape de checkout du job
`commit`, utilisait intentionnellement `persist-credentials: true`
pour publier les changements SEO sur la branche historique
`nova-a1-reference-documents`. Plutôt que de désactiver le scan ou de
casser l'ancien mécanisme d'écriture :

- Le checkout du job `commit` passe à `persist-credentials: false`.
- `contents: write` demeure **uniquement** sur ce job explicitement
  borné à la branche NOVA ; le job de normalisation conserve `read`.
- Le token `${{ github.token }}` est fourni **seulement à l'étape de
  `git push`**, sous la variable d'environnement `SEO_PUSH_TOKEN`.
- Un `GIT_ASKPASS` créé avec `umask 077` et permissions `0700`
  transmet le jeton pour cette seule opération. Les helpers Git
  existants sont neutralisés et le script temporaire est supprimé avec
  `trap ... EXIT`, même en cas d'échec.
- `scripts/validate_nova_seo_workflow_security.py` interdit toute
  restauration de la persistance, les jetons hors de l'étape finale,
  la suppression du nettoyage et les permissions faibles du script.
  Le code de normalisation historique ne s'exécute toujours **jamais**
  dans le job avec `contents: write`.

Cette migration conserve le `git push` vers la **seule branche NOVA
prévue** mais ne constitue pas un déploiement SINJIRA ni une
réactivation des services NOVA sur le site principal.

**Séparation du contrôle de sécurité et des anciens tests d'interface :**
le workflow universel `workflow-supply-chain-security.yml` exécute
désormais aussi **les 32 mutations négatives du writer NOVA** et son
contrat statique. Il peut donc refuser une régression de credentials
sur chaque PR même si le workflow historique `Validation Projet Nova`
échoue pour une raison indépendante.

**Constat de compatibilité :** le workflow `Validation Projet Nova`
exécute `scripts/check_nova_a1.py`, qui exige encore un logo NOVA sur
la page d'accueil. Le projet NOVA ayant été retiré de cette page, ce
contrôle visuel ancien est incompatible avec le site actuel. Ce
résultat n'est pas une preuve que le nouveau contrôle de credentials
est défectueux. **Ne pas masquer cette erreur, ne pas remettre NOVA à
l'accueil et ne pas effacer les règles de sécurité pour obtenir un
résultat vert**. Une réconciliation séparée des tests historiques
restera nécessaire avant toute fusion ayant des contrôles obligatoires.

## Limites et vérifications avant protection de branche

Ce garde réduit l'exposition des credentials aux étapes GitHub Actions,
mais n'empêche pas l'exfiltration depuis une étape volontairement
privilégiée ni une attaque sur une action déjà compromise. Les environnements
de production doivent conserver des approbations séparées et des jetons à
privilèges minimaux. Un analyseur statique n'est pas un parseur YAML complet;
la revue d'un workflow modifié reste nécessaire.

Le contexte de job à envisager comme contrôle obligatoire est
`Contrat de provenance et de permissions GitHub Actions`,
source **GitHub Actions**, sous réserve de vérifier l'identité exacte du
check et son émission sur une PR témoin. Éviter les checks homonymes et
ceux filtrés par chemins.

**Action admin non automatisable par cette intégration** : dans
GitHub > Settings > Rules > Rulesets, protéger `main` avec PR et revue
indépendante obligatoires, contrôles requis (dont ce job après vérification),
interdiction des poussées forcées/suppression, et absence de contournement
général. Vérifier ensuite que `main.protected = true` ou qu'un ruleset
effectivement appliqué refuse les fusions non revues. Le fait qu'un workflow
réussisse **ne remplace pas** cette protection côté serveur.

## Documentation externe

- https://github.com/actions/checkout#usage
- https://cheatsheetseries.owasp.org/cheatsheets/GitHub_Actions_Security_Cheat_Sheet.html
- https://docs.github.com/en/actions/reference/security/secure-use
- https://github.com/M0rdr3x/BenoitCantin/issues/135

**Aucune branche principale, permissions de dépôt, règle GitHub, clé,
base de données, compte, configuration Pages ou production modifiés.**

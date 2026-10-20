# Projet Nova — rendre les sondages visibles sur le site

**État au 20 octobre 2026 : pas encore en ligne.** Les deux questionnaires sont
dans la [PR #639](https://github.com/M0rdr3x/BenoitCantin/pull/639) en brouillon,
et sont absents de la branche `main`. La page publique
[Projet Nova](https://www.benoitcantin.com/projets/projet-nova/) ne contient pas
encore la section demandée.

## Emplacements exacts après publication sécurisée

- Accueil général : `https://www.benoitcantin.com/#sondages-nova`
- Accueil Projet Nova : `https://www.benoitcantin.com/projets/projet-nova/#consultations`
- Questionnaire référendaire **consultatif et non officiel**, 40 questions :
  `https://www.benoitcantin.com/projets/projet-nova/consultation-40.html`
- Sondage citoyen, 64 propositions :
  `https://www.benoitcantin.com/projets/projet-nova/sondage.html`
- Icône approuvée :
  `/projets/projet-nova/assets/nova-sondage-icone.webp`

**Les réponses ne sont pas collectées** dans cette préparation. Le contrôle
18+ est autodéclaré, sans vérification documentaire. Ne pas présenter les
résultats comme représentatifs ou comme ceux d'un référendum légal.

## Ce que le propriétaire du dépôt doit approuver

1. Consulter l'[incident de sécurité Pages #450](https://github.com/M0rdr3x/BenoitCantin/issues/450)
   et le runbook détaillé [PAGES_CONTROLLED_CUTOVER.md](PAGES_CONTROLLED_CUTOVER.md).
   Conserver une copie des réglages Pages et préparer une période de changement.
2. Vérifier la protection de `main` et les contrôles obligatoires, notamment
   **Construire puis auditer Pages sans déployer** et
   **Garde de promotion — Source Pages conforme exigée**.
3. Coordonner le passage de
   [Settings → Pages](https://github.com/M0rdr3x/BenoitCantin/settings/pages)
   à **GitHub Actions** avec la revue et l'intégration atomique du nouveau workflow
   isolé. **Ne pas basculer Source seule** alors que `main` ne contient pas
   encore le workflow : risque d'interruption.
4. Une fois la fusion de la PR de publication explicitement approuvée,
   relever le SHA complet de `main`; lancer
   [Pages — déploiement isolé explicitement approuvé](https://github.com/M0rdr3x/BenoitCantin/actions/workflows/deploy-pages-controlled.yml)
   en `DRY_RUN`, `NOT_CONFIRMED`, SHA exact. Valider les audits de l'artefact
   Jekyll isolé `_site`. Le workflow ne téléverse **jamais** la racine `.`.
5. Si le DRY_RUN est approuvé, autoriser séparément `PUBLISH` avec
   `ACTIONS_ONLY` et le même SHA exact. Le changement reste soumis aux
   autorisations d'environnement et aux attestations de Pages.
6. Vérifier sur le domaine réel les deux accueils, les deux questionnaires et
   l'icône (200, MIME correct et octets du SHA), ainsi que **14 chemins
   techniques** en 404/410, notamment `/supabase/config.toml`,
   `/tests/e2e/test_public_site.py` et `/mobile-native/App.tsx`.
   Toute anomalie bloque la clôture; ne jamais rétablir `path: .`.

Les nouvelles vérifications `scripts/validate_nova_public_access.py`
contrôlent les deux cartes et icônes cliquables, la collecte fermée et
l'intégrité des ressources dans `_site`. Elles sont exécutées en CI et en
DRY_RUN/PUBLISH; ce n'est pas une autorisation de collecte.

**Après publication, l'issue #675 reste ouverte** avant toute activation
d'envoi d'opinions politiques : confidentialité, droit de retrait après
agrégation et conservation doivent être examinés et approuvés.

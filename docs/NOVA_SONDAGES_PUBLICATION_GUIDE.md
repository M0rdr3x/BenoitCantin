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

## Prévisualiser les questionnaires sans modifier le domaine

Sur la PR #639, ouvrir le dernier workflow réussi **SINJIRA — catalogues
Romans Jeux Logiciels**, puis sa section **Artifacts** et télécharger
`nova-sondages-apercu-pr-639-<SHA>` (conservé **7 jours**). Il contient
cinq PNG de **préproduction locale seulement** :

1. Carte avec l'icône officielle sur l'accueil général;
2. Cartes des deux consultations sur l'accueil Projet Nova;
3. Introduction du questionnaire référendaire de 40 questions;
4. Introduction du sondage citoyen de 64 propositions.
5. Aperçu des résultats publics, indiquant l'absence réelle de votes publiés.

Le fichier `LISEZ-MOI.txt` identifie le commit exact et le run CI.
Ces images n'indiquent **pas** que le contenu est en ligne.
La capture fonctionne uniquement en Chromium après les tests de
navigation réussis, n'envoie aucune opinion et ne charge aucun compte.
Le workflow ne téléverse que les cinq PNG et le fichier d'explication,
avec des permissions GitHub `contents: read`, et **jamais**
l'artefact entier du dépôt, les fichiers techniques ou le site compilé.


### Répartition collective publiquement vérifiable

Le portail Nova possède dans la PR #639 `resultats-sondages.html` et son registre public `data/resultats-sondages-publics-v1.json`. Aucune donnée réelle n'existe encore : le fichier est fermé (`not_open`). Les résultats ne peuvent être débloqués simplement en modifiant l'interface : la CI refuse toute statistique avant une approbation indépendante de #675, impose un total de 30 participants au minimum et une suppression de chaque répartition qui risquerait de divulguer un effectif entre 1 et 9. Une réponse individuelle n'est jamais exportable par le registre public.

La publication contrôlée vérifie maintenant **27 routes publiques** (dont la page résultats et ses deux fichiers) en HTTP 200 direct et au MIME attendu, **14 routes techniques** en HTTP 404/410, puis les octets SHA des **28 ressources CDN critiques**. Ces contrôles ne sont exécutés en production qu'après un PUBLISH réellement autorisé; `main` et la configuration Pages restent inchangés ici.


## Accès aux résultats publics sur les deux accueils

L'accueil général propose désormais un troisième bouton dédié aux **résultats publics et à la méthode**, à côté des questionnaires 40 et 64. L'accueil Projet Nova affiche ce lien immédiatement sous les deux cartes et explique que les réponses individuelles, les identités et les votes de démonstration ne sont pas publiés. Le contrôle `validate_nova_public_access.py` exige le lien sur **les deux accueils**. La page de résultats affiche pour l'instant « Aucun résultat publié » : aucun décompte ne peut être inventé et le protocole de collecte d'opinions politiques reste bloqué par #675. Les interfaces restent sur la PR #639 tant que le cutover Pages #450 n'est pas approuvé.

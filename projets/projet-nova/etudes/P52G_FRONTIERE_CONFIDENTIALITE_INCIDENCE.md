# Projet Nova — P52G : confidentialité des simulations fiscales dans les artefacts GitHub

**18 octobre 2026 · Mesure de sécurité documentaire / code candidat · NON ADOPTÉ · NO_GO**

## 1. Défaut corrigé

Les modèles [P52D](./P52D_METHODE_INCIDENCE_MENAGES_ENTREPRISES.md) et [P52E–P52F](./P52E_NORME_CANDIDATE_NON_APPAUVRISSEMENT.md) comparent **42 cas non représentatifs** (30 ménages et 12 entreprises) dans deux régimes et trois trajectoires. Leurs résultats détaillés comprennent des **soldes, variations monétaires et décompositions par catégorie de cas**.

Jusqu'à P52F, les workflows GitHub calculaient et archivaient les rapports complets, avec leurs listes `resultats` ou `cas`. **Aujourd'hui les 720 données sont absentes : il n'y a pas de fuite constatée.** Toutefois, une future entrée chiffrée dans le gabarit aurait pu entraîner l'archivage de détails financiers par cas dans un artefact GitHub. La confidentialité doit être intégrée **avant** tout renseignement de l'étude.

## 2. Correction logicielle livrée

Les scripts suivants possèdent chacun une option `--rapport-agrege` :
- `scripts/comparer_incidence_fiscale_nova_p52d.py`;
- `scripts/evaluer_garde_fous_revenu_nova_p52e.py`.

Le mode réalise les calculs en mémoire, puis **reconstruit un objet JSON neuf à partir d'une liste explicite de champs autorisés**, au lieu de retirer quelques noms de champs sensibles du rapport complet. Cette stratégie de **liste blanche** limite la propagation accidentelle d'un nouveau champ détaillé ajouté ultérieurement au calculateur.

### Informations conservées

P52D conserve uniquement : nombre de régimes, scénarios, cas, montants manquants, cas conditionnellement calculables, interdictions de généralisation, de fusion et de publication, plus la décision `NO_GO_AUTOMATIQUE`.

P52E conserve uniquement : les mêmes totaux structurels, les nombres globaux de cas signalant une perte ou un changement non fiscal, la répartition agrégée des statuts, les limites sur la représentativité et la décision `NO_GO_AUTOMATIQUE`.

### Informations exclues des exports agrégés

- Aucune ligne par catégorie de ménage ou d'entreprise;
- aucun montant de revenu, prestations, taxe, salaire, chiffre d'affaires, subvention ou solde;
- aucune différence monétaire ou décomposition par cas;
- aucune référence de fichier ou URL propre à un cas;
- aucune liste de cas avec identifiant ou catégorie.

Les champs `rapport_agrege_sans_details: true` et `aucun_montant_individuel_exporte: true` indiquent uniquement **le format de sortie**, **pas** une certification juridique d'anonymisation.

## 3. Utilisation de la CLI

Depuis la racine du dépôt, export destiné aux tests CI et à un partage interne limité :

```bash
python scripts/comparer_incidence_fiscale_nova_p52d.py \
  --gabarit projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json \
  --rapport-agrege --rapport p52d_resume_agrege.json

python scripts/evaluer_garde_fous_revenu_nova_p52e.py \
  --gabarit projets/projet-nova/etudes/P52D_GABARIT_INCIDENCE_MENAGES_ENTREPRISES.json \
  --rapport-agrege --rapport p52e_resume_agrege.json
```

Le **mode local détaillé** sans `--rapport-agrege` reste disponible à des experts dûment habilités pour examiner un cas *fictif ou public*, mais les sorties complètes ne doivent **jamais** être versées dans un dépôt, un ticket, un commentaire PR, un artefact partagé ou des journaux CI. Ne pas introduire des dossiers fiscaux personnels, noms, adresses, numéros d'impôts, relevés bancaires ou autres renseignements identifiants dans le dépôt GitHub.

Les deux modes stricts d'origine restent actifs : ils renvoient le code **3** faute de preuve indépendante de complétude ou de non-appauvrissement, **sans devenir une approbation juridique ou politique**. Le mode agrégé n'assouplit pas ces conditions.

## 4. Tests de confidentialité et limites

Les suites contiennent maintenant :
- **P52D : 37 tests** (31 antérieurs et 6 spécifiques à P52G);
- **P52E–P52F : 41 tests** (35 antérieurs et 6 spécifiques à P52G).

Les essais P52G vérifient un cas fictif entièrement rempli avec une variation distinctive de **−7 777,77 $** : le calcul détaillé la conserve pour l'analyste, mais **aucun montant ni catégorie du cas ne figure dans l'export agrégé**. Ils vérifient également l'absence de fuite si une métadonnée inattendue apparaît, ainsi que le maintien de `NO_GO_AUTOMATIQUE` et du **refus strict**.

Les workflows `.github/workflows/validate-nova-p52d.yml` et `validate-nova-p52e.yml` sont modifiés pour appeler directement `--rapport-agrege` et n'archiver que ces fichiers. **Des agrégats peuvent encore présenter un risque de réidentification lorsque les groupes sont minuscules ou les données personnelles connues ailleurs.** La présente mesure **ne constitue donc pas une autorisation de traiter des microdonnées fiscales réelles**. Un avis de protection des renseignements personnels, une base légale, le contrôle des accès, une réduction du risque des petites cellules et une politique de conservation doivent précéder tout traitement réel.

## 5. Conséquences politiques et scientifiques

Aucun des **720 montants inconnus** n'a été renseigné; les **20 preuves P52A** restent non validées; aucune pondération de population ni analyse de coût des services n'a été produite. **Un résultat agrégé n'est pas plus représentatif qu'un rapport par cas**. Les alertes de pertes concernent les seuls cas hypothétiques et ne démontrent ni une amélioration du revenu disponible des Québécois, ni la soutenabilité d'une réforme à deux prélèvements.

Ce correctif ne modifie ni les `official/reference`, ni les pages publiques, ni la branche `main`. Les revues indépendantes et les autorisations administratives restent distinctes. **PR640 NE PAS FUSIONNER. Aucune publication, collecte, fusion ni adoption automatique.**

# P55V — Premier comparateur opérationnel avant / après pour les ménages et les entreprises

**7 novembre 2026.** Complément exécutable aux jalons P55S, P55T et P55U du Projet Nova. Ce jalon crée une **capacité de calcul**, pas une conclusion économique ou un taux fiscal adopté.

## Décision et avancement

Le baromètre P55N reste **53 % de complétude estimée** (fourchette indicative 45 à 60 %). La source d'incertitude majeure est connue : **600 montants budgétaires P52B et 720 montants d'incidence P52D restent non renseignés**. Il ne serait pas sérieux de les remplacer par des zéros ni de présenter un gain fictif comme une promesse du projet.

Le changement de fond de P55V consiste à permettre **la comparaison arithmétique complète d'un cas une fois ses données remplies**, ou de rendre visibles les données encore manquantes dans un dossier partiel. Les résultats restent strictement **conditionnels et non certifiés** jusqu'à la vérification indépendante des assiettes, crédits, prestations, coûts en nature et effets de prix.

## 1. Deux régimes, trois scénarios, deux groupes

Le comparateur reçoit une année fiscale **2026**, un régime (**Québec dans le Canada** ou **Québec souverain hypothétique**), une trajectoire (**central, prudent ou stress**) et un profil parmi les **cinq catégories de ménages** et les **deux catégories d'entreprises** du gabarit P52D.

Pour les ménages, les huit postes exigés de chaque situation « actuel / proposé » sont : revenu brut, prestations fédérales, prestations Québec/État, impôt fédéral, impôt Québec/État, cotisations obligatoires, prélèvements municipaux directs et taxes à la consommation supportées.

Pour les entreprises, les dix postes exigés sont : chiffre d'affaires, coûts d'exploitation hors salaires, masse salariale, impôts fédéral et Québec/État, cotisations employeur, prélèvements municipaux, taxes à la consommation non recouvrables, subventions reçues et charge additionnelle hypothétique anti-évasion.

**Aucun barème fiscal du Projet Nova n'est imposé par le logiciel.** Les montants doivent être fournis explicitement, poste par poste. Un résultat monétaire ne remplace pas un travail de qualification fiscale, de simulation des transferts ou d'analyse des entreprises.

### Différence essentielle entre le revenu disponible et le calcul du comparateur

Le [Gouvernement du Québec](https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible) définit le revenu disponible de sa simulation à partir du revenu, des impôts, des cotisations et des aides. Il précise que son calcul exclut certaines catégories de revenus, de déductions et de crédits. L'[Institut de la statistique du Québec](https://statistique.quebec.ca/fr/document/revenu-disponible) fournit les définitions statistiques générales, et [ses publications méthodologiques](https://statistique.quebec.ca/fr/produit/publication/revenu-disponible-par-habitant-2024-quebec-et-regions) rappellent que la valeur des services publics **en nature** et les différences territoriales de coût de la vie ne sont pas intégrées à l'indicateur général.

Le comparateur affiche donc le **flux direct partiel** et, séparément, un flux **après les taxes à la consommation supportées**. Le second n'est **pas** le revenu disponible officiel. Les services de santé et d'éducation, la répercussion des impôts sur les prix, les coûts de logement et les besoins essentiels nécessitent un travail supplémentaire. Pour les entreprises, le calcul est un **flux illustratif**, et non un bénéfice fiscal, une trésorerie auditée ou une prévision d'emploi.

## 2. Un outil qui fonctionne déjà sur des données complètes *expressément fictives*

`P55V_EXEMPLE_COMPARAISON_FICTIVE_AVANT_APRES.json` fournit deux cas de calculs de démonstration : un ménage modeste et une PME, tous deux explicitement fictifs, avec la mention `FICTIF_EXPLICITE_NON_SOURCE` pour chaque valeur. Ils servent à vérifier les opérations arithmétiques et le traitement des taxes, **sans** prétendre qu'un ménage ou qu'une entreprise réelle obtiendrait ces résultats.

```bash
python scripts/comparer_cas_fiscaux_nova_p55v.py \
  --jeu projets/projet-nova/etudes/P55V_EXEMPLE_COMPARAISON_FICTIVE_AVANT_APRES.json \
  --bilan-public /hors_git/p55v_couverture_publique.json \
  --rapport-technique /hors_git/p55v_exemple_technique.json
```

Le **rapport public** indique le **nombre** de cas complets, incomplets et de valeurs manquantes, mais **n'exporte aucun gain chiffré de démonstration**. Le rapport technique, à conserver hors publication, énumère les résultats explicitement **conditionnels**, avec les labels de non-représentativité et d'absence de certification. Les rapports ne contiennent pas les valeurs de revenu brut individuelles d'entrée.

## 3. Un premier dossier documentaire partiel réellement examiné

`P55V_CAS_PARTIEL_OFFICIEL_2026_A_COMPLETER.json` contient **un seul revenu brut de 50 000 $**, repris de l'**hypothèse d'exemple** de la [page gouvernementale de calcul du revenu disponible mise à jour le 17 juin 2026](https://www.quebec.ca/finances-impots-et-taxes/credits-impots-deductions/estimer-revenu-disponible).

**Important : le 50 000 $ est le revenu supposé d'une illustration gouvernementale, pas le revenu réellement constaté d'un citoyen.** Sa provenance est déclarée pour le champ « actuel », et toutes les autres composantes nécessaires aux deux situations restent inconnues. Dans le dossier `cas-p01`, le comparateur constate ainsi **1 valeur explicitement fournie, 15 valeurs `null`**, **0 cas calculable** et **0 effet Nova attribuable**. Il ne déclare pas que les 15 valeurs manquantes seraient nulles, et ne modifie aucun des 720 postes du fichier P52D.

```bash
python scripts/comparer_cas_fiscaux_nova_p55v.py \
  --jeu projets/projet-nova/etudes/P55V_CAS_PARTIEL_OFFICIEL_2026_A_COMPLETER.json
```

Le code accepte aussi les dossiers en mode `CANDIDAT_DOCUMENTE_NON_AUDITE` lorsque **chaque montant non nul possède une référence HTTPS déclarée**. Il ne vérifie toutefois **pas** le contenu des liens ni leur conformité aux règles fiscales. Cette provenance déclarée n'est donc **jamais** qualifiée d'audit indépendant ni de preuve suffisante pour faire évoluer un score de complétude.

## 4. Garde-fous de publication et décision

Le validateur exige :
- l'année, la catégorie, le régime, le scénario et le périmètre exacts de chaque cas;
- les huit ou dix champs dans les deux états, avec **`null` lorsqu'une valeur manque**;
- une provenance explicite et appropriée à chaque valeur présente;
- aucune identification nominative et aucune validation légale supposée;
- l'interdiction de publier un résultat fictif comme un gain public;
- l'absence de tout passage automatique à la certification.

Le schéma limite le nombre de cas par fichier et n'accepte que des montants décimaux déclarés sous forme de texte afin d'éviter les flottants imprécis. Les sorties préexistantes ne peuvent pas être écrasées. **Aucun outil ne télécharge de dossier privé ni n'envoie les données vers un service externe.**

La commande `--exiger-faisabilite` doit toujours retourner **3 (`NO_GO_AUTOMATIQUE`)** tant que les valeurs ne constituent pas une étude financière et juridique indépendante. Une erreur de format ou de provenance retourne le code **2**. Les tests automatisés vérifient ces refus ainsi que l'exactitude des calculs synthétiques.

## 5. Chemin crédible vers davantage de complétude

P55V constitue le **premier pont informatique réutilisable** entre les références officielles collectées et les cas « actuel / proposé » de P52D. Pour gagner réellement des points dans P55N, il faudra : compléter les champs d'un **même profil**, harmoniser les sources et les années, formuler la proposition fiscale dans des textes juridiquement cohérents, contrôler les prestations et les prix, vérifier le coût du maintien des services, et confronter ces résultats à **deux budgets décennaux entièrement sourcés**. Une contre-expertise externe signée demeure indispensable.

**Maturité maintenue : 53 % estimatifs.** Aucune nouvelle taxe adoptée ni économie certifiée, aucune réduction d'emploi ou de service présumée, protections du pouvoir d'achat maintenues, SINJIRA inchangé, aucune dépense ou prise de contact, aucune fusion dans `main`. **`NO_GO_AUTOMATIQUE`.**

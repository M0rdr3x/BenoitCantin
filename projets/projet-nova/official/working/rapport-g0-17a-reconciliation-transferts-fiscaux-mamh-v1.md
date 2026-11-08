# Projet Nova–Sinjira — G0.17a : intégrité des sources MAMH et financement des municipalités

**8 novembre 2026 · Rapport de travail technique · Préparation Nova : 47/100, soit 53 points restants.**

**Statut : des transferts fiscaux de 2024 sont visibles dans une publication gouvernementale; la version 2025 du même fichier reste en litige technique.** Aucun taux Nova, financement nouveau, économie municipale, mise en vigueur ou audit externe du programme n'est validé.

## 1. Pourquoi cette étape corrige la trajectoire

Les phases G0.16w à G0.16z sont **déjà présentes dans GitHub** : elles décrivent les assiettes fiscales, les flux provinciaux et municipaux, un avant-projet légal et un cadre décennal. G0.16z avait déjà documenté **une incohérence de millésime** dans une source MAMH plus générale. G0.17a est un deuxième contrôle indépendant sur une autre ressource, le **Sommaire des transferts fiscaux**.

Le [site officiel de fiscalité municipale du MAMH](https://www.quebec.ca/gouvernement/gestion-municipale/finances-fiscalite-municipales/fiscalite/encadrement) affiche le lien **« Sommaire des transferts fiscaux 2025 »**. Le PDF accessible à la même adresse présente deux vues divergentes dans le navigateur de recherche :

- **Texte extrait** : « Sommaire des transferts fiscaux 2025 », © MAMH **2026**, avec un tableau des paiements décrits pour 2025.
- **Rendu des pages PDF 3 et 4** : couverture du tableau **« Sommaire des transferts fiscaux 2024 »** et données explicitement **2024**.

**Adresse concernée :** https://cdn-contenu.quebec.ca/cdn-contenu/adm/min/affaires-municipales/publications/finances_indicateurs_fiscalite/information_financiere/SOM_transferts_fiscaux.pdf

Il ne s'agit pas d'affirmer que le ministère a publié des montants erronés. **Le mécanisme d'accès aux sources présente des éditions discordantes pour un URL mutable**. La tentative de téléchargement direct du fichier pour en obtenir les octets et l'empreinte SHA-256 a échoué dans l'environnement courant. La version 2025 ne peut donc pas être comparée comme si elle avait été inspectée visuellement à partir du même document figé.

## 2. Transferts fiscaux 2024 : valeurs contrôlées à l'écran

Le tableau visible de la **page 3**, index PDF **2**, est intitulé « Transferts fiscaux en faveur des organismes municipaux du Québec ». Il couvre **uniquement les programmes fiscaux explicitement recensés par le MAMH**, et non toutes les recettes ni tous les transferts municipaux. Il décrit des **montants versés en 2024** au titre de ces programmes.

| Catégorie d'organismes municipaux | Total programmes recensés (2024) | Dont partage de TVQ |
| --- | ---: | ---: |
| Moins de 2 000 habitants | 79 665 308 $ | 32 404 720 $ |
| 2 000 à 9 999 habitants | 89 521 975 $ | 62 289 357 $ |
| 10 000 à 24 999 habitants | 74 014 520 $ | 53 383 394 $ |
| 25 000 à 99 999 habitants | 109 859 973 $ | 82 761 508 $ |
| 100 000 habitants et plus | 222 544 163 $ | 214 161 020 $ |
| **Sous-total des programmes présents dans ce tableau** | **575 605 939 $** | **444 999 999 $** |

La somme des cinq tranches de population a été recalculée et les six colonnes par tranche concordent. Les autres programmes visibles totalisent ensemble **130 605 940 $** : compensations pour les terres publiques, redevances de ressources naturelles, péréquation et dispositifs de neutralité.

Les **onze grandes villes** détaillées à la page 4 sont des **éléments du groupe 100 000 habitants et plus**, et non une sixième ligne à additionner au total. Par exemple, Montréal figure pour **91 995 476 $** et Québec pour **28 418 885 $** dans cette sous-liste. Le tableau n'établit **pas les débits et crédits de chaque relevé bancaire municipal**, même si sa description ministérielle parle des versements exécutés.

## 3. Chiffres 2025 : texte extrait en quarantaine

L'extraction textuelle affiche :

- **777 824 703 $** comme somme arithmétique de cinq tranches.
- **647 000 012 $** comme somme de la colonne partage d'une partie de la TVQ.
- Un tableau ne présentant pas toutes les colonnes de neutralité du tableau visuellement attribué à 2024.

Ces sommes sont **cohérentes à l'intérieur du tableau extrait**, mais **elles ne sont pas présentées comme observations 2025 vérifiées par G0.17a**, puisque la capture visuelle de la même URL demeure celle de 2024. Le registre les conserve dans un bloc explicite **`version2025_text_quarantined`**, tandis que les champs « 2025 vérifié », « croissance 2024→2025 » et « remplacement 2026–2027 » restent **`null`**.

Il est interdit de publier le pourcentage d'évolution entre **575,606 M$** et **777,825 M$**, ou d'en tirer une économie, jusqu'à ce qu'une copie immuable de chaque édition — millésime, pages et empreinte SHA-256 — soit disponible et que les rubriques soient reconnues comparables.

## 4. Ce que cela change pour l'engagement fiscal Nova

Le Projet Nova propose de remplacer la fiscalité actuelle par deux instruments principaux : impôt sur le revenu et prélèvement anti-paradis fiscaux, avec protection des services, du personnel et du pouvoir d'achat. La disparition éventuelle de la **TVQ** supprimerait ou modifierait aussi des **mécanismes de financement liés à sa croissance** :

1. **La source 2024 repère près de 445 M$ affectés aux organismes municipaux par les programmes recensés.** Ces flux doivent avoir un mécanisme de continuité ou un financement de remplacement légalement défini. Le montant 2024 est historique, **pas une estimation 2026**.
2. Un transfert du gouvernement provincial vers une municipalité est une **charge et un décaissement chez l'expéditeur**, et une **recette chez le bénéficiaire**; lorsqu'on consolide les deux ordres de gouvernement, il faut **éliminer cette opération interne une seule fois**, plutôt que l'ajouter à nouveau comme recette disponible à l'échelle du Québec.
3. Neutraliser le double comptage en consolidation **n'autorise pas la suppression du financement des services**. Les sommes nécessaires à l'eau potable, aux routes, à la sécurité, aux activités municipales, au paiement de la dette et à la continuité des salariés demeurent.
4. Le régime municipal actuel comporte taxes, droits, tarifs et redevances. Chacune exige une **qualification juridique**, distincte d'une suppression automatique sous la promesse politique « deux prélèvements ».
5. Dans le scénario **Québec dans le Canada**, les pouvoirs provinciaux et fédéraux ne sont pas interchangeables. Dans le scénario **Québec souverain**, les transferts actuellement associés à un autre ordre de gouvernement ne sont pas présumés se poursuivre sans accord, remplacement ou cadre légal.

La simulation de transferts du module G0.17a opère uniquement en mode **`SYNTHETIC_ONLY`**. Elle ne prétend pas calculer des paiements réels ni un taux fiscal Nova.

## 5. Source ouverte plus appropriée pour le prochain rapprochement

Le portail [Données Québec — Rapport financier des organismes municipaux et autres documents connexes](https://www.donneesquebec.ca/recherche/dataset/rapport-financier-des-organismes-municipaux-et-autres-documents) répertorie notamment les **données réelles 2024 et 2025**, les fichiers CSV d'occurrences, les formulaires codifiés et les listes d'organismes absents. Les ressources observées indiquent une mise à jour **le 7 novembre 2026**.

**Les CSV détaillés n'ont pas été téléchargés et analysés dans G0.17a.** Leur existence ne prouve pas automatiquement un montant agrégé, et leurs organismes, rubriques, versions et dates devront être normalisés avant toute consolidation.

Pour résoudre l'anomalie et avancer, il faudra :

- Obtenir une copie **figée, horodatée et hachée SHA-256** des éditions PDF 2024 et 2025.
- Vérifier que couverture, tableau et extraction proviennent **des mêmes octets**.
- Charger les données municipales 2024 et 2025 en utilisant les **formulaires de comptes codifiés** correspondants et les listes de municipalités absentes.
- Retrouver les **transferts provinciaux correspondants**, même exercice et même objet, en distinguant finances municipales par **année civile** et comptes du Québec par **exercice avril–mars**.
- Construire des **éliminations internes** reproductibles pour éviter les doubles comptes, puis estimer les recettes qu'il faudra réellement remplacer.
- Faire examiner l'incidence sur le revenu disponible, le maintien des services et l'emploi par des spécialistes indépendants.

## 6. Résultats de contrôle, décision et suite

- `data/g017a-transferts-fiscaux-mamh-controle-versions-2024-2025.json` : tableau 2024 issu d'une capture visible, extraction 2025 mise en quarantaine, dates et sources, contrôles de consolidation et tâches de résolution.
- `assets/g017a-mamh-transfer-source-gates.mjs` : refus des taux, écarts et financements inventés, plus test d'élimination des transferts internes en données **exclusivement fictives**.
- `tests/g017a-mamh-transfer-source-integrity.test.mjs` : **44 tests réussis au rejeu JavaScript/V8 isolé**. Ce résultat ne remplace pas une exécution GitHub Actions native, la validation des PDF immuables ou un audit externe.

**Décision G0.17a : contrôle de source renforcé; 2024 programmes MAMH visuellement documentés, 2025 chiffres non publiables comme comparables, TVA municipale à protéger dans la transition. Le conflit de version reste ouvert. Programme Nova–Sinjira inchangé à 47/100.**

**Suite G0.17b :** importer les données municipales réelles 2024–2025 à partir des fichiers codifiés, croiser chaque poste significatif avec sa contrepartie provinciale et réviser le modèle fiscal et les garanties de service sans inventer les recettes manquantes.

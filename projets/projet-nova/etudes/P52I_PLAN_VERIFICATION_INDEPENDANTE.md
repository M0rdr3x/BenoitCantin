# Projet Nova — P52I : plan de preuve indépendante et sources vérifiables

**19 octobre 2026 — Étude candidate, NON ADOPTÉE — PR #673 en brouillon.**

## 1. Objet et limites
P52H démontre l'intégrité d'une chaîne de contrôles techniques, **pas** la faisabilité d'une réforme fiscale. P52I ouvre un véritable registre de pistes de sources officielles pour les 20 exigences F01–F20 sans changer leur état « NON_VALIDE ». Les 600 valeurs de projection P52B et 720 valeurs d'incidence P52D restent inconnues (1 320). **Aucun taux, gain, exemption, montant ou abolition n'est autorisé ici.** Une page trouvée n'est ni une extraction validée ni un avis indépendant.

Le registre `P52I_SOURCES_ET_ATTESTATIONS.json` est un **plan d'acquisition et de revue**, pas un dossier de preuves obtenues. Les indicateurs et les URL de ce fichier sont publics et non personnels. Aucun fichier de microsimulation ni résultat par personne n'est ajouté au dépôt.

## 2. Séparation obligatoire des périmètres
- **Québec au Canada :** comptabilité provinciale propre; TPS et impôt fédéral toujours distincts; le Québec n'abolit pas seul les prélèvements fédéraux.
- **Fédéral :** recenser séparément les recettes, transferts, engagements, services, prestations et coûts d'administration pertinents. Un transfert fédéral reçu par le Québec **ne s'additionne pas** au bilan consolidé comme nouvelle richesse.
- **Municipal :** intégrer taxes foncières/scolaires, transferts, services locaux et actifs, sans masquer un prélèvement local sous le nom de « frais ».
- **Souveraineté hypothétique :** étude séparée de reprise des fonctions fédérales, dette/actifs, stabilité monétaire, ententes et institutions. Aucune responsabilité ne disparaît parce qu'un impôt est aboli.

**Règle anti-double comptage :** chaque ligne doit posséder un niveau institutionnel, une année, un statut (prévision/réalisé), une unité, une fonction, une contrepartie, un code de consolidation et la page exacte du document. Les transferts entre niveaux sont éliminés lors de la consolidation. Le budget annuel n'est pas un modèle décennal.

## 3. Chaîne de preuve exigée, pièce par pièce
1. Identifier le document primaire et vérifier sa version, sa date, son périmètre et les droits d'utilisation.
2. Relever l'URL stable, la page/tableau, la définition, l'année, l'unité, l'arrondi et, lorsque permis, une empreinte du fichier. Noter la date du relevé.
3. Effectuer une double saisie/reconciliation indépendante des totaux et de leurs sous-composantes. Corriger les erreurs sans écraser l'historique.
4. Demander un **avis contradictoire indépendant**, daté, traçable et signé par une personne identifiée et autorisée : expertise fiscale/juridique pour F01–F08, comptable/économique pour F09–F18, démocratique et vie privée pour F19–F20.
5. Indiquer explicitement ce que la source **ne** permet **pas** de conclure. Le responsable fonctionnel nommé dans F01–F20 n'est pas une personne réellement mandatée.
6. Publier uniquement une synthèse dépourvue de données individuelles **après** autorisations humaines formelles. Réexécuter P52B–P52H sur les nouvelles données auditées, sans autorisation de publication automatique.

## 4. Plan de mesure de la protection du pouvoir d'achat
Le passage de 42 **cas illustratifs non représentatifs** à une estimation pour la population exige un cadre statistique autorisé : échantillonnage/calibration Québec, pondérations, sous-groupes (déciles, compositions familiales, régions, aînés), prélèvements **et** transferts fédéraux/provinciaux, taxes indirectes, effet sur logement, énergie et services. Calculer les pertes potentielles avant/après, leur ampleur et leur distribution; distinguer l'incidence directe des effets de prix, d'emploi et de croissance non observés.

**Piste institutionnelle :** Statistique Canada indique que sa BD/MSPS permet la microsimulation de politiques fiscales et de transferts sur une base statistiquement représentative. Son utilisation exige une entente de licence; il s'agit d'un modèle **statique**, non d'une estimation des effets comportementaux d'une indépendance éventuelle. L'accès, la licence, l'expertise et les résultats sont **non obtenus**. Voir : https://www.statcan.gc.ca/fr/microsimulation/bdmsps/bdmsps.

D'autres sources identifiées : [Budget 2026–2027 du Québec](https://www.finances.gouv.qc.ca/Budget_et_mise_a_jour/budget/), [inégalité de revenu au Québec](https://statistique.quebec.ca/fr/document/inegalite-revenu-menages-et-particuliers), [revenus des ménages québécois](https://statistique.quebec.ca/fr/document/revenu-menages-et-particuliers), [statistiques municipales](https://www150.statcan.gc.ca/t1/tbl1/fr/tv.action?pid=1010002001) et [documents des finances fédérales](https://www.canada.ca/fr/ministere-finances/organisation/transparence/documents-information/2026.html). Ces liens n'attestent aucun des 20 points.

## 5. Contrôle et décisions
Le vérificateur `scripts/auditer_sources_fiscales_nova_p52i.py` :
- lit directement F01–F20 dans P52A, vérifie le parallélisme exact des identifiants, régimes et exigences;
- refuse les URL non HTTPS et les domaines non approuvés dans ce registre, les références à une source inconnue, les validations fictives, les chiffres de preuve inventés, les identifiants en double et tout statut de GO;
- exige trois niveaux budgétaires sans consolidation supposée;
- refuse toute prétention à une étude de représentativité ou à une certification de non-appauvrissement;
- émet **seulement des nombres agrégés**, sans URL, microdonnée ni nom de personne. Le code 0 signifie « inventaire techniquement cohérent »; le code 3 sur `--exiger-preuves` signifie « preuve insuffisante »; le code 2 signifie « document invalide ».

**Décision : NO_GO_AUTOMATIQUE.** Aucun dépôt légal, adoption, taux, réforme, donation, collecte, formulaire, fusion ni déploiement ne s'ensuit. PR #640 : ne pas fusionner; les issues #135 (protection de main) et #662 (revues indépendantes) demeurent ouvertes. Préserver SINJIRA.

## 6. Livrable requis pour P52J
Pour chacune des 20 exigences : pièce officielle contrôlable, extraction et rapprochement documentés, avis humain contradictoire et résolution des réserves. Pour F11 : plan d'étude représentatif exécuté avec droit d'usage et publication d'estimations agrégées sécurisées. Pour F09/F16 : comptes consolidés des trois niveaux et coût de la reprise souveraine. Un **GO fiscal** reste impossible tant que les validations légales, démocratiques et financières ne sont pas réellement constatées.

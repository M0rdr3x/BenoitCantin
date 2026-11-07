# Projet Nova — P53S : registre de suivi documentaire et recours, sans événement réel présumé

**22 octobre 2026 — état initial NON DÉPOSÉ. Projet de gouvernance préparatoire, sans autorité gouvernementale.**

## 1. Première priorité : réparer la validation P53R

Le workflow P53R précédent a échoué à **un seul test sur 48** : test_46_quebec_rtc_double_count cherchait exactement l'expression « écritures réciproques » dans les deux courriers Québec/RTC. La lettre de Québec utilisait « éliminations réciproques », ce qui ne satisfaisait pas le contrôle textuel bien que le sujet comptable soit le même. La correction P53S ajoute dans les deux projets de courrier une note commune sur les **écritures réciproques**, leur périmètre et le risque de seconde élimination. Les tests P53R doivent être relancés et vérifiés séparément : le succès ne peut être présumé.

## 2. Un registre de suivi qui ne simule pas l'État

P53R contient six projets de lettres **non envoyées**. P53Q répertorie 102 besoins documentaires des six organismes Montréal, ARTM, Québec, STM, RTC et Saint-Valère. P53S construit **66 positions de suivi** : onze phases de contrôle × six organismes, **zéro événement vérifié**, sans transmettre aucune demande.

Les onze phases de suivi préparées sont : projet non déposé, responsable pressenti identifié, envoi déclaré, réception déclarée, prolongation déclarée, réponse partielle déclarée, réponse complète déclarée, refus déclaré, silence déclaré sans délai vérifié, recours déclaré et archivage déclaré. Seules les deux premières ne concernent pas directement des communications effectives. Tout état après « préparation » doit rester **DECLARÉ NON AUTHENTIFIÉ** tant que les pièces externes n'ont pas été examinées humainement et juridiquement.

Le système refuse les sauts chronologiques, les doublons d'étape dans un même organisme, les dates invalides et les déclarations de recours sans au moins un événement antérieur pertinent. Les événements de réponse/refus/prolongation ne peuvent être déclarés sans une réception préalable elle-même déclarative; ces conditions garantissent la cohérence des dossiers **sans prouver qu'ils existent réellement**.

## 3. Types de justificatifs et conservation hors dépôt

Un envoi déclaré exige une classe « trace d'envoi »; une réception déclarée exige une classe « accusé de réception »; une prolongation exige un avis; une réponse exige un document de décision; un refus exige une décision de refus; un recours exige une trace du dépôt; le classement nécessite un bordereau d'archivage. L'entrée locale peut indiquer qu'un justificatif externe est disponible et fournir son empreinte SHA-256 au format standard. Le programme ne lit ni n'acquiert le justificatif : **la présence d'un hash valide ne valide jamais une signature, un émetteur, un canal, une date ou un droit d'accès**.

Les dossiers confidentiels et les accusés contenant des renseignements personnels doivent rester dans une solution documentaire autorisée, hors GitHub. Les déclarations JSON ne contiennent ni noms, ni adresses, ni courriels, ni numéros de dossier gouvernemental, ni texte de pièce ni URL privés; les champs supplémentaires sont rejetés. Les sorties comprennent des dossiers initiaux neutres et un bilan **agrégé sans date, hash, identité ou montant** de déclaration.

## 4. Délais : repères juridiques, pas alertes fictives

Au Québec, l'article 46 de la Loi sur l'accès aux documents des organismes publics exige un **avis écrit de date de réception** pour une demande écrite. L'article 47 prévoit en principe **20 jours civils** pour répondre à partir de la réception réelle, avec prolongation d'au plus **10 jours** dans les cas et formes prévus. L'article 135 prévoit généralement **30 jours** pour saisir la Commission d'accès à l'information d'une révision, après décision ou échéance, sous réserve des règles spécifiques et de motifs raisonnables. Les parties tierces, la nature du document et les autres délais particuliers peuvent modifier l'analyse; une révision juridique humaine s'impose.

- Loi A-2.1 : https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1
- Commission d'accès à l'information : https://www.cai.gouv.qc.ca/acces-documents-organismes-publics/citoyens-acces-documents-publics/comment-acceder-documents-organismes-publics
- Règles du gouvernement du Québec : https://www.quebec.ca/acces-information

**Une date saisie, même associée à une empreinte SHA, ne crée pas de délai réel.** P53S refuse de calculer de fausses échéances sur ces données, de déclarer une révision déposée ou un silence légalement constitué sans contrôle humain.

## 5. Prudence constitutionnelle et budgétaire

Les procédures A-2.1 sont celles des **organismes actuellement concernés au Québec dans le Canada**, sans extension automatique à un Québec indépendant hypothétique. Les flux 2024 des organismes municipaux ne représentent ni de nouvelles ressources fiscales ni des coûts éliminables. Québec et le RTC imposent un contrôle strict des écritures interorganismes **déjà consolidées**. Les garanties de maintien des emplois, des services et du pouvoir d'achat restent obligatoires. Les hypothèses fiscales F01–F20 et les 1 320 valeurs Nova non démontrées ne sont pas certifiées par ce protocole.

## 6. Mode d'emploi

    python scripts/suivre_demandes_acces_nova_p53s.py --bilan p53s_bilan.json --registre p53s_registre.json
    python scripts/suivre_demandes_acces_nova_p53s.py --exiger-envoi-ou-reception-verifie

Les déclarations locales facultatives s'ajoutent avec --evenement chemin.json, en ordre chronologique, au maximum 66 événements. Le code de sortie **0** atteste seulement la structure; **2** signale une erreur de données ou un écrasement interdit; **3** est le refus normal d'une certification demandée. Les sorties existantes ne sont pas écrasées. Aucun appel réseau ni transmission n'est effectué.

**NO_GO_AUTOMATIQUE** : 0 envoi vérifié, 0 accusé de réception authentifié, 0 réponse ou recours attesté, 0 pièce comptable primaire auditée, 0 économie certifiée, 0 publication ou fusion, aucune baisse des effectifs ou des services autorisée.

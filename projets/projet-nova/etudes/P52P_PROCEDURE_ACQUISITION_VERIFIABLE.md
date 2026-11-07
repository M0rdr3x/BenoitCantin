# Projet Nova — P52P : registre des lacunes, statut des sources et preuve d'incomplétude calculée

**19 octobre 2026 · Examen technique non adopté, PR #673 en brouillon · NO_GO pour toute adoption ou fusion.**

## 1. Objectif concret

Les jalons P52A–P52O fournissent vingt exigences F01–F20, des pistes officielles, une relecture assistée de deux tableaux 2026-2027, un protocole d'empreintes et des cahiers de mandat. **Ils ne contiennent pas d'avis d'experts réellement authentifiés.** Une URL de texte de loi ou de page statistique n'est pas un avis juridique; la relecture d'un tableau budgétaire ne vaut pas consolidation indépendante; une empreinte numérique non enregistrée n'est pas une archive authentifiée.

P52P met ces distinctions sous contrôle automatisé à partir des *vrais fichiers de la branche*. Il crée une fiche d'acquisition de **chaque** preuve, recoupe son régime, son comité, son ordre de priorité, ses dépendances et la liste exacte de pistes `S01–S08` (P52I) et `REF01–REF10` (P52O). Les deux documents primaires relus en P52J sont indiqués pour F09 **comme relecture assistée uniquement**, non comme attestation.

## 2. Résultats du diagnostic P52P

- **20 exigences bloquantes**, vingt attestations indépendantes manquantes.
- **18 URL/candidats issus de P52I et P52O**, plus **2 documents primaires lus** (P52J); les doublons éventuels entre ces registres ne sont **pas** additionnés comme sources indépendantes.
- **13 exigences** ont au moins une *piste de source* associée par P52I/P52O; **7** n'en ont aucune (F06, F08, F12, F13, F14, F15, F19). La couverture documentaire n'est **pas** la couverture d'expertise.
- **2 PDF originaux P52K sans copie archivée/empreinte attestée** dans le registre. Le hash n'est pas une signature de l'État.
- **600 valeurs monétaires inconnues sur 60 exercices/scénarios P52B**, et **720 valeurs monétaires inconnues sur 42 cas P52D**, soit **1 320 inconnues financières**. P52B comporte également 120 indicateurs de contexte (`solde_budgetaire_precedent`, `ratio_dette_nette_pib_pct`) actuellement inconnus, *non inclus* dans les 1 320 postes monétaires. Aucun chiffre n'est imputé.
- Les 30 exemples de ménages et 12 exemples d'entreprises P52D **ne sont pas représentatifs** de la population; aucun modèle de perte évitée n'est démontré.

Le validateur **recompte** effectivement les nulls dans les fichiers P52B et P52D pour détecter toute modification silencieuse. Il rejette toute valeur financière ajoutée sans validation correspondante (ne remplace pas l'état actuel par un modèle fictif), ainsi qu'une modification de scénario, de régime, de source ou de preuve.

## 3. Chaîne de réception des pièces (travail humain)

Pour transformer une *piste* en dossier susceptible d'examen, un responsable habilité devra :
1. **Acquérir** la version primaire licite, complète et datée, avec date de récupération et règles d'usage. Identifier l'année, la juridiction et l'organisme.
2. **Conserver** le document original dans une archive sous contrôle d'accès, avec hachage SHA-256 des octets, version et traçabilité; ne pas utiliser GitHub comme coffre de données fiscales ou de signatures.
3. **Extraire** les faits avec page, tableau, unité, arrondis, définition et distinction entre prévision et résultat réel. Refaire le calcul indépendamment.
4. **Obtenir un expert réel** possédant mandat vérifié, indépendance, méthode accessible, déclarations d'intérêt, réserve et avis signé contrôlé par un tiers.
5. **Prévoir une contre-expertise** et le règlement des divergences, notamment lorsqu'une donnée altère le budget, les services, les droits ou la distribution des revenus.
6. **Renvoyer au décideur compétent**, selon le droit et les règles démocratiques applicables; une preuve acceptée n'est toujours pas une loi adoptée.

Le gabarit `P52P_GABARIT_RECEPTION_PIECE.json` est volontairement **vide** : ce n'est ni une preuve ni un formulaire de collecte ouvert. Toute vraie preuve et tout identifiant personnel demeurent *hors du dépôt public*. La fiche P52P enregistre huit étapes documentaires vides pour chacune des vingt exigences. Dans ce jalon les étapes et attestations restent toutes `null`/`false`.

## 4. Distinction des deux régimes

Pour **Québec dans le Canada**, ne pas prétendre modifier TPS, douanes fédérales ou impôt fédéral provincialement, ni assimiler la fiscalité foncière municipale à l'impôt québécois. Pour un **Québec souverain hypothétique**, consolider dette, actifs, prestations, défense, frontières, pension, monnaie, administrations et accords, sans les considérer acquis; la souveraineté ne supprime pas les obligations comptables.

Une estimation de recettes anti-évasion additionnelles reste **zéro par prudence non certifiée** dans le gabarit P52B, pas un résultat observé et pas une taxe définitivement fixée. Les montants `null` ne sont pas des zéros. Le programme rejette toute prétendue validation automatique, y compris si toutes les URL sont présentes.

## 5. Utilisation et mécanisme de protection

```bash
python scripts/auditer_lacunes_preuves_nova_p52p.py --rapport /chemin/prive/p52p_agregat.json
python scripts/auditer_lacunes_preuves_nova_p52p.py --exiger-preuves --rapport /chemin/prive/p52p_refus.json
```

- Code **0** : inventaire mécanique cohérent, **NO_GO**.
- Code **2** : divergence documentaire, scénario altéré ou données prétendument validées.
- Code **3** : inventaire cohérent mais **preuves indépendantes toujours absentes**.
- Rapports non écrasants et **agrégés**; jamais de noms, URL, numéros de document, montants individuels, identifiants de source ni contenu de PDF.
- GitHub Actions tourne en lecture seule et utilise seulement ces agrégats; il ne certifie pas le contenu des pages officielles ni l'actualité d'une version législative.

## 6. Suite réellement utile

**P52Q :** faire constituer par une autorité humaine un dossier de réception de pièces de la première vague (F01–F04, F07, F09, F19–F20), obtenir les textes consolidés, vérifier les dates/versions et traiter les écarts. La capacité réelle de procéder exige des mandats, des budgets et des personnes compétentes, pas une multiplication de fichiers techniques.

Priorités de gouvernance en parallèle : protection serveur de `main` (issue #135), revue extérieure par des personnes nommées (issue #662), préservation de SINJIRA et refus de fusionner PR #640. PR #673 reste en brouillon et non fusionnée.

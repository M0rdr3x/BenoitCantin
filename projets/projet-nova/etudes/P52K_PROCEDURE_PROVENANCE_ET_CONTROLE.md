# Projet Nova — P52K : chaîne de conservation et d'attestation des preuves budgétaires

**Date de préparation : 19 octobre 2026 · Statut : candidat non adopté · Autorisation : NO_GO.**

## 1. Résultat attendu et protection contre les fausses certitudes

P52J compare les 21 lignes de revenus, les huit agrégats et dix valeurs signées des prévisions budgétaires 2026-2027 à deux tableaux publics. Les tableaux sont identifiés et leur lecture visuelle est reproductible. Ils ne constituent toujours pas un budget Nova, une projection pluriannuelle, une attestation comptable indépendante ou une adoption législative.

P52K crée une **chaîne de provenance technique locale** pour ces deux PDF sources :
- `DISC2026_T3` : discours budgétaire, tableau 3, page imprimée 27, index PDF 29;
- `PLAN2026_F2` : plan budgétaire, tableau F.2, page imprimée F.9, index PDF 277.

Les URL complètes sont reliées à P52J par un registre verrouillé `P52K_REGISTRE_PROVENANCE_BUDGET.json`. **Aucun original PDF n'a été acquis dans ce jalon et aucune empreinte réelle n'est annoncée.** Le registre reste volontairement sans empreinte, sans horodatage certifié et sans attestation humaine. Le script P52K permet une **acquisition ultérieure sur un poste de travail autorisé**, sans accès réseau et sans publier les documents.

## 2. Notions à ne jamais confondre

1. **Intégrité locale :** SHA-256 atteste qu'un lot d'octets vérifié ultérieurement est identique aux octets hachés lors de la création d'un reçu; il ne garantit ni l'auteur du PDF, ni son authenticité, ni que le PDF émane de l'administration.
2. **Provenance externe :** pour établir la version officielle reçue, conserver le document à sa source licite, le contexte de téléchargement, les mentions d'édition, les métadonnées utiles et une archive à contrôle d'accès. Le lien URL seul ne prouve pas la version; deux captures à dates différentes peuvent différer.
3. **Horodatage probant :** l'heure de l'ordinateur qui produit le reçu est déclarative. Un horodatage de tiers vérifiable, si nécessaire, doit être obtenu hors du script.
4. **Double vérification :** un expert indépendant doit rapprocher la capture originale avec les tableaux officiels, les éventuelles versions révisées et les règles de consolidation budgétaire.
5. **Gouvernance :** une signature, un mandat et un registre de conflits d'intérêts doivent être vérifiés par les autorités compétentes. Le passage de « contrôlé techniquement » à « certifié » n'est jamais automatique.

## 3. Utilisation locale — sans téléchargement dans GitHub Actions

La commande `audit` vérifie la cohérence du registre P52K avec les 20 preuves P52A, le plan P52I et les références primaires P52J :

```bash
python scripts/controler_provenance_budget_nova_p52k.py audit
python scripts/controler_provenance_budget_nova_p52k.py audit --exiger-attestation
```

**Codes de sortie :** 0 = registre cohérent mais non certifié; 2 = document invalide; 3 = attestation insuffisante attendue. Le contrôle ne télécharge aucun fichier et ne cherche aucun secret.

Pour calculer une **empreinte sur un PDF obtenu légalement et conservé en dehors du dépôt**, sélectionner un ID exact. Le reçu doit être écrit dans un répertoire local privé, jamais commité :

```bash
python scripts/controler_provenance_budget_nova_p52k.py empreinte \
  --source-id DISC2026_T3 \
  --pdf "/chemin/prive/Budget2627_Discours.pdf" \
  --sortie "/chemin/prive/recus/discours.json"
python scripts/controler_provenance_budget_nova_p52k.py verifier \
  --source-id DISC2026_T3 \
  --pdf "/chemin/prive/Budget2627_Discours.pdf" \
  --recu "/chemin/prive/recus/discours.json"
```

Les reçus locaux contiennent : ID documentaire, URL de référence connue, taille, hachage SHA-256 des octets, heure UTC du poste et déclarations explicites « non certifié », « aucun GO ». Ils **ne** comportent pas le chemin du fichier ni l'identité du vérificateur. Le script vérifie que le fichier semble avoir une enveloppe PDF, mais **il n'interprète pas les tableaux** et ne doit pas être considéré comme un outil de vérification de signature électronique. Aucun reçu n'est incorporé automatiquement au registre officiel P52K. Une modification simultanée du PDF et du reçu peut tromper une vérification locale : il faut une référence externe, un contrôle d'accès et une revue indépendante.

## 4. Dossier probatoire à constituer manuellement

Pour chaque PDF : conserver la page source, la copie binaire, les métadonnées d'acquisition, le reçu SHA-256, la copie d'archive en lecture seule, la seconde lecture indépendante, les écarts, les corrections signées et l'historique des versions. Isoler les PDF publics de toute donnée confidentielle.

Pour la preuve **F09** : vérifier l'évolution des prévisions en 2026-2027, la consolidation des flux entre administrations et l'absence de double compte; faire signer un avis comptable indépendant. La preuve demeure `NON_VALIDE` tant que cette revue n'est pas reçue.

Pour **F20** : mener une analyse de proportionnalité et de protection des données; vérifier les droits d'accès, de contestation et de conservation; ne jamais déposer d'identifiants fiscaux, de rapports de cas ou de documents confidentiels dans GitHub. La preuve demeure `NON_VALIDE`.

Pour **F01–F08, F10–F19** : les étapes de provenance ne lèvent **aucun** blocage de fond. Garder les vingt statuts inchangés tant qu'une preuve humaine réelle n'est pas constatée.

## 5. Règles de correction des divergences

Toute modification de référence, de valeur budgétaire ou de méthode exige une nouvelle version du registre, une justification datée, un état avant/après, une relecture par une seconde personne indépendante et un test de non-régression. Un reçu déjà émis ne doit pas être écrasé; produire un nouveau reçu et conserver le précédent selon la politique documentaire applicable. Éviter de placer des attestations contenant des noms ou signatures dans un dépôt public.

Si les montants du PDF acquis ne concordent pas avec les prévisions P52C/P52J, **arrêter l'utilisation de la source concernée, ne pas modifier silencieusement P52C et conserver le statut NO_GO** jusqu'à résolution formelle.

## 6. GitHub et prochaine décision

Le workflow P52K contrôle la structure, le chaînage des 20 preuves et les opérations d'empreinte sur **un faux PDF de test créé dans les tests**, jamais sur les PDF réels. La réussite des tests confirme le comportement du code; elle ne modifie aucune approbation.

Aucun changement à `main`, aucun déploiement, aucune collecte, aucun changement à SINJIRA; préserver le statut brouillon de PR #673. Les revues indépendantes, la protection préventive de `main` (issues #662 et #135), la pertinence de l'étude de microsimulation et la validation des budgets consolidés restent des dépendances bloquantes.

**Suite logique P52L :** matrice formelle d'acceptation/refus des avis humains avec traitement des réserves contradictoires, exigences de compétence et de conflits d'intérêts, jamais d'approbation fondée sur un statut saisi sans pièce authentifiée.

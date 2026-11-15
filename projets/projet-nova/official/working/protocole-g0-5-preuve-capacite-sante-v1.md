# NOVA-SINJ-G0-SAN-006 — G0.5 : preuve d'accès réel, capacité de soins et coût complet

**Projet :** Projet Nova  
**Version :** 1.0 — 3 novembre 2026  
**Statut :** protocole opérationnel et matrice de preuves, **étude non adoptée**. Ni mandat de recherche clinique, ni accès à des données personnelles, ni appel d'offres, ni engagement financier.  
**Porte :** G0 diagnostic **non franchie**; les 18 régions sociosanitaires sont couvertes par la matrice de vérification, **pas par un tableau complet de coûts ou d'accès réalisé**.  
**Méthode :** enchaînement entre les preuves G0.4 de l'ISQ et les données publiques ou institutionnelles qui permettraient une véritable comparaison ultérieure.

## 1. Problème à résoudre et grandeurs à ne pas confondre

**Question de politique publique :** pour une consultation de première ligne médicalement assurée, quels sont le délai pour **un soin effectivement reçu**, sa continuité et sa sécurité, le nombre **net** de professionnels nécessaires et le coût **complet**, selon des groupes de besoins, des territoires et des périodes comparables?

Le tableau de bord du Québec précise lui-même que :
1. **attitration** à un médecin/équipe ≠ facilité à obtenir un rendez-vous;
2. **formulaire GAP reçu** ≠ personne unique ni consultation;
3. **premier rappel du GAP** (moyenne mobile sur sept jours) ≠ rendez-vous attribué ≠ consultation réalisée; le rappel comprend les heures non ouvrables dans le délai;
4. **complétion du GAP** peut couvrir des tâches administratives et l'attribution d'un rendez-vous — ce n'est pas une confirmation de soin reçu;
5. **orientations du GAP** : une demande peut recevoir plusieurs orientations.

Source des définitions : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/performance-reseau-sante-services-sociaux .

**Aucun taux d'affiliation n'est substitué à un délai clinique.** Les 16 taux de l'ISQ documentés en G0.4 restent des mesures descriptives d'enquête avec des exclusions de territoire, non des « scores de service ».

## 2. Sources vérifiées — trois voies complémentaires

| Source et période | Variables potentiellement utiles | Ce qui est réellement acquis dans le dépôt | Ce qui reste bloqué |
| --- | --- | --- | --- |
| **ISQ, Panorama 2026, enquête 2025** | Affiliation, lieu habituel de suivi des affiliés, démarches vers urgence au dernier besoin | 16 taux RSS transcrits du PDF dans G0.4; 2 RSS hors enquête; dénominateurs et marques de précision notés | Aucun délai demande → consultation, aucune main-d'œuvre ni coût par épisode |
| **Québec/RAMQ-MSSS, 31 déc. 2024 et 31 mars 2025** | Inscription médicale, assiduité des médecins, volumes des visites aux urgences de triage 4/5 | Catalogue public confirmant deux fichiers et leurs variables | **Aucun fichier XLS/XLSX importé dans G0.5**; période différente; visites d'urgence administratives ≠ démarches déclarées dans l'enquête 2025 |
| **Santé Québec, tableau de performance** | Attitration, GAP, urgences, expérience patient, RH et périodes de 13 cycles financiers | Définitions officielles et fréquence de mise à jour documentées | **Aucune série chiffrée dynamique extraite à la date de ce dossier**; un rappel du GAP n'est pas une consultation médicale |
| **Québec, personnel 2024–2025** | Personnel des établissements publics et privés conventionnés par région, catégorie et statut; St@tRAMQ par profession/RSS | Existence du fichier RH régional et de St@tRAMQ vérifiée | Fichier RH **non importé**, absence des employés de certains opérateurs et absence de preuve d'ETP **nets en première ligne** |
| **RAMQ, statistiques et données sur demande** | Paiements, professions rémunérées, programmes et possibles extractions sous conditions | Catalogue et mécanisme de demande confirmés | **Aucun coût complet par épisode** ni ventilation comparative par prestataire validée |
| **Québec, tableau stratégique 2024–2025** | Quelques résultats provinciaux historiques : consultation en clinique sous 36 h, attitration, rétention de nouvelles embauches | Trois valeurs sourcées et **isolées de la matrice régionale** | Ne pas présenter comme observations de l'EQUSSSS 2025, valeurs 2026 ou indicateurs régionaux |

Liens de référence :
- ISQ 2025 : https://statistique.quebec.ca/fr/document/utilisation-services-sante-et-services-sociaux
- Québec, accès à la première ligne et fichiers historiques : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/donnees-acces-services-medicaux-premiere-ligne
- Québec, méthodes du tableau de bord : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/performance-reseau-sante-services-sociaux
- Québec, données RH : https://www.quebec.ca/sante/systeme-et-services-de-sante/organisation-des-services/donnees-systeme-sante-quebecois-services/ressources-humaines
- RAMQ, données sur demande : https://www.ramq.gouv.qc.ca/fr/donnees-statistiques
- Tableau stratégique Québec, résultats 2024–2025 : https://performance.gouv.qc.ca/tableau-de-bord/resultats-detailles/sante-et-services-sociaux

### Chiffres historiques provinciaux, explicitement non comparables
Dans le tableau gouvernemental de **l'exercice 2024–2025**, au niveau du plan stratégique :
- **36 %** des personnes ont consulté un professionnel de la santé dans les 36 heures **dans les cliniques médicales** (indicateur du plan stratégique, pas le premier rappel du GAP);
- **84 %** de personnes attitrées à un professionnel ou à une équipe de première ligne (indicateur administratif; non directement comparable aux **82 % de l'enquête ISQ 2025**);
- **79,5 %** de taux de rétention de 0 à 12 mois des nouvelles embauches **dans l'ensemble du réseau**, sans chiffre régional d'ETP première ligne.

Ces trois chiffres ne sont **ni actuels au 3 novembre 2026**, ni des chiffres de l'étude régionale EQUSSSS, ni des taux par prestataire public/privé. Ils sont enregistrés comme **références historiques distinctes** pour illustrer les risques de jointure.

## 3. La chaîne de soins à mesurer
Un épisode comparable ne se résume pas à un paiement RAMQ. Il faut définir la séquence :

`Besoin déclaré → demande datée → triage clinique → service proposé → consultation réellement effectuée → suivi/conséquence aval`

Une consultation peut être donnée par un médecin, une IPS ou une autre profession habilitée selon les actes, les règles d'assurance et le lieu. **Avant les chiffres**, un avis clinique et juridique doit définir les services réellement comparables, les niveaux de risque et les exclusions légitimes. Les personnes non servies ou orientées hors parcours doivent rester visibles dans le dénominateur approprié.

**Tableau G0.5 minimal à acquérir :**

| Dimension | Unité et base de calcul (à finaliser) | Mesure critique | Blocage actuel |
| --- | --- | --- | --- |
| Accès réel | Nombre d'épisodes avec demande et consultation effectuée / demandes admissibles | Médiane, p90, demandes non servies et adéquation clinique | Aucun rapprochement de parcours validé |
| Qualité / continuité | Épisodes avec suivi adéquat / épisodes nécessitant suivi | Complications, réorientation et retours ajustés à la complexité | Définition clinique et données à obtenir |
| Équité | Sous-groupes et territoires au même périmètre | Écarts, populations exclues et accès hors ligne | RSS 17–18 non enquêtées en EQUSSSS |
| Personnel | Équivalents temps plein **nets** par région et profession | Embauches, départs, mobilité public/privé, compétences et réserve | Catalogue RH existant, aucune série ETP réconciliée |
| Coût public | CAD/épisode de besoin comparable | Paiements + gestion publique non comptée + aval + transition et réserve | Aucun coût régional complet |
| Coût économique | CAD/épisode avec comptes de ressources | Ressources, capital, usagers/proches, aval, moins les doubles comptes | Aucun coût de ressource validé |
| Légalité et données | Avis écrit par montage proposé | Couverture RAMQ, confidentialité, garde-fous, recours | Aucun montage approuvé |
| Contrefactuel | Même cas, même territoire, même horizon | Public actuel **et améliorable**, privé agréé assuré, OBNL/cooperative | Aucun comparateur causal démontré |

## 4. Règles de rapprochement — refus des jointures trompeuses
**Grain candidat :** `RSS × période homogène × besoin clinique et complexité × épisode assuré × mode de prestation`. Chaque pièce de preuve doit porter le **code RSS**, le **début/fin d'observation**, le **numérateur/dénominateur**, la **méthode**, les **exclusions**, le **droit de diffusion** et l'**incertitude**.

- Une **RSS** ne se déduit pas d'un **RTS**, d'une région administrative ou du seul établissement; fournir une table de correspondance autorisée et les limites de cette correspondance.
- Une série d'enquête **2025** ne peut pas être alignée mécaniquement avec un portrait RH **2024–2025** et une facturation datée **2026** pour en déduire un coût causal.
- Le nombre de professionnels **rémunérés par la RAMQ** n'est pas automatiquement le nombre d'ETP actifs dans les établissements de première ligne; les données des établissements **publics et privés conventionnés** n'englobent pas tout le privé, tandis que la pratique privée peut elle-même recevoir des fonds publics.
- Le recours déclaré à l'urgence lors d'un **dernier besoin** dans l'EQUSSSS n'est pas le volume administratif des **visites de triage 4/5**.
- Une donnée absente doit rester `null`, jamais `0`. Le tableau de bord officiel prévient lui-même que les valeurs vides et les zéros peuvent être masqués selon les écrans.
- Ne pas supposer que les 82 % d'affiliation en enquête 2025 constituent la variation des 84 % d'attitration indiqués par le gouvernement en exercice 2024–2025.

## 5. Huit dimensions bloquantes par région
1. **PERIMETRE :** définir assurabilité, panier, horizon de l'épisode et services réellement comparables.
2. **ACCES_REEL :** mesurer le temps de la demande au soin réellement reçu et les demandes non servies.
3. **QUALITE :** mesurer sécurité, résultats et continuité avec ajustement des risques.
4. **EQUITE :** protéger l'accès et les besoins complexes et apporter des sources adaptées aux territoires sous-représentés.
5. **PERSONNEL :** démontrer l'effet sur les ETP nets par région, pas seulement les effectifs d'un opérateur.
6. **COUT_COMPLET :** réconcilier payeur, coûts de ressources, capital, aval, ménages et réserves.
7. **DROITS :** avis juridique sur couverture, données, frais, droits et recours.
8. **CONTREFACTUEL :** démontrer le comparateur public améliorable et l'évaluation indépendante des autres modes.

**État actuel : 18 régions × 8 dimensions = 144 cellules de preuves, aucune cellule classée « validée indépendamment ».** Ce n'est pas un constat d'échec du réseau de santé; c'est le niveau d'éléments probants présents **dans le dossier Nova**, qui ne dispose pas de toutes les données institutionnelles.

Une matrice de disponibilité ne doit pas être transformée en palmarès de régions ou en démonstration d'incapacité d'une équipe publique.

## 6. Le garde-fou automatisé ne vote jamais une réforme
Le module `assets/g0-sante-gate-core.mjs` réalise un contrôle documentaire :
- une case ne compte comme complète que si elle porte statut `VALIDEE_INDEPENDAMMENT`, période, lien HTTPS de preuve, référence officielle, périmètre, méthode validée, identité du contrôleur et validation indépendante;
- une case partielle, absente, mal formée ou une RSS en contradiction avec son champ d'enquête crée un **blocage**;
- le résultat normal reste **NON_FRANCHI**;
- même si les huit dimensions de chaque RSS étaient plus tard complètes, l'algorithme ne pourrait répondre que **REVUE_FORMELLE_REQUISE**, sans donner **ni autorisation de pilote ni autorisation de budget**;
- les décisions G0–G4 exigent autorités, procédures et validations indépendantes adaptées, puis une décision formelle traçable.

**La notion de preuve validée à l'intérieur d'un fichier ne confère aucune autorité juridique :** l'outil peut vérifier que des champs sont remplis, pas que les avis cités sont authentiques ou suffisants. La revue manuelle est incontournable.

## 7. Plan d'action sans envoi automatique
Les huit tâches `Q01`–`Q08` du registre sont ordonnées selon une **priorité de collecte méthodologique proposée**, pas selon un budget ou une urgence clinique : accès réel, personnel, périmètre juridique et clinique, coût complet, qualité, équité, contrefactuel, droits. Toutes ont le statut **NON_ENTAME** et `received:false`.

Les demandes préexistantes `M01`–`M09` et les trois modèles de correspondance restent **NON TRANSMISES**. Les pages d'origine des tableaux peuvent être lues sans requérir de dossiers de santé personnels. Il faut ensuite, seulement avec autorisation, établir la disponibilité de données agrégées et les compétences des organismes.

## 8. Résultat recherché avant G1
La phase G0.5 sera utile lorsqu'un tableau comparatif aura, par territoire et période, une **référence de besoins et de personnel, des indicateurs de services effectivement reçus, des coûts complets**, des droits vérifiés et une analyse des effets sur les autres établissements. Les deux RSS absentes de l'EQUSSSS exigent une procédure spécifique et concertée.

**Statut final : dispositif de suivi et de non-régression, sans données inventées; G0 reste NON FRANCHIE, aucune privatisation et aucune économie automatique.**

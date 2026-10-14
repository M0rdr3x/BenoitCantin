# Projet Nova — P50K : consultation préalable des prestataires (aucun fournisseur retenu)

**Pièce préparatoire, 14 octobre 2026. SANS appel d'offres officiel, acquisition, contrat, réception de renseignements ni déploiement.**

## 1. Modalités de présélection

Les **douze exigences** V01 à V12 sont éliminatoires. Elles ne constituent ni une matrice de points fictifs ni des seuils de conformité déjà atteints. Un fournisseur ne peut être réputé admissible que si un responsable habilité a authentifié les preuves, écarté les conflits d'intérêts et obtenu les avis professionnels requis. Une démonstration commerciale n'est **pas** une preuve suffisante.

Les critères doivent d'abord être adaptés au **statut juridique réel** de Projet Nova et aux finalités déterminées, faute de quoi les réponses risqueraient de donner une fausse impression de conformité.

| Code | Preuve à obtenir et examiner HORS dépôt public | Défaut bloquant |
| --- | --- | --- |
| V01 | Contrat avec rôle des parties, confidentialité, droits et retour des données | Aucun cadre contractuel recevable |
| V02 | Localisation par couche (stockage, sauvegarde, assistance, clés) et chaîne de sous-traitance | Juridictions ou sous-traitants inconnus |
| V03 | EFVP de transfert et protection adéquate si applicables, garanties écrites | Flux hors Québec non évalués |
| V04 | Modèle d'habilitation, MFA, délégations temporaires et journal de révocation | Droits excessifs ou MFA absent |
| V05 | Configuration de chiffrement et cycle des clés, responsabilités et récupération | Clés accessibles à des acteurs non habilités |
| V06 | Journalisation minimisée, horodatage, accès aux journaux et supervision | Journaux exposant les données |
| V07 | Quarantaine des pièces, filtrage et isolation des fichiers potentiellement malveillants | Upload non maîtrisé |
| V08 | Politique de sauvegarde, tests de restauration et engagements convenus (RPO/RTO à déterminer) | Restauration non prouvée |
| V09 | Effacement/export, copies de sauvegarde, procédure de sortie | Données impossibles à purger légalement |
| V10 | Canal d'incident, registre, coopération et exigences contractuelles | Incident non notifiable ou non traçable |
| V11 | Gestion de vulnérabilités, correctifs, vérification indépendante | Risques critiques non corrigés |
| V12 | Sortie et portabilité, destruction, révocation des accès, assistance de transition | Dépendance irréversible |

**Une seule preuve inconnue à une exigence éliminatoire → fournisseur non admissible à la sélection à ce stade.**

## 2. Méthode de traitement des réponses

1. Préparer une fiche de besoins minimale qui n'identifie aucune personne concernée et ne demande aucune pièce privée réelle.
2. Faire examiner les exigences par des responsables réellement nommés (confidentialité, sécurité, juridique, exploitation).
3. Demander à chaque prestataire les mêmes catégories de **preuves professionnelles appropriées**, avec espace privé sécurisé et accord de confidentialité si nécessaire.
4. Classer la réponse selon : `NON_EVALUE`, `A_VERIFIER`, `DEMONTRÉ_HORS_DEPOT`, `NON_CONFORME`. **Aucun statut ne doit être changé dans le modèle GitHub public P50K.**
5. Si les douze exigences sont confirmées hors dépôt, seulement alors comparer coûts complets, portabilité, stabilité, délais contractuels, accessibilité et soutien — sans calculer d'économies inventées.
6. La décision d'achat/de traitement est distincte de l'autorisation électorale, du mandat du responsable des données et du GO d'ouverture du coffre.

## 3. Contrôles complémentaires

- **Service de courriel actuel** : fait l'objet d'un **audit distinct** des données, fournisseurs et accès effectifs; P50K ne prouve aucun détail de configuration ou stockage.
- **Conservation** : la durée doit découler de chaque finalité et de la législation applicable, sans valeur arbitraire globale.
- **Transferts hors Québec** : leur existence et leur régime doivent être établis; ne pas présumer que l'utilisation d'une adresse courriel ou d'un domaine implique ou exclut un transfert.
- **Contact direct** : la communication actuelle volontaire n'autorise pas à solliciter des identifiants sensibles, signatures ou dossiers légaux.
- **Accessibilité et réversibilité** : prendre en compte les besoins réels, support en français et continuité de service sans dégrader la sécurité.

## 4. Décision et signature

**Statut : NO_GO.** Aucun prestataire testé, noté, comparé ni retenu dans le présent jalon. Les signatures, les rapports techniques sensibles et les contrats éventuels devront être conservés **hors GitHub**.

### Références juridiques à qualifier
- Loi sur le privé, article 3.3, concernant certains projets technologiques impliquant des renseignements personnels.
- Loi sur le privé, article 17, concernant certaines communications de renseignements hors Québec.
- CAI : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/utilisation-communication-renseignements-personnels
- CAI : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/incidents-confidentialite-mesures-securite-entreprises

Ne pas extrapoler les obligations d'un organisme public ou d'un parti officiellement autorisé à une structure juridique non qualifiée.

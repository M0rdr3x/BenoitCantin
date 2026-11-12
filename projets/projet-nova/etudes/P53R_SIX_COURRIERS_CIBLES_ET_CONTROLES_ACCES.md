# Projet Nova — P53R : six projets de demandes d'accès, prêts à la relecture

**22 octobre 2026. Aucun courrier expédié, aucun délai déclenché, aucune pièce acquise.**

## Objectif

À la suite des six dossiers institutionnels P53P et de l'inventaire P53Q des **102 familles de pièces encore absentes**, ce jalon crée **six projets de lettres d'accès aux documents** : Montréal, ARTM, Québec, STM, RTC et Saint-Valère. Chaque projet est limité à **trois groupes de documents existants** de l'exercice 2024, soit 18 descriptions ciblées, plutôt qu'une demande excessive ou vague de tous les grands livres de l'organisme.

Les projets sont produits par un programme en lecture seule. Ils sont marqués « NE PAS TRANSMETTRE SANS REVUE HUMAINE », et omettent volontairement coordonnées du demandeur, noms privés, signatures, dates de dépôt et identité du responsable nominatif. Le processus doit **vérifier le canal de réception et le bon détenteur** immédiatement avant toute démarche humaine.

## Destinataires et procédures institutionnelles publiques vérifiées

| Code MAMH | Organisation | Procédure publique repérée | Documents demandés en priorité |
|---|---|---|---|
| 66023 | Montréal | https://montreal.ca/services/acces-linformation | Périmètre consolidé, rapport financier 2024, tableaux existants d'éliminations |
| T1025 | ARTM | https://www.artm.quebec/a-propos-de-l-artm/acces-aux-documents-et-protection-des-renseignements-personnels/ | Ententes de financement 2024, annexes de financement, périmètre |
| 23027 | Ville de Québec | https://www.ville.quebec.qc.ca/apropos/acces-information/demande.aspx | Tableaux d'éliminations 2024 déjà détenus, périmètre, rapport financier |
| T0081 | STM | https://www.stm.info/fr/a-propos/gouvernance-d-entreprise/acces-linformation | Indicateurs de service 2024, états annuels, ententes détenues |
| T0088 | RTC | https://www.rtcquebec.ca/propos/gouvernance/acces-linformation | Traitement des écritures réciproques 2024, indicateurs, états annuels |
| 39135 | Saint-Valère | https://www.msvalere.qc.ca/acces-linformation | Rapport financier 2024, résolutions, appels de quote-parts existants |

Chaque site publie sa procédure; P53R ne déduit pas de ces pages que ces 18 types de documents sont tous détenus, communicables ou déjà publiés. Pour Montréal, les documents de la Ville et ceux des arrondissements peuvent relever de circuits différents. Pour Québec, le RTC est une personne morale distincte bien qu'il figure au périmètre consolidé : une demande à la Ville ne suffit pas à établir que la Ville détient les documents originaux du RTC.

## Règles de recevabilité et de protection

**Loi A-2.1, version en vigueur à vérifier avant transmission :**

- **Articles 42 et 43** : une demande doit permettre d'identifier les documents recherchés et être adressée au responsable de l'accès de l'organisme concerné; elle peut être écrite ou verbale, mais la forme écrite doit être privilégiée pour préserver le droit de révision.
- **Documents existants** : demander copie d'un document détenu, et non la production de nouveaux calculs, comparaisons, rapports, synthèses ou appariements de transactions. Demander, si disponible, la version publiée d'abord.
- **Protection des tiers** : permettre le caviardage conforme à la loi; vérifier les restrictions relatives aux renseignements personnels, secrets commerciaux, informations confidentielles et services essentiels.
- **Frais de transmission** : demander qu'ils soient précisés avant la reproduction ou l'envoi.
- **Délais indicatifs** : la règle générale de 20 jours après réception peut faire l'objet d'une prolongation de 10 jours et d'autres procédures suivant la situation, notamment les renseignements de tiers. **Aucun délai ne court tant qu'aucun dépôt n'a eu lieu.**
- **Recours** : un refus total, partiel ou une absence de réponse peut, sous conditions, faire l'objet d'un recours auprès de la Commission d'accès à l'information. Les conditions sont à vérifier pour le cas particulier.

Références officielles :
- https://www.legisquebec.gouv.qc.ca/fr/document/lc/A-2.1
- https://www.cai.gouv.qc.ca/acces-documents-organismes-publics/citoyens-acces-documents-publics/comment-acceder-documents-organismes-publics
- https://www.quebec.ca/acces-information

## Articulation avec les preuves économiques

- Une réponse à une demande d'accès **n'authentifie pas automatiquement** tous les montants ni les pièces comptables bilatérales.
- Les documents du Québec dans le Canada ne sont pas des preuves de revenus ni de compétences d'un Québec souverain hypothétique.
- La Ville de Québec et le RTC exigent une vérification particulière : leur publication financière 2024 indique que des opérations entre entités du périmètre consolidé ont déjà été éliminées. Les éliminer une deuxième fois constituerait un double compte.
- Une diminution de dépense ne sera jamais proposée si elle réduit les emplois, les conditions de travail, les services essentiels ou transfère un coût aux citoyens et aux entreprises.
- P53R ne sollicite ni grand livre confidentiel par défaut ni renseignement d'employé ou d'usager. Les pièces plus sensibles de P53Q restent à traiter après qualification juridique par un responsable habilité.

## Programme et tests

    python scripts/preparer_demandes_acces_nova_p53r.py --bilan p53r_bilan.json --courriers p53r_six_courriers.json
    python scripts/preparer_demandes_acces_nova_p53r.py --exiger-depot-confirme

Les courriers JSON sont **des brouillons contenant seulement des descriptions génériques de documents publics potentiels**. Les rapports CI ne publient que le bilan agrégé et jamais les entrées de revue locales, identités, coordonnées ou documents originaux.

Sorties : **0** = génération structurelle valide; **2** = données non conformes ou tentative d'écrasement; **3** = refus obligatoire d'une affirmation de dépôt. Aucun message n'est envoyé; aucune personne ne peut être induite à croire qu'un dossier est officiellement déposé.

## Conditions avant tout envoi réel

Vérifier manuellement : détenteur et destinataire compétent; versions déjà disponibles; trois descriptions à la portée des documents existants; confidentialité et droits des tiers; demandeur, identité et coordonnées privées; frais éventuels; validation juridique et autorisation de l'expéditeur. Le modèle n'offre aucune fonctionnalité d'envoi : la démarche relève d'une action humaine distincte et volontaire.

**NO_GO_AUTOMATIQUE** : 0 demandes envoyées, 0 accusés de réception vérifiés, 0 originaux comptables authentifiés, 0 avis indépendants signés, 0 économies certifiées, F01–F20 non validées, 1 320 inconnues fiscales. Aucun taux adopté, aucune réduction d'emploi ou de service, aucune fusion sur main ni déploiement officiel.

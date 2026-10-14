# Projet Nova — P50L : dossier de qualification des traitements effectifs

**14 octobre 2026 — Document préparatoire en lecture seule. État : NO_GO.**
**Aucun compte de messagerie, renseignement personnel, preuve privée ni service réel n'a été consulté.**

## 1. Objet et filiation

P50L poursuit P50K (PR 650 : pré-EFVP méthodologique, quatre flux F01–F04, 14 hypothèses de risque et 12 exigences de prestataires), lequel demeure **en brouillon et non fusionné**. La nouvelle priorité est de **distinguer le code HTML observé, les déclarations éditoriales du site et les pratiques internes non vérifiées**. Le projet demeure **Projet Nova**; « Parti Nova » reste une appellation éventuelle et conditionnelle. Archives historiques et base maîtresse V3.40 : préservées, non remplacées.

P50L n'est **pas** une EFVP, un audit Gmail, un audit de sécurité, un avis juridique, une attestation de droit électoral ou une autorisation de traitement.

## 2. Constat sur la branche principale à la date du jalon

`main` SHA `9ed5f70cbe7022f25a679346a1288701f3b09067`.
Pages lues via connecteur GitHub, **source HTML seulement**, pas une vérification des réponses HTTP de production :

| Page | Ce qui est constatable dans la source | Limite |
| --- | --- | --- |
| `contact.html` | Contact `mailto:`, avertissement de ne pas envoyer spontanément des données sensibles, canal de demandes de confidentialité | Aucun droit d'accès réel ni traitement de la boîte connu |
| `recrutement.html` | Contact direct minimal et suspension des formulaires annoncée | Ne démontre pas l'effacement, la localisation ou le chiffrement des courriels |
| `confidentialite.html` | Politique de minimisation, contact volontaire et formulaires externes déclarés suspendus | Le texte n'est pas un audit du fournisseur ni un avis juridique indépendant |
| `participer.html` | Annonce encore un « formulaire intégré de soutien et de préadhésion » | Incohérence publique; correction en PR **636**, non fusionnée |
| `avis-legal.html` | Contient encore « Les formulaires servent uniquement à communiquer avec le Projet Nova » | Incohérence publique; correction en PR **636**, non fusionnée |

Le texte peut mentionner un formulaire sans contenir de balise `<form>`. Le vérificateur P50L doit rapporter **séparément** les deux observations. Les formulations du site ne suffisent pas à établir qu'une collecte est activée ou désactivée dans un service tiers; la suspension Formspree reste **une déclaration** des documents publics.

## 3. Trois niveaux de fiabilité

1. **SOURCE_OBSERVEE** : extrait de page GitHub lié à un SHA, conforme ou contradictoire sur le plan rédactionnel.
2. **DECLARATION_PUBLIQUE** : information publiée sur la politique ou le comportement voulu, à vérifier avant d'en faire une garantie.
3. **VERIFICATION_OPERATIONNELLE_PRIVEE** : preuves d'accès et de configuration du fournisseur, inventaire réel, mandat, captures censurées, avis de sécurité, journaux vérifiés — **AUCUNE FOURNIE**.

Il est interdit de promouvoir un niveau 1 ou 2 au niveau 3 par un rapport automatisé. Une réussite CI teste le **code de contrôle** et non le fonctionnement effectif d'un fournisseur de messagerie.

## 4. Douze pièces de qualification à obtenir HORS GITHUB

| ID | Question de contrôle | Exigence probatoire |
| --- | --- | --- |
| M01 | Qui est le porteur légal et quel régime de protection s'applique? | Qualification indépendante et mandat daté |
| M02 | Qui détient et administre effectivement le compte de courriel? | Responsabilité, délégation et preuve d'habilitation |
| M03 | Quels sont les accès, appareils, sessions et protections MFA? | Revue de configuration sécurisée sans exposer de secrets |
| M04 | Quels tiers, applications, délégations et redirections lisent les messages? | Inventaire d'autorisations et règle de révocation |
| M05 | Où ont lieu traitement, stockage, assistance et sauvegardes? | Attestations prestataires et sous-traitants, sans inférer de l'adresse courriel |
| M06 | Quelle est la finalité des demandes de participation et de confidentialité? | Inventaire des catégories et analyse de nécessité |
| M07 | Quels contenus sensibles sont reçus spontanément et comment sont-ils isolés? | Procédure approuvée, uniquement des statistiques agrégées si licites |
| M08 | Comment les demandes d'accès, rectification et suppression sont-elles gérées? | Procédure et registre privé avec délais selon régime réellement applicable |
| M09 | Quelles périodes de conservation et quelles purges existent? | Calendrier validé, exceptions légales et méthode de destruction |
| M10 | Existe-t-il un transfert ou accès hors Québec et une EFVP est-elle requise? | Cartographie et décision juridique motivée préalable |
| M11 | Quels sont le registre d'incidents et les modalités d'alerte? | Politique, responsables, calendrier de revue et tests autorisés |
| M12 | Comment préserver la cohérence des annonces et contrôler leur publication? | Revue des PR 636/638, preuve de déploiement réel et plan de retour arrière |

Les douze éléments restent **NON_DOCUMENTE** à P50L; leur réalisation ne doit pas être présumée. Ne pas inscrire dans GitHub les courriels des particuliers, le nom des détenteurs, signatures, pièces, journaux de connexion ou empreintes de documents personnels.

## 5. Contrôles de risque et priorités

- **Priorité A : informations contradictoires** — les PR 636/638 proposent les corrections, mais n'ont pas de revues habilitantes attestées; garder la distinction entre changements source et publication réelle.
- **Priorité A : canal courriel déjà déclaré** — le fait que les formulaires soient suspendus ne dispense pas de déterminer les données traitées par la messagerie, ses accès et ses sous-traitants.
- **Priorité A : responsable/mandat non établis** — obtenir la qualification et l'analyse juridique du régime avant de déduire la portée d'obligations spécifiques.
- **Priorité B : conservation et incidents** — procédure future proportionnée, sans durée arbitraire ni affirmation d'une purge déjà testée.
- **Priorité B : coffre non déployé** — conserver la décision P50K, aucun fournisseur choisi ni réception de preuves réelles.
- **Priorité B : cohérence de la communication publique** — revoir les pages, liens, CTA et déclarations après décision de publication et contrôle de la production.

## 6. Procédure future d'audit privé (NE PAS EXÉCUTER AUTOMATIQUEMENT)

**Préconditions** : mandat vérifié, avis du responsable de confidentialité et du juriste, périmètre limité, espace de conservation adapté, limitation des preuves, protocole d'incident. L'auditeur habilité consulte uniquement les **paramètres de configuration nécessaires**, jamais la boîte entière par défaut.

**Séquence** :
1. Identifier la structure porteuse et le responsable des renseignements; valider leur droit d'agir.
2. Cartographier les rôles, accès, applications, redirections, sous-traitants et lieux effectifs.
3. Faire une analyse par catégorie et finalité **sans exporter des messages individuels dans les dossiers de projet**.
4. Examiner les réglages de conservation, purge et droits; documenter les incertitudes avec preuve privée et dates.
5. Décider, pour chaque traitement, les obligations applicables en s'appuyant sur un conseil compétent, y compris les déclencheurs éventuels d'EFVP.
6. Faire approuver séparément un plan de correction, un éventuel nouveau prestataire et une éventuelle mise en ligne.
7. Vérifier effectivement la publication (HTTP bruts + traces de changement) seulement **après** autorisation humaine compétente; dresser B12/B14 séparément.

## 7. Contrôle automatique associé à P50L

`scripts/audit_nova_messagerie_publique_p50l.py` lit seulement des fichiers locaux dans une copie du dépôt. Il vérifie les cinq pages ci-dessus, les présences de balises HTML, les liens `mailto:`, les marqueurs de formulaires externes et les deux formulations obsolètes; il ne conserve pas les adresses de courriel dans les résultats, ne charge aucune boîte, n'accède à aucun réseau ni ne traite de renseignements personnels. L'analyse doit distinguer `ECART_EDITO`, `SURFACE_FORMULAIRE`, `OBSERVATION_SOURCE` et `NON_VERIFIE`.

Un résultat de contrôle stable peut rendre la CI verte **tout en signalant des écarts connus** : CI verte ne signifie ni contenu corrigé, ni confidentialité démontrée, ni décision de publication. Le rapport porte toujours `NO_GO_AUTOMATIQUE`.

## 8. Statuts antérieurs préservés

- **PR 640 : NE PAS FUSIONNER**.
- PR 636/638 et PR 645–650 : brouillons, ne pas fusionner ni publier par automatisme.
- V3.40 conservée; P2-C0-49 EN_COURS; W0 NON_CLOTUREE; W1 NO_GO; W2–W4 NON_AUTORISEES.
- E26 0/20, pouvoirs 0/14, pièces financières 0/16, 14/14 portes financières bloquantes selon le dossier de reprise.
- Formulaires, signatures, adhésions, dons, prêts, contributions et nouvel hébergement de preuve : **non activés**.

## 9. Références officielles

- CAI, champ d'application des obligations des organisations privées : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/champ-application-loi_entreprises
- CAI, responsabilité et délégation : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/responsable-protection-renseignements-personnels-entreprise
- CAI, conservation et destruction : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/conservation-destruction-renseignements-personnels
- CAI, incidents et mesures de sécurité : https://www.cai.gouv.qc.ca/protection-renseignements-personnels/information-entreprises-privees/incidents-confidentialite-mesures-securite-entreprises

Ces références générales ne prouvent ni le statut juridique individuel du Projet Nova, ni les pratiques réelles de sa messagerie.

**Sortie du jalon :** protocole et inventaire préparatoires. **Aucune preuve privée authentifiée et aucun GO accordé.** Suite possible P50M : exercice indépendant de vérification de conformité sur éléments de configuration redigés (hors Git), après désignation des responsables réels.
